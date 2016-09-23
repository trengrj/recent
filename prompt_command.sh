#/bin/bash
export PROMPT_COMMAND='log-recent -r $? -c "$(history 1)" -p $$'
