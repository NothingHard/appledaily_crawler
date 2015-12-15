#!/bin/bash
SESSIONNAME="crawler"

# new session with name $SESSIONNAME and window 0 named "base"
/usr/bin/tmux new-session -d -s $SESSIONNAME -n base
/usr/bin/tmux split-window -t $SESSIONNAME:0

/usr/bin/tmux select-pane -t 0
/usr/bin/tmux send-keys '/home/cslin/work/appledaily_crawler/crawler/watsi.sh' 'C-m'
/usr/bin/tmux select-pane -t 1
/usr/bin/tmux send-keys '/home/cslin/work/appledaily_crawler/crawler/appledaily.sh' 'C-m'

## switch the "base" window
/usr/bin/tmux select-window -t $SESSIONNAME:0
