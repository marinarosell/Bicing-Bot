import telegram
from telegram.ext import Updater
from telegram.ext import CommandHandler
from staticmap import StaticMap, CircleMarker, Line
import data
import os
import networkx as nx


# Inicia la conversa amb el bicing_bot
# Crea un graf de distància 100 automàticament
def start(bot, update, user_data):
    data.create_graph(user_data)
    text = '''
Hola!😄 Sóc un bot de bicing🚲

Acabes de crear automàticament un graf amb les arestes més petites o iguals \
a 1000.

Escriu 🆘 /help 🆘 per tenir una llista de totes les comandes disponibles.
    '''
    bot.send_message(chat_id=update.message.chat_id, text=text,
                     parse_mode=telegram.ParseMode.MARKDOWN)
    return


def error(bot, update, tipus):
    if tipus == 0:
        text = "No has inicialitzat cap graf😡"

    # els errors següents són únicament per la funció de distribute
    if tipus == 1:
        text = '''
Has de introduir dos paràmetres, els quals corresponen al nombre mínim de \
bicis i al nombre mínim de forats lliures a cada estació, respectivament
'''
    elif tipus == 2:
        text = "No hem pogut trobar cap solució"
    elif tipus == 3:
        text = "Model de graf incorrecte"
    bot.send_message(chat_id=update.message.chat_id, text=text)
    return


# Fa una llista de les possibles comandes amb una breu descripció
def help(bot, update):
    text = '''
Aquí tens una llista 📝 amb totes les comandes i la seva descripció:

/start - inicialitza el bot i crea automàticament un graf de distància 1000
/help - fa una llista de les possibles comandes amb una breu descripció d'elles
/graph - crea un nou graf. Amb aquesta comanda has d'introduir un paràmetre, \
el qual correspon a la distància màxima de les arestes que formen el graf
/nodes - escriu el nombre d'estacions del graf
/edges - escriu el nombre d'arestes del graf
/components - escriu el nombre de components connexos del graf
/plotgraph - mostra un mapa totes les estacions que conformen el graf i les \
arestes que les connecten
/route - mostra en un mapa el camí més ràpid per anar d'una direcció d'origen \
a una direcció de destí. Amb aquesta comanda has d'introduir dues direccions \
de Barcelona
/authors - nom i email de les autores del bot
/distribute - fa una redistribució de les bicis de cada estació. Amb aquesta \
comanda has d'introduir dos paràmetres, els quals corresponen, respectivament,\
 al nombre de bicis mínim i al nombre de forats mínim per cada estació

[Enunciat de la pràctica](https://github.com/jordi-petit/ap2-bicingbot-2019)
    '''
    bot.send_message(chat_id=update.message.chat_id, text=text,
                     parse_mode=telegram.ParseMode.MARKDOWN)


def authors(bot, update):
    text = '''
Marina Rosell Murillo 🌱, marina.rosell@est.fib.upc.edu

Patricia Cabot Álvarez 🥑, patricia.cabot@est.fib.upc.edu
    '''
    bot.send_message(chat_id=update.message.chat_id, text=text,
                     parse_mode=telegram.ParseMode.MARKDOWN)


# Indica al bot que s'utilitza un nou graf
# Nota: tote les comandes posteriors usen el darrer graf generat
def graph(bot, update, args, user_data):  # args és la variable distancia
    if len(args) == 0:
        bot.send_message(chat_id=update.message.chat_id,
                         text="Has d'introduir una distància 😡")
    elif int(args[0]) < 0:
        bot.send_message(chat_id=update.message.chat_id,
                         text="Distància no vàlida ❌")
    else:
        data.create_graph(user_data, args)
        bot.send_message(chat_id=update.message.chat_id,
                         text="Has creat un graf correctament!✅")
    return


# Escriu el nombre de nodes del graf
def nodes(bot, update, user_data):
    exists = data.existent(user_data)
    if not exists:
        error(bot, update, 0)
    else:
        n = data.number_nodes(user_data)
        bot.send_message(chat_id=update.message.chat_id, text=n)
    return


# Escriu el nombre d'arestes del graf
def edges(bot, update, user_data):
    exists = data.existent(user_data)
    if not exists:
        error(bot, update, 0)
    else:
        m = data.number_arestes(user_data)
        bot.send_message(chat_id=update.message.chat_id, text=m)
    return


