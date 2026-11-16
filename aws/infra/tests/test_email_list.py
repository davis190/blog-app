"""Tests for the email list Lambdas. Run from the repo root:

    python3 -m unittest discover -s aws/infra/tests -v

Everything AWS is replaced by small in-memory fakes; nothing touches the network.
"""
import io
import json
import os
import re
import sys
import time
import unittest
from datetime import datetime, timedelta, timezone
from email.utils import format_datetime
from unittest import mock

from botocore.exceptions import ClientError

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "email-list"))

import common  # noqa: E402
import index  # noqa: E402
import notify  # noqa: E402

LIST_BUCKET = "list-bucket"
SITE_BUCKET = "site-bucket"
ENV = {
    "BUCKET_NAME": LIST_BUCKET,
    "EMAIL_LIST_KEY": "email-list.txt",
    "NOTIFY_STATE_KEY": "sent-posts.json",
    "SITE_BUCKET": SITE_BUCKET,
    "SIGNING_SECRET_ARN": "arn:secret",
    "SITE_URL": "https://blog.example.com",
    "FROM_ADDRESS": "from@example.com",
    "OWNER_ADDRESS": "owner@example.com",
    "ALLOW_LEGACY_UNSUBSCRIBE": "false",
    "MAX_AGE_DAYS": "3",
    "DRY_RUN": "false",
}


class FakeS3:
    def __init__(self):
        self.objects = {}

    def get_object(self, Bucket, Key):
        if (Bucket, Key) not in self.objects:
            raise ClientError({"Error": {"Code": "NoSuchKey"}}, "GetObject")
        return {"Body": io.BytesIO(self.objects[(Bucket, Key)])}

    def put_object(self, Bucket, Key, Body, **kwargs):
        self.objects[(Bucket, Key)] = Body

    def text(self, bucket, key):
        return self.objects[(bucket, key)].decode()


class FakeSES:
    def __init__(self):
        self.sent = []
        self.fail_for = set()

    def send_email(self, Source, Destination, Message, ReplyToAddresses):
        to = Destination["ToAddresses"][0]
        if to in self.fail_for:
            raise ClientError({"Error": {"Code": "MessageRejected"}}, "SendEmail")
        self.sent.append({
            "to": to,
            "bcc": Destination.get("BccAddresses", []),
            "subject": Message["Subject"]["Data"],
            "html": Message["Body"]["Html"]["Data"],
            "text": Message["Body"]["Text"]["Data"],
        })


class FakeSecrets:
    def get_secret_value(self, SecretId):
        return {"SecretString": "unit-test-signing-key"}


class AwsTestCase(unittest.TestCase):
    def setUp(self):
        self.s3, self.ses = FakeS3(), FakeSES()
        clients = {"s3": self.s3, "ses": self.ses, "secretsmanager": FakeSecrets()}
        patches = [mock.patch.dict(os.environ, ENV), mock.patch.object(common, "aws", lambda name: clients[name])]
        for p in patches:
            p.start()
            self.addCleanup(p.stop)
        common._signing_key.cache_clear()

    def set_list(self, text):
        self.s3.objects[(LIST_BUCKET, "email-list.txt")] = text.encode()

    def subscribers(self):
        return common.load_list()

    def call(self, method, resource, body):
        return index.handler({"httpMethod": method, "resource": resource, "body": body}, None)

    def token_in(self, mail, page):
        match = re.search(r"/%s/index\.html\?token=([A-Za-z0-9_.-]+)" % page, mail["text"])
        self.assertIsNotNone(match, "no %s link in email: %s" % (page, mail["text"]))
        return match.group(1)


