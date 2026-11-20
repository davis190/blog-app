"""Arms one-off EventBridge Scheduler schedules that rebuild the site when a future-dated post comes due.

Hugo leaves future-dated posts out of the build, and nothing else rebuilds the site on the day. So after each
build this script asks Hugo which posts are still in the future and makes the schedule group match: one `at()`
schedule per post, firing at its publish time and starting the pipeline. Schedules delete themselves once fired.
Any schedule in the group that no longer matches a future post (re-dated, un-drafted, removed) is deleted.

Run from the repo root, after the build and the stack deploy:

    python3 aws/schedule_publish.py --hugo ./hugo --stack blog-email-subscription [--dry-run]

The group, role and pipeline ARN come from the stack outputs. A failure exits non-zero so the build goes red:
a post that can't be armed would otherwise just never publish.
"""
import argparse
import csv
import hashlib
import io
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone

from botocore.exceptions import ClientError

NAME_PREFIX = "pub-"
# `at()` can't be in the past, and the build that arms it is still running, so keep a little lead time.
MIN_LEAD = timedelta(seconds=90)


def parse_time(value):
    parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def parse_future(output):
    """Returns [(content path, publish time in UTC)].

    Hugo 0.93 prints bare `path,date` rows. Newer Hugo prints a header row and more columns.
    """
    posts = []
    header = None
    for row in csv.reader(io.StringIO(output)):
        if not row:
            continue
        if row[0] == "path":
            header = row
            continue
        if header:
            fields = dict(zip(header, row))
            when = fields.get("publishDate") or fields.get("date")
        else:
            when = row[1]
        posts.append((row[0], parse_time(when)))
    return posts


def slug_for(path):
    parts = re.split(r"[\\/]", path)
    stem = parts[-1].rsplit(".", 1)[0]
    if stem in ("index", "_index") and len(parts) > 1:
        stem = parts[-2]
    return re.sub(r"[^0-9a-zA-Z]+", "-", stem).strip("-").lower() or "post"


def schedule_name(path, publish_at):
    """Scheduler names allow [0-9a-zA-Z-_.] up to 64 characters.

    The publish time is part of the name, so re-dating a post yields a new name: the old schedule is
    deleted and a new one created, with no need to read an existing schedule back.
    """
    digest = hashlib.sha1(path.encode()).hexdigest()[:6]
    return f"{NAME_PREFIX}{slug_for(path)[:36]}-{digest}-{publish_at:%Y%m%d%H%M}"


def desired_schedules(posts, now):
    """Returns {schedule name: (publish time, time the schedule fires)}."""
    wanted = {}
    for path, publish_at in posts:
        fires_at = max(publish_at, now + MIN_LEAD)
        wanted[schedule_name(path, publish_at)] = (publish_at, fires_at)
    return wanted


def existing_names(client, group):
    names = set()
    token = None
    while True:
        kwargs = {"GroupName": group, "NamePrefix": NAME_PREFIX}
        if token:
            kwargs["NextToken"] = token
        page = client.list_schedules(**kwargs)
        names.update(s["Name"] for s in page.get("Schedules", []))
        token = page.get("NextToken")
        if not token:
            return names


def is_missing(error):
    return error.response["Error"]["Code"] == "ResourceNotFoundException"


def reconcile(client, group, role_arn, pipeline_arn, wanted, dry_run=False):
    have = existing_names(client, group)
    for name in sorted(have - set(wanted)):
        print(f"delete  {name}")
        if not dry_run:
            try:
                client.delete_schedule(Name=name, GroupName=group)
            except ClientError as error:
                if not is_missing(error):
                    raise
                # it fired and deleted itself since we listed
    for name in sorted(set(wanted) - have):
        publish_at, fires_at = wanted[name]
        print(f"create  {name}  publish {publish_at:%Y-%m-%d %H:%M} UTC  fires {fires_at:%Y-%m-%d %H:%M:%S} UTC")
        if dry_run:
            continue
        client.create_schedule(
            Name=name,
            GroupName=group,
            Description=f"Rebuild the blog so the post due {publish_at:%Y-%m-%d %H:%M} UTC goes live.",
            ScheduleExpression=f"at({fires_at:%Y-%m-%dT%H:%M:%S})",
            ScheduleExpressionTimezone="UTC",
            FlexibleTimeWindow={"Mode": "OFF"},
            ActionAfterCompletion="DELETE",
            Target={
                "Arn": pipeline_arn,
                "RoleArn": role_arn,
                # An extra pipeline run is harmless (a no-op rebuild), so retrying is safe.
                "RetryPolicy": {"MaximumRetryAttempts": 2, "MaximumEventAgeInSeconds": 3600},
            },
        )
    kept = len(set(wanted) & have)
    print(f"{len(wanted)} future post(s): {len(set(wanted) - have)} armed, {kept} already armed, "
          f"{len(have - set(wanted))} stale removed")


def stack_outputs(cloudformation, stack):
    described = cloudformation.describe_stacks(StackName=stack)["Stacks"][0]
    return {o["OutputKey"]: o["OutputValue"] for o in described.get("Outputs", [])}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--hugo", default="hugo", help="Hugo binary used for `hugo list future`")
    parser.add_argument("--stack", required=True, help="stack whose outputs name the group, role and pipeline")
    parser.add_argument("--region", default="us-east-1")
    parser.add_argument("--dry-run", action="store_true", help="print what would change, change nothing")
    args = parser.parse_args(argv)

    import boto3  # imported here so the parsing helpers can be used without it

    listed = subprocess.run([args.hugo, "list", "future"], check=True, capture_output=True, text=True)
    posts = parse_future(listed.stdout)
    wanted = desired_schedules(posts, datetime.now(timezone.utc))

    outputs = stack_outputs(boto3.client("cloudformation", region_name=args.region), args.stack)
    reconcile(
        boto3.client("scheduler", region_name=args.region),
        outputs["PublishScheduleGroupName"],
        outputs["PublishSchedulerRoleArn"],
        outputs["PublishPipelineArn"],
        wanted,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    sys.exit(main())
