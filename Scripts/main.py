import asyncio
import sys
import json
import random
import string
from bs4 import BeautifulSoup
from threading import Thread
import time
from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup
from selenium import webdriver
from selenium.webdriver.edge.options import Options
from seleniumwire import webdriver

proxyList = []
badProxy = []
teleloop = asyncio.new_event_loop()


########################################################################################################################
##########################################################User Module###################################################
########################################################################################################################

Users = []

class User:
    ID = ""
    role = "User"
    links = []
    lastParse = []
    linksNames = []
    linkLimit = 1
    lifetime = 2592000
    lifetimeWarning = True

    def __init__(self, user_id, user_role="User", user_links=[], user_lp=[], user_lk=[], user_linkslim=1, user_life=259200):
        self.ID = user_id
        self.role = user_role
        self.links = user_links
        self.lastParse = user_lp
        self.linksNames = user_lk
        self.linkLimit = user_linkslim
        self.lifetime = user_life

    def to_json(self):
        usr = {"id": self.ID, "role": self.role, "links": self.links,"lastParse": self.lastParse,
               "linksName": self.linksNames, "linkLimit": self.linkLimit, "lifetime": self.lifetime}
        with open('users.json') as f:
            data = json.load(f)

        data["Users"].append(usr)

        with open('users.json', 'w') as f:
            json.dump(data, f)


class Link:
    href = ''
    users = []
    usersLinkID = []

    def __init__(self, link, users, ID):
        self.href = link
        self.users = users
        self.id = ID


def keygen():
    chars = string.ascii_letters + string.digits
    key = ''.join(random.choice(chars) for i in range(24))
    return key


def newkey(role):
    key = keygen()
    with open('users.json') as f:
        data = json.load(f)

    if role == "SuperUser":
        data["SuperKeys"].append(key)
    elif role == "Admin":
        data["AdminKeys"].append(key)
    else:
        return "Error"

    with open('users.json', 'w') as f:
        json.dump(data, f)

    return key


def FindUser(ID):
    try:
        for i in range(len(Users)):
            if Users[i].ID == ID:
                index = i
                break
        return index
    except Exception as e:
        return "null"


with open('users.json', 'r') as f:
    userlist = json.load(f)
    for user in userlist.get("Users"):
        Users.append(User(user.get("id"), user.get("role"), user.get("links"), user.get("lastParse"),
                          user.get("linksName"), user.get("linkLimit"), user.get("lifetime")))

for user in Users:
    for link in user.links:
        user.linkLimit -=1

########################################################################################################################
#########################################################Telegram Module################################################
########################################################################################################################

TOKEN = "6776153287:AAF-Xo-O7gRLDNWTI0ArI08rjlOuINbBqVM"
bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot=bot, storage=storage)


####################Buttons################################

startButtonLine1 = ["Добавить ссылку", "Удалить ссылку"]
startButtonLine2 = ["Ввести код", "Статус аккаунта"]
startButtonAdminLine2 = ["Добавить прокси", "Удалить прокси"]
startButtonAdminLine3 = ["Задать интервал парсинга", "Задать интервал отдыха"]
startButtonAdminLine4 = ["Статус системы", "Сгенерировать код", "Экстренная остановка"]
startButtonAdminLine5 = "Статус аккаунта"
generateCodeButton = ["Суперпользователь", "Администратор"]
cancelButton = "Отмена"


########################Keyboards##########################

startKeyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
startKeyboard.add(*startButtonLine1)
startKeyboard.add(*startButtonLine2)

adminKeyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
adminKeyboard.add(*startButtonLine1)
adminKeyboard.add(*startButtonAdminLine2)
adminKeyboard.add(*startButtonAdminLine3)
adminKeyboard.add(*startButtonAdminLine4)
adminKeyboard.add(startButtonAdminLine5)

generateCodeKeyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
generateCodeKeyboard.add(*generateCodeButton)

cancelkeyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
cancelkeyboard.add(cancelButton)


def chooseStartkeyboard(userID):
    userIndex = FindUser(userID)
    if Users[userIndex].role == "Admin":
        return adminKeyboard
    else:
        return startKeyboard


def TelegramModule():
    asyncio.set_event_loop(loop=teleloop)
    executor.start_polling(dp, skip_updates=True)


