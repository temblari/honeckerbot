# shit functions :D
def lainaus(update: Update, context: CallbackContext):
    r = requests.get('https://api.quotable.io/random')
    data = json.loads(r.content)
    quoteHeader=("Author: " + data["author"])
    quoteContent=("Quote: " + data["content"])
    lainaus=str(quoteHeader + "\n" + quoteContent)
    context.bot.sendMessage(chat_id=update.effective_chat.id, text=lainaus)

def louhi(update: Update, context: CallbackContext):
    kolikot = random.randrange(0, 15)
    if kolikot == 0:
        louhivastaus = "Et onnistunut louhimaan :("
    else:
        louhivastaus = f'Onnistuit louhimaan {kolikot} {"kolikkoa." if kolikot != 1 else "kolikon."}'

    context.bot.sendMessage(chat_id=update.effective_chat.id, text=louhivastaus)
