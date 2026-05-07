-- Gaya System v1: player.gem column + gaya_shop_items table
-- Run manually. Idempotent (IF NOT EXISTS / stored-proc guard).

DELIMITER $$
DROP PROCEDURE IF EXISTS add_col_if_missing$$
CREATE PROCEDURE add_col_if_missing(
    IN tbl VARCHAR(64),
    IN col_name VARCHAR(64),
    IN col_def  VARCHAR(255)
)
BEGIN
    SET @db = DATABASE();
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = @db AND TABLE_NAME = tbl AND COLUMN_NAME = col_name
    ) THEN
        SET @q = CONCAT('ALTER TABLE `', tbl, '` ADD COLUMN `', col_name, '` ', col_def);
        PREPARE stmt FROM @q;
        EXECUTE stmt;
        DEALLOCATE PREPARE stmt;
    END IF;
END$$
DELIMITER ;

CALL add_col_if_missing('player', 'gem', 'INT NOT NULL DEFAULT 0 AFTER `gold`');
CALL add_col_if_missing('player_deleted', 'gem', 'INT NOT NULL DEFAULT 0 AFTER `gold`');

DROP PROCEDURE IF EXISTS add_col_if_missing;

CREATE TABLE IF NOT EXISTS `gaya_shop_items` (
    `player_id`    INT UNSIGNED NOT NULL,
    `slot_index`   TINYINT UNSIGNED NOT NULL,
    `item_vnum`    INT UNSIGNED NOT NULL DEFAULT 0,
    `item_count`   INT UNSIGNED NOT NULL DEFAULT 1,
    `item_price`   BIGINT NOT NULL DEFAULT 0,
    `is_purchased` TINYINT UNSIGNED NOT NULL DEFAULT 0,
    `refreshed_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`player_id`, `slot_index`),
    KEY `idx_player_id` (`player_id`)
);
