import os
import subprocess
import sys
import shutil

from nittymcpick.cls.difffile import DiffFile

class Job():
    def __init__(self, event, gl, args, sgl, linter):
        self.__event = event
        self.__gl = gl
        self.__args = args
        self.__sgl = sgl
        self.__linter = linter

    def __repr__(self):
        return "Project: {}, MR: {}".format(self.__event.project_id, self.__event.object_attributes["iid"])

    def Run(self):
        if self.__event.work_in_progress and not self.__args.nowip:
            return
        if self.__event.state in ["merged", "closed"]:
            # Don't act on closed or MRs
            return
        _path = self.__checkout_source_branch()
        _files = self.__get_commits_diffs(_path)
        if _path:
            _finding = self.__run_linter(_files)
            self.__lint_to_comments(_finding)
            self.__remove_clone(_path)

    def __get_commits_diffs(self, _path):
        mr = self.__sgl.projects.get(self.__event.project_id).mergerequests.get(
            self.__event.object_attributes["iid"])
        changes = mr.changes()
        return [DiffFile(x["new_path"], x["diff"], changes["diff_refs"]["base_sha"], changes["diff_refs"]["start_sha"], changes["diff_refs"]["head_sha"], _path)
                for x in mr.changes()["changes"]]

    def __checkout_source_branch(self, path="/tmp"):
        _path = f"{path}/{self.__event.project_id}/{self.__event.object_attributes['iid']}"
        good = False
        for method in [self.__event.object_attributes["source"]["ssh_url"], self.__event.object_attributes["source"]["http_url"]]:
            try:
                if os.path.exists(_path):
                    self.__remove_clone(_path)
                subprocess.check_call(["git", "clone", method, _path])
                subprocess.check_call(["git", "-C", _path, "checkout", self.__event.object_attributes["last_commit"]["id"]])
                good = True
                break
            except subprocess.CalledProcessError:
                pass
        if not good:
            sys.stderr.write("Ohhhhhhh noooo - check out failed\n")
            return None
        return _path

    def __remove_clone(self, _path):
        shutil.rmtree(_path, ignore_errors=True)

    def __run_linter(self, _files):
        res = []
        for l in self.__linter:
            res += l.Run(_files)
        return res

    def __lint_to_comments(self, _input):
        mr = self.__sgl.projects.get(self.__event.project_id).mergerequests.get(
            self.__event.object_attributes["iid"])
        for f in _input:
            mr.discussions.create(f.get_data())