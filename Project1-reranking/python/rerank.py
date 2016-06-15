import os
import re

qrelsfile = "../qrels/qrels.txt"
def readrerank(path):
    with open(path) as f:
        file = f.readlines()
    ranks = [query.split(",") for query in file]
    return ranks

def rerankinner(ranks,reranks,name,count,f,fun):
    rank = [[x[0],x[1],x[2],str(i+1),str(round(fun(reranks[i]),5)),x[5]] for i,x in enumerate(ranks)]
    rank = [" ".join(x) for x in rank]
    rank = "".join(rank)
    f.write(rank)
    return
    rerank = zip (ranks,reranks)
    rerank.sort(key=fun)
    rank = [x[0] for x in rerank]
    rank = [[x[0],x[1],x[2],str(i+1),str(round(fun(rerank[i]),5)),x[5]] for i,x in enumerate(rank)]
    rank = [" ".join(x) for x in rank]
    rank = "".join(rank)
    f.write(rank)

def parseTrec_Eval(path,name):
    with open (path,"r") as f:
        file = f.read()
    p5reg = re.compile("P_5\\s+all\\s+([0-9.]+)",re.IGNORECASE)
    p5 = p5reg.findall(file)[0]
    recipreg = re.compile("recip_rank\\s+all\\s+([0-9.]+)",re.IGNORECASE)
    recip = recipreg.findall(file)[0]
    return recip,p5


def parseTrec_EvalNDCG(path, name):
    with open(path, "r") as f:
        file = f.read()
    p5reg = re.compile("([0-9.]+)")
    NDCG = p5reg.findall(file)[1]
    return NDCG


def rerank(name,count):

    with open("../queries/results/best/" + name  + str(count) + ".txt") as f:
        file = f.readlines()
    baseline = [rank.split(" ") for rank in file]

    reranksall = readrerank("../queries/results/best/rankings/" + name + str(count) + ".txt")

    resfilerlm = "../queries/results/best/" + name + str(count) + ".txt"
    resfiler1 = "../queries/results/best/reranks/" + name + str(count) + ".r1.txt"
    resfiler2 = "../queries/results/best/reranks/" + name + str(count) + ".r2.txt"
    resfiler1r2 = "../queries/results/best/reranks/" + name + str(count) + ".r1r2.txt"


    trecfilerlm  = "../trec/rerank/" + name + str(count) + ".txt"
    trecfiler1   = "../trec/rerank/" + name + str(count) + ".r1.txt"
    trecfiler2   = "../trec/rerank/" + name + str(count) + ".r2.txt"
    trecfiler1r2 = "../trec/rerank/" + name + str(count) + ".r1r2.txt"

    fr1 = open(resfiler1,"w")
    fr2 = open(resfiler2,"w")
    fr1r2 = open(resfiler1r2,"w")


    for i in range(150):
        ranks = [rank for rank in baseline if rank[0] == str(i+301)]
        reranks = [rerank for rerank in reranksall if rerank[0] == str(i+301)]
        #rerankinner(ranks,reranks,name,count,fr1,lambda x: float(x[1][2]))
        #r1
        rerankinner(ranks,reranks,name,count,fr1,lambda x: float(x[2]))
        #rerankinner(ranks,reranks,name,count,fr2,lambda x: float(x[1][3]))
        #r2
        rerankinner(ranks,reranks,name,count,fr2,lambda x: float(x[3]))
        #r1+r2
        rerankinner(ranks,reranks,name,count,fr1r2,lambda x: (float(x[2])+float(x[3]))/2)
        #rerankinner(ranks,reranks,name,count,fr1r2,lambda x: (float(x[1][2])+float(x[1][3]))/2)


    fr1.close()
    fr2.close()
    fr1r2.close()

    os.system("../trec_eval " + qrelsfile + " " + resfilerlm + " > " + trecfilerlm)
    os.system("../trec_eval " + qrelsfile + " " + resfiler1 + " > " + trecfiler1)
    os.system("../trec_eval " + qrelsfile + " " + resfiler2 + " > " + trecfiler2)
    os.system("../trec_eval " + qrelsfile + " " + resfiler1r2 + " > " + trecfiler1r2)
    lm = parseTrec_Eval(trecfilerlm, name)
    R1 = parseTrec_Eval(trecfiler1, name)
    R2 = parseTrec_Eval(trecfiler2, name)
    R1R2 = parseTrec_Eval(trecfiler1r2, name)

    os.system("../trec_eval -m ndcg_cut " + qrelsfile + " " + resfilerlm + " > " + trecfilerlm)
    os.system("../trec_eval -m ndcg_cut " + qrelsfile + " " + resfiler1 + " > " + trecfiler1)
    os.system("../trec_eval -m ndcg_cut " + qrelsfile + " " + resfiler2 + " > " + trecfiler2)
    os.system("../trec_eval -m ndcg_cut " + qrelsfile + " " + resfiler1r2 + " > " + trecfiler1r2)
    lmNDCG = parseTrec_EvalNDCG(trecfilerlm, name)
    R1NDCG = parseTrec_EvalNDCG(trecfiler1, name)
    R2NDCG = parseTrec_EvalNDCG(trecfiler2, name)
    R1R2NDCG = parseTrec_EvalNDCG(trecfiler1r2, name)



    print name + " & P\\_5 & " + lm[0] + " & " + R1[0] + " & " + R2[0] + " & " + R1R2[0] + " \\\\ \hline "
    print name + " & MMR & " + lm[1] + " & " + R1[1] + " & " + R2[1] + " & " + R1R2[1] + " \\\\ \hline"
    print name + " & NDCG@5 & " + lmNDCG + " & " + R1NDCG + " & " + R2NDCG + " & " + R1R2NDCG + " \\\\ \hline"


if __name__ == "__main__":
    for count in [20, 50]:
        print "name & type  & lm & +R1 & +R2 & +R1+R2 & NDCG@5 \\\\ \hline"
        for name in ["la","ft","fbis"]:
            rerank(name,count)


