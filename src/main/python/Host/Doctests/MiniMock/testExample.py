# Example function to be tested using minimock

import smtplib

def send_email(from_addr, to_addr, subject, body):
    conn = smtplib.SMTP('localhost')
    msg = 'To: %s\nFrom: %s\nSubject: %s\n\n%s' % (to_addr,from_addr,subject,body)
    conn.sendmail(from_addr,[to_addr],msg)
    conn.quit()

def get_open_file(filename):
    return open(filename,"w")

# Class which is to be tested

class MyClass(object):
    def method1(self,number):
        number += 4
        number **= 0.5
        number *= 7
        return number

    def method2(self,number):
        return ((number * 2) ** 1.27) * 0.3

    def method3(self,number):
        return self.method1(number) + self.method2(number)

    def method4(self):
        return self.method3(id(self))
