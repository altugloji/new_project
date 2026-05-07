#### @martysama0134 backup scripts ####
### Inside /etc/crontab paste:
## for automatic backups every hour:
# 0 * * * * root cd /home/m2_svfiles/baks/ && /usr/local/bin/python3 backup_db.py dump
## for automatic clean of backups older than 7 days every week:
# 0 0 * * 1 root cd /home/m2_svfiles/baks/ && /usr/local/bin/python3 backup_db.py wclean

import os
import re
import shutil
import subprocess
import sys
import logging
from datetime import datetime, timedelta
import platform

from subprocess import check_output as sp_co, call as sp_call, CalledProcessError as sp_CalledProcessError
def fShell(szCmd, bRet=False):
	try:
		if bRet:
			return sp_co(szCmd, shell=True)[:-1]	# remove final \n
		else:
			return sp_call(szCmd, shell=True)
	except sp_CalledProcessError:
		return -1

def SlashFix(pathname):
	if platform.system() in ("FreeBSD", "Linux"):
		return pathname.replace("\\", "/")
	elif platform.system()=="Windows":
		return pathname.replace("/", "\\")
	return pathname

def SymLinkCreate(src, dst, is_file):
	src = SlashFix(src)
	dst = SlashFix(dst)
	if platform.system() == "FreeBSD":
		fShell(f"ln -Ffnsw {src} {dst}")
	elif platform.system() == "Linux":
		fShell(f"ln -Ffns {src} {dst}")
	elif platform.system() == "Windows":
		if is_file:
			fShell(f"mklink {dst} {src}")
		else:
			fShell(f"mklink /D {dst} {src}")

def IsWindows(): return platform.system()=="Windows"
def cecho(text): print(text) if IsWindows() else print("\033[36m" + text + "\033[0m")

DATE = datetime.now().strftime("%Y%m%d-%H%M%S")

OUTPATH = "db"
MY_LOGF = os.path.join(OUTPATH, "log.txt")

MYSQLDUMP = "/usr/local/bin/mysqldump"
if IsWindows():
    MYSQLDUMP = "mysqldump"

MY_HOST = "localhost"
MY_USER = "root"
MY_PASS = "password"
PREFIX = "srv1_"
DATABASES = [
	"mysql",
	PREFIX+"account",
	PREFIX+"common",
	PREFIX+"player",
	PREFIX+"log",
]

# Determine MySQL version
def process_flags(FLAGS):
    mysql_version_full = subprocess.check_output(["mysql", "--version"]).decode("utf-8")
    if "MariaDB" in mysql_version_full:
        return

    mysql_version = mysql_version_full.split()[2]
    if mysql_version.startswith("8."):
        FLAGS.append("--set-gtid-purged=OFF")
    elif mysql_version.startswith("5.7"):
        FLAGS.append("--set-gtid-purged=OFF")
    elif mysql_version.startswith("5.6"):
        FLAGS.append("--set-gtid-purged=OFF")
    else:
        logging.error(f"Unknown MySQL version: {mysql_version}")

def delete_old_backups():
    for entry in os.listdir(OUTPATH):
        # Check if entry is a directory and matches the format "YYYYmmdd-HHMMSS"
        if os.path.isdir(os.path.join(OUTPATH, entry)) and re.match(r'\d{8}-\d{6}', entry):
            shutil.rmtree(os.path.join(OUTPATH, entry))
            logging.info(f"Deleted old backup: {entry}")

def delete_1week_old_backups():
    for entry in os.listdir(OUTPATH):
        # Check if entry is a directory and matches the format "YYYYmmdd-HHMMSS"
        if os.path.isdir(os.path.join(OUTPATH, entry)) and re.match(r'\d{8}-\d{6}', entry):
            try:
                # Convert the directory name to datetime format
                backup_date = datetime.strptime(entry, "%Y%m%d-%H%M%S")
                # Delete the directory if it's older than a certain threshold
                if datetime.now() - backup_date > timedelta(days=7):
                    shutil.rmtree(os.path.join(OUTPATH, entry))
                    logging.info(f"Deleted old backup: {entry}")
            except ValueError:
                # Skip directories that do not match the expected format
                continue

def init_logging():
    logging.basicConfig(filename=MY_LOGF, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)
    logging.getLogger('').addHandler(console_handler)

def dump():
    """Save backups"""
    os.makedirs(os.path.join(OUTPATH, DATE), exist_ok=True)
    for db in DATABASES:
        logging.info(f"Dumping {DATE}/{db}.sql.gz...")
        FLAGS = []
        process_flags(FLAGS)
        if db==PREFIX+"log":
            FLAGS.append("--no-data")
        command = f"{MYSQLDUMP} {' '.join(FLAGS)} -u {MY_USER} -p{MY_PASS} -h {MY_HOST} {db} | gzip -9 > {OUTPATH}/{DATE}/{db}.sql.gz"
        subprocess.run(command, shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        # create symlink
        SymLinkCreate(f"{DATE}/{db}.sql.gz", f"{OUTPATH}/{db}.sql.gz", is_file=True)

def recovery():
    """Recovery backups"""
    for db in DATABASES:
        logging.info(f"Recovering {db}.sql.gz...")
        command = f"gunzip < {OUTPATH}/{db}.sql.gz | mysql -u {MY_USER} -p{MY_PASS} -h {MY_HOST} {db}"
        subprocess.run(command, shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)

def clean():
    """Delete all the backups"""
    delete_old_backups()

def lclean():
    """Delete the log file"""
    if os.path.exists(MY_LOGF):
        os.remove(MY_LOGF)

def wclean():
    """Delete the backups older than 1 week"""
    delete_1week_old_backups()

def cleanall():
    """Delete all the backups and logs"""
    clean()
    lclean()

actions = {
    "dump": dump,
    "recovery": recovery,
    "clean": clean,
    "lclean": lclean,
    "wclean": wclean,
    "cleanall": cleanall
}

# Execute the appropriate function based on user input
if __name__ == "__main__":
    if not os.path.exists(OUTPATH):
        os.makedirs(OUTPATH)

    init_logging()

    if len(sys.argv) < 2:
        print("Available actions:")
        for action in actions.keys():
            print("    {}".format(action))

        ret = input('Enter an action: ').split()
        if not ret:
            cecho('No argument provided. Quitting.')
            sys.exit()

        action = ret[0]
        commands = ret[1:] if len(ret) >= 2 else []
    else:
        action = sys.argv[1]
        commands = sys.argv[2:] if len(sys.argv) >= 3 else []
        # print(" ".join(sys.argv[1:]))

    commands = " ".join(commands)

    selected_action = actions.get(action)
    if selected_action:
        logging.info(f"Started action {action}")
        selected_action()
        logging.info(f"Stopped action {action}")
    else:
        print("Invalid action. Please choose one of: {}".format(", ".join(actions.keys())))
