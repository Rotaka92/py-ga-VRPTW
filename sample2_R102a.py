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
from gavrptw.flp3 import make_data, flp


import os
from json import load
instName = 'R102a'

#type in the path of the direct, where the folder gavrptw is in
#for loading the instance
#BASE_DIR = 'C:\\Users\\Robin\\py-ga-VRPTW'
BASE_DIR = 'C:\\Users\\TapperR\\Desktop\\VRP2\\py-ga-VRPTW'
jsonDataDir = os.path.join(BASE_DIR,'data', 'json')
jsonFile = os.path.join(jsonDataDir, '%s.json' % instName)
with open(jsonFile) as f:
    instance = load(f)

def main():
    
    random.seed(54)
    
    
    
    
    cp = 0.5        #Cost per employed person in depot per minute
    cU = 0.001    #Cost per entity of distance 
        
    instName = 'R102a'
    
    initCost = 60.0     #cost per initialization a new roboter
    persCost = 0.073667 #cp? cp in FLP, pers in GA -> TEST IT
    
    indSize = 10        #length of a chromosom
    popSize = 80        #Size of the population
    cxPb = 0.7          #Probability for a crossover
    mutPb = 0.01        #Probability for a mutation
    NGen = 100          #Number of iterations 
    
    
    I,J,d,M,f,c = make_data()   #make data for the flp
    model = flp(I,J,d,M,f,c,cp,cU)  #establish the flp
    model.optimize()            #solve the flp
    

    instanceAll = {}
    
    #### dividing the instance in three sub-instances ####
    #reopening the full instance
    for j in J:  
        #j = 1        
        jsonFile = os.path.join(jsonDataDir, '%s.json' % instName)
        with open(jsonFile) as f:
            instance = load(f)
    
    #tupel: which station does the customer belong to and
    #       which customer is it for the station           
        f = [0,0,0] 
        for i in range(1,I+1):
            #i = 1
            for k in J:
                #k = 1
                if round(model.getVal(model.data[2][i-1,k]),1) == 1.0:
                    instance['customer_%d' % i]['belongs_to']  =  k, f[k]
                    f[k] = f[k]+1 

    #pop out the customer which does not belong to the explicit station
    #and filling up the instance 
        for i in range(1,I+1):
            #i = 1
            if instance['customer_%d' % i]['belongs_to'][0] != j:
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
    main()


#stopping the time
t1 = time.time()
total = t1-t0

print ('Time of calculations[sec]: %f' %total)
