# -*- coding: utf-8 -*-

import os
import random
from json import load
import numpy as np
import pandas as pd
from csv import DictWriter
from deap import base, creator, tools
from operator import attrgetter
from . import BASE_DIR
from .utils import makeDirsForFile, exist


#os.chdir('C:\\Users\\TapperR\\Desktop\\VRP2\\py-ga-VRPTW')
#os.chdir('C:\\Users\\Robin\\py-ga-VRPTW')


def ind2route(individual, instance):
    #individual = pop[0], individual = bestInd 
    route = []
    vehicleCapacity = instance['vehicle_capacity']
    deportReadyTime = instance['deport']['due_time']    #when the vehicle can start soonest, has to be implemented somewhere
    deportDueTime =  instance['deport']['due_time']     #when the vehicle has to be back 'home'
    ### Initialize a sub-route
    subRoute = []
    vehicleLoad = 0
    elapsedTime = 0
    subRouteDist = 0
    lastCustomerID = 0
    for customerID in individual:
        # customerID = 5
        ### Update vehicle load
        demand = instance['customer_%d' % customerID]['demand']
        dist = instance['distance_matrix'][lastCustomerID][customerID]
        subRouteDist = subRouteDist + dist + instance['distance_matrix'][customerID][0]
        updatedVehicleLoad = vehicleLoad + demand
        # Update elapsed time
        serviceTime = instance['customer_%d' % customerID]['service_time']
        returnTime = instance['distance_matrix'][customerID][0]    #time to the deport
        updatedElapsedTime = elapsedTime + instance['distance_matrix'][lastCustomerID][customerID] + serviceTime + returnTime 
        # Validate vehicle load, elapsed time and the accumulator capacities
        if (updatedVehicleLoad <= vehicleCapacity) and (updatedElapsedTime <= deportDueTime)\
        and updatedElapsedTime<=instance['accpower_time'] and subRouteDist <= instance['accpower_len']:
            # Add to current sub-route
            subRoute.append(customerID)
            vehicleLoad = updatedVehicleLoad
            elapsedTime = updatedElapsedTime - returnTime
            subRouteDist = subRouteDist - instance['distance_matrix'][customerID][0]
        else:
            # Save current sub-route
            route.append(subRoute)
            # Initialize a new sub-route and add to it
            subRoute = [customerID]
            vehicleLoad = demand
            subRouteDist = instance['distance_matrix'][0][customerID]
            elapsedTime = instance['distance_matrix'][0][customerID] + serviceTime
        # Update last customer ID
        lastCustomerID = customerID
    if subRoute != []:
        # Save current sub-route before return if not empty
        route.append(subRoute)
    return route


def printRoute(route, merge=False):
    routeStr = '0'
    subRouteCount = 0
    for subRoute in route:
        #print (subRoute), subroute = route[0]
        subRouteCount += 1
        subRouteStr = '0'
        for customerID in subRoute:
            subRouteStr = subRouteStr + ' - ' + str(customerID)
            routeStr = routeStr + ' - ' + str(customerID)
        subRouteStr = subRouteStr + ' - 0'
        if not merge:
            print('  Vehicle %d\'s route: %s' % (subRouteCount, subRouteStr))
        routeStr = routeStr + ' - 0'
    if merge:
        print(routeStr)
    return






def evalVRPTW(individual, instance, unitCost=1.0, initCost=0, waitCost=0, delayCost=0, persCost = 0):
    #individual = pop[0], individual = tools.selBest(pop, 1)[0], individual = bestInd
    totalCost = 0
    route = ind2route(individual, instance)
    totalCost = 0
    for subRoute in route:
        #print (subRoute)      
        #subRoute = [5, 11, 7, 12, 9]
        subRouteTimeCost = 0
        subRouteDistance = 0
        elapsedTime = 0
        lastCustomerID = 0
        for customerID in subRoute:
            # customerID = 5
            # Calculate section distance
            distance = instance['distance_matrix'][lastCustomerID][customerID]
            # Update sub-route distance
            subRouteDistance = subRouteDistance + distance
            # Calculate time cost
            arrivalTime = elapsedTime + distance
            timeCost = delayCost * max(arrivalTime - instance['customer_%d' % customerID]['due_time'], 0)
            # Update sub-route time cost
            subRouteTimeCost = subRouteTimeCost + timeCost
            # Update elapsed time for the two cases, both waiting for the customer and arriving at the customer after his ready_time
            if arrivalTime > instance['customer_%d' % customerID]['ready_time']:
                elapsedTime = arrivalTime + instance['customer_%d' % customerID]['service_time']
            else:
                elapsedTime = instance['customer_%d' % customerID]['ready_time'] + instance['customer_%d' % customerID]['service_time']
            # Update last customer ID
            lastCustomerID = customerID
        # Calculate transport cost
        subRouteDistance = subRouteDistance + instance['distance_matrix'][lastCustomerID][0]
        subRouteTranCost = initCost + unitCost * subRouteDistance
        # Obtain sub-route cost
        subRouteCost = subRouteTimeCost + subRouteTranCost
        # Update total cost
        totalCost = totalCost + subRouteCost
    #for-loop for the accumulation of the personal costs in case of more than one deport-station    
    personalCost = persCost*(instance['deport']['due_time']-instance['deport']['ready_time'])
    totalCost = totalCost + personalCost
    fitness = 1.0 / totalCost
    return fitness,


