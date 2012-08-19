notset = object()
	 
class MonkeyPatch:
    def __init__(self):
        self._setattr = []
        self._setitem = []

    def setattr(self, obj, name, value):
        self._setattr.insert(0, (obj, name, getattr(obj, name, notset)))
        setattr(obj, name, value)
 
    def setitem(self, dictionary, name, value):
        self._setitem.insert(0, (dictionary, name, dictionary.get(name, notset)))
        dictionary[name] = value
 
    def finalize(self):
        for obj, name, value in self._setattr:
            if value is not notset:
                setattr(obj, name, value)
            else:
                delattr(obj, name)
        for dictionary, name, value in self._setitem:
            if value is notset:
                del dictionary[name]
            else:
                dictionary[name] = value
	 
def func():
    return "Real function"

def target():
    return func()

if __name__ == "__main__":
    print target()
    monkeypatch = MonkeyPatch()
    monkeypatch.setitem(globals(), 'func', lambda:"Mock function")
    print target()
    monkeypatch.finalize()
    print target()