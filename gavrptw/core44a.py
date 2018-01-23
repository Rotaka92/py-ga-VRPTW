"""
Created on Sat Jan  8 13:34:07 2018

@author: Robin Tappert
"""


### Coding for the introduction into the genetic algorithm: ###
    
# for the optimum chromosom described
# second in the paper [10, 8, 7, 9, 4, 3, 2, 6, 5, 1], 
# just run the coding

# for the first example in the paper, you have to go to line 309, 
# run the commented code and then run the code lines between 310-317, 
# after defining all the functions above


import os
import random
from json import load
from deap import base, creator, tools
import math

# loading the instance for getting informations about customers 
# and depots
instName = 'R102a'
BASE_DIR = 'C:\\Users\\TapperR\\Desktop\\VRP2\\py-ga-VRPTW'
#BASE_DIR = 'C:\\Users\\Robin\\py-ga-VRPTW'
jsonDataDir = os.path.join(BASE_DIR,'data', 'json')
jsonFile = os.path.join(jsonDataDir, '%s.json' % instName)
with open(jsonFile) as f:
    instance = load(f)
    
    
initCost = 60.0     #cost per initialization a new roboter
indSize = 10        #length of a chromosom
popSize = 80        #Size of the population
cxPb = 0.7          #Probability for a crossover
mutPb = 0.01        #Probability for a mutation
NGen = 100          #Number of iterations 
unitCost = 8        #Cost per entity of distance 

# getting the euclidean distance between A and B
def distance(x1,y1,x2,y2):
    return (math.sqrt((x2-x1)**2 + (y2-y1)**2))*1000



def make_data():
    # amount of customers
    I = 10
    
    # get the demand of each customer
    d = [instance['customer_%d'%i]['demand'] for i in range(1,I+1)]  

    
    # get the x - coordinates of the depots
    xDep = [instance['deport%d' %i]['coordinates']['x']\
            for i in range(3)]
    
    # get the y - coordinates of the depots
    yDep = [instance['deport%d' %i]['coordinates']['y']\
            for i in range(3)]
    
    # get the x - coordinates of the customers
    xCust = [instance['customer_%d' %i]['coordinates']['x']\
             for i in range(1,I+1)]    
    
    # get the y - coordinates of the customers
    yCust = [instance['customer_%d' %i]['coordinates']['y']\
             for i in range(1,I+1)]
    
    # concatenate the coordinates of depots and customers
    x1 = xDep + xCust
    y1 = yDep + yCust
    
    # calculation of the distance between all of them -> matrix
    c = {}
    for i in range(len(x1)):
        #i = 0
        for j in range(len(y1)):
            #j = 1
            c[i,j] = distance(x1[i],y1[i],x1[j],y1[j])
    return I,d,c


I,d,c = make_data()

#calculation of the matrix for the time from A to B
c = {k: c[k] / 60 for k in c.keys()}  



# function for creating the route with its subroutes, lists in list
def ind2route(individual, instance, c):
    ### Initialize a route 
    route = []
    ### set a capacity for the vehicle
    vehicleCapacity = instance['vehicle_capacity']
    #vehicleCapacity = 10
    #when the vehicle has to be back 'home' at the latest
    deportDueTime =  instance['deport1']['due_time']  
    ### Initialize a sub-route with start at the depot
    subRoute = []
    vehicleLoad = 0
    elapsedTime = 0
    lastCustomerID = 1
    for customerID in individual:
        # customerID = 7
        ### Update vehicle load
        demand = instance['customer_%d' % customerID]['demand']
        updatedVehicleLoad = vehicleLoad + demand
        # Update elapsed time
        serviceTime = instance['customer_%d' % customerID]['service_time']
        returnTime = c[customerID+2, 1]    #time to the deport
        updatedElapsedTime = elapsedTime + \
        c[lastCustomerID, customerID+2] + serviceTime + returnTime 
        # Validate vehicle load and elapsed time
        if (updatedVehicleLoad <= vehicleCapacity) and\
        (updatedElapsedTime <= deportDueTime):
            # Add to current sub-route
            subRoute.append(customerID)
            vehicleLoad = updatedVehicleLoad
            elapsedTime = updatedElapsedTime - returnTime
        else:
            # Save current sub-route
            route.append(subRoute)
            # Initialize a new sub-route and add to it
            subRoute = [customerID]
            vehicleLoad = demand
            elapsedTime = c[1, customerID+2] + serviceTime
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
            print('  Vehicle %d\'s route: %s' %\
                  (subRouteCount, subRouteStr))
        routeStr = routeStr + ' - 0'
    if merge:
        print(routeStr)
    return



