"""
Бафер для торгового чата
"""

import re
import time
from datetime import timedelta

from vk_api import *
from vk_api.longpoll import *


class Baffer(object):
    """ Заготовка класса """

    # Версия
    VERSION = 2.1

    def __init__(self, token: str, channel: int, index: int, race: str):
        """ Конструктор """
        self.token = token
        self.channel = channel
        self.index = index
        self.race = race
        self.avail = False
        self.session = None
        self.longpoll = None
        self.time = datetime.min
        self.reg_app = self.compile(r"^апо (\d+)")
        self.reg_query = self.compile(r"^(?:\[.+?]|хочу) баф (.+)")
        self.reg_set = self.compile(r"^✨\[id(\d+)\|(.+?)], на Вас наложено благословение")

    def run(self):
        """ Жизненный цикл """
        print("Initialization...")
        self.session = VkApi(token=self.token)
        self.longpoll = VkLongPoll(self.session)
        print("-> Loaded v%s" % self.VERSION)
        # Пока не выключится
        while True:
            try:
                for event in self.longpoll.listen():
                    if event.type == VkEventType.MESSAGE_NEW:
                        self.check(event)
            except Exception as e:
                print("Network error:")
                print(e)
                time.sleep(3)
                pass

    def compile(self, pattern: str):
        """ Сборка регулярки """
        return re.compile(pattern, re.IGNORECASE | re.UNICODE | re.DOTALL | re.MULTILINE)

    def send(self, text: str, reply: int):
        """ Отправка сообщения """
        tmp_params = {
            "peer_id": self.channel,
            "message": text,
            "random_id": 0
        }
        # Если надо ответить
        if reply:
            tmp_params["reply_to"] = reply
        # Отправим
        return self.session.method("messages.send", tmp_params)

    def delete(self, messagesids: int):
        """ Удаление сообщения """
        tmp_params = {
            "message_ids": messagesids,
            "delete_for_all": 1
        }
        # Отправим
        return self.session.method("messages.delete", tmp_params)

    def check(self, event: {}):
        """ Обработка запроса """
        if not event.from_chat:
            return False
        if event.peer_id != self.channel:
            return False
        # Найдено смена апостола
        tmp_match = self.reg_app.match(event.message)
        if tmp_match:
            return self.useApp(event, tmp_match)
        # Пробьем регулярку
        tmp_match = self.reg_query.search(event.message)
        if tmp_match:
            return self.useBaf(event, tmp_match)
        # Найдено наложение бафа
        tmpMatch = self.reg_set.match(event.message)
        if tmpMatch:
            return self.usePay()
        # Иначе нчиего
        return False

    def usePay(self):
        """ Учет наложения бафа """
        if self.avail:
            self.time = datetime.today() + timedelta(minutes=15)
        # Все хорошо
        return True

    def useApp(self, event: {}, match: {}):
        """ Разрешение бафера """
        self.avail = int(match[1]) == self.index
        if not self.avail:
            return True
        tmp_time = datetime.today()
        if tmp_time < self.time:
            tmp_time = (self.time - tmp_time).total_seconds()
            tmp_min = int(tmp_time / 60)
            tmp_sec = int(tmp_time % 60)
            tmp_time = "⌛"
            if tmp_min > 0:
                tmp_time += " %s мин." % tmp_min
            tmp_time += " %s сек." % tmp_sec
        else:
            tmp_time = "⌛ доступен"
        self.send("%s (%s)" % (tmp_time, self.race), event.message_id)
        return True

    def useBaf(self, event: {}, match: {}):
        """ Отправим и удалим """
        if self.avail:
            print("%s queried baf %s" % (event.user_id, match[1]))
            self.delete(self.send("Благословение %s" % match[1], event.message_id))
            time.sleep(3)
        return True


Baffer("", 2000000000, 4, "человек").run()
