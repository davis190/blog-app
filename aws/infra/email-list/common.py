"""Shared helpers for the email list Lambdas: list storage, signed links, and email."""
import base64
import hashlib
import hmac
import html
import json
import os
import re
import time
from functools import lru_cache

import boto3
from botocore.exceptions import ClientError

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
CONFIRM_TTL_SECONDS = 3 * 24 * 60 * 60

ACCENT = "#54df77"


def env(name, default=None):
    return os.environ.get(name, default)


@lru_cache(maxsize=None)
def aws(service):
    """One place that builds boto3 clients, so tests can swap it out."""
    return boto3.client(service)


# ---------------------------------------------------------------- subscribers

def clean_email(raw):
    """Returns the trimmed address, or None if it doesn't look like an email."""
    email = (raw or "").strip()
    if len(email) > 254 or not EMAIL_RE.fullmatch(email):
        return None
    return email


def load_list():
    """Returns the subscriber addresses, ignoring blank lines."""
    try:
        obj = aws("s3").get_object(Bucket=env("BUCKET_NAME"), Key=env("EMAIL_LIST_KEY"))
    except ClientError as e:
        if e.response["Error"]["Code"] == "NoSuchKey":
            return []
        raise
    lines = obj["Body"].read().decode("utf-8").splitlines()
    return [line.strip() for line in lines if line.strip()]


def save_list(emails):
    aws("s3").put_object(
        Bucket=env("BUCKET_NAME"),
        Key=env("EMAIL_LIST_KEY"),
        Body=("\n".join(emails) + "\n").encode("utf-8"),
        ContentType="text/plain",
    )


def add_subscriber(email):
    """Adds the address. Returns False if it was already subscribed (case-insensitive)."""
    emails = load_list()
    if email.lower() in {e.lower() for e in emails}:
        return False
    save_list(emails + [email])
    return True


def remove_subscriber(email):
    """Removes the address. Returns False if it wasn't subscribed."""
    emails = load_list()
    remaining = [e for e in emails if e.lower() != email.lower()]
    if len(remaining) == len(emails):
        return False
    save_list(remaining)
    return True


# --------------------------------------------------------------- signed links
#
# Links in emails carry a signed token instead of a bare address, so nobody can
# confirm or unsubscribe an address they can't read mail for. The token is
# base64url(payload) + "." + base64url(HMAC-SHA256). The payload is signed, not
# encrypted: it contains the address.

def _b64(raw):
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _unb64(text):
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


@lru_cache(maxsize=None)
def _signing_key():
    secret = aws("secretsmanager").get_secret_value(SecretId=env("SIGNING_SECRET_ARN"))
    return secret["SecretString"].encode("utf-8")


def _sign(body):
    return _b64(hmac.new(_signing_key(), body.encode("ascii"), hashlib.sha256).digest())


def make_token(purpose, email, ttl_seconds=None):
    payload = {"p": purpose, "e": email}
    if ttl_seconds:
        payload["x"] = int(time.time()) + ttl_seconds
    body = _b64(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    return body + "." + _sign(body)


def read_token(token, purpose):
    """Returns the address in a valid, unexpired token for this purpose, else None."""
    try:
        body, signature = (token or "").strip().split(".")
        if not hmac.compare_digest(signature, _sign(body)):
            return None
        payload = json.loads(_unb64(body))
    except (ValueError, UnicodeError):
        return None
    if payload.get("p") != purpose:
        return None
    if payload.get("x") and payload["x"] < time.time():
        return None
    return clean_email(payload.get("e"))


def site_url():
    return env("SITE_URL", "https://blog.claytondavis.dev").rstrip("/")


def page_link(page, token):
    return "%s/%s/index.html?token=%s" % (site_url(), page, token)


def unsubscribe_link(email):
    return page_link("unsubscribe", make_token("unsubscribe", email))


# ---------------------------------------------------------------------- email

def message(paragraphs, button=None, footer=None, heading=None):
    """Builds a simple (html, text) pair. Heading, paragraphs and footer are plain text."""
    html_parts = []
    text_parts = []
    if heading:
        html_parts.append("<h2 style=\"margin:0 0 16px 0;font-size:22px;line-height:1.3\">%s</h2>" % html.escape(heading))
        text_parts.append(heading)
    html_parts += ["<p style=\"margin:0 0 16px 0\">%s</p>" % html.escape(p) for p in paragraphs]
    text_parts += list(paragraphs)
    if button:
        label, url = button
        html_parts.append(
            "<p style=\"margin:24px 0\"><a href=\"%s\" style=\"background:%s;color:#111;"
            "padding:12px 22px;border-radius:4px;text-decoration:none;font-weight:600;"
            "display:inline-block\">%s</a></p>" % (html.escape(url, quote=True), ACCENT, html.escape(label))
        )
        text_parts.append("%s: %s" % (label, url))
    if footer:
        text, link_label, link_url = footer
        html_parts.append(
            "<hr style=\"border:none;border-top:1px solid #eee;margin:32px 0 16px 0\">"
            "<p style=\"font-size:13px;color:#777;margin:0\">%s <a href=\"%s\" style=\"color:#777\">%s</a></p>"
            % (html.escape(text), html.escape(link_url, quote=True), html.escape(link_label))
        )
        text_parts.append("-- \n%s %s: %s" % (text, link_label, link_url))
    wrapped = (
        "<div style=\"font-family:-apple-system,Segoe UI,Helvetica,Arial,sans-serif;max-width:560px;"
        "margin:0 auto;padding:24px;color:#222;line-height:1.6;font-size:16px\">%s</div>" % "".join(html_parts)
    )
    return wrapped, "\n\n".join(text_parts)


def html_to_text(markup):
    """Crude tag stripper for plain-text fallbacks and feed summaries."""
    text = html.unescape(re.sub(r"<[^>]+>", " ", markup or ""))
    return re.sub(r"\s+", " ", text).strip()


def send_email(to, subject, html_body, text_body, bcc_owner=False):
    owner = env("OWNER_ADDRESS")
    destination = {"ToAddresses": [to]}
    if bcc_owner:
        destination["BccAddresses"] = [owner]
    aws("ses").send_email(
        Source=env("FROM_ADDRESS"),
        Destination=destination,
        Message={
            "Subject": {"Data": subject, "Charset": "UTF-8"},
            "Body": {
                "Html": {"Data": html_body, "Charset": "UTF-8"},
                "Text": {"Data": text_body, "Charset": "UTF-8"},
            },
        },
        ReplyToAddresses=[owner],
    )


def unsubscribe_footer(email):
    return ("You're getting this because you subscribed to blog.claytondavis.dev.", "Unsubscribe", unsubscribe_link(email))
