#!/bin/bash
set -eou pipefail

source .env.local # SAS_TOKEN should be in here
export PGUSER=jknutson
export PGHOST=localhost
export PGDATABASE=mn-gis-projects

WORKING_DIR=/opt/weatherman

pushd $WORKING_DIR

case $1 in
        5min|10min)
        echo "select wm_update_latest_readings();" | psql > /dev/null
        echo "select json_agg(wm_latest_readings)->0 from wm_latest_readings where station='pico' limit 1" | psql -t -o ./current_conditions.json
        curl -s -X PUT -d "@./current_conditions.json" -H "x-ms-date: $(TZ=GMT date '+%a, %d %h %Y %H:%M:%S %Z')" -H "x-ms-blob-type: BlockBlob" "https://weatherman.blob.core.windows.net/%24web/current_conditions.json${SAS_TOKEN}"
        ;;

        hourly)
        echo "select wm_update_hourly_summaries();" | psql > /dev/null
        ;;

esac

popd
