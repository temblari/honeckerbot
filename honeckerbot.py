#!/usr/bin/env python
# -*- coding: utf-8 -*-

from telegram import Update
from telegram.ext import CallbackContext, Updater, CommandHandler, Filters, MessageHandler

import datetime
import json
import logging
import os
import random
import re
import requests

import mysql.connector

DBHOST = "localhost"
DBUSER = "honecker"
DBNAME = "honeckerdb"
DBPASSWORD = os.environ.get('DBPASSWORD')
SALAISUUS = os.environ.get('SALAISUUS')

global horinat
global sleeps
horinat = ["...huh, anteeksi, torkahdin hetkeksi, kysyisitkö uudestaan", "mieti nyt tarkkaan...", "suututtaa"]
unet = ["...zzz...zz...", "..zz...z...", "...zz..z.zz..."]

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

def dbtest(update: Update, context: CallbackContext):
    tuloste = str(cursor.execute("show tables"))
    context.bot.sendMessage(chat_id=update.effective_chat.id, text=tuloste)

def initdb():
    return mysql.connector.connect(
        host = DBHOST,
        user = DBUSER,
        password = DBPASSWORD,
        database = DBNAME
        )

#########
# QUOTE #
######################################################################################
# TODO: use database
def save_quote(name : str, quote : str):
    insert_quotes = (
       "INSERT INTO Quotes (name, quote) "
       "VALUES (%s, %s)"
    )
    data = (name, quote)
    cursor.execute(insert_quotes, data)
    #if not name in quotes:
    #    quotes[name] = [quote]
    #else:
    #    quotes[name].append(quote)
# TODO: use database
def get_quote(name : str) -> str:
    if not name in quotes:
        return f"No quotes exist for {name}"
    else:
        return random.choice(quotes[name])

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

######################################################################################

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

def horinaa():
    return random.choice(horinat)

def sleeps():
    return random.choice(unet)

def main():
    global quotes
    global db
    global cursor
    db = initdb()
    cursor = db.cursor()
    updater = Updater(SALAISUUS, use_context=True)
    dispatcher = updater.dispatcher
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

    honecker_re = re.compile(r'arvon pääsihteeri', flags=re.IGNORECASE)

    handlers = []
    handlers.append(CommandHandler("addquote", add_quote))
    handlers.append(CommandHandler("quote", quote))
    handlers.append(CommandHandler("dbtest", dbtest))
    handlers.append(MessageHandler(Filters.regex(honecker_re), arvon_paasihteeri))

    for handler in handlers:
        dispatcher.add_handler(handler)

    updater.start_polling()
    updater.idle()

main()
