import os
import sys
import json
import math
import glob
import subprocess
import numpy as np
import pandas as pd
from tqdm import tqdm
from Bio import SeqIO,AlignIO,Alphabet
from Bio.SeqRecord import SeqRecord
from multiprocessing.dummy import Pool as ThreadPool

def matrix_to_binary(pamat):
    binarize = lambda x:np.where(x > 0, 1, 0)
    vecbin = np.vectorize(binarize)
    return vecbin(pamat)

def pickGeneFamiliesForTrees(pamat,columnindex,minsize):
    gene_family_list = []
    if type(minsize) == float and (minsize > 0 and minsize < 1):
        minsize = int(math.floor(minsize*pamat.shape[0]))
    print('minimum organisms gene family must be present in: {}'.format(minsize))
    binmat = matrix_to_binary(pamat)
    sizes = np.apply_along_axis(sum,0,binmat)
    family_idxs = [str(i) for i,size in enumerate(sizes) if size >= minsize]
    print('using {} of {} gene families for trees'.format(len(family_idxs),pamat.shape[1]))
    return family_idxs

def extractSeqsForTree(headerlist,nucFasta,outdir,genefam):
    seqRecordlist = []
    seqiter = SeqIO.parse(open(nucFasta),'fasta') #open fasta file
    seqRecordlist = [seq for seq in seqiter if seq.id in headerlist] #put sequences in list
    fastafilename = '{}/fastas/{}.fna'.format(outdir,genefam)
    return fastafilename, seqRecordlist

def fixNames(seqlist):
    fixedseqs = []
    for sequence in seqlist:
        fixedseqs.append(SeqRecord(sequence.seq, name=sequence.name.replace(':','__'), id=sequence.id.replace(':','__')))
    return fixedseqs

def writeFastas(nameseqiter):
    for name,seqs in nameseqiter.items():
        with open(name,'w') as outfile:
            SeqIO.write(seqs,outfile,'fasta') #write all seqs to a fasta file
    return None

def alignGeneFamilies(outdir):
    mafftbase = 'mafft --quiet --localpair --maxiterate 1000'
    for fastafile in tqdm(os.listdir('{}/fastas'.format(outdir)),desc='aligning'):
        fastabase = fastafile.split('.')[0]
        fastaname = '{}/fastas/{}'.format(outdir,fastafile)
        alnfile = '{}/tmp.aln'.format(outdir,fastabase)
        align = '{} {} > {}'.format(mafftbase,fastaname,alnfile)
        os.system(align)
        AlignIO.convert(alnfile,'fasta','{}/nexus/{}.nex'.format(outdir,fastabase),'nexus',alphabet=Alphabet.generic_dna)
    return None

def buildTrees(outdir):
    for nexfile in tqdm(os.listdir('{}/nexus'.format(outdir)),desc='trees'):
        nexbase = nexfile.split('.')[0]
        mbf = """set autoclose=yes nowarn=yes
execute {}/nexus/{}
lset nst=6 rates=gamma
mcmc ngen=10000 savebrlens=yes file={}
quit""".format(outdir,nexfile,nexbase)
        treedir = '{}/trees/{}'.format(outdir,nexbase)
        os.system('mkdir -p {}'.format(treedir))
        mbscriptname = '{}/mb_script.txt'.format(treedir)
        open(mbscriptname,'w').write(mbf)
        logfilename = '{}/mb_log.txt'.format(treedir)
        with open(mbscriptname,'rb',0) as mbscript, open(logfilename,'wb',0) as logfile:
            logtxt = subprocess.run(['mb'],
                                    stdin=mbscript,
                                    stdout=logfile,
                                    check=True)
        for fp in glob.glob('./{}*'.format(nexbase)):
            os.rename(fp,os.path.join(os.getcwd(),treedir,fp))
    return None

def main(pamat,columns,familys,nucFasta,genusname,minsize):
    #set up out directories
    outdir = 'gene_tree_files'
    os.system('mkdir -p {}'.format(outdir))
    os.system('mkdir -p {}/fastas'.format(outdir))
    os.system('mkdir -p {}/nexus'.format(outdir))
    os.system('mkdir -p {}/trees'.format(outdir))
    #pick families
    family_col_idxs = pickGeneFamiliesForTrees(pamat,columns,minsize)
    family_idxs = [columns[col_idx] for col_idx in family_col_idxs]
    headerlists = {famidx:familys[famidx] for famidx in family_idxs}
    #write families to fasta files
    seqs_to_write = [extractSeqsForTree(heads,nucFasta,outdir,fam) for fam,heads in tqdm(headerlists.items(),total=len(list(headerlists.keys())),desc='getseqs')]
    seqs_to_write = {name:fixNames(seqs) for (name,seqs) in seqs_to_write}
    writeFastas(seqs_to_write)
    #align gene family fastas and convert to nexus
    alignGeneFamilies(outdir)
    #buiil gene trees with mrbayes from alingments
    buildTrees(outdir)
    return None

if __name__ == '__main__':
    pamat = np.load(sys.argv[1])
    colidx = json.load(open(sys.argv[2]))
    famidx = json.load(open(sys.argv[3]))
    nucFasta = sys.argv[4]
    genusname = sys.argv[5]
    minsize = 0.3
    main(pamat,colidx,famidx,nucFasta,genusname,minsize)