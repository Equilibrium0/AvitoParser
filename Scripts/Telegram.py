from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup

from selenium import webdriver
from selenium.webdriver.edge.options import Options
from seleniumwire import webdriver

import asyncio
import json
import logging

from Classes import Users, User, FindUser, newkey, proxyList, badProxy, set_T, set_C, T, C

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

file_handler = logging.FileHandler('BotLogs.txt')
file_handler.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s %(name)s %(levelname)s  %(message)s')
file_handler.setFormatter(formatter)

logger.addHandler(file_handler)

TOKEN = "6776153287:AAF-Xo-O7gRLDNWTI0ArI08rjlOuINbBqVM"
bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot=bot, storage=storage)
teleloop = asyncio.new_event_loop()

####################Buttons################################

startButtonLine1 = ["Добавить ссылку", "Удалить ссылку"]
startButtonLine2 = ["Ввести код", "Статус аккаунта"]
startButtonAdminLine2 = ["Добавить прокси", "Удалить прокси"]
startButtonAdminLine3 = ["Задать интервал парсинга", "Задать интервал отдыха", "Логи"]
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
    logger.info(f"MESSAGE USER: {userID}, COMMAND: Start")
    if FindUser(userID) != 'null':
        if Users[FindUser(userID)].role == "Admin":
            await message.answer(f"Добро пожаловать обратно! \n"
                                 f"Чем я могу вам помочь?", reply_markup=adminKeyboard)
            logger.info(f"ANSWER USER: {userID}, COMMAND: Start, NEW: Old User, ROLE: Admin")
        else:
            await message.answer(f"Добро пожаловать обратно! \n"
                                 f"Чем я могу вам помочь?", reply_markup=startKeyboard)
            logger.info(f"ANSWER USER: {userID}, COMMAND: Start, NEW: Old User, ROLE: User")
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
        logger.info(f"ANSWER USER: {userID}, COMMAND: Start, NEW: New User, ROLE: User")


@dp.message_handler(commands='cancel', state='*')
async def cmd_cancel(message: types.Message, state: FSMContext):
    userID = message.from_user.id
    await state.finish()
    await message.answer("Операция отменена", reply_markup=chooseStartkeyboard(userID))
    logger.info(f"MESSAGE USER: {userID}, COMMAND: Cancel")


@dp.message_handler(lambda message: message.text == "Отмена", state='*')
async def msg_cancel(message: types.Message, state: FSMContext):
    userID = message.from_user.id
    await state.finish()
    await message.answer("Операция отменена", reply_markup=chooseStartkeyboard(userID))
    logger.info(f"MESSAGE USER: {userID}, COMMAND: Cancel")


######################Account Info#########################

@dp.message_handler(lambda message: message.text == "Статус аккаунта")
async def acc_info(message: types.Message):
    userID = message.from_user.id
    userIndex = FindUser(userID)
    logger.info(f"MESSAGE USER: {userID}, COMMAND: ACCOUT STATUS")
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
                         f" ID: {Users[userIndex].ID}\n"
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
    logger.info(f"MESSAGE USER: {userID}, ROLE: {Users[userIndex].role}, COMMAND: New Link, STAGE: 1")
    if Users[userIndex].linkLimit > 0:
        await message.answer("Введите ссылку", reply_markup=cancelkeyboard)
        await state.set_state(AddLink.waiting_for_link.state)
        logger.info(f"ANSWER USER: {userID}, ROLE: {Users[userIndex].role}, COMMAND: New Link, STAGE: 1, CONTENT: Await link")
    else:
        await message.answer("Вы исчерпали лимит ссылок", reply_markup=chooseStartkeyboard(userID))
        logger.info(f"ANSWER USER: {userID}, ROLE: {Users[userIndex].role}, COMMAND: New Link, STAGE: 1, CONTENT: Out of links")
        return