# Escriu el nombre de components connexs del graf
def components(bot, update, user_data):
    exists = data.existent(user_data)
    if not exists:
        error(bot, update, 0)
    else:
        c = data.number_components(user_data)
        bot.send_message(chat_id=update.message.chat_id, text=c)
    return


# Mostra un mapa amb les estacions del graf i les arestes que les connecten
def plotgraph(bot, update, user_data):
    exists = data.existent(user_data)
    if not exists:
        error(bot, update, 0)
    else:
        user_data['user'] = update.message.chat_id
        bot.send_message(chat_id=update.message.chat_id,
                         text="S'està carregant la imatge... 💬")
        data.create_plotgraph(user_data)
        name = str(user_data['user']) + '_mapa.png'
        bot.send_photo(chat_id=update.message.chat_id,
                       photo=open(name, 'rb'))
        os.remove(name)
    return


# Mostra en un mapa el camí més ràpid per anar d'un punt d'orígen a un altre
# destí. Els punts d'origen i de destí es dónen a través de dues adreces de
# Barcelona separades per una coma
def route(bot, update, args, user_data):
    exists = data.existent(user_data)
    if not exists:
        error(bot, update, 0)
    else:
        if len(args) == 0:
            text = '''
Has d'introduir les direccions d'origen i destí per poder crear una ruta 📌
'''
            bot.send_message(chat_id=update.message.chat_id, text=text)
        else:
            user_data['user'] = update.message.chat_id
            bot.send_message(chat_id=update.message.chat_id,
                             text="S'està creant la ruta... 🗺")
            ruta = data.create_route(args, user_data)
            if not ruta:
                bot.send_message(chat_id=update.message.chat_id,
                                 text="Adreça no trobada 🚫")
            else:
                name = str(user_data['user']) + '_ruta.png'
                bot.send_photo(chat_id=update.message.chat_id,
                               photo=open(name, 'rb'))
                os.remove(name)
    return


# Fa una redistribució de les bicis de cada estació i retorna el cost total i
# el moviment amb el major cost. La distribució es basa en els dos paràmetres,
# els quals equivalen, respectivament, al nombre mínim de bicis i al nombre
# mínim de forats.
def distribute(bot, update, args, user_data):
    exists = data.existent(user_data)
    if not exists:
        error(bot, update, 0)
    else:
        if len(args) != 2:
            error(bot, update, 1)
        else:
            flowCost, flowMax = data.distribution(args, user_data)
            if flowCost is None:
                if flowMax is False:
                    error(bot, update, 2)
                elif flowMax is True:
                    error(bot, update, 3)
            else:
                text1 = "Total cost of transfering bicycles is " + \
                    str(flowCost/1000) + " km"
                bot.send_message(chat_id=update.message.chat_id, text=text1)
                text2 = "The maximum cost of redistributing bicycles is: " + \
                    str(flowMax[0]) + " → " + str(flowMax[1]) + ", " + \
                    str(flowMax[2]) + " bikes, distance " + \
                    str(flowMax[3]/1000) + " km"
                bot.send_message(chat_id=update.message.chat_id, text=text2)
    return


TOKEN = open('token.txt').read().strip()
updater = Updater(token=TOKEN)
dispatcher = updater.dispatcher

# per utilitzar el data_user hem de posar -> pass_user_data=True
dispatcher.add_handler(CommandHandler('start', start, pass_user_data=True))
dispatcher.add_handler(CommandHandler('help', help))
dispatcher.add_handler(CommandHandler('authors', authors))
dispatcher.add_handler(CommandHandler('graph', graph, pass_args=True,
                                      pass_user_data=True))
dispatcher.add_handler(CommandHandler('nodes', nodes, pass_user_data=True))
dispatcher.add_handler(CommandHandler('edges', edges, pass_user_data=True))
dispatcher.add_handler(CommandHandler('components', components,
                                      pass_user_data=True))
dispatcher.add_handler(CommandHandler('plotgraph', plotgraph,
                                      pass_user_data=True))
dispatcher.add_handler(CommandHandler('route', route, pass_args=True,
                                      pass_user_data=True))
dispatcher.add_handler(CommandHandler('distribute', distribute, pass_args=True,
                                      pass_user_data=True))
updater.start_polling()
