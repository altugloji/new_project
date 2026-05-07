DROP TABLE IF EXISTS `priv_settings`;
CREATE TABLE `priv_settings` (
`priv_type`  enum('PLAYER','GUILD','EMPIRE') NOT NULL DEFAULT 'EMPIRE' COMMENT 'GUILD and PLAYER are untested.' ,
`id`  int UNSIGNED NOT NULL DEFAULT 0 COMMENT 'this is for empire_id, player_id or guild_id' ,
`type`  int UNSIGNED NOT NULL DEFAULT 4 COMMENT '1:item_drop, 2:gold_drop, 3:gold10_drop, 4:exp (1~4)' ,
`value`  int NOT NULL DEFAULT 0 COMMENT '0~1000%' ,
`duration`  datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ,
PRIMARY KEY (`priv_type`, `id`, `type`)
);

INSERT INTO `priv_settings` VALUES ('EMPIRE', '0', '1', '200', '2020-01-01 00:00:00');
INSERT INTO `priv_settings` VALUES ('EMPIRE', '0', '2', '200', '2020-01-01 00:00:00');
INSERT INTO `priv_settings` VALUES ('EMPIRE', '0', '3', '200', '2020-01-01 00:00:00');
INSERT INTO `priv_settings` VALUES ('EMPIRE', '0', '4', '200', '2020-01-01 00:00:00');
