#!/usr/bin/env sh

STATUS=$(celery -A celeryconfig status | grep $(hostname) | awk '{print $3}')

if [ "${STATUS}" = "OK" ]; then
    exit 0
else
    exit 1
fi