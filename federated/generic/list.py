class List:

    def __init__(self):
        self.list = []

    def append(self, item):
        self.append(item)

    def first(self):
        return self.list[0]

    def last(self):
        return self.list[-1]

    def count(self):
        return len(self.list)

    def __repr__(self):
        return str(self.list)
