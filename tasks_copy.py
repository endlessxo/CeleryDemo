from celery import Celery
import datetime
import celery

import smtplib

import imaplib
import time
import uuid
from email import email
import string 
 
 
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
 
    def get_count(self):
        self.imap.select('Inbox')
        status, data = self.imap.search(None, 'ALL')
        return sum(1 for num in data[0].split())
 
    def fetch_message(self, num):
        self.imap.select('Inbox')
        status, data = self.imap.fetch(str(num), '(RFC822)')
        email_msg = email.message_from_string(data[0][1])
        return email_msg
 
    def delete_message(self, num):
        self.imap.select('Inbox')
        self.imap.store(num, '+FLAGS', r'\Deleted')
        self.imap.expunge()
 
    def delete_all(self):
        self.imap.select('Inbox')
        status, data = self.imap.search(None, 'ALL')
        for num in data[0].split():
            self.imap.store(num, '+FLAGS', r'\Deleted')
        self.imap.expunge()
 
    def print_msgs(self):
        self.imap.select('Inbox')
        status, data = self.imap.search(None, 'ALL')
        for num in reversed(data[0].split()):
            status, data = self.imap.fetch(num, '(RFC822)')
            print 'Message %s\n%s\n' % (num, data[0][1])

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

    def print_unread_msgs(self):
        
        self.imap.select('Inbox')
        status, data = self.imap.search(None, '(UNSEEN)')
        for num in data[0].split():
            status, data = self.imap.fetch(num, '(RFC822)')
            #print 'Message %s\n%s\n' % (num, data[0][1])          
            #print self.parse_data(data[0][1]) 
            self.unread_email.append(self.parse_data(data[0][1]))


    def get_latest_email_sent_to(self, email_address, timeout=300, poll=1):
        start_time = time.time()
        while ((time.time() - start_time) < timeout):
            # It's no use continuing until we've successfully selected
            # the inbox. And if we don't select it on each iteration
            # before searching, we get intermittent failures.
            status, data = self.imap.select('Inbox')
            if status != 'OK':
                time.sleep(poll)
                continue
            status, data = self.imap.search(None, 'TO', email_address)
            data = [d for d in data if d is not None]
            if status == 'OK' and data:
                for num in reversed(data[0].split()):
                    status, data = self.imap.fetch(num, '(RFC822)')
                    email_msg = email.message_from_string(data[0][1])
                    return email_msg
            time.sleep(poll)
        raise AssertionError("No email sent to '%s' found in inbox "
             "after polling for %s seconds." % (email_address, timeout))
 
    def delete_msgs_sent_to(self, email_address):
        self.imap.select('Inbox')
        status, data = self.imap.search(None, 'TO', email_address)
        if status == 'OK':
            for num in reversed(data[0].split()):
                status, data = self.imap.fetch(num, '(RFC822)')
                self.imap.store(num, '+FLAGS', r'\Deleted')
        self.imap.expunge()

app = Celery('tasks', broker='amqp://guest@localhost//')

@app.task
def add(x, y):
    return x + y

#@celery.decorators.periodic_task(run_every=datetime.timedelta(seconds=1))
#def myfunc():   
#    return datetime.datetime.now().time()

globvar = 0

@celery.decorators.periodic_task(run_every=datetime.timedelta(seconds=5))
def foofunc():
    #imap_username = 'abcd'
    #imap_password = 'abcd'
    imap_username = 'bostonunderwater@gmail.com'
    imap_password = 'Yahtzee2012'    
    fromaddr = imap_username
    toaddrs = imap_username
    
    global globvar
    globvar = globvar + 1
    msg = str(globvar)
    server = smtplib.SMTP('smtp.gmail.com:587')
    server.starttls()
    server.login(imap_username, imap_password)
    server.sendmail(fromaddr, toaddrs, msg)
    server.quit()
    
    with MailBox(imap_username, imap_password) as mbox:
	return "There are " + str(mbox.get_count()) + " unread emails!"
        #mbox.print_unread_msgs()
        #print mbox.unread_email    

globbar = 7777

@celery.decorators.periodic_task(run_every=datetime.timedelta(seconds=10))
def barfunc():
    imap_username = 'bostonunderwater@gmail.com'
    imap_password = 'Yahtzee2012'
    fromaddr = imap_username
    toaddrs = imap_username

    global globbar
    globbar = globbar + 1000
    msg = str(globbar) 
    server = smtplib.SMTP('smtp.gmail.com:587')
    server.starttls()
    server.login(imap_username, imap_password)
    server.sendmail(fromaddr, toaddrs, msg)
    server.quit()

    