@dp.message_handler(commands=['start'])
async def start_handler(message: types.Message):
    userID = message.from_user.id
    ak = adminKeyboard
    if FindUser(userID) != 'null':
        if Users[FindUser(userID)].role == "Admin":
            await message.answer(f"Добро пожаловать обратно! \n"
                                 f"Чем я могу вам помочь?", reply_markup=ak)
        else:
            await message.answer(f"Добро пожаловать обратно! \n"
                                 f"Чем я могу вам помочь?", reply_markup=startKeyboard)
    else:

        NewUser = User(userID)
        NewUser.to_json()
        Users.append(NewUser)
        await message.answer(f"Приветствую! Вижу вы здесь впервые,\n"
                             f"давайте объясню как тут всё работает.\n"
                             f"Вы вводите запрос на Авито (не забудьте поставить сортировку по дате!) и присылаете мне ссылку, "
                             f"а я, в свою очередь, буду оповещать вас о новых товарах, "
                             f"которые появились по этой ссылке.\n"
                             f"Всё просто :)\n"
                             f"Также вы можете отменить любую операцию введя /cancel")
        await message.answer("Сейчас ваш аккаунт запущен в демонстрационном режиме.\n"
                             "В нём у вас есть возможность парсить лишь одну ссылку,\n"
                             "а срок действия аккаунта ограничен 1 неделей")
        await message.answer("Для улучшения аккаунта вы можете ввести код, полученный от администратора",
                             reply_markup=startKeyboard)


@dp.message_handler(commands='cancel', state='*')
async def cmd_cancel(message: types.Message, state: FSMContext):
    userID = message.from_user.id
    await state.finish()
    await message.answer("Операция отменена", reply_markup=chooseStartkeyboard(userID))


@dp.message_handler(lambda message: message.text == "Отмена", state='*')
async def msg_cancel(message: types.Message, state: FSMContext):
    userID = message.from_user.id
    await state.finish()
    await message.answer("Операция отменена", reply_markup=chooseStartkeyboard(userID))


######################Account Info#########################

@dp.message_handler(lambda message: message.text == "Статус аккаунта")
async def acc_info(message: types.Message):
    userID = message.from_user.id
    userIndex = FindUser(userID)
    links = ""
    for i in range(len(Users[userIndex].links)):
        links += (f"{Users[userIndex].linksNames[i]}\n"
                  f"{Users[userIndex].links[i]}\n\n")
    match Users[userIndex].role:
        case "User": linklm = 1
        case "SuperUser": linklm = 10
        case "Admin": linklm = 9999
        case other: linklm = -1

    await message.answer(f"Статус аккаунта:\n"
                         f" ID: {Users[userIndex].ID}"
                         f" Роль: {Users[userIndex].role}\n"
                         f" Лимит ссылок: {linklm}\n"
                         f" Свободных слотов для ссылок: {Users[userIndex].linkLimit}\n"
                         f" Ссылок в работе: {len(Users[userIndex].links)}\n\n"
                         f" {links}")


######################New Link#############################

class AddLink(StatesGroup):
    waiting_for_link = State()
    waiting_for_name = State()


@dp.message_handler(lambda message: message.text == "Добавить ссылку")
async def link_start(message: types.Message, state: FSMContext):
    userID = message.from_user.id
    userIndex = FindUser(userID)
    if Users[userIndex].linkLimit > 0:
        await message.answer("Введите ссылку", reply_markup=cancelkeyboard)
        await state.set_state(AddLink.waiting_for_link.state)
    else:
        await message.answer("Вы исчерпали лимит ссылок", reply_markup=chooseStartkeyboard(userID))
        return


@dp.message_handler(state=AddLink.waiting_for_link)
async def link_name(message: types.Message, state: FSMContext):
    if (("https://www.avito.ru/" not in message.text) and
            ("https://avito.ru/" not in message.text) and
            ("https://m.avito.ru/" not in message.text)):
        await message.answer("Это не ссылка на Авито\nВведите корректную ссылку", reply_markup=cancelkeyboard)
        return

    userID = message.from_user.id
    index = FindUser(userID)
    for link in Users[index].links:
        if link == message.text:
            await message.answer("Данная ссылка уже добавлена", reply_markup=cancelkeyboard)
            return

    await state.update_data(newLink=message.text)
    await state.set_state(AddLink.waiting_for_name.state)
    await message.answer("Выберите название для ссылки\n(Оно будет использоваться в уведомлениях)", reply_markup=cancelkeyboard)


