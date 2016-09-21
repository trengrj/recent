#!/usr/bin/env python
import sqlite3
import sys
import os

DB_PATH = os.environ['HOME'] + "/.recent/db"

if (len(sys.argv) != 4):
  print("usage: log.py command pid return_val")
  exit(1)

command = sys.argv[1]
pid = sys.argv[2]
return_val = sys.argv[3]

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS commands
                 (command_dt timestamp, command text, pid int, return_val int, pwd text)''')
c.execute("INSERT INTO commands VALUES (datetime(), ?, ?, ?, ?)", (command, pid, return_val, os.environ['PWD'])) 
conn.commit()
conn.close()
