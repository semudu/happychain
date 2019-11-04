from enum import Enum


class Message(Enum):
    BIP_HELP = "Puan sorgulamak için PUAN yaz gönder. \n\nArkadaşına puan göndermek için arkadaşının isminin ilk 3-4 harfini yaz, gelen listeden seçimini yap, puanı gönder.\n\nArkadaşlarının isimlerini liste halinde görmek için LISTE  yaz gönder.",
    BIP_BALANCE = "IMS Bakiyen: %s IMS\n\nGönderdiğin: 👼 %s IMS \nSana Gelen: 🙏 %s IMS",
    BIP_LAST_SENT = "Gönderdiğin son %s mesaj:\n\n",
    BIP_LAST_RECEIVED = "Aldığın son %s mesaj:\n\n"
