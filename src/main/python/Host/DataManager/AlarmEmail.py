from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
import smtplib
COMMASPACE = ', '

class AlarmEmail(object):
    def __init__(self, toAddrList=["alee@picarro.com"], fromAddr="alee@picarro.com"):
        self.smtpHostname = "woodstock.blueleaf.com"
        self.toAddrList = toAddrList
        self.fromAddr = fromAddr

    def sendMsg(self, subject="Message from CRDS", msg="This is a testing alarm message"):
        msg = MIMEText(msg)
        outer = MIMEMultipart()
        outer['Subject'] = subject
        outer['To'] = COMMASPACE.join(self.toAddrList)
        outer['From'] = self.fromAddr
        outer.attach(msg)
        mailServer = smtplib.SMTP(self.smtpHostname)
        mailServer.sendmail(self.fromAddr, self.toAddrList, outer.as_string())