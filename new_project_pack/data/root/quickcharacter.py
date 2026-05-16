# --- FAST_LOGIN_CHARACTER_SAVE:PORT:BEGIN quickcharacter_module ---
# Quick character favorites: HKCU registry under SOFTWARE\\Metin2 (same root as SAVE_ACCOUNT).
# Legacy: quickcharacter.json is imported once if registry has no quickfav data.
# Disabled when app.FAST_LOGIN_CHARACTER_SAVE is 0 (Locale_inc.h FAST_LOGIN_CHARACTER_SAVE).
import json
import os

try:
	import app
except ImportError:
	app = None

try:
	import dbg
except ImportError:
	dbg = None

FILE_NAME = "quickcharacter.json"


def _fast_login_save_enabled():
	if not app:
		return False
	try:
		return int(getattr(app, "FAST_LOGIN_CHARACTER_SAVE", 0)) != 0
	except (TypeError, ValueError):
		return False


MAX_FAVORITES = 10

# Same hive/path pattern as constInfo.SAB.regPath
_QCF_REG_PATH = r"SOFTWARE\AyazMt2_Srv1"
_QCF_REG_PREFIX = "quickfav%02d_%s"
_QCF_FIELDS = ("account", "slot", "name", "pwd")

_read_cache = None


def _trace(msg):
	if not dbg:
		return
	try:
		dbg.TraceError(msg)
	except:
		pass


def _reg_sz(v):
	if v is None:
		return ""
	try:
		if isinstance(v, unicode):
			return v.encode("utf-8", "replace")
		return str(v)
	except Exception:
		return ""


def _reg_key(idx, field):
	return _QCF_REG_PREFIX % (idx, field)


def _use_registry():
	if os.name != "nt":
		return False
	try:
		import constInfo
		return hasattr(constInfo, "GetWinRegKeyValue") and hasattr(constInfo, "SetWinRegKeyValue")
	except ImportError:
		return False


def _reg_get(idx, field):
	if not _use_registry():
		return None
	try:
		import constInfo
		return constInfo.GetWinRegKeyValue(_QCF_REG_PATH, _reg_key(idx, field))
	except Exception:
		return None


def _reg_set(idx, field, value):
	if not _use_registry():
		return False
	try:
		import constInfo
		return constInfo.SetWinRegKeyValue(_QCF_REG_PATH, _reg_key(idx, field), _reg_sz(value))
	except Exception:
		return False


def _reg_del(idx, field):
	if not _use_registry():
		return False
	try:
		import constInfo
		return constInfo.DelWinRegKeyValue(_QCF_REG_PATH, _reg_key(idx, field))
	except Exception:
		return False


def _reg_del_slot(idx):
	for f in _QCF_FIELDS:
		_reg_del(idx, f)


def _read_slot_from_registry(idx):
	slot = _reg_get(idx, "slot")
	if slot is None or not str(slot).strip():
		return None
	try:
		slot_int = int(slot)
	except (ValueError, TypeError):
		return None
	acc = _reg_get(idx, "account")
	name = _reg_get(idx, "name")
	pwd = _reg_get(idx, "pwd")
	return {
		"account": acc if acc else "",
		"slot": slot_int,
		"name": name if name else "",
		"pwd": pwd if pwd else "",
	}


def _read_all_from_registry():
	data = {}
	for idx in xrange(MAX_FAVORITES):
		e = _read_slot_from_registry(idx)
		if e:
			data[str(idx)] = e
	return data


def _read_json_file_dict():
	import os
	for cand in _candidate_read_paths():
		try:
			if not os.path.isfile(cand):
				continue
			f = open(cand, "r")
			try:
				raw = json.load(f)
			finally:
				f.close()
			if isinstance(raw, dict):
				return raw
		except Exception:
			continue
	return {}


def get_storage_path():
	return "registry:HKCU\\%s\\%s*" % (_QCF_REG_PATH.replace("\\", "\\\\"), _QCF_REG_PREFIX.replace("%02d", "00").split("_")[0])


