#!/bin/sh
until mysqladmin ping --silent -h"$DB_HOST"; do
    echo "Waiting for MySQL..."
    sleep 2
done
exec "$@"
