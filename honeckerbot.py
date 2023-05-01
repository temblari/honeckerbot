#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pytz import timezone
from telegram import Update
from telegram.ext import CallbackContext, Updater, CommandHandler, Filters, MessageHandler
from dotenv import load_dotenv

import datetime
import logging
import os
import random
import re
import time

load_dotenv()
SALAISUUS = os.getenv("SALAISUUS")
GROUP_ID = os.getenv("GROUP_ID")
DB_HOST = os.getenv("DBHOST")
DB_USER = os.getenv("DBUSER")
DB_PASSWORD = os.getenv("DBPASSWORD")
DB_NAME = os.getenv("DBNAME")

import initdb
import db

horinat = ["...huh, anteeksi, torkahdin hetkeksi, kysyisitkö uudestaan", "mieti nyt tarkkaan...", "suututtaa", "mä en nyt jaksa", "sano mua johtajaks"]

def horinaa():
    return random.choice(horinat)

def arvon_paasihteeri(update: Update, context: CallbackContext):
    noppa = random.randint(0, 10)

    if noppa == 1:
        paasihteeri = "Politbyroo hyväksyy"
    elif noppa == 2:
        paasihteeri = horinaa()
    else:
        paasihteeri = "SIPERIAAN!"

    context.bot.sendMessage(chat_id=update.effective_chat.id, text=paasihteeri)


# DB
#####################################################################################


def dbtest(update: Update, context: CallbackContext):
    context.bot.sendMessage(chat_id=update.effective_chat.id, text=db.readScore())

#def initdb():
#    return mysql.connector.connect(
#        host = DBHOST,
#        user = DBUSER,
#        password = DBPASSWORD,
#        database = DBNAME
#        )
#
#def dbopen():
#    global db
#    global cursor
#    db = initdb()
#    cursor = db.cursor(buffered=True)
#
#def dbclose():
#    db.commit()
#    cursor.close()
#    db.close()

# SOCIAL CREDITS 
######################################################################################
def kansalaiseksi(update: Update, context: CallbackContext):
    name = update.message.from_user.username
    name.strip('@')
    if db.is_in_db(name):
        context.bot.sendMessage(chat_id=update.effective_chat.id, text="Olet jo kansalainen")
    else:
        db.insertKansalainen(name)
        context.bot.sendMessage(chat_id=update.effective_chat.id, text="Olet nyt kansalainen")

def ilmianna(update: Update, context: CallbackContext):
    if len(context.args) < 2:
        response = "Usage: /vinkkaa <henkilö> <syy>"

    else:
        subject = context.args[0].strip('@')
        reason = ' '.join(context.args[1:])

        # check for valid username
        if subject == "honeckerbot" or subject == "pääsihteeri":
            context.bot.sendMessage(chat_id=update.effective_chat.id, text="Pääsihteeri ei voi tehdä väärin")
            if db.is_in_db(update.message.from_user.username):
                db.update_credit(update.message.from_user.username, -100)

        elif db.is_in_db(subject):
            punishment = random.randint(-100, -1)
            db.update_credit(subject, punishment)

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
    elif not db.is_in_db(context.args[0].strip('@')):
        response = "Henkilö ei ole kansalainen"
    else:
        subject = context.args[0].strip('@')
        reason = ' '.join(context.args[1:])

        price = random.randint(1, 10)
        db.update_credit(subject, price)

        response = f"@{subject}, pääsihteeri on tyytyväinen:\n+{price} pistettä: {reason}"

    context.bot.sendMessage(chat_id=update.effective_chat.id, text=response)


def tilanne(update: Update, context: CallbackContext):
    response = ""
    user = update.message.from_user.username
    user.strip('@')

    if db.is_in_db(user):
        response = db.readUserScore(user)
    else:
        response = "Et ole kansalainen"

    context.bot.sendMessage(chat_id=update.effective_chat.id, text=response)


def paras_kansalainen(update: Update, context: CallbackContext):
    result = db.readBestCitizen()
    if result:
        response = f"Paras kansalainen on @{result[0]} {result[1]} {'pisteellä' if result[1] == 1 else 'pisteillä'}"
    else:
        response = "Ei vielä yhtään kansalaista"

    context.bot.sendMessage(chat_id=update.effective_chat.id, text=response)



