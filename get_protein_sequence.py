#!/usr/bin/python

import sys

fn = sys.argv[1]

with open(fn, 'r') as fin:
    #res = {}
    #old_resid = ''
    FLAG = True
    ids = []
    for line in fin:
        if line[:6].strip() in ('HETATM', 'ATOM'):
            #chain = line[20:22]
            resid = int(line[22:26])
            resn  = line[17:20]
            atomn = line[13:16].strip()
            atomi = int(line[6:11])
            if atomn == 'O1':
                FLAG = (not FLAG)
            if FLAG:
                print line, 
                ids.append(atomi)
        elif line[:6] == 'CONECT':
            if int(line[6:11]) in ids:
                print line, 
            #if not chain in res:
                #res[chain] = []
            #if not resid == old_resid:
                #res[chain].append(line[17:20])
            #old_resid = resid
#for chain in res:
    #for r in res[chain]:
        #print chain, r