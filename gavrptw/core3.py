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



#os.chdir('C:\\Users\\TapperR\\Desktop\\VRP2\\py-ga-VRPTW')


def ind2route(individual, instance, stat_nr, dist_matr):
    #individual = pop[0], individual = bestInd 
    route = []
    
    #which specific customers are assigned to the station
    p = []
    for i in instance:
        #print (i), i = 'customer_10'
        if i.startswith('cust'):
            t = i.split('_')[1]
            p.append(t)
            
            
    vehicleCapacity = instance['vehicle_capacity']
    deportDueTime =  instance['deport%d'%stat_nr]['due_time']   #when the vehicle has to be back 'home'
    ### Initialize a sub-route
    subRoute = []
    vehicleLoad = 0
    dist1 = 0
    elapsedTime = instance['deport%d'%stat_nr]['ready_time']
    lastCustomerID = stat_nr
    for customerID in individual:
        # customerID = individual[4]
        ### Update vehicle load
        customerID = customerID - 1
        for i in p:
            #print (i), i = str(4), i = 1
            if instance['customer_%s' % i]['belongs_to'][1] == customerID:
                demand = instance['customer_%s' % i]['demand']
                updatedVehicleLoad = vehicleLoad + demand
                
                # Update distance
                dist1 = dist1 + dist_matr[lastCustomerID, int(i)+2] + dist_matr[stat_nr, int(i)+2]
                
                # Update elapsed time
                serviceTime = instance['customer_%s' % i]['service_time']
                returnTime = (dist_matr[stat_nr, int(i)+2])/60    #time to the deport
                updatedElapsedTime = elapsedTime + (dist_matr[lastCustomerID, int(i)+2]/60) + serviceTime + returnTime 
                arrive = elapsedTime + (dist_matr[lastCustomerID, int(i)+2]/60)
                
                # Validate vehicle load, elapsed time and that the delivery is in the time window
                if (updatedVehicleLoad <= vehicleCapacity) and (updatedElapsedTime <= deportDueTime)\
                and instance['customer_%s' % i]['ready_time'] < arrive < instance['customer_%s' % i]['due_time']\
                and updatedElapsedTime < instance['accpower_time']+480 and dist1 < instance['accpower_len']:
                    # Add to current sub-route
                    subRoute.append(i)
                    vehicleLoad = updatedVehicleLoad
                
                    #because the journey continues, delete time and distance to the depot
                    elapsedTime = updatedElapsedTime - returnTime
                    dist1 = dist1 - dist_matr[stat_nr, int(i)+2]
                else:
                    # Save current sub-route
                    route.append(subRoute)
                    # Initialize a new sub-route and add to  it
                    subRoute = [i]
                    vehicleLoad = demand
                    elapsedTime = instance['customer_%s' % i]['ready_time'] + serviceTime
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
            print('  Vehicle %d\'s route: %s' % (subRouteCount, subRouteStr))
        routeStr = routeStr + ' - 0'
    if merge:
        print(routeStr)
    return


        

def evalVRPTW(individual, instance, dist_matr, cU, initCost, persCost, stat_nr):
    #individual = pop[0], individual = tools.selBest(pop, 1)[0], individual = bestInd, unitCost = cU
    totalCost = 0
    route = ind2route(individual, instance, stat_nr, dist_matr)
    totalCost = 0
    for subRoute in route:
        #print (subRoute)      
        #subRoute = ['4', '1']
        subRouteDistance = 0
        lastCustomerID = stat_nr
        for customerID in subRoute:
            # customerID = '4'
            # Calculate section distance
            distance = dist_matr[lastCustomerID, int(customerID)+2]
            # Update sub-route distance
            subRouteDistance = subRouteDistance + distance
            # Update last customer ID
            lastCustomerID = int(customerID)
            
        # Calculate transport cost
        subRouteDistance = subRouteDistance + dist_matr[lastCustomerID, stat_nr]
        subRouteTranCost = initCost + cU * subRouteDistance
        # Obtain sub-route cost
        subRouteCost = subRouteTranCost
        # Update total cost
        totalCost = totalCost + subRouteCost        
    personalCost = persCost*(instance['deport%d'%stat_nr]['due_time']-instance['deport%d'%stat_nr]['ready_time'])
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


def gaVRPTW(instance, stat_nr, dist_matr, instName, cU, initCost, persCost, indSize, popSize, cxPb, mutPb, NGen):
    #BASE_DIR = 'C:\\Users\\TapperR\\Desktop\\py-ga-VRPTW-master (2)\\py-ga-VRPTW-master', dist_matr = c, 
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
    toolbox.register('evaluate', evalVRPTW, instance=instance, dist_matr = dist_matr, cU=cU, initCost=initCost,  persCost=persCost, stat_nr=stat_nr)
    #toolbox.evaluate()
    toolbox.register('select', tools.selRoulette)
    toolbox.register('mate', cxPartialyMatched)
    toolbox.register('mutate', mutInverseIndexes)
    #pop[0]
    pop = toolbox.population(n=popSize)
    # Results holders for exporting results to CSV file
    # csvData = []
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
#    print('-- End of (successful) evolution --')
    bestInd = tools.selBest(pop, 1)[0]
    
    #### For evaluating the chromosome which is examined in the paper, run this Individual ####
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
































