import json
from bipwrapper.type.ctype import CType


class MessageContent:
    def __init__(self, ctype: CType, content):
        self.type = ctype
        self.content = content

    @classmethod
    def from_json(cls, json_str):
        obj = json.loads(json_str)
        return cls(CType(obj["type"]), obj["content"])

    def get_json_str(self):
        return '{"type": "%s", "content": "%s"}' % (self.type.value, self.content)
