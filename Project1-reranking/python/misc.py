import re
import os

if __name__ == "__main__":
    base = "../trec/"
    for fn in os.listdir(base):
        with open(base + fn) as f:
            res = f.read()
        reg = re.compile("P_5\\s+all\\s+([\\d.]+)")
        print reg.findall(res)[0]