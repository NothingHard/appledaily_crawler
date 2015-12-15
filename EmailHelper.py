#coding: utf-8
import smtplib
from email.mime.text import MIMEText


class EmailHelper:
    @staticmethod
    def send(subject, emailBody):
        pw = "nJ442**YCEUk$@r2m!S^WZwahB3^cVtfKXP!"
        user = "mmnet602"
        #define variables
        textfile = 'email_message.txt'
        smtp_server = 'smtp.gmail.com'
        fromAddr = 'mmnet602@gmail.com'
        toAddr = fromAddr


        # # Open a plain text file for reading.  For this example, assume that
        # # the text file contains only ASCII characters.
        # fp = open(textfile, 'rb')
        # # Create a text/plain message
        # msg = MIMEText(fp.read())
        # fp.close()

        msg = MIMEText(emailBody)
        msg['Subject'] = subject
        msg['From'] = fromAddr
        msg['To'] = toAddr

        smtp = smtplib.SMTP('smtp.gmail.com', 587)
        smtp.ehlo()
        smtp.starttls()
        smtp.ehlo()
        smtp.login(user, pw)
        smtp.sendmail(fromAddr, [toAddr], msg.as_string())
        smtp.quit()
