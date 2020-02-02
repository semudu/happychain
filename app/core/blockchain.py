# import logging
#
# import requests
#
# from .database import Database
#
# logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)
#
#
# class Blockchain:
#     def __init__(self, config):
#         self.db = Database(config)
#         self.balance_url = config.BLOCKCHAIN_URL + "/balance"
#         self.new_transaction_url = config.BLOCKCHAIN_URL + "/transactions/new"
#         self.headers = {"Content-Type": "application/json"}
#
#     def create_wallet(self, user_id):
#         # TODO
#         pass
#
#     def get_balance(self, user_id):
#         wallet = self.db.get_wallet_by_userid(user_id)
#         response = requests.post(self.balance_url, headers=self.headers, json={
#             "wallet": wallet["wallet_key"]
#         })
#         if response:
#             return response.json()["Type1"]
#         return -1
#
#     def send_coin(self, amount, sender_user_id, receiver_user_id):
#         # TODO
#         pass
