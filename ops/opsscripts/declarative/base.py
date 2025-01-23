import typing as t


class Declarative(t.Protocol):
    def current(self):
        pass

    def desired(self):
        pass
