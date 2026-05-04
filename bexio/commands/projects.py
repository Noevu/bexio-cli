"""Project, milestone, and work-package commands."""

import sys
from bexio.output import print_json

V3 = "https://api.bexio.com/3.0"


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

def register(sub):
    p = sub.add_parser("projects", help="Project commands")
    s = p.add_subparsers(dest="action")

    ls = s.add_parser("list", help="List projects")
    ls.add_argument("--limit", type=int, default=100)

    show = s.add_parser("show", help="Show project")
    show.add_argument("id", type=int)

    search = s.add_parser("search", help="Search projects by name")
    search.add_argument("query")

    create = s.add_parser("create", help="Create project")
    create.add_argument("--name", required=True)
    create.add_argument("--contact-id", type=int, dest="contact_id")
    create.add_argument("--start", dest="start_date")
    create.add_argument("--end", dest="end_date")
    create.add_argument("--type-id", type=int, dest="pr_project_type_id")

    edit = s.add_parser("edit", help="Edit project")
    edit.add_argument("id", type=int)
    edit.add_argument("--name")
    edit.add_argument("--start", dest="start_date")
    edit.add_argument("--end", dest="end_date")

    delete = s.add_parser("delete", help="Delete project")
    delete.add_argument("id", type=int)

    archive = s.add_parser("archive", help="Archive project")
    archive.add_argument("id", type=int)

    reactivate = s.add_parser("reactivate", help="Reactivate project")
    reactivate.add_argument("id", type=int)

    s.add_parser("types", help="List project types")
    s.add_parser("statuses", help="List project statuses")

    return p


def register_milestones(sub):
    p = sub.add_parser("milestones", help="Milestone commands")
    s = p.add_subparsers(dest="action")

    ls = s.add_parser("list", help="List milestones")
    ls.add_argument("--project-id", type=int, required=True, dest="project_id")

    show = s.add_parser("show", help="Show milestone")
    show.add_argument("--project-id", type=int, required=True, dest="project_id")
    show.add_argument("id", type=int)

    create = s.add_parser("create", help="Create milestone")
    create.add_argument("--project-id", type=int, required=True, dest="project_id")
    create.add_argument("--name", required=True)
    create.add_argument("--finish-date", dest="finish_date")

    edit = s.add_parser("edit", help="Edit milestone")
    edit.add_argument("--project-id", type=int, required=True, dest="project_id")
    edit.add_argument("id", type=int)
    edit.add_argument("--name")
    edit.add_argument("--finish-date", dest="finish_date")

    delete = s.add_parser("delete", help="Delete milestone")
    delete.add_argument("--project-id", type=int, required=True, dest="project_id")
    delete.add_argument("id", type=int)

    return p


def register_work_packages(sub):
    p = sub.add_parser("work-packages", help="Work-package commands")
    s = p.add_subparsers(dest="action")

    ls = s.add_parser("list", help="List work packages")
    ls.add_argument("--project-id", type=int, required=True, dest="project_id")

    show = s.add_parser("show", help="Show work package")
    show.add_argument("--project-id", type=int, required=True, dest="project_id")
    show.add_argument("id", type=int)

    create = s.add_parser("create", help="Create work package")
    create.add_argument("--project-id", type=int, required=True, dest="project_id")
    create.add_argument("--name", required=True)
    create.add_argument("--hours", dest="estimated_hours")

    edit = s.add_parser("edit", help="Edit work package")
    edit.add_argument("--project-id", type=int, required=True, dest="project_id")
    edit.add_argument("id", type=int)
    edit.add_argument("--name")
    edit.add_argument("--hours", dest="estimated_hours")

    delete = s.add_parser("delete", help="Delete work package")
    delete.add_argument("--project-id", type=int, required=True, dest="project_id")
    delete.add_argument("id", type=int)

    return p


# ---------------------------------------------------------------------------
# Handlers
# ---------------------------------------------------------------------------

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
    elif args.action == "archive":
        _archive(args, client, json_flag)
    elif args.action == "reactivate":
        _reactivate(args, client, json_flag)
    elif args.action == "types":
        _types(args, client, json_flag)
    elif args.action == "statuses":
        _statuses(args, client, json_flag)
    else:
        sys.exit("Usage: bexio projects {list|show|search|create|edit|delete|archive|reactivate|types|statuses}")


