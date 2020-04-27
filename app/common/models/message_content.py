import json
from bipwrapper.type.ctype import CType


class MessageContent:
    def __init__(self, ctype: CType, content):
        self.type = ctype
        self.content = content

    @property
    def ctype(self):
        return self.type

    @property
    def message(self):
        return self.content

    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__)

    @classmethod
    def from_json(cls, json_str):
        obj = json.loads(json_str)
        return cls(CType(obj["type"]), obj["content"])
