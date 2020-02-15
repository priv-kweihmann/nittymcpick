import os

from unidiff import PatchSet
class DiffFile():

    def __init__(self, file, diff, base_sha, start_sha, head_sha, rootpath=""):
        self.__diff = "diff --git a/{} b/{}\n--- a/{}\n+++ b/{}\n{}".format(file, file, file, file, diff)
        self.__file = file
        self.__base_sha = base_sha
        self.__start_sha = start_sha
        self.__head_sha = head_sha
        self.__rootpath = rootpath
        self.__affectedlines = self.__get_modified_lines()

    def __get_modified_lines(self):
        res = []
        _patch = PatchSet(self.__diff)
        for _f in _patch.added_files + _patch.modified_files:
            for h in [x for x in _f]:
                res += h.target_lines()
        res = [x.target_line_no for x in res]
        return res
    
    def __getpath(self, relative=False):
        if not relative:
            if not self.__file.startswith("/"):
                return os.path.join(self.__rootpath, self.__file)
            return self.__file
        else:
            if not self.__file.startswith("/"):
                return self.__file
            return self.__file.replace(self.__rootpath, "", 1).lstrip("/")

    @property
    def file(self):
        return self.__getpath(relative=False)

    @property
    def relpath(self):
        return self.__getpath(relative=True)

    @property
    def diff(self):
        return self.__diff
    
    @property
    def base_sha(self):
        return self.__base_sha
    
    @property
    def affectedlines(self):
        return self.__affectedlines
    
    @property
    def start_sha(self):
        return self.__start_sha
    
    @property
    def head_sha(self):
        return self.__head_sha