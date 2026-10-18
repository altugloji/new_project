-- ============================================================================
-- ENABLE_LUCKY_DRAW v2 YUKSELTMESI (v1 tablolari KURULMUSSA calistirin)
-- ============================================================================
-- v2 yenilikleri: 5 kazanan (3 -> 5), 5 farkli katilim itemi (1 -> 5),
--                 pencerede katilimci listesi.
-- Kolonlar SONA eklenir: kod SELECT * ile [7]..[14] indekslerinden okur,
-- mevcut [0]..[6] indeksleri DEGISMEZ. Kolon sirasina dokunmayin.
--
-- Taze kurulumda bu dosyaya gerek YOKTUR (luckydraw.sql v2 semasini icerir).
-- UYGULAMA: server kapaliyken bir kez calistirin.
-- GERI ALMA: ALTER TABLE player.luckydraw_config
--              DROP COLUMN needed_item_vnum2, DROP COLUMN needed_item_count2,
--              DROP COLUMN needed_item_vnum3, DROP COLUMN needed_item_count3,
--              DROP COLUMN needed_item_vnum4, DROP COLUMN needed_item_count4,
--              DROP COLUMN needed_item_vnum5, DROP COLUMN needed_item_count5;
--            DELETE FROM player.luckydraw_winners WHERE winner_place IN (4,5);
-- ============================================================================

USE player;

-- IF NOT EXISTS (MariaDB 10.0.2+): betik idempotenttir, tekrar calistirilabilir
ALTER TABLE `luckydraw_config`
	ADD COLUMN IF NOT EXISTS `needed_item_vnum2`  INT UNSIGNED NOT NULL DEFAULT 0,
	ADD COLUMN IF NOT EXISTS `needed_item_count2` INT UNSIGNED NOT NULL DEFAULT 0,
	ADD COLUMN IF NOT EXISTS `needed_item_vnum3`  INT UNSIGNED NOT NULL DEFAULT 0,
	ADD COLUMN IF NOT EXISTS `needed_item_count3` INT UNSIGNED NOT NULL DEFAULT 0,
	ADD COLUMN IF NOT EXISTS `needed_item_vnum4`  INT UNSIGNED NOT NULL DEFAULT 0,
	ADD COLUMN IF NOT EXISTS `needed_item_count4` INT UNSIGNED NOT NULL DEFAULT 0,
	ADD COLUMN IF NOT EXISTS `needed_item_vnum5`  INT UNSIGNED NOT NULL DEFAULT 0,
	ADD COLUMN IF NOT EXISTS `needed_item_count5` INT UNSIGNED NOT NULL DEFAULT 0;

INSERT INTO `luckydraw_winners` (`winner_place`, `winner_pid`, `winner_name`, `reward1_vnum`, `reward2_vnum`, `reward3_vnum`, `reward4_vnum`, `reward5_vnum`, `is_taken`)
VALUES (4, 0, '', 0, 0, 0, 0, 0, 0), (5, 0, '', 0, 0, 0, 0, 0, 0)
ON DUPLICATE KEY UPDATE `winner_place` = `winner_place`;
