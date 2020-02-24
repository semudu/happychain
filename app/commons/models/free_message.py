import json
from bipwrapper.type.ctype import CType


class FreeMessage:
    def __init__(self, message_type: CType, content: str):
        self.type = message_type
        self.content = content

    def __init__(self, json_str):
        obj = json.loads(json_str)
        self.type = CType(obj["type"])
        self.content = obj["content"]

    @property
    def get_json_str(self):
        return '{"type": "%s", "content": "%s"}' % (self.type.value, self.content)
