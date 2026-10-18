-- ============================================================================
-- ENABLE_LUCKY_DRAW - Sansli Cekilis etkinligi tablolari (ZORUNLU)
-- ============================================================================
-- Sistem 3 tablo kullanir (hepsi player DB'sinde):
--   luckydraw_config  : tek satir ayar (limitler, katilim bedeli, aktiflik).
--                       KOLON SIRASI ONEMLIDIR - kod SELECT * ile indeksten okur.
--   luckydraw_joiners : bilet kayitlari (her katilim = 1 satir; etkinlik
--                       baslarken DELETE ile temizlenir).
--   luckydraw_winners : 3 sabit satir (winner_place 1..3). reward1..5_vnum
--                       kolonlarina GM odul itemlerini elle yazar; cekilis
--                       bitince winner_pid/winner_name doldurulur, is_taken=0
--                       yapilir; oyuncu /lucky_draw 3 ile odulu alinca 1 olur.
--
-- ANLAM NOTU: max_join_count = OYUN GENELI toplam bilet kapasitesi,
--             max_ticket_count = OYUNCU BASINA bilet limiti.
--             (Kod bu sekilde kullanir; eski kaynaktaki yorumlar terstir.)
--
-- UYGULAMA: server acilmadan once bir kez calistirin (TAZE kurulum):
--           mysql -u<user> -p < luckydraw.sql
-- DIKKAT: v1 tablolari zaten kuruluysa bu dosya config'e v2 kolonlarini EKLEMEZ
--         (CREATE IF NOT EXISTS atlanir) - o durumda luckydraw_v2_upgrade.sql
--         calistirin. Server eski semayi gorurse syserr'e uyari yazar.
-- GERI ALMA: DROP TABLE player.luckydraw_config, player.luckydraw_joiners,
--            player.luckydraw_winners;
-- ============================================================================

USE player;

CREATE TABLE IF NOT EXISTS `luckydraw_config` (
	`id`                 INT UNSIGNED     NOT NULL AUTO_INCREMENT,  -- [0]
	`max_join_count`     INT UNSIGNED     NOT NULL DEFAULT 10000,   -- [1] oyun geneli toplam bilet kapasitesi
	`max_ticket_count`   INT UNSIGNED     NOT NULL DEFAULT 10,      -- [2] oyuncu basina bilet limiti
	`needed_item_vnum`   INT UNSIGNED     NOT NULL DEFAULT 0,       -- [3] katilim sarti 1. item (0 = yok)
	`needed_item_count`  INT UNSIGNED     NOT NULL DEFAULT 0,       -- [4] 1. item adedi
	`needed_yang`        BIGINT UNSIGNED  NOT NULL DEFAULT 0,       -- [5] katilim ucreti yang (0 = ucretsiz)
	`is_activated`       TINYINT UNSIGNED NOT NULL DEFAULT 0,       -- [6] etkinlik acik mi (start/end komutu yonetir)
	`needed_item_vnum2`  INT UNSIGNED     NOT NULL DEFAULT 0,       -- [7] katilim sarti 2. item
	`needed_item_count2` INT UNSIGNED     NOT NULL DEFAULT 0,       -- [8]
	`needed_item_vnum3`  INT UNSIGNED     NOT NULL DEFAULT 0,       -- [9] katilim sarti 3. item
	`needed_item_count3` INT UNSIGNED     NOT NULL DEFAULT 0,       -- [10]
	`needed_item_vnum4`  INT UNSIGNED     NOT NULL DEFAULT 0,       -- [11] katilim sarti 4. item
	`needed_item_count4` INT UNSIGNED     NOT NULL DEFAULT 0,       -- [12]
	`needed_item_vnum5`  INT UNSIGNED     NOT NULL DEFAULT 0,       -- [13] katilim sarti 5. item
	`needed_item_count5` INT UNSIGNED     NOT NULL DEFAULT 0,       -- [14]
	PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

INSERT INTO `luckydraw_config` (`id`, `max_join_count`, `max_ticket_count`, `needed_item_vnum`, `needed_item_count`, `needed_yang`, `is_activated`)
VALUES (1, 10000, 10, 0, 0, 100000, 0)
ON DUPLICATE KEY UPDATE `id` = `id`;

CREATE TABLE IF NOT EXISTS `luckydraw_joiners` (
	`id`          INT UNSIGNED NOT NULL AUTO_INCREMENT,            -- AUTO_INCREMENT sart: kod uiInsertID != 0 ile basariyi anlar
	`account_id`  INT UNSIGNED NOT NULL DEFAULT 0,
	`player_id`   INT UNSIGNED NOT NULL DEFAULT 0,
	`player_name` VARCHAR(32)  NOT NULL DEFAULT '',
	`join_time`   DATETIME     NOT NULL,
	PRIMARY KEY (`id`),
	KEY `player_id` (`player_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

CREATE TABLE IF NOT EXISTS `luckydraw_winners` (
	`winner_place` TINYINT UNSIGNED NOT NULL,                      -- [0] 1..3
	`winner_pid`   INT UNSIGNED     NOT NULL DEFAULT 0,            -- [1]
	`winner_name`  VARCHAR(32)      NOT NULL DEFAULT '',           -- [2]
	`reward1_vnum` INT UNSIGNED     NOT NULL DEFAULT 0,            -- [3] bu siradaki kazananin odul itemleri (GM elle ayarlar)
	`reward2_vnum` INT UNSIGNED     NOT NULL DEFAULT 0,            -- [4]
	`reward3_vnum` INT UNSIGNED     NOT NULL DEFAULT 0,            -- [5]
	`reward4_vnum` INT UNSIGNED     NOT NULL DEFAULT 0,            -- [6]
	`reward5_vnum` INT UNSIGNED     NOT NULL DEFAULT 0,            -- [7]
	`is_taken`     TINYINT UNSIGNED NOT NULL DEFAULT 0,            -- [8] odul teslim edildi mi (yeni cekiliste kod 0'a ceker)
	PRIMARY KEY (`winner_place`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

INSERT INTO `luckydraw_winners` (`winner_place`, `winner_pid`, `winner_name`, `reward1_vnum`, `reward2_vnum`, `reward3_vnum`, `reward4_vnum`, `reward5_vnum`, `is_taken`)
VALUES (1, 0, '', 0, 0, 0, 0, 0, 0), (2, 0, '', 0, 0, 0, 0, 0, 0), (3, 0, '', 0, 0, 0, 0, 0, 0),
       (4, 0, '', 0, 0, 0, 0, 0, 0), (5, 0, '', 0, 0, 0, 0, 0, 0)
ON DUPLICATE KEY UPDATE `winner_place` = `winner_place`;
