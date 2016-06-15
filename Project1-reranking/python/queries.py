import re
import os
import shutil

indexpath = "/home/ginger/Documents/IR/Project1-reranking/"
datapath = "/home/ginger/Documents/IR/IR2016/"

def makeQueries(path, dest, f,doprint):
    with open(path) as f2:
        content = f2.read()
    reg = "<num> Number: ([0-9]+) *\n<title> +(.*?)<desc>"
    reg = re.compile(reg, re.DOTALL)
    res = reg.findall(content)
    counter = 0
    min = 9999999999999999999
    max = -1
    for match in res:
        title = re.sub('([^\s\w]|_)+', "", match[1])
        title = title.rstrip()
        f.write("<query>\n")
        f.write("<number>" + match[0] + "</number>\n")
        f.write("<text>" + title + "</text>\n")
        f.write("</query>\n")
        counter += len(title)
        if len(title) < min:
            min = len(title)
        if len(title) > max:
            max = len(title)
    return ( counter,min,max)

def parseTrec_Eval(path,name,mu,trecoutput):
    with open (path,"r") as f:
        file = f.read()
    p5reg = re.compile("P_5\\s+all\\s+([0-9.]+)",re.IGNORECASE)
    p5 = p5reg.findall(file)[0]
    recipreg = re.compile("recip_rank\\s+all\\s+([0-9.]+)",re.IGNORECASE)
    recip = recipreg.findall(file)[0]
    trecoutput.write("\n" + name + "," + str(mu) + "," + recip + "," + p5 )
    print name, mu, recip, p5
    return recip,p5


def innerQuery(name, dest, count, mu,doprint,stopwords,trecoutput):
    with open(dest, "w") as f:
        f.write("<parameters>\n")
        f.write("<index>" + indexpath + name + "-index</index>\n")
        f.write("<runID>2016</runID>\n")
        f.write("<trecFormat>true</trecFormat>\n")
        f.write("<count>" + str(count) + "</count>\n")
        f.write("<rule>method:dir,mu:" + str(mu) + "</rule>\n")
        f.write("<stemmer>Krovetz</stemmer>")
        counter1, min1, max1 = makeQueries(datapath + "queries/topics.301-350", dest, f,doprint)
        counter2, min2, max2 = makeQueries(datapath + "queries/topics.351-400", dest, f,doprint)
        counter3, min3, max3 = makeQueries(datapath + "queries/topics.401-450", dest, f,doprint)
        f.write(stopwords)
        f.write("</parameters>\n")

        # Run query thingy bash file


    if doprint:
        counter = sum([counter1, counter2, counter3])
        minval = min([min1, min2, min3])
        maxval = max([max1, max2, max3])
        print "queries,150,", 1. * counter / 150, ",", minval, ",", maxval
        print "name,mu,k,recip,p5"
        trecoutput.write( "name,mu,k,recip,p5")
    #do indri stuff
    qrelsfile = "../qrels/qrels.txt"
    namefile = str(name) + str(mu) + "." + str(count)
    resfile = "../queries/results/" + namefile + ".txt"
    queryfile = "../queries/" + namefile + ".txt"
    trecfile = "../trec/" + namefile + ".txt"

    os.system( "IndriRunQuery " + queryfile + " > " + resfile)
    os.system( "../trec_eval " + qrelsfile + " " + resfile + " > " + trecfile)
    return parseTrec_Eval(trecfile, name + "," + str(count),mu,trecoutput)

def loadQueries(path):
    with open(path) as f:
        content = f.read()
    reg = "<num> Number: ([0-9]+) *\n<title> +(.*?)<desc>"
    reg = re.compile(reg, re.DOTALL)
    res = reg.findall(content)




    return res

def parseTitle(title,stopwords):
    res = re.sub('([^\s\w]|_)+', "", title)
    res = res.rstrip()
    res = res.split()
    res = " ".join([res for res in res if not res in stopwords])


    return res

def parsedQueries(stopwords):

    data = []
    data.extend(loadQueries(datapath + "queries/topics.301-350"))
    data.extend(loadQueries(datapath + "queries/topics.351-400"))
    data.extend(loadQueries(datapath + "queries/topics.401-450"))

    data = "\n".join([str(num) + "," + parseTitle(title,stopwords) for num,title in data])

    with open("../queries/parsedQueries.txt", "w") as f:
        f.write(data)

def mainQuery():
    base = "../queries/"
    doprint = True
    with open("../stopwords.txt","r") as f:
        stopwords = f.read()

    parsedQueries(stopwords)

    with open("../trec/result.txt","w") as trecoutput:
        for name in ["la", "ft", "fbis"]:
            for count in [20, 50]:
                results = []
                mus = [1000, 1500, 2000, 2500, 3000]
                for mu in mus:
                    #recip,p5
                    res = innerQuery(name, base + name + str(mu) + "." + str(count) + ".txt", count,mu ,doprint,stopwords,trecoutput)
                    doprint = False
                    results.append(res)
                best = 0
                bestloc = 0
                for i,(_,p5) in enumerate(results):
                    if p5 > best:
                        best = i
                shutil.copy("../queries/results/" + name + str(mus[best]) + "." + str(count) + ".txt","../queries/results/best/" + name  + str(count) + ".txt" )
                #shutil.copy("../trec/" + name + str(mus[i]) + "." + str(count) + ".txt","../trec/best/" + name  + str(count) + ".txt" )


def mainQrels():
    result = ""
    base = "../../IR2016/qrels/"
    for fn in sorted(os.listdir(base)):
        with open(base + fn) as f:
            result += f.read()
    with open("../qrels/qrels.txt", "w") as f:
        f.write(result[:-1])


if __name__ == "__main__":
    mainQrels()
    mainQuery()
