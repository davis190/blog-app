import base64

import common


def handler(event, context):
    route = ROUTES.get((event.get("httpMethod"), event.get("resource")))
    if route is None:
        return api_response("Not found", 404)

    body = event.get("body") or ""
    if event.get("isBase64Encoded"):
        body = base64.b64decode(body).decode("utf-8")
    print("%s %s" % (event["httpMethod"], event["resource"]))
    return route(body.strip())


def api_response(text, code):
    return {
        "isBase64Encoded": False,
        "statusCode": code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS",
        },
        "body": text,
    }


def subscribe(body):
    """Emails a confirmation link. Nothing is added to the list until it's clicked."""
    email = common.clean_email(body)
    if not email:
        return api_response("Invalid email", 400)

    token = common.make_token("confirm", email, common.CONFIRM_TTL_SECONDS)
    html_body, text_body = common.message(
        [
            "Thanks for subscribing to the blog! Please confirm your email address "
            "so I know it was really you.",
            "This link expires in 3 days. If you didn't sign up, you can ignore this email.",
        ],
        button=("Confirm subscription", common.page_link("confirm", token)),
    )
    common.send_email(email, "Confirm your subscription - blog.claytondavis.dev", html_body, text_body)
    # Same answer whether or not the address is already subscribed.
    return api_response("Success", 200)


def confirm(body):
    email = common.read_token(body, "confirm")
    if not email:
        return api_response("Invalid or expired link", 400)

    if common.add_subscriber(email):
        html_body, text_body = common.message(
            [
                "You're subscribed. Thanks for signing up!",
                "There's no schedule and no spam. I'll just email you when I publish something new.",
                "If you ever want to talk about something I wrote, reply to this email. It comes straight to me.",
                "Clayton",
            ],
            button=("Read the blog", common.site_url() + "/"),
            footer=common.unsubscribe_footer(email),
        )
        common.send_email(email, "You're subscribed - blog.claytondavis.dev", html_body, text_body, bcc_owner=True)
    return api_response("Success", 200)


def unsubscribe(body):
    email = common.read_token(body, "unsubscribe")
    # Links in emails sent before signed links existed carry the bare address.
    if not email and common.env("ALLOW_LEGACY_UNSUBSCRIBE") == "true":
        email = common.clean_email(body)
    if not email:
        return api_response("Invalid link", 400)

    # Only email people who were actually on the list.
    if common.remove_subscriber(email):
        html_body, text_body = common.message(["You have been unsubscribed. Come back soon!"])
        common.send_email(email, "Unsubscribed - blog.claytondavis.dev", html_body, text_body, bcc_owner=True)
    return api_response("Success", 200)


ROUTES = {
    ("POST", "/api/email/subscribe"): subscribe,
    ("POST", "/api/email/confirm"): confirm,
    ("DELETE", "/api/email/unsubscribe"): unsubscribe,
}


def sendEmail(event, context):
    """Manual send to everyone on the list. Invoke with {"subject": "...", "body": "<html>"}.

    New posts are emailed automatically by notify.handler; this is for one-off messages.
    """
    sent, failed = 0, 0
    for email in common.load_list():
        footer_html, footer_text = common.message([], footer=common.unsubscribe_footer(email))
        try:
            common.send_email(
                email,
                event["subject"],
                event["body"] + footer_html,
                common.html_to_text(event["body"]) + "\n\n" + footer_text,
            )
            sent += 1
        except Exception as e:  # keep going so one bad address doesn't stop the rest
            print("Failed to send to a subscriber: %s" % e)
            failed += 1
    print("Sent %d, failed %d" % (sent, failed))
    return {"sent": sent, "failed": failed}
