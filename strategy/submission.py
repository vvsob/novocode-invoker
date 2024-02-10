import datetime
from strategy.executable import Compilable


class Submission:
    def __init__(self, source: Compilable, timestamp: datetime.datetime, author: str):
        self.source = source
        self.timestamp = timestamp
        self.author = author
