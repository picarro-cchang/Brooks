#!/usr/bin/python
"""
File Name: EmailSender.py
Purpose: Sends e-mails (optionally with attachments) to a list of receipients

File History:
    23-Dec-2013  sze   Initial Version

Copyright (c) 2013 Picarro, Inc. All rights reserved
"""
from email import encoders
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from email.mime.text import MIMEText
import mimetypes
import os
import smtplib

boolDict = {'1': True, 'yes': True, 'true': True, 'on': True,
            '0': False, 'no': False, 'false': False, 'off': False}
        
def toBoolean(value):
    """Converts value (string) into a Boolean.
    
    The keys in boolDict are the (lower-case) allowed values
    """
    value = value.strip().lower()
    if value not in boolDict:
        raise ValueError("%s is not a boolean" % value)
    else:
        return boolDict[value]

class EmailSender(object):
    """Sender for e-mail messages with optional attachments.
    """
    def __init__(self, settings):
        assert 'Username' in settings, "Username not set in EmailSender"
        assert 'Server' in settings, "SMTP server not set in EmailSender"
        self.settings = settings
        self.toAddrList = []
        self.setupDefaults()
        
    def setupDefaults(self):
        if 'Port' not in self.settings:
            self.settings['Port'] = 465
        if 'UseSSL' not in self.settings:
            self.settings['UseSSL'] = 'no'
        if 'UseAuthentication' not in self.settings:
            self.settings['UseAuthentication'] = 'no'
        if 'Password' not in self.settings:
            self.settings['Password'] = ''

        # Create list of receipient addresses
        toAddrList = []
        for key in self.settings:
            if key.startswith('Receipient'):
                toAddrList.append(self.settings[key])
        self.toAddrList = toAddrList
        
    def handleAttachments(self, attachments, outer):
        """Attach files to the message.
        
        Args:
            attachments: List of files to attach
            outer: MIMEMultipart wrapper for e-mail
        """
        assert isinstance(attachments, list), "Need to specify a list of attachments"
        assert isinstance(outer, MIMEMultipart)
        
        for path in attachments:
            _, filename = os.path.split(path)
            # Guess the content type based on the file's extension.  Encoding
            # will be ignored, although we should check for simple things like
            # gzip'd or compressed files.
            ctype, encoding = mimetypes.guess_type(path)
            if ctype is None or encoding is not None:
                # No guess could be made, or the file is encoded (compressed), so
                # use a generic bag-of-bits type.
                ctype = 'application/octet-stream'
            maintype, subtype = ctype.split('/', 1)
            if maintype == 'text':
                fp = open(path, 'r')
                # Note: we should handle calculating the charset
                msg = MIMEText(fp.read(), _subtype=subtype)
                fp.close()
            elif maintype == 'image':
                fp = open(path, 'rb')
                msg = MIMEImage(fp.read(), _subtype=subtype)
                fp.close()
            elif maintype == 'audio':
                fp = open(path, 'rb')
                msg = MIMEAudio(fp.read(), _subtype=subtype)
                fp.close()
            else:
                fp = open(path, 'rb')
                msg = MIMEBase(maintype, subtype)
                msg.set_payload(fp.read())
                fp.close()
                # Encode the payload using Base64
                encoders.encode_base64(msg)
            # Set the filename parameter
            msg.add_header('Content-Disposition', 'attachment', filename=filename)
            outer.attach(msg)    
        
    def sendMessage(self, subject, message=None, attachments=None):
        """Sends e-mail message to list of receipients.
        
        Args:
            subject: Subject of e-mail message
            message: Text of message
            attachments: List of files to be attached to the e-mail message
            
        Returns:
            list indicating receipients for whom the send succeeded
        """
        # Create the enclosing (outer) message
        fromAddr = self.settings['Username']
        if not self.toAddrList:
            return []
        
        outer = MIMEMultipart()
        outer['Subject'] = subject
        outer['To'] = ", ".join(self.toAddrList)
        outer['From'] = fromAddr
        outer.preamble = '\n'
        # To guarantee the message ends with a newline
        outer.epilogue = ''
        
        if message is not None:
            assert isinstance(message, (str, unicode))
            outer.attach(MIMEText(message))
    
        if attachments is not None:
            self.handleAttachments(attachments, outer)
        
        try:
            mailServer = smtplib.SMTP(self.settings['Server'], int(self.settings['Port']))
            if self.settings['UseSSL']:
                mailServer.ehlo()
                mailServer.starttls() 
                mailServer.ehlo()
            if self.settings['UseAuthentication']:
                mailServer.login(fromAddr, self.settings['Password'])
            failedReceipients = mailServer.sendmail(fromAddr, self.toAddrList, outer.as_string())
            mailServer.quit()
            successList = self.toAddrList[:]
            failedList = []
            for key in failedReceipients.keys():
                failedList.append(key)
                successList.remove(key)
        except smtplib.SMTPException:
            successList = []
        return successList