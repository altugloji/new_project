/*
SELECT * FROM `mob_proto_004_completo` WHERE `mount_capacity` <> '0';
^([0-9]+)\t([0-9]+)$
update mob_proto set mount_capacity=$2 where vnum=$1 limit 1;
*/
update mob_proto set mount_capacity=1 where vnum=1191 limit 1;
update mob_proto set mount_capacity=1 where vnum=1192 limit 1;
