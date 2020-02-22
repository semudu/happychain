from collections import defaultdict
from app.service.channel import Channel
from app.commons.bip_request import BipRequest
from app.commons.constants.command import Command


class Task:
    def __init__(self):
        self.channel = Channel()

    def __tasks(self):
        return {
            Command.MENU: self.channel.send_menu,
            Command.HELP: self.channel.send_help_message,
            Command.POINT: self.channel.send_balance,
            Command.LAST_SENT: self.channel.send_last_n_sent,
            Command.LAST_RECEIVED: self.channel.send_last_n_received,
            Command.MESSAGE_LIST: self.channel.send_message_list,
            Command.FINISH_TRANSACTION: self.channel.send_message
        }

    def run(self, request_json):
        request = BipRequest(request_json)
        task = defaultdict(lambda: self.channel.non_command, self.__tasks())
        task(request)
