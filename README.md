# Scavenger - OSINT Bot

---

[bot in action](https://twitter.com/leak_scavenger)

## Intro
Just the code of my OSINT bot searching for sensitive data leaks on different paste sites.

Search terms:
- credentials
- private RSA keys
- Wordpress configuration files
- MySQL connect strings
- onion links
- links to files hosted inside the onion network (PDF, DOC, DOCX, XLS, XLSX)
- SQL dumps

Keep in mind:
1. This bot is not beautiful. I wrote it quick and dirty and do not care about code conventions or other shit... I will never care about those things.
	
2. The code is not complete so far. Some parts like integrating the credentials in a database are missing in this online repository. 
	
3. If you want to use this code, feel free to do so. Keep in mind you have to customize things to make it run on your system.
	
4. I know that I have some false positives and I know that I miss some credentials. So if you think this is crap...ok. leave now. If you have ideas for a better detection, just let me know!
	
5. And again: QUICK AND DIRTY! Do not expect nice code.

## Articles About Scavenger
- https://jakecreps.com/2019/05/08/osint-collection-tools-for-pastebin/
- https://jakecreps.com/2019/01/08/scavenger/
- https://youtu.be/VCwiZ2dh17Q?t=51 (the bot is mentioned here)

## IMPORTANT

For pastebin.com the bot can be run in two major modes:
- API mode
- Scraping mode (using TOR)

I highly recommend to use the API mode. It is the intended method of scraping pastes from Pastebin.com and it is just fair to do so. The only thing you need is a Pastebin.com PRO account and whitelist your public IP on their site.

To start the bot in API mode just run the program in the following way:

```console
python3 run.py -0
```

However, it is not always possible to use this intended method, as you might be in NAT mode and therefore you do not have an IP exclusively (whitelisting your IP is not reasonable here). That is the reason I also implemented a scraping mode where fast TOR cycles in combination with reasonable user agents are used to avoid IP blocking and Cloudflare captchas.

To start the bot in scraping mode run it in the following way:

!!! THE TOR SCRAPING MODE DOES NOT WORK AT THE MOMENT !!!

 ```console
python3 run.py -1
```

Important note: you need the TOR service installed on your system listening on port 9050. Additionally you need to add the following line to your /etc/tor/torrc file.
 ```console
MaxCircuitDirtiness 30
```
This sets the maximum cycle time of TOR to 30 seconds.

To start the module which scrapes random pastes of paste.org just type in the following command:

 ```console
python3 run.py -2
```

## Usage

To learn how to use the software you just need to call the run.py script with the -h/--help argument.
```console
python3 run.py -h
```
Output:
```console

  _________
 /   _____/ ____ _____ ___  __ ____   ____    ____   ___________
 \_____  \_/ ___\\__  \\  \/ // __ \ /    \  / ___\_/ __ \_  __ \
 /        \  \___ / __ \\   /\  ___/|   |  \/ /_/  >  ___/|  | \/
/_______  /\___  >____  /\_/  \___  >___|  /\___  / \___  >__|
        \/     \/     \/          \/     \//_____/      \/

usage: run.py [-h] [-0] [-1] [-2]

Control software for the different modules of this paste crawler.

optional arguments:
  -h, --help            show this help message and exit
  -0, --pastebinCOMapi  Activate Pastebin.com module (using API)
  -1, --pastebinCOMtor  Activate Pastebin.com module (standard scraping using
                        TOR to avoid IP blocking)
  -2, --pasteORG        Activate Paste.org module
```

So far I implemented modules for the following paste sites:
* Pastebin.com
* Paste.org

If you want to observe specific mail addresses just add them to the file notification_targets.txt line by line.
If the bot identifies one of these addresses on Pastebin it will write the name of the paste and the corresponding password to the file notification_results.txt.

---

Just start the Pastebin.com module separately (first module I implemented)...
```console
python3 P_bot.py
```
Pastes are stored in data/raw_pastes until they are more then 48000.
When they are more then 48000 they get filtered, ziped and moved to the archive folder. 
All pastes which contain credentials are stored in data/files_with_passwords

---

Keep in mind that at the moment only combinations like USERNAME:PASSWORD and other simple combinations are detected.
However, there is a tool to search for proxy logs containing credentials. 

You can search for proxy logs (URLs with username and password combinations) by using getProxyLogs.py file
```console
python3 getProxyLogs.py data/raw_pastes/
```

---

If you want to search the raw data for specific strings you can do it using searchRaw.py (really slow). 
```console
python3 searchRaw.py SEARCHSTRING
```

---

To see statistics of the bot just call
```console
python3 status.py 
```

---

The file findSensitiveData.py searches a folder (with pastes) for sensitive data like credit cards, RSA keys or mysqli_connect strings. Keep in mind that this script uses grep and therefore is really slow on a big amount of paste files. 
If you want to analyze a big amount of pastes I recommend an ELK-Stack.
```console
python3 findSensitiveData.py data/raw_pastes/ 
```

---

There are two scripts stalk_user.py/stalk_user_wrapper.py which can be used to monitor a specific twitter user. This means every tweet he posts gets saved and every containing URL gets downloaded. To start the stalker just execute the wrapper.
```console
python3 stalk_user_wrapper.py
```

---

## To Do

I discovered other sites like Pastebin which allow to read the latest paste and crawl them. I need to integreate them into my bot. If you know additional sites which are worth a look, just let me know.
```console
Examples:
https://slexy.org/recent
http://pastebin.fr
http://pastebin.es/lists
http://pastebin.it/archive.php
```
