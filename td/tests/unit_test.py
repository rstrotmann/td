from td.td import *

def convert_bool(input):
    return([1 if i else 0 for i in input])


def test_leading_trailing_edge():
    data = [False, False, True, True, True, False, True, False, False]
    print()
    print(f'input:    {convert_bool(data)}')
    print(f'leading:  {convert_bool(leading_edge(data))}')
    print(f'trailing: {convert_bool(trailing_edge(data))}')
