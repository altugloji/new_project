#! /usr/local/bin/python3

"""pre_qc - Metin2 quest preprocessor.

Expands `define` macros in .quest source files before the quest compiler
(qc.py / qc.exe / qc) consumes them. Reads either a quest_list file (one
path per line, '#' starts a comment) or a single .quest via -f. Writes
the substituted files under ./.pre_qc/.

Supported define forms
----------------------
1. Simple:
       define NAME value
   Every whole-token occurrence of NAME outside strings and compound
   identifiers is replaced with `value`.

2. Group (v2.1):
       define group NAME a b c d
   Expands NAME into a Lua table literal: {a,b,c,d}. Square brackets and
   commas in the declaration are optional sugar - the tokenizer treats
   them as separators, so "define group NAME [a, b, c, d]" is accepted.

Substitution rules
------------------
- Whole-token only: `prefix__NAME__suffix` is left alone (underscores
  are not token separators).
- String literals "..." are preserved verbatim; tokens inside strings
  are not substituted.
- Defines must appear before the first `quest` keyword in the file.

Known issues (deferred to v2.2, not fixed in v2.1)
--------------------------------------------------
- Line and block comments are not skipped during substitution. Tokens
  inside `-- ...` or `--[[ ... ]]` are still replaced.
- `define NAME "a b c d"` is misparsed - the space inside quotes breaks
  tokenization and only `"a` survives. Workaround: avoid spaces in
  string-valued defines.

Written by martysama0134.
Licensed under the MIT License - see LICENSE for details.
"""

import os
import shutil
import sys
import time

# ═══════════════════════════════════════════════════════════════════════════
# Section 0: Configuration
# ═══════════════════════════════════════════════════════════════════════════
#
# Default paths and flags for the CLI, plus the benchmarking trampoline used
# when --verbose is set. The TOKEN_LIST tuple is what my_split_with_seps and
# my_split treat as separators during tokenization - adding to it changes
# what counts as a token boundary in every substitution pass below.

__version__ = "2.1.0"

QUESTLIST_PATH_DFT="./quest_list"
WORKINGPATH_DFT="./.pre_qc"
COPYALL_DFT=False
VERBOSITY_DFT=False
BACKUP_DFT=False
SINGLEFILE_DFT=""
TOKEN_LIST = ("\t", ",", " ", "=", "[", "]", "{", "}","-","<",">","~","!",".","(",")","+","*","/","\n","\r")

def IsWindows():
    return os.name == "nt"

def BenchMe(fnc, *args, **kw):
    print("--- BenchMe calling for {} with args {}, {} Begin ---".format(fnc.__name__, args, kw))
    t_start = time.time()
    rtn = fnc(*args, **kw)
    print(time.time()-t_start)
    print("--- BenchMe for {} End ---".format(fnc.__name__))
    return rtn
def NoBenchMe(fnc, *args, **kw):
    return fnc(*args, **kw)

# ═══════════════════════════════════════════════════════════════════════════
# Section 1: PreQC class (CLI-facing API)
# ═══════════════════════════════════════════════════════════════════════════
#
# One object per invocation. Holds the config flags from the CLI, loads the
# quest_list (or a single file), drives preprocessing via Generate(), and
# optionally invokes the compiler (qc.py preferred, else qc.exe / ./qc) via
# Compile(). Working directory is wiped and recreated on every construction.

class PreQC:
    def __init__(self, questlistpath=QUESTLIST_PATH_DFT, workingpath=WORKINGPATH_DFT, verbosity=VERBOSITY_DFT, backup=BACKUP_DFT, copyall=COPYALL_DFT, singlefile=SINGLEFILE_DFT):
        self.questlistpath = questlistpath
        self.workingpath = workingpath
        self.verbosity = verbosity
        self.backup = backup
        self.copyall = copyall
        self.singlefile = singlefile
        self.benchFunc = BenchMe if verbosity else NoBenchMe
        if os.path.exists(self.workingpath):
            shutil.rmtree(self.workingpath)
        os.makedirs(self.workingpath)
        self.lista = []
        if self.copyall or not self.singlefile:
            self.benchFunc(self.LoadList)
        else:
            self.lista.append(self.singlefile)

    def LoadList(self):
        with open(self.questlistpath, "r", encoding="ascii", errors="surrogateescape") as f:
            for fname in f.readlines():
                fname = fname.rstrip()
                if not fname or fname[0]=="#":
                    continue
                self.lista.append(fname)
            if self.verbosity:
                print("--- PreQC.LoadList Begin ---")
                for ffname in self.lista: print(repr(ffname))
                print("--- PreQC.LoadList End ---")

    def Generate(self):
        for fname in self.lista:
            self.benchFunc(Run, *(fname, self.workingpath, self.copyall))

    def Compile(self):
        if os.path.exists("object"):
            if self.backup:
                os.rename("object", "object__{}".format(time.strftime("%Y%m%d-%H%M%S", time.localtime())))
            shutil.rmtree("./object")
        #iter quest list
        isPyQCAvail = os.path.exists("qc.py")
        for fname in self.lista:
            if not fname:
                continue
            #no popen for convenience
            if "/" in fname:
                #fix bug if .quest paths contain /
                #you should not call two quests with the same name anyway
                fname=fname.split("/")[-1]
            if isPyQCAvail:
                retcode = os.system("python qc.py {}/{}".format(self.workingpath, fname))
            else:
                if IsWindows():
                    retcode = os.system("qc.exe {}/{}".format(self.workingpath, fname))
                else:
                    retcode = os.system("./qc {}/{}".format(self.workingpath, fname))
            if retcode:
                print("Error {} occurred on quest {}/{}".format(retcode, self.workingpath, fname), file=sys.stderr)
                sys.exit(1)
        if not IsWindows():
            os.system("chmod -R ug+rwx object")

