# -*- coding: utf-8 -*-
"""
Created on Sat Jan  6 12:48:48 2018

@author: Robin
"""

"""
flp.py:  model for solving the capacitated facility location problem

minimize the total (weighted) travel cost from n customers
to some facilities with fixed costs and capacities.

Copyright (c) by Joao Pedro PEDROSO and Mikio KUBO, 2012

"""

import os
from json import load
import numpy as np
import math
from pyscipopt import Model, quicksum, multidict
instName = 'R102b'
BASE_DIR = 'C:\\Users\\Robin\\py-ga-VRPTW'
jsonDataDir = os.path.join(BASE_DIR,'data', 'json')
jsonFile = os.path.join(jsonDataDir, '%s.json' % instName)
with open(jsonFile) as f:
    instance = load(f)





#Scalars

cp = 0.5    #personal cost per minute
cU = 0.001    #Cost per entity of distance 

def flp(I,J,d,M,f,c,cp,cU):
    """flp -- model for the capacitated facility location problem
    Parameters:
        - I: set of customers
        - J: set of facilities
        - d[i]: demand for customer i
        - M[j]: capacity of facility j
        - f[j]: fixed cost for using a facility in point j
        - c[i,j]: unit cost of servicing demand point i from facility j
    Returns a model, ready to be solved.
    """
   
        
    model = Model("flp")

    x,y,y2 = {},{},{}
    for j in range(len(J)):
        y[j] = model.addVar(vtype="B", name="y(%s)"%j)
        for i in range(I):
            x[i,j] = model.addVar(vtype="C", name="x(%s,%s)"%(i,j))
            y2[i,j] = model.addVar(vtype="B", name="y2(%s,%s)"%(i,j))
    
    #### restrictions: ####
    
        #demand has to be completely served by the facilities
    for i in range(I):
        model.addCons(quicksum(x[i,j]*y2[i,j]\
                               for j in range(len(J))) == d[i]) 
        
        #demand served by a facility is not allowed to exceed 
        #the capacity of it
        
    for j in range(len(M)):
        model.addCons(quicksum(x[i,j]*y2[i,j]\
                               for i in range(I)) <= M[j]*y[j])
        
        
        #delivery to customer is not allowed to exceed customers demand

    for (i,j) in x:
        model.addCons(x[i,j]*y2[i,j] <= d[i]*y[j])
       
        
    for i in range(I):
        #i = 0
        for j in J:
            #j = 0
            model.addCons(y2[i,j] <= y[j])
      
        
        

        ####objective function: variable cost for open station #####
        ####                       plus cost for deliveries  ######      
    model.setObjective(
#        quicksum(f[j]*y[j] for j in J) +
        quicksum(c[i+3,j]*x[i,j]*cU for i in range(I) for j in J) + 
        quicksum(y[j]*((instance['deport%d' %(j)]['due_time']-\
                 instance['deport%d' %(j)]['ready_time'])*cp)\
            for j in range(len(J))),"minimize")
            
        #for the possibility to get access to the values of each 
        #defined variable
            
    model.data = x,y,y2

    return model




def distance(x1,y1,x2,y2):
    return (math.sqrt((x2-x1)**2 + (y2-y1)**2))*1000



def make_data():
    I = 10
    d = [instance['customer_%d'%i]['demand'] for i in range(1,I+1)] # demand         
    J,M,f = multidict({0:[8,20], 1:[20,20], 2:[20,20]}) # capacity, fixed costs
    xDep = [instance['deport%d' %i]['coordinates']['x'] for i in range(len(J))]
    yDep = [instance['deport%d' %i]['coordinates']['y'] for i in range(len(J))]
    xCust = [instance['customer_%d' %i]['coordinates']['x'] for i in range(1,I+1)]    # positions of the points in the plane
    yCust = [instance['customer_%d' %i]['coordinates']['y'] for i in range(1,I+1)]
    x1 = xDep + xCust
    y1 = yDep + yCust
    c = {}
    for i in range(len(x1)):
        #i = 0
        for j in range(len(y1)):
            #j = 1
            c[i,j] = distance(x1[i],y1[i],x1[j],y1[j])
    return I,J,d,M,f,c



if __name__ == "__main__":
    I,J,d,M,f,c = make_data()
    model = flp(I,J,d,M,f,c,cp,cU)
#    model.setPresolve(pyscipopt.SCIP_PARAMSETTING.OFF)
#    model.setHeuristics(pyscipopt.SCIP_PARAMSETTING.OFF)
#    model.disablePropagation()
    model.optimize()    


    EPS = 1.e-9
    x,y,y2 = model.data
    edges = [(i,j) for (i,j) in x if model.getVal(x[i,j]) > EPS]
    facilities = [j for j in y if model.getVal(y[j]) > EPS]
    if len(edges)>I:
        print("Optimal value:", model.getObjVal())
        print("Facilities at nodes:", facilities)
        print("Edges:", edges)
        
        
    #how much does customer 8 get by each depot
    cust8 = [round(model.getVal(x[4,i])) for i in J]
    print("What customer 8 gets by each depot:", cust8)
    
   
        
        
        
#### examining the variables in detail ####

#print('\nis i served by j (binary):')       
#for i in range(I):
#    for j in range(len(J)):
#       print(x[i,j], model.getVal(y2[i,j]))      
#
#print('\nquantity:')        
#for i in range(I):
#    for j in range(len(J)):
#       print(x[i,j],model.getVal(x[i,j]))
#
#
#print('\nwhich facilities are used at all (binary):')
#for j in range(len(J)):
#   print(model.getVal(y[j]))






