#### @martysama0134 backup scripts ####
### Inside /etc/crontab paste:
## for automatic backups every hour:
# 0 * * * * root cd /home/m2_svfiles/baks/ && /usr/local/bin/python3 backup_dbrev.py dump

import os
import re
import shutil
import subprocess
import sys
import logging
from datetime import datetime, timedelta
import platform

def IsWindows(): return platform.system()=="Windows"
def cecho(text): print(text) if IsWindows() else print("\033[36m" + text + "\033[0m")

OUTPATH = "dbrev"
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
TABLES = {
    PREFIX+"account" : "block_exception GameTime GameTimeIP iptocountry string",
    PREFIX+"common"  : "",
    PREFIX+"player"  : "banword item_attr item_attr_rare item_proto land mob_proto object_proto refine_proto shop shop_item skill_proto string",
}

def remove_auto_increment(input_file: str, output_file: str = None):
    """
    Removes AUTO_INCREMENT values from MySQL dump file.

    :param input_file: Path to the input SQL dump file.
    :param output_file: Path to the output file (if None, it overwrites input file).
    """
    output_file = output_file or input_file  # Overwrite if no output file specified

    with open(input_file, 'rb') as file:
        sql_content = file.read()

    # Remove AUTO_INCREMENT=xxx
    cleaned_sql = re.sub(rb'AUTO_INCREMENT=\d+\b', b'', sql_content)

    with open(output_file, 'wb') as file:
        file.write(cleaned_sql)

    # print(f"Processed: {input_file} ? {output_file}")

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
        # Check if entry is a file and matches the format "*.sql"
        if os.path.isfile(os.path.join(OUTPATH, entry)) and re.match(r'.*\.sql$', entry):
            os.remove(os.path.join(OUTPATH, entry))
            logging.info(f"Deleted old backup: {entry}")

def init_logging():
    logging.basicConfig(filename=MY_LOGF, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)
    logging.getLogger('').addHandler(console_handler)

def dump():
    """Save backups"""
    os.makedirs(OUTPATH, exist_ok=True)

    for db in DATABASES:
        outfile = f"{OUTPATH}/{db}-schema.sql"
        logging.info(f"Dumping {outfile}...")
        FLAGS = ["--no-data","--skip-extended-insert","--skip-dump-date"]
        process_flags(FLAGS)
        command = f"{MYSQLDUMP} {' '.join(FLAGS)}  -u {MY_USER} -p{MY_PASS} -h {MY_HOST} {db} > {outfile}"
        subprocess.run(command, shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        if os.path.exists(f"{outfile}") and os.stat(f"{outfile}").st_size > 0:
            remove_auto_increment(f"{outfile}")

    for db, tables in TABLES.items():
        outfile = f"{OUTPATH}/{db}-data.sql"
        logging.info(f"Dumping {outfile}...")
        FLAGS = ["--no-create-info","--skip-extended-insert","--skip-dump-date"]
        process_flags(FLAGS)
        command = f"{MYSQLDUMP} {' '.join(FLAGS)} -u {MY_USER} -p{MY_PASS} -h {MY_HOST} {db} {tables} > {outfile}"
        subprocess.run(command, shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        if os.path.exists(f"{outfile}") and os.stat(f"{outfile}").st_size > 0:
            remove_auto_increment(f"{outfile}")

def recovery():
    """Recovery backups"""
    for db in DATABASES:
        logging.info(f"Recovering {db}-schema.sql...")
        command = f"mysql -u {MY_USER} -p{MY_PASS} -h {MY_HOST} {db} 2>> {MY_LOGF} < {OUTPATH}/{db}-schema.sql"
        subprocess.run(command, shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)

    for db, tables in TABLES.items():
        logging.info(f"Recovering {db}-data.sql...")
        command = f"mysql -u {MY_USER} -p{MY_PASS} -h {MY_HOST} {db} 2>> {MY_LOGF} < {OUTPATH}/{db}-data.sql"
        subprocess.run(command, shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)

def clean():
    """Delete all the backups"""
    delete_old_backups()

def lclean():
    """Delete the log file"""
    if os.path.exists(MY_LOGF):
        os.remove(MY_LOGF)

def cleanall():
    """Delete all the backups and logs"""
    clean()
    lclean()

actions = {
    "dump": dump,
    "recovery": recovery,
    "clean": clean,
    "lclean": lclean,
    "cleanall": cleanall,
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
