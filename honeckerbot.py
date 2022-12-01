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
import time
# import requests

import mysql.connector

DBHOST = "localhost"
DBUSER = "honecker"
DBNAME = "honeckerdb"
DBPASSWORD = os.environ.get('DBPASSWORD')
SALAISUUS = os.environ.get('SALAISUUS')

horinat = ["...huh, anteeksi, torkahdin hetkeksi, kysyisitkö uudestaan", "mieti nyt tarkkaan...", "suututtaa", "mä en nyt jaksa", "sano mua johtajaks"]
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

def noppa() -> int:
    global noppa
    noppa = random.randint(0, 9)
    return noppa

def arvon_paasihteeri(update: Update, context: CallbackContext):
    paasihteeri = sleeps()
    noppa = noppa()
    if not check_cooldown() or noppa == 1:
        if noppa == 0:
            paasihteeri = "Politbyroo hyväksyy"
        elif noppa == 1 or noppa == 2:
            paasihteeri = horinaa()
            noppa = noppa()
            if noppa == 0:
                context.bot.sendMessage(chat_id=update.effective_chat.id, text=paasihteeri)
                time.sleep(noppa)
                paasihteeri = "...GULAG!"
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
    dbopen()

    name = update.message.from_user.username
    name.strip('@')

    if is_in_db(name):
        context.bot.sendMessage(chat_id=update.effective_chat.id, text="Olet jo kansalainen")
    else:
        cursor.execute("INSERT INTO Stasi (Username, Credits) VALUES (%s, %s)", (name, 0))
        db.commit()
        context.bot.sendMessage(chat_id=update.effective_chat.id, text="Olet nyt kansalainen")
    
    dbclose()


def update_credit(name: str, amount: int):
    dbopen()

    cursor.execute("SELECT Credits FROM Stasi WHERE Username = %s", [(name)])
    credits = int(cursor.fetchone()[0])
    credits = credits + amount
    cursor.execute("UPDATE Stasi SET Credits = %s WHERE Username = %s", (credits, name))

    dbclose()


def is_in_db(name: str) -> bool:
    dbopen()

    cursor.execute("SELECT * FROM Stasi WHERE username = %s", [(name)])
    return cursor.rowcount > 0

    dbclose()


def ilmianna(update: Update, context: CallbackContext):
    if len(context.args) < 2:
        response = "Usage: /vinkkaa <henkilö> <syy>"

    else:
        subject = context.args[0].strip('@')
        reason = ' '.join(context.args[1:])

        # check for valid username
        if subject == "honeckerbot" or subject == "pääsihteeri":
            context.bot.sendMessage(chat_id=update.effective_chat.id, text="Pääsihteeri ei voi tehdä väärin")

        if is_in_db(subject):
            punishment = random.randint(-100, -1)
            update_credit(subject, punishment)

            response = f"@{subject}, pääsihteeri on vihainen:\n{punishment} pistettä: {reason}"
        else:
            response = f"Henkilö ei ole kansalainen"

    context.bot.sendMessage(chat_id=update.effective_chat.id, text=response)


def kehu(update: Update, context: CallbackContext):
    if len(context.args) < 2:
        response = "Usage: /kehu <name> <syy>"
    elif context.args[0].strip('@') == "honeckerbot"  or context.args[0] == "pääsihteeri":
        response = "Tiesin jo"
    elif context.args[0].strip('@') == update.message.from_user.username:
        response = "Et voi kehua itseäsi"
    elif not is_in_db(context.args[0].strip('@')):
        response = "Henkilö ei ole kansalainen"
    else:
        subject = context.args[0].strip('@')
        reason = ' '.join(context.args[1:])

        price = random.randint(1, 10)
        update_credit(subject, price)

        response = f"@{subject}, pääsihteeri on tyytyväinen:\n+{price} pistettä: {reason}"

    context.bot.sendMessage(chat_id=update.effective_chat.id, text=response)


