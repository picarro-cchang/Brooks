import subprocess

while True:
    #p = subprocess.Popen([r'c:\python27\scripts\nosetests.exe','-s','-v','testProjectSupport.py:TestWorker'])
    p = subprocess.Popen(['py.test.exe','-v','testProjectSupport.py'])
    if p.wait(): break
p.terminate()    