import json
import logging
from threading import Thread
from Classes import proxyList
import Classes
import Telegram
import Parser


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

file_handler = logging.FileHandler('BotLogs.txt')
file_handler.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s %(name)s %(levelname)s  %(message)s')
file_handler.setFormatter(formatter)

logger.addHandler(file_handler)

with open('users.json', 'r') as f:
    userlist = json.load(f)
    for user in userlist.get("Users"):
        Classes.Users.append(Classes.User(user.get("id"), user.get("role"), user.get("links"), user.get("lastParse"),
                          user.get("linksName"), user.get("linkLimit"), user.get("lifetime")))
logger.info(f"INITIALIZATION... USER LOADED: {len(Classes.Users)}")

with open('users.json', 'r') as f:
    data = json.load(f)
    for proxy in data["Proxies"]:
        proxyList.append(proxy)
logger.info(f"INITIALIZATION... PROXIES LOADED: {len(proxyList)}")


for user in Classes.Users:
    for link in user.links:
        user.linkLimit -= 1


t1 = Thread(target=Telegram.TelegramModule)
t1.start()
t2 = Thread(target=Parser.main_parsing)
t2.start()
t1.join()
t2.join()

