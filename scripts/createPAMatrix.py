import os
import sys
import json
import numpy as np
import pandas as pd
from tqdm import tqdm
from Bio import SeqIO

#ARGS
#arg 1 is the json with the list of gene families (including singletons verified by blasting against NR database)
#arg 2 should be path to a directory that contains all .faa files for every taxa in the matrix. The gene names in the files in arg 2 should match the gene names from the families in arg 1
#arg 3 is the genus name
#python scripst/createPAMatrix.py gene_families.json protein_fastas/ genusname

def getOrganismGeneList(fastapath):
    genelist = []
    with open(fastapath) as fasta:
        for record in SeqIO.parse(fasta,'fasta'):
            genelist.append(record.id)
    accession = genelist[0].strip('>').split(':')[0]
    return accession,genelist

def allOrganismsGeneLists(fastadirpath):
    organismGenes = {}
    for fastapath in os.listdir(fastadirpath):
        if fastapath.endswith('.faa'):
            fullfastapath = os.path.join(fastadirpath,fastapath)
            accession,genelist = getOrganismGeneList(fullfastapath)
            organismGenes[accession] = genelist
    return organismGenes

def buildmatrix(organismGenes,genefamilies):
    pajson = []
    organisms = list(organismGenes.keys())
    genefams = list(genefamilies.keys())
    for org in tqdm(organisms,leave=True):
        orgcol = {'organism':org}
        for fam in tqdm(genefams,leave=False):
            orggenes = set(organismGenes[org])
            famgenes = set(genefamilies[fam])
            orgcol[fam] = len(orggenes.intersection(famgenes))
        pajson.append(orgcol)
    return pajson

def jsonToCsv(jsondata,outfile):
    df = pd.DataFrame(jsondata).T
    df.columns = df.loc['organism']
    df = df.drop('organism',axis=0)
    binarize = lambda x: 1 if x > 0 else x
    df = df.applymap(binarize)
    df.to_csv(outfile,index_label='gene_family')
    return None

def main(genefamilies,fastadir,outfile):
    if os.path.exists(outfile):
        print('already calcualted')
        return None
    genefamilies = json.load(open(genefamilies))
    organismGenes = allOrganismsGeneLists(fastadir)
    pajson = buildmatrix(organismGenes,genefamilies)
    jsonToCsv(pajson,outfile)
    return None

if __name__ == '__main__':
    genefamilies = sys.argv[1]
    fastadir = sys.argv[2]
    outfile = 'binary_pa_matrix.csv'
    main(genefamilies,fastadir,outfile)
    print('\nPA Matrix csv written to {}'.format(outfile))

#DEPRECIATED
#def accessionFromGBFF(fastapath):
#    gbff_dir = "/home/sid/thesis_SidReed/bacterialGBFFs/rawdata_s1"
#    gbff_base = fastapath.split('.faa')[0]
#    gbff_file = os.path.join(gbff_dir,gbff_base)
#    return SeqIO.read(open(gbff_file,'r'),'genbank').name
#def buildmatrix(organismgenes,genefamilies):
#    pamat = np.zeros((len(list(organismgenes.keys())),len(list(genefamilies.keys()))))
#    orgidxs = {i:o for i,o in enumerate(organismgenes.keys())}
#    famidxs = {i:f for i,f in enumerate(genefamilies.keys())}
#    for oidx,org in tqdm(orgidxs.items(),total=len(list(orgidxs.keys()))):
#        for fidx,fam in tqdm(famidxs.items(),total=len(list(famidxs.keys()))):
#            orggenes = set(organismgenes[org])
#            famgenes = set(genefamilies[fam])
#            pamat[oidx][fidx] = len(orggenes.intersection(famgenes))
#    return pamat,orgidxs,famidxs
#def matrix_to_binary(pamat):
#    binarize = lambda x:np.where(x > 0, 1, 0)
#    vecbin = np.vectorize(binarize)
#    return vecbin(pamat)
#def namegenerator(basename):
#    matname = 'pa_matrix.npy'
#    biname = 'binary_pa_matrix.csv'
#    orgidxname = 'row_organism_idxs.json'
#    famidxname = 'column_indexes_families.json'
#    return matname,biname,orgidxname,famidxname
#def main(families,fastadir):
#    families = json.load(open(families))
#    orggenes = allOrganismsGeneLists(fastadir)
#    pamat = buildmatrix(orggenes,families)
#    return pamat
#if __name__ == '__main__':
#    pamat,orgidxs,famidxs = main(sys.argv[1],sys.argv[2])
#    matn,binn,orgidxn,famidxn = namegenerator(sys.argv[3])
#
#    np.save(open(matn,'wb'),pamat)
#    print('\nP/A matrix saved to {}'.format(matn))
#
#    json.dump(orgidxs,open(orgidxn,'w'))
#    print('row index organisms saved to {}'.format(orgidxn))
#    json.dump(famidxs,open(famidxn,'w'))
#    print('col index families saved to {}'.format(famidxn))
#    print('family numbers in {} correspond to those in {}'.format(famidxn,sys.argv[1]))
#
#    binmat = matrix_to_binary(pamat)
#    np.savetxt(binn,binmat,fmt="%d",delimiter=',',newline='\n')
#    print('binary P/A matrix saved to {}'.format(binn))
