from Classes import Users, FindUser, Link, T, C
from Telegram import send_to_user

import time
import logging
import random
from threading import Thread
import asyncio
from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.edge.options import Options
from seleniumwire import webdriver

from Classes import proxyList, badProxy
from Telegram import bot, teleloop
proxyNumber = 0

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

file_handler = logging.FileHandler('BotLogs.txt')
file_handler.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s %(name)s %(levelname)s  %(message)s')
file_handler.setFormatter(formatter)

logger.addHandler(file_handler)


def linkcount():
    number= 0
    for user in Users:
        for link in user.links:
            number += 1
    return number


def userdelay():
    delay = []
    for user in Users:
        delay.append(len(user.links))
    return delay


def main_parsing():
    t = 30.0
    timer = time.time()
    while True:
        if time.time() - timer >= t:
            t = random.uniform(T-5, T+5)
            print(f"t = {t}")
            linkPool = []
            print("linkpool ", linkPool)
            for user in Users:
                if user.lifetime > 0:
                    print(time.time())
                    user.lifetime -= time.time()-timer
                    print(user.lifetime)
                    for link in range(len(user.links)):
                        newlink = True
                        for i in linkPool:
                            if user.links[link] == i.href:
                                i.users.append(user.ID)
                                i.usersLinkID.append(link)
                                newlink = False
                        if newlink:
                            new = Link(user.links[link])
                            new.users.append(user.ID)
                            new.usersLinkID.append(link)
                            linkPool.append(new)
                else:
                    print("Out of time")
            if linkPool == []:
                time.sleep(t)
                continue
            delay = t/len(linkPool)
            timer = time.time()
            logger.info(f"START PARSING CYCLE, LINKS IN POOL: {len(linkPool)}, DELAY: {delay}")
            for linkfrompool in linkPool:
                parse = Thread(target=link_betwen, args=(linkfrompool, ))
                parse.start()
                time.sleep(delay)


def link_betwen(linkfrompool):
    newloop = asyncio.new_event_loop()
    asyncio.set_event_loop(newloop)
    asyncio.run(link_parse(linkfrompool))


async def link_parse(linkfrompool):
    global proxyNumber
    logger.info(f"LINK PARSE HREF: {linkfrompool.href}, USERS: {linkfrompool.users}, LINKIDS: {linkfrompool.usersLinkID}, PROXY: {proxyList[proxyNumber]}")
    try:
        if len(proxyList) == 0:
            logger.warning(f"OUT OF PROXIES!, HREF: {linkfrompool.href}")
            return

        edge_options = Options()
        proxopt = {
            'proxy': {
                'http': f'{proxyList[proxyNumber]}',
                'https': f'{proxyList[proxyNumber]}',
            },
        }
        print('Current Proxy', proxyList[proxyNumber])
        proxyNumber = (proxyNumber + 1) % len(proxyList)
        # edge_options.add_argument("--headless=new")
        prefs = {'profile.default_content_setting_values': {'cookies': 2, 'images': 2, 'javascript': 2,
                                                            'plugins': 2, 'popups': 2, 'geolocation': 2,
                                                            'notifications': 2, 'auto_select_certificate': 2,
                                                            'fullscreen': 2,
                                                            'mouselock': 2, 'mixed_script': 2, 'media_stream': 2,
                                                            'media_stream_mic': 2, 'media_stream_camera': 2,
                                                            'protocol_handlers': 2,
                                                            'ppapi_broker': 2, 'automatic_downloads': 2,
                                                            'midi_sysex': 2,
                                                            'push_messaging': 2, 'ssl_cert_decisions': 2,
                                                            'metro_switch_to_desktop': 2,
                                                            'protected_media_identifier': 2, 'app_banner': 2,
                                                            'site_engagement': 2,
                                                            'durable_storage': 2}}
        edge_options.add_experimental_option('prefs', prefs)
        drive = webdriver.Edge(options=edge_options, seleniumwire_options=proxopt)
        drive.get(linkfrompool.href)

        if "Доступ ограничен: проблема с IP" in drive.page_source:
            badProxy.append(proxyList[proxyNumber])
            proxyList.remove(proxyList[proxyNumber])
            logger.warning(f"BAD PROXY!, HREF: {linkfrompool.href}")
            return

    except Exception as e:
        badProxy.append(proxyList[proxyNumber])
        proxyList.remove(proxyList[0])
        logger.error(f"PROXY ERROR!, HREF: {linkfrompool.href}")
        return

    try:
        soup = BeautifulSoup(drive.page_source, "html.parser")
        items = soup.find_all('div', {'data-marker': 'item'})
        links = []
        for item in items:
            links.append(item.find('a').get('href'))

        lastItem = 40

        for link in range(len(links)):
            if links[link] in Users[FindUser(linkfrompool.users[0])].lastParse[linkfrompool.usersLinkID[0]]:
                lastItem = link
                break

        print(lastItem)
        print(Users[FindUser(linkfrompool.users[0])].lastParse[linkfrompool.usersLinkID[0]])

        if Users[FindUser(linkfrompool.users[0])].lastParse[linkfrompool.usersLinkID[0]] != []:
            print("Enter1")
            for i in range(lastItem):
                print("Enter2")
                fulllink = "https://www.avito.ru" + links[i]
                price = items[i].find('meta', {'itemprop': 'price'}).get('content')
                title = items[i].find('a').get('title')[11:len(items[i].find('a').get('title'))-13]

                for user in range(len(linkfrompool.users)):
                    print("Enter3")
                    message = (f"Новое объявление по запросу {Users[FindUser(linkfrompool.users[user])].linksNames[linkfrompool.usersLinkID[user]]}\n\n"
                               f"{title}\n\n"
                               f"Цена: {price} руб\n\n"
                               f" {fulllink}")
                    print("Enter4")
                    asyncio.run_coroutine_threadsafe(bot.send_message(chat_id=Users[FindUser(linkfrompool.users[user])].ID, text=message), teleloop)
                    print("Enter5")

        for user in range(len(linkfrompool.users)):
            Users[FindUser(linkfrompool.users[user])].lastParse[linkfrompool.usersLinkID[user]] = links

        logger.info(f"LINK PARSE SUCCESSFULLY,  HREF:{linkfrompool.href}")
    except Exception as e:
        logger.error(f"REMOVAL ERROR!, HREF: {linkfrompool.href}")