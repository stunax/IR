#include <iostream>
#include <vector>
#include <limits>
#include <string>

std::string codepath = "/home/ginger/Documents/IR/Project2-qpp/";
std::string indexpath = "/home/ginger/Documents/IR/Project2-qpp/";
using namespace __gnu_cxx;
#include "indri/Repository.hpp"
#include "indri/QueryEnvironment.hpp"
#include "indri/SnippetBuilder.hpp"

using namespace indri::api;

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
    std::cout << "," << avg << "," << min << "," << max << "\n";

}


void indri_start(char *path,char *name){
    indri::collection::Repository repository;
    repository.openRead(path);
    // get the index from the repository
    // in our case it will be the first index
    indri::collection::Repository::index_state repIndexState = repository.indexes();
    indri::index::Index *thisIndex=(*repIndexState)[0];
    printStats(thisIndex,name);


    // our builder object - false in the constructor means no HTML output.
    //SnippetBuilder builder(false);

    // create a query environment
    //QueryEnvironment indriEnvironment;

    std::string pathToIndex = "/";
    pathToIndex += name;
    pathToIndex += "-index";
    // open the index
    //indriEnvironment.addIndex(pathToIndex);


    repository.close();
}




int main() {
    int i = system (("cd " + codepath + "python; python queries.py").c_str());

    std::cout << "name,docCount,avg,min,max\n";

    std::string path1 = indexpath + "la-index";
    indri_start((char*)path1.c_str(),(char*)"la");

    std::string path2 = indexpath + "fbis-index";
    indri_start((char*)path2.c_str(),(char*)"fbis");

    std::string path3 = indexpath + "ft-index";
    indri_start((char*)path3.c_str(),(char*)"ft");


    return 0;
}