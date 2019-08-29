from datetime import datetime, timedelta
import dateutil.parser
import json
import os
import pytz
import tempfile
import isodate
import requests
from tzlocal import get_localzone


class ClockifyEntryCacheManager:

    def get_cache_directory(self):
        cache_dir = os.path.join(tempfile.gettempdir(), 'cft')

        if not os.path.isdir(cache_dir):
            os.mkdir(cache_dir)

        return cache_dir

    def get_cache_filepath(self, identifier):
        return os.path.join(self.get_cache_directory(), 'cft-{}'.format(identifier))

    def create_from_entry(self, entry):
        filepath = self.get_cache_filepath(entry['id'])

        if os.path.isfile(filepath):
            os.remove(filepath)

        with open(filepath, 'w') as cache_file:
            cache_file.write(json.dumps(entry))

    def create_from_new_entry_response(self, response_data):
        cached_entry = response_data.copy()

        cached_entry['project'] = {'id': cached_entry['projectId']}
        del cached_entry['projectId']
        cached_entry['tags'] = None
        del cached_entry['tagIds']
        cached_entry['task'] = None
        del cached_entry['taskId']

        self.create_from_entry(cached_entry)

    def generate_update_entry(self, entry_id, comments=None, date=None):
        # Need to use cached time entry data because API doesn't support getting time entry data by ID
        cached_entry = self.get_cached_entry(entry_id)

        if not cached_entry:
            return

        # Change TimeEntrySummaryDto to work as UpdateTimeEntryRequest format (see Clockify API documentation)
        updated_entry = {}
        updated_entry['id'] = cached_entry['id']
        updated_entry['description'] = cached_entry['description']
        updated_entry['start'] = cached_entry['timeInterval']['start']
        updated_entry['end'] = cached_entry['timeInterval']['end']
        updated_entry['projectId'] = cached_entry['project']['id']
        updated_entry['billable'] = cached_entry['billable']
        updated_entry['tagIds'] = []

        if 'task' in cached_entry and cached_entry['task']:
            updated_entry['taskId'] = cached_entry['task']['id']

        if 'tags' in cached_entry and cached_entry['tags']:
            for tag in cached_entry['tags']:
                updated_entry['tagIds'].append(tag['id'])

        # Change comments, if necessary
        if comments:
            updated_entry['description'] = comments

        # Change UTC start date/time, if necessary
        if date:
            # Convert entry date to simple sting in local timezone
            tz = get_localzone()

            original_date_localized = dateutil.parser.parse(updated_entry['start']).astimezone(tz)
            original_date = original_date_localized.strftime('%Y-%m-%d')

            if original_date != date:
                # Convert new date to UTC ISO 8601
                naive_date = dateutil.parser.parse(date)
                localized_date = tz.localize(naive_date)
                utc_datetime = localized_date.astimezone(pytz.utc)
                updated_entry['start'] = isodate.datetime_isoformat(utc_datetime)

        return updated_entry

    def get_cached_entry(self, identifier):
        filepath = self.get_cache_filepath(identifier)

        if not os.path.isfile(filepath):
            return

        with open(self.get_cache_filepath(identifier)) as json_file:
            return json.load(json_file)

    def iso_duration_to_hours(self, duration):
        minutes = isodate.parse_duration(duration).total_seconds() / 60
        return minutes / 60


