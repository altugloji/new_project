
# Get MySQL server version
mysql_version=$(mysql --version | awk '{print $5}')

## Create db struct and mt2 user with limited privileges
mysql -uroot -ppassword < base/db_create.sql


if [ "$(echo "$mysql_version" | awk -F'.' '{print $1"."$2}' )" = "8.0" ] || [ "$(echo "$mysql_version" | awk -F'.' '{print $1"."$2}' )" \> "8.0" ]; then
    # echo "MySQL version is 8.0 or higher: $mysql_version"
    mysql -uroot -ppassword < base/mt2_user_g.sql
elif [ "$(echo "$mysql_version" | awk -F'.' '{print $1"."$2}' )" = "5.7" ] || [ "$(echo "$mysql_version" | awk -F'.' '{print $1"."$2}' )" \> "5.7" ]; then
    # echo "MySQL version is 5.7 or higher: $mysql_version"
    mysql -uroot -ppassword < base/mt2_user_f.sql
elif [ "$(echo "$mysql_version" | awk -F'.' '{print $1"."$2}' )" = "5.6" ] || [ "$(echo "$mysql_version" | awk -F'.' '{print $1"."$2}' )" \> "5.6" ]; then
    # echo "MySQL version is 5.6 but not 5.7: $mysql_version"
    mysql -uroot -ppassword < base/mt2_user_d.sql
elif echo "$mysql_version" | grep -q "MariaDB"; then
    # echo "MariaDB is installed: $mysql_version"
    mysql -uroot -ppassword < base/mt2_user_g.sql
else
    echo "MySQL version is lower than 5.6 and not MariaDB: $mysql_version"
fi



## Create clean metin2 db struct
mysql -uroot -ppassword account < account.sql
mysql -uroot -ppassword common < common.sql
mysql -uroot -ppassword log < log.sql
mysql -uroot -ppassword player < player.sql

## Insert new features in metin2 db struct
mysql -uroot -ppassword player < updates/player__skill_proto.sql
mysql -uroot -ppassword player < updates/player__updates.sql

### NOTE: DON'T TOUCH updates/post/ queries! (they are just for rare cases!)
