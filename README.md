# Scavenger

[bot in action](https://twitter.com/leak_scavenger)

## Intro
Just the code of my OSINT bot searching for credentials on different paste sites.

Keep in mind:
1. This bot is not beautiful. I wrote it quick and dirty and do not care about code conventions or other shit... I will never care about those things.
	
2. The code is not complete so far. Some parts like integrating the credentials in a database are missing in this online repository. 
	
3. If you want to use this code, feel free to do so. Keep in mind you have to customize things to make it run on your system.
	
4. I know that I have some false positives and I know that I miss some credentials. So if you think this is crap...ok. leave now. If you have ideas for a better detection, just let me know!
	
5. And again: QUICK AND DIRTY! Do not expect nice code.

## IMPORTANT
I recently updated the bot because Pastebin.com started to block my IP as I am scraped their website to gather the information without using their API.
Now I implemented that at least the pastes itself are downloaded using their API. Therefore I implemented a switch inside the P_bot.py file. To activate the usage of the API you need to edit the run.py file by changing

```sh
os.system("tmux new -d -s pastebincomCrawler './P_bot.py scrape'")
```
to
```sh
os.system("tmux new -d -s pastebincomCrawler './P_bot.py api'")
```
If you do not enable the API usage you may get blocked by Pastebin.com too. I did not make this change the default configuration because you need a Pastebin.com PRO account to use the API. If you have one you need to whitelist your IP on their website and you will be fine using the API :-) 

## Usage

To learn how to use the software you just need to call the run.py script with the -h/--help argument.
```sh
python run.py -h
```
Output:
```sh

  _________
 /   _____/ ____ _____ ___  __ ____   ____    ____   ___________
 \_____  \_/ ___\\__  \\  \/ // __ \ /    \  / ___\_/ __ \_  __ \
 /        \  \___ / __ \\   /\  ___/|   |  \/ /_/  >  ___/|  | \/
/_______  /\___  >____  /\_/  \___  >___|  /\___  / \___  >__|
        \/     \/     \/          \/     \//_____/      \/

usage: run.py [-h] [-0] [-1]

Control software for the different modules of this paste crawler.

optional arguments:
  -h, --help         show this help message and exit
  -0, --pastebinCOM  Activate Pastebin.com module
  -1, --pasteORG     Activate Paste.org module
```

So far I only implemented the Pastebin.com module and I am working on Paste.org. I will add more modules and update this script over time.

---

Just start the Pastebin.com module separately (first module I implemented)...
```sh
python P_bot.py
```
Pastes are stored in data/raw_pastes until they are more then 48000.
When they are more then 48000 they get filtered, ziped and moved to the archive folder. 
All pastes which contain credentials are stored in data/files_with_passwords

---

Keep in mind that at the moment only combinations like USERNAME:PASSWORD and other simple combinations are detected.
However, there is a tool to search for proxy logs containing credentials. 

You can search for proxy logs (URLs with username and password combinations) by using getProxyLogs.py file
```sh
python getProxyLogs.py data/raw_pastes
```

---

If you want to search the raw data for specific strings you can do it using searchRaw.py (really slow). 
```sh
python searchRaw.py SEARCHSTRING
```

---

To see statistics of the bot just call
```sh
python status.py 
```

---

The file findSensitiveData.py searches a folder (with pastes) for sensitive data like credit cards, RSA keys or mysqli_connect strings. Keep in mind that this script uses grep and therefore is really slow on a big amount of paste files. 
If you want to analyze a big amount of pastes I recommend an ELK-Stack.
```sh
python findSensitiveData.py data/raw_pastes 
```

---

There are two scripts stalk_user.py/stalk_user_wrapper.py which can be used to monitor a specific twitter user. This means every tweet he posts gets saved and every containing URL gets downloaded. To start the stalker just execute the wrapper.
```sh
python stalk_user_wrapper.py
```

---

## To Do

I discovered other sites like Pastebin which allow to read the latest paste and crawl them. I need to integreate them into my bot. If you know additional sites which are worth a look, just let me know.
```sh
Examples:
https://www.paste.org/p/random/paste
https://slexy.org/recent
http://pastebin.fr
http://pastebin.es/lists
http://pastebin.it/archive.php
```