@dp.message_handler(state=AddLink.waiting_for_link)
async def link_name(message: types.Message, state: FSMContext):
    userID = message.from_user.id
    index = FindUser(userID)
    logger.info(f"MESSAGE USER: {userID}, ROLE: {Users[index].role}, COMMAND: New Link, STAGE: 2")

    if (("https://www.avito.ru/" not in message.text) and
            ("https://avito.ru/" not in message.text) and
            ("https://m.avito.ru/" not in message.text)):
        await message.answer("Это не ссылка на Авито\nВведите корректную ссылку", reply_markup=cancelkeyboard)
        logger.info(f"ANSWER USER: {userID}, ROLE: {Users[index].role}, COMMAND: New Link, STAGE: 2, CONTENT: Bad link")

        return


    for link in Users[index].links:
        if link == message.text:
            await message.answer("Данная ссылка уже добавлена", reply_markup=cancelkeyboard)
            logger.info(f"ANSWER USER: {userID}, ROLE: {Users[index].role}, COMMAND: New Link, STAGE: 2, CONTENT: Link Exist")
            return

    await state.update_data(newLink=message.text)
    await state.set_state(AddLink.waiting_for_name.state)
    await message.answer("Выберите название для ссылки\n(Оно будет использоваться в уведомлениях)", reply_markup=cancelkeyboard)
    logger.info(f"ANSWER USER: {userID}, ROLE: {Users[index].role}, COMMAND: New Link, STAGE: 2, CONTENT: Await name")


