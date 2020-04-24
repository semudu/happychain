from bipwrapper import BipWrapper
from config import BIP
from .database import Database

database = Database()
bip = BipWrapper(BIP.ENVIRONMENT, BIP.USERNAME, BIP.PASSWORD)
