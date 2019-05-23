from __future__ import print_function
import os
import yaml
import helpers


def load_config():
    """Return configuration, from YAML file, for this application.
    Raises:
        Exception: If not able to read or parse the configuration file for any
                   reason or if "base branch" isn't set in the configuration
                   file.
    Returns:
        dict: Configuration information.
    """
    config_filename = '.cft.yml'

    # Attempt to load configuration file from user's home directory
    config_path = os.path.join(os.path.expanduser('~'), config_filename)

    try:
        config = yaml.safe_load(open(config_path))
    except IOError:
        raise Exception('Unable to load ~/{}: does it exist (or is there a YAML error)?'.format(config_filename))

    # Add config filename to config
    config['filename'] = config_filename

    # Verify Clockify API key has been set in the config file
    if 'api key' not in config:
        raise Exception('Please set Clockify API key as "api key" in {}.'.format(config_filename))

    return config


def time_entry_list(from_date, to_date, user, redmine):
    print("Fetching time entries from {} to {} for {}...".format(from_date, to_date, user))
    print()

    # Get yesterday's time entries
    time_entries = redmine.time_entry.filter(user_id=user.id, from_date=from_date, to_date=to_date, sort='hours:desc')

    if time_entries:
        sum = 0

        # Print scrum update template
        report = "Time entries:\n"

        for entry in time_entries:
            report += helpers.entry_bullet_point(entry)
            sum += entry.hours

        report += "\n" + str(sum) + " hours.\n"
    else:
        report = "No time entries.\n"

    print(report)
