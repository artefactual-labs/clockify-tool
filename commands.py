from __future__ import print_function
from datetime import date
import dateutil
import isodate
import helpers


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

    helpers.time_entry_list(from_date, to_date, app_data['clockify'])


def new_entry(args, config, app_data):
    if 'hours' not in args or not args.hours:
        print('Specifiy hours.')
        return

    entry = app_data['clockify'].create_entry(args.id, args.comments, args.hours, args.date)

    if 'message' in entry and 'code' in entry:
        print(entry['message'])
        return

    print(helpers.entry_bullet_point(entry))

    print("Time entry created.")


def update_entry(args, config, app_data):
    changed = False

    # Need to use cached time entry data because API doesn't support getting time entry data by ID
    cached_entry = helpers.get_cached_entry(args.id)

    if not cached_entry:
        print('Time entry does not exist or is not cached.')
        return

    # Change TimeEntrySummaryDto to work as UpdateTimeEntryRequest format (see Clockify API documentation)
    entry = {}
    entry['id'] = cached_entry['id']
    entry['description'] = cached_entry['description']
    entry['start'] = cached_entry['timeInterval']['start']
    entry['end'] = cached_entry['timeInterval']['end']
    entry['projectId'] = cached_entry['project']['id']
    entry['billable'] = cached_entry['billable']
    entry['tagIds'] = []

    if 'task' in cached_entry and cached_entry['task']:
        entry['taskId'] = cached_entry['task']['id']

    if 'tags' in cached_entry and cached_entry['tags']:
        for tag in cached_entry['tags']:
            entry['tagIds'].append(tag['id'])

    # Update description, if necessary
    if args.comments and args.comments != entry['description']:
        changed = True

        entry['description'] = args.comments
        cached_entry['description'] = args.comments
        print('Changing comments to: ' + args.comments)

    # Establish entry hours
    current_hours = helpers.iso_duration_to_hours(cached_entry['timeInterval']['duration'])

    if args.hours and (args.hours[:1] == '+' or args.hours[:1] == '-' or current_hours != float(args.hours)):
        changed = True

        original_hours = current_hours

        if args.hours[:1] == '+':
            current_hours += float(args.hours[1:])
        elif args.hours[:1] == '-':
            current_hours -= float(args.hours[1:])
        else:
            current_hours = float(args.hours)

        print('Changing hours from ' + str(original_hours) + ' to: ' + str(current_hours))

    # Change UTC start date/time, if necessary
    if args.date:
        # Convert entry date to simple sting in local timezone
        original_date_localized = dateutil.parser.parse(entry['start']).astimezone(app_data['clockify'].tz)
        original_date = original_date_localized.strftime('%Y-%m-%d')

        if original_date != args.date:
            changed = True

            # Convert new date to UTC ISO 8601
            entry['start'] = app_data['clockify'].local_date_string_to_utc_iso_8601(args.date)
            cached_entry['timeInterval']['start'] = entry['start']

            print('Changing activies from ' + original_date + ' to ' + args.date)

    # Convert UTC start/time to localized datetime and use it to calculate ISO 8601 end date/time
    start_datetime = dateutil.parser.parse(entry['start'])
    entry['end'] = app_data['clockify'].add_hours_to_localized_datetime_and_convert_to_iso_8601(start_datetime, current_hours)

    cached_entry['timeInterval']['duration'] = isodate.duration_isoformat(dateutil.parser.parse(entry['end']) - dateutil.parser.parse(entry['start']))
    cached_entry['timeInterval']['end'] = entry['end']

    if changed:
        # Perform update via API
        response = app_data['clockify'].update_entry(entry)

        if response.status_code == 200:
            helpers.write_cache_entry(cached_entry)
            print(helpers.entry_bullet_point(cached_entry))
            print('Time entry updated.')
        else:
            response_data = response.json()
            print('Unexpected response status code: ' + str(response.status_code))
            if 'message' in response_data:
                print('Message: ' + response_data['message'])
    else:
        print('No update as no change requested.')


def delete_entry(args, config, app_data):
    app_data['clockify'].delete_entry(args.id)
    print('Time entry deleted.')


def list_workspaces(args, config, app_data):
    for workspace in app_data['clockify'].workspaces():
        print('* {} [{}]'.format(workspace['name'], workspace['id']))


def list_projects(args, config, app_data):
    for project in app_data['clockify'].projects():
        print('* {} [{}]'.format(project['name'].encode('utf-8'), project['id']))
