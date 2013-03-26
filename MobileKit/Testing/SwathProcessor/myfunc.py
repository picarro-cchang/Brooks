import os.path
def getssh(): # pseudo application code
    return os.path.join(os.path.expanduser("~admin"), '.ssh')

def func():
    return "Real function"

def target():
    return func()

def test_mytest(monkeypatch):
    def mockreturn(path):
        return '/abc'
    monkeypatch.setattr(os.path, 'expanduser', mockreturn)
    x = getssh()
    assert x == '/abc\\.ssh'
    
def test_target(monkeypatch):
    monkeypatch.setitem(globals(),'target',lambda: 'Mock function')
    assert target() == "Mock function"
    monkeypatch.undo()
    assert target() == "Real function"
