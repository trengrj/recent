#!/usr/bin/env python
import sqlite3
import os
import argparse
import hashlib
import re
import socket

SCHEMA_VERSION = 1

class Term:

    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class SQL:

    INSERT_ROW = """insert into commands (command_dt, command, pid, return_val, pwd, session)
        values (datetime('now','localtime'), ?, ?, ?, ?, ?)"""
    INSERT_SESSION = """insert into sessions (created_dt, updated_dt,
        term, hostname, user, sequence, session)
        values (datetime('now','localtime'), datetime('now','localtime'), ?, ?, ?, ?, ?)"""
    UPDATE_SESSION = """update sessions set updated_dt = datetime('now','localtime'), sequence = ?
        where session = ?"""
    TAIL_N_ROWS = """select command_dt, command from (select * from commands where
        order by command_dt desc limit ?) order by command_dt"""
    CREATE_COMMANDS_TABLE = """create table if not exists commands
        (command_dt timestamp, command text, pid int, return_val int, pwd text, session text)"""
    CREATE_SESSIONS_TABLE = """create table if not exists sessions
        (session text primary key not null, created_dt timestamp, updated_dt timestamp,
        term text, hostname text, user text, sequence int)"""
    CREATE_DATE_INDEX = """create index if not exists command_dt_ind on commands (command_dt)"""
    CHECK_COMMANDS_TABLE = """select count(*) as count from sqlite_master where type='table'
        and name='commands'"""
    GET_SESSION_SEQUENCE = """select sequence from sessions where session = ?"""
    GET_SCHEMA_VERSION = """pragma user_version"""
    UPDATE_SCHEMA_VERSION = """pragma user_version = """
    MIGRATE_0_1 = "alter table commands add column session text"


class Session:

    def __init__(self, pid, sequence):
        self.sequence = sequence
        self.empty = False
        # This combinaton of ENV vars *should* provide a unique session
        # TERM_SESSION_ID for OS X Terminal
        # XTERM for xterm
        # TMUX, TMUX_PANE for tmux
        # STY for GNU screen
        # SHLVL handles nested shells
        seed = "{}-{}-{}-{}-{}".format(
            os.getenv('TERM_SESSION_ID', ''), os.getenv('WINDOWID', ''), os.getenv('SHLVL', ''),
            os.getenv('TMUX', ''), os.getenv('TMUX_PANE',''), os.getenv('STY',''), pid)
        self.id = hashlib.md5(seed.encode('utf-8')).hexdigest()

    def update(self, conn):
        c = conn.cursor()
        try:
            term = os.getenv('TERM', '')
            hostname = socket.gethostname()
            user = os.getenv('USER', '')
            c.execute(SQL.INSERT_SESSION, [term, hostname, user, self.sequence, self.id])
            self.empty = True
        except sqlite3.IntegrityError:
            # Carriage returns need to be ignored
            if c.execute(SQL.GET_SESSION_SEQUENCE, [self.id]).fetchone()[0] == int(self.sequence):
                self.empty = True
            c.execute(SQL.UPDATE_SESSION, [self.sequence, self.id])


def migrate(version, conn):
    if version > SCHEMA_VERSION:
        exit(Term.FAIL + 'recent: your command history database does not match recent, please update' + Term.ENDC)

    c = conn.cursor()
    if version == 0:
        if c.execute(SQL.CHECK_COMMANDS_TABLE).fetchone()[0] != 0:
            print(Term.WARNING + 'recent: migrating schema to version {}'.format(SCHEMA_VERSION) + Term.ENDC)
            c.execute(SQL.MIGRATE_0_1)
        else:
            print(Term.WARNING + 'recent: building schema' + Term.ENDC)
        c.execute(SQL.CREATE_COMMANDS_TABLE)
        c.execute(SQL.CREATE_SESSIONS_TABLE)
        c.execute(SQL.CREATE_DATE_INDEX)

    c.execute(SQL.UPDATE_SCHEMA_VERSION + str(SCHEMA_VERSION))
    conn.commit()


def parse_history(history):
    match = re.search(r'^\s+(\d+)\s+(.*)$', history, re.MULTILINE and re.DOTALL)
    if match:
        return (match.group(1), match.group(2))
    else:
        return (None, None)

def parse_date(format):
    if re.match(r'^\d{4}$', format):
        return 'strftime(\'%Y\', command_dt) = ?'
    if re.match(r'^\d{4}-\d{2}$', format):
        return 'strftime(\'%Y-%m\', command_dt) = ?'
    if re.match(r'^\d{4}-\d{2}-\d{2}$', format):
        return 'date(command_dt) = ?'
    else:
        return 'command_dt = ?'


def create_connection():
    recent_db = os.getenv('RECENT_DB', os.environ['HOME'] + '/.recent.db')
    conn = sqlite3.connect(recent_db)
    build_schema(conn)
    return conn

def build_schema(conn):
    try:
        c = conn.cursor()
        current = c.execute(SQL.GET_SCHEMA_VERSION).fetchone()[0]
        if current != SCHEMA_VERSION:
            migrate(current, conn)
    except (sqlite3.OperationalError, TypeError) as e:
        migrate(0, conn)

def log():
    parser = argparse.ArgumentParser()
    parser.add_argument('-r', '--return_value', help='set to $?', default=0)
    parser.add_argument('-c', '--command', help='set to $(HISTTIMEFORMAT= history 1)', default='')
    parser.add_argument('-p', '--pid', help='set to $$', default=0)
    args = parser.parse_args()

    sequence, command = parse_history(args.command)
    pid, return_value = args.pid, args.return_value
    pwd = os.getenv('PWD', '')

    if sequence == None or command == None:
        print(Term.WARNING + 'recent: cannot parse command output, please check your bash trigger looks like this:'  + Term.ENDC)
        print("""export PROMPT_COMMAND='log-recent -r $? -c "$(HISTTIMEFORMAT= history 1)" -p $$'""")
        exit(1)

    conn = create_connection()
    session = Session(pid, sequence)
    session.update(conn)

    if not session.empty:
        c = conn.cursor()
        c.execute(SQL.INSERT_ROW, [command, pid, return_value, pwd, session.id])

    conn.commit()
    conn.close()


def query_builder(args):
    query = SQL.TAIL_N_ROWS
    filters = []
    parameters = []
    if (args.pattern != ''):
        filters.append('command like ?')
        parameters.append('%' + args.pattern + '%')
    if (args.w != ''):
        filters.append('pwd = ?')
        parameters.append(os.path.abspath(os.path.expanduser(args.w)))
    if (args.d != ''):
        filters.append(parse_date(args.d))
        parameters.append(args.d)
    try:
        n = int(args.n)
        parameters.append(n)
    except:
        exit(Term.FAIL + '-n must be a integer' + Term.ENDC)
    where = 'where ' + ' and '.join(filters) if len(filters) > 0 else ''
    return (query.replace('where', where), parameters)



def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('pattern', nargs='?', default='', help='optional pattern to search')
    parser.add_argument('-n', metavar=('20'), help='max results to return', default=20)
    parser.add_argument('-w', metavar=('/folder'), help='working directory', default='')
    parser.add_argument('-d', metavar=('2016-10-01'), help='date in YYYY-MM-DD, YYYY-MM, or YYYY format', default='')
    args = parser.parse_args()
    conn = create_connection()
    c = conn.cursor()
    query, parameters = query_builder(args)
    for row in c.execute(query, parameters):
        if row[0] and row[1]:
            print(Term.WARNING + row[0] + Term.ENDC + ' ' + row[1])
    conn.close()
