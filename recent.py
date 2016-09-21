#!/usr/bin/env python
import sqlite3
import sys
import os
import argparse
import re

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def parse_history(history):
    # TODO: Make this handle unusual HISTTIMEFORMATs
    return re.sub(r"^\s+\d+\s+", "", history)

def create_connection():
    recent_db = os.environ['HOME'] + "/.recent.db"
    return sqlite3.connect(recent_db)

def log():
    parser = argparse.ArgumentParser()
    parser.add_argument("command")
    parser.add_argument("pid")
    parser.add_argument("return_val")
    args = parser.parse_args()
    conn = create_connection()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS commands
        (command_dt timestamp, command text, pid int, return_val int, pwd text)''')
    c.execute("INSERT INTO commands VALUES (datetime('now','localtime'), ?, ?, ?, ?)",
        (parse_history(args.command), args.pid, args.return_val, os.environ['PWD']))
    conn.commit()
    conn.close()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("pattern", nargs='?', default='', help='optional pattern to search')
    parser.add_argument('-n', metavar=('20'), help='max results to return', default=20)
    args = parser.parse_args()
    pattern = '%' + args.pattern + '%'
    conn = create_connection()
    c = conn.cursor()
    for row in c.execute('''select command_dt, command from (select * from commands where command like ?
                            order by command_dt desc limit ?) order by command_dt''', (pattern, args.n)):
        print(bcolors.WARNING + row[0] + bcolors.ENDC + ' ' + row[1])
    conn.close()
