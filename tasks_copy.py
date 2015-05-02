from celery import Celery
import datetime
import celery

import smtplib
import time

import imaplib
import uuid
from email import email
import string
from datetime import datetime
from datetime import *
import psycopg2 
 

IMAP_SERVER = 'imap.gmail.com'
IMAP_PORT = '993'
IMAP_USE_SSL = True
 
 
 
class MailBox(object):
    def __init__(self, user, password):
        self.user = user
        self.password = password
        self.unread_email = []
        if IMAP_USE_SSL:
            self.imap = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
        else:
            self.imap = imaplib.IMAP4(IMAP_SERVER, IMAP_PORT)
    def __enter__(self):
        self.imap.login(self.user, self.password)
        return self
    def __exit__(self, type, value, traceback):
        self.imap.close()
        self.imap.logout()         

    def get_all_count(self):
        self.imap.select('Inbox')
        status, data = self.imap.search(None, 'ALL')
        return sum(1 for num in data[0].split())
    #Note, this does not read the email, it just gives you the number of unread emails.    
    def get_unread_count(self):
        self.imap.select('Inbox')
        status, data = self.imap.search(None, 'UNSEEN')
        return sum(1 for num in data[0].split())

    #Excuse my poor coding
    def parse_data(self, foo):
        kungfoo = foo.split()
        flag = False
        doge = ''
        for word in kungfoo:
            if word == '--':
                flag = False
            if flag:
                doge = doge + (word + ' ')
            if word == 'delsp=yes':
                flag = True
        return doge

    #Note, this actually reads the email and turns unread emails to read emails.
    def append_unread_msgs(self):
        self.imap.select('Inbox')
        status, data = self.imap.search(None, '(UNSEEN)')
        for num in data[0].split():
            status, data = self.imap.fetch(num, '(RFC822)')
            #print 'Message %s\n%s\n' % (num, data[0][1])          
            #print self.parse_data(data[0][1]) 
            self.unread_email.append(self.parse_data(data[0][1]))

class Converter(object):
    def __init__(self, email):
        self.message = {}
        self.inputstream = []
        for x in email.split():
            self.inputstream.append(x)
        #If the list inputstream is not empty...
        if self.inputstream: 
            self.create_dictionary()

        
    #Given inputs like: Red 181 Green 48 Blue 8 Lat 0.0 Long 0.0 Date Mar 30, 2015 4:29:37 PM ID a0000034a6193f
    def create_dictionary(self):    
        self.message[self.inputstream[0]] = self.inputstream[1]
        self.message[self.inputstream[2]] = self.inputstream[3]
        self.message[self.inputstream[4]] = self.inputstream[5]
        self.message[self.inputstream[6]] = self.inputstream[7]
        self.message[self.inputstream[8]] = self.inputstream[9]
        self.message[self.inputstream[10]] = self.inputstream[11:16] 
        self.message[self.inputstream[16]] = self.inputstream[17]
        self.message['Color'] = self.inputstream[1] + " " + self.inputstream[3] + " " + self.inputstream[5]

    #Source: http://stackoverflow.com/questions/3418050/month-name-to-month-number-and-vice-versa-in-python
    def monthToNum(self, date):
        return{
                'Jan' : '01',
                'Feb' : '02',
                'Mar' : '03',
                'Apr' : '04',
                'May' : '05',
                'Jun' : '06',
                'Jul' : '07',
                'Aug' : '08',
                'Sep' : '09', 
                'Oct' : '10',
                'Nov' : '11',
                'Dec' : '12',
        } [date]

    def to24Hours(self, time):
        return str(datetime.strptime(time, '%I:%M:%S %p').time())


    def get_proper_datetime_syntax(self):
        #2015/02/07 16:51.01
        foo = self.message['Date'][2] + '/' + self.monthToNum(self.message['Date'][0]) + '/' + self.message['Date'][1][:-1] + " " + self.to24Hours(" ".join(self.message['Date'][3:]))
        return foo

    def get_insert_sql_query(self):
        print "Message Dict - ", self.message
        self.query = ""
        try:
            self.query = self.query + "INSERT INTO bostonunderwater_beacon (latitude, longitude, water_level, node_number, time) VALUES (" + self.message['Lat'] + ", " + self.message['Long']  + ", " + ColorAnalyzerInt(self.message['Color']).get_water_level() + ", '" + self.message['ID'] + "', '" + self.get_proper_datetime_syntax() + "')"         
        except:
            self.query = "Invalid"
        print "Query - ", self.query
        return self.query


    def print_message(self):
        print "Message Dict - ", self.message



