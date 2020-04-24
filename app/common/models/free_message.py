import json
from bipwrapper.type.ctype import CType


class FreeMessage:
    def __init__(self, message_type, content):
        self.type = message_type
        self.content = content

    @classmethod
    def from_json(cls, json_str):
        obj = json.loads(json_str)
        return cls(CType(obj["type"]), obj["content"])

    def get_json_str(self):
        return '{"type": "%s", "content": "%s"}' % (self.type.value, self.content)
