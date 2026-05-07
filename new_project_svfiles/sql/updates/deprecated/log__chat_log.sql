/* new log table to store player/staff chat logs */
CREATE TABLE `chat_log` (
`where`  int unsigned NOT NULL ,
`who_id`  int unsigned NOT NULL ,
`who_name`  varchar(25) NOT NULL ,
`whom_id`  int unsigned NULL ,
`whom_name`  varchar(25) NULL ,
`type`  enum('NORMAL','WHISPER','PARTY','GUILD') NOT NULL ,
`msg`  varbinary(512) NOT NULL ,
`when`  datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ,
`ip`  varchar(15) NOT NULL
);
