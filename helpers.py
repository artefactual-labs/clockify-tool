from __future__ import print_function
from datetime import date, datetime, timedelta
import json
import os
import tempfile
import isodate


PERIODS = {
  'y': {'name': 'yesterday', 'description': 'day before today'},
  'lw': {'name': 'lastweek', 'description': 'last work week (Monday to Friday)'},
  'cw': {'name': 'currentweek', 'description': 'current work week (Monday to Friday)'},
  'flw': {'name': 'fulllastweek', 'description': 'last full week (Sunday to Saturday)'},
  'fcw': {'name': 'fullcurrentweek', 'description': 'current full week (Sunday to Saturday)'}
}


def time_entry_list(from_date, to_date, clockify):
    print("Fetching time entries from {} to {}...".format(from_date, to_date))
    print()

    # Get yesterday's time entries
    time_entries = clockify.entries(start=from_date + 'T00:00:00', end=to_date + 'T23:59:59')

    if time_entries:
        sum = 0

        # Print time entries
        report = "Time entries:\n"

        for entry in time_entries:
            # Cache entry in case user wants to update event
            write_cache_entry(entry)

            report += entry_bullet_point(entry)
            sum += iso_duration_to_hours(entry['timeInterval']['duration'])

        report += "\n" + str(sum) + " hours.\n"
    else:
        report = "No time entries.\n"

    print(report)


def entry_bullet_point(entry):
    item = '* {}'.format(entry['description'])

    if 'project' in entry and 'name' in entry['project']:
        item = item + ' ({}: {})'.format(entry['project']['name'], entry['project']['id'])

    hours = iso_duration_to_hours(entry['timeInterval']['duration'])
    item = item + ' [{} hours: {}]'.format(hours, entry['id'])

    return item + "\n"


def iso_duration_to_hours(duration):
    minutes = isodate.parse_duration(duration).total_seconds() / 60
    return minutes / 60


def hours_to_iso_duration(hours):
    duration = timedelta(hours=1.5)
    return isodate.duration_isoformat(duration)


def handle_date_calculation_value(date_value):
    if date_value[:1] == '+' or date_value[:1] == '-':
        date_value_raw = date.today() + timedelta(int(date_value))
        date_value = date_value_raw.strftime('%Y-%m-%d')

    return date_value


def weekday_of_week(day_of_week, weeks_previous=0):
    days_ahead_of_weekday_last_week = date.today().weekday() + (weeks_previous * 7) - day_of_week
    last_weekday = datetime.now() - timedelta(days=days_ahead_of_weekday_last_week)
    return last_weekday.strftime("%Y-%m-%d")


def weekday_last_week(day_of_week):
    return weekday_of_week(day_of_week, 1)


def resolve_period_abbreviation(period):
    period = period.lower()

    if period in PERIODS:
        return PERIODS[period]['name']

    if period in {abbr: item.get('name') for abbr, item in PERIODS.items()}.values():
        return period

    return None


def resolve_period(period):
    if period == 'yesterday':
        yesterday = handle_date_calculation_value('-1')
        return {'start': yesterday, 'end': yesterday}

    if period == 'lastweek':
        start_date = weekday_last_week(0)  # last Monday
        end_date = weekday_last_week(4)  # last Friday
        return {'start': start_date, 'end': end_date}

    if period == 'currentweek':
        start_date = weekday_of_week(0)  # this Monday
        end_date = weekday_of_week(4)  # this Friday
        return {'start': start_date, 'end': end_date}

    if period == 'fulllastweek':
        start_date = weekday_of_week(6, 2)  # last Sunday
        end_date = weekday_of_week(5, 1)  # last Saturday
        return {'start': start_date, 'end': end_date}

    if period == 'fullcurrentweek':
        start_date = weekday_last_week(6)  # this Sunday
        end_date = weekday_of_week(5)  # this Saturday
        return {'start': start_date, 'end': end_date}


def resolve_project_template(project_name, templates):
    if project_name in templates:
        return templates[project_name]


def template_field(issue_name, field, templates):
    template = resolve_project_template(issue_name, templates)
    if template and field in template:
        return template[field]


def resolve_project_alias(issue_id, templates):
    resolved_id = template_field(issue_id, 'id', templates)

    if resolved_id:
        return resolve_project_alias(resolved_id, templates)
    else:
        return issue_id


def get_cache_directory():
    cache_dir = os.path.join(tempfile.gettempdir(), 'cft')

    if not os.path.isdir(cache_dir):
        os.mkdir(cache_dir)

    return cache_dir


def get_cache_filepath(identifier):
    return os.path.join(get_cache_directory(), 'cft-{}'.format(identifier))


def write_cache_entry(entry):
    filepath = get_cache_filepath(entry['id'])

    if os.path.isfile(filepath):
        os.remove(filepath)

    with open(filepath, 'w') as cache_file:
        cache_file.write(json.dumps(entry))


def get_cached_entry(identifier):
    filepath = get_cache_filepath(identifier)

    if not os.path.isfile(filepath):
        return

    with open(get_cache_filepath(identifier)) as json_file:
        return json.load(json_file)


def describe_periods():
    description = 'Available periods: '
    first = True

    for abbreviation, period in PERIODS.items():
        if not first:
            description += ', '

        description += '"{}" ("{}"): {}'.format(period['name'], abbreviation, period['description'])

        first = False

    return description
