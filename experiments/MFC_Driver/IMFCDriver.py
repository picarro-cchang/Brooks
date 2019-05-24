from abc import ABC, abstractmethod


class IMFCDriver(ABC):

    @abstractmethod
    def connect(self):
        pass

    @abstractmethod
    def send(self, command):
        pass

    @abstractmethod
    def close(self):
        pass

