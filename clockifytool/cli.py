import argparse
import dateutil
import os
import sys

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir))

from clockifytool import helpers


def preprocess_argv():
    # Remove script from argv
    argv = sys.argv[1:]

    if len(argv):
        command_abbreviations = {
            'l': 'list',
            'n': 'new',
            'u': 'update',
            'd': 'delete',
            'w': 'workspaces',
            'p': 'projects',
            'pd': 'project',
            'td': 'task',
            '-v': 'version',
            '--version': 'version'
        }

        if argv[0] in command_abbreviations:
            # Expand command abbreviation
            argv[0] = command_abbreviations[argv[0]]
        elif argv[0][0:1] == '+':
            # "+<project>" is shorthand for "new <project>"
            argv = ['new', argv[0][1:]] + argv[1:]
        elif helpers.resolve_period_abbreviation(argv[0]):
            # If time period given, not command, use as basis for list command
            argv = ['list'] + argv[0:]
    else:
        # Default to "list" command
        argv = ['list']

    return argv


def arg_parser():
    """Return ArgumentParser for this application."""
    parser = argparse.ArgumentParser(description='Clockify client.')
    parser.add_argument('-v', '--version', help='show version and exit', action='store_true')

    subparsers = parser.add_subparsers(dest='command')

    # Parent parser for entry-specific commands
    entry_parser = argparse.ArgumentParser(add_help=False)
    entry_parser.add_argument('-c', '--comments', metavar='comments: required for new time entries', action='store')
    entry_parser.add_argument('-t', '--hours', metavar='hours spent: required for new time entries', action='store')
    entry_parser.add_argument('-d', '--date', metavar='date', action='store', help='defaults to today')
    entry_parser.add_argument('-b', '--billable', action='store_true')

    # New entry command
    parser_new = subparsers.add_parser('new', help='Create new time entry', parents=[entry_parser])
    parser_new.add_argument('id', metavar='project ID', help='ID of project or task: required')
    parser_new.add_argument('-s', '--start', metavar='start time', action='store')
    parser_new.set_defaults(func='new_entry')

    # Update entry command
    parser_update = subparsers.add_parser('update', help='Update time entry', parents=[entry_parser])
    parser_update.add_argument('id', metavar='entry ID', help='ID of time entry: required')
    parser_update.add_argument('-a', '--append', metavar='append: append text to comments', action='store')
    parser_update.add_argument('-u', '--unbillable', action='store_true')
    parser_update.set_defaults(func='update_entry')

    # List command
    parser_list = subparsers.add_parser('list', help='List time entries', epilog=helpers.describe_periods())
    parser_list.add_argument('period', nargs='?', metavar='period', help='time period: optional, overrides -s and -e')
    parser_list.add_argument('-s', '--start', metavar='start date', action='store')
    parser_list.add_argument('-e', '--end', metavar='end date', action='store')
    parser_list.add_argument('--strict', action='store_true')
    parser_list.add_argument('-v', '--verbose', action='store_true')
    parser_list.set_defaults(func='list_entries')

    # Delete command
    parser_delete = subparsers.add_parser('delete', help='Delete time entry')
    parser_delete.add_argument('id', metavar='time entry ID', help='ID of time entry: required')
    parser_delete.set_defaults(func='delete_entry')

    # Workspaces command
    parser_workspaces = subparsers.add_parser('workspaces', help='List workspaces')
    parser_workspaces.set_defaults(func='list_workspaces')

    # Projects command
    parser_projects = subparsers.add_parser('projects', help='List projects')
    parser_projects.set_defaults(func='list_projects')

    # Project details command
    parser_project = subparsers.add_parser('project', help='Project details')
    parser_project.add_argument('id', metavar='project ID', help='ID of project: required')
    parser_project.set_defaults(func='project_details')

    # Task details command
    parser_task = subparsers.add_parser('task', help='Task details')
    parser_task.add_argument('id', metavar='task ID', help='ID of task: required')
    parser_task.set_defaults(func='task_details')

    # Cache command
    parser_cache = subparsers.add_parser('cache', help='Cache status/management')
    parser_cache.add_argument('-f', '--flush', action='store_true')
    parser_cache.set_defaults(func='cache_statistics')

    # Version commmand
    parser_version = subparsers.add_parser('version', help='Display version')

    return parser


def validate_args(parser, args, config):
    # Normalize and validate period
    if 'period' in args and args.period:
        args.period = helpers.resolve_period_abbreviation(args.period)
        if not args.period:
            parser.error('Invalid period.')

    # Normalize and validate project/entry ID
    if 'id' in args and args.id:
        if args.command == 'new':
            # Allow use of preset comments and/or hours
            default_comments = helpers.template_field(args.id, 'comments', config['projects'])
            default_hours = helpers.template_field(args.id, 'hours', config['projects'])

            if default_comments and not args.comments:
                args.comments = default_comments

            if default_hours and not args.hours:
                args.hours = default_hours

        # Resolve preset name to ID
        args.id = helpers.resolve_project_alias(args.id, config['projects'])

    # Resolve dates, if set
    if 'date' in args and args.date:
        args.date = resolve_and_validate_date_value(args.date, parser)

    if 'start' in args and args.start:
        args.start = resolve_and_validate_date_value(args.start, parser)

    if 'end' in args and args.end:
        args.end = resolve_and_validate_date_value(args.end, parser)

    # Don't allow both billable and unbillable options to be used at the same time
    if ('billable' in args and args.billable) and ('unbillable' in args and args.unbillable):
        parser.error("Both --billable and --unbillable can't be used at the same time.")

    # Sanity-check hours, if set
    if 'hours' in args and args.hours:
        try:
            float(args.hours)
        except ValueError:
            parser.error('Invalid hours value.')

    return args


def resolve_and_validate_date_value(value, parser):
    # Resolve date calculation
    value = helpers.handle_date_calculation_value(value)

    # Make sure value is actually a date
    try:
        dateutil.parser.parse(value)
    except ValueError:
        parser.error('{} is not a valid date.'.format(value))

    return value
