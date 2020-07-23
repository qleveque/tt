from typing import Tuple

import numpy as np
import requests
import json
import os
import time
import argparse
import re
from collections import defaultdict
from datetime import datetime, timedelta

HOME_PATH = os.path.expanduser('~')
CONFIG_PATH = os.path.join(HOME_PATH,'.config')
if not os.path.isdir(CONFIG_PATH):
    os.mkdir(CONFIG_PATH)
TT_PATH = os.path.join(CONFIG_PATH, 'tt')
if not os.path.isdir(TT_PATH):
    os.mkdir(TT_PATH)
    
SAVE_FILE = os.path.join(TT_PATH,"save_tt.json")
CONFIG_FILE = os.path.join(TT_PATH,"config.json")

FMT = "%H:%M"
DATE_FMT = "%Y-%m-%d"
URL = "http://bluedev/timetracker/"
NOW = time.strftime(FMT)
TODAY = time.strftime(DATE_FMT)
YEAR = time.strftime("%Y")

HOURS_PER_WEEK = 41
HOURS_PER_DAY = HOURS_PER_WEEK/5
DAYS_OFF = 20

PUBLIC_HOLIDAY = ["2020-01-01",
                  "2020-01-02",
                  "2020-04-05",
                  "2020-04-10",
                  "2020-04-12",
                  "2020-04-13",
                  "2020-05-21",
                  "2020-05-31",
                  "2020-06-01",
                  "2020-08-01",
                  "2020-09-20",
                  "2020-09-21",
                  "2020-12-25",
                  ]


class Task:
    def __init__(self, project_number, task_number, project, task="", note="", start=""):
        self.project_number = project_number
        self.task_number = task_number
        self.project = project
        self.task = task
        self.note = note
        self.start = start

    @staticmethod
    def from_dict(d):
        if d.get("project_number") is None:
            return None
        all_attributes = ["project_number", "task_number", "project", "task", "note", "start"]
        return Task(**{attr: d.get(attr, "") for attr in all_attributes})

    def to_str(self):
        r = self.project
        if self.task:
            r += ', ' + self.task
        if self.note:
            r += ': "{}"'.format(self.note)
        if self.start:
            r += " ({})".format(self.start)
        return r


TASK_MAP = {
    "scrum": Task(68, 2, 'scrum', note='SCRUM meeting'),
    "tactical": Task(3, 1, 'tactical', note='Tactical meeting'),
    "al": Task(1, 2, 'al', note='ANT lab'),
    "as": Task(53, 2, 'as', note='ANT server'),
    "ant": Task(50, 2, 'ant', note='ANT'),
    "man": Task(3, 1, 'man', note='Management'),
    "rd": Task(68, 1, 'rd', note='R&D')
}


def remaining(data):
    if data is None:
        return 0
    start = data.get("start", None)
    if start is None:
        return 0
    tdelta = datetime.strptime(NOW, FMT) - datetime.strptime(start, FMT)
    r = tdelta.total_seconds()/(60*60)
    return r


def login(config_data):
    password = config_data.get("password", None)
    user = config_data.get("user", None)
        
    if password is None or user is None:
        exit("Error credentials")

    login_data = {
        "login": user,
        "password": password,
        "btn_login": "Connexion",
        "browser_today": TODAY
    }

    try:
        r = requests.post(URL + "login.php", data=login_data)
    except:
        exit('cannot connect')
    return r.cookies


def get_hour(config, from_, to_):
    cookies = login(config)
    submit_data = {
        "favorite_report": -1,
        "project": None,
        "task": None,
        "period": None,
        "start_date": from_,
        "end_date": to_,
        "chproject": 1,
        "chstart": 1,
        "chduration": 1,
        "chtask": 1,
        "chfinish": 1,
        "chnote": 1,
        "group_by": "date",
        "chtotalsonly": 1,
        "new_fav_report": None,
        "btn_generate": "Generate",
        "fav_report_changed": None
    }
    try:
        r = requests.post(URL + "reports.php", data=submit_data, cookies = cookies)
    except:
        exit('cannot connect')
    format = '<td nowrap class="cellRightAlignedSubtotal">(\\d+):(\\d+)</td>'
    m = re.search(format, r.text)
    try:
        hours, minutes = int(m.group(1)), int(m.group(2))
    except:
        return 0
    return hours + minutes/60.0


def choose_project(config, match):
    cookies = login(config)
    try:
        r = requests.get(URL + "time.php", cookies=cookies)
    except:
        exit('cannot connect')
    project_names = {}
    task_ids = {}
    task_names = {}
    for line in r.text.split('\n'):
        line = line.strip()
        m = re.match('^([\\w_]+)\\[(\\d+)] = ".*";$', line)
        if m:
            exec(line)

    results = []
    for idx, name in project_names.items():
        if re.findall(match, name, re.IGNORECASE):
            tasks = task_ids[idx]
            for task in tasks.split(','):
                results.append(Task(idx, int(task), name, task_names[int(task)]))

    if not results:
        exit("No matching project")

    for i, result in enumerate(results):
        print('{} -> {}: {}'.format(i, result.project, result.task))

    choice = input('Choose a project: ')

    try:
        return results[int(choice)]
    except:
        exit("No matching project")


def get_project(config, option, start, note):
    if not option:
        project = Task.from_dict(config.get("saved_work", {}))
        if project is None:
            exit("No default work")
    elif option in TASK_MAP:
        project = TASK_MAP[option]
    else:
        project = choose_project(config, option)

    if note:
        project.note = note
    project.start = start
    return project


