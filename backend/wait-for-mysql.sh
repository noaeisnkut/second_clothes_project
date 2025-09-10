#!/bin/sh

# Debug info
echo "Waiting for MySQL at host: $DB_HOST, user: $DB_USER"

# מחכה עד שה-MySQL מוכן
until mysqladmin ping -h"$DB_HOST" -u"$DB_USER" -p"$DB_PASSWORD" --silent; do
   echo "Waiting for MySQL..."
   sleep 2
done

echo "MySQL is up!"
exec "$@"
