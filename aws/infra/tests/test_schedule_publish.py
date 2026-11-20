"""Tests for aws/schedule_publish.py. Run from the repo root:

    python3 -m unittest discover -s aws/infra/tests -v

The scheduler is replaced by an in-memory fake; nothing touches the network.
"""
import os
import re
import sys
import unittest
from datetime import datetime, timedelta, timezone

from botocore.exceptions import ClientError

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import schedule_publish as sp  # noqa: E402

GROUP = "blog-scheduled-publish"
ROLE = "arn:aws:iam::111111111111:role/scheduler"
PIPELINE = "arn:aws:codepipeline:us-east-1:111111111111:Blog-App"
NOW = datetime(2026, 11, 20, 18, 0, tzinfo=timezone.utc)


class FakeScheduler:
    def __init__(self, names=()):
        self.schedules = {n: {} for n in names}
        self.deleted = []
        self.gone_before_delete = set()

    def list_schedules(self, GroupName, NamePrefix, NextToken=None):
        names = sorted(n for n in self.schedules if n.startswith(NamePrefix))
        start = int(NextToken or 0)
        page = names[start:start + 2]  # tiny pages to exercise pagination
        result = {"Schedules": [{"Name": n} for n in page]}
        if start + 2 < len(names):
            result["NextToken"] = str(start + 2)
        return result

    def create_schedule(self, **kwargs):
        self.schedules[kwargs["Name"]] = kwargs

    def delete_schedule(self, Name, GroupName):
        if Name in self.gone_before_delete:
            raise ClientError({"Error": {"Code": "ResourceNotFoundException"}}, "DeleteSchedule")
        self.deleted.append(Name)
        del self.schedules[Name]


class ParseTests(unittest.TestCase):
    def test_hugo_0_93_rows_have_no_header(self):
        out = "content/post/013-monday/index.md,2026-11-23T08:00:00-06:00\n"
        self.assertEqual(
            sp.parse_future(out),
            [("content/post/013-monday/index.md", datetime(2026, 11, 23, 14, 0, tzinfo=timezone.utc))],
        )

    def test_newer_hugo_has_a_header_and_more_columns(self):
        out = (
            "path,slug,title,date,expiryDate,publishDate,draft,permalink\n"
            'content/post/013-monday/index.md,monday,"A, title",2026-11-23T08:00:00-06:00,,2026-11-23T08:00:00-06:00,false,https://x/\n'
        )
        self.assertEqual(
            sp.parse_future(out),
            [("content/post/013-monday/index.md", datetime(2026, 11, 23, 14, 0, tzinfo=timezone.utc))],
        )

    def test_nothing_in_the_future(self):
        self.assertEqual(sp.parse_future(""), [])
        self.assertEqual(sp.parse_future("path,slug,title,date,expiryDate,publishDate,draft,permalink\n"), [])

    def test_utc_and_naive_times(self):
        self.assertEqual(sp.parse_time("2026-11-23T14:00:00Z"), datetime(2026, 11, 23, 14, tzinfo=timezone.utc))
        self.assertEqual(sp.parse_time("2026-11-23T14:00:00"), datetime(2026, 11, 23, 14, tzinfo=timezone.utc))


class NameTests(unittest.TestCase):
    def test_slug_comes_from_the_post_folder_or_file(self):
        self.assertEqual(sp.slug_for("content/post/013-Monday_Post/index.md"), "013-monday-post")
        self.assertEqual(sp.slug_for("content/post/quick-note.md"), "quick-note")
        self.assertEqual(sp.slug_for("content\\post\\win\\index.md"), "win")

    def test_name_is_valid_for_scheduler_and_stable(self):
        when = datetime(2026, 11, 23, 14, 0, tzinfo=timezone.utc)
        path = "content/post/" + "very-long-title-" * 10 + "/index.md"
        name = sp.schedule_name(path, when)
        self.assertLessEqual(len(name), 64)
        self.assertRegex(name, r"^[0-9a-zA-Z_.-]+$")
        self.assertEqual(name, sp.schedule_name(path, when))
        self.assertTrue(name.endswith("-202611231400"))

    def test_redating_a_post_changes_the_name(self):
        path = "content/post/013-monday/index.md"
        a = sp.schedule_name(path, datetime(2026, 11, 23, 14, 0, tzinfo=timezone.utc))
        b = sp.schedule_name(path, datetime(2026, 11, 24, 14, 0, tzinfo=timezone.utc))
        self.assertNotEqual(a, b)

    def test_similar_slugs_dont_collide(self):
        when = datetime(2026, 11, 23, 14, 0, tzinfo=timezone.utc)
        self.assertNotEqual(
            sp.schedule_name("content/post/a b/index.md", when),
            sp.schedule_name("content/post/a-b/index.md", when),
        )


