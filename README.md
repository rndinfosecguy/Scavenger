# Scavenger - OSINT Bot - 3.0

---

[bot in action](https://twitter.com/leak_scavenger) (currently not running)

---

## Intro
Just the code of my OSINT bot searching for sensitive data leaks on paste sites.
email:password combinations are always collected.

Search terms:
```
mysqli_connect(
BEGIN RSA PRIVATE KEY
-----BEGIN
The name of the database for WordPress
Return-Path:
insert into
INSERT INTO
.onion
AKIA
ASIA
ghp_
github_pat_
AIza
sk_live_
rk_live_
xoxb-
SG.
client_secret
jdbc:
mongodb://
mongodb+srv://
mysql://
postgresql://
redis://
Bearer
authorization: basic
```

Search terms can be customized. You can learn more about it in the configuration section.

## Articles About Scavenger
- https://jakecreps.com/2019/05/08/osint-collection-tools-for-pastebin/
- https://jakecreps.com/2019/01/08/scavenger/
- https://youtu.be/VCwiZ2dh17Q?t=51 (the bot is mentioned here)

## Main Features

For pastebin.com the bot has two modes:
- looking for sensitive data in the archive via scraping
- looking for sensitive data by tracking users who publish leaks

Additional features:
- customizable search terms

## Configuration

1. Delete the README.md files in every subfolder as they are only placeholders 
2. The bot searches for email:password combinations and other kinds sensitive data by default. If you want to add more search terms edit the __configs/searchterms.txt__ file or use the -2 switch in the control script
Default __configs/searchterms.txt__ configuration:

If you want to add other search terms just add them to file line by line.
You know a useful search terms which is missing here? Tell me! :-)
3. For the user tracking module of pastebin.com you need to add the target users line by line to the __configs/users.txt__ file.

## Usage

Program help:
```console
$ python3 scavenger.py -h
╭── Scavenger 2.0 ─────────────────────────────────╮
│ pastebin credential-leak crawler                 │
│                                                  │
│   -0  archive scrape module                      │
│   -1  user track module                          │
│   -2  edit search terms                          │
│   -3  edit tracked users                         │
│                                                  │
│ python3 scavenger.py -0 -1  (combine flags)      │
╰──────────────────────────────────────────────────╯
usage: scavenger.py [-h] [-0] [-1] [-2] [-3]

control script

options:
  -h, --help          show this help message and exit
  -0, --pbincom       Activate pastebin.com archive scraping module
  -1, --pbincomTrack  Activate pastebin.com user track module
  -2, --editsearch    Edit search terms file for additional search terms (email:password combinations will always be searched)
  -3, --editusers     Edit user file of the pastebin.com user track module

example usage: python3 scavenger.py -0 -1
```

Crawled pastes are stored at different locations depending on their status.
- Paste crawled but nothing was detected -> __data/raw_pastes__
- Paste crawled and an email:password combination was detected -> __data/raw_pastes__ and __data/files_with_passwords__
- Paste crawled and other sensitive data was detected -> __data/raw_pastes__ and __data/otherSensitivePastes__

Pastes get stored in data/raw_pastes until they reach a limit of 48000 files.
Once there are more then 48000 pastes they get ziped and moved to the archive folder.

---

Start the pastebin.com archive scraping module
```console
$ python3 scavenger.py -0
```
Start pastebin.com user tracking module
```console
$ python3 scavenger.py -1
```
When starting one of these modules, a tmux session with the running module is created in the background.

List tmux sessions
```console
$ tmux ls
pastebincomArchive: 1 windows (created Sun Apr 14 06:33:32 2021) [204x58]
pastebincomTrack: 1 windows (created Sun Apr 14 06:33:32 2021) [204x58]
```
Interact with a tmux session example

```console
$ tmux a -t pastebincomArchive
$ tmux a -t pastebincomTrack
```

To detach from a session hit STRG+b d.

---

If you want to start a module without using the control software you can do this by calling them directly.

Pastebin.com archive scraper
```console
$ python3 pbincomArchiveScrape.py
```

Pastebin.com user tracker
```console
$ python3 pbincomTrackUser.py
```

---

## To Do

If you miss anything and want me to add features or make changes, just let me know via Twitter or GitHub issue :-)

