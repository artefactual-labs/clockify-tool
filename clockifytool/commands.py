import os
import shutil
import sys
from datetime import date

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir))

from clockifytool import helpers


def list_entries(args, config, app_data):
    today_raw = date.today()
    today = today_raw.strftime("%Y-%m-%d")

    if args.start or args.end:
        # Handle --start and --end
        if args.start and not args.end:
            from_date = args.start

            if from_date < today:
                to_date = today
            else:
                to_date = from_date
        elif not args.start and args.end:
            to_date = args.end

            if to_date > today:
                from_date = today
            else:
                from_date = to_date
        else:
            from_date = args.start
            to_date = args.end
    else:
        # List defaults to current day
        from_date = today
        to_date = today

    # Periods will override --from and --to
    if args.period and helpers.resolve_period(args.period):
        period = helpers.resolve_period(args.period)
        from_date = period["start"]
        to_date = period["end"]

    helpers.time_entry_list(
        from_date, to_date, app_data["clockify"], args.strict, args.verbose
    )


def new_entry(args, config, app_data):
    if "hours" not in args or not args.hours:
        print("Specify hours.")
        return

    if float(args.hours) <= 0:
        print("Hours value must be positive.")
        return

    # Check if ID indicates a task rather than project
    task_id = None
    project_id = None

    task = app_data["clockify"].cache.get_cached_entry(args.id, "task")

    # If task hasn't been cached, cache all project tasks
    if task is None:
        helpers.cache_workspace_tasks(app_data["clockify"])
        task = app_data["clockify"].cache.get_cached_entry(args.id, "task")

    if task is not None:
        project_id = task["projectId"]

    if project_id is None:
        project_id = args.id
    else:
        task_id = args.id

    # Set start time to default if date's different than current
    today_raw = date.today()
    today = today_raw.strftime("%Y-%m-%d")

    if args.date is not None and args.date != today and args.start is None:
        args.start = "08:00:00"

    entry = app_data["clockify"].create_entry(
        project_id,
        args.comments,
        args.hours,
        args.date,
        args.start,
        args.billable,
        task=task_id,
    )

    if "message" in entry and "code" in entry:
        print(entry["message"])
        return

    print(helpers.entry_bullet_point(app_data["clockify"], entry))
    print("Time entry created.")


def delete_entry(args, config, app_data):
    response = app_data["clockify"].delete_entry(args.id)

    if response.status_code == 204:
        cache_filepath = app_data["clockify"].cache.get_cache_filepath(args.id)

        if os.path.isfile(cache_filepath):
            os.remove(cache_filepath)

        print("Time entry deleted.")
    else:
        print("Time entry not found.")


def list_workspaces(args, config, app_data):
    for workspace in app_data["clockify"].workspaces():
        print("* {} [{}]".format(workspace["name"], workspace["id"]))


def list_projects(args, config, app_data):
    project_names = []
    project_data = {}

    for project in app_data["clockify"].projects(args.limit):
        project_names.append(project["name"])
        project_data[(project["name"])] = project

    project_names.sort()
    for project in project_names:
        print("* {} [{}]".format(project.encode("utf-8"), project_data[project]["id"]))


def cache_statistics(args, config, app_data):
    cache_dir = os.path.join(app_data["clockify"].cache.get_cache_directory())

    cache_files = [
        f for f in os.listdir(cache_dir) if os.path.isfile(os.path.join(cache_dir, f))
    ]

    if len(cache_files):
        print("Cached time entries: {}".format(str(len(cache_files))))

        if "flush" in args and args.flush:
            print("Cache flushed.")
            shutil.rmtree(cache_dir)
    else:
        print("Cache is empty.")


def project_details(args, config, app_data):
    project_data = app_data["clockify"].get_project(args.id)

    if "message" in project_data:
        print(project_data["message"])
        return

    print("Name: {}".format(project_data["name"]))

    if "clientName" in project_data:
        print("Client: {}".format(project_data["clientName"]))

    print()
    print("Tasks:")

    for project in app_data["clockify"].project_tasks(args.id):
        print("* {} [{}]".format(project["name"].encode("utf-8"), project["id"]))


def task_details(args, config, app_data):
    task = app_data["clockify"].cache.get_cached_entry(args.id, "task")

    # If task hasn't been cached, cache all project tasks
    if task is None:
        helpers.cache_workspace_tasks(app_data["clockify"])
        task = app_data["clockify"].cache.get_cached_entry(args.id, "task")

    if task is None:
        print("Task not found.")
    else:
        print("Name: {}".format(task["name"]))
        print("Project ID: {}".format(task["projectId"]))
