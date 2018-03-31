#!/usr/bin/python

import sys
import os
import time

raw_pastes_folder = "data/raw_pastes"
password_files_folder = "data/files_with_passwords"
archive_folder = "archive"

while True:
        print """


        \t\t  ___|
        \t\t\___ \   __|  _` |\ \   / _ \ __ \   _` |  _ \  __|
        \t\t      | (    (   | \ \ /  __/ |   | (   |  __/ |
        \t\t_____/ \___|\__,_|  \_/ \___|_|  _|\__, |\___|_|
        \t\t                                   |___/

        """

        print "-----------------------------------------------------"

        numfiles_raw_pastes = len([f for f in os.listdir(raw_pastes_folder) if os.path.isfile(os.path.join(raw_pastes_folder, f)) and f[0] != '.'])
        numfiles_password_files = len([f for f in os.listdir(password_files_folder) if os.path.isfile(os.path.join(password_files_folder, f)) and f[0] != '.'])
        numfiles_archives = len([f for f in os.listdir(archive_folder) if os.path.isfile(os.path.join(archive_folder, f)) and f[0] != '.'])

        print "|\tNumber of raw pastes: " + str(numfiles_raw_pastes)
        print "|\tNumber of files with passwords: " + str(numfiles_password_files)
        print "|\tNumber of archives: " + str(numfiles_archives)
        print "-----------------------------------------------------"

        time.sleep(3)
        os.system("clear")

