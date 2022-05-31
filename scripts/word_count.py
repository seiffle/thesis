#!/usr/bin/python3
import sys

if len(sys.argv) > 1:
    path = sys.argv[1]
else:
    path = "input.txt"

word_count = {}

with open(path) as input_file:
    word = input_file.readline()
    while word:
        word = word.replace('\n', '')
        if word not in word_count:
            word_count[word] = 1
        else:
            word_count[word] += 1
        word = input_file.readline()

for k, v in word_count.items():
    print("{}:{}".format(k, v))
