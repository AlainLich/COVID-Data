# coding: utf-8

# (C) A.Lichnewsky, 2020

__author__ = 'Alain Lichnewsky'
__license__ = 'MIT License'
__version__ = '1.0'


#
#  These are classes for displaying graphics related to data from USA
#
#            ----------------------------------------
 
# Common imports
import math
import numpy             as NP
import numpy.random      as RAND
import scipy.stats       as STATS
from scipy import sparse
from scipy import linalg


import matplotlib        as MPL
import matplotlib.pyplot as PLT
import seaborn as SNS
SNS.set(font_scale=1)

# Python programming
from itertools import cycle
from time import time
import datetime

# Using pandas
import pandas as PAN

from lib.figureHelpers import *
from lib.pandaUtils    import *

# The figure making process is generalized into this class, facilitating coding
# graphics, and also enabling variants as derived classes
#


class perStateFigure(object):
    """ This permits to make figures of data organized by State, it is expected that 
        derived classes will bring different selections and orderings; further 
        parametrization is also envisionned
    """
    def __init__(self, dateStart):
        self.dateStart = dateStart

    def initPainter(self, subnodeSpec=None, figsize=(15,15), maxCol=6, colFirst=False):
        if subnodeSpec is None:
            subnodeSpec = self.subnodeSpec
        elif isinstance(subnodeSpec,int):
            self.subnodeSpec = (lambda i,j:{"nrows":i,"ncols":j})                                        (*subPlotShape( subnodeSpec, maxCol=maxCol,
                                                       colFirst=colFirst))
            subnodeSpec = self.subnodeSpec
            
        self.painter = figureFromFrame(None, subplots=subnodeSpec, figsize=figsize)

    def skipIfCond(self, count, state):
        return False

    def breakIfCond(self, count, state):
        return count > 15

    def getDemographics(self, data_USAPopChangeTbl):
        """
            Watch out, here we need the data showing the population  per state, so 
            we just get it from an argument, which should have been loaded by something
            like:
              data_USAPopChangeTbl = read_csvPandas(ad(USAPopChangeCSV), error_bad_lines=False, sep="," )
        """
        demogrCols=("SUMLEV","STATE","NAME","POPESTIMATE2019" )
        demogrX = data_USAPopChangeTbl.loc[:,demogrCols]
        demogrX["SUMLEV"]== 40
        self.demogr = demogrX[demogrX["SUMLEV"]== 40 ].copy() 

        
    def getPop(self, state, dfx, doPrint=True):
            # get the population for the state (plus state name)
            fips = dfx.iloc[0,:].loc["fips"]
            demox = self.demogr.loc[self.demogr ["STATE"] == fips, :]
            if demox.shape[0] < 1:
                print(f"Issue with state encoding: state={state}")  
                self.abbrevIssueList.append(state)
                stName = None
                stPop  = None
            else:
                stName = demox.loc[:, "NAME"].iloc[0]
                stPop = demox.loc[:, "POPESTIMATE2019"].iloc[0]
            if doPrint:
                print(f"state={state}:{stName} fips={fips} pop={stPop}")
            return (stName, stPop, fips)
        
    def getPopStateTble(self,  groupedDF):
        data = []
        for (state, dfExtractOrig) in groupedDF:
            stName, stPop, fips = self.getPop(state, dfExtractOrig, doPrint=False)
            data.append( (state, stName, stPop, fips) )
            
        df = PAN.DataFrame(data, columns=("state","stName","pop","fips" ))
        return df
        
    def mkImage(self, groupedDF, plotCols):
        count = 0
        self.abbrevIssueList=[]
        
        for (state, dfExtractOrig) in groupedDF:
            count+=1
            if self.skipIfCond(count, state):
                continue
            if self.breakIfCond(count, state):
                break
            
            stName, stPop, fips = self.getPop(state, dfExtractOrig)
            if stPop is None:
                continue

            dfExtract = dfExtractOrig.set_index("elapsedDays").copy()

            for c in plotCols:
                dfExtract.loc[:,c] = dfExtract.loc[:,c]/stPop*1.0e6

            self.painter.doPlot(df = dfExtract.loc[:, plotCols] )
            self.painter.setAttrs(label=f"Days since {self.dateStart}",
                         title=f"Data from USA CovidTracking: {stName}",
                         legend=True,
                         xlabel=f"Days since {self.dateStart}",
                         ylabel="Events per million population"   )
        
            self.painter.advancePlotIndex()  


class perStateSelected(perStateFigure):
    def __init__(self, dateStart, select):
        perStateFigure.__init__(self, dateStart)
        self.selected = select
        
    def skipIfCond(self, count, state):
        return state not in self.selected
    
    def breakIfCond(self, count, state):
        return False
            