@dp.message_handler(state=AddLink.waiting_for_name)
async def link_final(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    linkData = await state.get_data()
    userID = message.from_user.id
    index = FindUser(userID)

    for link in Users[index].linksNames:
        if link == message.text:
            await message.answer("Данное название уже используется", reply_markup=cancelkeyboard)
            return

    Users[index].links.append(linkData['newLink'])
    Users[index].linksNames.append(linkData['name'])
    Users[index].lastParse.append([])

    with open('users.json', 'r') as f:
        data = json.load(f)
    data["Users"][index]["links"].append(linkData['newLink'])
    data["Users"][index]["linksName"].append(linkData['name'])
    data["Users"][index]["lastParse"].append([])
    data["Users"][index]["linkLimit"] -= 1
    with open('users.json', 'w') as f:
        json.dump(data, f)
    await message.answer("Ссылка добавлена", reply_markup=chooseStartkeyboard(userID))
    Users[index].linkLimit -= 1
    await state.finish()


######################Delete Link##########################

class RemoveLink(StatesGroup):
    choose_link = State()


@dp.message_handler(lambda message: message.text == "Удалить ссылку")
async def remove_link(message: types.Message, state: FSMContext):
    userID = message.from_user.id
    keyboard = types.InlineKeyboardMarkup()
    index = FindUser(userID)
    await state.update_data(id=index)
    if len(Users[index].links) == 0:
        await message.answer("На данный момент у вас нет ссылок", reply_markup=chooseStartkeyboard(userID))
        return
    else:
        for i in range(len(Users[index].links)):
            keyboard.add(types.InlineKeyboardButton(text=f"{Users[index].linksNames[i]}", callback_data=f"{i}"))
        await state.set_state(RemoveLink.choose_link.state)
        await message.answer("Какую ссылку удалить?(используйте /cancel для отмены)\n", reply_markup=keyboard)


@dp.callback_query_handler(state=RemoveLink.choose_link)
async def delete_link(call: types.CallbackQuery, state: FSMContext):
    userID = call.from_user.id
    data = await state.get_data()
    index = data['id']
    Users[index].links.remove(Users[index].links[int(call.data)])
    Users[index].linksNames.remove(Users[index].linksNames[int(call.data)])
    Users[index].lastParse.remove(Users[index].lastParse[int(call.data)])
    with open('users.json', 'r') as f:
        data = json.load(f)
    data["Users"][index]["links"].remove(data["Users"][index]["links"][int(call.data)])
    data["Users"][index]["linksName"].remove(data["Users"][index]["linksName"][int(call.data)])
    data["Users"][index]["lastParse"].remove(data["Users"][index]["lastParse"][int(call.data)])
    data["Users"][index]["linkLimit"] += 1
    with open('users.json', 'w') as f:
        json.dump(data, f)
    await state.finish()
    await call.answer()
    Users[index].linkLimit += 1
    await call.message.answer("Ссылка удалена", reply_markup=chooseStartkeyboard(userID))


#######################Account Upgrade#####################

class AccUpg(StatesGroup):
    code = State()


@dp.message_handler(lambda message: message.text == "Ввести код")
async def upgrade(message: types.Message, state: FSMContext):
    await message.answer("Введите код, полученный от администратора", reply_markup=cancelkeyboard)
    await state.set_state(AccUpg.code.state)


@dp.message_handler(state=AccUpg.code)
async def confirm(message: types.Message, state: FSMContext):
    userID = message.from_user.id
    index = FindUser(userID)
    super = False
    admin = False

    with open('users.json', 'r') as f:
        data = json.load(f)
    for code in range(len(data["SuperKeys"])):
        if message.text == data["SuperKeys"][code]:
            super = True
            keyid = code
    for code in range(len(data["AdminKeys"])):
        if message.text == data["AdminKeys"][code]:
            admin = True
            keyid = code
    if admin:
        Users[index].role = "Admin"
        data["Users"][index]["role"] = "Admin"
        data["AdminKeys"].remove(data["AdminKeys"][keyid])
        priv = "Администратора"
        Users[index].linkLimit = -1
        data["Users"][index]["linkLimit"] = 1000
        Users[index].lifetime = 999999999
        data["Users"][index]["lifetime"] = 999999999
    elif super:
        Users[index].role = "SuperUser"
        data["Users"][index]["role"] = "SuperUser"
        data["SuperKeys"].remove(data["SuperKeys"][keyid])
        priv = "Супер пользователя"
        Users[index].linkLimit = 10
        data["Users"][index]["linkLimit"] = 10
        Users[index].lifetime = 999999999
        data["Users"][index]["lifetime"] = 999999999
    else:
        await message.answer("Неверный код", reply_markup=cancelkeyboard)
        return
    with open('users.json', 'w') as f:
        json.dump(data, f)
    await message.answer(f"Ваш аккаун был улучшен до {priv}!", reply_markup=chooseStartkeyboard(userID))
    await state.finish()


########################Add Proxy##########################

class NewProxy(StatesGroup):
    proxy_await = State()


@dp.message_handler(lambda message: message.text == "Добавить прокси")
async def proxy_add(message: types.Message, state: FSMContext):
    userID = message.from_user.id
    userRole = Users[FindUser(userID)].role
    if userRole != "Admin":
        await message.answer("Отказано в доступе", reply_markup=startKeyboard)
        return
    else:
        await message.answer("Введите прокси в следующем формате:\n"
                             "<Протокол>://<Имя пользователя>:<Пароль>@<IP>:<Порт>", reply_markup=cancelkeyboard)
        await state.set_state(NewProxy.proxy_await.state)


@dp.message_handler(state=NewProxy.proxy_await)
async def proxy_check(message: types.Message, state: FSMContext):
    proxyopt={
        'proxy': {
            'http': f'{message.text}',
            'https': f'{message.text}',
        },
    }
    opt = Options()
    opt.add_argument("--headless=new")
    drive = webdriver.Edge(seleniumwire_options=proxyopt, options=opt)
    try:
        drive.get('https://www.google.com/')
        proxyList.append(message.text)
        proxyList.append(message.text)
        await message.answer("Прокси добавлены", reply_markup=adminKeyboard)
    except Exception as e:
        print(e)
        await message.answer("Произошла ошибка\nПрокси не добавелны", reply_markup=cancelkeyboard)

    with open('users.json', 'r') as f:
        data = json.load(f)
    data["Proxies"].append(message.text)
    with open('users.json', 'w') as f:
        json.dump(data, f)
    await state.finish()

#########################Delete Proxy######################

class DeleteProxy(StatesGroup):
    choose_proxy = State()


@dp.message_handler(lambda message: message.text == "Удалить прокси")
async def delete_proxy(message: types.Message, state: FSMContext):
    userID = message.from_user.id
    userIndex = FindUser(userID)
    if Users[userIndex].role != "Admin":
        await message.answer("Отказано в доступе", reply_markup=startKeyboard)
        return
    else:
        chooseKeyboard = types.InlineKeyboardMarkup()
        for i in range(len(proxyList)):
            chooseKeyboard.add(types.InlineKeyboardButton(text=f"{proxyList[i]}", callback_data=f"{i}"))
        await message.answer("Какие прокси удалить?\n(используйте /cancel для отмены)", reply_markup=chooseKeyboard)
        await state.set_state(DeleteProxy.choose_proxy.state)


@dp.callback_query_handler(state=DeleteProxy.choose_proxy)
async def delete_link(call: types.CallbackQuery, state: FSMContext):
    proxyList.remove(proxyList[int(call.data)])
    with open('users.json', 'r') as f:
        data = json.load(f)
    data["Proxies"].remove(data["Proxies"][int(call.data)])
    with open('users.json', 'w') as f:
        json.dump(data, f)
    await call.answer()
    await call.message.answer("Прокси удалены", reply_markup=adminKeyboard)
    await state.finish()



#########################Generate Code#####################

class CodeGen(StatesGroup):
    choose_role = State()


@dp.message_handler(lambda message: message.text == "Сгенерировать код")
async def generate_code(message: types.Message, state: FSMContext):
    userID = message.from_user.id
    userIndex = FindUser(userID)
    if Users[userIndex].role != "Admin":
        await message.answer("Недостаточно прав для выполнения операции", reply_markup=startKeyboard)
        return
    else:
        await message.answer("Для какой роли сгенерировать код?\n(используйте /cancel для отмены)", reply_markup=generateCodeKeyboard)
        await state.set_state(CodeGen.choose_role.state)


@dp.message_handler(state=CodeGen.choose_role)
async def role_choosen(message: types.Message, state: FSMContext):
    if message.text == "Суперпользователь":
        key = newkey("SuperUser")
        await message.answer("Код сгенерирован. Передайте его пользователю\n"
                             f"{key}", reply_markup=adminKeyboard)
        await state.finish()
    elif message.text == "Администратор":
        key = newkey("Admin")
        await message.answer("Код сгенерирован. Передайте его пользователю\n"
                             f"{key}", reply_markup=adminKeyboard)
        await state.finish()
    else:
        await message.answer("Некоректная роль", reply_markup=generateCodeKeyboard)
        return


#####################System Status#########################

@dp.message_handler(lambda message: message.text == "Статус системы")
async def system_status(message: types.Message):
    userID = message.from_user.id
    userIndex = FindUser(userID)
    if Users[userIndex].role != "Admin":
        await message.answer("Отказано в доступе", reply_markup=startKeyboard)
        return
    else:
        linkCount = 0
        for user in Users:
            for link in user.links:
                linkCount += 1
        goodprox = ""
        bad = ""

        for proxy in proxyList:
            goodprox += f'{proxy}\n\n'

        for bp in badProxy:
            bad += f'{bp}\n\n'

        await message.answer(f"Всего пользователей: {len(Users)}\n"
                             f"Всего ссылок: {linkCount}\n"
                             f"Рабочих прокси: {len(proxyList)}\n"
                             f"{goodprox}\n"
                             f"Нерабочих прокси: {len(badProxy)}\n"
                             f"{bad}\n"
                             f"Интервал парсинга: {T} сек\n"
                             f"Время отдыха нерабочих прокси: {C} сек", reply_markup=adminKeyboard)


########################Set Parsing########################
class SetInteval(StatesGroup):
    interval = State()


@dp.message_handler(lambda message: message.text == "Задать интервал парсинга")
async def set_parsing(message: types.Message, state: FSMContext):
    userID = message.from_user.id
    userIndex = FindUser(userID)
    if Users[userIndex].role != "Admin":
        await message.answer("Отказано в доступе", reply_markup=startKeyboard)
        return
    else:
        await message.answer("Введите интервал в секундах", reply_markup=cancelkeyboard)
        await state.set_state(SetInteval.interval.state)


@dp.message_handler(state=SetInteval.interval)
async def set_inteval(message: types.Message, state: FSMContext):
    try:
        global T
        interval = float(message.text)
        T = interval
        await message.answer("Интервал установлен", reply_markup=adminKeyboard)
        await state.finish()
    except Exception as e:
        await message.answer("Интервал не установлен", reply_markup=cancelkeyboard)
        return


########################Set badproxy#######################

class SetBadInterval(StatesGroup):
    interval = State()


@dp.message_handler(lambda message: message.text == "Задать интервал отдыха")
async def set_cooldown(message: types.Message, state: FSMContext):
    userID = message.from_user.id
    userIndex = FindUser(userID)
    if Users[userIndex].role != "Admin":
        await message.answer("Отказано в доступе", reply_markup=startKeyboard)
        return
    else:
        await message.answer("Введите интервал в секундах", reply_markup=cancelkeyboard)
        await state.set_state(SetBadInterval.interval.state)


@dp.message_handler(state=SetBadInterval.interval)
async def set_bad_inteval(message: types.Message, state: FSMContext):
    try:
        global C
        interval = float(message.text)
        C = interval
        await message.answer("Интервал установлен", reply_markup=adminKeyboard)
        await state.finish()
    except Exception as e:
        await message.answer("Интервал не установлен", reply_markup=cancelkeyboard)
        return


######################Add linklimit########################

class AddLinkLimit(StatesGroup):
    userID = State()
    linkNumber = State()


@dp.message_handler(lambda message: message.text == "Увеличить лимит ссылок")
async def add_linklimit(message: types.Message, state: FSMContext):
    userID = message.from_user.id
    userIndex = FindUser(userID)
    if Users[userIndex].role != "Admin":
        await message.answer("Отказано в доступе", reply_markup=startKeyboard)
        return
    else:
        await message.answer("Введите ID пользователя", reply_markup=cancelkeyboard)
        await state.set_state(AddLinkLimit.userID.state)

@dp.message_handler(state=AddLinkLimit.userID)
async def linklimit_user(message: types.Message, state: FSMContext):
    try:
        userIndex = FindUser(message.text)
        await state.update_data(index=userIndex)
        await message.answer("Сколько слотов добавить?", reply_markup=cancelkeyboard)
        await state.set_state(AddLinkLimit.linkNumber.state)
    except Exception as e:
        await message.answer("Пользователь не найден", reply_markup=cancelkeyboard)


@dp.message_handler(state=AddLinkLimit.linkNumber)
async def linklimit_finale(message: types.Message, state: FSMContext):
    data =  await state.get_data()
    userIndex = data['id']
    try:
        Users[userIndex].linkLimit += int(message.text)
        await message.answer("Лимит пользователя был увеличен", reply_markup=adminKeyboard)
    except Exception as e:
        await message.answer("Ошибка", reply_markup=cancelkeyboard)
        return




######################Emergency Exit#######################
@dp.message_handler(lambda message: message.text == "Экстренная остановка")
async def emergency_stop(message: types.Message):
    userID = message.from_user.id
    userIndex = FindUser(userID)
    if Users[userIndex].role != "Admin":
        await message.answer("Отказано в доступе", reply_markup=startKeyboard)
    else:
        sys.exit(1)

########################################################################################################################
########################################################Parsing Module##################################################
########################################################################################################################
proxyNumber = 0

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


with open('users.json', 'r') as f:
    data = json.load(f)
    for proxy in data["Proxies"]:
        proxyList.append(proxy)


T = 30.0
C = 1200.0


def main_parsing():
    t = 30.0
    timer = 0
    while True:
        if time.time() - timer >= t:
            t = random.uniform(T-5, T+5)
            print(f"t = {t}")
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
                            new = Link(user.links[link], [], [])
                            new.users.append(user.ID)
                            new.usersLinkID.append(link)
                            linkPool.append(new)
                else:
                    print("Out of time")

            delay = t/len(linkPool)
            timer = time.time()
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
    try:
        try:
            if len(proxyList) == 0:
                print("out of proxies")
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
                print("Bad proxy")
                badProxy.append(proxyList[proxyNumber])
                proxyList.remove(proxyList[proxyNumber])
                return

        except Exception as e:
            print("Proxy Error!")
            badProxy.append(proxyList[proxyNumber])
            proxyList.remove(proxyList[0])
            return

        soup = BeautifulSoup(drive.page_source, "html.parser")
        items = soup.find_all('div', {'data-marker': 'item'})
        links = []
        for item in items:
            links.append(item.find('a').get('href'))

        lastItem = 40

        for link in range(len(links)):
            if links[link] in Users[FindUser(linkfrompool.users[0])].lastParse[linkfrompool.id]:
                lastItem = link
                break

        print(lastItem)
        print(Users[FindUser(linkfrompool.users[0])].lastParse[linkfrompool.id])

        if Users[FindUser(linkfrompool.users[0])].lastParse[linkfrompool.id] != []:
            for i in range(lastItem):
                fulllink = "https://www.avito.ru" + links[i]
                price = items[i].find('meta', {'itemprop': 'price'}).get('content')
                title = items[i].find('a').get('title')[11:len(items[i].find('a').get('title'))-13]

                for user in range(len(linkfrompool.users)):
                    message = (f"Новое объявление по запросу {Users[FindUser(linkfrompool.users[user])].linksNames[linkfrompool.usersLinkID[user]]}\n\n"
                               f"{title}\n\n"
                               f"Цена: {price} руб\n\n"
                               f" {fulllink}")
                    asyncio.run_coroutine_threadsafe(bot.send_message(chat_id=Users[FindUser(linkfrompool.users[user])].ID, text=message), teleloop)
                    Users[FindUser(linkfrompool.users[user])].lastParse[linkfrompool.usersLinkID[linkfrompool.usersLinkID[user]]] = links

    except Exception as e:
        print("Removal Error")


t1 = Thread(target=TelegramModule)
# t1.start()
t2 = Thread(target=main_parsing)
t2.start()
# t1.join()
t2.join()
