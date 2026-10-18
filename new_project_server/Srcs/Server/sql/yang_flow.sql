-- ============================================================
-- ENABLE_YANG_FLOW_ANALYTICS - harita bazli yang giris analizi
-- LOG veritabanina uygulanir (game core'lar yang_flow'a yazar).
-- DEPLOY SIRASI: once bu SQL, sonra yeni game core acilir
-- (tablo yokken core INSERT deneyip syserr'e async query hatasi basar).
-- Yuk: core basina saatte (kaynak x harita) kadar satir, cok kucuk kalir.
-- ============================================================

CREATE TABLE IF NOT EXISTS yang_flow (
	id INT UNSIGNED NOT NULL AUTO_INCREMENT,
	time DATETIME NOT NULL,
	channel TINYINT UNSIGNED NOT NULL DEFAULT 0,
	map_index INT NOT NULL,
	source TINYINT UNSIGNED NOT NULL COMMENT '1=mob altini, 2=NPC satis, 3=quest odulu, 4=altin calma efsunu, 5=F5 hizli satis',
	gold BIGINT NOT NULL,
	cnt INT UNSIGNED NOT NULL COMMENT 'olay sayisi (kill/satis/odul adedi)',
	PRIMARY KEY (id),
	KEY ix_time (time),
	KEY ix_map_source (map_index, source)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- ------------------------------------------------------------
-- Ornek rapor sorgulari:
--
-- 1) Son 24 saatte oyuna giren yang, harita bazinda:
-- SELECT map_index,
--        SUM(CASE WHEN source=1 THEN gold ELSE 0 END) AS mob_altini,
--        SUM(CASE WHEN source=2 THEN gold ELSE 0 END) AS npc_satis,
--        SUM(CASE WHEN source=3 THEN gold ELSE 0 END) AS quest,
--        SUM(CASE WHEN source=4 THEN gold ELSE 0 END) AS altin_calma,
--        SUM(CASE WHEN source=5 THEN gold ELSE 0 END) AS f5_satis,
--        SUM(gold) AS toplam
-- FROM yang_flow
-- WHERE time >= NOW() - INTERVAL 1 DAY
-- GROUP BY map_index
-- ORDER BY toplam DESC;
--
-- 2) Kanal bazinda dagilim (ayni sorguya channel ekle):
-- ... GROUP BY channel, map_index ...
--
-- 3) Saatlik trend (tek harita):
-- SELECT DATE_FORMAT(time, '%Y-%m-%d %H:00') AS saat, source, SUM(gold)
-- FROM yang_flow WHERE map_index = 21
-- GROUP BY saat, source ORDER BY saat;
-- ------------------------------------------------------------
