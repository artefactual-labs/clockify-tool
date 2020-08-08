from __future__ import print_function
from datetime import date
import shutil
import os
import sys

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir))

from clockifytool import helpers


def list_entries(args, config, app_data):
    today_raw = date.today()
    today = today_raw.strftime('%Y-%m-%d')

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
        from_date = period['start']
        to_date = period['end']

    helpers.time_entry_list(from_date, to_date, app_data['clockify'], args.strict, args.verbose)


def new_entry(args, config, app_data):
    if 'hours' not in args or not args.hours:
        print('Specify hours.')
        return

    if float(args.hours) <= 0:
        print('Hours value must be positive.')
        return

    # Check if ID indicates a task rather than project
    task_id = None
    project_id = app_data['clockify'].get_task_project_id(args.id)

    if project_id is None:
        project_id = args.id
    else:
        task_id = args.id

    entry = app_data['clockify'].create_entry(project_id, args.comments, args.hours, args.date, args.start, args.billable, task=task_id)

    if 'message' in entry and 'code' in entry:
        print(entry['message'])
        return

    print(helpers.entry_bullet_point(app_data['clockify'], entry))
    print("Time entry created.")


def update_entry(args, config, app_data):
    changed = False

    # Need to use cached time entry data because API doesn't support getting time entry data by ID
    cached_entry = app_data['clockify'].cache.get_cached_entry(args.id)

    if not cached_entry:
        print('Time entry does not exist or is not cached.')
        return

    # Establish entry hours
    cached_hours = app_data['clockify'].cache.iso_duration_to_hours(cached_entry['timeInterval']['duration'])
    updated_hours = cached_hours

    # Adjust hours, if necessary
    if args.hours and (helpers.contains_calculation(args.hours) or cached_hours != float(args.hours)):
        changed = True
        updated_hours = helpers.handle_hours_calculation_value(float(cached_hours), args.hours)
        print("Changing hours from {} to: {}".format(str(cached_hours), str(updated_hours)))

    updated_entry = app_data['clockify'].cache.generate_update_entry(args.id, comments=args.comments, date=args.date, hours=updated_hours)

    # Update description, if necessary
    if args.comments and args.comments != cached_entry['description']:
        changed = True
        print("Changing comments to: {}".format(args.comments))

    # Append to description, if necesary
    if args.append:
        changed = True
        updated_entry['description'] += ' ' + args.append
        print("Appended to comments: {}".format(args.append))

    # Update start date, if necessary
    if args.date:
        cached_date_local = app_data['clockify'].utc_iso_8601_string_to_local_datetime(cached_entry['timeInterval']['start'])
        update_date_local = app_data['clockify'].utc_iso_8601_string_to_local_datetime(updated_entry['start'])

        if cached_date_local.date() != update_date_local.date():
            changed = True
            print("Changing date to {}".format(args.date))

    # Update billable status, if necessary
    if args.billable and not cached_entry['billable']:
        updated_entry['billable'] = True
        changed = True
        print('Setting to billable.')

    if args.unbillable and cached_entry['billable']:
        updated_entry['billable'] = False
        changed = True
        print('Setting to unbillable.')

    if changed:
        # Perform update via API
        response = app_data['clockify'].update_entry(updated_entry, cached_entry)

        if response.status_code == 200:
            print(helpers.entry_bullet_point(app_data['clockify'], cached_entry))
            print('Time entry updated.')
        else:
            response_data = response.json()
            print('Unexpected response status code: ' + str(response.status_code))
            if 'message' in response_data:
                print('Message: ' + response_data['message'])
    else:
        print('No update as no change requested.')


def delete_entry(args, config, app_data):
    response = app_data['clockify'].delete_entry(args.id)

    if response.status_code == 204:

        cache_filepath = app_data['clockify'].cache.get_cache_filepath(args.id)

        if os.path.isfile(cache_filepath):
            os.remove(cache_filepath)

        print('Time entry deleted.')
    else:
        print('Time entry not found.')


def list_workspaces(args, config, app_data):
    for workspace in app_data['clockify'].workspaces():
        print('* {} [{}]'.format(workspace['name'], workspace['id']))


def list_projects(args, config, app_data):
    project_names = []
    project_data = {}

    for project in app_data['clockify'].projects():
        project_names.append(project['name'])
        project_data[(project['name'])] = project

    project_names.sort()
    for project in project_names:
        print('* {} [{}]'.format(project.encode('utf-8'), project_data[project]['id']))


def cache_statistics(args, config, app_data):
    cache_dir = os.path.join(app_data['clockify'].cache.get_cache_directory())

    cache_files = [f for f in os.listdir(cache_dir) if os.path.isfile(os.path.join(cache_dir, f))]

    if (len(cache_files)):
        print('Cached time entries: {}'.format(str(len(cache_files))))

        if 'flush' in args and args.flush:
            print('Cache flushed.')
            shutil.rmtree(cache_dir)
    else:
        print('Cache is empty.')


def project_details(args, config, app_data):
    project_data = app_data['clockify'].get_project(args.id)

    print("Name: {}".format(project_data['name']))

    if 'clientName' in project_data:
        print("Client: {}".format(project_data['clientName']))

    print()
    print("Tasks:")

    for project in app_data['clockify'].project_tasks(args.id):
        print('* {} [{}]'.format(project['name'].encode('utf-8'), project['id']))


def task_details(args, config, app_data):
    project_id = app_data['clockify'].get_task_project_id(args.id)
    print("Project ID: {}".format(project_id))
