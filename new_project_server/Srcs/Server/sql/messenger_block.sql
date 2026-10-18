-- ============================================================
-- ENABLE_MESSENGER_BLOCK - Oyuncu Engelleme Sistemi
-- Bu tablo PLAYER veritabanina uygulanir (messenger_list ile ayni DB).
-- Not: kolon sirasi onemlidir; game kodu kolon adi belirtmeden
--   INSERT INTO messenger_block_list VALUES ('hesap', 'engellenen', NOW())
-- seklinde yazar (account, companion, block_date sirasi degismemeli).
-- ============================================================

CREATE TABLE IF NOT EXISTS `messenger_block_list` (
	`account`    varchar(24) NOT NULL DEFAULT '',
	`companion`  varchar(24) NOT NULL DEFAULT '',
	`block_date` datetime    NOT NULL DEFAULT '0000-00-00 00:00:00',
	PRIMARY KEY (`account`,`companion`),
	KEY `companion` (`companion`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;

-- Istege bagli temizlik: karakteri silinmis oyuncularin bayat kayitlarini kaldirmak icin
-- (karakter silme akisi bu tabloyu otomatik temizlemez; ara sira elle calistirilabilir):
-- DELETE bl FROM messenger_block_list bl
--   LEFT JOIN player p1 ON p1.name = bl.account
--   LEFT JOIN player p2 ON p2.name = bl.companion
--  WHERE p1.id IS NULL OR p2.id IS NULL;