class ClockifyApi:

    def __init__(self, apiKey, url=None):
        if not url:
            url = 'https://api.clockify.me/api/'

        self.url = url
        self.key = apiKey
        self.headers = {'Content-Type': 'application/json', 'X-Api-Key': self.key}
        self.tz = get_localzone()

        self.cache = ClockifyEntryCacheManager()

    def post(self, url, data):
        return requests.post(url, data=json.dumps(data), headers=self.headers)

    def set_workspace(self, id):
        self.workspace = id

    def workspaces(self):
        response = requests.get(self.url + 'workspaces/', headers=self.headers)
        return response.json()

    def projects(self):
        url = self.url + 'workspaces/' + self.workspace + '/projects/'
        response = requests.get(url, headers=self.headers)
        return response.json()

    def local_date_string_to_localized_datetime(self, date_string):
        naive_date = dateutil.parser.parse(date_string)
        return self.tz.localize(naive_date)

    def local_date_string_to_utc_iso_8601(self, date_string):
        localized_date = self.local_date_string_to_localized_datetime(date_string)
        utc_datetime = localized_date.astimezone(pytz.utc)
        return isodate.datetime_isoformat(utc_datetime)

    def add_hours_to_localized_datetime_and_convert_to_iso_8601(self, localized_datetime, hours):
        new_localized_datetime = localized_datetime + timedelta(hours=float(hours))
        utc_datetime = new_localized_datetime.astimezone(pytz.utc)
        return isodate.datetime_isoformat(utc_datetime)

    def replace_datetime_time(self, date, time):
        time_data = time.split(':')

        hours = int(time_data[0])
        minutes = int(time_data[1])

        return date.replace(hour=hours, minute=minutes)

    def create_entry(self, project, description, hours, date=None, start_time=None, task=None):
        if not date:
            local_datetime = datetime.now()

            if start_time:
                local_datetime = self.replace_datetime_time(local_datetime, start_time)

            utc_start_datetime = self.tz.localize(local_datetime).astimezone(pytz.utc)
            localized_end_datetime = utc_start_datetime + timedelta(hours=float(hours))
            utc_end_datetime = localized_end_datetime.astimezone(pytz.utc)

            start_date = isodate.datetime_isoformat(utc_start_datetime)
            end_date = isodate.datetime_isoformat(utc_end_datetime)
        else:
            if start_time:
                date = date + ' ' + start_time

            start_date = self.local_date_string_to_utc_iso_8601(date)
            localized_datetime = self.local_date_string_to_localized_datetime(date)
            end_date = self.add_hours_to_localized_datetime_and_convert_to_iso_8601(localized_datetime, hours)

        data = {
            "start": start_date,
            "end": end_date,
            "billable": "false",
            "description": description,
            "projectId": project,
            "taskId": task,
            "tagIds": []
        }

        url = self.url + 'workspaces/' + self.workspace + '/timeEntries/'
        response = self.post(url, data)

        # Cache entry if entry was created
        response_data = response.json()

        if 'projectId' in response_data:
            self.cache.create_from_new_entry_response(response_data)

        return response_data

    # entry argument must be in UpdateTimeEntryRequest format (see Clockify API documentation)
    def update_entry(self, entry):
        url = self.url + 'workspaces/' + self.workspace + '/timeEntries/' + entry['id'] + '/'
        return requests.put(url, data=json.dumps(entry), headers=self.headers)

    def delete_entry(self, id):
        url = self.url + 'workspaces/' + self.workspace + '/timeEntries/' + id + '/'
        return requests.delete(url, headers=self.headers)

    def entries(self, start=None, end=None):
        data = {'me': 'true'}

        if start:
            data['startDate'] = self.local_date_string_to_utc_iso_8601(start)
        if end:
            data['endDate'] = self.local_date_string_to_utc_iso_8601(end)

        data['userGroupIds'] = []
        data['userIds'] = []
        data['projectIds'] = []
        data['clientIds'] = []
        data['taskIds'] = []
        data['tagIds'] = []
        data['billable'] = 'BOTH'

        url = self.url + 'workspaces/' + self.workspace + '/reports/summary/'
        response = self.post(url, data)

        # work around API issue by manually culling entries out of date/time range
        response_data = response.json()

        entries = []

        for entry in response_data['timeEntries']:
            if entry['timeInterval']['start'] >= data['startDate'] and entry['timeInterval']['end'] <= data['endDate']:
                entries.append(entry)

                # Cache entry in case user wants to later update event
                self.cache.create_from_entry(entry)

        return entries

    def project_tasks(self, id):
        url = self.url + 'workspaces/' + self.workspace + '/projects/' + id + '/tasks/'
        response = requests.get(url, headers=self.headers)
        return response.json()

    def get_task_project_id(self, id):
        url = self.url + 'workspaces/' + self.workspace + '/projects/taskIds/'
        data = {'ids': [id]}
        tasks = self.post(url, data).json()

        if tasks != []:
            return tasks[0]['projectId']
        else:
            return None