def _candidate_read_paths():
	seen = set()
	out = []
	try:
		import sys
		if getattr(sys, "frozen", False):
			root = os.path.dirname(sys.executable)
		else:
			argv0 = sys.argv[0]
			if argv0:
				root = os.path.dirname(os.path.abspath(argv0))
			else:
				root = ""
			if not root or root in (".", os.path.curdir):
				root = os.getcwd()
		p1 = os.path.join(os.path.normpath(root), FILE_NAME)
	except Exception:
		p1 = FILE_NAME
	for p in (p1, os.path.join(os.getcwd(), FILE_NAME), FILE_NAME):
		if not p:
			continue
		try:
			ap = os.path.abspath(p)
		except Exception:
			ap = p
		if ap in seen:
			continue
		seen.add(ap)
		out.append(p)
	return out


def _migrate_json_to_registry_if_empty():
	if not _use_registry():
		return
	if _read_all_from_registry():
		return
	legacy = _read_json_file_dict()
	if not legacy:
		return
	_write_registry_from_dict(legacy)
	_trace("QCF migrate json->registry keys=%r" % (sorted(legacy.keys()),))


def _write_registry_from_dict(data):
	if not _use_registry():
		return
	for idx in xrange(MAX_FAVORITES):
		key = str(idx)
		rec = data.get(key)
		if isinstance(rec, dict) and "slot" in rec:
			try:
				slot_int = int(rec["slot"])
			except (ValueError, TypeError):
				_reg_del_slot(idx)
				continue
			_reg_set(idx, "account", rec.get("account", ""))
			_reg_set(idx, "slot", slot_int)
			_reg_set(idx, "name", rec.get("name", ""))
			pw = rec.get("pwd")
			if isinstance(pw, basestring) and pw.strip():
				_reg_set(idx, "pwd", pw)
			else:
				_reg_del(idx, "pwd")
		else:
			_reg_del_slot(idx)


def _read_all_impl():
	if _use_registry():
		_migrate_json_to_registry_if_empty()
		data = _read_all_from_registry()
		_trace("QCF read registry path=%r keys=%r" % (_QCF_REG_PATH, sorted(data.keys())))
		return data
	return _read_json_file_dict()


def _invalidate_cache():
	global _read_cache
	_read_cache = None


def _read_all():
	global _read_cache
	if _read_cache is not None:
		return _read_cache
	_read_cache = _read_all_impl()
	return _read_cache


def LoadAllEntries():
	if not _fast_login_save_enabled():
		return {}
	return _read_all()


def invalidate_read_cache():
	if not _fast_login_save_enabled():
		return
	_invalidate_cache()


def _write_all(data):
	if _use_registry():
		_write_registry_from_dict(data)
		_invalidate_cache()
		return
	path = None
	try:
		import sys
		if getattr(sys, "frozen", False):
			root = os.path.dirname(sys.executable)
		else:
			argv0 = sys.argv[0]
			root = os.path.dirname(os.path.abspath(argv0)) if argv0 else os.getcwd()
			if not root or root in (".", os.path.curdir):
				root = os.getcwd()
		path = os.path.join(os.path.normpath(root), FILE_NAME)
		f = open(path, "w")
		try:
			json.dump(data, f, indent=2, ensure_ascii=True)
		finally:
			f.close()
		_invalidate_cache()
	except Exception as e:
		_trace("QCF write fail path=%r err=%r" % (path, e))


def SaveFavorite(idx, account, slot, name, pwd=None):
	if not _fast_login_save_enabled():
		return
	if idx < 0 or idx >= MAX_FAVORITES:
		return
	data = {}
	if _use_registry():
		for j in xrange(MAX_FAVORITES):
			e = _read_slot_from_registry(j)
			if e:
				data[str(j)] = dict(e)
	else:
		blob = _read_json_file_dict()
		for j in xrange(MAX_FAVORITES):
			e = blob.get(str(j))
			if isinstance(e, dict) and "slot" in e:
				data[str(j)] = dict(e)
	old = data.get(str(idx))
	if not isinstance(old, dict):
		old = {}
	rec = {
		"account": account,
		"slot": int(slot),
		"name": name,
	}
	if pwd is not None:
		if isinstance(pwd, basestring) and pwd.strip():
			rec["pwd"] = pwd
		elif old.get("pwd"):
			rec["pwd"] = old["pwd"]
	elif old.get("pwd"):
		rec["pwd"] = old["pwd"]
	data[str(idx)] = rec
	_write_all(data)
	_trace("QCF save idx=%d store=%r slot=%r name=%r" % (idx, "registry" if _use_registry() else "json", rec.get("slot"), rec.get("name")))


