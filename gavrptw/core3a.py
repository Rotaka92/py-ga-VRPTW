"""
Created on Sat Jan  11 14:24:11 2018

@author: Robin Tappert
"""


### Coding for the modified genetic algorithm: ###

import os
import random
from json import load
import numpy as np
import pandas as pd
from csv import DictWriter
from deap import base, creator, tools
from operator import attrgetter
from . import BASE_DIR


def ind2route(individual, instance, stat_nr, dist_matr):
    route = []
    
    #which specific customers are assigned to the station
    p = []
    for i in instance:
        if i.startswith('cust'):
            t = i.split('_')[1]
            p.append(t)
            
            
    vehicleCapacity = instance['vehicle_capacity']
    #when the vehicle has to be back 'home'
    deportDueTime =  instance['deport%d'%stat_nr]['due_time']   
    ### Initialize a sub-route
    subRoute = []
    vehicleLoad = 0
    dist1 = 0
    elapsedTime = instance['deport%d'%stat_nr]['ready_time']
    lastCustomerID = stat_nr
    for customerID in individual:
        ### Update vehicle load
        customerID = customerID - 1
        for i in p:
            if instance['customer_%s' % i]['belongs_to'][1] == customerID:
                demand = instance['customer_%s' % i]['demand']
                updatedVehicleLoad = vehicleLoad + demand
                
                # Update distance
                dist1 = dist1 + dist_matr[lastCustomerID, int(i)+2]\
                + dist_matr[stat_nr, int(i)+2]
                
                # Update elapsed time
                serviceTime = instance['customer_%s' % i]['service_time']
                #time to the deport
                returnTime = (dist_matr[stat_nr, int(i)+2])/60    
                updatedElapsedTime = elapsedTime + \
                (dist_matr[lastCustomerID, int(i)+2]/60) + \
                serviceTime + returnTime 
                arrive = elapsedTime + \
                (dist_matr[lastCustomerID, int(i)+2]/60)
                
                # Validate vehicle load, elapsed time and
                #that the delivery is in the time window
                if (updatedVehicleLoad <= vehicleCapacity) and\
                (updatedElapsedTime <= deportDueTime)\
                and instance['customer_%s' % i]['ready_time'] < arrive\
                < instance['customer_%s' % i]['due_time']\
                and updatedElapsedTime < instance['accpower_time']+480\
                and dist1 < instance['accpower_len']:
                    # Add to current sub-route
                    subRoute.append(i)
                    vehicleLoad = updatedVehicleLoad
                
                    #because the journey continues,
                    #delete time and distance to the depot
                    elapsedTime = updatedElapsedTime - returnTime
                    dist1 = dist1 - dist_matr[stat_nr, int(i)+2]
                else:
                    # Save current sub-route
                    route.append(subRoute)
                    # Initialize a new sub-route and add to  it
                    subRoute = [i]
                    vehicleLoad = demand
                    elapsedTime = instance['customer_%s' % i]\
                    ['ready_time'] + serviceTime
                    dist1 = 0
                # Update last customer ID
                lastCustomerID = int(i)+2
    if subRoute != []:
                # Save current sub-route before return if not empty
        route.append(subRoute)
        
     
        
    route = [x for x in route if x != []]
    
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
            print('  Vehicle %d\'s route: %s' %\
                  (subRouteCount, subRouteStr))
        routeStr = routeStr + ' - 0'
    if merge:
        print(routeStr)
    return


        

def evalVRPTW(individual, instance, dist_matr,\
              cU, initCost, persCost, stat_nr):
    totalCost = 0
    route = ind2route(individual, instance, stat_nr, dist_matr)
    totalCost = 0
    for subRoute in route:
        subRouteDistance = 0
        lastCustomerID = stat_nr
        for customerID in subRoute:
            # Calculate section distance
            distance = dist_matr[lastCustomerID, int(customerID)+2]
            # Update sub-route distance
            subRouteDistance = subRouteDistance + distance
            # Update last customer ID
            lastCustomerID = int(customerID)
            
        # Calculate transport cost
        subRouteDistance = subRouteDistance +\
        dist_matr[lastCustomerID, stat_nr]
        subRouteTranCost = initCost + cU * subRouteDistance
        # Obtain sub-route cost
        subRouteCost = subRouteTranCost
        # Update total cost
        totalCost = totalCost + subRouteCost        
    personalCost = persCost*(instance['deport%d'%stat_nr]['due_time']-\
                             instance['deport%d'%stat_nr]['ready_time'])
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
    individual = individual[:start] + individual[stop:start-1:-1]\
    + individual[stop+1:]
    return individual,


