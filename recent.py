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

class sql:
    INSERT_ROW = """insert into commands values (datetime('now','localtime'), ?, ?, ?, ?)"""
    TAIL_N_ROWS = """select command_dt, command from (select * from commands where command like ?
        order by command_dt desc limit ?) order by command_dt"""
    CREATE_COMMANDS_TABLE = """create table if not exists commands
        (command_dt timestamp, command text, pid int, return_val int, pwd text)"""
    CREATE_DATE_INDEX = """create index if not exists command_dt_ind on commands (command_dt)"""
    CHECK_COMMANDS_TABLE = """select count(*) as count from sqlite_master where type='table'
        and name='commands'"""

def parse_history(history):
    # TODO: Make this handle unusual HISTTIMEFORMATs
    return re.sub(r"^\s+\d+\s+", "", history)

def create_connection():
    recent_db = os.environ['HOME'] + "/.recent.db"
    conn = sqlite3.connect(recent_db)
    build_schema(conn)
    return conn

def build_schema(conn):
    c = conn.cursor()
    schema_exists = c.execute(sql.CHECK_COMMANDS_TABLE).fetchone()[0];
    if not schema_exists:
        print("recent: building schema")
        c.execute(sql.CREATE_COMMANDS_TABLE)
        c.execute(sql.CREATE_DATE_INDEX)
        conn.commit()


def log():
    parser = argparse.ArgumentParser()
    parser.add_argument("command")
    parser.add_argument("pid")
    parser.add_argument("return_val")
    args = parser.parse_args()
    conn = create_connection()
    c = conn.cursor()
    c.execute(sql.INSERT_ROW,
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
    for row in c.execute(sql.TAIL_N_ROWS, (pattern, args.n)):
        print(bcolors.WARNING + row[0] + bcolors.ENDC + ' ' + row[1])
    conn.close()