class TokenTests(AwsTestCase):
    def test_round_trip(self):
        token = common.make_token("confirm", "a@example.com", 60)
        self.assertEqual(common.read_token(token, "confirm"), "a@example.com")

    def test_wrong_purpose_is_rejected(self):
        token = common.make_token("confirm", "a@example.com", 60)
        self.assertIsNone(common.read_token(token, "unsubscribe"))

    def test_tampered_payload_is_rejected(self):
        body, signature = common.make_token("unsubscribe", "a@example.com").split(".")
        forged = common._b64(json.dumps({"p": "unsubscribe", "e": "victim@example.com"}).encode())
        self.assertIsNone(common.read_token(forged + "." + signature, "unsubscribe"))

    def test_signed_with_another_key_is_rejected(self):
        token = common.make_token("unsubscribe", "a@example.com")
        common._signing_key.cache_clear()
        with mock.patch.object(common, "_signing_key", lambda: b"some-other-key"):
            self.assertIsNone(common.read_token(token, "unsubscribe"))

    def test_expired_is_rejected(self):
        token = common.make_token("confirm", "a@example.com", 60)
        with mock.patch.object(time, "time", return_value=time.time() + 120):
            self.assertIsNone(common.read_token(token, "confirm"))

    def test_garbage_is_rejected(self):
        for junk in ("", None, "abc", "a.b", "a.b.c", "....", "%%%.%%%"):
            self.assertIsNone(common.read_token(junk, "confirm"), junk)

    def test_unsubscribe_tokens_do_not_expire(self):
        token = common.make_token("unsubscribe", "a@example.com")
        with mock.patch.object(time, "time", return_value=time.time() + 10 * 365 * 86400):
            self.assertEqual(common.read_token(token, "unsubscribe"), "a@example.com")


class SubscribeFlowTests(AwsTestCase):
    def test_subscribe_sends_confirmation_and_does_not_add(self):
        self.set_list("existing@example.com\n")
        response = self.call("POST", "/api/email/subscribe", " new@example.com ")
        self.assertEqual(response["statusCode"], 200)
        self.assertEqual(self.subscribers(), ["existing@example.com"])
        self.assertEqual(len(self.ses.sent), 1)
        mail = self.ses.sent[0]
        self.assertEqual(mail["to"], "new@example.com")
        self.assertEqual(mail["bcc"], [])
        self.assertIn("https://blog.example.com/confirm/index.html?token=", mail["html"])

    def test_invalid_emails_are_rejected_without_sending(self):
        for bad in ("", "nope", "a@b", "a b@example.com", "a@example.com\nBcc: x@y.com", "x" * 300 + "@example.com"):
            self.assertEqual(self.call("POST", "/api/email/subscribe", bad)["statusCode"], 400, bad)
        self.assertEqual(self.ses.sent, [])

    def test_full_flow_confirm_adds_once_and_welcomes_once(self):
        self.set_list("")
        self.call("POST", "/api/email/subscribe", "new@example.com")
        token = self.token_in(self.ses.sent[0], "confirm")

        self.assertEqual(self.call("POST", "/api/email/confirm", token)["statusCode"], 200)
        self.assertEqual(self.subscribers(), ["new@example.com"])
        welcome = self.ses.sent[1]
        self.assertEqual(welcome["to"], "new@example.com")
        self.assertEqual(welcome["bcc"], ["owner@example.com"])
        self.assertIn("reply to this email", welcome["text"])
        self.assertIn("Read the blog: https://blog.example.com/", welcome["text"])

        # Clicking again (or a link scanner) must not duplicate the address or re-send.
        self.assertEqual(self.call("POST", "/api/email/confirm", token)["statusCode"], 200)
        self.assertEqual(self.subscribers(), ["new@example.com"])
        self.assertEqual(len(self.ses.sent), 2)

    def test_welcome_email_unsubscribe_link_is_for_the_new_subscriber(self):
        # Regression: this link used to point at the last address already on the list.
        self.set_list("someone.else@example.com\n")
        self.call("POST", "/api/email/subscribe", "new@example.com")
        self.call("POST", "/api/email/confirm", self.token_in(self.ses.sent[0], "confirm"))
        unsub = self.token_in(self.ses.sent[1], "unsubscribe")
        self.assertEqual(common.read_token(unsub, "unsubscribe"), "new@example.com")

    def test_confirm_rejects_bad_expired_and_wrong_purpose_tokens(self):
        self.assertEqual(self.call("POST", "/api/email/confirm", "garbage")["statusCode"], 400)
        self.assertEqual(self.call("POST", "/api/email/confirm", "")["statusCode"], 400)
        unsub_token = common.make_token("unsubscribe", "a@example.com")
        self.assertEqual(self.call("POST", "/api/email/confirm", unsub_token)["statusCode"], 400)
        old = common.make_token("confirm", "a@example.com", 60)
        with mock.patch.object(time, "time", return_value=time.time() + 4 * 86400):
            self.assertEqual(self.call("POST", "/api/email/confirm", old)["statusCode"], 400)
        self.assertEqual(self.subscribers(), [])

    def test_confirm_is_case_insensitive_about_existing_subscribers(self):
        self.set_list("\nNew@Example.com\n")
        token = common.make_token("confirm", "new@example.com", 60)
        self.call("POST", "/api/email/confirm", token)
        self.assertEqual(self.subscribers(), ["New@Example.com"])
        self.assertEqual(self.ses.sent, [])

    def test_missing_list_file_is_an_empty_list(self):
        token = common.make_token("confirm", "first@example.com", 60)
        self.assertEqual(self.call("POST", "/api/email/confirm", token)["statusCode"], 200)
        self.assertEqual(self.subscribers(), ["first@example.com"])


