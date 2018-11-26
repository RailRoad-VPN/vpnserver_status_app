import calendar
from datetime import datetime


def random_with_n_digits(n):
    range_start = 10 ** (n - 1)
    range_end = (10 ** n) - 1
    from random import randint
    return randint(range_start, range_end)


def random_x(minX, maxX):
    import random
    return random.randint(minX, maxX)


def get_unixtime() -> int:
    d = datetime.utcnow()
    unixtime = calendar.timegm(d.utctimetuple())
    return unixtime