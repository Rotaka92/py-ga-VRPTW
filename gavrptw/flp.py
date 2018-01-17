# -*- coding: utf-8 -*-
"""
Created on Fri Jan  5 21:42:13 2018

@author: Robin
"""


#### Facility location problem with more than one depot ####

from pyscipopt import Model, multidict, quicksum


#I = Index of customer, d = demand of each customer
I, d = multidict({1:80, 2:270, 3:250, 4:160, 5:180})


#Index of basis station, max Capacity of the station, fix cost of opening the station
J, M, f = multidict({1:[500,1000], 2:[500,1000], 3:[500,1000]})


#cost per unit for each road
c = {(1,1):4,  (1,2):6,  (1,3):9,
     (2,1):5,  (2,2):4,  (2,3):7,
     (3,1):6,  (3,2):3,  (3,3):4,
     (4,1):8,  (4,2):5,  (4,3):3,
     (5,1):10, (5,2):8,  (5,3):4,
     }




def flp(I,J,d,M,f,c):
    model = Model("flp")
    x,y = {},{}
    for j in J:
        #j = 1
        y[j] = model.addVar(vtype="B", name="y(%s)"%j)
        for i in I:
            #i = 1
            x[i,j] = model.addVar(vtype="C", name="x(%s,%s)"%(i,j))
    for i in I:
        #i = 1,2,3,4,5
        model.addCons(quicksum(x[i,j] for j in J) == d[i], "Demand(%s)"%i)
    for j in M:
        #j = 1,2,3
        model.addCons(quicksum(x[i,j] for i in I) <= M[j]*y[j], "Capacity(%s)"%i)
    for (i,j) in x:
        #(i,j) = (1,1), (2,1), ...
        model.addCons(x[i,j] <= d[i]*y[j], "Strong(%s,%s)"%(i,j))
    model.setObjective(
        quicksum(f[j]*y[j] for j in J) +
        quicksum(c[i,j]*x[i,j] for i in I for j in J),
        "minimize")
    model.data = x,y
    return model


#model.getSols()
#model.getObjective()
#model.getConss()
#model.getVars()[0]
#a = model.getBestSol()
##model.getSolObjVal(a)      #kernel dies
#model.getSolVal(a, var = model.getVars()[0]) #kernel dies


#model = flp(I, J, d, M, f, c)
#model.optimize()
#EPS = 1.e-6
#x,y = model.__data
#edges = [(i,j) for (i,j) in x if model.getVal(x[i,j]) > EPS]
#facilities = [j for j in y if model.getVal(y[j]) > EPS]
#print ("Optimal value=", model.GetObjVal())
#print ("Facilities at nodes:", facilities)
#print ("Edges:", edges)
#


### alternative ####


model = flp(I, J, d, M, f, c)
model.optimize()
EPS = 1.e-6
x,y = model.data
edges = [(i,j) for (i,j) in x if model.getVal(x[i,j]) > EPS]
facilities = [j for j in y if model.getVal(y[j]) > EPS]
print ("Optimal value =", model.getObjVal())
print ("Facilities at nodes:", facilities)
print ("Edges:", edges)



