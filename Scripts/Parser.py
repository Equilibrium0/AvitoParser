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
from DataBase import write_to_base, get_price_from_base

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
    t = 0
    timer = time.time()
    while True:
        if time.time() - timer >= t:
            t = random.uniform(T-5, T+5)
            linkPool = []
            for user in Users:
                if user.lifetime > 0:
                    user.lifetime -= time.time()-timer
                    for link in range(len(user.links)):
                        newlink = True
                        for i in linkPool:
                            if user.links[link] == i.href:
                                i.users.append(user.ID)
                                i.usersLinkID.append(link)
                                newlink = False
                        if newlink:
                            new = Link(user.links[link])
                            if "avito" in user.links[link]:
                                new.link_type = "avito"
                            elif "youla" in user.links[link]:
                                new.link_type = "youla"
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
    print("start parsing")
    print(linkfrompool.href)
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
        print("link type: ", linkfrompool.link_type)

        if "Доступ ограничен: проблема с IP" in drive.page_source:
            badProxy.append(proxyList[proxyNumber])
            proxyList.remove(proxyList[proxyNumber])
            logger.warning(f"BAD PROXY!, HREF: {linkfrompool.href}")
            return
        print("Enter 5")
        match linkfrompool.link_type:
            case "detailed_avito": await detailed_link(linkfrompool, drive.page_source)
            case "avito": await avito_parse(linkfrompool, drive.page_source)
            # case "youla": await youla_parsing(linkfrompool, drive.page_source)

    except Exception as e:
        badProxy.append(proxyList[proxyNumber])
        proxyList.remove(proxyList[0])
        print(e)
        logger.error(f"PROXY ERROR!, HREF: {linkfrompool.href}")
        return


async def avito_parse(linkfrompool, html_code):
    print("avito parse")
    try:
        soup = BeautifulSoup(html_code, "html.parser")
        items = soup.find_all('div', {'data-marker': 'item'})
        links = []
        for item in items:
            links.append(item.find('a').get('href'))

        lastItem = 40

        for link in range(len(links)):
            if links[link] in Users[FindUser(linkfrompool.users[0])].lastParse[linkfrompool.usersLinkID[0]]:
                lastItem = link
                break

        if Users[FindUser(linkfrompool.users[0])].lastParse[linkfrompool.usersLinkID[0]] != []:
            for i in range(lastItem):
                fulllink = "https://www.avito.ru" + links[i]
                detailed_thread = Thread(target=pre_data_vacuum, args=(linkfrompool, fulllink, ))
                detailed_thread.start()

                # asyncio.create_task(data_vacuum(fulllink))

                # price = items[i].find('meta', {'itemprop': 'price'}).get('content')
                # title = items[i].find('a').get('title')[11:len(items[i].find('a').get('title')) - 13]
                #
                # for user in range(len(linkfrompool.users)):
                #     message = (
                #         f"Новое объявление по запросу {Users[FindUser(linkfrompool.users[user])].linksNames[linkfrompool.usersLinkID[user]]}\n\n"
                #         f"{title}\n\n"
                #         f"Цена: {price} руб\n\n"
                #         f" {fulllink}")
                #     asyncio.run_coroutine_threadsafe(
                #         bot.send_message(chat_id=Users[FindUser(linkfrompool.users[user])].ID, text=message), teleloop)

        for user in range(len(linkfrompool.users)):
            Users[FindUser(linkfrompool.users[user])].lastParse[linkfrompool.usersLinkID[user]] = links

        logger.info(f"LINK PARSE SUCCESSFULLY,  HREF:{linkfrompool.href}")
    except Exception as e:
        logger.error(f"REMOVAL ERROR!, HREF: {linkfrompool.href}")


def pre_data_vacuum(linkfrompool, new_href):
    newloop = asyncio.new_event_loop()
    asyncio.set_event_loop(newloop)
    asyncio.run(data_vacuum(linkfrompool, new_href))


