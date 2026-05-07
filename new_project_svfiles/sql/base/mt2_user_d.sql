INSERT IGNORE INTO mysql.user (user, host, password) VALUES ('mt2', 'localhost', PASSWORD('mt2'));
FLUSH PRIVILEGES;

GRANT SELECT, INSERT, UPDATE, DELETE ON `player`.* TO 'mt2'@'localhost';

GRANT SELECT, INSERT, UPDATE, DELETE ON `log`.* TO 'mt2'@'localhost';

GRANT SELECT, INSERT, UPDATE, DELETE ON `hotbackup`.* TO 'mt2'@'localhost';

GRANT SELECT, INSERT, UPDATE, DELETE ON `common`.* TO 'mt2'@'localhost';

GRANT SELECT, INSERT, UPDATE, DELETE ON `account`.* TO 'mt2'@'localhost';