def LoadFavorite(idx, data=None):
	if not _fast_login_save_enabled():
		return None
	if idx < 0 or idx >= MAX_FAVORITES:
		return None
	if data is None:
		data = _read_all()
	entry = data.get(str(idx))
	if not isinstance(entry, dict):
		return None
	if "slot" not in entry:
		return None
	out = {}
	for k, v in entry.iteritems():
		out[k] = v
	if "account" not in out:
		out["account"] = ""
	raw_name = out.get("name")
	if raw_name is None:
		raw_name = out.get("Name")
	if isinstance(raw_name, basestring):
		out["name"] = raw_name.strip()
	elif raw_name is not None:
		try:
			out["name"] = str(raw_name).strip()
		except Exception:
			out["name"] = ""
	else:
		out["name"] = ""
	try:
		out["slot"] = int(out["slot"])
	except (ValueError, TypeError):
		return None
	return out


def AccountsMatch(saved_account, typed_id):
	if not _fast_login_save_enabled():
		return False
	if saved_account is None or typed_id is None:
		return False

	def norm(x):
		if isinstance(x, unicode):
			return x.strip()
		try:
			return unicode(x, "utf-8").strip()
		except UnicodeDecodeError:
			try:
				return unicode(x, "cp1252").strip()
			except UnicodeDecodeError:
				return unicode(x, errors="replace").strip()

	return norm(saved_account) == norm(typed_id)


def _to_login_str(x):
	if x is None:
		return ""
	try:
		return str(x)
	except UnicodeEncodeError:
		if isinstance(x, unicode):
			return x.encode("utf-8", "replace")
		return ""


def ResolveCredentials(account_key, pwd_from_json=None):
	if not _fast_login_save_enabled():
		return (_to_login_str(account_key).strip(), "")
	acc = _to_login_str(account_key).strip()
	pw = ""
	if isinstance(pwd_from_json, basestring) and pwd_from_json.strip():
		pw = _to_login_str(pwd_from_json).strip()
	if pw:
		return (acc, pw)
	try:
		import constInfo
	except ImportError:
		return (acc, "")
	if not getattr(constInfo, "ENABLE_SAVE_ACCOUNT", False):
		return (acc, "")
	if not hasattr(constInfo, "SAB"):
		return (acc, "")
	sab = constInfo.SAB
	for idx in xrange(sab.slotCount):
		row = sab.accData.get(idx)
		if not row:
			continue
		sid, spwd = row[0], row[1]
		if not sid or not spwd:
			continue
		if AccountsMatch(sid, acc):
			return (_to_login_str(sid).strip(), _to_login_str(spwd).strip())
	if sab.storeType == sab.ST_FILE:
		for idx in xrange(sab.slotCount):
			id_f, pwd_f = constInfo.GetJsonSABData(idx)
			if not id_f or not pwd_f:
				continue
			if AccountsMatch(id_f, acc):
				return (str(id_f).strip(), str(pwd_f).strip())
	return (acc, "")


def HasStoredLoginForEntry(entry):
	if not _fast_login_save_enabled():
		return False
	if not entry or not entry.get("name"):
		return False
	acc, pwd = ResolveCredentials(entry.get("account"), entry.get("pwd"))
	return bool(pwd)


def ClearFavorite(idx):
	if not _fast_login_save_enabled():
		return
	if idx < 0 or idx >= MAX_FAVORITES:
		return
	if _use_registry():
		_reg_del_slot(idx)
		_invalidate_cache()
		return
	data = _read_json_file_dict()
	key = str(idx)
	if key not in data:
		return
	del data[key]
	path = None
	try:
		import sys
		if getattr(sys, "frozen", False):
			root = os.path.dirname(sys.executable)
		else:
			argv0 = sys.argv[0]
			root = os.path.dirname(os.path.abspath(argv0)) if argv0 else os.getcwd()
			if not root or root in (".", os.path.curdir):
				root = os.getcwd()
		path = os.path.join(os.path.normpath(root), FILE_NAME)
		f = open(path, "w")
		try:
			json.dump(data, f, indent=2, ensure_ascii=True)
		finally:
			f.close()
		_invalidate_cache()
	except Exception as e:
		_trace("QCF clear fail path=%r err=%r" % (path, e))
# --- FAST_LOGIN_CHARACTER_SAVE:PORT:END quickcharacter_module ---
