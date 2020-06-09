#!/usr/bin/env python
# coding: utf-8

# # Analyze population data from https://covidtracking.com
# 
# 
# **Note:** This is a Jupyter notebook which is also available as its executable export as a Python 3 script (therefore with automatically generated comments).

# # Libraries

# In[ ]:


# Sys import
import sys, os, re
# Common imports
import math
import numpy             as NP
import numpy.random      as RAND
import scipy.stats       as STATS
from scipy import sparse
from scipy import linalg

# Better formatting functions
from IPython.display import display, HTML
from IPython import get_ipython

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
import xlrd


# In[ ]:


import warnings
warnings.filterwarnings('ignore')
print("For now, reduce python warnings, I will look into this later")


# ### Import my own modules
# The next cell attempts to give user some information if things improperly setup.
# Intended to work both in Jupyter and when executing the Python file directly.

# In[ ]:


if not get_ipython() is None and os.path.abspath("../source/") not in sys.path:
    sys.path.append(os.path.abspath("../source/"))
try:
    from lib.utilities     import *
    from lib.figureHelpers import *
    from lib.DataMgrJSON   import *
    from lib.DataMgr       import *
    from lib.pandaUtils    import *
except Exception as err:
    print("Could not find library 'lib' with contents 'DataGouvFr' ")
    if get_ipython() is None:
        print("Check the PYTHONPATH environment variable which should point to 'source' wich contains 'lib'")
    else:
        print("You are supposed to be running in JupySessions, and '../source/lib' should exist")
    raise err


# In[ ]:


from IPython.core.display import display, HTML
display(HTML("<style>.container { width:100% !important; }</style>"))


# ## Check environment
# 
# It is expected that:
# - your working directory is named `JupySessions`, 
# - that it has subdirectories 
#    - `images/*` where generated images may be stored to avoid overcrowding. 
# - At the same level as your working dir there should be directories 
#    - `../data` for storing input data and 
#    - `../source` for python scripts.
#    
# My package library is in `../source/lib`, and users running under Python (not in Jupyter) should
# set their PYTHONPATH to include "../source" ( *or whatever appropriate* ).

# In[ ]:


checkSetup(chap="Chap04")
ImgMgr = ImageMgr(chapdir="Chap04")


# # Load Data

# ## Functions

# ## Load CSV and XLSX data from remote 
# The `dataFileVMgr` will manage a cache of data files in `../dataUSCovidTrack`.
# 
# We check what is in the cache/data directory; for each file, we identify the latest version, 
# and list this below to make sure. Files of interest are documented in `.filespecs.json`
# 
# Consulted: https://github.com/COVID19Tracking/covid-tracking-api
#   
# Downloaded: see `.filespecs.json`
#   
#  

# In[ ]:


dataFileVMgr = manageAndCacheFilesJSONHandwritten("../dataUSCovidTrack")


# In[ ]:


dataFileVMgr.getRemoteInfo()
dataFileVMgr.updatePrepare()
dataFileVMgr.cacheUpdate()


# In[ ]:


print("Most recent versions of files in data directory:")
for f in dataFileVMgr.listMostRecent() :
    print(f"\t{f}")


# In[ ]:


last = lambda x: dataFileVMgr.getRecentVersion(x,default=True)


# This ensures we load the most recent version, so that it is not required to update the list 
# below. The timestamps shown in the following sequence will be update by the call to `getRecentVersion`.

# In[ ]:


USStatesDailyCSV    = last('CTStatesDaily.csv' ) 
USStatesInfoCSV     = last('CTStatesInfo.csv')
USDailyCSV          = last('CTUSDaily.csv')

USAPopChangeCSV     =  last('USACensusPopchange.csv')  
USAPopChangeRankCSV =  last('USACensusPopchangeRanks.csv')


# Now load the stuff

# In[ ]:


ad  = lambda x: "../dataUSCovidTrack/"+x

data_USStatesDaily    = read_csvPandas(ad(USStatesDailyCSV) , error_bad_lines=False, sep="," )
data_USStatesInfo     = read_csvPandas(ad(USStatesInfoCSV),   error_bad_lines=False, sep="," )
data_USDaily          = read_csvPandas(ad(USDailyCSV),        error_bad_lines=False, sep="," )
data_USAPopChange     = read_csvPandas(ad(USAPopChangeCSV) ,  error_bad_lines=False, sep="," )
data_USAPopChangeRank = read_csvPandas(ad(USAPopChangeRankCSV), error_bad_lines=False, sep="," )


# Show the shape of the loaded data:

# In[ ]:


def showBasics(data,dataName):
    print(f"{dataName:24}\thas shape {data.shape}")

