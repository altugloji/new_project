#!/usr/local/bin/python3
#### @martysama0134 start scripts ####
import os
import sys
import subprocess
from gen import IsWindows,SymLinkCreate

def fecho(text): print(text) if IsWindows() else print("\033[35m" + text + "\033[0m")
def _fecho(text): print(text) if IsWindows() else print("\033[4;35m" + text + "\033[0m")
def f_echo(text): print(text) if IsWindows() else print("\033[1;35m" + text + "\033[0m")
def becho(text): print(text) if IsWindows() else print("\033[34m" + text + "\033[0m")
def yecho(text): print(text) if IsWindows() else print("\033[33m" + text + "\033[0m")
def _yecho(text): print(text) if IsWindows() else print("\033[4;33m" + text + "\033[0m")
def y_echo(text): print(text) if IsWindows() else print("\033[1;33m" + text + "\033[0m")
def gecho(text): print(text) if IsWindows() else print("\033[32m" + text + "\033[0m")
def recho(text): print(text) if IsWindows() else print("\033[31m" + text + "\033[0m")
def _recho(text): print(text) if IsWindows() else print("\033[4;31m" + text + "\033[0m")
def r_echo(text): print(text) if IsWindows() else print("\033[1;31m" + text + "\033[0m")
def cecho(text): print(text) if IsWindows() else print("\033[36m" + text + "\033[0m")
def ruecho(text): print(text) if IsWindows() else print("\033[1;4;33;41m" + text + "\033[0m")
def bnecho(text): print(text) if IsWindows() else print("\033[1;4;30;47m" + text + "\033[0m")
def rnecho(text): print(text) if IsWindows() else print("\033[1;4;30;41m" + text + "\033[0m")
def abio(text): print(text) if IsWindows() else print("\033[31m" + text + "\033[32m" + text + "\033[33m" + text + "\033[34m" + text + "\033[35m" + text + "\033[36m" + text + "\033[37m" + text + "\033[0m")

def run_command(cmd):
    subprocess.run(cmd.split())

def search_for_port_in_configs(path):
    for root, dirs, files in os.walk(path):
        for file in files:
            if file == "CONFIG":
                config_file_path = os.path.join(root, file)
                with open(config_file_path, 'r') as f:
                    for line in f:
                        if "PORT" in line:
                            print(line.strip())

def delete_file(filepath):
    if os.path.exists(filepath):
        if os.path.islink(filepath):
            os.unlink(filepath)
        else:
            os.remove(filepath)

def delete_symlink(filepath):
    try:
        os.unlink(filepath)
    except FileNotFoundError:
        pass

