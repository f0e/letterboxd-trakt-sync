#!/bin/sh

cd /app

if ! pgrep -f 'python -m letterboxd_trakt.main' > /dev/null; then
    echo 'Started script'
    python -u -m letterboxd_trakt.main
fi