class UnsubscribeTests(AwsTestCase):
    def setUp(self):
        super().setUp()
        self.set_list("\nKeep@example.com\nLeave@Example.com\n")

    def test_signed_link_removes_only_that_address(self):
        token = common.make_token("unsubscribe", "leave@example.com")
        self.assertEqual(self.call("DELETE", "/api/email/unsubscribe", token)["statusCode"], 200)
        self.assertEqual(self.subscribers(), ["Keep@example.com"])
        self.assertEqual(self.ses.sent[0]["to"], "leave@example.com")
        self.assertEqual(self.ses.sent[0]["bcc"], ["owner@example.com"])

    def test_not_subscribed_succeeds_quietly_without_sending_email(self):
        token = common.make_token("unsubscribe", "stranger@example.com")
        self.assertEqual(self.call("DELETE", "/api/email/unsubscribe", token)["statusCode"], 200)
        self.assertEqual(self.ses.sent, [])
        self.assertEqual(len(self.subscribers()), 2)

    def test_bare_address_is_rejected_by_default(self):
        self.assertEqual(self.call("DELETE", "/api/email/unsubscribe", "Leave@Example.com")["statusCode"], 400)
        self.assertEqual(len(self.subscribers()), 2)

    def test_bare_address_works_when_legacy_links_are_enabled(self):
        with mock.patch.dict(os.environ, {"ALLOW_LEGACY_UNSUBSCRIBE": "true"}):
            self.assertEqual(self.call("DELETE", "/api/email/unsubscribe", "leave@example.com")["statusCode"], 200)
        self.assertEqual(self.subscribers(), ["Keep@example.com"])

    def test_a_confirm_token_cannot_unsubscribe(self):
        token = common.make_token("confirm", "leave@example.com", 60)
        self.assertEqual(self.call("DELETE", "/api/email/unsubscribe", token)["statusCode"], 400)
        self.assertEqual(len(self.subscribers()), 2)


class RoutingTests(AwsTestCase):
    def test_unknown_routes_and_methods(self):
        self.assertEqual(self.call("GET", "/api/email/subscribe", "")["statusCode"], 404)
        self.assertEqual(self.call("DELETE", "/api/email/subscribe", "a@example.com")["statusCode"], 404)
        self.assertEqual(self.call("POST", "/api/email/unsubscribe", "a@example.com")["statusCode"], 404)

    def test_responses_allow_cross_origin_calls_from_the_blog(self):
        response = self.call("POST", "/api/email/subscribe", "x@example.com")
        self.assertEqual(response["headers"]["Access-Control-Allow-Origin"], "*")

    def test_missing_body(self):
        self.assertEqual(index.handler({"httpMethod": "POST", "resource": "/api/email/subscribe", "body": None}, None)["statusCode"], 400)