if __name__ == "__main__":
    v_base = os.getcwd()
    v_mt2f = v_base
    v_bakf = os.path.join(v_base, '..', 'baks')
    v_foldername = 'srv1'
    v_localename = 'germany'
    v_bin = 'python3'
    if IsWindows():
        v_bin = 'python'

    r_echo(".:. AdminPanel .:.")
    gecho("What do you want to do?")
    recho("1. Start (start)")
    recho("1i. Start Interactive (starti)")
    recho("111. Restart (restart)")
    recho("111a. Restart+Daemon (restartall)")
    recho("111b. Restart+Gen+Quest (fullrestart)")
    recho("2. Stop (stop|close)")
    recho("2i. Stop Interactive (stopi|closei)")
    recho("3. Clean (clean|clear)")
    recho("33. Clean All (cleanall|clearall)")
    recho("4. Backup mysql/db (bak1|db|db_backup)")
    recho("4b. Backup mysql no user-data (dbrev)")
    recho("5. Backup game/fs (bak2|fs|fs_backup)")
    recho("666. Generate (gen)")
    recho("777. Compile Quests (quest)")
    recho("888. Game Symlink (symlink)")
    recho("999. Search (search)")
    _yecho("1a. Start+Daemon (startall)")
    _yecho("2a. Stop+Daemon (stopall|closeall)")
    _recho("0. Quit (quit)")


    if len(sys.argv) < 2:
        ret = input('Enter a phase: ').split()
        if not ret:
            cecho('No argument provided. Quitting.')
            sys.exit()
        phase = ret[0]
        commands = ret[1:] if len(ret) >= 2 else []
    else:
        phase = sys.argv[1]
        commands = sys.argv[2:] if len(sys.argv) >= 3 else []
        # print(" ".join(sys.argv[1:]))

    commands = " ".join(commands)

    if phase in ['111', 'restart']:
        os.chdir(v_mt2f)
        run_command(f'{v_bin} stop.py')
        run_command(f'{v_bin} start.py')
        os.chdir(v_base)
        cecho('restart completed')

    elif phase in ['111a', 'restartall']:
        p = subprocess.run(['ps', 'afx'], stdout=subprocess.PIPE)
        ps_output = p.stdout.decode()
        for line in ps_output.split('\n'):
            if f'{v_bin} daemon_srv1.py' in line and 'grep' not in line:
                pid = line.split()[0]
                os.kill(pid, 9)
        os.chdir(v_mt2f)
        run_command(f'{v_bin} stop.py')
        run_command(f'{v_bin} start.py')
        os.system(f'{v_bin} daemon_srv1.py &')

        os.chdir(v_base)
        cecho('restartall completed')

    elif phase in ['111b', 'fullrestart']:
        os.chdir(v_mt2f)
        run_command(f'{v_bin} admin_panel.py clear')
        run_command(f'{v_bin} admin_panel.py gen')
        run_command(f'{v_bin} admin_panel.py quest')
        run_command(f'{v_bin} admin_panel.py restart')
        os.chdir(v_base)
        cecho('restart completed')

    elif phase in ['1', 'start']:
        os.chdir(v_mt2f)
        run_command(f'{v_bin} start.py {commands}')
        os.chdir(v_base)
        cecho('start completed')

    elif phase in ['1i', 'starti']:
        os.chdir(v_mt2f)
        run_command(f'{v_bin} start.py --prompt')
        os.chdir(v_base)
        cecho('starti completed')

    elif phase in ['1a', 'startall']:
        os.chdir(v_mt2f)
        os.system(f'{v_bin} daemon_srv1.py &')
        os.chdir(v_base)
        cecho('startall completed')

    elif phase in ['2', 'stop', 'close']:
        os.chdir(v_mt2f)
        run_command(f'{v_bin} stop.py {commands}')
        os.chdir(v_base)
        cecho('stop completed')

    elif phase in ['2i', 'stopi', 'closei']:
        os.chdir(v_mt2f)
        run_command(f'{v_bin} stop.py --prompt')
        os.chdir(v_base)
        cecho('stopi completed')

    elif phase in ['2a', 'stopall', 'closeall']:
        p = subprocess.run(['ps', 'afx'], stdout=subprocess.PIPE)
        ps_output = p.stdout.decode()
        for line in ps_output.split('\n'):
            if 'daemon_srv1.py' in line and 'grep' not in line:
                pid = int(line.split()[0])
                print(f"Killing process {pid}")
                os.kill(pid, 9)
        os.chdir(v_mt2f)
        run_command(f'{v_bin} stop.py')
        os.chdir(v_base)
        cecho('stopall completed')

    elif phase in ['3', 'clean', 'clear']:
        os.chdir(v_mt2f)
        run_command(f'{v_bin} clear.py')
        os.chdir(v_base)
        cecho('clean completed')

    elif phase in ['33', 'cleanall', 'clearall']:
        os.chdir(v_mt2f)
        response = input("Are you sure you want to delete the backups as well? [Ny] ")
        if response.lower() == 'y':
            run_command(f'{v_bin} clear.py')
            os.chdir(v_bakf)
            run_command(f'{v_bin} backup_db.py clean')
            run_command(f'{v_bin} backup_fs.py clean')
            os.chdir(v_base)
            cecho('cleanall completed')
        else:
            cecho('cleanall cancelled')

    elif phase in ['4', 'bak1', 'db', 'db_backup']:
        os.chdir(v_bakf)
        run_command(f'{v_bin} backup_db.py dump')
        os.chdir(v_base)
        cecho('bak db completed')

    elif phase in ['4b','dbrev', 'dbrev_backup']:
        os.chdir(v_bakf)
        run_command(f'{v_bin} backup_dbrev.py dump')
        os.chdir(v_base)
        cecho('bak dbrev completed')

    elif phase in ['5', 'bak2', 'fs', 'fs_backup']:
        os.chdir(v_bakf)
        run_command(f'{v_bin} backup_fs.py dump')
        os.chdir(v_base)
        cecho('bak fs completed')

    elif phase in ['666', 'gen']:
        os.chdir(v_mt2f)
        run_command(f'{v_bin} gen.py')
        os.chdir(v_base)
        cecho('gen completed')

    elif phase in ['777', 'quest']:
        os.chdir(os.path.join(v_mt2f, v_foldername, 'share', 'locale', v_localename, 'quest'))
        if not IsWindows():
            run_command('chmod u+x qc')
        run_command(f'{v_bin} pre_qc.py -ac')
        os.chdir(v_base)
        cecho('quest completed')

    elif phase in ['888', 'symlink']:
        os.chdir(os.path.join(v_mt2f, v_foldername, 'share', 'bin'))
        if IsWindows():
            delete_symlink('game.exe')
            delete_symlink('db.exe')
            os.system(r'mklink game.exe "..\..\..\..\..\server\Srcs\Server\game\bin\release\game.exe"')
            os.system(r'mklink db.exe "..\..\..\..\..\server\Srcs\Server\db\bin\release\db.exe"')
        else:
            delete_symlink('game')
            delete_symlink('db')
            run_command('ln -s /home/asf-v5-ex/server/Srcs/Server/game/game_symlink game')
            run_command('ln -s /home/asf-v5-ex/server/Srcs/Server/db/db_symlink db')
        cecho('symlink completed')

    elif phase in ['999', 'search']:
        search_for_port_in_configs(v_base)

    elif phase in ['0', 'quit']:
        abio('.:|:.')
        sys.exit()

    else:
        cecho(f'{phase} not found')