# ═══════════════════════════════════════════════════════════════════════════
# Section 2: Tokenizer helpers
# ═══════════════════════════════════════════════════════════════════════════
#
# Pure string-processing utilities used by the preprocessor core. They do
# not touch the filesystem or the PreQC state. split_by_quote separates
# string literals from code; my_split / my_split_with_seps tokenize around
# the TOKEN_LIST separators, with the *_with_seps variant preserving the
# separators so the token stream can be rejoined verbatim.

def split_by_quote(buf):
    """Split a line into alternating non-string and string ('"..."') chunks.

    The returned list preserves the quotes on string chunks - a chunk
    starting with '"' is a verbatim string literal; other chunks are
    regular source to be tokenized and substituted.
    """
    p = False
    l = list(buf)
    l.reverse()
    s = ""
    res = []
    while l:
        c = l.pop()
        if c == '"':
            if p == True:
                s += c
                res += [s]
                s = ""
            else:
                if len(s) != 0:
                    res += [s]
                s = '"'
            p = not p
        elif c == "\\" and l[0] == '"':
            s += c
            s += l.pop()
        else:
            s += c

    if len(s) != 0:
        res += [s]
    return res

def AddSepMiddleOfElement(l, sep):
    """Interleave `sep` between elements of `l`: [a,b,c] -> [a,sep,b,sep,c]."""
    l.reverse()
    new_list = [l.pop()]
    while l:
        new_list.append(sep)
        new_list.append(l.pop())
    return new_list

def my_split_with_seps(s, seps):
    """Tokenize `s` by any of `seps`, preserving the separators as tokens.

    Empty results are filtered. Used during Replace so the token stream can
    be rejoined with writelines() byte-faithfully.
    """
    res = [s]
    for sep in seps:
        new_res = []
        for r in res:
            sp = r.split(sep)
            sp = AddSepMiddleOfElement(sp, sep)
            new_res += sp
        res = new_res
    new_res = []
    for r in res:
        if r != "":
            new_res.append(r)
    return new_res

def my_split(s, seps):
    """Tokenize `s` by any of `seps` without preserving the separators.

    Empty results are filtered. Used during MakeParameterTable where we
    only need the significant tokens, not the exact spacing.
    """
    res = [s]
    for sep in seps:
        new_res = []
        for r in res:
            sp = r.split(sep)
            new_res += sp
        res = new_res
    new_res = []
    for r in res:
        if r != "":
            new_res.append(r)
    return new_res
# ═══════════════════════════════════════════════════════════════════════════
# Section 3: Preprocessor core
# ═══════════════════════════════════════════════════════════════════════════
#
# MakeParameterTable scans top-of-file `define` declarations and stops at
# the first `quest` keyword. Replace walks the remaining lines and expands
# every known key into its value (or `{v0,v1,...}` table literal for group
# defines). Run ties them together for a single quest file.

def Replace(lines, parameter_table, keys):
    """Expand every `key` in `lines` using `parameter_table`.

    Preserves string literals verbatim. For a key whose table entry has
    multiple values, emits a Lua table literal '{v0,v1,...}'. Returns a
    flat list of tokens suitable for file.writelines().
    """
    r = []
    for string in lines:
        l = split_by_quote(string)
        for s in l:
            if s[0] == '"':
                r += [s]
            else:
                tokens = my_split_with_seps(s, TOKEN_LIST)
                for key in keys:
                    if key not in parameter_table:
                        continue
                    indices = [i for i, tok in enumerate(tokens) if tok == key]
                    for i in indices:
                        if len(parameter_table[key]) > 1:
                            tokens[i] = "{" + ",".join(str(x) for x in parameter_table[key]) + "}"
                        else:
                            tokens[i] = parameter_table[key][0]
                r += tokens
    return r