def tilanne(update: Update, context: CallbackContext):
    dbopen()

    response = ""
    user = update.message.from_user.username
    user.strip('@')

    if is_in_db(user):
        cursor.execute("SELECT Credits FROM Stasi WHERE username = %s", [(user)])
        credits = int(cursor.fetchone()[0])

        if credits < 0:
            response = f"{credits} {'piste' if credits == -1 else 'pistettä'}, kuolema on sinun kohtalosi"
        elif credits == 0:
            response = f"0 pistettä, teitä valvotaan tarkalla silmällä"
        elif credits < 100:
            response = f"{credits} {'piste' if credits == 1 else 'pistettä'}, takaisin töihin"
        elif credits < 100:
            response = f"{credits} pistettä, olet hyvä kansalainen"

    else:
        response = "Et ole kansalainen"

    context.bot.sendMessage(chat_id=update.effective_chat.id, text=response)

    dbclose()


def paras_kansalainen(update: Update, context: CallbackContext):
    dbopen()

    cursor.execute("SELECT Username, Credits FROM Stasi ORDER BY Credits DESC LIMIT 1")
    result = cursor.fetchone()

    if result:
        response = f"Paras kansalainen on @{result[0]} {result[1]} {'pisteellä' if result[1] == 1 else 'pisteillä'}"
    else:
        response = "Ei vielä yhtään kansalaista"

    context.bot.sendMessage(chat_id=update.effective_chat.id, text=response)

    dbclose()


def seksi(update: Update, context: CallbackContext):
    user = update.message.from_user.username
    response = "Ei tälleen"

    if is_in_db(user):
        update_credit(user, -100)
        response += ", -100 pistettä"

    context.bot.sendMessage(chat_id=update.effective_chat.id, text=response)


# QUOTE 
######################################################################################
# TODO: use database
def save_quote(name : str, quote : str, addedby : str):
    dbopen()
    timestamp = str(datetime.datetime.now())
    insert_quotes = (
       "INSERT INTO Quotes (name, quote, addedby, timestamp) "
       "VALUES (%s, %s, %s, %s)"
    )
    data = (name, quote, addedby, timestamp)
    cursor.execute(insert_quotes, data)
    dbclose()

# TODO: use database
def get_quote(name : str) -> str:
    dbopen()
    select_quote = (
        "SELECT quote FROM Quotes "
        "WHERE name = %s "
        "ORDER BY RAND() "
        "LIMIT 1 "
    )
    data = [(name)]
    cursor.execute(select_quote, data)
    quote = str(cursor.fetchone()[0])
    dbclose()
    return quote
    
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
        #print("EBIN DEUBG PRINT")
        #print(update.message.chat_id)
        addedby = str(update.message.from_user.username) 
        if quote[0] == '"' and quote[len(quote) - 1] == '"':
            quote = quote[1:len(quote) - 1]
    save_quote(name, quote, addedby)
    #context.bot.sendMessage(chat_id=update.message.chat.id, text='Quote saved!') # maybe not necessary to inform of success

def quote(update: Update, context: CallbackContext):
    try:
        name = context.args[0].strip('@')
        quote = get_quote(name)
        formated_quote = f'"{quote}" - {name}'
        context.bot.sendMessage(chat_id=update.message.chat.id, text=formated_quote)
    except:
        pass

# main
######################################################################################
def main():
    global quotes
    global db
    global cursor
    global noppa

    updater = Updater(SALAISUUS, use_context=True)
    dispatcher = updater.dispatcher
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

    honecker_re = re.compile(r'arvon pääsihteeri', flags=re.IGNORECASE)

    handlers = []
    handlers.append(CommandHandler("addquote", add_quote))
    handlers.append(CommandHandler("quote", quote))
    handlers.append(CommandHandler("dbtest", dbtest))
    handlers.append(CommandHandler("kansalaiseksi", kansalaiseksi))
    handlers.append(CommandHandler("seksi", seksi))
    handlers.append(CommandHandler("kehu", kehu))
    handlers.append(CommandHandler("ilmianna", ilmianna))
    handlers.append(CommandHandler("tilanne", tilanne))
    handlers.append(CommandHandler("paras", paras_kansalainen))
    handlers.append(MessageHandler(Filters.regex(honecker_re), arvon_paasihteeri))

    for handler in handlers:
        dispatcher.add_handler(handler)

    updater.start_polling()
    updater.idle()

main()
