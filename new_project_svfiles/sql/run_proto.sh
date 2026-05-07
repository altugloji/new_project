## Additionally for the protos when you will unpack them with Mysql2Proto
mysql -uroot -ppassword player < protos/item_proto.sql
mysql -uroot -ppassword player < protos/mob_proto.sql
# mysql -uroot -ppassword player < protos/item_names.sql
# mysql -uroot -ppassword player < protos/mob_names.sql

## Additionally to fix the mount's invisible mobs issue
mysql -uroot -ppassword player < protos/mob_proto__updates.sql

## Additionally to fix the missing values in the official mob proto
mysql -uroot -ppassword player < protos/mob_proto__default__dam_multiply.sql
mysql -uroot -ppassword player < protos/mob_proto__default__gold_minmax.sql
mysql -uroot -ppassword player < protos/mob_proto__default__mount_capacity.sql
mysql -uroot -ppassword player < protos/mob_proto__default__polymorph_item.sql
mysql -uroot -ppassword player < protos/mob_proto__default__resurrection_vnum.sql
mysql -uroot -ppassword player < protos/mob_proto__default__setRaceFlag_string.sql
mysql -uroot -ppassword player < protos/mob_proto__default__skill_all.sql
mysql -uroot -ppassword player < protos/mob_proto__default__sp_all.sql

mysql -uroot -ppassword player < protos/item_proto__acce_absorb.sql

# mysql -uroot -ppassword player < protos/item_proto__adjust__mount_seals.sql
# mysql -uroot -ppassword player < protos/item_proto__adjust__pet_seals.sql

### NOTE: DON'T TOUCH updates/post/ queries! (they are just for rare cases!)
