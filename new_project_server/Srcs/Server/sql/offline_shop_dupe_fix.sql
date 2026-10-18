-- =====================================================================
-- OFFLINE_SHOP kapanis dupe fix - sema degisikligi (2026-07-25)
-- =====================================================================
-- player_gift.src_shop_item_id: gift satirinin turedigi player_shop_items.id
-- UNIQUE kisit sayesinde ayni pazar satiri IKI KEZ gift'lenemez (son savunma
-- hatti; kod tarafindaki claim-first fix'lerinin sema sigortasi).
-- NULL serbesttir (para odulleri vb. kaynaksiz satirlar); MariaDB'de UNIQUE
-- birden fazla NULL'a izin verir.
--
-- !!! DEPLOY SIRASI KRITIK !!!
-- Bu ALTER'lar yeni game binary'sinden ONCE calistirilmali. Kolon yokken yeni
-- binary'nin gift INSERT'leri "unknown column" ile duser (DUPE_GUARD sys_err)
-- ve kapanan pazarlarin itemleri gift'e YAZILAMAZ (kayip!).
--
-- Calistirma (player DB):
--   mysql player < offline_shop_dupe_fix.sql

ALTER TABLE player_gift ADD COLUMN src_shop_item_id INT UNSIGNED NULL DEFAULT NULL;
ALTER TABLE player_gift ADD UNIQUE KEY uk_gift_src_shop_item (src_shop_item_id);
