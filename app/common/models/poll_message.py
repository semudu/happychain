class PollMessage:
    def __init__(self, id, title, desc, image):
        self.__id = id
        self.__title = title
        self.desc = desc
        self.image = image

    @property
    def command(self):
        return self.__id

    @property
    def title(self):
        return self.__title

    @property
    def description(self):
        return self.desc

    @property
    def image_url(self):
        return self.image