def seksi(update: Update, context: CallbackContext):
    user = update.message.from_user.username
    response = "Ei tälleen"

    if db.is_in_db(user):
        db.update_credit(user, -100)
        response += ", -100 pistettä"

    context.bot.sendMessage(chat_id=update.effective_chat.id, text=response)


# QUOTE 
######################################################################################
def add_quote(update: Update, context: CallbackContext):
    if len(context.args) < 2:
            context.bot.sendMessage(chat_id=update.message.chat.id, text='Usage: /addquote <name> <quote>')
    else:
        name = context.args[0].strip('@')
        quote = ' '.join(context.args[1:])
        addedby = str(update.message.from_user.username) 
        if quote[0] == '"' and quote[len(quote) - 1] == '"':
            quote = quote[1:len(quote) - 1]
    db.insertQuote(name, quote, addedby)

def quote(update: Update, context: CallbackContext):
    try:
        name = context.args[0].strip('@')
        quote = db.readQuote(name)
        formated_quote = f'"{quote}" - {name}'
        context.bot.sendMessage(chat_id=update.message.chat.id, text=formated_quote)
    except:
        pass

# DOKAUSKALENTERI
######################################################################################
dokaus_days = {} # {date: list[str]}

def listaa_dokaukset() -> str:
    global dokaus_days
    doks = dict(sorted(dokaus_days.items()))
    dokaukset = ""
    for day in doks:
        dokaukset = dokaukset + str(day) + " "
        for dokaus in doks[day]:
            dokaukset += dokaus
            dokaukset += " "
        dokaukset += "\n"

    return dokaukset


def dokataanko_tanaan() -> tuple[bool, str]:
    global dokaus_days
    today = datetime.date.today()
    if today in dokaus_days:
        return True, dokaus_days[today]
    return False, ""


def save_dokaus(date, reason : str):
    global dokaus_days
    if not date in dokaus_days:
        dokaus_days[date] = [reason]
    else:
        dokaus_days[date].append(reason)

def add_dokaus(update: Update, context: CallbackContext):
    if len(context.args) < 2:
            context.bot.sendMessage(chat_id=update.message.chat.id, text='Usage: /dokausta <DD.MM.YYYY> <reason>')
    else:
        try:
            date = datetime.datetime.strptime(context.args[0], '%d.%m.%Y').date()
        except ValueError:
            context.bot.sendMessage(chat_id=update.message.chat.id, text='Usage: /dokausta <DD.MM.YYYY> <reason>')

        reason = ' '.join(context.args[1:])
        save_dokaus(date, reason)
        if date == datetime.date.today():
            context.bot.sendMessage(chat_id=update.message.chat.id, text=f'Tänään vissiin dokataan: {reason}')

def dokaukset(update: Update, context: CallbackContext):
    dokaukset = listaa_dokaukset()
    if not dokaukset == "":
        context.bot.sendMessage(chat_id=update.message.chat.id, text=dokaukset)

def callback_dokaus(context: CallbackContext):
    res = dokataanko_tanaan()
    if res[0]:
        context.bot.send_message(chat_id=GROUP_ID, text=f'Tänään dokataan: {res[1]}')


# main
######################################################################################
def main():
    #global quotes
    #global db
    #global cursor
    #global noppa
    initdb.initdb()

    updater = Updater(SALAISUUS, use_context=True)
    dispatcher = updater.dispatcher
    jobs = updater.job_queue

    dokaus_check_time = datetime.time(9, 00, tzinfo=timezone('Europe/Helsinki'))
    jobs.run_daily(callback_dokaus, dokaus_check_time)
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

    paasihteeri_re = re.compile(r'arvon pääsihteeri', flags=re.IGNORECASE)

    handlers = [
        CommandHandler("lisaaloki", add_quote),
        CommandHandler("loki", quote),
        CommandHandler("dbtest", dbtest),
        CommandHandler("kansalaiseksi", kansalaiseksi),
        CommandHandler("seksi", seksi),
        CommandHandler("kehu", kehu),
        CommandHandler("ilmianna", ilmianna),
        CommandHandler("tilanne", tilanne),
        CommandHandler("paras", paras_kansalainen),
        CommandHandler("dokausta", add_dokaus),
        CommandHandler("dokaukset", dokaukset),
        MessageHandler(Filters.regex(paasihteeri_re), arvon_paasihteeri)
    ]

    for handler in handlers:
        dispatcher.add_handler(handler)

    updater.start_polling()
    updater.idle()

main()
