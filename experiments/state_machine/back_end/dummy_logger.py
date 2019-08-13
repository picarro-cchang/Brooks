class DummyLoggerClient:
    def __init__(self, client_name, verbose):
        self.client_name = client_name
        self.verbose = verbose

    def Log(self, message, level=0):
        if self.verbose:
            print(message)

    def debug(self, message):
        self.Log(message, level=10)

    def info(self, message):
        self.Log(message, level=20)

    def warning(self, message):
        self.Log(message, level=30)

    def error(self, message):
        self.Log(message, level=40)

    def critical(self, message):
        self.Log(message, level=50)