def cxPartialyMatched(ind1, ind2):
    #ind1 = child1, ind2 = child2
    size = min(len(ind1), len(ind2))
    cxpoint1, cxpoint2 = sorted(random.sample(range(size), 2))
    temp1 = ind1[cxpoint1:cxpoint2+1] + ind2
    temp2 = ind1[cxpoint1:cxpoint2+1] + ind1
    ind1 = []
    for x in temp1:
        #x=10
        if x not in ind1:
            ind1.append(x)
    ind2 = []
    for x in temp2:
        if x not in ind2:
            ind2.append(x)
    return ind1, ind2


def mutInverseIndexes(individual):
    #individual = offspring[0]
    start, stop = sorted(random.sample(range(len(individual)), 2))
    individual = individual[:start] + individual[stop:start-1:-1] + individual[stop+1:]
    return individual,


def gaVRPTW(instName, unitCost, initCost, waitCost, delayCost, persCost, indSize, popSize, cxPb, mutPb, NGen, exportCSV=False, customizeData=False):
    #BASE_DIR = 'C:\\Users\\TapperR\\Desktop\\py-ga-VRPTW-master (2)\\py-ga-VRPTW-master'
    if customizeData:
        jsonDataDir = os.path.join(BASE_DIR,'data', 'json_customize')
    else:
        jsonDataDir = os.path.join(BASE_DIR,'data', 'json')
    jsonFile = os.path.join(jsonDataDir, '%s.json' % instName)
    with open(jsonFile) as f:
        instance = load(f)
    creator.create('FitnessMax', base.Fitness, weights=(1.0,))
    creator.create('Individual', list, fitness=creator.FitnessMax)
    #creator.Individual()
    toolbox = base.Toolbox()
    # Attribute generator
    toolbox.register('indexes', random.sample, range(1, indSize + 1), indSize)
    #toolbox.indexes()
    # Structure initializers
    toolbox.register('individual', tools.initIterate, creator.Individual, toolbox.indexes)
    #toolbox.individual()
    toolbox.register('population', tools.initRepeat, list, toolbox.individual)
    #toolbox.population(n=popSize)
    # Operator registering
    toolbox.register('evaluate', evalVRPTW, instance=instance, unitCost=unitCost, initCost=initCost, waitCost=waitCost, delayCost=delayCost, persCost=persCost)
    #toolbox.evaluate()
    toolbox.register('select', tools.selRoulette)
    toolbox.register('mate', cxPartialyMatched)
    toolbox.register('mutate', mutInverseIndexes)
    #pop[0]
    pop = toolbox.population(n=popSize)
    # Results holders for exporting results to CSV file
    csvData = []
#    print('Start of evolution')
    # Evaluate the entire population
    fitnesses = list(map(toolbox.evaluate, pop))
    for ind, fit in zip(pop, fitnesses):
        #print (ind,fit)
        ind.fitness.values = fit
    #max(fitnesses)
