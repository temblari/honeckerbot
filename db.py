from contextlib import contextmanager
import mysql.connector as mysql
import datetime
import os

DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")

config = {
    'host': DB_HOST,
    'user': DB_USER,
    'password': DB_PASSWORD,
    'database': DB_NAME
}


@contextmanager
def cursor():
    try:
        conn = mysql.connect(**config)
        cur = conn.cursor(buffered=True)
        yield cur
        conn.commit()
    finally:
        conn.close()


# Testing purposes for db and getting credits for all users
def readScore() -> str:
    with cursor() as cur:
        stats = ''
        cur.execute("SELECT * FROM Stasi")
        for x in cur:
            x = str(x)
            stats += ("".join(x))
        return stats


def is_in_db(name: str) -> bool:
    with cursor() as cur:
        cur.execute("SELECT * FROM Stasi WHERE username = %s", [name])
        return cur.rowcount > 0


def insertKansalainen(name: str):
    with cursor() as cur:
        cur.execute("INSERT INTO Stasi (Username, Credits) VALUES (%s, %s)", (name, 0))


def insertQuote(name: str, quote: str, addedby: str):
    with cursor() as cur:
        timestamp = str(datetime.datetime.now())
        insert_quotes = (
            'INSERT INTO Quotes (name, quote, addedby, timestamp),'
            'VALUES (%s, %s, %s, %s)'
        )
        data = (name, quote, addedby, timestamp)
        cur.execute(insert_quotes, data)


def update_credit(name: str, amount: int):
    with cursor() as cur:
        cur.execute("SELECT Credits FROM Stasi WHERE Username = %s", [(name)])
        credits = int(cur.fetchone()[0])
        credits = credits + amount
        cur.execute("UPDATE Stasi SET Credits = %s WHERE Username = %s", (credits, name))


def readUserScore(user: str) -> str:
    with cursor() as cur:
        cur.execute("SELECT Credits FROM Stasi WHERE username = %s", [(user)])
        credits = int(cur.fetchone()[0])

        if credits < 0:
            response = f"{credits} {'piste' if credits == -1 else 'pistettä'}, kuolema on sinun kohtalosi"
        elif credits == 0:
            response = f"0 pistettä, teitä valvotaan tarkalla silmällä"
        elif credits < 100:
            response = f"{credits} {'piste' if credits == 1 else 'pistettä'}, takaisin töihin"
        elif credits < 100:
            response = f"{credits} pistettä, olet hyvä kansalainen"
        return response


def readBestCitizen():
    with cursor() as cur:
        cur.execute("SELECT Username, Credits FROM Stasi ORDER BY Credits DESC LIMIT 1")
        return cur.fetchone()


def readQuote(name: str) -> str:
    with cursor() as cur:
        select_quote = (
            "SELECT quote FROM Quotes "
            "WHERE name = %s "
            "ORDER BY RAND() "
            "LIMIT 1 "
        )
        data = [(name)]
        cur.execute(select_quote, data)
        return str(cursor.fetchone()[0])
