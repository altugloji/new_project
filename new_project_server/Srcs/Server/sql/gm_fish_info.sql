-- GM Balik Bilgisi (ENABLE_GM_FISH_INFO) - log DB indeksi
-- /fish_info sorgusu: WHERE player_name = ? ORDER BY take_time DESC LIMIT 500
--
-- NEDEN GEREKLI: sorgu LogManager'in tek async SQL thread'inden gider; ayni thread
-- TUM log INSERT'lerini de isler. fishing_log buyukse indekssiz tam tablo taramasi
-- log kuyrugunu saniyelerce geriletebilir. Bu bilesik indeks WHERE + ORDER BY'i
-- birlikte karsilar, sorgu aninda doner.
--
-- UYGULAMA (log DB'nin oldugu MySQL sunucusunda, ornegin 185.128.112.193):
--   mysql -u root -p log < gm_fish_info.sql
-- Buyuk tabloda indeks olusturma surebilir; oyun calisirken de uygulanabilir
-- (InnoDB online DDL), ama sakin bir saatte yapilmasi onerilir.

ALTER TABLE fishing_log
    ADD INDEX idx_fishinfo_player_time (player_name, take_time);
