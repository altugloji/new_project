-- ============================================================================
-- ENABLE_SOULBIND_SYSTEM (Ruha Baglama: Baglama Parsomeni 50263 /
-- Ayirma Parsomeni 50264) kurulum SQL'i
-- Hedef DB: player
--
-- ONEMLI SIRA: Bu dosya, define'i acik yeni db/game binary'leri DEPLOY
-- EDILMEDEN ONCE uygulanmali! Yeni db core, item tablosundan 'sealbind'
-- kolonunu ISIMLE SELECT eder ve her item kaydinda ISIMLE yazar. Kolon yoksa:
--   * karakter item SELECT'i duser -> oyuncular item'siz (bos envanter /
--     ekipman) girer,
--   * depo / nesne market acilmaz, guvenli ticaret item'leri gelmez,
--   * item kayitlari "Unknown column 'sealbind'" ile duser (hicbir item
--     degisikligi diske yazilmaz).
-- Kolon eklendikten sonra ESKI binary calismaya devam eder (eski sorgular
-- kolonlari isimle okur/yazar, fazla kolon zarar vermez; DEFAULT 0 = bagli
-- degil) - yani SQL'i onceden uygulamak guvenlidir (ALTER'in suresi / tablo
-- kilidi icin asagidaki "AFTER verilmedi" notuna bakin).
--
-- item.sealbind degerleri:
--    0 = serbest (ruha bagli degil)
--   -1 = kalici ruha bagli (Baglama Parsomeni)
--   >0 = ayirma suruyor: bagin kalkacagi unix zamani (Ayirma Parsomeni)
-- Kolon ISARETLI (signed) INT olmali, cunku -1 yazilir: UNSIGNED / TINYINT
-- YAPMAYIN. NOT NULL DEFAULT 0 olmali (db core NULL hucreyi 0 = serbest okur).
--
-- AFTER verilmedi, kolon sona eklenir: butun sorgular kolonu isimle kullanir,
-- sona ekleme MariaDB 10.3+ ve InnoDB tabloda anliktir (tablo yeniden
-- yazilmaz). Daha eski surumde VEYA item tablosu MyISAM/Aria ise ALTER, item
-- tablosunu (player DB'nin en buyuk tablosu) kopyalar ve o sirada kilitler ->
-- sakin saatte / core'lar kapaliyken calistirin.
-- (Tablo motorunu gormek icin: SHOW TABLE STATUS LIKE 'item';)
--
-- TABLE_POSTFIX: db CONFIG dosyasinda TABLE_POSTFIX tanimliysa tablo adi
-- item<postfix> olur; asagidaki 'item' adlarini ona gore degistirin
-- (varsayilan: tanimsiz -> tablo adi 'item').
-- ============================================================================

USE player;

-- (IF NOT EXISTS: MariaDB'de dosyanin ikinci kez calistirilmasi hata vermez)
ALTER TABLE item ADD COLUMN IF NOT EXISTS sealbind INT(11) NOT NULL DEFAULT 0;

-- Kontrol (yeni db core'u baslatmadan ONCE): tek satir donmeli ve
-- Type = int(11), Null = NO, Default = 0 olmali.
SHOW COLUMNS FROM item LIKE 'sealbind';

-- Kolon bu dosyadan once zaten varsa (ornegin eski bir dump'tan) IF NOT EXISTS
-- ona dokunmaz. Yukaridaki kontrol farkli bir tip / unsigned / Null = YES
-- gosterirse su iki satiri elle calistirin:
-- UPDATE item SET sealbind = 0 WHERE sealbind IS NULL;
-- ALTER TABLE item MODIFY COLUMN sealbind INT(11) NOT NULL DEFAULT 0;

-- Veri kontrolu (define ACIK binary'ler ILK KEZ baslatilmadan ONCE bakin; sorgu
-- tum item tablosunu tarar): kolon bu dosyayla yeni eklendiyse bagli_esya = 0
-- doner. 0 DEGILSE kolon eski bir dump'tan dolu gelmistir: yeni binary'ler bu
-- degerleri gercek bag sayar ve esya, o an kimin uzerindeyse (kendisi
-- baglamamis olsa bile) ona ruha bagli gorunur. Temizlemek icin, define ACIK
-- db core'u baslatmadan ONCE (db core kapaliyken; acikken item cache degeri
-- geri yazar):
-- UPDATE item SET sealbind = 0 WHERE sealbind <> 0;
-- DIKKAT: sistem canliya alindiktan SONRA bu sayi dogal olarak 0 olmaz; o zaman
-- UPDATE'i CALISTIRMAYIN - oyuncularin gercek baglarini siler.
SELECT COUNT(*) AS bagli_esya, MIN(sealbind) AS en_kucuk,
       MAX(sealbind) AS en_buyuk FROM item WHERE sealbind <> 0;

-- ============================================================================
-- GERI ALMA (rollback):
-- ALTER TABLE item DROP COLUMN sealbind;
-- (Geri almadan once ENABLE_SOULBIND_SYSTEM KAPALI db+game binary'leri deploy
--  edilmis olmali, aksi halde item yukleme/kaydetme sorgulari duser.
--  DROP ile butun ruha baglama bilgisi kalici olarak silinir.)
--
-- GECICI KAPATMA (define KAPALI binary + kolon BIRAKILIR): kapali binary'ler
-- sealbind'i ne okur ne yazar, degerler tabloda aynen kalir. Bu surede bagli
-- esya ticaret / guvenli ticaret ile el degistirebilir; define yeniden
-- ACILDIGINDA bag, esya o an kimdeyse onun uzerinde yeniden gecerli olur (yeni
-- sahip Ayirma Parsomeni 50264 + bekleme suresi ile cozer). Bunu istemiyorsaniz
-- yeniden acmadan once, core'lar kapaliyken:
-- UPDATE item SET sealbind = 0 WHERE sealbind <> 0;
-- (BUTUN baglari siler; el degistirmis esyayi digerlerinden ayiran bilgi yok.)
-- ============================================================================
