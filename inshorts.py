from urllib import *
from urllib.request import urlopen
from bs4 import BeautifulSoup
import sqlite3
from telegram.ext import Updater
import logging
from telegram.ext import CommandHandler

def fetchNews():
    conn = sqlite3.connect('inshorts.db')
    cur = conn.cursor()

    fhand = urlopen('https://www.inshorts.com/read')
    webpgstr = fhand.read()
    soup = BeautifulSoup(webpgstr, "lxml")

    news_collection = soup.find_all("div", attrs={"class": "news-card z-depth-1"})

    print ("Total news found : ", len(news_collection))

    count = 0

    news_collection.reverse()

    for news in news_collection:
        time = (news.contents[3].div.find_all("span")[2].string)
        date = (news.contents[3].div.find_all("span")[3].string)
        title = (news.contents[3].a.span.string)
        content = ((news.contents[5].find_all("div")[0].string))
        datetime = time + " " + date
        cur.execute('''SELECT Title FROM News WHERE Title = ? OR Content = ?''', (title, content))
        row = cur.fetchone()
        if row is None:
            cur.execute('''INSERT INTO News (Timestamp, Title, Content) VALUES ( ?, ?, ? )''', (datetime , title, content ))
            count += 1
        conn.commit()

    print ("Total news written to database : ", count)

    cur.close()

def today(bot, update):
    fetchNews()
    conn = sqlite3.connect('inshorts.db')
    cursor = conn.execute("SELECT Timestamp, Title, Content from News ORDER BY ID DESC LIMIT 5")
    for row in cursor:
        news = row[0] + "\n\n" + row[1] + "\n\n" + row[2]
        print (news)
        bot.sendMessage(chat_id=update.message.chat_id, text=news)


updater = Updater(token='TOKEN KEY')
dispatcher = updater.dispatcher
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
today_handler = CommandHandler('today', today)
dispatcher.add_handler(today_handler)
updater.start_polling()
