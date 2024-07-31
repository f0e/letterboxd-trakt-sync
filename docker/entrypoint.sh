#!/bin/sh

if [ -z "$CRON_SCHEDULE" ]; then
    CRON_SCHEDULE="0 */12 * * *"
fi

if [ "$RUN_ONCE" == "true" ]; then
    echo 'RUN_ONCE=true, running script'

    source /app/docker/run.sh
fi

echo 'Started cron'

crontab /app/docker/crontab
echo "${CRON_SCHEDULE} /app/docker/run.sh" | crontab -

crond -f -l 8
