from datetime import date, timedelta
from random import randint

def random_day():
    """
    Returns a date object. For testing purposes only.
    """
    return date.today() + timedelta(days=randint(-10000, 10000))