def handle_milestones(args, client, json_flag):
    if args.action == "list":
        _milestones_list(args, client, json_flag)
    elif args.action == "show":
        _milestones_show(args, client, json_flag)
    elif args.action == "create":
        _milestones_create(args, client, json_flag)
    elif args.action == "edit":
        _milestones_edit(args, client, json_flag)
    elif args.action == "delete":
        _milestones_delete(args, client, json_flag)
    else:
        sys.exit("Usage: bexio milestones {list|show|create|edit|delete}")


def handle_work_packages(args, client, json_flag):
    if args.action == "list":
        _packages_list(args, client, json_flag)
    elif args.action == "show":
        _packages_show(args, client, json_flag)
    elif args.action == "create":
        _packages_create(args, client, json_flag)
    elif args.action == "edit":
        _packages_edit(args, client, json_flag)
    elif args.action == "delete":
        _packages_delete(args, client, json_flag)
    else:
        sys.exit("Usage: bexio work-packages {list|show|create|edit|delete}")


# ---------------------------------------------------------------------------
# Project internals
# ---------------------------------------------------------------------------

def _list(args, client, json_flag):
    projects = client.get("/pr_project", params={"limit": args.limit})
    if not isinstance(projects, list):
        sys.exit(f"Unexpected response: {projects}")
    if json_flag:
        print_json(projects)
        return
    if not projects:
        print("No projects found.")
        return
    for p in projects:
        start = (p.get("start_date") or "")[:10]
        end = (p.get("end_date") or "")[:10]
        print(f"{p['id']:>5}  {p['name'][:48]:<48}  {p.get('pr_state_id', ''):>2}  {start}  {end}")


def _show(args, client, json_flag):
    p = client.get(f"/pr_project/{args.id}")
    if json_flag:
        print_json(p)
        return
    print(f"ID:         {p['id']}")
    print(f"Name:       {p['name']}")
    print(f"Start:      {p.get('start_date', '—')}")
    print(f"End:        {p.get('end_date', '—')}")
    print(f"Status:     {p.get('pr_state_id', '—')}")
    print(f"Type:       {p.get('pr_project_type_id', '—')}")
    print(f"Contact:    {p.get('contact_id', '—')}")
    if p.get("comment"):
        print(f"Comment:    {p['comment']}")


def _search(args, client, json_flag):
    body = [{"field": "name", "value": args.query, "criteria": "like"}]
    projects = client.post("/pr_project/search", body=body)
    if not isinstance(projects, list):
        sys.exit(f"Unexpected response: {projects}")
    if json_flag:
        print_json(projects)
        return
    if not projects:
        print("No projects found.")
        return
    for p in projects:
        start = (p.get("start_date") or "")[:10]
        print(f"{p['id']:>5}  {p['name'][:48]:<48}  {start}")


def _create(args, client, json_flag):
    body = {"name": args.name}
    if args.contact_id is not None:
        body["contact_id"] = args.contact_id
    if args.start_date:
        body["start_date"] = args.start_date
    if args.end_date:
        body["end_date"] = args.end_date
    if args.pr_project_type_id is not None:
        body["pr_project_type_id"] = args.pr_project_type_id
    result = client.post("/pr_project", body=body)
    if json_flag:
        print_json(result)
        return
    print(f"Project {result['id']} created.")


def _edit(args, client, json_flag):
    body = {}
    if args.name:
        body["name"] = args.name
    if args.start_date:
        body["start_date"] = args.start_date
    if args.end_date:
        body["end_date"] = args.end_date
    result = client.put(f"/pr_project/{args.id}", body=body)
    if json_flag:
        print_json(result)
        return
    print(f"Project {args.id} updated.")


def _delete(args, client, json_flag):
    client.delete(f"/pr_project/{args.id}")
    print(f"Project {args.id} deleted.")


def _archive(args, client, json_flag):
    client.post(f"/pr_project/{args.id}/archive")
    print(f"Project {args.id} archived.")


def _reactivate(args, client, json_flag):
    client.post(f"/pr_project/{args.id}/reactivate")
    print(f"Project {args.id} reactivated.")


def _types(args, client, json_flag):
    types = client.get("/pr_project_type")
    if json_flag:
        print_json(types)
        return
    for t in (types if isinstance(types, list) else []):
        print(f"{t['id']:>3}  {t['name']}")


