import re
import os
from scipy.stats.stats import pearsonr,spearmanr
import numpy as np



def mad(arr):
    arr = np.ma.array(arr).compressed() # should be faster to not use masked arrays.
    med = np.median(arr)
    return np.median(np.abs(arr - med))

def makeQueries(path, dest, f,doprint):
    with open(path) as f2:
        content = f2.read()
    reg = "<num> Number: ([0-9]+) *\n<title> +(.*?)<desc>"
    reg = re.compile(reg, re.DOTALL)
    res = reg.findall(content)
    counter = 0
    min = 9999999999999999999
    max = -1
    wordcount = []
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
        wordcount.append(len(title.rsplit()))
    return ( counter,min,max,wordcount)

def parseTrec_Eval(path,name,trecoutput):
    with open (path,"r") as f:
        file = f.read()
    p10reg = re.compile("P_10\\s+([0-9]+)\\s+([0-9.]+)",re.IGNORECASE)
    p10 = p10reg.findall(file)

    p10 = [float(current[1]) for current in p10]
    return p10

def applyCut(pathin,pathout,count,cut,fun,normalized):
    sds = []
    result = []
    with open(pathin) as f:
        file = f.readlines()
    with open("../queries/parsedQueries.txt") as f:
        queries = f.readlines()
        queries = [query.split(",")[1] for query in queries]
        querylens = [len(query.split(" ")) for query in queries]



    file = [line.split() for line in file]
    for i,query in enumerate( range(301,451)):
        current = str(query)
        res = [line for line in file if line[0] == current]
        # no result
        if len(res) == 0:
            #sds.append(0)
            continue
        scores = [float(line[4]) for line in res ]
        #above cut
        maxscore = max(scores)
        scores = [score for score in scores if score >= maxscore*cut]
        sd = fun(np.array(scores))
        if normalized:
            sd = sd/querylens[i]
        sds.append(sd)
        overCut = [" ".join(line) for line in res if line[4] >= maxscore * cut]

        result.extend(overCut)
    with open(pathout, "w") as f:
        f.write("\n".join(result))
    #maxsd = max(sds)
    #sds = [sd/maxsd for sd in sds]
    #sds = sds/querylens
    return sds



def innerQuery(name, dest, count, doprint,stopwords,trecoutput,sorm,normalized):
    with open(dest, "w") as f:
        f.write("<parameters>\n")
        f.write("<index>/home/ginger/Documents/IR/Project2-qpp/" + name + "-index</index>\n")
        f.write("<runID>2016</runID>\n")
        f.write("<trecFormat>true</trecFormat>\n")
        f.write("<stemmer>Krovetz</stemmer>\n")
        f.write("<count>" + str(count) + "</count>\n")
        f.write("<baseline>okapi,k1:1.2,b:0.75,k3:7</baseline>\n")
        counter1, min1, max1, wcount1 = makeQueries("../../IR2016/queries/topics.301-350", dest, f,doprint)
        counter2, min2, max2, wcount2 = makeQueries("../../IR2016/queries/topics.351-400", dest, f,doprint)
        counter3, min3, max3, wcount3 = makeQueries("../../IR2016/queries/topics.401-450", dest, f,doprint)
        f.write(stopwords)
        f.write("</parameters>\n")

    wordcounts = wcount1
    wordcounts.extend(wcount2)
    wordcounts.extend(wcount3)

    if doprint:
        counter = sum([counter1, counter2, counter3])
        minval = min([min1, min2, min3])
        maxval = max([max1, max2, max3])
        print "queries,150,", 1. * counter / 150, ",", minval, ",", maxval
        #trecoutput.write( "name,k,recip,p10")
    #do indri stuff
    qrelsfile = "../qrels/qrels.txt"
    namefile = str(name) + str(count)
    resfile = "../queries/results/" + namefile + ".txt"
    queryfile = "../queries/" + namefile + ".txt"
    if sorm:
        fun = mad
        namefile = "MAD" + namefile
    else:
        fun = np.std

    os.system( "IndriRunQuery " + queryfile + " > " + resfile)
    correlations0 = "Pearsons "
    correlations1 = "Spearman "
    for cut in np.arange(0.1,1,0.2):
        newresfile = "../queries/results/" + namefile + "." + str(cut) + ".txt"
        trecfile = "../trec/" + namefile  + "." + str(cut) + ".txt"
        sds = applyCut(resfile,newresfile,count,cut,fun,normalized)
        os.system( "../trec_eval -q " + qrelsfile + " " + newresfile + " > " + trecfile)
        p10s = parseTrec_Eval(trecfile, name + "," + str(count),trecoutput)
        correlations0 += " & " + str(round(pearsonr(sds,p10s)[0],4))
        correlations1 += " & " + str(round(spearmanr(sds, p10s)[0],4))

    lineending = " \\\\ \\hline"
    print '''\\begin{table}[h!]
\\centering
\\begin{tabular}{|l|l|l|l|l|l|}
\\hline'''
    print name + " " + str(count ) + " & $\sigma_{0.1\%}$ & $\sigma_{0.3\%}$ & $\sigma_{0.5\%}$ & $\sigma_{0.7\%}$ & $\sigma_{0.9\%}$" + lineending
    print correlations0 + lineending
    print correlations1 + lineending
    print '''\\end{tabular}
\\caption{$\\sigma_{\\%}$ correlations for ''' + namefile + '''}
\\end{table}'''

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
    data.extend(loadQueries("../../IR2016/queries/topics.301-350"))
    data.extend(loadQueries("../../IR2016/queries/topics.351-400"))
    data.extend(loadQueries("../../IR2016/queries/topics.401-450"))

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
        for normalized in [False,True]:
            #standard deviation or mad
            for sorm in [False,True]:
                for name in ["la", "ft", "fbis"]:
                    for count in [20, 50,100,200]:
                        print normalized, sorm, name, count
                        innerQuery(name, base + name + str(count) + ".txt", count,doprint,stopwords,trecoutput,sorm,normalized)
                        doprint = False


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
