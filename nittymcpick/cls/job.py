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

    def __is_subset(self, large, subset):
        return all((k in large and v == large[k]) for k,v in subset.items())

    def __lint_to_comments(self, _input):
        mr = self.__sgl.projects.get(self.__event.project_id).mergerequests.get(
            self.__event.object_attributes["iid"])

        existing_comments = [mr.discussions.get(
            x.id) for x in mr.discussions.list(all=True)]
        __all_notes = set()
        for e in existing_comments:
            __all_notes.update(e.attributes['notes'])

        new_comments = set()
        for f in _input:
            for e in existing_comments:
                __all_notes += e.attributes['notes']
            if not any([self.__is_subset(x, f.get_data()) for x in __all_notes]):
                new_comments.add(f.get_data())

        resolved_comments = set()
        for e in existing_comments:
            for n in e.attributes['notes']:
                if n["author"]["username"] != self.__args.botname:
                    continue
                if not any([self.__is_subset(n, x.get_data()) for x in _input]):
                    if n["resolvable"] and not n["resolved"]:
                        resolved_comments.add(e.attributes["id"])
                        
        print("Resolved {} issues for: {}".format(len(resolved_comments), self))
        print("New {} issues for: {}".format(len(new_comments), self))
        for f in new_comments:
            try:
                mr.discussions.create(f)
            except:
                try:
                    # for new files the old_line attribute
                    # will not be accepted by the API
                    # so let's retry it without it
                    del f["position"]["old_line"]
                    mr.discussions.create(f)
                except:
                    pass

        for f in resolved_comments:
            try:
                item = mr.discussions.get(f)
                item.resolved = True
                item.save()
            except Exception as e:
                print(e)
        print("Done with {}".format(self))
