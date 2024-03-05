import psycopg2
from psycopg2.extras import NamedTupleCursor

# try:
#     conn = psycopg2.connect(dbname="Users", user='postgres', password='lolkek228', host='localhost')
#     with conn:
#         with conn.cursor() as curs:
#             curs.execute("SELECT datname FROM pg_database")
#             base = curs.fetchone()
#             print(base)
#             name = 'postgres'
#             if base == (f'{name}',):
#                 print(1)
#             else:
#                 print(0)
#             try:
#                 newconn = psycopg2.connect(dbname="postgres", user='postgres', password='lolkek228', host='localhost')
#             except:
#                 print(":(")
# except:
#     print("error")
table = "qwerty"
fields = ["состояние", "производитель", "цвет"]
values = ["1", "2", "3"]
price = 120000


def write_to_base(table, price, fields, values):
    fieldline = ''
    field = ""
    value = ""
    for item in fields:
        fieldline += item + " VARCHAR, "
        field += item + ", "
    fieldline += "price INTEGER"
    field += "price"
    for item in values:
        value += "'" + item + "'" + ", "
    value = value[0:len(value)-2]
    conn = psycopg2.connect(dbname="Users", user='postgres', password='lolkek228', host='localhost')
    with conn:
        try:
            with conn.cursor() as curs:
                curs.execute(f"CREATE TABLE IF NOT EXISTS {table} ({fieldline});")
                conn.commit()
                curs.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name = '{table}'"
                             f"ORDER BY ordinal_position;")
                columns = curs.fetchall()
                print(columns)
                for i in fields:
                    j = (f'{i}',)
                    print(j)
                    if j not in columns:
                        print("new column")
                        curs.execute(f"ALTER TABLE {table} ADD {i} VARCHAR")
                line = f"INSERT INTO {table} ({field}) VALUES ({value}, {price})"
                print(line)
                print("Enter 0")
                curs.execute(f"INSERT INTO {table} ({field}) VALUES ({value}, {price})")
                conn.commit()

        except Exception as e:
            print(e)


def get_price_from_base(table, fields, values):
    condition = ''
    for i in range(len(fields)):
        condition += f"{fields[i]} = '{values[i]}' AND "
    condition = condition[0:len(condition)-5]
    print(condition)
    conn = psycopg2.connect(dbname="Users", user='postgres', password='lolkek228', host='localhost')
    with conn:
        with conn.cursor() as curs:
            curs.execute(f"SELECT price FROM {table} WHERE {condition}")
            prices = curs.fetchall()
    for i in range(len(prices)):
        prices[i] = prices[i][0]
    print(prices)

get_price_from_base(table, fields, values)