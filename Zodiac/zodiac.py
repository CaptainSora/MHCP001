from dategen import random_day

def foo():
    somedate = random_day()
    print(somedate.day)
    print(somedate.month)
    print(somedate.year)

foo()