class ManualSendTests(AwsTestCase):
    def test_sends_to_everyone_with_their_own_unsubscribe_link_and_survives_failures(self):
        self.set_list("a@example.com\nbroken@example.com\nc@example.com\n")
        self.ses.fail_for = {"broken@example.com"}
        result = index.sendEmail({"subject": "Hello", "body": "<p>Hi there</p>"}, None)
        self.assertEqual(result, {"sent": 2, "failed": 1})
        self.assertEqual([m["to"] for m in self.ses.sent], ["a@example.com", "c@example.com"])
        for mail in self.ses.sent:
            self.assertEqual(mail["bcc"], [])
            self.assertIn("Hi there", mail["html"])
            token = self.token_in(mail, "unsubscribe")
            self.assertEqual(common.read_token(token, "unsubscribe"), mail["to"])


def feed_item(title, link, published, description):
    date = format_datetime(published) if published else "Mon, 01 Jan 0001 00:00:00 +0000"
    return ("<item><title>%s</title><link>%s</link><pubDate>%s</pubDate><guid>%s</guid>"
            "<description>%s</description></item>" % (title, link, date, link, description))


def feed(*items):
    return ("<?xml version=\"1.0\"?><rss version=\"2.0\"><channel><title>Blog</title>%s</channel></rss>" % "".join(items)).encode()