#    print('  Evaluated %d individuals' % len(pop))
    # Begin the evolution
    for g in range(NGen):
        #print (g), g=0, g=1
        #print('-- Generation %d --' % g)
        # Select the next generation individuals by selecting individuals from the precious population randomly
        #pop1 in pop, pop[79] = pop1, pop1 in offspring, offspring = toolbox.select(pop, 400), offspring[0] == pop [0] 
        offspring = toolbox.select(pop, len(pop))
        # Clone the selected individuals
        offspring = list(map(toolbox.clone, offspring))
        #offspring2 = list(map(toolbox.clone, offspring))
        #t == offspring[79], offspring == offspring2
        

        
        # Apply crossover and mutation on the offspring
        for child1, child2 in zip(offspring[::2], offspring[1::2]):
        #for child1, child2 in zip(offspring2[::2], offspring2[1::2]):
            #print (child1, child2), child1, child2 = offspring[0], offspring[1], cxPb = 0.8, pop[1].fitness.values, child1, child2 = pop[0], pop[1] 
            if random.random() < cxPb:
                toolbox.mate(child1, child2)
                #print (child1, child2)
                del child1.fitness.values
                del child2.fitness.values
        #for mutant in offspring2:
        for mutant in offspring:
            #mutant = offspring[0]
            if random.random() < mutPb:
                toolbox.mutate(mutant)
                del mutant.fitness.values
        # Evaluate the individuals with an invalid fitness, because the same individuals was used in the crossover/ mutation as parents
        # child1 in offspring, child2 in offspring, mutant in offspring, ind1 = pop[0], offspring[1].fitness.values, ind = child2
        invalidInd = [ind for ind in offspring if not ind.fitness.valid]       
        fitnesses = map(toolbox.evaluate, invalidInd)
        for ind, fit in zip(invalidInd, fitnesses):
            ind.fitness.values = fit
#        print('  Evaluated %d individuals' % len(invalidInd))
        
        
        
        
        
        # The population is entirely replaced by the offspring
        pop[:] = offspring
        # Gather all the fitnesses in one list and print the stats
        fits = [ind.fitness.values[0] for ind in pop]
        #len(fits)
        length = len(pop)
        mean = sum(fits) / length
#        print (mean)
        
        
        
        
        sum2 = sum(x*x for x in fits)
        std = abs(sum2 / length - mean**2)**0.5
#        print('  Min %s' % min(fits))
#        print('  Max %s' % max(fits))
#        print('  Avg %s' % mean)
#        print('  Std %s' % std)
        # Write data to holders for exporting results to CSV file
        if exportCSV:
            csvRow = {
                'generation': g,
                'evaluated_individuals': len(invalidInd),
                'min_fitness': min(fits),
                'max_fitness': max(fits),
                'avg_fitness': mean,
                'std_fitness': std,
            }
            csvData.append(csvRow)
#    print('-- End of (successful) evolution --')
    bestInd = tools.selBest(pop, 1)[0]
    
    #### For evaluating the chromosome which is examined in the paper, run this Individual ####
    #bestInd = creator.Individual([5, 11, 7, 12, 9, 14, 15, 2, 4, 6, 13, 1, 3, 8, 10])
    #bestInd = creator.Individual([5, 6, 13, 14, 15, 4, 3, 10, 11, 7, 8, 12, 1, 2, 9])
    #fit = toolbox.evaluate(bestInd)
    #bestInd.fitness.values = fit
    print('Best individual: %s' % bestInd)
    print('Fitness: %s' % bestInd.fitness.values[0])
    printRoute(ind2route(bestInd, instance))
    print('Total cost: %s' % (1 / bestInd.fitness.values[0]))
    if exportCSV:
        csvFilename = '%s_uC%s_iC%s_wC%s_dC%s_iS%s_pS%s_cP%s_mP%s_nG%s.csv' % (instName, unitCost, initCost, waitCost, delayCost, indSize, popSize, cxPb, mutPb, NGen)
        csvPathname = os.path.join(BASE_DIR, 'results', csvFilename)
        print('Write to file: %s' % csvPathname)
        makeDirsForFile(pathname=csvPathname)
        if not exist(pathname=csvPathname, overwrite=True):
            with open(csvPathname, 'w') as f:
                fieldnames = ['generation', 'evaluated_individuals', 'min_fitness', 'max_fitness', 'avg_fitness', 'std_fitness']
                writer = DictWriter(f, fieldnames=fieldnames, dialect='excel')
                writer.writeheader()
                for csvRow in csvData:
                    writer.writerow(csvRow)








########### Examining each of the deap-tools in detail ############


