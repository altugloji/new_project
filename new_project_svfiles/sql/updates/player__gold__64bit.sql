ALTER TABLE `player`
MODIFY COLUMN `gold` bigint NOT NULL DEFAULT 0 AFTER `exp`;
ALTER TABLE `player_deleted`
MODIFY COLUMN `gold` bigint NOT NULL DEFAULT 0 AFTER `exp`;
