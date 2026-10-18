-- ENABLE_PLAYER_STATISTICS ek: isimli boss kesim siralamalari (Aylik Siralama sekmesi)
-- player_statistics.sql'den SONRA (veya bagimsiz) calistirilabilir; yeni game core
-- canliya alinmadan ONCE bu tablo olusturulmalidir (async INSERT'ler bu tabloya yazar).
--
-- boss_group eslesmesi (statistics_rank.cpp GetBossGroupByVnum ile ayni):
--   0 = Lusifer (1093)
--   1 = Azrail (2598)
--   2 = General (2491, 2492, 2494, 2495)
--   3 = Cadi (1192)
--   4 = Ejder / BeranSetaou (2493)

CREATE TABLE IF NOT EXISTS player.boss_kill_ranking (
	pid INT UNSIGNED NOT NULL,
	boss_group TINYINT UNSIGNED NOT NULL,
	kill_count BIGINT NOT NULL DEFAULT 0,
	PRIMARY KEY (pid, boss_group),
	KEY idx_group_count (boss_group, kill_count)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- Geri alma (gerekirse):
-- DROP TABLE player.boss_kill_ranking;
