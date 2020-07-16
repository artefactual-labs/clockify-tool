from __future__ import print_function
from __future__ import unicode_literals
from builtins import str
import calendar
import collections
from datetime import date, datetime, timedelta
import dateutil.parser


PERIODS = collections.OrderedDict()

PERIODS['y'] = {'name': 'yesterday', 'description': 'day before today'}
PERIODS['dby'] = {'name': 'daybeforeyesterday', 'description': 'day before yesterday'}
PERIODS['lw'] = {'name': 'lastweek', 'description': 'last work week (Monday to Friday)'}
PERIODS['cw'] = {'name': 'currentweek', 'description': 'current work week (Monday to Friday)'}
PERIODS['flw'] = {'name': 'fulllastweek', 'description': 'last full week (Sunday to Saturday)'}
PERIODS['fcw'] = {'name': 'fullcurrentweek', 'description': 'current full week (Sunday to Saturday)'}
PERIODS['lm'] = {'name': 'lastmonth', 'description': 'last month'}
PERIODS['cm'] = {'name': 'currentmonth', 'description': 'current month'}
PERIODS['ly'] = {'name': 'lastyear', 'description': 'last year'}
PERIODS['cy'] = {'name': 'currentyear', 'description': 'current year'}
PERIODS['mon'] = {'name': 'monday', 'description': 'Monday'}
PERIODS['tue'] = {'name': 'tuesday', 'description': 'Tuesday'}
PERIODS['wed'] = {'name': 'wednesday', 'description': 'Wednesday'}
PERIODS['thu'] = {'name': 'thursday', 'description': 'Thursday'}
PERIODS['fri'] = {'name': 'friday', 'description': 'Friday'}
PERIODS['sat'] = {'name': 'saturday', 'description': 'Saturday'}
PERIODS['sun'] = {'name': 'sunday', 'description': 'Sunday'}
PERIODS['lmon'] = {'name': 'lastmonday', 'description': 'Last Monday'}
PERIODS['ltue'] = {'name': 'lasttuesday', 'description': 'Last Tuesday'}
PERIODS['lwed'] = {'name': 'lastwednesday', 'description': 'Last Wednesday'}
PERIODS['lthu'] = {'name': 'lastthursday', 'description': 'Last Thursday'}
PERIODS['lfri'] = {'name': 'lastfriday', 'description': 'Last Friday'}
PERIODS['lsat'] = {'name': 'lastsaturday', 'description': 'Last Saturday'}
PERIODS['lsun'] = {'name': 'lastsunday', 'description': 'Last Sunday'}
PERIODS['cp'] = {'name': 'currentpayperiod', 'description': 'current pay period'}
PERIODS['pp'] = {'name': 'previouspayperiod', 'description': 'previous pay period'}


# Artefactual's pay period details
PERIOD_DAYS = 14
PERIOD_FIRST_DAY = date(2019, 7, 6)  # Known first day of period.


def time_entry_list(from_date, to_date, clockify, strict=False, verbose=False):
    from_date_description = '{} ({})'.format(from_date, date_string_to_weekday_string(from_date))
    to_date_description = '{} ({})'.format(to_date, date_string_to_weekday_string(to_date))

    if from_date == to_date:
        print("Fetching time entries from {}...".format(from_date_description))
    else:
        print("Fetching time entries from {} to {}...".format(from_date_description, to_date_description))
    print()

    # Get yesterday's time entries
    time_entries = clockify.entries(start=from_date + 'T00:00:00', end=to_date + 'T23:59:59', strict=strict)

    if time_entries:
        sum = 0

        # Print time entries
        report = "Time entries:\n"

        for entry in time_entries:
            report += entry_bullet_point(clockify, entry, verbose)
            sum += clockify.cache.iso_duration_to_hours(entry['timeInterval']['duration'])

        report += "\n" + str(sum) + " hours.\n"
    else:
        report = "No time entries.\n"

    print(report)


def entry_bullet_point(clockify, entry, verbose=False):
    item = '* '

    if verbose:
        local_date_and_time = clockify.cache.utc_iso_8601_string_to_local_datatime_string(entry['timeInterval']['start'])
        item += '{} - '.format(str(local_date_and_time))

    item += '{}'.format(str(entry['description']))

    if 'project' in entry and 'name' in entry['project']:
        if 'task' in entry and entry['task'] is not None and 'name' in entry['task']:
            if verbose:
                item = item + ' ({}: {} / task: {}: {})'.format(entry['project']['name'], entry['project']['id'], entry['task']['name'], entry['task']['id'])
            else:
                item = item + ' (task: {}:{})'.format(entry['task']['name'], entry['task']['id'])
        else:
            item = item + ' ({}: {})'.format(entry['project']['name'], entry['project']['id'])

    hours = clockify.cache.iso_duration_to_hours(entry['timeInterval']['duration'])
    item = item + ' [{} hours: {}'.format(hours, entry['id'])

    if entry['billable']:
        item = item + ', billable'

    item = item + ']'

    return item + "\n"


