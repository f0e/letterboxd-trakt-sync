#!/bin/sh

if [ -z "$CRON_SCHEDULE" ]; then
    CRON_SCHEDULE="0 */12 * * *"
fi

if [ "$RUN_ON_START" == "true" ]; then
    echo 'RUN_ON_START=true, running script'

    source /app/docker/run.sh
fi

echo 'Started cron'

echo "${CRON_SCHEDULE} /app/docker/run.sh" | crontab -

crond -f -l 8
