#!/bin/sh
if [ -z "$DB_HOST" ]; then
  echo "DB_HOST is not set"
  exit 1
fi

until mysqladmin ping -h"$DB_HOST" --silent; do
    echo "Waiting for MySQL..."
    sleep 2
done

exec "$@"
