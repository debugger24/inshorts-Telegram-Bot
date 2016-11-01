from urllib import *
from urllib.request import urlopen
from bs4 import BeautifulSoup
import sqlite3
from telegram.ext import Updater
import logging
from telegram.ext import CommandHandler
import datetime
import re
import os

API_KEY = ""

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
        imageLink = (news.contents[1]['style'])
        imageLink = re.findall('(https.+jpg)', imageLink)[0]
        time = (news.contents[3].div.find_all("span")[2].string)
        date = (news.contents[3].div.find_all("span")[3].string)
        title = (news.contents[3].a.span.string)
        content = ((news.contents[5].find_all("div")[0].string))
        datetime = time + " " + date
        cur.execute('''SELECT Title FROM News WHERE Title = ? OR Content = ?''', (title, content))
        row = cur.fetchone()
        if row is None:
            cur.execute('''INSERT INTO News (Timestamp, Title, Content, Image) VALUES ( ?, ?, ?, ? )''', (datetime , title, content, imageLink ))
            count += 1
        conn.commit()

    print ("Total news written to database : ", count)

    cur.close()

def checkUserLastNews(chat_id):
    conn = sqlite3.connect('inshorts.db')
    cur = conn.cursor()
    cur.execute('SELECT LastNewsID FROM Users WHERE ChatID = ?', (chat_id, ))
    row = cur.fetchone()
    if row is None:
        cur.execute('INSERT INTO Users (ChatID, LastNewsID) VALUES (? , ?)', (chat_id, 1))
        LastReadNewsID = 1
        print ("\nNew User :", chat_id, "\nLast Read News ID =", LastReadNewsID)
    else:
        LastReadNewsID = row[0]
        print ("\nOld User :", chat_id, "\nLast Read News ID =", LastReadNewsID)
    conn.commit()
    cur.close()
    return LastReadNewsID

def checkTodayFirstNewsID():
    conn = sqlite3.connect('inshorts.db')
    cur = conn.cursor()
    now = datetime.datetime.now()
    date = now.strftime("%d %b %Y")
    likeDate = "%" + date + "%"
    cur.execute('''SELECT ID FROM News WHERE Timestamp LIKE ? ORDER BY ID ASC LIMIT 1''', (likeDate, ))
    row = cur.fetchone()
    if row is None:
        TodayFirstNewsID = 0
        print ("\nToday First News :", "No news")
    else:
        TodayFirstNewsID = row[0]
        print ("\nToday First News :", TodayFirstNewsID)
    cur.close()
    return TodayFirstNewsID

def getNews(LastReadNewsID, chat_id):
    conn = sqlite3.connect('inshorts.db')
    cur = conn.cursor()
    print (LastReadNewsID)
    cur.execute("SELECT ID, Timestamp, Title, Content, Image FROM News WHERE ID > ? ORDER BY ID ASC LIMIT 1", (LastReadNewsID, ))
    row = cur.fetchone()
    if row is None:
        news = "You have already read all new news."
    else:
        news = row[1] + "\n\n" + row[2] + "\n\n" + row[3]
        image = row[4]
        cursor = conn.execute("UPDATE Users SET `LastNewsID` = ? WHERE ChatID = ?", (row[0], chat_id))
    conn.commit()
    cur.close()
    return (news,image)

def today(bot, update):
    fetchNews()


    # Check if user exists
    chat_id = update.message.chat_id

    LastReadNewsID = checkUserLastNews(chat_id)
    TodayFirstNewsID = checkTodayFirstNewsID()

    if(TodayFirstNewsID == 0):
        news = "No news for today."
    elif(LastReadNewsID < TodayFirstNewsID):
        LastReadNewsID = TodayFirstNewsID

    if(TodayFirstNewsID != 0):
        news,image = getNews(LastReadNewsID, chat_id)

    bot.sendPhoto(chat_id=chat_id, photo=image)
    bot.sendMessage(chat_id, news)


updater = Updater(token=API_KEY)
dispatcher = updater.dispatcher
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
today_handler = CommandHandler('today', today)
dispatcher.add_handler(today_handler)
updater.start_polling()