class NotifyTests(AwsTestCase):
    NOW = datetime(2026, 11, 17, 15, 0, tzinfo=timezone.utc)

    def setUp(self):
        super().setUp()
        self.set_list("a@example.com\nb@example.com\n")
        patch = mock.patch.object(notify, "datetime", wraps=datetime)
        fake = patch.start()
        fake.now.return_value = self.NOW
        self.addCleanup(patch.stop)

    def set_feed(self, *items):
        self.s3.objects[(SITE_BUCKET, "index.xml")] = feed(*items)

    def run_notifier(self):
        notify.handler({}, None)

    def state(self):
        return json.loads(self.s3.text(LIST_BUCKET, "sent-posts.json"))["sent"]

    def new_post(self, hours_old=6, title="Fresh Post"):
        return feed_item(title, "https://blog.example.com/post/new/", self.NOW - timedelta(hours=hours_old),
                         "&lt;p&gt;%s&lt;/p&gt;&lt;p&gt;The first paragraph.&lt;/p&gt;" % title)

    OLD = feed_item("Old Post", "https://blog.example.com/post/old/", datetime(2022, 3, 9, tzinfo=timezone.utc), "Old summary")
    ABOUT = feed_item("About", "https://blog.example.com/about/", None, "About me")

    def test_announces_a_fresh_post_to_every_subscriber_and_reports_to_the_owner(self):
        self.set_feed(self.new_post(), self.OLD, self.ABOUT)
        self.run_notifier()

        to_subscribers = [m for m in self.ses.sent if m["to"] != "owner@example.com"]
        self.assertEqual([m["to"] for m in to_subscribers], ["a@example.com", "b@example.com"])
        mail = to_subscribers[0]
        self.assertEqual(mail["subject"], "New post: Fresh Post")
        self.assertIn("https://blog.example.com/post/new/", mail["html"])
        self.assertIn("The first paragraph.", mail["text"])
        self.assertEqual(common.read_token(self.token_in(mail, "unsubscribe"), "unsubscribe"), "a@example.com")
        report = [m for m in self.ses.sent if m["to"] == "owner@example.com"]
        self.assertEqual(len(report), 1)
        self.assertIn("2 subscribers (0 failed)", report[0]["text"])

    def test_old_posts_and_pages_are_recorded_but_never_emailed(self):
        self.set_feed(self.OLD, self.ABOUT)
        self.run_notifier()
        self.assertEqual(self.ses.sent, [])
        self.assertEqual(list(self.state()), ["https://blog.example.com/post/old/"])
        self.assertIn("skipped", self.state()["https://blog.example.com/post/old/"])

    def set_page(self, body):
        self.s3.objects[(SITE_BUCKET, "post/new/index.html")] = body.encode()

    def test_email_uses_the_posts_description_when_the_page_has_one(self):
        self.set_page('<head><meta name="description" content="Why it&#39;s about the &amp; not the code." /></head>')
        self.set_feed(self.new_post())
        self.run_notifier()
        mail = self.ses.sent[0]
        self.assertIn("Why it&#x27;s about the &amp; not the code.", mail["html"])  # escaped, displays as "it's" and "&"
        self.assertIn("Why it's about the & not the code.", mail["text"])
        self.assertNotIn("The first paragraph.", mail["text"])

    def test_email_falls_back_to_the_feed_summary_without_a_page_or_description(self):
        for page in (None, "<head><title>No description here</title></head>"):
            self.s3.objects.pop((LIST_BUCKET, "sent-posts.json"), None)
            self.ses.sent.clear()
            if page:
                self.set_page(page)
            self.set_feed(self.new_post())
            self.run_notifier()
            self.assertIn("The first paragraph.", self.ses.sent[0]["text"])

    def test_each_post_is_sent_once(self):
        self.set_feed(self.new_post())
        self.run_notifier()
        count = len(self.ses.sent)
        self.run_notifier()
        self.run_notifier()
        self.assertEqual(len(self.ses.sent), count)

    def test_a_later_post_is_sent_without_resending_the_earlier_one(self):
        self.set_feed(self.new_post())
        self.run_notifier()
        first = len(self.ses.sent)
        second = feed_item("Another", "https://blog.example.com/post/another/", self.NOW - timedelta(hours=1), "Another summary")
        self.set_feed(self.new_post(), second)
        self.run_notifier()
        subjects = [m["subject"] for m in self.ses.sent[first:] if m["to"] != "owner@example.com"]
        self.assertEqual(subjects, ["New post: Another"] * 2)

    def test_a_failed_recipient_does_not_stop_the_rest_or_cause_a_resend(self):
        self.ses.fail_for = {"a@example.com"}
        self.set_feed(self.new_post())
        self.run_notifier()
        self.assertEqual([m["to"] for m in self.ses.sent if m["to"] == "b@example.com"], ["b@example.com"])
        self.assertEqual(self.state()["https://blog.example.com/post/new/"]["failed"], 1)
        self.ses.fail_for = set()
        before = len(self.ses.sent)
        self.run_notifier()
        self.assertEqual(len(self.ses.sent), before)

    def test_a_crash_midway_never_causes_a_second_send(self):
        self.set_feed(self.new_post())
        self.ses.fail_for = {"owner@example.com"}  # the owner report is sent last
        with self.assertRaises(ClientError):
            self.run_notifier()
        self.assertIn("started", self.state()["https://blog.example.com/post/new/"])
        self.ses.fail_for = set()
        before = len(self.ses.sent)
        self.run_notifier()
        self.assertEqual(len(self.ses.sent), before)

    def test_posts_older_than_the_window_are_not_announced(self):
        self.set_feed(self.new_post(hours_old=24 * 4))
        self.run_notifier()
        self.assertEqual(self.ses.sent, [])

    def test_dry_run_sends_and_records_nothing(self):
        self.set_feed(self.new_post())
        with mock.patch.dict(os.environ, {"DRY_RUN": "true"}):
            self.run_notifier()
        self.assertEqual(self.ses.sent, [])
        self.assertNotIn((LIST_BUCKET, "sent-posts.json"), self.s3.objects)

    def test_summary_drops_a_repeated_title_and_is_shortened(self):
        long_text = "word " * 200
        posts = notify.parse_feed(feed(feed_item(
            "Shift Left", "https://blog.example.com/post/s/", self.NOW,
            "&lt;h1&gt;Shift Left&lt;/h1&gt;&lt;p&gt;%s&lt;/p&gt;" % long_text)))
        summary = posts[0]["summary"]
        self.assertTrue(summary.startswith("word"))
        self.assertLessEqual(len(summary), notify.SUMMARY_LENGTH + 3)
        self.assertTrue(summary.endswith("..."))

    def test_missing_feed_fails_loudly(self):
        with self.assertRaises(ClientError):
            self.run_notifier()


if __name__ == "__main__":
    unittest.main()