class DesiredTests(unittest.TestCase):
    def test_fires_at_the_publish_time(self):
        when = NOW + timedelta(days=3)
        wanted = sp.desired_schedules([("content/post/x/index.md", when)], NOW)
        ((publish_at, fires_at),) = wanted.values()
        self.assertEqual((publish_at, fires_at), (when, when))

    def test_a_post_due_in_seconds_is_pushed_out_so_the_schedule_is_valid(self):
        when = NOW + timedelta(seconds=10)
        wanted = sp.desired_schedules([("content/post/x/index.md", when)], NOW)
        ((publish_at, fires_at),) = wanted.values()
        self.assertEqual(publish_at, when)
        self.assertEqual(fires_at, NOW + sp.MIN_LEAD)


class ReconcileTests(unittest.TestCase):
    def posts(self, *days):
        return [(f"content/post/{d}-post/index.md", NOW + timedelta(days=d)) for d in days]

    def run_reconcile(self, client, posts, **kwargs):
        wanted = sp.desired_schedules(posts, NOW)
        sp.reconcile(client, GROUP, ROLE, PIPELINE, wanted, **kwargs)
        return wanted

    def test_creates_one_schedule_per_future_post(self):
        client = FakeScheduler()
        wanted = self.run_reconcile(client, self.posts(3, 5, 9))
        self.assertEqual(set(client.schedules), set(wanted))
        schedule = client.schedules[sp.schedule_name("content/post/3-post/index.md", NOW + timedelta(days=3))]
        self.assertEqual(schedule["GroupName"], GROUP)
        self.assertEqual(schedule["ScheduleExpression"], "at(2026-11-23T18:00:00)")
        self.assertEqual(schedule["ScheduleExpressionTimezone"], "UTC")
        self.assertEqual(schedule["ActionAfterCompletion"], "DELETE")
        self.assertEqual(schedule["FlexibleTimeWindow"], {"Mode": "OFF"})
        self.assertEqual(schedule["Target"]["Arn"], PIPELINE)
        self.assertEqual(schedule["Target"]["RoleArn"], ROLE)
        self.assertRegex(schedule["ScheduleExpression"], r"^at\(\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\)$")

    def test_second_run_changes_nothing(self):
        client = FakeScheduler()
        self.run_reconcile(client, self.posts(3, 5))
        before = dict(client.schedules)
        self.run_reconcile(client, self.posts(3, 5))
        self.assertEqual(client.schedules, before)
        self.assertEqual(client.deleted, [])

    def test_removes_schedules_for_posts_that_are_no_longer_future(self):
        client = FakeScheduler()
        self.run_reconcile(client, self.posts(3, 5))
        wanted = self.run_reconcile(client, self.posts(5))  # the 3-day post was re-dated into the past or deleted
        self.assertEqual(set(client.schedules), set(wanted))
        self.assertEqual(len(client.deleted), 1)

    def test_redating_replaces_the_schedule(self):
        client = FakeScheduler()
        self.run_reconcile(client, self.posts(3))
        moved = [("content/post/3-post/index.md", NOW + timedelta(days=4))]
        wanted = self.run_reconcile(client, moved)
        self.assertEqual(set(client.schedules), set(wanted))
        self.assertEqual(len(client.deleted), 1)

    def test_schedule_that_already_fired_and_deleted_itself_is_not_an_error(self):
        client = FakeScheduler(names=["pub-old-abc123-202611200800"])
        client.gone_before_delete.add("pub-old-abc123-202611200800")
        self.run_reconcile(client, [])
        self.assertEqual(client.deleted, [])

    def test_other_schedules_in_the_group_are_left_alone(self):
        client = FakeScheduler(names=["something-else"])
        self.run_reconcile(client, [])
        self.assertIn("something-else", client.schedules)

    def test_dry_run_changes_nothing(self):
        client = FakeScheduler(names=["pub-stale-abc123-202611200800"])
        self.run_reconcile(client, self.posts(3), dry_run=True)
        self.assertEqual(set(client.schedules), {"pub-stale-abc123-202611200800"})
        self.assertEqual(client.deleted, [])

    def test_other_errors_are_not_swallowed(self):
        class Broken(FakeScheduler):
            def delete_schedule(self, Name, GroupName):
                raise ClientError({"Error": {"Code": "AccessDeniedException"}}, "DeleteSchedule")

        client = Broken(names=["pub-stale-abc123-202611200800"])
        with self.assertRaises(ClientError):
            self.run_reconcile(client, [])

    def test_listing_follows_pagination(self):
        client = FakeScheduler(names=[f"pub-{i}-aaaaaa-202611200800" for i in range(5)])
        self.assertEqual(len(sp.existing_names(client, GROUP)), 5)


if __name__ == "__main__":
    unittest.main()
