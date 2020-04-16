## TT, Finally an API for Anuko Time Tracker!

:clock10: Never forget to write your hours with this easy to use command line interface

### Installation:
```
sudo python3 setup.py install
```

### Configure
Configure your account
```
tt set_user <USERNAME>
tt set_password <PASSWORD>
```
and you are good to go.

### Standard workflow
You arrive at BBx, and you start working on the project "ABC". You even want to be more precise: you add the note "the notes of the task".
You can then use `tt` as follow:
```
tt start ABC "the notes of the task"
```
"ABC" may be ambiguous, you may select a specific project within a match list.
To ensure your work had been properly set, you can run
```
tt show
```
An hour goes by. You start a new task: the "DEF" task. This time, you don't need any note on that task. So you can just type:
```
tt start DEF
```
Then, it's lunch time!
```
tt stop
```
You start working again at 13:00. But you forgot to report it using tt, and it is already 14:30.
No problem, you can just use the `-s` parameter:
```
tt start DEF "after lunch work" -s 13:00
```
You relealize you did not start at 13:00, but rather at 13:30, because you were playing table tennis.
No worries, you can just run
```
tt cancel
tt start DEF "after lunch work" -s 13:30
```
And it is already the end of the day...
```
tt stop -s 18:00
```

### Useful commands
```
tt day
tt year
tt overtime
tt holiday
```

### How to be even more efficient
You can also specify a default work on tt:
```
tt set_work MY_PROJECT "this text will always be the same day after day..."
```
Once you have done that, "MY_PROJECT" will be considered as your default project. So you no longer need to specify it when working on that project:
```
tt start
```

### Default works
I don't want you to struggle with daily/weekly meetings. This is what I created a predefined project list. You can print it with:
```
tt projects
```
They also have predefined notes, so you don't need to bother rewriting the notes.

