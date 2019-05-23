# clockify-tool

The Clockify Tool (`cft`) can be used to list, create, and delete time entries in
Clockify. Tested with Python 2.7.

Clockify's API requires that all important details about a time entry be
provided when making a change to a time entry. Because of this `cft`, when
your list time entries, caches these details. Given this if you list time
entries in `cft`, change one of the listed time entries using Clockify's web
UI, then change the same time entry using `cft` you'd lose the changes you
make in the web UI. For this reason it's advised to stick to `cft` for time
entry if you want to use `cft`. You can still safely use the web UI for
searching, etc.

Also note that `cft` isn't concerned about start time. Start time, when adding
a time entry via `cft`, will always be midnight. Updating existing time
entries, however, will preserve their start time. The ability to specify a
start time when creating a time entry will be added if needed.


Installation
------------

Clone this repo, change into the repo directory, then enter the following
command:

    $ pip install -r requirements.txt


Basic Configuration
-------------------

To use `cft` you'll need to, in the Clockify web UI, click the "GENERATE"
button on the "Personal settings" page to generate an API key. You'll then need
to put the key into the `cft` configuration file, which is YAML-formatted and
must be created in `$HOME/.cft.yml`.

Here's an example configuration file containing an API key:

    api key: aLedJtL4rl48s2O7

Once you've created a configuration file, you can then run `cft` which will
provide you will a list of available workspaces.

For example:

    $ ./cft
    Please set workspace ID as "workspace" in /home/vagrant/.cft.yml.
    
    Available workspaces:
    * Client-Project-Task Workspace [4c31a29da059321c02e301e0]

Edit the configuration file to set the ID of the workspace you'd like to use.

Example configuration with API key and workspace set:

    api key: aLedJtL4rl48s2O7
    workspace: 4c31a29da059321c02e301e0

Read on to learn about the basic functionality of `cft` and, once you've got
the hang of things, check out `Advanced Configuration` to learn how you can
save time when entering new time entries.


Commands
--------

Clockify Tool allows you to list, create and delete Clockify time entries.


### Listing time entries in a period of time

Help for the list command:

    $ ./cft list -h
    usage: cft list [-h] [-s start date] [-e end date] [period]
    
    positional arguments:
      period                time period: optional, overrides -s and -e
    
    optional arguments:
      -h, --help            show this help message and exit
      -s start date, --start start date
      -e end date, --end end date
    
    Available periods: "yesterday" ("y"): day before today, "lastweek" ("lw"):
    last work week (Monday to Friday), "currentweek" ("cw"): current work week
    (Monday to Friday), "fulllastweek" ("flw"): last full week (Sunday to
    Saturday), "fullcurrentweek" ("fcw"): current full week (Sunday to Saturday)

Example list of today's time entries:

    $ ./cft

Here's example output:

    $ ./cft 
    Fetching time entries from 2019-05-14 to 2019-05-14...
    
    Time entries:
    * Reading email. (Email: 5cdb08621080ec2d4a8e707e) [0.25 hours: 5cdb08bfb0798752b039c5ba]
    * Daily scrum. (Meetings: 5cdb08ead278ae206156ae6f) [0.25 hours: 5cdb090bb0798752b039c5f6]
    
    0.5 hours.

In the output each line under "Time entries" that begins with a `*` is a time
entry. The time entry's description is first shown, then the entry's project
name and ID, then the hours spent and the time entry's ID.

Here's an example of listing yesterday's time entries:

    $ ./cft list yesterday

Yesterday is one time period of a number of available time periods.

Note that there are one letter abbreviations for the periods. The abbreviation
for "yesterday" is "y", for example.

`cft` commands like "list" can have one letter abbreviations. So if you
wanted to list yesterday's time entries you could enter:

    $ ./cft l y

Another time saver: if you enter a time period, instead of a command, you'll
get a list of entries in the time period:

    $ ./cft y


### List time entries in an arbitrary date range

When listing time entries, an arbitrary date range can be specified using the
`--start` (or `-s-`) and/or `--end` (or `-e`) options.

