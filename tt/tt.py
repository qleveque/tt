import numpy as np
import requests
import sys
import json
import os
import time
import click
import re
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

class Project:
    def __init__(self, project, task, note = ""):
        self.project = project
        self.task = task
        self.note = note

PROJECT_MAP = {
    "scrum": Project(68, 2, "SCRUM meeting"),
    "al": Project(1, 2),
    "as": Project(53, 2),
    "ant": Project(50, 2),
    "tactical": Project(3, 1, "Tactical meeting"),
    "man": Project(3, 1),
    "rd": Project(68, 1)
}   

def remaining(data):
    if data is None:
        return 0
    t = data.get("time", None)
    if time is None:
        return 0
    tdelta = datetime.strptime(NOW, FMT) - datetime.strptime(t, FMT)
    r = tdelta.total_seconds()/(60*60)
    return r

def login(data):
    config_data = load_config()
    password = config_data.get("password", None)
    user = config_data.get("user", None)
        
    if password is None or user is None:
        print("error credentials")
        return
        
    login_data = {
        "login": user,
        "password": password,
        "btn_login": "Connexion",
        "browser_today": TODAY
    }

    r = requests.post(URL + "login.php", data=login_data)
    return r.cookies

def get_hour(data, from_, to_):
    cookies = login(data)
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
    r = requests.post(URL + "reports.php", data=submit_data, cookies = cookies)
    format = '<td nowrap class="cellRightAlignedSubtotal">(\\d+):(\\d+)</td>'
    m = re.search(format, r.text)
    try:
        hours, minutes = int(m.group(1)), int(m.group(2))
    except:
        return 0
    return hours + minutes/60.0

def get_days_off():
    config_data = load_config()
    return config_data.get("days_off", [])

def add_to_tt(data, t):
    cookies = login(data)
    submit_data = {
        "project": data["project"],
        "task": data["task"],
        "start": data["time"],
        "finish": t,
        "date": TODAY,
        "note": data["note"],
        "btn_submit": "Submit",
        "browser_today": TODAY
    }
    
    r = requests.post(URL + "time.php", data=submit_data, cookies = cookies)

def save_config(key, value):
    config_data = {}
    if os.path.isfile(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding = "utf-8") as file:
            config_data = json.load(file)
    config_data[key] = value
    with open(CONFIG_FILE, 'w', encoding="utf-8") as file:
        json.dump(config_data, file)
      
def load_config():
    if os.path.isfile(CONFIG_FILE):
            with open(CONFIG_FILE, "r", encoding = "utf-8") as file:
                config_data = json.load(file)
                return config_data
    return None

def save_data(new_data):
    with open(SAVE_FILE, 'w', encoding="utf-8") as file:
        json.dump(new_data, file)
        
def load_data():
    if os.path.isfile(SAVE_FILE):
            with open(SAVE_FILE, "r", encoding = "utf-8") as file:
                config_data = json.load(file)
                return config_data
    return None
        
def remove_data():
    os.remove(SAVE_FILE)

@click.command()
@click.argument('command', required=True)
@click.argument('option', required=False)
@click.argument('note', required=False, default="")
@click.option('--start', '-s', help='Start at', default=None)
def main(command, option, note, start):
    """
    Existing commands: stop, start, cancel, show, set_work, set_password, set_user, year, day
    Existing projects: scrum, al, as, ant, tactical, man, rd
    """
    data = load_data()
    config = load_config()
    hour = start
    
    if hour is None:
        hour = NOW
       
    # command stop
    if command == "stop":
        if data is not None:
            add_to_tt(data, hour)
            remove_data()
        else:
            print("error 1")

    # command start
    elif command == "start":
        if data is not None:
            add_to_tt(data, hour)
        
        if not option and config is not None:
            option = config.get("work_proj", "")
            note = config.get("work_desc", "")
        
        if option in PROJECT_MAP:
            proj = PROJECT_MAP[option]
            if not note:
                note=proj.note
            new_data = {
                "command": option,
                "project": proj.project,
                "task": proj.task,
                "time": hour,
                "note": note
            }
            save_data(new_data)
        else:
            print("error 2")
    
    elif command == "cancel":
        remove_data()
    
    elif command == "show":
        if data is not None:
            print("Current work: {} {} {}".format(data.get("command",""),
                                                  data.get("time", ""),
                                                  data.get("note", "")))
        else:
            print("No current work.")
            
        if config is not None:
            print("Current default work: {} {}".format(config.get("work_proj",""),
                                                       config.get("work_desc","")))
            print("Current user: {}".format(config.get("user","")))
        else:
            print("No current user.")
        
    elif command == "set_work":
        save_config("work_proj", option)
        save_config("work_desc", note)
    
    elif command == "set_password":
        save_config("password", option)
        
    elif command == "set_user":
        save_config("user", option)
        
    elif command == "year":
        if not option:
            option = YEAR
        from_ = "{}-01-01".format(str(option))
        to_ = "{}-12-31".format(str(option))
        tot = get_hour(data, from_, to_)
        tot += remaining(data)
        print(tot)
    
    elif command == "day":
        if not option:
            option = TODAY
        tot = get_hour(data, option, option)
        tot += remaining(data)
        print(tot)

    elif command == "overtime" or command == "ot":
        holidays = PUBLIC_HOLIDAY + get_days_off()
        working_day = np.busday_count(YEAR, TODAY, weekmask='1111100', holidays=holidays)
        working_hours = working_day * HOURS_PER_DAY

        from_ = "{}-01-01".format(str(YEAR))
        yesterday = (datetime.now() - timedelta(1)).strftime(DATE_FMT)
        worked_hours = get_hour(data, from_, yesterday)

        worked_hours_today = get_hour(data, TODAY, TODAY) + remaining(data)
        worked_hours += worked_hours_today

        if worked_hours_today < HOURS_PER_DAY:
            working_hours += worked_hours_today
            should_work_until = datetime.strptime(NOW, FMT) \
                                + timedelta(hours=(HOURS_PER_DAY - worked_hours_today))
            print("Your day is not done, you should work until",
                  datetime.strftime(should_work_until, FMT))
        else:
            working_hours += HOURS_PER_DAY
            print("Well, imma head out ! {} overtime hours today !"
                  .format(round(worked_hours_today - HOURS_PER_DAY, 2)))

        print("You worked {} hours in {}:".format(round(worked_hours, 2), YEAR))
        print("You should have worked at least:", working_hours)
        overtime = round(worked_hours - working_hours, 2)

        if overtime >= 0:
            print("You have {} overtime hours. GG!".format(overtime))
        else:
            print("Uh oh, you are {} late! Gotta catch up!".format(-overtime))

    elif command == "public-holiday" or command == "public":
        print("Here are the public holidays for {}:".format(YEAR))
        print(PUBLIC_HOLIDAY)

    elif command == "holiday":
        off = get_days_off()
        off_nb = len(off)
        if not off_nb:
            print("You have no holidays registered in TT, add them in {} if needed"
                  .format(CONFIG_FILE))
            return
        print("You have used {} of your {} off days so far".format(off_nb, YEAR))
        left = DAYS_OFF - off_nb
        print("You have {} days left !".format(max(0, left)))
        print("Here is what you have used:\n{}".format(off))

    else:
        print("error 3")    

if __name__ == "__main__":
    main()