"""Emails subscribers when a new post shows up in the site's RSS feed.

Runs on a schedule. The feed is read straight from the site bucket (not through
CloudFront, which can serve a stale copy). Posts already announced are tracked in
a small JSON file next to the subscriber list, so each post is sent exactly once.
"""
import html
import json
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import urlparse

from botocore.exceptions import ClientError

import common

SUMMARY_LENGTH = 300


def handler(event, context):
    now = datetime.now(timezone.utc)
    max_age = timedelta(days=int(common.env("MAX_AGE_DAYS", "3")))
    dry_run = common.env("DRY_RUN") == "true"

    state = load_state()
    dirty = False
    for post in sorted(read_posts(), key=lambda p: p["published"]):
        if post["link"] in state["sent"]:
            continue

        # The first run sees every existing post. Anything old is recorded, not emailed.
        if now - post["published"] > max_age:
            state["sent"][post["link"]] = {"skipped": "older than %s" % max_age, "at": now.isoformat()}
            dirty = True
            continue

        if dry_run:
            print("DRY RUN: would email subscribers about '%s'" % post["title"])
            continue

        # Record the post before sending. If this run dies midway, the next run must not
        # email everyone a second time; a missed recipient is better than a duplicate.
        state["sent"][post["link"]] = {"started": now.isoformat()}
        save_state(state)
        post["blurb"] = page_description(post["link"]) or post["summary"]
        result = announce(post)
        state["sent"][post["link"]] = dict(result, at=now.isoformat())
        save_state(state)
        dirty = False

    if dirty:
        save_state(state)


def announce(post):
    sent, failed = 0, 0
    for email in common.load_list():
        html_body, text_body = common.message(
            [post["blurb"]],
            heading=post["title"],
            button=("Read the post", post["link"]),
            footer=common.unsubscribe_footer(email),
        )
        try:
            common.send_email(email, "New post: " + post["title"], html_body, text_body)
            sent += 1
        except Exception as e:  # keep going so one bad address doesn't stop the rest
            print("Failed to send to a subscriber: %s" % e)
            failed += 1

    print("Announced '%s': sent %d, failed %d" % (post["title"], sent, failed))
    report, report_text = common.message(
        ["Sent to %d subscribers (%d failed)." % (sent, failed), post["link"]],
        heading="Announced: " + post["title"],
    )
    common.send_email(common.env("OWNER_ADDRESS"), "Sent: " + post["title"], report, report_text)
    return {"sent": sent, "failed": failed}


def read_posts():
    feed = common.aws("s3").get_object(Bucket=common.env("SITE_BUCKET"), Key=common.env("FEED_KEY", "index.xml"))
    return parse_feed(feed["Body"].read())


def parse_feed(xml_bytes):
    """Returns the posts in an RSS feed. Pages like About have no date and are skipped."""
    posts = []
    for item in ET.fromstring(xml_bytes).findall("./channel/item"):
        link = (item.findtext("link") or "").strip()
        published = item.findtext("pubDate")
        if "/post/" not in link or not published:
            continue
        title = (item.findtext("title") or "").strip()
        posts.append({
            "title": title,
            "link": link,
            "published": parsedate_to_datetime(published),
            "summary": summarize(title, item.findtext("description")),
        })
    return posts


def page_description(link):
    """The post's own front-matter description, read from its page's <meta> tag.

    Better than a slice of the opening paragraphs, which can stop mid-thought.
    Returns None if the page or tag isn't there.
    """
    key = urlparse(link).path.lstrip("/")
    if not key or key.endswith("/"):
        key += "index.html"
    try:
        page = common.aws("s3").get_object(Bucket=common.env("SITE_BUCKET"), Key=key)["Body"].read().decode("utf-8", "replace")
    except ClientError:
        return None
    match = re.search(r'<meta name="description" content="([^"]*)"', page)
    return html.unescape(match.group(1)).strip() if match else None


def summarize(title, description):
    text = common.html_to_text(description)
    if text.startswith(title):  # some posts open with a copy of their own title
        text = text[len(title):].strip()
    if len(text) > SUMMARY_LENGTH:
        text = text[:SUMMARY_LENGTH].rsplit(" ", 1)[0].rstrip(",;:.") + "..."
    return text


def load_state():
    try:
        obj = common.aws("s3").get_object(Bucket=common.env("BUCKET_NAME"), Key=common.env("NOTIFY_STATE_KEY"))
    except ClientError as e:
        if e.response["Error"]["Code"] == "NoSuchKey":
            return {"sent": {}}
        raise
    return json.loads(obj["Body"].read())


def save_state(state):
    common.aws("s3").put_object(
        Bucket=common.env("BUCKET_NAME"),
        Key=common.env("NOTIFY_STATE_KEY"),
        Body=json.dumps(state, indent=2, sort_keys=True).encode("utf-8"),
        ContentType="application/json",
    )