def add_to_tt(config, data, t):
    cookies = login(config)
    project = Task.from_dict(data)
    if project is None:
        exit("No current project")
    submit_data = {
        "project": project.project_number,
        "task": project.task_number,
        "start": project.start,
        "finish": t,
        "date": TODAY,
        "note": project.note,
        "btn_submit": "Submit",
        "browser_today": TODAY
    }

    try:
        r = requests.post(URL + "time.php", data=submit_data, cookies=cookies)
    except:
        exit('cannot connect')


def save_config(new_config):
    with open(CONFIG_FILE, 'w', encoding="utf-8") as file:
        json.dump(new_config, file)


def load_config():
    config_data = defaultdict(lambda: {})
    if os.path.isfile(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as file:
            config_data.update(json.load(file))
            return config_data
    return config_data


def remove_data(config):
    if 'data' in config:
        del config['data']
        save_config(config)

def hours_to_hours_mn(hours: float) -> Tuple[int, int]:
    overtime_minutes = int((hours - int(hours)) * 60)
    overtime_hours = int(hours)
    return overtime_hours, overtime_minutes

def main():
    """
    Existing commands:
    stop, start, cancel, show, set_work, set_password, set_user, year, day, list,
    overtime (ot), public-holiday (public), projects
    """

    # Parsing the data
    parser = argparse.ArgumentParser(description=main.__doc__)
    parser.add_argument('command', type=str)
    parser.add_argument('option', type=str, nargs='?')
    parser.add_argument('note', type=str, nargs='?')
    parser.add_argument('-s', '--start',
                        metavar='sarting_time',
                        help='Set the starting time of the action',
                        type=str,
                        default=None)
    args = parser.parse_args()

    command = args.command
    note = args.note
    option = None if not args.option else args.option

    config = load_config()
    data = config.get('data', None)
    start = args.start

    if start is None:
        start = NOW

    # command stop
    if command == "stop":
        if data is None:
            exit("You are not currently working")
        add_to_tt(config, data, start)
        remove_data(config)

    # command start
    elif command == "start":
        if data is not None:
            add_to_tt(config, data, start)
        project = get_project(config, option, start, note)
        config['data'] = project.__dict__
        save_config(config)

    elif command == "cancel":
        remove_data(config)

    elif command == "show":
        if data is not None:
            project = Task.from_dict(data)
            print("Current work: {}".format(project.to_str()))
        else:
            print("No current work.")
            
        project = Task.from_dict(config.get("saved_work", {}))

        if project is not None:
            print("Current default work: {}".format(project.to_str()))
        else:
            print("No current default work.")

        print("Current user: {}".format(config.get("user", "None")))

    elif command == "set_work":
        project = get_project(config, option, start, note)
        config["saved_work"] = project.__dict__
        save_config(config)
    
    elif command == "set_password":
        config["password"] = option
        save_config(config)
        
    elif command == "set_user":
        config["user"] = option
        save_config(config)
        
    elif command == "year":
        if not option:
            option = YEAR
        from_ = "{}-01-01".format(str(option))
        to_ = "{}-12-31".format(str(option))
        tot = get_hour(config, from_, to_)
        tot += remaining(data)
        print(tot)
    
    elif command == "day":
        if not option:
            option = TODAY
        tot = get_hour(config, option, option)
        tot += remaining(data)
        print(tot)

    elif command == "overtime" or command == "ot":
        holidays = PUBLIC_HOLIDAY + config.get("days_off", [])
        working_day = np.busday_count(YEAR, TODAY, weekmask='1111100', holidays=holidays)
        working_hours = (working_day * HOURS_PER_DAY) * int(config.get("percentage", 100))/100

        from_ = "{}-01-01".format(str(YEAR))
        yesterday = (datetime.now() - timedelta(1)).strftime(DATE_FMT)
        worked_hours = get_hour(config, from_, yesterday)

        worked_hours_today = get_hour(config, TODAY, TODAY) + remaining(data)
        worked_hours += worked_hours_today

        if worked_hours_today < HOURS_PER_DAY:
            working_hours += worked_hours_today
            should_work_until = (datetime.strptime(NOW, FMT) +
                                 timedelta(hours=(HOURS_PER_DAY - worked_hours_today)))
            print("Your day is not done, you should work until",
                  datetime.strftime(should_work_until, FMT))
        else:
            working_hours += HOURS_PER_DAY
            overtime_hours, overtime_minutes =\
                hours_to_hours_mn((worked_hours_today - HOURS_PER_DAY))
            print(f"Well, imma head out ! {overtime_hours}h {overtime_minutes}mn"
                  f" of overtime today !")

        print("You worked {} hours in {}:".format(round(worked_hours, 2), YEAR))
        print("You should have worked at least:", working_hours)
        overtime = round(worked_hours - working_hours, 2)

        if overtime >= 0:
            overtime_h, overtime_mn = hours_to_hours_mn(overtime)
            print("You have {}h {}mn overtime hours. GG!".format(overtime_h, overtime_mn))
        else:
            print("Uh oh, you are {} late! Gotta catch up!".format(-overtime))

    elif command == "public-holiday" or command == "public":
        print("Here are the public holidays for {}:".format(YEAR))
        print(PUBLIC_HOLIDAY)

    elif command == "holiday":
        off = config.get("days_off", [])
        off_nb = len(off)
        if not off_nb:
            print("You have no holidays registered in TT, add them in {} if needed"
                  .format(CONFIG_FILE))
            return
        print("You have used {} of your {} off days so far".format(off_nb, YEAR))
        left = DAYS_OFF - off_nb
        print("You have {} days left !".format(max(0, left)))
        print("Here is what you have used:\n{}".format(off))

    elif command == "projects":
        for name, value in TASK_MAP.items():
            print(value.to_str())

    else:
        exit("Unknown command")


if __name__ == "__main__":
    main()
