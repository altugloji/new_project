-- ============================================================================
-- ENABLE_GLOVE_SYSTEM + ENABLE_GLOVE_RANDOM_ATTR kurulum SQL'i
-- Hedef DB: player
--
-- ONEMLI SIRA: Bu dosya, define'lari acik yeni db/game binary'leri
-- DEPLOY EDILMEDEN ONCE uygulanmali! (Yeni db core boot'ta item_attr ve
-- item_attr_rare tablolarindan 'glove' kolonunu SELECT eder; kolon yoksa
-- "no result from item_attr" hatasiyla boot ETMEZ.)
-- Kolonlar eklendikten sonra eski binary calismaya devam eder (SELECT isimle
-- yapildigi icin fazla kolon zarar vermez) - yani SQL'i onceden uygulamak guvenlidir.
-- ============================================================================

USE player;

-- 1) Iki tabloya da 'glove' kolonu (kolon adi birebir 'glove' olmali)
--    (IF NOT EXISTS: MariaDB'de dosyanin ikinci kez calistirilmasi hata vermez)
ALTER TABLE item_attr      ADD COLUMN IF NOT EXISTS glove tinyint(4) NOT NULL DEFAULT 0 AFTER ear;
ALTER TABLE item_attr_rare ADD COLUMN IF NOT EXISTS glove tinyint(4) NOT NULL DEFAULT 0 AFTER ear;

-- 2) Nazar Tilsimi (71202) efsun havuzu: item_attr_rare'de glove > 0 olan satirlar
--    havuza girer; efsun secim orani ayni satirin 'prob' kolonudur, seviye ise
--    1..glove (en fazla 5) arasi rastgele gelir ve deger lv1..lv5 kolonundan okunur.
--    (Bir seviyenin lv kolonu 0/bos ise dolu olan ust seviyeye yuvarlanir;
--    tablodaki satirlarda sadece lv1 doluysa efsunlar fiilen tek seviyeli gelir.)
--
--    Baslangic olarak MEVCUT TUM rare efsunlari tavan 5 ile aciyoruz:
UPDATE item_attr_rare SET glove = 5;

--    Havuzu daraltmak / tavani dusurmek icin ornekler:
--    UPDATE item_attr_rare SET glove = 0 WHERE apply = 'MAX_HP';      -- havuzdan cikar
--    UPDATE item_attr_rare SET glove = 1 WHERE apply = 'ATT_SPEED';   -- sadece lv1 gelsin
--    Oranlari degistirmek icin 'prob' kolonunu guncelleyin (yeniden boot gerekir).
--
--    SINIR UYARILARI: lv1..lv5 degerleri -32767..32767 araliginda kalmali
--    (item efsun degeri short'tur, asan deger sessizce kirpilir/sarar);
--    'prob' degerlerinin TOPLAMI da makul kalmali (int araligi; milyonlar yeter).

-- 3) item_attr.glove kasitli olarak 0 birakildi: 71202 normal efsun tasi
--    (g_map_itemAttr) yolunu kullanmiyor; eldiven tipi item eklenmedikce
--    bu kolonun dolu olmasi gerekmez.

-- ============================================================================
-- GERI ALMA (rollback):
-- ALTER TABLE item_attr      DROP COLUMN glove;
-- ALTER TABLE item_attr_rare DROP COLUMN glove;
-- (Geri almadan once ENABLE_GLOVE_SYSTEM kapali binary'ler deploy edilmis olmali,
--  aksi halde db core boot edemez.)
-- ============================================================================
