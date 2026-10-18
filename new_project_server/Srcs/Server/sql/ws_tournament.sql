-- ============================================================================
-- WS 1v1 Turnuva sistemi (ENABLE_WS_TOURNAMENT) - player DB'ye uygulanir
-- KURULUM SIRASI ONEMLI: bu dosya, yeni game core'lar acilmadan ONCE uygulanmali.
-- Tablolar yoksa sistem kendini devre disi birakir (boot'ta syserr yazar).
-- ============================================================================

USE player;

-- Turnuva ana kaydi
-- status: 1=kayit 2=devam 3=bitti 4=iptal(boot recovery) 5=iptal(gm/katilim) 6=kazanansiz
CREATE TABLE IF NOT EXISTS ws_tournament (
	id INT UNSIGNED NOT NULL AUTO_INCREMENT,
	status TINYINT UNSIGNED NOT NULL DEFAULT 1,
	fee_gold BIGINT NOT NULL DEFAULT 0,
	set_count TINYINT UNSIGNED NOT NULL DEFAULT 3,
	match_minutes TINYINT UNSIGNED NOT NULL DEFAULT 5,
	min_level TINYINT UNSIGNED NOT NULL DEFAULT 1,
	max_level TINYINT UNSIGNED NOT NULL DEFAULT 135,
	job_filter TINYINT UNSIGNED NOT NULL DEFAULT 0,
	rake_pct TINYINT UNSIGNED NOT NULL DEFAULT 15,
	winner_pid INT UNSIGNED NOT NULL DEFAULT 0,
	winner_name VARCHAR(24) NOT NULL DEFAULT '',
	pool_gold BIGINT NOT NULL DEFAULT 0,
	created_by VARCHAR(24) NOT NULL DEFAULT '',
	created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
	finished_at DATETIME NULL DEFAULT NULL,
	PRIMARY KEY (id),
	KEY status_idx (status)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- Katilimcilar (escrow kaydi: ucret kesildigi anda satir yazilir)
-- status: 0=aktif 1=elendi 2=dq 3=sampiyon ; refunded: iade claim'i yazildi mi
CREATE TABLE IF NOT EXISTS ws_entry (
	id INT UNSIGNED NOT NULL AUTO_INCREMENT,
	tournament_id INT UNSIGNED NOT NULL,
	account_id INT UNSIGNED NOT NULL,
	pid INT UNSIGNED NOT NULL,
	name VARCHAR(24) NOT NULL DEFAULT '',
	level TINYINT UNSIGNED NOT NULL DEFAULT 0,
	job TINYINT UNSIGNED NOT NULL DEFAULT 0,
	fee_gold BIGINT NOT NULL DEFAULT 0,
	status TINYINT UNSIGNED NOT NULL DEFAULT 0,
	refunded TINYINT UNSIGNED NOT NULL DEFAULT 0,
	created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
	PRIMARY KEY (id),
	UNIQUE KEY uniq_tourn_account (tournament_id, account_id),
	KEY tourn_idx (tournament_id)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- Mac gecmisi
-- result: 0=bekliyor 1=A 2=B 3=cift eleme
-- reason: 1=skor 2=hukmen 3=timeout-hp 4=timeout-hasar 5=dq 6=iptal 7=sonucsuz 8=pasif
CREATE TABLE IF NOT EXISTS ws_match (
	id INT UNSIGNED NOT NULL AUTO_INCREMENT,
	tournament_id INT UNSIGNED NOT NULL,
	round SMALLINT UNSIGNED NOT NULL DEFAULT 1,
	pid_a INT UNSIGNED NOT NULL DEFAULT 0,
	pid_b INT UNSIGNED NOT NULL DEFAULT 0,
	name_a VARCHAR(24) NOT NULL DEFAULT '',
	name_b VARCHAR(24) NOT NULL DEFAULT '',
	result TINYINT UNSIGNED NOT NULL DEFAULT 0,
	reason TINYINT UNSIGNED NOT NULL DEFAULT 0,
	damage_a BIGINT NOT NULL DEFAULT 0,
	damage_b BIGINT NOT NULL DEFAULT 0,
	created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
	ended_at DATETIME NULL DEFAULT NULL,
	PRIMARY KEY (id),
	KEY tourn_idx (tournament_id)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- Idempotent odul/iade kuyrugu: odeme UPDATE ... WHERE status=0 kapisiyla yapilir,
-- ayni satir iki kez ASLA odenmez (cift odeme yapisal olarak engelli)
-- status: 0=bekliyor 1=odendi/gecersiz 2=emanet (uzak kayit ucusta; 120sn sonra
--         ProcessClaims sweep'i status=0'a cevirir, host kayit islerse status=1 yapar)
CREATE TABLE IF NOT EXISTS ws_claim (
	id INT UNSIGNED NOT NULL AUTO_INCREMENT,
	account_id INT UNSIGNED NOT NULL,
	pid INT UNSIGNED NOT NULL DEFAULT 0,
	gold BIGINT NOT NULL DEFAULT 0,
	reason VARCHAR(32) NOT NULL DEFAULT '',
	status TINYINT UNSIGNED NOT NULL DEFAULT 0,
	created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
	claimed_at DATETIME NULL DEFAULT NULL,
	PRIMARY KEY (id),
	KEY acc_status_idx (account_id, status)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
