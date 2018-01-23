# -*- coding: utf-8 -*-
"""
Created on Sat Jan  7 11:24:15 2018

@author: Robin Tappert
"""

import time
#starting the stop watch
t0 = time.time()

import random

#loading the GA for the EVRP-TW
from gavrptw.core3 import gaVRPTW

#solving the FLP with this file
from gavrptw.flp4 import make_data, flp


import os
from json import load
instName = 'R102b'

#type in the path of the direct, where the folder gavrptw is in
#for loading the instance
BASE_DIR = 'C:\\Users\\Robin\\py-ga-VRPTW'
#BASE_DIR = 'C:\\Users\\TapperR\\Desktop\\VRP2\\py-ga-VRPTW'
jsonDataDir = os.path.join(BASE_DIR,'data', 'json')
jsonFile = os.path.join(jsonDataDir, '%s.json' % instName)
with open(jsonFile) as f:
    instance = load(f)

def main():

    
    
    
    cp = 0.073667        #Cost per employed person in depot per minute
    cU = 0.01              #Cost per entity of distance 
        
    instName = 'R102b'
    
    initCost = 80.0     #cost per initialization a new roboter
    persCost = 0.073667 #cp? cp in FLP, pers in GA -> TEST IT
    
    indSize = 10        #length of a chromosom
    popSize = 80        #Size of the population
    cxPb = 0.7          #Probability for a crossover
    mutPb = 0.01        #Probability for a mutation
    NGen = 100          #Number of iterations 
    
    
    I,J,d,M,f,c = make_data()   #make data for the flp
    model = flp(I,J,d,M,f,c,cp,cU)  #establish the flp
    model.optimize()            #solve the flp
    
    
    
    
    EPS = 1.e-9
    x,y,y2 = model.data
    edges = [(i,j) for (i,j) in x if model.getVal(x[i,j]) > EPS]
    facilities = [j for j in y if model.getVal(y[j]) > EPS]
    if len(edges)>I:
        print("Optimal value:", model.getObjVal())
        print("Facilities at nodes:", facilities)
        print("Edges:", edges)
        
        
    
    [model.getVal(model.data[2][i,k]) for i in range(I) for k in J]



    ##### MOST IMPORTANT CHANGE OF THE ALGORITHM ########
    
    
                
    ##########################################################
    instanceAll = {}
    
    #### dividing the instance in three sub-instances ####
    #reopening the full instance
    for j in J:  
        #j = 1        
        jsonFile = os.path.join(jsonDataDir, '%s.json' % instName)
        with open(jsonFile) as f:
            instance = load(f)
            
        for i in range(1,I+1):
            #i = 1
            for k in J:
                #k = 0                
                    instance['customer_%d' % i]['get_from']  =\
                    [round(model.getVal(model.data[0][i-1, k])) for k in J]
            
    
    #tupel: which station does the customer belong to and
    #       which customer in row is it for the station           
        f = [0,0,0] 
        for i in range(1,I+1):
            instance['customer_%d' % i]['belongs_to'] = []
            #i = 1
            for k in J:
                 #k = 1
                if round(model.getVal(model.data[2][i-1,k]),1) == 1.0:             
                    instance['customer_%d' % i]['belongs_to'].append([k, f[k]])
                    f[k] = f[k]+1

    #pop out the customer which does not belong to the explicit station
    #and filling up the instance ### lot of space for improvement here!!!! #####
        for i in range(1,I+1):
            #i = 5, j = 1
            
            if len(instance['customer_%d' % i]['belongs_to']) == 2:
                for p in range(2):
                    #p = 1
                    if instance['customer_%d' % i]['belongs_to'][p][0] != j:
                        del instance['customer_%d' % i]['belongs_to'][p]
                                    #does it count in general?
                        instance['customer_%d' % i]['demand'] = instance['customer_%d' % i]['get_from'][j]
                    ### lot of space for improvement here!!!! #####
                    elif instance['customer_%d' % i]['belongs_to'][0][0] != j and instance['customer_%d' % i]['belongs_to'][1][0] != j:
                        instance.pop('customer_%d' % i)
            elif instance['customer_%d' % i]['belongs_to'][0][0] != j:
                instance.pop('customer_%d' % i)
            
    
    
        
    
        instanceAll['instance_%d' %j] = instance
        
    p = 0
  
    #run the genetic algorithm for a certain depot with
    #its particular instance 
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
            
    #prints out the total cost of all depots and deliveries
    print('\n\nTotalTotalCost: %f' %p)


if __name__ == '__main__':
    random.seed(3)
    main()


#stopping the time
t1 = time.time()
total = t1-t0

print ('Time of calculations[sec]: %f' %total)
