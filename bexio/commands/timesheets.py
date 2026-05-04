"""Timesheet commands."""

import sys
from bexio.output import print_json


def register(sub):
    p = sub.add_parser("timesheets", help="Timesheet commands")
    s = p.add_subparsers(dest="action")

    ls = s.add_parser("list", help="List timesheets")
    ls.add_argument("--limit", type=int, default=100)

    show = s.add_parser("show", help="Show timesheet")
    show.add_argument("id", type=int)

    search = s.add_parser("search", help="Search timesheets by text")
    search.add_argument("query", type=str)

    create = s.add_parser("create", help="Create a timesheet entry")
    create.add_argument("--date", required=True, help="Date (YYYY-MM-DD)")
    create.add_argument("--duration", required=True, help="Duration (HH:MM)")
    create.add_argument("--user-id", dest="user_id", type=int)
    create.add_argument("--project-id", dest="project_id", type=int)
    create.add_argument("--text", help="Description")

    edit = s.add_parser("edit", help="Edit a timesheet entry")
    edit.add_argument("id", type=int)
    edit.add_argument("--date", help="Date (YYYY-MM-DD)")
    edit.add_argument("--duration", help="Duration (HH:MM)")
    edit.add_argument("--text", help="Description")

    delete = s.add_parser("delete", help="Delete a timesheet entry")
    delete.add_argument("id", type=int)

    s.add_parser("statuses", help="List timesheet statuses")

    return p


def handle(args, client, json_flag):
    if args.action == "list":
        _list(args, client, json_flag)
    elif args.action == "show":
        _show(args, client, json_flag)
    elif args.action == "search":
        _search(args, client, json_flag)
    elif args.action == "create":
        _create(args, client, json_flag)
    elif args.action == "edit":
        _edit(args, client, json_flag)
    elif args.action == "delete":
        _delete(args, client, json_flag)
    elif args.action == "statuses":
        _statuses(args, client, json_flag)
    else:
        sys.exit("Usage: bexio timesheets {list|show|search|create|edit|delete|statuses}")


def _tracking_date(t):
    if not t:
        return "-"
    return t.get("date", "-") or "-"


def _tracking_duration(t):
    if not t:
        return "-"
    return t.get("duration", "-") or "-"


def _list(args, client, json_flag):
    entries = client.get("/timesheet", params={"limit": args.limit})
    if not isinstance(entries, list):
        sys.exit(f"Unexpected response: {entries}")
    if json_flag:
        print_json(entries)
        return
    if not entries:
        print("No timesheets found.")
        return
    for e in entries:
        t = e.get("tracking") or {}
        date = _tracking_date(t)
        duration = _tracking_duration(t)
        text = (e.get("text") or "")[:40]
        project = e.get("pr_project_id") or "-"
        print(f"{e['id']:>5}  {date}  {duration}  user:{e.get('user_id', '-')}  proj:{project}  {text}")


def _show(args, client, json_flag):
    e = client.get(f"/timesheet/{args.id}")
    if json_flag:
        print_json(e)
        return
    t = e.get("tracking") or {}
    print(f"ID:         {e['id']}")
    print(f"Date:       {_tracking_date(t)}")
    print(f"Duration:   {_tracking_duration(t)}")
    print(f"User ID:    {e.get('user_id', '-')}")
    print(f"Project ID: {e.get('pr_project_id', '-')}")
    print(f"Status ID:  {e.get('status_id', '-')}")
    print(f"Billable:   {e.get('allowable_bill', '-')}")
    print(f"Text:       {e.get('text', '-')}")


def _search(args, client, json_flag):
    results = client.post("/timesheet/search", body=[
        {"field": "text", "value": args.query, "criteria": "like"}
    ])
    if not isinstance(results, list):
        sys.exit(f"Unexpected response: {results}")
    if json_flag:
        print_json(results)
        return
    if not results:
        print("No timesheets found.")
        return
    for e in results:
        t = e.get("tracking") or {}
        date = _tracking_date(t)
        duration = _tracking_duration(t)
        text = (e.get("text") or "")[:40]
        project = e.get("pr_project_id") or "-"
        print(f"{e['id']:>5}  {date}  {duration}  user:{e.get('user_id', '-')}  proj:{project}  {text}")


def _create(args, client, json_flag):
    body = {
        "tracking": {
            "type": "duration",
            "date": args.date,
            "duration": args.duration,
        }
    }
    if args.user_id is not None:
        body["user_id"] = args.user_id
    if args.project_id is not None:
        body["pr_project_id"] = args.project_id
    if args.text is not None:
        body["text"] = args.text
    result = client.post("/timesheet", body=body)
    if json_flag:
        print_json(result)
        return
    print(f"Timesheet {result.get('id')} created")


def _edit(args, client, json_flag):
    body = {}
    tracking = {}
    if args.date is not None:
        tracking["date"] = args.date
    if args.duration is not None:
        tracking["duration"] = args.duration
    if tracking:
        tracking["type"] = "duration"
        body["tracking"] = tracking
    if args.text is not None:
        body["text"] = args.text
    result = client.put(f"/timesheet/{args.id}", body=body)
    if json_flag:
        print_json(result)
        return
    print(f"Timesheet {args.id} updated")


def _delete(args, client, json_flag):
    client.delete(f"/timesheet/{args.id}")
    print(f"Timesheet {args.id} deleted")


def _statuses(args, client, json_flag):
    statuses = client.get("/timesheet_status")
    if json_flag:
        print_json(statuses)
        return
    for s in statuses:
        print(f"{s['id']:>3}  {s['name']}")
