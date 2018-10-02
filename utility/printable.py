class Printable:
    """Base class implementing printing"""
    def __repr__(self):
        return str(self.__dict__)