#
#def selRoulette(individuals, k, fit_attr="fitness"):
#    """Select *k* individuals from the input *individuals* using *k*
#    spins of a roulette. The selection is made by looking only at the first
#    objective of each individual. The list returned contains references to
#    the input *individuals*.
#    
#    :param individuals: A list of individuals to select from.
#    :param k: The number of individuals to select.
#    :param fit_attr: The attribute of individuals to use as selection criterion
#    :returns: A list of selected individuals.
#    
#    This function uses the :func:`~random.random` function from the python base
#    :mod:`random` module.
#    
#    .. warning::
#       The roulette selection by definition cannot be used for minimization 
#       or when the fitness can be smaller or equal to 0.
#    """
#
#
##individuals = pop, k = len(pop), fit_attr="fitness"
#
#    s_inds = sorted(individuals, key=attrgetter(fit_attr), reverse=True)
#    #fitnesses = list(map(toolbox.evaluate, s_inds))    
#    sum_fits = sum(getattr(ind, fit_attr).values[0] for ind in individuals)
#    #ind = s_inds[0]
#    chosen = []
#    for i in range(k):
#        #i = 0
#        u = random.random() * sum_fits
#        sum_ = 0
#        #i = 0
#        for ind in s_inds:
#            #ind = s_inds[0],
#            sum_ += getattr(ind, fit_attr).values[0]
#            #i +=1
#            if sum_ > u:
#                chosen.append(ind)
#                break
#    
#    return chosen
#
#
#def cxPartialyMatched(ind1, ind2):
#    #ind1 = child1, ind2 = child2
#    size = min(len(ind1), len(ind2))
#    cxpoint1, cxpoint2 = sorted(random.sample(range(size), 2))
#    temp1 = ind1[cxpoint1:cxpoint2+1] + ind2
#    temp2 = ind1[cxpoint1:cxpoint2+1] + ind1
#    ind1 = []
#    for x in temp1:
#        #x=10
#        if x not in ind1:
#            ind1.append(x)
#    ind2 = []
#    for x in temp2:
#        if x not in ind2:
#            ind2.append(x)
#    return ind1, ind2
#
#
#def cxPartialyMatched(ind1, ind2):
#    """Executes a partially matched crossover (PMX) on the input individuals.
#    The two individuals are modified in place. This crossover expects
#    :term:`sequence` individuals of indices, the result for any other type of
#    individuals is unpredictable.
#    
#    :param ind1: The first individual participating in the crossover.
#    :param ind2: The second individual participating in the crossover.
#    :returns: A tuple of two individuals.
#    Moreover, this crossover generates two children by matching
#    pairs of values in a certain range of the two parents and swapping the values
#    of those indexes. For more details see [Goldberg1985]_.
#    This function uses the :func:`~random.randint` function from the python base
#    :mod:`random` module.
#    
#    .. [Goldberg1985] Goldberg and Lingel, "Alleles, loci, and the traveling
#       salesman problem", 1985.
#    """
#    #ind1 = child1, ind2 = child2
#    size = min(len(ind1), len(ind2))
#    p1, p2 = [0]*size, [0]*size
#
#    # Initialize the position of each indices in the individuals
#    for i in range(size):
#        #i = 0
#        p1[ind1[i]] = i
#        p2[ind2[i]] = i
#    # Choose crossover points
#    cxpoint1 = random.randint(0, size)
#    cxpoint2 = random.randint(0, size - 1)
#    if cxpoint2 >= cxpoint1:
#        cxpoint2 += 1
#    else: # Swap the two cx points
#        cxpoint1, cxpoint2 = cxpoint2, cxpoint1
#    
#    # Apply crossover between cx points
#    for i in range(cxpoint1, cxpoint2):
#        # Keep track of the selected values
#        temp1 = ind1[i]
#        temp2 = ind2[i]
#        # Swap the matched value
#        ind1[i], ind1[p1[temp2]] = temp2, temp1
#        ind2[i], ind2[p2[temp1]] = temp1, temp2
#        # Position bookkeeping
#        p1[temp1], p1[temp2] = p1[temp2], p1[temp1]
#        p2[temp1], p2[temp2] = p2[temp2], p2[temp1]
#    
#    return ind1, ind2
#
#
#
##### giving the first 15 x and y coordinates for the system of coordinates ####
#import matplotlib.pyplot as plt
#coord = pd.DataFrame({'x': [], 'y': []})
#
#for i in np.arange(1,len(bestInd)+1):
#    p = instance['customer_%d' % i]['coordinates']
#    t   = pd.DataFrame([p])
#    coord = coord.append(t)
#
#
#coord.reset_index(inplace = True, drop = True)
#
#plt.scatter(x = coord['x'].values, y = coord['y'].values)
#




#### Clustering with k-Means ####

