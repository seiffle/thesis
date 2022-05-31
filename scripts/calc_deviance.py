#!/usr/bin/python3

"""Since we deal with large files and assume that not all input fits
into main memory, we read the files line by line and save only words
in the dictionary, which we have not seen twice yet. Values, which are
not needed anymore, will be deleted."""
import sys
largest_deviance = 0
dev_word = ""
dev_str = ""
wc = {}

path1 = sys.argv[1]
path2 = sys.argv[2]


def compare(word, val, num):
    global largest_deviance
    global wc
    global dev_word
    global dev_str

    val = int(val)
    if word in wc:
        dev = abs(wc[word]["count"] - val)
        if dev > largest_deviance:
            largest_deviance = dev
            dev_word = word
            if num == 1:
                dev_str = "{} vs {}".format(val, wc[word]["count"])
            else:
                dev_str = "{} vs {}".format(wc[word]["count"], val)
        del wc[word]
    else:
        wc[word] = {"count": val, "num": num}


wc_file1 = open(path1)
wc_file2 = open(path2)
line1 = wc_file1.readline().replace("\n", "")
line2 = wc_file2.readline().replace("\n", "")


while(wc_file1 or wc_file2):
    if line1:
        line1 = line1.split(":")
        compare(*line1, 1)
    if line2:
        line2 = line2.split(":")
        compare(*line2, 2)

    if wc_file1:
        line1 = wc_file1.readline().replace("\n", "")
        if not line1:
            wc_file1.close()
            wc_file1 = None
    if wc_file2:
        line2 = wc_file2.readline().replace("\n", "")
        if not line2:
            wc_file2.close()
            wc_file2 = None

# Process words, which only appear in one of the files
for word in wc:
    if wc[word]["count"] > largest_deviance:
        largest_deviance = wc[word]["count"]
        dev_word = word
        if wc[word]["num"] == 1:
            dev_str = "{} vs {}".format(wc[word]["count"], 0)
        else:
            dev_str = "{} vs {}".format(0, wc[word]["count"])

print("Word: " + dev_word)
print("Deviance: {}".format(largest_deviance))
print("Word counts: " + dev_str)
