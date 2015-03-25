# CeleryDemo
A brief working Celery application that sends incremental numbers to an email. 

The command to start up the Celery application is:
celery -A tasks worker --loglevel=info --beat
