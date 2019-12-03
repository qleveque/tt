import requests
import sys
import json
import os
import time
import click
import re


HOME_PATH = os.path.expanduser('~')
CONFIG_PATH = os.path.join(HOME_PATH,'.config')
if not os.path.isdir(CONFIG_PATH):
    os.mkdir(CONFIG_PATH)
TT_PATH = os.path.join(CONFIG_PATH, 'tt')
if not os.path.isdir(TT_PATH):
    os.mkdir(TT_PATH)
    
SAVE_FILE = os.path.join(TT_PATH,"save_tt.json")
CONFIG_FILE = os.path.join(TT_PATH,"config.json")

URL = "http://bluedev/timetracker/"
NOW = time.strftime("%H:%M")
TODAY = time.strftime("%Y-%m-%d")
YEAR = time.strftime("%Y")

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
    "man": Project(3, 1)
}   

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

def get_total_hour(data, year):
    cookies = login(data)
    submit_data = {
        "favorite_report": -1,
        "project": None,
        "task": None,
        "period": None,
        "start_date": "{}-01-01".format(str(year)),
        "end_date": "{}-12-31".format(str(year)),
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
    format = '<td nowrap class="cellRightAlignedSubtotal">(\\d+:\\d+)</td>'
    m = re.search(format, r.text)
    try:
        return m.group(1)
    except:
        return "impossible to fetch total time"
    
    

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
        
    elif command == "setuser":
        save_config("user", option)
        
    elif command == "total":
        if not option:
            option = YEAR
        tot = get_total_hour(data, option)
        print(tot)
    
    else:
        print("error 3")    

if __name__ == "__main__":
    main()