-- ============================================================================
-- ENABLE_IKASHOP_SEARCH - OPSIYONEL performans indexleri
-- ============================================================================
-- Sistem yeni tablo/kolon GEREKTIRMEZ; kalici veri mevcut player_shop /
-- player_shop_items(sold) / player_gift tablolarindadir. Bu iki index yalnizca
-- arama sorgusunu (WHERE sold=0 AND price/vnum ...) hizlandirir.
--
-- UYGULAMA: bakim penceresinde (dusuk trafik) calistirin; ALTER tabloyu kisa
-- sure kilitleyebilir. Tamamen atlanabilir - sorgu EXPLAIN olcumune gore karar.
-- GERI ALMA: ALTER TABLE player_shop_items DROP INDEX ix_ikasearch_sold_vnum,
--            DROP INDEX ix_ikasearch_sold_price;
-- ============================================================================

USE player;

ALTER TABLE player_shop_items
	ADD INDEX ix_ikasearch_sold_vnum (sold, vnum),
	ADD INDEX ix_ikasearch_sold_price (sold, price);
