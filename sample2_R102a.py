# -*- coding: utf-8 -*-
# sample_R101.py

import time
t0 = time.time()

import random

#loading the GA for the EVRP-TW
from gavrptw.core3 import gaVRPTW


#solving the FLP with this file
from gavrptw.flp3 import make_data, flp



import os
from json import load
import math
from pyscipopt import Model, quicksum, multidict
from deap import base, creator, tools
instName = 'R102a'
BASE_DIR = 'C:\\Users\\Robin\\py-ga-VRPTW'
jsonDataDir = os.path.join(BASE_DIR,'data', 'json')
jsonFile = os.path.join(jsonDataDir, '%s.json' % instName)
with open(jsonFile) as f:
    instance = load(f)

#jsonFile = os.path.join(jsonDataDir, '%s.json' % instName)
#with open(jsonFile) as f:
#    instance = load(f)

### seed 0 for the optimum in vehicle = 3, customers = 15 ###


def main():
    ### for a good solution, which is descriped at first in the paper ###
    random.seed(54)
    
    ### for sufficient good solution (heuristic), which is also described in the paper, uncomment this random.seed-function ###
    #random.seed(52)
    
    
    cp = 0.5
    cU = 0.001    #Cost per entity of distance 
        
    instName = 'R102a'
    
    initCost = 60.0
    persCost = 0.073667
    
    indSize = 15
    popSize = 80
    cxPb = 0.7
    mutPb = 0.01
    NGen = 100
    
    
    I,J,d,M,f,c = make_data()
    model = flp(I,J,d,M,f,c,cp,cU)
#    model.setPresolve(pyscipopt.SCIP_PARAMSETTING.OFF)
#    model.setHeuristics(pyscipopt.SCIP_PARAMSETTING.OFF)
#    model.disablePropagation()
    model.optimize()
    
    
#    EPS = 1.e-9
#    x,y,y2 = model.data
#    edges = [(i,j) for (i,j) in x if model.getVal(x[i,j]) > EPS]
#    facilities = [j for j in y if model.getVal(y[j]) > EPS]
#
#    print("Optimal value:", model.getObjVal())
#    print("Facilities at nodes:", facilities)
#    print("Edges:", edges)
    
    instanceAll = {}
    
    #reopening the full instance
    for j in J:  
        #j = 1        
        jsonFile = os.path.join(jsonDataDir, '%s.json' % instName)
        with open(jsonFile) as f:
            instance = load(f)
    
    #tupel: which station does the customer belong to and which customer is it for the station           
        f = [0,0,0] 
        for i in range(1,I+1):
            #i = 1
            for k in J:
                #k = 1
                if round(model.getVal(model.data[2][i-1,k]),1) == 1.0:
                    instance['customer_%d' % i]['belongs_to']  =  k, f[k]
                    f[k] = f[k]+1 

#[round(model.getVal(model.data[2][i-1,k]) for i in range(1, I+1) for k in J),1]


    #pop out the customer which does not belong to the explicit station
    #and filling up the instance all dict 
        for i in range(1,I+1):
            #i = 1
            if instance['customer_%d' % i]['belongs_to'][0] != j:
                instance.pop('customer_%d' % i)
    
        instanceAll['instance_%d' %j] = instance
        
    p = 0
  

    for j in J:
        #j = 1
        instance=instanceAll['instance_%d' %j]
        indSize=len(instance)-8
        if indSize != 0:
            t = gaVRPTW(
                instance=instance,
                stat_nr=j,
                dist_matr = c,
                instName=instName,
                cU=cU,
                initCost=initCost,
                persCost = persCost,
                indSize=indSize,
                popSize=popSize,
                cxPb=cxPb,
                mutPb=mutPb,
                NGen=NGen,
            )
            p = p + t 

    print('\n\nTotalTotalCost: %f' %p)

if __name__ == '__main__':
    main()



t1 = time.time()
total = t1-t0

print ('Time of calculations[sec]: %f' %total)


