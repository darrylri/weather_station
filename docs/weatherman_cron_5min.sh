#!/bin/bash

echo "select wm_update_latest_readings();" | psql -h localhost -U jknutson -d mn-gis-projects
# echo "\copy (select json_agg(wm_latest_readings)->0 from wm_latest_readings where station='pico' limit 1) to stdout quote '$'" | psql -h localhost -U jknutson -d mn-gis-projects > /var/www/html/current_conditions.json
echo "select json_agg(wm_latest_readings)->0 from wm_latest_readings where station='pico' limit 1" | psql -t -h localhost -U jknutson -d mn-gis-projects 2>/dev/null > /var/www/html/current_conditions.json
cat /var/www/html/current_conditions.json
curl -s -X PUT -d "@/var/www/html/current_conditions.json" -H "x-ms-date: $(TZ=GMT date '+%a, %d %h %Y %H:%M:%S %Z')" -H "x-ms-blob-type: BlockBlob" "https://weatherman.blob.core.windows.net/%24web/current_conditions.json${SAS_TOKEN}"
