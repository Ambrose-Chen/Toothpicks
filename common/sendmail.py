import smtplib
import logging
from email.mime.text import MIMEText

import sys
import os
directory = os.path.split(os.path.realpath(__file__))[0]
sys.path.append(os.path.join(directory, '..'))
from config import get_config


mail_smtp = get_config()['mail']["smtp_addr"]
mail_user = get_config()['mail']["user"]
mail_pass = get_config()['mail']["pass"]
sender = get_config()['mail']["sender"]
receivers = get_config()['mail']["receivers"]


def send_mail(title, context):
    message = MIMEText(context, 'plain', 'utf-8')
    message['Subject'] = title
    message['From'] = sender
    message['To'] = ','.join(receivers)

    try:
        smtpObj = smtplib.SMTP()
        smtpObj.connect(mail_smtp, 25)
        smtpObj.login(mail_user, mail_pass)
        smtpObj.sendmail(
            sender, receivers, message.as_string()
        )
        smtpObj.quit()
        logging.info(f'Mail sent successfully')
    except Exception as e:
        logging.error(f'Mail delivery failure')
        logging.error(e)
