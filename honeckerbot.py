#!/usr/bin/env python
# -*- coding: utf-8 -*-

from telegram import Update
from telegram.ext import CallbackContext, Updater, CommandHandler, Filters, MessageHandler

import datetime
# import json
import logging
import os
import random
import re
# import requests

import mysql.connector

DBHOST = "localhost"
DBUSER = "honecker"
DBNAME = "honeckerdb"
DBPASSWORD = os.environ.get('DBPASSWORD')
SALAISUUS = os.environ.get('SALAISUUS')

horinat = ["...huh, anteeksi, torkahdin hetkeksi, kysyisitkö uudestaan", "mieti nyt tarkkaan...", "suututtaa", "mä en nyt jaksa"]
unet = ["...zzz...zz...", "..zz...z...", "...zz..z.zz...", "..."]

def horinaa():
    return random.choice(horinat)

def sleeps():
    return random.choice(unet)

# Cooldown related stuff
COOLDOWN = {"minutes" : 1, "last" : None}

def check_cooldown() -> bool:
    global COOLDOWN
    now = datetime.datetime.now()
    last = COOLDOWN["last"]

    if last == None:
        COOLDOWN["last"] = now
        return False

    delta = now - last
    diff_in_minutes = round(delta.total_seconds() / 60)

    if diff_in_minutes < COOLDOWN["minutes"]:
        print(f"diff: {diff_in_minutes}")
        return True

    COOLDOWN['last'] = now
    return False

def arvon_paasihteeri(update: Update, context: CallbackContext):
    paasihteeri = sleeps()
    noppa = random.randint(0, 9)
    if not check_cooldown() or noppa == 1:
        if noppa == 0:
            paasihteeri = "Politbyroo hyväksyy"
        elif noppa == 1:
            paasihteeri = horinaa()
        else:
            paasihteeri = "SIPERIAAN!"
    context.bot.sendMessage(chat_id=update.effective_chat.id, text=paasihteeri)

# DB
#####################################################################################

def dbtest(update: Update, context: CallbackContext):
    dbopen()
    cursor.execute("show tables")
    for x in cursor:
        context.bot.sendMessage(chat_id=update.effective_chat.id, text=x)
    dbclose()
    
def initdb():
    return mysql.connector.connect(
        host = DBHOST,
        user = DBUSER,
        password = DBPASSWORD,
        database = DBNAME
        )

def dbopen():
    global db
    global cursor
    db = initdb()
    cursor = db.cursor(buffered=True)
    
def dbclose():
    db.commit()
    cursor.close()
    db.close()

# SOCIAL CREDITS 
######################################################################################
def kansalaiseksi(update: Update, context: CallbackContext):
    name = context.message.from_user.username
    name.strip('@')

    if is_in_db(name):
        context.bot.sendMessage(chat_id=update.effective_chat.id, text="Olet jo kansalainen")
    else:
        cursor.execute("INSERT INTO Stasi (Username, Credits) VALUES (%s, %s)", (name, 0))
        db.commit()
        context.bot.sendMessage(chat_id=update.effective_chat.id, text="Olet nyt kansalainen")


def update_credit(name: str, amount: int):
    credits = cursor.execute("SELECT Credits FROM Stasi WHERE Username = %s", (name))
    credits = credits + amount
    cursor.execute("UPDATE Stasi SET Credits = %s WHERE Username = %s", (credits, name))
    db.commit()


def is_in_db(name: str) -> bool:
    cursor.execute("SELECT * FROM stasi WHERE username = %s", (name))
    return cursor.rowcount > 0


def ilmianna(update: Update, context: CallbackContext):
    subject = ""
    reason = ""

    if len(context.args) < 2:
        subject = context.message.from_user.username
        reason = "Usage: /vinkkaa <henkilö> <syy>"

    else:
        subject = context.args[0].strip('@')

        reason = ' '.join(context.args[1:])

    # check for valid username
    if subject == "honeckerbot":
        reason = "Pääsihteeri ei voi tehdä väärin"
        punishment = -1000
    elif is_in_db(subject):
        punishment = random.randint(-1, -100)
        update_credit(subject, punishment)

        response = f"@{subject}, pääsihteeri on vihainen:\n-{punishment} pistettä: {reason}"
    else:
        response = f"Henkilö ei ole kansalainen"

    context.bot.sendMessage(chat_id=update.effective_chat.id, text=response)