#from sklearn.cluster import KMeans
#
#X = np.array([[1, 2], [1, 4], [1, 0], [4, 2], [4, 4], [4, 0]])
#
#X = pd.DataFrame(X)
#kmeans = KMeans(n_clusters=2, random_state=0).fit(X)
#kmeans.labels_
#kmeans.predict([[0, 0], [4, 4]])
#kmeans.cluster_centers_
#
#
#kmeans = KMeans(n_clusters=2, random_state=0).fit(coord)
#kmeans.labels_
#kmeans.predict([[0, 0], [4, 4]])
#kmeans.cluster_centers_





#### Facility location problem with more than one depot ####
#
#import pyscipopt
#from pyscipopt import Model, multidict, quicksum
#
#
##I = Index of customer, d = demand of each customer
#I, d = multidict({1:80, 2:270, 3:250, 4:160, 5:180})
#
#
##Index of basis station, max Capacity of the station, fix cost of opening the station
#J, M, f = multidict({1:[500,1000], 2:[500,1000], 3:[500,1000]})
#
#
##cost per unit for each road
#c = {(1,1):4,  (1,2):6,  (1,3):9,
#     (2,1):5,  (2,2):4,  (2,3):7,
#     (3,1):6,  (3,2):3,  (3,3):4,
#     (4,1):8,  (4,2):5,  (4,3):3,
#     (5,1):10, (5,2):8,  (5,3):4,
#     }
#
#
#
#
#def flp(I,J,d,M,f,c):
#    model = Model("flp")
#    x,y = {},{}
#    for j in J:
#        #j = 1
#        y[j] = model.addVar(vtype="B", name="y(%s)"%j)
#        for i in I:
#            #i = 1
#            x[i,j] = model.addVar(vtype="C", name="x(%s,%s)"%(i,j))
#    for i in I:
#        #i = 1,2,3,4,5
#        model.addCons(quicksum(x[i,j] for j in J) == d[i], "Demand(%s)"%i)
#    for j in M:
#        #j = 1,2,3
#        model.addCons(quicksum(x[i,j] for i in I) <= M[j]*y[j], "Capacity(%s)"%i)
#    for (i,j) in x:
#        #(i,j) = (1,1), (2,1), ...
#        model.addCons(x[i,j] <= d[i]*y[j], "Strong(%s,%s)"%(i,j))
#    model.setObjective(
#        quicksum(f[j]*y[j] for j in J) +
#        quicksum(c[i,j]*x[i,j] for i in I for j in J),
#        "minimize")
#    model.data = x,y
#    return model
#
#
#model = flp(I, J, d, M, f, c)
#model.optimize()
#EPS = 1.e-6
#x,y = model.__data
#edges = [(i,j) for (i,j) in x if model.GetVal(x[i,j]) > EPS]
#facilities = [j for j in y if model.GetVal(y[j]) > EPS]
#print ("Optimal value=", model.GetObjVal())
#print ("Facilities at nodes:", facilities)
#print ("Edges:", edges)
#
#
#
#
#





#from gurobipy import *
#import math
#
#def distance(a,b):
#  dx = a[0] - b[0]
#  dy = a[1] - b[1]
#  return math.sqrt(dx*dx + dy*dy)
#
## Problem data
#clients = [[0, 1.5],[2.5, 1.2]]
#facilities = [[0,0],[0,1],[0,1],
#              [1,0],[1,1],[1,2],
#              [2,0],[2,1],[2,2]]
#charge = [3,2,3,1,3,3,4,3,2]
#
#numFacilities = len(facilities)
#numClients = len(clients)
#
#m = Model()
#
## Add variables
#x = {}
#y = {}
#d = {} # Distance matrix (not a variable)
#alpha = 1
#
#for j in range(numFacilities):
#  x[j] = m.addVar(vtype=GRB.BINARY, name="x%d" % j)
#
#for i in range(numClients):
#  for j in range(numFacilities):
#    y[(i,j)] = m.addVar(lb=0, vtype=GRB.CONTINUOUS, name="t%d,%d" % (i,j))
#    d[(i,j)] = distance(clients[i], facilities[j])
#
#m.update()
#
## Add constraints
#for i in range(numClients):
#  for j in range(numFacilities):
#    m.addConstr(y[(i,j)] <= x[j])
#
#for i in range(numClients):
#  m.addConstr(quicksum(y[(i,j)] for j in range(numFacilities)) == 1)
#
#m.setObjective( quicksum(charge[j]*x[j] + quicksum(alpha*d[(i,j)]*y[(i,j)]
#                for i in range(numClients)) for j in range(numFacilities)) )
#
#m.optimize()
#
#




