@dp.message_handler(state=AddLink.waiting_for_name)
async def link_final(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    linkData = await state.get_data()
    userID = message.from_user.id
    index = FindUser(userID)
    logger.info(f"MESSAGE USER: {userID}, ROLE: {Users[index].role}, COMMAND: New Link, STAGE: 3")

    for link in Users[index].linksNames:
        if link == message.text:
            await message.answer("Данное название уже используется", reply_markup=cancelkeyboard)
            logger.info(f"ANSWER USER: {userID}, ROLE: {Users[index].role}, COMMAND: New Link, STAGE: 3, CONTENT: Name Exist")
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
    logger.info(f"ANSWER USER: {userID}, ROLE: {Users[index].role}, COMMAND: New Link, STAGE: 3, CONTENT: Link Added")


######################Delete Link##########################

class RemoveLink(StatesGroup):
    choose_link = State()


@dp.message_handler(lambda message: message.text == "Удалить ссылку")
async def remove_link(message: types.Message, state: FSMContext):
    userID = message.from_user.id
    keyboard = types.InlineKeyboardMarkup()
    index = FindUser(userID)
    logger.info(f"MESSAGE USER: {userID}, ROLE: {Users[index].role}, COMMAND: Delete Link, STAGE: 1")
    await state.update_data(id=index)
    if len(Users[index].links) == 0:
        await message.answer("На данный момент у вас нет ссылок", reply_markup=chooseStartkeyboard(userID))
        logger.info(
            f"ANSWER USER: {userID}, ROLE: {Users[index].role}, COMMAND: Delete Link, STAGE: 1, CONTENT: No Links")
        return
    else:
        for i in range(len(Users[index].links)):
            keyboard.add(types.InlineKeyboardButton(text=f"{Users[index].linksNames[i]}", callback_data=f"{i}"))
        await state.set_state(RemoveLink.choose_link.state)
        await message.answer("Какую ссылку удалить?(используйте /cancel для отмены)\n", reply_markup=keyboard)
        logger.info(
            f"ANSWER USER: {userID}, ROLE: {Users[index].role}, COMMAND: Delete Link, STAGE: 1, CONTENT: Await Link Index")


@dp.callback_query_handler(state=RemoveLink.choose_link)
async def delete_link(call: types.CallbackQuery, state: FSMContext):
    userID = call.from_user.id
    data = await state.get_data()
    index = data['id']

    logger.info(f"MESSAGE USER: {userID}, ROLE: {Users[index].role}, COMMAND: Delete Link, STAGE: 2")

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
    logger.info(
        f"ANSWER USER: {userID}, ROLE: {Users[index].role}, COMMAND: Delete Link, STAGE: 2, CONTENT: Link Deleted")

#######################Account Upgrade#####################

class AccUpg(StatesGroup):
    code = State()


@dp.message_handler(lambda message: message.text == "Ввести код")
async def upgrade(message: types.Message, state: FSMContext):
    userID = message.from_user.id
    index = FindUser(userID)
    logger.info(f"MESSAGE USER: {userID}, ROLE: {Users[index].role}, COMMAND: Acc Upgrade, STAGE: 1")
    await message.answer("Введите код, полученный от администратора", reply_markup=cancelkeyboard)
    await state.set_state(AccUpg.code.state)
    logger.info(
        f"ANSWER USER: {userID}, ROLE: {Users[index].role}, COMMAND: Acc Upgrade, STAGE: 1, CONTENT: Await Code")


@dp.message_handler(state=AccUpg.code)
async def confirm(message: types.Message, state: FSMContext):
    userID = message.from_user.id
    index = FindUser(userID)

    logger.info(f"MESSAGE USER: {userID}, ROLE: {Users[index].role}, COMMAND: Acc Upgrade, STAGE: 2")

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
        logger.info(
            f"ANSWER USER: {userID}, ROLE: {Users[index].role}, COMMAND: Acc Upgrade, STAGE: 2, CONTENT: Up To Admin")
    elif super:
        Users[index].role = "SuperUser"
        data["Users"][index]["role"] = "SuperUser"
        data["SuperKeys"].remove(data["SuperKeys"][keyid])
        priv = "Супер пользователя"
        Users[index].linkLimit = 10
        data["Users"][index]["linkLimit"] = 10
        Users[index].lifetime = 999999999
        data["Users"][index]["lifetime"] = 999999999
        logger.info(
            f"ANSWER USER: {userID}, ROLE: {Users[index].role}, COMMAND: Acc Upgrade, STAGE: 2, CONTENT: Up To Super")
    else:
        await message.answer("Неверный код", reply_markup=cancelkeyboard)
        logger.info(
            f"ANSWER USER: {userID}, ROLE: {Users[index].role}, COMMAND: Acc Upgrade, STAGE: 2, CONTENT: Invalid Code")
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
    index = FindUser(userID)
    userRole = Users[FindUser(userID)].role

    logger.info(f"MESSAGE USER: {userID}, ROLE: {Users[index].role}, COMMAND: Add Proxy, STAGE: 1")

    if userRole != "Admin":
        await message.answer("Отказано в доступе", reply_markup=startKeyboard)
        logger.info(
            f"ANSWER USER: {userID}, ROLE: {Users[index].role}, COMMAND: Add Proxy, STAGE: 1, CONTENT: Access Denied")
        return
    else:
        await message.answer("Введите прокси в следующем формате:\n"
                             "<Протокол>://<Имя пользователя>:<Пароль>@<IP>:<Порт>", reply_markup=cancelkeyboard)
        await state.set_state(NewProxy.proxy_await.state)
        logger.info(
            f"ANSWER USER: {userID}, ROLE: {Users[index].role}, COMMAND: Add Proxy, STAGE: 1, CONTENT: Await Proxy")


@dp.message_handler(state=NewProxy.proxy_await)
async def proxy_check(message: types.Message, state: FSMContext):
    userID = message.from_user.id
    index = FindUser(userID)

    logger.info(f"MESSAGE USER: {userID}, ROLE: {Users[index].role}, COMMAND: Add Proxy, STAGE: 2")

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
        logger.info(
            f"ANSWER USER: {userID}, ROLE: {Users[index].role}, COMMAND: Add Proxy, STAGE: 2, CONTENT: Proxy Added")
    except Exception as e:
        print(e)
        await message.answer("Произошла ошибка\nПрокси не добавелны", reply_markup=cancelkeyboard)
        logger.info(
            f"ANSWER USER: {userID}, ROLE: {Users[index].role}, COMMAND: Add Proxy, STAGE: 2, CONTENT: Proxy Not Added")

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

    logger.info(f"MESSAGE USER: {userID}, ROLE: {Users[userIndex].role}, COMMAND: Delete Proxy, STAGE: 1")

    if Users[userIndex].role != "Admin":
        await message.answer("Отказано в доступе", reply_markup=startKeyboard)
        logger.info(
            f"ANSWER USER: {userID}, ROLE: {Users[userIndex].role}, COMMAND: Delete Proxy, STAGE: 1, CONTENT: Access Denied")
        return
    else:
        chooseKeyboard = types.InlineKeyboardMarkup()
        for i in range(len(proxyList)):
            chooseKeyboard.add(types.InlineKeyboardButton(text=f"{proxyList[i]}", callback_data=f"{i}"))
        await message.answer("Какие прокси удалить?\n(используйте /cancel для отмены)", reply_markup=chooseKeyboard)
        await state.set_state(DeleteProxy.choose_proxy.state)
        logger.info(
            f"ANSWER USER: {userID}, ROLE: {Users[userIndex].role}, COMMAND: Delete Proxy, STAGE: 1, CONTENT: Await Proxy Index")


@dp.callback_query_handler(state=DeleteProxy.choose_proxy)
async def delete_link(call: types.CallbackQuery, state: FSMContext):
    userID = call.from_user.id
    userIndex = FindUser(userID)

    logger.info(f"MESSAGE USER: {userID}, ROLE: {Users[userIndex].role}, COMMAND: Delete Proxy, STAGE: 2")

    proxyList.remove(proxyList[int(call.data)])
    with open('users.json', 'r') as f:
        data = json.load(f)
    data["Proxies"].remove(data["Proxies"][int(call.data)])
    with open('users.json', 'w') as f:
        json.dump(data, f)
    await call.answer()
    await call.message.answer("Прокси удалены", reply_markup=adminKeyboard)
    await state.finish()
    logger.info(
        f"ANSWER USER: {userID}, ROLE: {Users[userIndex].role}, COMMAND: Delete Proxy, STAGE: 2, CONTENT: Proxy Deleted")



#########################Generate Code#####################

class CodeGen(StatesGroup):
    choose_role = State()


@dp.message_handler(lambda message: message.text == "Сгенерировать код")
async def generate_code(message: types.Message, state: FSMContext):
    userID = message.from_user.id
    userIndex = FindUser(userID)

    logger.info(f"MESSAGE USER: {userID}, ROLE: {Users[userIndex].role}, COMMAND: Generate Code, STAGE: 1")

    if Users[userIndex].role != "Admin":
        await message.answer("Недостаточно прав для выполнения операции", reply_markup=startKeyboard)
        logger.info(
            f"ANSWER USER: {userID}, ROLE: {Users[userIndex].role}, COMMAND: Generate Code, STAGE: 1, CONTENT: Access Denied")
        return
    else:
        await message.answer("Для какой роли сгенерировать код?\n(используйте /cancel для отмены)", reply_markup=generateCodeKeyboard)
        await state.set_state(CodeGen.choose_role.state)
        logger.info(
            f"ANSWER USER: {userID}, ROLE: {Users[userIndex].role}, COMMAND: Generate Code, STAGE: 1, CONTENT: Await Role")


@dp.message_handler(state=CodeGen.choose_role)
async def role_choosen(message: types.Message, state: FSMContext):
    userID = message.from_user.id
    userIndex = FindUser(userID)

    logger.info(f"MESSAGE USER: {userID}, ROLE: {Users[userIndex].role}, COMMAND: Generate Code, STAGE: 2")

    if message.text == "Суперпользователь":
        key = newkey("SuperUser")
        await message.answer("Код сгенерирован. Передайте его пользователю\n"
                             f"{key}", reply_markup=adminKeyboard)
        await state.finish()
        logger.info(
            f"ANSWER USER: {userID}, ROLE: {Users[userIndex].role}, COMMAND: Generate Code, STAGE: 2, CONTENT: Super Generated")
    elif message.text == "Администратор":
        key = newkey("Admin")
        await message.answer("Код сгенерирован. Передайте его пользователю\n"
                             f"{key}", reply_markup=adminKeyboard)
        await state.finish()
        logger.info(
            f"ANSWER USER: {userID}, ROLE: {Users[userIndex].role}, COMMAND: Generate Code, STAGE: 2, CONTENT: Admin Generated")
    else:
        await message.answer("Некоректная роль", reply_markup=generateCodeKeyboard)
        logger.info(
            f"ANSWER USER: {userID}, ROLE: {Users[userIndex].role}, COMMAND: Generate Code, STAGE: 2, CONTENT: Invalid Role")
        return


#####################System Status#########################

@dp.message_handler(lambda message: message.text == "Статус системы")
async def system_status(message: types.Message):
    userID = message.from_user.id
    userIndex = FindUser(userID)

    logger.info(f"MESSAGE USER: {userID}, ROLE: {Users[userIndex].role}, COMMAND: System Status, STAGE: 1")

    if Users[userIndex].role != "Admin":
        await message.answer("Отказано в доступе", reply_markup=startKeyboard)
        logger.info(
            f"ANSWER USER: {userID}, ROLE: {Users[userIndex].role}, COMMAND: System Status, STAGE: 1, CONTENT: Access Denied")
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
        logger.info(
            f"ANSWER USER: {userID}, ROLE: {Users[userIndex].role}, COMMAND: System Status, STAGE: 1, CONTENT: Status Shown")


########################Set Parsing########################
class SetInteval(StatesGroup):
    interval = State()


@dp.message_handler(lambda message: message.text == "Задать интервал парсинга")
async def set_parsing(message: types.Message, state: FSMContext):
    userID = message.from_user.id
    userIndex = FindUser(userID)

    logger.info(f"MESSAGE USER: {userID}, ROLE: {Users[userIndex].role}, COMMAND: Set Parsing, STAGE: 1")

    if Users[userIndex].role != "Admin":
        await message.answer("Отказано в доступе", reply_markup=startKeyboard)
        logger.info(
            f"ANSWER USER: {userID}, ROLE: {Users[userIndex].role}, COMMAND: Set Parsing, STAGE: 1, CONTENT: Access Denied")
        return
    else:
        await message.answer("Введите интервал в секундах", reply_markup=cancelkeyboard)
        await state.set_state(SetInteval.interval.state)
        logger.info(
            f"ANSWER USER: {userID}, ROLE: {Users[userIndex].role}, COMMAND: Set Parsing, STAGE: 1, CONTENT: Await interval")


@dp.message_handler(state=SetInteval.interval)
async def set_inteval(message: types.Message, state: FSMContext):
    userID = message.from_user.id
    userIndex = FindUser(userID)

    logger.info(f"MESSAGE USER: {userID}, ROLE: {Users[userIndex].role}, COMMAND: Set Parsing, STAGE: 2")

    try:
        interval = float(message.text)
        set_T(interval)
        await message.answer("Интервал установлен", reply_markup=adminKeyboard)
        await state.finish()
        logger.info(
            f"ANSWER USER: {userID}, ROLE: {Users[userIndex].role}, COMMAND: Set Parsing, STAGE: 2, CONTENT: Interval Setted")
    except Exception as e:
        await message.answer("Интервал не установлен", reply_markup=cancelkeyboard)
        logger.info(
            f"ANSWER USER: {userID}, ROLE: {Users[userIndex].role}, COMMAND: Set Parsing, STAGE: 2, CONTENT: Interval Not Setted")
        return


########################Set badproxy#######################

class SetBadInterval(StatesGroup):
    interval = State()


@dp.message_handler(lambda message: message.text == "Задать интервал отдыха")
async def set_cooldown(message: types.Message, state: FSMContext):
    userID = message.from_user.id
    userIndex = FindUser(userID)

    logger.info(f"MESSAGE USER: {userID}, ROLE: {Users[userIndex].role}, COMMAND: Set Bad Proxy, STAGE: 1")

    if Users[userIndex].role != "Admin":
        await message.answer("Отказано в доступе", reply_markup=startKeyboard)
        logger.info(
            f"ANSWER USER: {userID}, ROLE: {Users[userIndex].role}, COMMAND: Set Bad Proxy, STAGE: 1, CONTENT: Access Denied")
        return
    else:
        await message.answer("Введите интервал в секундах", reply_markup=cancelkeyboard)
        await state.set_state(SetBadInterval.interval.state)
        logger.info(
            f"ANSWER USER: {userID}, ROLE: {Users[userIndex].role}, COMMAND: Set Bad Proxy, STAGE: 1, CONTENT: Await Interval")


@dp.message_handler(state=SetBadInterval.interval)
async def set_bad_inteval(message: types.Message, state: FSMContext):
    userID = message.from_user.id
    userIndex = FindUser(userID)

    logger.info(f"MESSAGE USER: {userID}, ROLE: {Users[userIndex].role}, COMMAND: Set Bad Proxy, STAGE: 2")

    try:
        interval = float(message.text)
        set_C(interval)
        await message.answer("Интервал установлен", reply_markup=adminKeyboard)
        await state.finish()
        logger.info(
            f"ANSWER USER: {userID}, ROLE: {Users[userIndex].role}, COMMAND: Set Bad Proxy, STAGE: 2, CONTENT: Interval Setted")
    except Exception as e:
        await message.answer("Интервал не установлен", reply_markup=cancelkeyboard)
        logger.info(
            f"ANSWER USER: {userID}, ROLE: {Users[userIndex].role}, COMMAND: Set Parsing, STAGE: 2, CONTENT: Interval Not Setted")
        return


######################Add linklimit########################

class AddLinkLimit(StatesGroup):
    userID = State()
    linkNumber = State()


@dp.message_handler(lambda message: message.text == "Увеличить лимит ссылок")
async def add_linklimit(message: types.Message, state: FSMContext):
    userID = message.from_user.id
    userIndex = FindUser(userID)

    logger.info(f"MESSAGE USER: {userID}, ROLE: {Users[userIndex].role}, COMMAND: Add Link Limit, STAGE: 1")

    if Users[userIndex].role != "Admin":
        await message.answer("Отказано в доступе", reply_markup=startKeyboard)
        logger.info(
            f"ANSWER USER: {userID}, ROLE: {Users[userIndex].role}, COMMAND: Add Link Limit, STAGE: 1, CONTENT: Access Denied")
        return
    else:
        await message.answer("Введите ID пользователя", reply_markup=cancelkeyboard)
        await state.set_state(AddLinkLimit.userID.state)
        logger.info(
            f"ANSWER USER: {userID}, ROLE: {Users[userIndex].role}, COMMAND: Add Link Limit, STAGE: 1, CONTENT: Await ID")

@dp.message_handler(state=AddLinkLimit.userID)
async def linklimit_user(message: types.Message, state: FSMContext):
    userID = message.from_user.id
    userIndex = FindUser(userID)

    logger.info(f"MESSAGE USER: {userID}, ROLE: {Users[userIndex].role}, COMMAND: Add Link Limit, STAGE: 2")

    try:
        userIndex = FindUser(message.text)
        await state.update_data(index=userIndex)
        await message.answer("Сколько слотов добавить?", reply_markup=cancelkeyboard)
        await state.set_state(AddLinkLimit.linkNumber.state)
        logger.info(
            f"ANSWER USER: {userID}, ROLE: {Users[userIndex].role}, COMMAND: Add Link Limit, STAGE: 2, CONTENT: Await Value")
    except Exception as e:
        await message.answer("Пользователь не найден", reply_markup=cancelkeyboard)
        logger.info(
            f"ANSWER USER: {userID}, ROLE: {Users[userIndex].role}, COMMAND: Add Link Limit, STAGE: 2, CONTENT: User Not Found")


@dp.message_handler(state=AddLinkLimit.linkNumber)
async def linklimit_finale(message: types.Message, state: FSMContext):
    data =  await state.get_data()
    userIndex = data['id']

    userID = message.from_user.id
    Index = FindUser(userID)

    logger.info(f"MESSAGE USER: {userID}, ROLE: {Users[Index].role}, COMMAND: Add Link Limit, STAGE: 3")

    try:
        Users[userIndex].linkLimit += int(message.text)
        await message.answer("Лимит пользователя был увеличен", reply_markup=adminKeyboard)
        logger.info(
            f"ANSWER USER: {userID}, ROLE: {Users[userIndex].role}, COMMAND: Add Link Limit, STAGE: 3, CONTENT: Limit Added")
    except Exception as e:
        await message.answer("Ошибка", reply_markup=cancelkeyboard)
        logger.info(
            f"ANSWER USER: {userID}, ROLE: {Users[userIndex].role}, COMMAND: Add Link Limit, STAGE: 3, CONTENT: Error")
        return




######################Emergency Exit#######################
@dp.message_handler(lambda message: message.text == "Экстренная остановка")
async def emergency_stop(message: types.Message):
    userID = message.from_user.id
    userIndex = FindUser(userID)

    logger.info(f"MESSAGE USER: {userID}, ROLE: {Users[userIndex].role}, COMMAND: Emergency Exit, STAGE: 1")

    if Users[userIndex].role != "Admin":
        await message.answer("Отказано в доступе", reply_markup=startKeyboard)
        logger.info(
            f"ANSWER USER: {userID}, ROLE: {Users[userIndex].role}, COMMAND: Emergency Exit, STAGE: 1, CONTENT: Access Denied")
    else:
        logger.warning(f"USER: {userID}, EMERGENCY EXIT!")
        # sys.exit(1)


#########################Get Logs##########################
@dp.message_handler(lambda message: message.text == "Логи")
async def get_logs(message: types.Message):
    userID = message.from_user.id
    userIndex = FindUser(userID)

    logger.info(f"MESSAGE USER: {userID}, ROLE: {Users[userIndex].role}, COMMAND: Get Logs, STAGE: 1")

    if Users[userIndex].role != "Admin":
        await message.answer("Отказано в доступе", reply_markup=startKeyboard)
        logger.info(
            f"ANSWER USER: {userID}, ROLE: {Users[userIndex].role}, COMMAND: Get Logs, STAGE: 1, CONTENT: Access Denied")
        return
    else:
        await message.answer_document(open("BotLogs.txt", 'rb'))
        logger.info(
            f"ANSWER USER: {userID}, ROLE: {Users[userIndex].role}, COMMAND: Get Logs, STAGE: 1, CONTENT: Logs Sent")

###################Send Message To User####################


async def send_to_user(chatID, message):
    print("Send")
    await bot.send_message(chat_id=chatID, text=message)