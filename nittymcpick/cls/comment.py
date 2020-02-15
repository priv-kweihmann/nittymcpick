class Comment():

    def __init__(self, text, line, file, base_sha, start_sha, head_sha):
        self.__body = text
        self.__line = line
        self.__file = file
        self.__base_sha = base_sha
        self.__start_sha = start_sha
        self.__head_sha = head_sha

    def __repr__(self):
        return "{}: {}: {}".format(self.__file, self.__line, self.__body)
    
    @property
    def body(self):
        return self.__body

    @property
    def line(self):
        return self.__line
    
    @property
    def line(self):
        return self.__line

    def get_data(self):
        return {
            "body": self.__body,
            "position": {
                "base_sha": self.__base_sha,
                "start_sha": self.__start_sha,
                "head_sha": self.__head_sha,
                "position_type": "text",
                "new_line": self.__line,
                "new_path": self.__file
            }
        }

    def equals(self, disobj):
        _data = self.get_data()
        if _data["body"] == disobj["body"] and \
        _data["position"]["new_line"] == disobj["position"]["new_line"] and \
        _data["position"]["new_path"] == disobj["position"]["new_path"]:
            print("Comment {} already exists".format(_data["body"]))
            return True
        return False