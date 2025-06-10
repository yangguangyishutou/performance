import json 
import os
import math


def transform():
    with open('tokens.json', 'r') as f:
        j = json.load(f)
    for item in j:
        # item['probability'] =  floor(item['probability'], 2)
        item['probability'] =  "{:.2f}".format(math.floor(item['probability'] * 100) / 100)

    with open('tokens2.json', 'w') as f:
        json.dump(j, f, indent=4)


def printm():
    with open('tokens2.json', 'r') as f:
        j = json.load(f)
    for item in j:
        print(item['token'] + " "+ str(item['probability']))

# transform()
printm()
















Ġenumerate 0.97
i 0.88
, 0.87
[ 0.85
Ġself 0.73
( 0.13
for 0.12
Ġadd 0.00
Ġrow 0.00
max_col_size X.XX