def kehu(update: Update, context: CallbackContext):
    if len(context.args) < 2:
        context.bot.sendMessage(chat_id=update.message.chat.id, text='Usage: /kehu <name> <syy>')
    else:
        name = context.args[0].strip('@')
        reason = ' '.join(context.args[1:])

        price = random.randint(1, 10)
        update_credit(name, price)

        response = f"@{name}, pääsihteeri on tyytyväinen:\n+{price} pistettä: {reason}"


def tilanne(update: Update, context: CallbackContext):
    response = ""
    user = context.message.from_user.username
    user.strip('@')

    credits = cursor.execute("SELECT Credits FROM stasi WHERE username = %s", (user))

    if credits < 0:
        response = f"{credits} pisteitä, kuolema on sinun kohtalosi"
    elif credits < 100:
        response = f"{credits} pisteitä, olet ihan ok kansalainen"
    elif credits < 100:
        response = f"{credits} pisteitä, olet hyvä kansalainen"

    context.bot.sendMessage(chat_id=update.effective_chat.id, text=response)

# QUOTE 
######################################################################################
# TODO: use database
def save_quote(name : str, quote : str):
    dbopen()
    timestamp = str(datetime.datetime.now())
    insert_quotes = (
       "INSERT INTO Quotes (name, quote) "
       "VALUES (%s, %s, %s)"
    )
    data = (name, quote, timestamp)
    cursor.execute(insert_quotes, data)
    dbclose()

# TODO: use database
def get_quote(name : str) -> str:
    dbopen()
    select_quote = (
        "SELECT * FROM Quotes "
        "WHERE name = %s "
        "ORDER BY RAND() "
        "LIMIT 1 "
    )
    data = [(name)]
    data = cursor.execute(select_quote, data)
    dbclose()
    return str(data)
    
    #if not name in quotes:
    #    return f"No quotes exist for {name}"
    #else:
    #    return random.choice(quotes[name])

def add_quote(update: Update, context: CallbackContext):
    if len(context.args) < 2:
            context.bot.sendMessage(chat_id=update.message.chat.id, text='Usage: /addquote <name> <quote>')
    else:
        name = context.args[0].strip('@')
        quote = ' '.join(context.args[1:])
        if quote[0] == '"' and quote[len(quote) - 1] == '"':
            quote = quote[1:len(quote) - 1]
    save_quote(name, quote)
    context.bot.sendMessage(chat_id=update.message.chat.id, text='Quote saved!') # maybe not necessary to inform of success

def quote(update: Update, context: CallbackContext):
        name = context.args[0].strip('@')
        quote = get_quote(name)
        formated_quote = f'"{quote}" - {name}'
        context.bot.sendMessage(chat_id=update.message.chat.id, text=formated_quote)

# main
######################################################################################
def main():
    global quotes
    global db
    global cursor

    updater = Updater(SALAISUUS, use_context=True)
    dispatcher = updater.dispatcher
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

    honecker_re = re.compile(r'arvon pääsihteeri', flags=re.IGNORECASE)

    handlers = []
    handlers.append(CommandHandler("addquote", add_quote))
    handlers.append(CommandHandler("quote", quote))
    handlers.append(CommandHandler("dbtest", dbtest))
    handlers.append(CommandHandler("kansalaiseksi", kansalaiseksi))
    handlers.append(CommandHandler("kehu", kehu))
    handlers.append(CommandHandler("ilmianna", ilmianna))
    handlers.append(CommandHandler("tilanne", tilanne))
    handlers.append(MessageHandler(Filters.regex(honecker_re), arvon_paasihteeri))

    for handler in handlers:
        dispatcher.add_handler(handler)

    updater.start_polling()
    updater.idle()

main()
