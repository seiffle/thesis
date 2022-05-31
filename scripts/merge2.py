#!/usr/bin/python3

# Slightly modified version of merge that is easier to handle
# We keep the old version for compatibility reasons
# The new version takes a path prefix parameter and merges
#   every file that starts with this prefix
import glob
import sys

prefix = sys.argv[1] + "*"
paths = glob.glob(prefix)

def merge_file(word_dict, input_file):
    while(True):
        line = input_file.readline()
        line = line.replace("\n", "")
        if not line:
            return
        word, val = line.split(":")
        val = int(val)
        if not word in word_dict:
            word_dict[word] = val
        else:
            word_dict[word] += val

word_dict = {}
group = sys.argv[1]
for filename in paths:
    with open(filename) as input_file:
        merge_file(word_dict, input_file)
            
wc_list = [(k, v) for k, v in word_dict.items()]
result = sorted(wc_list, key=lambda x: x[1], reverse=True)

for line in result:
    print("{}:{}".format(line[0], line[1]))
