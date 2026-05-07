ALTER TABLE `player`
ADD COLUMN `part_acce` int(11) UNSIGNED NOT NULL DEFAULT 0 AFTER `part_hair`;

ALTER TABLE `player_deleted`
ADD COLUMN `part_acce` int(11) UNSIGNED NOT NULL DEFAULT 0 AFTER `part_hair`;
