======
recent
======

Recent is a more structured way to log your bash history.

The standard ~/.bash_history file is inadequate in many ways, its
worst fault is to by default log only 500 history entries, with no timestamp.
You can alter your bash HISTFILESIZE and HISTTIMEFORMAT variables but it
is still a unstructured format with limited querying ability.

Recent does the following:

1. Logs current localtime, command text, current pid, command return value,
   working directory to an sqlite database in ``~/.recent.db``.

2. Logs history immediately, rather than at the close of the session.

3. Provides a command called recent for searching logs.

installation instructions
-------------------------

You need will need sqlite installed.

Install the recent pip package:

``pip install recent``

Add the following to your .bashrc or .bash_profile:

``export PROMPT_COMMAND='log-recent -r $? -c "$(HISTTIMEFORMAT= history 1)" -p $$'``

And start a new shell.

usage
-----

Look at your current history using recent:

``recent``

Search for a pattern as follows:

``recent git``

For more information see the help:

``recent -h``

Not currently recent doesn't integrate with bash commands such as
Ctrl-R, but this is in the pipeline.

You can directly query your history using the following:

``sqlite3 ~/.recent.db "select * from commands limit 10"``

dev installation instructions
-----------------------------

``git clone https://github.com/trengrj/recent && cd recent``

``pip install -e .``

security
--------

Please note, recent does not take into account enforcing logging
for security purposes. For this functionality on linux, have a
look at auditd http://people.redhat.com/sgrubb/audit/.
