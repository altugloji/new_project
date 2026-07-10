#ifndef BAN_IP_H_
#define BAN_IP_H_

#ifdef ENABLE_IP_BAN

// IP ban sistemi: her baglantida player.ban_ip tablosuna DOGRUDAN bakilir (cache/event yok).
// Tablo SADECE SQL ile duzenlenir (GM komutu yok). IP kayitliysa oyuncu, DESC olusmadan
// baglanti asamasinda (DESC_MANAGER::AcceptDesc) reddedilir; degisiklikler aninda gecerlidir.
bool IsIPBanned(const char * c_pszIP);

#endif // ENABLE_IP_BAN

#endif /* BAN_IP_H_ */