def _statuses(args, client, json_flag):
    statuses = client.get("/pr_project_state")
    if json_flag:
        print_json(statuses)
        return
    for s in (statuses if isinstance(statuses, list) else []):
        print(f"{s['id']:>3}  {s['name']}")


# ---------------------------------------------------------------------------
# Milestone internals
# ---------------------------------------------------------------------------

def _milestones_list(args, client, json_flag):
    path = f"/projects/{args.project_id}/milestones"
    milestones = client._request("GET", path, base=V3)
    if not isinstance(milestones, list):
        sys.exit(f"Unexpected response: {milestones}")
    if json_flag:
        print_json(milestones)
        return
    if not milestones:
        print("No milestones found.")
        return
    for m in milestones:
        print(f"{m['id']:>5}  {m['name'][:48]:<48}  {m.get('finish_date', '')}")


def _milestones_show(args, client, json_flag):
    path = f"/projects/{args.project_id}/milestones/{args.id}"
    m = client._request("GET", path, base=V3)
    if json_flag:
        print_json(m)
        return
    print(f"ID:          {m['id']}")
    print(f"Name:        {m['name']}")
    print(f"Finish date: {m.get('finish_date', '—')}")
    print(f"Project:     {m.get('project_id', '—')}")


def _milestones_create(args, client, json_flag):
    body = {"name": args.name}
    if args.finish_date:
        body["finish_date"] = args.finish_date
    path = f"/projects/{args.project_id}/milestones"
    result = client._request("POST", path, body=body, base=V3)
    if json_flag:
        print_json(result)
        return
    print(f"Milestone {result['id']} created.")


def _milestones_edit(args, client, json_flag):
    body = {}
    if args.name:
        body["name"] = args.name
    if args.finish_date:
        body["finish_date"] = args.finish_date
    path = f"/projects/{args.project_id}/milestones/{args.id}"
    result = client._request("PUT", path, body=body, base=V3)
    if json_flag:
        print_json(result)
        return
    print(f"Milestone {args.id} updated.")


def _milestones_delete(args, client, json_flag):
    path = f"/projects/{args.project_id}/milestones/{args.id}"
    client._request("DELETE", path, base=V3)
    print(f"Milestone {args.id} deleted.")


# ---------------------------------------------------------------------------
# Work-package internals
# ---------------------------------------------------------------------------

def _packages_list(args, client, json_flag):
    path = f"/projects/{args.project_id}/packages"
    packages = client._request("GET", path, base=V3)
    if not isinstance(packages, list):
        sys.exit(f"Unexpected response: {packages}")
    if json_flag:
        print_json(packages)
        return
    if not packages:
        print("No work packages found.")
        return
    for pkg in packages:
        hours = pkg.get("estimated_hours", "")
        print(f"{pkg['id']:>5}  {pkg['name'][:48]:<48}  {hours}")


def _packages_show(args, client, json_flag):
    path = f"/projects/{args.project_id}/packages/{args.id}"
    pkg = client._request("GET", path, base=V3)
    if json_flag:
        print_json(pkg)
        return
    print(f"ID:      {pkg['id']}")
    print(f"Name:    {pkg['name']}")
    print(f"Hours:   {pkg.get('estimated_hours', '—')}")
    print(f"Project: {pkg.get('project_id', '—')}")
    if pkg.get("comment"):
        print(f"Comment: {pkg['comment']}")


def _packages_create(args, client, json_flag):
    body = {"name": args.name}
    if args.estimated_hours:
        body["estimated_hours"] = args.estimated_hours
    path = f"/projects/{args.project_id}/packages"
    result = client._request("POST", path, body=body, base=V3)
    if json_flag:
        print_json(result)
        return
    print(f"Work package {result['id']} created.")


def _packages_edit(args, client, json_flag):
    body = {}
    if args.name:
        body["name"] = args.name
    if args.estimated_hours:
        body["estimated_hours"] = args.estimated_hours
    path = f"/projects/{args.project_id}/packages/{args.id}"
    result = client._request("PUT", path, body=body, base=V3)
    if json_flag:
        print_json(result)
        return
    print(f"Work package {args.id} updated.")


def _packages_delete(args, client, json_flag):
    path = f"/projects/{args.project_id}/packages/{args.id}"
    client._request("DELETE", path, base=V3)
    print(f"Work package {args.id} deleted.")
