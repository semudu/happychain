class Globals:
    LOAD_BALANCE_CRON = "* * * * MON"
    RESET_BALANCE_CRON = "* * 1 * *"
    LOAD_BALANCE_TIME = "01:00"
    RESET_BALANCE_TIME = "01:00"
    BIRTHDAY_MSG_TIME = "08:30"
    SPECIAL_DATE_MSG_TIME = "09:00"
    LOAD_BALANCE_AMOUNT = 200
    SEND_SAME_PERSON_LIMIT = 3
    SEND_SAME_TEAM_LIMIT = 10
    SEND_WAIT_LIMIT = 10  # SECOND
    SEND_AMOUNT = 10
    EARN_AMOUNT = 1
    DEFAULT_PASSWD = "123456"
    DELIMITER = ":::"


class Role:
    USER = "USER"
    SCOPE_ADMIN = "SCOPE_ADMIN"
    SUPER_ADMIN = "SUPER_ADMIN"


class Command:
    HELP = "__help"
    MENU = "__menu"
    POINT = "__point"
    LAST_SENT = "__last_sent"
    LAST_RECEIVED = "__last_received"


class Poll:
    MENU = "__menu"
    SHORT_LIST = "__short_list"
    MESSAGE_LIST = "__message_list"
    QUICK_REPLY = "__quick_reply"


class Image:
    SHORT_LIST_URL = "http://timsac.turkcell.com.tr/scontent/p2p/19022018/09/Pe336b30c03db3493052cdede73334c1b57443c13c219e3b7d70441d99add1e0d7.png"
    REASON_LIST_URL = "http://timsac.turkcell.com.tr/scontent/p2p/15032018/11/Pc2de09311da2d8e88395bdacec4c53a40b8801012dc80f501c4f4e397e258b318.jpg"


class Message:
    HELP = "Puan sorgulamak için PUAN yaz gönder. \n\nArkadaşına puan göndermek için arkadaşının isminin ilk 3-4 harfini yaz, gelen listeden seçimini yap, puanı gönder.\n\nArkadaşlarının isimlerini liste halinde görmek için LISTE  yaz gönder."
    BALANCE = "IMS Bakiyen: %s IMS\n\nGönderdiğin: 👼 %s IMS \nSana Gelen: 🙏 %s IMS"
    LAST_SENT = "Gönderdiğin son %s mesaj:\n\n"
    LAST_RECEIVED = "Aldığın son %s mesaj:\n\n"
    SHORT_LIST_TITLE = "%s ile başlayan kullanıcı isimleri: "
    SHORT_LIST_DESC = "İsmi seçip %s IMS Yolla!\n\n"
    SINGLE_TITLE = "%s ile başlayan sadece %s varmış 🙃"
    SINGLE_DESC = "Ona %s IMS yollamak ister misin?\n\n"
    NOT_FOUND = "%s ile başlayan kimseyi bulamadım 🙄"
    REASON_LIST_TITLE = "%s mesajınla birlikte %s IMS yolluyorsun 😇"
    REASON_LIST_DESC = "Ona hangi mesajı iletmemi istersin?"
    SAME_PERSON_LIMIT = "Malesef aynı kişiye günde %s kere gönderim yapabilirsin 🙄"
    SAME_TEAM_LIMIT = "Malesef kendi takımına günde %s kere gönderim yapabilirsin 🙄"
    INSUFFICIENT_FUNDS = "Tüm bakiyeni harcamışsın. 👏 Bir süre beklemen gerekicek maalesef. Eminim güzel bir geri dönüşü olacaktır 😊"
    SENT_MESSAGE = "%s\n\n%s\n\nmesajını da ileterek %s IMS yolladın ve bu gönderimden sen de %s IMS kazanmış oldun 👏\n\nMevcut bakiyen: %s IMS"
    FREE_MESSAGE = "Yazacağın ilk mesaj %s gönderilecek."
    RECEIVED_MESSAGE = "%s sana aşağıdaki mesajla birlikte %s IMS yolladı."