class Database(object):
    def __init__(self, request):
        try:
                self.conn = psycopg2.connect("dbname='django' user='django' host='localhost' password='EBmpfDB8NN'")
        except:
                print "I am unable to connect to the database"
        self.cur = self.conn.cursor()
        self.querymessage = []
        for x in request.split():
            self.querymessage.append(x)
        try:
            if self.querymessage[0] == "INSERT":
                self.insert_query(request)
            if self.querymessage[0] == "SELECT":
                self.select_query(request)
        except:
            print "You do not have a valid query."


    def select_query(self, payload):
        try:
            self.cur.execute("""{}""".format(payload))
            self.rows = self.cur.fetchall()
            self.dict = {}
            for self.row in self.rows:
                self.dict[self.row[0]] = {'latitude' : str(self.row[1]), 'longitude' : str(self.row[2]), 'time' : str(self.row[3]), 'water_level' : str(self.row[4]), 'node_number' : str(self.row[0])}             
            print self.dict     
        except:
            return False
        return True

    def insert_query(self, payload):
        try:
            self.cur.execute("{}".format(payload))
            self.conn.commit()
            print "Inserted!"
        except:
            return False
        return True

    def update_query(self, payload):
        return True

# print ColorAnalyzerInt("10 20 30").get_water_level()
class ColorAnalyzerInt(object):
    def __init__(self, stream):  
        self.colors = {}
        self.inputstream = []
        for x in stream.split():
            self.inputstream.append(x)
        if self.inputstream:
            self.create_dictionary()
    def create_dictionary(self):
        self.colors['Red'] = self.inputstream[0]
        self.colors['Green'] = self.inputstream[1]
        self.colors['Blue'] = self.inputstream[2]

    def print_colors(self):
        print "Color Dict - ", self.colors
        
    #Note: This below function wasted 30 minutes of my life. MAKE SURE YOU CAST THE STRING => INT or else you get funky comparisons, like '8' > '181' according to Python. >=[
    def get_water_level(self):
        # print "Color Dict - ", self.colors    
        if int(self.colors['Red']) > int(self.colors['Blue']) and int(self.colors['Red']) > int(self.colors['Green']):
            return "1"
        if int(self.colors['Blue']) > int(self.colors['Red']) and int(self.colors['Blue']) > int(self.colors['Green']):
            return "2"
        if int(self.colors['Green']) > int(self.colors['Blue']) and int(self.colors['Green']) > int(self.colors['Red']):
            return "3"

class ColorAnalyzerHex(object):
    def __init__(self, inputhex):  
        self.hex_value = inputhex
    def get_RGB(self):
        self.value = self.hex_value.lstrip('#')
        self.lv = len(self.value)
        return tuple(int(self.value[i:i + self.lv // 3], 16) for i in range(0, self.lv, self.lv // 3))
    def get_dominant_primary_color(self):
        self.color_tuple = self.get_RGB()
        self.highest_number = max(self.color_tuple)
        if self.color_tuple[0] == self.highest_number:
            return "Red"
        elif self.color_tuple[1] == self.highest_number:
            return "Green"
        elif self.color_tuple[2] == self.highest_number:
            return "Blue"

app = Celery('tasks', broker='amqp://guest@localhost//')
@app.task
def add(x, y):
    return x + y

#@celery.decorators.periodic_task(run_every=datetime.timedelta(seconds=1))
#def myfunc():   
#    return datetime.datetime.now().time()

# globvar = 0

@celery.decorators.periodic_task(run_every=datetime.timedelta(seconds=5))
def foofunc():
    imap_username = 'bostonunderwater@gmail.com'
    imap_password = 'Yahtzee2012'    
    with MailBox(imap_username, imap_password) as mbox:
        print "there are " + str(mbox.get_unread_count()) + " unread emails!"
        print "there are " + str(mbox.get_all_count()) + " emails!"
        mbox.append_unread_msgs()
        for i in mbox.unread_email:
            foo = Converter(i)
            foo.get_insert_sql_query()
            try:
                Database(foo.get_insert_sql_query())
            except:
                print "Failed"
# globbar = 7777

# @celery.decorators.periodic_task(run_every=datetime.timedelta(seconds=10))
# def barfunc():
#     imap_username = 'bostonunderwater@gmail.com'
#     imap_password = 'Yahtzee2012'
#     fromaddr = imap_username
#     toaddrs = imap_username

#     global globbar
#     globbar = globbar + 1000
#     msg = str(globbar) 
#     server = smtplib.SMTP('smtp.gmail.com:587')
#     server.starttls()
#     server.login(imap_username, imap_password)
#     server.sendmail(fromaddr, toaddrs, msg)
#     server.quit()

    
