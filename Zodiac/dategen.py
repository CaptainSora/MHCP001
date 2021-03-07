from datetime import datetime, timedelta
from random import randint

def random_day():
    """
    Returns a datetime object. For testing purposes only.
    """
    return datetime.now() + timedelta(days=randint(-10000, 10000))
