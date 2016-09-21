#/bin/bash
export PROMPT_COMMAND='RET=$?;log-recent "$(history 1)" $$ $RET'