dataListDescr = ( (data_USStatesDaily, "data_USStatesDaily"),
                  (data_USStatesInfo,  "data_USStatesInfo"),
                  (data_USDaily ,      "data_USDaily"),
                  (data_USAPopChange,  "data_USAPopChange"),
                  (data_USAPopChangeRank, "data_USAPopChangeRank"),
                )
    
for (dat,name) in dataListDescr:
    showBasics(dat,name)


# In[ ]:


for (dat,name) in dataListDescr:
    if name[0:5]=="meta_": continue
    print(f"\nDescription of data in '{name}'\n")
    display(dat.describe().transpose())


# In[ ]:


for (dat,name) in dataListDescr:
    if name[0:5]=="meta_": continue
    print(f"\nInformation about '{name}'\n")
    dat.info()


# ### Get demographics information
# The metadata is in `../dataUSCovidTrack/*.pdf`. We need to preprocess the demographics information for ease of use below. Notice that column `STATE` features state's **FIPS codes**.

# In[ ]:


demogrCols=("SUMLEV","STATE","NAME","POPESTIMATE2019" )
demogrX = data_USAPopChange.loc[:,demogrCols]
demogrX["SUMLEV"]== 40
demogr = demogrX[demogrX["SUMLEV"]== 40 ].copy() 


# In[ ]:


dtCols = ('date','fips', 'state', 
          'positive', 'negative', 
          'hospitalizedCurrently', 'hospitalizedCumulative', 
          'inIcuCurrently', 'inIcuCumulative',
          'onVentilatorCurrently', 'onVentilatorCumulative', 
          'recovered','death', 'hospitalized'
         )


# In[ ]:


dt  = data_USStatesDaily.loc[ :, dtCols].copy()
dt["dateNum"] = PAN.to_datetime(dt.loc[:,"date"], format="%Y%m%d")
dateStart = dt["dateNum"].min()
dateEnd   = dt["dateNum"].max() 
dateSpan  = dateEnd - dateStart 
print(f"Our statistics span {dateSpan.days+1} days, start: {dateStart} and end {dateEnd}")
dt["elapsedDays"] = (dt["dateNum"] - dateStart).dt.days

dt = dt.set_index("state")
dtg = dt.groupby("state")

#dtx = dt[dt.index == "Europe"]
#dtg = dtx.groupby("countriesAndTerritories")


# Now, the figure making process is generalized into this class, since we plan to emit multiple figures.

# In[ ]:


class perStateFigure(object):
    """ This permits to make figures of data organized by State, it is expected that derived classes
        will bring different selections and orderings; further parametrization is also envisionned
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

    def getPop(self, state, dfx, doPrint=True):
            # get the population for the state (plus state name)
            fips = dfx.iloc[0,:].loc["fips"]
            demox = demogr.loc[demogr ["STATE"] == fips, :]
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


# First attempt, just get the first!

# In[ ]:


plotCols=("recovered","death","hospitalized")

psFig =  perStateFigure(dateStart)
psFig.initPainter(subnodeSpec=15, maxCol=3)
psFig.mkImage(dtg,plotCols)
ImgMgr.save_fig("FIG001")
print(f"Had issues with state encodings:{psFig.abbrevIssueList}")


# ## Now select  States  according to multiple criteria
# ### Start with most populated states

# In[ ]:


tble = psFig.getPopStateTble(dtg)


# In[ ]:


mostPopulated = tble.sort_values(by=["pop"], ascending=False,).iloc[:15,0].values


# In[ ]:


class perStateSelected(perStateFigure):
    def __init__(self, dateStart, select):
        perStateFigure.__init__(self, dateStart)
        self.selected = select
        
    def skipIfCond(self, count, state):
        return state not in self.selected
    
    def breakIfCond(self, count, state):
        return False


# In[ ]:


psFig2 =  perStateSelected(dateStart,mostPopulated)
psFig2.initPainter(subnodeSpec=15, maxCol=3)
psFig2.mkImage(dtg,plotCols)
ImgMgr.save_fig("FIG002")
print(f"Had issues with state encodings:{psFig2.abbrevIssueList}")


# In[ ]:


dtgMax = dtg.max().loc[:,["fips","death","recovered","hospitalized"]]

dtgMerged = PAN.merge(dtgMax.reset_index(), demogr, left_on="fips", right_on="STATE")
dtgMerged["deathPM"]= dtgMerged.loc[:,"death"]/dtgMerged.loc[:,"POPESTIMATE2019"]*1.0e6

mostDeadly = dtgMerged.sort_values(by=["deathPM"], ascending=False,).iloc[:15,0].values


# In[ ]:


psFig3 =  perStateSelected(dateStart,mostDeadly)
psFig3.initPainter(subnodeSpec=15, maxCol=3)
psFig3.mkImage(dtg,plotCols)
ImgMgr.save_fig("FIG003")
print(f"Had issues with state encodings:{psFig3.abbrevIssueList}")

