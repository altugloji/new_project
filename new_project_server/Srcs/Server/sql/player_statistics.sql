-- ENABLE_PLAYER_STATISTICS: player.player tablosuna istatistik kolonlari
-- ONEMLI: Bu SQL, yeni game+db derlemeleri canliya alinmadan ONCE calistirilmalidir.
-- (db core player load SELECT'i bu kolonlari ister; kolon yoksa oyuncu yuklenemez.)
-- Kolonlar DEFAULT 0 oldugu icin mevcut oyuncular ve yeni karakter INSERT'i etkilenmez.

ALTER TABLE player.player
	ADD COLUMN st_dst_boss_cnt BIGINT NOT NULL DEFAULT 0,
	ADD COLUMN st_dst_stone_cnt BIGINT NOT NULL DEFAULT 0,
	ADD COLUMN st_max_boss_dmg BIGINT NOT NULL DEFAULT 0,
	ADD COLUMN st_max_stone_dmg BIGINT NOT NULL DEFAULT 0,
	ADD COLUMN st_max_player_dmg BIGINT NOT NULL DEFAULT 0,
	ADD COLUMN st_ronark_scores BIGINT NOT NULL DEFAULT 0;

-- Geri alma (gerekirse):
-- ALTER TABLE player.player
-- 	DROP COLUMN st_dst_boss_cnt,
-- 	DROP COLUMN st_dst_stone_cnt,
-- 	DROP COLUMN st_max_boss_dmg,
-- 	DROP COLUMN st_max_stone_dmg,
-- 	DROP COLUMN st_max_player_dmg,
-- 	DROP COLUMN st_ronark_scores;
