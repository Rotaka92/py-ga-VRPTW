# -*- coding: utf-8 -*-
# sample_R101.py

import random
from gavrptw.core3 import gaVRPTW

### seed 0 for the optimum in vehicle = 3, customers = 15 ###


def main():
    ### for a good solution, which is descriped at first in the paper ###
    #random.seed(64)
    
    ### for the optimum, which is also described in the paper, uncomment this random.seed-function ###
    random.seed(52)
        
    instName = 'R101'
    
    unitCost = 8.0
    initCost = 1500.0
    persCost = 0.4
    
    indSize = 15
    popSize = 80
    cxPb = 0.7
    mutPb = 0.01
    NGen = 100
    
    exportCSV = False

    gaVRPTW(
        instName=instName,
        unitCost=unitCost,
        initCost=initCost,
        persCost = persCost,
        indSize=indSize,
        popSize=popSize,
        cxPb=cxPb,
        mutPb=mutPb,
        NGen=NGen,
        exportCSV=exportCSV
    )
    

if __name__ == '__main__':
    main()


#
#
#Best individual: [5, 6, 13, 14, 15, 4, 3, 10, 11, 7, 8, 12, 1, 2, 9]
#Total cost: 3777.887270329896




