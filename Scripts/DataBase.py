import psycopg2
from psycopg2.extras import NamedTupleCursor

conn = psycopg2.connect(dbname="Users", user='postgres', password='lolkek228', host='127.0.0.1')


with conn.cursor(cursor_factory=NamedTupleCursor) as curs:
    curs.execute("SELECT id FROM test WHERE login = %s", ('loh',))
    user = curs.fetchall()
    print(user)