If either `--start` or `--end` are specified, but the other isn't, then the
one that's omitted they will default to today's date.

Example list of time entries in an arbitary date range:

    $ ./cft l -s 2019-03-06 --e 2019-03-09

The `-` or `+` operators, as a prefix to a integeter represeting a number of
days, can also be used to indicate a relative date.

For example, if one wanted to list time entries created five days ago to the
present day then one could use this command:

    $ ./cft l -s -5


### List projects

The `projects` (or `p`) command is used to list projects. The project name
and ID will be output.

For example:

    $ ./cft projects
    * Email [5cdb08621080ec2d4a8e707e]
    * Meetings [5cdb08ead278ae206156ae6f]


### Creating a time entry

The `new` (or `n`) command is used to create a new time entry. The number of
hours, rather than a particular time range, is specified.

Help for the new command:

    $ ./cft new -h
    usage: cft new [-h] [-c comments: required for new time entries]
                   [-t hours spent: required for new time entries] [-d date]
                   project ID
    
    positional arguments:
      project ID            ID of project: required
    
    optional arguments:
      -h, --help            show this help message and exit
      -c comments: required for new time entries, --comments comments: required for new time entries
      -t hours spent: required for new time entries, --hours hours spent: required for new time entries
      -d date, --date date  defaults to today

Here's an example (in which `5cb772f3f15c9857ee275d00` is the project ID:

    $ ./cft new 5cb772f3f15c9857ee275d00 --comments="Checking email." --hours=.25

Here's the same example in a briefer form.

    $ ./cft n 5cb772f3f15c9857ee275d00 -c "Checking email." -t .25


### Updating a time entry

The `update` (or `u`) command is used to update an existing time entry.

Help for the update command:

    $ ./cft update -h
    usage: cft update [-h] [-c comments: required for new time entries]
                      [-t hours spent: required for new time entries] [-d date]
                      entry ID
    
    positional arguments:
      entry ID              ID of time entry: required
    
    optional arguments:
      -h, --help            show this help message and exit
      -c comments: required for new time entries, --comments comments: required for new time entries
      -t hours spent: required for new time entries, --hours hours spent: required for new time entries
      -d date, --date date  defaults to today

Here's an example (in which `5ce54a35a02987296634c98a` is the time entry's ID:

    $ ./cft update 5ce54a35a02987296634c98a --hours=1.5

Note: make sure you read the intro to this README file so you know that there
can be issues with updating time entries if you use both Clockify's web UI and
`cft`.


### Deleting a time entry

The `delete` (or `d`) command is used to delete a time entry.

Here's an example (in which `5cd64137b079870300a9c9e0` is the time entry ID:

    $ ./cft delete 5cd64137b079870300a9c9e0


## List workspaces

The `workspaces` (or `w`) command is used to list workspaces. The workspace
name and ID will be output.

For example:

    $ ./cft workspaces
    * Client-Project-Task Workspace [4c31a29da059321c02e301e0]


Advanced configuration
----------------------

You can avoid save time through advanced configuration.

### Project time entry aliases

When specifying a project you can either use ID of the project or you can refer to
an alias specifed in your configuration file. You can also create aliases for
aliases.

Example:

    projects:
      meet:
        id: 4cb771f3f13c9855ee275d00
      meeting:
        id: meet


### Project time entry templates

In addition to using an alias to specify a project ID, you can use the same
technique to, when creating a time entry, automatically set the comments and
hours spent.

Example:

    projects:
      meet:
        id: 100
      meeting:
        id: meet
      scrum:
        id: meet
        comments: "Daily scrum."
        hours: .25

These values can be overridden by command-line options so if, building on the
previous example, you had a scrum meeting that lasted a half hour, instead of
15 minutes, you could add a time entry using the "scrum" alias and just
overrride the --time command-line option.

Example:

    $ ./cft n scrum -t .5


Shortcuts and abbreviations
---------------------------

Example of quick addition of a time entry using a template:

    $ ./cft +scrum
