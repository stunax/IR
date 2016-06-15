#include <cmath>
#include <iostream>
#include <vector>
#include <limits>
#include "csv.h"
#include <sstream>
#include <algorithm>
#include <iterator>



using namespace __gnu_cxx;
#include "indri/Repository.hpp"
#include "indri/QueryEnvironment.hpp"
#include "indri/SnippetBuilder.hpp"
#include "indri/KrovetzStemmer.hpp"
#include "indri/CompressedCollection.hpp"

using namespace indri::api;

std::string indexpath = "/home/ginger/Documents/IR/Project1-reranking/";
std::string codepath = "/home/ginger/Documents/IR/Project1-reranking/";
// a global repository object for our index






void printStats(indri::index::Index *thisIndex,char *name){
    std::cout << name ;
    std::cout << "," <<thisIndex->documentCount();

    indri::index::DocumentDataIterator *documents = thisIndex->documentDataIterator();

    int counter = 0;
    int min = std::numeric_limits<int>::max();
    int max = std::numeric_limits<int>::min();
    // const indri::index::DocumentData *current;
    documents->startIteration();
    while (!documents->finished()){
        const indri::index::DocumentData *current = documents->currentEntry();
        counter += current->totalLength;
        if (min > current->totalLength){
            min = current->totalLength;
        };
        if (max < current->totalLength){
            max = current->totalLength;
        };
        documents->nextEntry();
    }
    uint64_t avg = counter / thisIndex->documentCount();
    std::cout << "," << avg << "," << min << "," << max << std::endl;

}

void rerank(indri::index::Index *thisIndex,char *name, indri::collection::Repository *repository, char *count){

    vector<tuple<int,string>> queryInfo;
    indri::parse::KrovetzStemmer kStemmer;
    std::string queryloc = codepath;
    queryloc += "queries/parsedQueries.txt";

    io::CSVReader<2> queryFile(queryloc);
    int num;
    string terms;
    string stemmedTerms = "";
    while(queryFile.read_row(num, terms)){
        stringstream s(terms);
        string word;
        while (s >> word) {
            char *stemmedWord = strdup(word.c_str());;
            stemmedTerms += kStemmer.kstem_stemmer(stemmedWord);
            stemmedTerms += " ";
        }
        queryInfo.push_back(make_tuple(num,stemmedTerms));
        stemmedTerms = "";
    }
    string outpath = codepath;
    outpath += "queries/results/best/rankings/";
    outpath += name;
    outpath += count;
    outpath += ".txt";

    ofstream outputfile;
    outputfile.open(outpath,ios::out);


    // Result file of best mu
    std::string bestmuresPath = codepath ;
    bestmuresPath += "queries/results/best/";
    bestmuresPath += name;
    bestmuresPath += "50";
    bestmuresPath += ".txt";
    io::CSVReader<6, io::trim_chars<' ', '\t'>, io::no_quote_escape<' '>> resultFile(bestmuresPath);
    vector<tuple<int, lemur::api::EXDOCID_T >> resultInfo;

    int qId; string extra; string docId; int rank; string score; string id;
    while(resultFile.read_row(qId, extra, docId, rank, score, id)) {
        indri::collection::CompressedCollection *col = repository->collection();
        std::vector<lemur::api::DOCID_T> colDocId = col->retrieveIDByMetadatum("docno",docId);
        //int queryLength = CountWords(queryString);
        //Query as string
        string query = get<1>(queryInfo[qId-301]);
        //terms in document
        const indri::index::TermList *docTerms = thisIndex->termList(colDocId[0]);

        istringstream iss(query);
        vector<string> terms;
        copy(istream_iterator<string>(iss),
             istream_iterator<string>(),
             back_inserter(terms));
        unsigned long queryLength = terms.size();

        double maxtfidf = 0;
        vector<double> tfidfs;
        for (string term: terms){
            //r1 part
            indri::utility::greedy_vector<lemur::api::TERMID_T> termsVec = docTerms->terms();
            int tf = 0;
            lemur::api::TERMID_T termID = thisIndex->term(term);
            for (lemur::api::TERMID_T termVec:termsVec){
                if (termVec == termID){
                    tf += 1;
                }
            }
            double idf = thisIndex->documentCount()/(thisIndex->documentCount(term)+1);
            double rank = tf/idf;
            if(rank > maxtfidf)
                maxtfidf = rank;
            tfidfs.push_back(rank);


        }

        //r2 part
        double maxDiff = 0;
        double prevrank = -1;
        //r1 part
        double sum = 0;
        double current = 0;
        double r1,r2;
        if (maxtfidf <= 0){
            r1 = 0;
            r2 = 0;
        }
        else {
            for (double tfidf:tfidfs) {
                double rank = tfidf / maxtfidf;
                sum += rank;

                //r2 part
                if (prevrank != -1)
                    current = abs(prevrank - rank);
                if (current > maxDiff)
                    maxDiff = current;
                prevrank = rank;
            }
            r1 = sum / queryLength;
            //r2part
            r2 = 1 - maxDiff;
        }
        outputfile << qId << "," << rank << "," << r1 << "," << r2 << "\n";

    }
    outputfile.close();
}


void indri_start(char *indexpath,char *name){
    indri::collection::Repository repository;
    repository.openRead(indexpath);
    // get the index from the repository
    // in our case it will be the first index
    indri::collection::Repository::index_state repIndexState = repository.indexes();
    indri::index::Index *thisIndex=(*repIndexState)[0];
    printStats(thisIndex,name);

    string count = "20";
    rerank(thisIndex,name,&repository,(char*)count.c_str());
    count = "50";
    rerank(thisIndex,name,&repository,(char*)count.c_str());



}


int main() {
    //Print stats about queries and stuff
    int i = system (("cd " + codepath + "python; python queries.py").c_str());

    std::cout << "name,docCount,avg,min,max\n";

    std::string path1 = indexpath + "la-index";
    indri_start((char*)path1.c_str(),(char*)"la");

    std::string path2 = indexpath + "fbis-index";
    indri_start((char*)path2.c_str(),(char*)"fbis");

    std::string path3 = indexpath + "ft-index";
    indri_start((char*)path3.c_str(),(char*)"ft");


    int j = system (("cd " + codepath + "python; python rerank.py").c_str());

    std::cout << "--------------------done--------------------" << std::endl;
    std::cout.flush();
    return 0;
}