def contains_calculation(value):
    return value[:1] == '+' or value[:1] == '-'


def handle_date_calculation_value(date_value):
    if date_value == 'today':
        date_value = '+0'

    if contains_calculation(date_value):
        date_value_raw = date.today() + timedelta(int(date_value))
        date_value = date_value_raw.strftime('%Y-%m-%d')

    return date_value


def handle_hours_calculation_value(current_hours, new_value_or_calculation):
    if contains_calculation(new_value_or_calculation):
        current_hours += float(new_value_or_calculation)
    else:
        current_hours = float(new_value_or_calculation)

    return current_hours


def date_string_to_weekday_string(date_string):
    return dateutil.parser.parse(date_string).strftime('%A')


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

    if period == 'daybeforeyesterday':
        yesterday = handle_date_calculation_value('-2')
        return {'start': yesterday, 'end': yesterday}

    if period == 'lastweek':
        start_date = weekday_last_week(0)  # last Monday
        end_date = weekday_last_week(4)  # last Friday

    if period == 'currentweek':
        start_date = weekday_of_week(0)  # this Monday
        end_date = weekday_of_week(4)  # this Friday

    if period == 'fulllastweek':
        start_date = weekday_of_week(6, 2)  # last Sunday
        end_date = weekday_of_week(5, 1)  # last Saturday

    if period == 'fullcurrentweek':
        start_date = weekday_last_week(6)  # this Sunday
        end_date = weekday_of_week(5)  # this Saturday

    if period == 'monday':
        start_date = weekday_of_week(0)  # this Monday
        end_date = start_date

    if period == 'tuesday':
        start_date = weekday_of_week(1)  # this Tuesday
        end_date = start_date

    if period == 'wednesday':
        start_date = weekday_of_week(2)  # this Wednesday
        end_date = start_date

    if period == 'thursday':
        start_date = weekday_of_week(3)  # this Thursday
        end_date = start_date

    if period == 'friday':
        start_date = weekday_of_week(4)  # this Friday
        end_date = start_date

    if period == 'saturday':
        start_date = weekday_of_week(5)  # this Saturday
        end_date = start_date

    if period == 'sunday':
        start_date = weekday_of_week(6)  # last Sunday
        end_date = start_date

    if period == 'lastmonday':
        start_date = weekday_last_week(0)  # last Monday
        end_date = start_date

    if period == 'lasttuesday':
        start_date = weekday_last_week(1)  # last Tuesday
        end_date = start_date

    if period == 'lastwednesday':
        start_date = weekday_last_week(2)  # last Wednesday
        end_date = start_date

    if period == 'lastthursday':
        start_date = weekday_last_week(3)  # last Thursday
        end_date = start_date

    if period == 'lastfriday':
        start_date = weekday_last_week(4)  # last Friday
        end_date = start_date

    if period == 'lastsaturday':
        start_date = weekday_last_week(5)  # last Saturday
        end_date = start_date

    if period == 'lastsunday':
        start_date = weekday_last_week(6)  # Sunday before last Sunday
        end_date = start_date

    today = date.today()

    if period == 'lastmonth':
        first = today.replace(day=1)
        last_month = first - timedelta(days=1)
        last_year_and_month = last_month.strftime("%Y-%m")

        start_date = last_year_and_month + '-01'
        end_date = last_year_and_month + '-' + str(last_month.day)

    if period == 'currentmonth':
        year_and_month = datetime.today().strftime('%Y-%m')
        start_date = year_and_month + '-01'

        _, days_in_month = calendar.monthrange(today.year, today.month)
        end_date = year_and_month + '-' + str(days_in_month)

    if period == 'lastyear':
        start_date = '{}-01-01'.format(str(today.year - 1))
        end_date = '{}-12-31'.format(str(today.year - 1))

    if period == 'currentyear':
        start_date = '{}-01-01'.format(str(today.year))
        end_date = '{}-12-31'.format(str(today.year))

    # Payroll periods
    if period.endswith('payperiod'):
        past_days = (today - PERIOD_FIRST_DAY).days % PERIOD_DAYS

        if period == 'currentpayperiod':
            start_date = today - timedelta(days=past_days)
            end_date = today + timedelta(days=PERIOD_DAYS - past_days - 1)
        elif period == 'previouspayperiod':
            end_date = today - timedelta(days=past_days + 1)
            start_date = end_date - timedelta(days=PERIOD_DAYS - 1)

        return {
            'start': start_date.strftime("%Y-%m-%d"),
            'end': end_date.strftime("%Y-%m-%d")
        }

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


def describe_periods():
    description = 'Available periods: '
    first = True

    for abbreviation, period in PERIODS.items():
        if not first:
            description += ', '

        description += '"{}" ("{}"): {}'.format(period['name'], abbreviation, period['description'])

        first = False

    return description