def evalVRPTW(individual, instance, unitCost=1.0,\
              initCost=0, waitCost=0, delayCost=0, c = c):
    #individual = pop[0], individual = tools.selBest(pop, 1)[0]
    totalCost = 0
    route = ind2route(individual, instance, c)
    totalCost = 0
    for subRoute in route:
        #print (subRoute)      
        #subRoute = [5, 11, 7, 12, 9]
        subRouteTimeCost = 0
        subRouteDistance = 0
        elapsedTime = 0
        lastCustomerID = 1
        for customerID in subRoute:
            # customerID = 9
            # Calculate section distance
            distance = c[lastCustomerID, customerID+2]
            # Update sub-route distance
            subRouteDistance = subRouteDistance + distance
            # Calculate time cost
            arrivalTime = elapsedTime + distance
            timeCost = waitCost * max(instance['customer_%d' %\
                        customerID]['ready_time'] - arrivalTime, 0) +\
        delayCost * max(arrivalTime - instance['customer_%d' %\
                        customerID]['due_time'], 0)
            # Update sub-route time cost
            subRouteTimeCost = subRouteTimeCost + timeCost
            # Update elapsed time
            elapsedTime = arrivalTime + instance['customer_%d' %\
                        customerID]['service_time']
            # Update last customer ID
            lastCustomerID = customerID+2
        # Calculate transport cost
        subRouteDistance = subRouteDistance + c[lastCustomerID, 1]
        subRouteTranCost = initCost + unitCost * subRouteDistance
        # Obtain sub-route cost
        subRouteCost = subRouteTimeCost + subRouteTranCost
        # Update total cost
        totalCost = totalCost + subRouteCost
    fitness = 1.0 / totalCost
    return fitness,



# Defining the crossover-process
def cxPartialyMatched(ind1, ind2):
    size = min(len(ind1), len(ind2))
    cxpoint1, cxpoint2 = sorted(random.sample(range(size), 2))
    temp1 = ind1[cxpoint1:cxpoint2+1] + ind2
    temp2 = ind1[cxpoint1:cxpoint2+1] + ind1
    ind1 = []
    for x in temp1:
        if x not in ind1:
            ind1.append(x)
    ind2 = []
    for x in temp2:
        if x not in ind2:
            ind2.append(x)
    return ind1, ind2

# Defining the mutation-process
def mutInverseIndexes(individual):
    start, stop = sorted(random.sample(range(len(individual)), 2))
    individual = individual[:start] +\
    individual[stop:start-1:-1] + individual[stop+1:]
    return individual,

# main-function, which runs through the last command
def gaVRPTW(instance, instName, initCost, indSize,\
            popSize, cxPb, mutPb, NGen, c):
    creator.create('FitnessMax', base.Fitness, weights=(1.0,))
    creator.create('Individual', list, fitness=creator.FitnessMax)
    #creator.Individual()
    toolbox = base.Toolbox()
    # Attribute generator
    toolbox.register('indexes', random.sample,\
                     range(1, indSize + 1), indSize)
    #toolbox.indexes()
    # Structure initializers
    toolbox.register('individual', tools.initIterate,\
                     creator.Individual, toolbox.indexes)
    #toolbox.individual()
    toolbox.register('population', tools.initRepeat,\
                     list, toolbox.individual)
    #toolbox.population(n=popSize)
    # Operator registering
    toolbox.register('evaluate', evalVRPTW, instance=instance,\
                     unitCost=unitCost, initCost=initCost, c=c)
    #toolbox.evaluate()
    toolbox.register('select', tools.selRoulette)
    toolbox.register('mate', cxPartialyMatched)
    toolbox.register('mutate', mutInverseIndexes)
    #pop[0]
    pop = toolbox.population(n=popSize)
    # Evaluate the entire population
    fitnesses = list(map(toolbox.evaluate, pop))
    for ind, fit in zip(pop, fitnesses):
        #print (ind,fit)
        ind.fitness.values = fit

    # Begin the evolution
    for g in range(NGen):
        # Select the next generation individuals by
        #selecting individuals from the precious population randomly
        offspring = toolbox.select(pop, len(pop))
        # Clone the selected individuals
        offspring = list(map(toolbox.clone, offspring))
        #offspring2 = list(map(toolbox.clone, offspring))
        #t == offspring[79], offspring == offspring2
        

        
        # Apply crossover and mutation on the offspring
        for child1, child2 in zip(offspring[::2], offspring[1::2]):
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
        # Evaluate the individuals with an invalid fitness
        # because the same individuals was used
        # in the crossover/ mutation as parents
        
        invalidInd = [ind for ind in offspring if not\
                      ind.fitness.valid]       
        fitnesses = map(toolbox.evaluate, invalidInd)
        for ind, fit in zip(invalidInd, fitnesses):
            ind.fitness.values = fit
            
        # The population is entirely replaced by the offspring
        pop[:] = offspring
        # Gather all the fitnesses in one list and print the stats
        fits = [ind.fitness.values[0] for ind in pop]
        #len(fits)
        length = len(pop)
        mean = sum(fits) / length
        
    bestInd = tools.selBest(pop, 1)[0]
    
    #### For evaluating the chromosome which is
    #examined in the paper, run this Individual ####
    
    #bestInd = creator.Individual([4, 3, 7, 9, 5, 2, 8, 6, 10, 1])
    #bestInd = creator.Individual([10, 8, 7, 9, 4, 3, 2, 6, 5, 1])
    #fit = toolbox.evaluate(bestInd)
    #bestInd.fitness.values = fit
    print('Best individual: %s' % bestInd)
    print('Fitness: %s' % bestInd.fitness.values[0])
    printRoute(ind2route(bestInd, instance, c))
    print('Total cost: %s' % (1 / bestInd.fitness.values[0]))


if __name__ == '__main__':
    random.seed(66)
    gaVRPTW(instance=instance,
                instName=instName,
                initCost=initCost,
                indSize=indSize,
                popSize=popSize,
                cxPb=cxPb,
                mutPb=mutPb,
                NGen=NGen,
                c = c)