async def data_vacuum(linkfrompool, new_href):
    print("data vacuum")
    linkfrompool.href = new_href
    linkfrompool.link_type = "detailed_avito"
    await link_parse(linkfrompool)


async def detailed_link(linkfrompool, html_code):
    print("detailed link")
    print("href: ", linkfrompool.href)
    soup = BeautifulSoup(html_code, 'html.parser')
    tables = soup.find_all('span', {'itemprop': 'itemListElement'})
    price = soup.find('span', {'itemprop': 'price'}).get('content')
    table = tables[4].find('a').get('title')
    name = soup.find('h1', {'itemprop': 'name'}).text
    spec = soup.find('div', {'data-marker': 'item-view/item-params'})
    spec = spec.find_all('li')
    fields = []
    values = []
    for i in spec:
        fields.append(i.text[0:i.text.find(':')])
        values.append(i.text[i.text.find(':')+2:len(i.text)])

    write_to_base(table, name, price, fields, values)

    for user in range(len(linkfrompool.users)):
        message = (
            f"Новое объявление по запросу {Users[FindUser(linkfrompool.users[user])].linksNames[linkfrompool.usersLinkID[user]]}\n\n"
            f"{name}\n\n"
            f"Цена: {price} руб\n\n"
            f"Средняя цена аналогичного товара: {get_price(table, fields, values)} руб\n\n"
            f" {linkfrompool.href}")
        asyncio.run_coroutine_threadsafe(
            bot.send_message(chat_id=Users[FindUser(linkfrompool.users[user])].ID, text=message), teleloop)


async def get_price(table, fields, values):
    prices = get_price_from_base(table, fields, values)
    av_price = 0
    for price in prices:
        av_price += price
    av_price = av_price/len(prices)
    if av_price == 0:
        return "Нет данных"
    return av_price



# async def youla_parsing(linkfrompool, html_code):
#     try:
#         print("Enter0")
#         soup = BeautifulSoup(html_code, "html.parser")
#         items = soup.find_all('div', {'data-test-component':'ProductOrAdCard'})
#
#         for item in items:
#             try:
#                 item.find("a").get('title')
#                 item.find("span", {"data-test-component" : "Price"})
#             except:
#                 items.remove(item)
#
#         links = []
#
#         for item in items:
#             links.append(item.find("a").get('href'))
#
#         lastItem = 40
#
#         for link in range(len(links)):
#             if links[link] in Users[FindUser(linkfrompool.users[0])].lastParse[linkfrompool.usersLinkID[0]]:
#                 lastItem = link
#                 break
#
#         if Users[FindUser(linkfrompool.users[0])].lastParse[linkfrompool.usersLinkID[0]] != [] or True:
#             print("Enter1")
#             for i in range(lastItem):
#                 print("Enter2")
#                 fulllink = "https://www.youla.ru" + links[i]
#                 price = items[i].find('span', {'data-test-component":"Price'}).text[0:len(items[i].find('span', {"data-test-component":"Price"}).text)- 6]
#                 title = items[i].find('a').get('title')
#
#                 for user in range(len(linkfrompool.users)):
#                     print("Enter3")
#                     message = (
#                         f"Новое объявление по запросу {Users[FindUser(linkfrompool.users[user])].linksNames[linkfrompool.usersLinkID[user]]}\n\n"
#                         f"{title}\n\n"
#                         f"Цена: {price} руб\n\n"
#                         f" {fulllink}")
#                     print("Enter4")
#                     asyncio.run_coroutine_threadsafe(
#                         bot.send_message(chat_id=Users[FindUser(linkfrompool.users[user])].ID, text=message), teleloop)
#                     print("Enter5")
#
#         for user in range(len(linkfrompool.users)):
#             Users[FindUser(linkfrompool.users[user])].lastParse[linkfrompool.usersLinkID[user]] = links
#
#         logger.info(f"LINK PARSE SUCCESSFULLY,  HREF:{linkfrompool.href}")
#
#     except Exception as e:
#         print(e)
