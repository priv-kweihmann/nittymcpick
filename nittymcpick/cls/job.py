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
        if self.__event.object_attributes["work_in_progress"] and \
                not self.__args.nowip:
            print("Skip WIP for: {}".format(self))
            return
        if self.__event.object_attributes["state"] in ["merged", "closed"]:
            # Don't act on closed or merged MRs
            print("Skip closed for: {}".format(self))
            return

        _path = self.__checkout_source_branch(self.__args.tmpdir)
        _files = self.__get_commits_diffs(_path)
        if _path:
            _finding = self.__run_linter(_files)
            self.__lint_to_comments(_finding)
            self.__remove_clone(_path)

    def __get_commits_diffs(self, _path):
        mr = self.__sgl.projects.get(self.__event.project_id).mergerequests.get(
            self.__event.object_attributes["iid"])
        changes = mr.changes(all=True)
        return [DiffFile(x["new_path"], x["diff"], changes["diff_refs"]["base_sha"], changes["diff_refs"]["start_sha"], changes["diff_refs"]["head_sha"], _path)
                for x in mr.changes(all=True)["changes"]]

    def __checkout_source_branch(self, path):
        _path = f"{path}/{self.__event.project_id}/{self.__event.object_attributes['iid']}"
        good = False
        for method in [self.__event.object_attributes["source"]["ssh_url"], self.__event.object_attributes["source"]["http_url"]]:
            try:
                if os.path.exists(_path):
                    self.__remove_clone(_path)
                subprocess.check_call(
                    ["git", "clone", method, _path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                subprocess.check_call(["git", "-C", _path, "checkout", self.__event.object_attributes["last_commit"]["id"]],
                                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
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

        existing_comments = [mr.discussions.get(
            x.id) for x in mr.discussions.list(all=True)]
        __all_notes = []
        for e in existing_comments:
            __all_notes += e.attributes['notes']

        new_comments = []
        for f in _input:
            for e in existing_comments:
                __all_notes += e.attributes['notes']
            if not any([f.equals(x) for x in __all_notes]):
                if f.get_data() not in new_comments:
                    new_comments.append(f.get_data())

        resolved_comments = []
        for e in existing_comments:
            for n in e.attributes['notes']:
                if n["author"]["username"] != self.__args.botname:
                    continue
                if not any([x.equals(n) for x in _input]):
                    if (e, n["id"]) not in resolved_comments:
                        resolved_comments.append((e, n["id"]))
        print("Resolved {} issues for: {}".format(len(resolved_comments), self))
        print("New {} issues for: {}".format(len(new_comments), self))
        for f in new_comments:
            mr.discussions.create(f)

        for f in resolved_comments:
            try:
                f[0].notes.delete(f[1])
            except Exception as e:
                print(e)
        print("Done with {}".format(self))
