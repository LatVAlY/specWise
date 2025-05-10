#!/bin/bash

PROCESS=${PROCESS}

if [ "$PROCESS" = "worker" ]; then
    celery -A app.worker worker --loglevel=info
    celery -A app.worker beat --loglevel=info
elif [ "$PROCESS" = "server" ]; then
    gunicorn -c gunicorn.conf.py main:app -b 0.0.0.0:8080
else
    printf "Please specify the type of process to run: 'worker' or 'server'\n"
fi