def gaVRPTW(instance, stat_nr, dist_matr, instName,\
            cU, initCost, persCost, indSize, popSize, cxPb, mutPb, NGen):
    #BASE_DIR = 'C:\\Users\\TapperR\\Desktop\\py-ga-VRPTW-master\
    (2)\\py-ga-VRPTW-master', dist_matr = c, 
    creator.create('FitnessMax', base.Fitness, weights=(1.0,))
    creator.create('Individual', list, fitness=creator.FitnessMax)
    toolbox = base.Toolbox()
    # Attribute generator
    toolbox.register('indexes', random.sample,\
                     range(1, indSize + 1), indSize)
    # Structure initializers
    toolbox.register('individual', tools.initIterate,\
                     creator.Individual, toolbox.indexes)
    toolbox.register('population', tools.initRepeat,\
                     list, toolbox.individual)
    # Operator registering
    toolbox.register('evaluate', evalVRPTW, instance=instance,\
                     dist_matr = dist_matr, cU=cU,\
                     initCost=initCost,  persCost=persCost,\
                     stat_nr=stat_nr)
    toolbox.register('select', tools.selRoulette)
    toolbox.register('mate', cxPartialyMatched)
    toolbox.register('mutate', mutInverseIndexes)
    pop = toolbox.population(n=popSize)
    fitnesses = list(map(toolbox.evaluate, pop))
    for ind, fit in zip(pop, fitnesses):
        ind.fitness.values = fit
    # Begin the evolution
    for g in range(NGen):
        # Select the next generation individuals by
        #selecting individuals from the precious population 
        #by the fortune wheel
        offspring = toolbox.select(pop, len(pop))
        # Clone the selected individuals
        offspring = list(map(toolbox.clone, offspring))
        #offspring2 = list(map(toolbox.clone, offspring))
        #t == offspring[79], offspring == offspring2
        

        
        # Apply crossover and mutation on the offspring
        for child1, child2 in zip(offspring[::2], offspring[1::2]):
            if random.random() < cxPb:
                toolbox.mate(child1, child2)
                del child1.fitness.values
                del child2.fitness.values
        for mutant in offspring:
            if random.random() < mutPb:
                toolbox.mutate(mutant)
                del mutant.fitness.values
        # Evaluate the individuals with an invalid fitness,
        #because the same individuals was used
        #in the crossover/ mutation as parents
        invalidInd = [ind for ind in offspring if not ind.fitness.valid]       
        fitnesses = map(toolbox.evaluate, invalidInd)
        for ind, fit in zip(invalidInd, fitnesses):
            ind.fitness.values = fit
   
        
        # The population is entirely replaced by the offspring
        pop[:] = offspring
        # Gather all the fitnesses in one list and print the stats
        fits = [ind.fitness.values[0] for ind in pop]
        length = len(pop)
        mean = sum(fits) / length
        
        
        
        
        sum2 = sum(x*x for x in fits)
        std = abs(sum2 / length - mean**2)**0.5)
    bestInd = tools.selBest(pop, 1)[0]
    
    #### For evaluating the chromosome which is
    #examined in the paper, run this Individual ####
    #bestInd = creator.Individual([3,4,2,1,5])
    #bestInd = creator.Individual([2,4,3,5,1])
    #fit = toolbox.evaluate(bestInd)
    #bestInd.fitness.values = fit
    print('Best individual: %s' % bestInd)
    print('Fitness: %s' % bestInd.fitness.values[0])
    printRoute(ind2route(bestInd, instance, stat_nr, dist_matr))
    print('Total cost: %s' % (1 / bestInd.fitness.values[0]))
    print('\n\n\n')


    totalCost2 = 1 / bestInd.fitness.values[0]

    return totalCost2































