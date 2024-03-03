import json
import string
import random


proxyList = []
badProxy = []

T = 60.0
C = 1200.0


def set_T(time):
    global T
    T = time


def set_C(time):
    global C
    C = time


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


Users = []


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


class Link:
    href = ''
    link_type = ""
    users = []
    usersLinkID = []

    def __init__(self, link):
        self.href = link