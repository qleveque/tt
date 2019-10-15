import requests
import sys
import json
import os
import time
import click


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
    "tactical": Project(3, 1, "Tactical meeting")
}   
      
def add_to_tt(data, t):
    
    password = None
    user = None
    if os.path.isfile(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding = "utf-8") as file:
            config_data = json.load(file)
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
    cookies = r.cookies
    
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
        

def save(new_data):
    with open(SAVE_FILE, 'w', encoding="utf-8") as file:
        json.dump(new_data, file)

@click.command()
@click.argument('command', required=True)
@click.argument('option', required=False)
@click.argument('note', required=False, default="")
@click.option('--hour', '-h', help='Time', default=None)
def main(command, option, note, hour):
    data = None
    submit_data = None
    if hour is None:
        hour = NOW
    if os.path.isfile(SAVE_FILE):
        with open(SAVE_FILE, "r", encoding = "utf-8") as file:
            data = json.load(file)
       
    if command == "stop":
        if data is not None:
            add_to_tt(data, hour)
            os.remove(SAVE_FILE)
        else:
            print("error 1")

    elif command == "start":
        if data is not None:
            add_to_tt(data, hour)
        
        if option in PROJECT_MAP:
            proj = PROJECT_MAP[option]            
            if note=="":
                note=proj.note
            new_data = {
                "command": option,
                "project": proj.project,
                "task": proj.task,
                "time": hour,
                "note": note
            }
            save(new_data)
        else:
            print("error 2")
    
    elif command == "cancel":
        os.remove(SAVE_FILE)
    
    elif command == "show":
        if data is not None:
            print("{} {} {}".format(data["command"], data["time"], data["note"]))
        else:
            print("None")
    
    elif command == "setpw":
        save_config("password", option)
        
    elif command == "setuser":
        save_config("user", option)
    
    else:
        print("error 3")
            
if __name__ == "__main__":
    main()