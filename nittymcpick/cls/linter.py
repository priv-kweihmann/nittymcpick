import json
import subprocess
import re
import sys

from nittymcpick.cls.comment import Comment

class Linter():

    def __init__(self, _config, _appargs):
        self.__name = _config["linter"]["name"]
        self.__exec = _config["linter"]["path"]
        self.__args = _config["linter"]["args"]
        self.__appargs = _appargs
        self.__retregex = _config["linter"]["ret_regex"]
        self.__pattern = _config["matches"]["pattern"]
        self.__lineadjust = _config["linter"]["tweaks"]["line_count_adjust"]
        self.__singlefileexec = _config["linter"]["tweaks"]["single_file_exec"]

    def __eval(self, _in, _files):
        res = []
        for m in re.finditer(self.__retregex, _in, re.MULTILINE):
            _tpl = {
                "file": "Unknown file",
                "severity": "issue",
                "line": 1,
                "message": ""
            }
            for k, v in _tpl.items():
                if isinstance(v, int):
                    try:
                        _t = int(m.group(k).strip())
                    except (IndexError, ValueError):
                        _t = _tpl[k]
                    _tpl[k] = _t + self.__lineadjust
                else:
                    try:
                        _tpl[k] = m.group(k).strip()
                    except IndexError:
                        pass
            _f = [x for x in _files if x.file == _tpl["file"]]
            if _f:
                _f = _f[0]
                # if finding is not in change set, don't issue anything
                if (_tpl["line"] in _f.affectedlines and self.__appargs.onlynew) or (not self.__appargs.onlynew):
                    _msg = "{} found a potential {} - {}".format(self.__name, _tpl["severity"], _tpl["message"])
                    res.append(Comment(_msg, _tpl["line"], _f.relpath, _f.base_sha, _f.start_sha, _f.head_sha))
        return res

    def Run(self, _files):
        _matchfiles = [x for x in _files if re.match(self.__pattern, x.file)]
        if self.__singlefileexec:
            _loops = [[x] for x in _matchfiles]
        else:
            _loops = _matchfiles
        out = ""
        for l in _loops:
            try:
                out += subprocess.check_output([self.__exec] + self.__args + [x.file for x in l], 
                                            universal_newlines=True, stderr=subprocess.STDOUT)
            except subprocess.CalledProcessError as e:
                out += e.stdout or ""
        return self.__eval(out, _matchfiles)

    @staticmethod
    def SetupLinter(_args):
        res = []
        __config = []
        try:
            with open(_args.config) as i:
                __config = json.load(i)
        except (json.JSONDecodeError, FileNotFoundError, PermissionError) as e:
            sys.stderr.write("Can't decode config: {}\n".format(e))
            sys.exit(-1)
        for c in __config:
            res.append(Linter(c, _args))
        return res