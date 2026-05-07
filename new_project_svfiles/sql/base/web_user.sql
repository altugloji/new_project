/* choose user n password generated from https://passwordsgenerator.net/ without special symbols possibly; length 16 is ok */
CREATE USER 'web_WUeJ526zu8mz'@'%' IDENTIFIED BY 'XBMyq6wubfXqhKck';

GRANT SELECT, INSERT, UPDATE, DELETE ON `player`.* TO 'web_WUeJ526zu8mz'@'%';

GRANT SELECT, INSERT, UPDATE, DELETE ON `log`.* TO 'web_WUeJ526zu8mz'@'%';

GRANT SELECT, INSERT, UPDATE, DELETE ON `hotbackup`.* TO 'web_WUeJ526zu8mz'@'%';

GRANT SELECT, INSERT, UPDATE, DELETE ON `common`.* TO 'web_WUeJ526zu8mz'@'%';

GRANT SELECT, INSERT, UPDATE, DELETE ON `account`.* TO 'web_WUeJ526zu8mz'@'%';

