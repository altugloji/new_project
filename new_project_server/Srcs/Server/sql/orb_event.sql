-- ============================================================================
-- Kure Avi (ENABLE_ORB_EVENT) - player DB tablolari
-- ----------------------------------------------------------------------------
-- Dagitim sirasi: 1) bu dosya player DB'ye (bir kez; IF NOT EXISTS idempotent)
--                 2) game rebuild (ENABLE_ORB_EVENT) + TUM core'lar birlikte restart (GG 51)
-- player_gift tablosu DEGISMEZ (odul satirlari mevcut GIFT_SYSTEM kolonlariyla eklenir).
-- db core yeniden derlenmez.
-- Saat: start_time/end_time game sunucusu saatinden FROM_UNIXTIME(eid) ile yazilir ve odul kontrolu
--   UNIX_TIMESTAMP(end_time) ile yine game saatine gore yapilir (DB oturum saat dilimi gidis-donusu
--   tutarli). distributed_at=NOW() DB saatidir: game ve DB sunucu saatleri NTP ile senkron tutulmali
--   (fark 60 sn altinda kalmali).
-- ============================================================================

USE player;

-- tur kaydi: event_id = tur baslangic epoch'u (program: saat basi; test: /orb_admin start ani)
CREATE TABLE IF NOT EXISTS orb_event (
  event_id       INT UNSIGNED     NOT NULL,
  start_time     DATETIME         NOT NULL,
  end_time       DATETIME         NOT NULL,
  state          TINYINT UNSIGNED NOT NULL DEFAULT 0,   -- 0 aktif/bekliyor, 3 odul dagitildi, 4 iptal (odulsuz)
  dist_token     INT UNSIGNED     NOT NULL DEFAULT 0,   -- dagitim jetonu (cift dagitim kilidi)
  participants   INT UNSIGNED     NOT NULL DEFAULT 0,
  distributed_at DATETIME         NULL,
  PRIMARY KEY (event_id),
  KEY idx_state_end (state, end_time)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- core basina MUTLAK skor satiri (saniyede bir idempotent upsert; toplam = SUM over core_id)
CREATE TABLE IF NOT EXISTS orb_event_score (
  event_id   INT UNSIGNED      NOT NULL,
  pid        INT UNSIGNED      NOT NULL,
  core_id    SMALLINT UNSIGNED NOT NULL,                -- mother_port
  score      INT               NOT NULL DEFAULT 0,   -- ISARETLI: beyaz kure eksi puan, core toplami negatif olabilir
  blue_cnt   INT UNSIGNED      NOT NULL DEFAULT 0,
  white_cnt  INT UNSIGNED      NOT NULL DEFAULT 0,
  last_ts    BIGINT UNSIGNED   NOT NULL DEFAULT 0,      -- son toplama ms epoch (beraberlik: erken olan ustte)
  PRIMARY KEY (event_id, pid, core_id),
  KEY idx_event_score (event_id, score)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- dagitilan oduller (bir satir / kazanan; player_gift'e buradan kopyalanir)
CREATE TABLE IF NOT EXISTS orb_event_reward (
  event_id     INT UNSIGNED NOT NULL,
  pid          INT UNSIGNED NOT NULL,
  rank_no      INT UNSIGNED NOT NULL,
  score        INT NOT NULL,
  reward_vnum  INT UNSIGNED NOT NULL,
  reward_count INT UNSIGNED NOT NULL,
  created_at   TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (event_id, pid),
  UNIQUE KEY uk_event_rank (event_id, rank_no)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- Tablolar daha once score INT UNSIGNED ile olusturulduysa (v1) isaretli puana gecis;
-- taze INT kolonda no-op (idempotent), bu yuzden her kurulumda calistirilir:
ALTER TABLE orb_event_score  MODIFY score INT NOT NULL DEFAULT 0;
ALTER TABLE orb_event_reward MODIFY score INT NOT NULL;
