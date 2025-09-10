#!/bin/sh
until mysqladmin ping -h"$DB_HOST" -u"$DB_USER" -p"$DB_PASSWORD" --silent; do
   echo "Waiting for MySQL..."
   sleep 2
done
exec "$@"
