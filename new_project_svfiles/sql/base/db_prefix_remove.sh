#!/bin/sh

# MySQL connection details
DB_USER="root"
DB_PASSWORD="password"
DB_OLD_PREFIX=""
DB_NEW_PREFIX=""

echo "### duplicating the ${DB_OLD_PREFIX}XXX databases to ${DB_NEW_PREFIX}XXX"
mysql -u"$DB_USER" -p"$DB_PASSWORD" -e "CREATE DATABASE IF NOT EXISTS ${DB_NEW_PREFIX}account;"
mysqldump -u"$DB_USER" -p"$DB_PASSWORD" -v ${DB_OLD_PREFIX}account | mysql -u"$DB_USER" -p"$DB_PASSWORD" ${DB_NEW_PREFIX}account

mysql -u"$DB_USER" -p"$DB_PASSWORD" -e "CREATE DATABASE IF NOT EXISTS ${DB_NEW_PREFIX}common;"
mysqldump -u"$DB_USER" -p"$DB_PASSWORD" -v ${DB_OLD_PREFIX}common | mysql -u"$DB_USER" -p"$DB_PASSWORD" ${DB_NEW_PREFIX}common

mysql -u"$DB_USER" -p"$DB_PASSWORD" -e "CREATE DATABASE IF NOT EXISTS ${DB_NEW_PREFIX}log;"
mysqldump -u"$DB_USER" -p"$DB_PASSWORD" -v ${DB_OLD_PREFIX}log | mysql -u"$DB_USER" -p"$DB_PASSWORD" ${DB_NEW_PREFIX}log

mysql -u"$DB_USER" -p"$DB_PASSWORD" -e "CREATE DATABASE IF NOT EXISTS ${DB_NEW_PREFIX}player;"
mysqldump -u"$DB_USER" -p"$DB_PASSWORD" -v ${DB_OLD_PREFIX}player | mysql -u"$DB_USER" -p"$DB_PASSWORD" ${DB_NEW_PREFIX}player

mysql -u"$DB_USER" -p"$DB_PASSWORD" -e "CREATE DATABASE IF NOT EXISTS hotbackup;"



echo "### Checking mt2@localhost user..."
USER_EXISTS=$(mysql -u"$DB_USER" -p"$DB_PASSWORD" -N -B -e "SELECT EXISTS(SELECT 1 FROM mysql.user WHERE user = 'mt2' AND host = 'localhost');")
if [ "$USER_EXISTS" -eq 1 ]; then
  mysql -u"$DB_USER" -p"$DB_PASSWORD" -e "GRANT SELECT, INSERT, UPDATE, DELETE ON ${DB_NEW_PREFIX}account.* TO 'mt2'@'localhost';"
  mysql -u"$DB_USER" -p"$DB_PASSWORD" -e "GRANT SELECT, INSERT, UPDATE, DELETE ON ${DB_NEW_PREFIX}common.* TO 'mt2'@'localhost';"
  mysql -u"$DB_USER" -p"$DB_PASSWORD" -e "GRANT SELECT, INSERT, UPDATE, DELETE ON ${DB_NEW_PREFIX}log.* TO 'mt2'@'localhost';"
  mysql -u"$DB_USER" -p"$DB_PASSWORD" -e "GRANT SELECT, INSERT, UPDATE, DELETE ON ${DB_NEW_PREFIX}player.* TO 'mt2'@'localhost';"
  mysql -u"$DB_USER" -p"$DB_PASSWORD" -e "GRANT SELECT, INSERT, UPDATE, DELETE ON ${DB_NEW_PREFIX}hotbackup.* TO 'mt2'@'localhost';"
  echo "### Regranted privileges for mt2@localhost user."
else
  echo "### WARNING: mt2@localhost user does not exist in mysql.user table. Regrant it manually."
fi




echo "### Checking if protos@% user exists..."
USER_EXISTS=$(mysql -u"$DB_USER" -p"$DB_PASSWORD" -N -B -e "SELECT EXISTS(SELECT 1 FROM mysql.user WHERE user = 'protos' AND host = '%');")

if [ "$USER_EXISTS" -eq 1 ]; then
  echo "### Regranting protos@% user..."

  # Re-grant privileges
  mysql -u"$DB_USER" -p"$DB_PASSWORD" -e "GRANT SELECT ON ${DB_NEW_PREFIX}player.item_proto TO 'protos'@'%';"
  mysql -u"$DB_USER" -p"$DB_PASSWORD" -e "GRANT SELECT ON ${DB_NEW_PREFIX}player.mob_proto TO 'protos'@'%';"

  echo "### Regranted privileges for protos@% user."
else
  echo "### WARNING: protos@% user does not exist in mysql.user table. Regrant it manually if you use sql protos."
fi