def MakeParameterTable(lines, parameter_table, keys):
    """Scan `lines` top-down, populate `parameter_table` and `keys` with
    every `define` encountered, and return the 1-based line index of the
    first `quest` keyword (the point at which Replace should start).

    Handles both `define NAME value` and `define group NAME v0 v1 ...`
    forms. Mutates `parameter_table` and `keys` in place.
    """
    group_names = []
    group_values = []
    idx = 0
    for line in lines:
        idx += 1
        line = line.rstrip()
        if -1 != line.find("--"):
            line = line[0:line.find("--")]

        tokens = my_split(line, ["\t", ",", " ", "=", "[", "]", "\r", "\n"])
        if len(tokens) == 0:
            continue
        if tokens[0] == "quest":
            start = idx
            break
        if tokens[0] == "define":
            if tokens[1] == "group":
                group_value = []
                for value in tokens[3:]:
                    if parameter_table.get(value, 0) != 0:
                        value = parameter_table[value]
                    group_value.append(value)
                parameter_table[tokens[2]] = group_value
                keys.append(tokens[2])
            elif len(tokens) > 5:
                print("pre_qc: line {}: invalid 'define' syntax".format(idx), file=sys.stderr)
                print("  expected: define NAME value", file=sys.stderr)
                print("       or:  define group NAME v0 v1 v2 ...", file=sys.stderr)
            else:
                value = tokens[2]
                if parameter_table.get(value, 0) != 0:
                    value = parameter_table[value]
                parameter_table[tokens[1]] = [value]
                keys.append(tokens[1])
    return start

def Run(inputFN=SINGLEFILE_DFT, workingpath=WORKINGPATH_DFT, copyall=COPYALL_DFT):
    """Preprocess one .quest file.

    Reads `inputFN`, expands its defines, and writes the result to
    `workingpath/<basename(inputFN)>`. If the file has no defines and
    `copyall` is True, the input is copied verbatim; otherwise an
    input with no defines produces no output. Returns True on success,
    False if inputFN is empty.
    """
    parameter_table = {}
    keys = []
    if not inputFN:
        return False

    with open(inputFN, encoding="ascii", errors="surrogateescape") as fname:
        lines = fname.readlines()
        start = MakeParameterTable(lines, parameter_table, keys)
        outputFN = "{}/{}".format(workingpath, inputFN.split("/")[-1])

        if not len(keys) == 0:
            lines = lines [start-1:]
            r = Replace(lines, parameter_table, keys)
            # dump
            with open(outputFN, "w", encoding="ascii", errors="surrogateescape") as f:
                f.writelines(r)
        elif copyall:
            shutil.copyfile(inputFN, outputFN)
    return True

# ═══════════════════════════════════════════════════════════════════════════
# Section 4: CLI
# ═══════════════════════════════════════════════════════════════════════════
#
# Entry point when the module is run as a script. getopt-based argument
# parsing; see Usage() for the flag list. An argparse migration is planned
# for v2.2 but not in this release.

if __name__ == "__main__":
    def Usage():
        print("""Usage:
    --help or -h to show this message
    --lpath or -l to select the quest_list file path (./quest_list by default)
    --epath or -e to select the working folder path (./pre_qc by default)
    --all or -a to copy to pre_qc folder all the quests even they have no define tokens
    --compile or -c to automatically run ./qc for each quest (False by default)
    --nopre or -n to just read the list without start processing (False by default)
    --verbose or -v to enable verbosity (False by default)
    --backup or -b to perform a backup of object (False by default)
    --file or -f to compile a single quest file
    # ./pre_qc.py
    # ./pre_qc.py -cf game_option.quest
    # ./pre_qc.py -l quest_list -e pre_qc
    # ./pre_qc.py -l ./muhsecret/quest_list -e ./foldername/pre_qc
    # ./pre_qc.py -ac
    # ./pre_qc.py -bv
""")
    import getopt
    import os
    import sys
    try:
        # grab args
        optlist, args = getopt.getopt(sys.argv[1:], "hl:e:acnvbf:", ("help","lpath","epath","all","compile","nopre","verbose","backup","file"))
        # config
        v_bcomp = False
        v_bnpre = False
        v_copyall = COPYALL_DFT
        v_questlistpath = QUESTLIST_PATH_DFT
        v_workingpath = WORKINGPATH_DFT
        v_verbosity = VERBOSITY_DFT
        v_backup = BACKUP_DFT
        v_singlefile = ''
        # analyze args
        for o, a in optlist:
            if o in ("-h", "--help"):
                sys.exit(Usage())
            if o in ("-l", "--lpath"):
                v_questlistpath = a
            elif o in ("-e", "--epath"):
                v_workingpath = a
            elif o in ("-a", "--all"):
                v_copyall = True
            elif o in ("-c", "--compile"):
                v_bcomp = True
            elif o in ("-n", "--nopre"):
                v_bnpre = True
            elif o in ("-v", "--verbose"):
                v_verbosity = True
            elif o in ("-b", "--backup"):
                v_backup = True
            elif o in ("-f", "--file"):
                v_singlefile = a
            else:
                sys.exit(Usage())
        # check
        if (not v_questlistpath) or (not v_workingpath):
            sys.exit(Usage())
        # start
        pQC = PreQC(questlistpath=v_questlistpath, workingpath=v_workingpath, verbosity=v_verbosity, backup=v_backup, copyall=v_copyall, singlefile=v_singlefile)
        if not v_bnpre:
            pQC.benchFunc(pQC.Generate)
        if v_bcomp:
            pQC.benchFunc(pQC.Compile)
    except getopt.GetoptError as err:
        sys.exit(err)
