#!/usr/bin/env python
# coding: utf-8

# #  Simple tool to analyze data from https://data.europa.eu/
# 
# The EU Open Data Portal (EU ODP) aims to encourage the use of EU datasets for building third-party applications.
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
import numpy as NP


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
    from lib.DataMgrRdf        import *
    import lib.basicDataCTE as DCTE
except Exception as err:
    print("Could not find library 'lib' with contents 'DataGouvFr' ")
    if get_ipython() is None:
        print("Check the PYTHONPATH environment variable which should point to 'source' wich contains 'lib'")
    else:
        print("You are supposed to be running in JupySessions, and '../source/lib' should exist")
    raise err


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


checkSetup(chap="Chap03")
ImgMgr = ImageMgr(chapdir="Chap03")


# # Load Data

# ## Functions

# ## Load CSV and XLSX data from remote 
# The `dataFileVMgr` will manage a cache of data files in `../dataEURdf`, the data will be downloaded
# from  https://data.europa.eu using the SPARQL query endpoint. The meta information is stored/cached  in `../dataEURdf/.cache*`
# 
# We check what is in the cache/data directory; for each file, we identify the latest version, 
# and list this below to make sure. The file name will usually contain a time stamp.
# 
# <FONT COLOR="RED">TO BE CHECKED For the files used in this notebook, the latest version is used/loaded irrespective of the
# timestamp used in the notebook.</FONT>

# In[ ]:


dataFileVMgr = manageAndCacheDataFilesRdfEU( "../dataEURdf", maxDirSz= 80*(2**10)**2)
dataFileVMgr.getRemoteInfo()


# This can be long, the SPARQL processor used is not fast

# In[ ]:


dataFileVMgr.updatePrepare()
dataFileVMgr.cacheUpdate()


# ## Get some understanding of the available resource

# In[ ]:


nbLastDays = 30


# ## Dig into the data

# In[ ]:


print("Most recent versions of files in data directory:")
for f in dataFileVMgr.listMostRecent(nonTS=True) :
    print(f"\t{f}")


# In[ ]:


last = lambda x: dataFileVMgr.getRecentVersion(x,default=os.path.join(dataFileVMgr.dirpath,x))


# In[ ]:


dataFileVMgr.nonTSFiles


# In[ ]:


covidDataEUCsv = last("covid-19-coronavirus-data.csv")
data_covidDataEU  = read_csvPandas(covidDataEUCsv , error_bad_lines=False,sep="," )


# In[ ]:


data_covidDataEU.info()


# After the transformation to weekly data, check that numbers are really weekly, dates appear in 'DateRep' and also in 'year_week' in distinct formats. Checked weekly results with "StopCovid" application at https://www.gouvernement.fr/info-coronavirus/tousanticovid (still factor 2 discrepancy ?) .

# In[ ]:


msk= data_covidDataEU.loc[:,'countriesAndTerritories'] == 'France'
data_covidDataEU[msk].iloc[:3]


# In[ ]:


def sortedIds(df,col):
   t=df.loc[:,col].unique()
   return sorted([ x  for x in t if isinstance(x, str) ])


# In[ ]:


data_covidDataEU.columns


# This seems necessary, since there were NaNs in the "geoId" column

# In[ ]:


for coln in ("geoId" , "countryterritoryCode", "countriesAndTerritories"):
    si = sortedIds(data_covidDataEU, coln)
    print(f"{coln:30}-> {len(si)} elts")


# In[ ]:


data_covidDataEU["date"] = PAN.to_datetime(data_covidDataEU.loc[:,"dateRep"], format="%d/%m/%Y")


# In[ ]:


dateStart = data_covidDataEU["date"].min()
dateEnd   = data_covidDataEU["date"].max() 
dateSpan  = dateEnd - dateStart 
print(f"Our statistics span {dateSpan.days+1} days, start: {dateStart} and end {dateEnd}")

data_covidDataEU["elapsedDays"] = (data_covidDataEU["date"] - dateStart).dt.days


# In[ ]:


data_covidDataEU["elapsedDays"][:3] 


# In[ ]:


dt  = data_covidDataEU.copy()
dt = dt.set_index("continentExp")


# In[ ]:


dtx = dt[dt.index == "Europe"]
dtg = dtx.groupby("countriesAndTerritories")


# In[ ]:


for (country,dfExtract) in dtg:
    print(f"{country:30}\t-> data over {dfExtract.shape[0]*7} days")


# In[ ]:


for (country,dfExtract) in dtg :
       #print(f"{country:30}\t-> data over {dfExtract.shape[0]} days")
       PLT.plot( dfExtract.loc[:,["elapsedDays"]], dfExtract.loc[:,["cases_weekly"]]/7)
       PLT.yscale("log")
       #painter = figureTSFromFrame(dfExtract.loc[:,["cases","deaths"]],figsize=(12,8))
       #painter.doPlot()


# In[ ]:


dtx = dt[ (dt.index == "Europe") & (dt["popData2019"] > 10.0e6) ]
dtg = dtx.groupby("countriesAndTerritories")
subnodeSpec=(lambda i,j:{"nrows":i,"ncols":j})(*subPlotShape(len(dtg),maxCol=4))


# In[ ]:


painter = figureFromFrame(None, subplots=subnodeSpec, figsize=(15,15))
for (country,dfExtractOrig) in dtg :
    pop = dfExtractOrig["popData2019"][0]
    print(f"Country={country}, pop:{pop/1.0E6}M")
    dfExtract = dfExtractOrig.set_index("elapsedDays").copy()
    dfExtract.loc[:,"cumcases"] = dfExtract.loc[:,"cases_weekly"].sort_index().cumsum()/dfExtract.loc[:,"popData2019"]*1.0E6
    dfExtract.loc[:,"cumdeaths"] = dfExtract.loc[:,"deaths_weekly"].sort_index().cumsum()/dfExtract.loc[:,"popData2019"]*1.0E6
    dfExtract.loc[:,"cases"] = dfExtract.loc[:,"cases_weekly"]/dfExtract.loc[:,"popData2019"]*1.0E6/7
    dfExtract.loc[:,"deaths"] = dfExtract.loc[:,"deaths_weekly"]/dfExtract.loc[:,"popData2019"]*1.0E6/7
    painter.doPlot(df = dfExtract.loc[:,["cases","deaths","cumcases","cumdeaths"]])
    painter.setAttrs(label=f"Days since {dateStart}",
                 title=f"Data from EU Data Portal: {country}",
                 legend=True,
                 xlabel=f"Days since {dateStart}",
                 ylabel="Daily Events per million population"   )
        
    painter.advancePlotIndex()  
ImgMgr.save_fig("FIG007")  


# In[ ]:


painter = figureFromFrame(None, subplots=subnodeSpec, figsize=(15,15))
for (country,dfExtractOrig) in dtg :
    pop = dfExtractOrig["popData2019"][0]
    print(f"Country={country}, pop:{pop/1.0E6}M")
    dfExtract = dfExtractOrig.set_index("elapsedDays").copy()
    dfExtract.loc[:,"cumdeaths"] = dfExtract.loc[:,"deaths_weekly"].sort_index().cumsum()/dfExtract.loc[:,"popData2019"]*1.0E6
    dfExtract.loc[:,"cases"] = dfExtract.loc[:,"cases_weekly"]/dfExtract.loc[:,"popData2019"]*1.0E6/7
    dfExtract.loc[:,"deaths"] = dfExtract.loc[:,"deaths_weekly"]/dfExtract.loc[:,"popData2019"]*1.0E6/7
    painter.doPlot(df = dfExtract.loc[:,["cases","deaths","cumdeaths"]])
    painter.setAttrs(label=f"Days since {dateStart}",
                 title=f"Data from EU Data Portal: {country}",
                 legend=True,
                 xlabel=f"Days since {dateStart}",
                 ylabel="Daily Events per million population"   )
        
    painter.advancePlotIndex()  
ImgMgr.save_fig("FIG017")  


# In[ ]:


painter = figureFromFrame(None, subplots=subnodeSpec, figsize=(15,15))
for (country,dfExtractOrig) in dtg :
    pop = dfExtractOrig["popData2019"][0]
    print(f"Country={country}, pop:{pop/1.0E6}M")
    dfExtract = dfExtractOrig.set_index("elapsedDays").copy()
    dfExtract.loc[:,"deaths"] = dfExtract.loc[:,"deaths_weekly"]/dfExtract.loc[:,"popData2019"]*1.0E6/7
    painter.doPlot(df = dfExtract.loc[:,["deaths"]])
    painter.setAttrs(label=f"Days since {dateStart}",
                 title=f"Data from EU Data Portal: {country}",
                 legend=True,
                 xlabel=f"Days since {dateStart}",
                 ylabel="Daily Events per million population"   )
        
    painter.advancePlotIndex()  
ImgMgr.save_fig("FIG017B")  


# In[ ]:


painter = figureFromFrame(None,  subplots=subnodeSpec, figsize=(15,15))
for (country,dfExtractOrig) in dtg :
    pop = dfExtractOrig["popData2019"][0]
    print(f"Country={country}, pop:{pop/1.0E6}M")
    dfExtract = dfExtractOrig.set_index("elapsedDays").copy()
    dfExtract.loc[:,"cumcases"] = dfExtract.loc[:,"cases_weekly"].sort_index().cumsum()/dfExtract.loc[:,"popData2019"]*1.0E6
    dfExtract.loc[:,"cumdeaths"] = dfExtract.loc[:,"deaths_weekly"].sort_index().cumsum()/dfExtract.loc[:,"popData2019"]*1.0E6
    dfExtract.loc[:,"cases"] = dfExtract.loc[:,"cases_weekly"]/dfExtract.loc[:,"popData2019"]*1.0E6/7
    dfExtract.loc[:,"deaths"] = dfExtract.loc[:,"deaths_weekly"]/dfExtract.loc[:,"popData2019"]*1.0E6/7
    painter.doPlot( df = dfExtract.loc[:,["cases","deaths","cumcases","cumdeaths"]],
                      colOpts={"cases": {"yscale":'log'},
                            "deaths": {"yscale":'log'},
                            "cumcases": {"yscale":'log'},
                            "cumdeaths": {"yscale":'log'},})
    painter.setAttrs(label=f"Days since {dateStart}",
                 title=f"Data from EU Data Portal\nstats for {country}",
                 legend=True,
                 xlabel=f"Days since {dateStart}",
                 ylabel="Daily events per million population"   )
    painter.advancePlotIndex()
ImgMgr.save_fig("FIG008")        


# ### Look at the largest countries

# In[ ]:


dtx = dt[ dt["popData2019"] > 65.0e6 ]
dtg = dtx.groupby("countriesAndTerritories")
subnodeSpec=(lambda i,j:{"nrows":i,"ncols":j})(*subPlotShape(len(dtg),maxCol=4, colFirst=False))


# In[ ]:


painter = figureFromFrame(None, subplots=subnodeSpec, figsize=(15,20))
for (country,dfExtractOrig) in dtg :
    pop = dfExtractOrig["popData2019"][0]
    print(f"Country={country}, pop:{pop/1.0E6}M")
    dfExtract = dfExtractOrig.set_index("elapsedDays").copy()
    dfExtract.loc[:,"cumcases"] = dfExtract.loc[:,"cases_weekly"].sort_index().cumsum()/dfExtract.loc[:,"popData2019"]*1.0E6
    dfExtract.loc[:,"cumdeaths"] = dfExtract.loc[:,"deaths_weekly"].sort_index().cumsum()/dfExtract.loc[:,"popData2019"]*1.0E6
    dfExtract.loc[:,"cases"] = dfExtract.loc[:,"cases_weekly"]/dfExtract.loc[:,"popData2019"]*1.0E6/7
    dfExtract.loc[:,"deaths"] = dfExtract.loc[:,"deaths_weekly"]/dfExtract.loc[:,"popData2019"]*1.0E6/7
    painter.doPlot(df = dfExtract.loc[:,["cases","deaths","cumcases","cumdeaths"]])
    painter.setAttrs(label=f"Days since {dateStart}",
                 title=f"Data from EU Data Portal: {country}",
                 legend=True,
                 xlabel=f"Days since {dateStart}",
                 ylabel="Daily events per million population"   )
        
    painter.advancePlotIndex()  
ImgMgr.save_fig("FIG009")  


# In[ ]:


painter = figureFromFrame(None, subplots=subnodeSpec, figsize=(15,20))
for (country,dfExtractOrig) in dtg :
    pop = dfExtractOrig["popData2019"][0]
    print(f"Country={country}, pop:{pop/1.0E6}M")
    dfExtract = dfExtractOrig.set_index("elapsedDays").copy()
    dfExtract.loc[:,"cumdeaths"] = dfExtract.loc[:,"deaths_weekly"].sort_index().cumsum()/dfExtract.loc[:,"popData2019"]*1.0E6
    dfExtract.loc[:,"cases"] = dfExtract.loc[:,"cases_weekly"]/dfExtract.loc[:,"popData2019"]*1.0E6/7
    dfExtract.loc[:,"deaths"] = dfExtract.loc[:,"deaths_weekly"]/dfExtract.loc[:,"popData2019"]*1.0E6/7
    painter.doPlot(df = dfExtract.loc[:,["cases","deaths","cumdeaths"]])
    painter.setAttrs(label=f"Days since {dateStart}",
                 title=f"Data from EU Data Portal: {country}",
                 legend=True,
                 xlabel=f"Days since {dateStart}",
                 ylabel="Daily events per million population"   )
        
    painter.advancePlotIndex()  
ImgMgr.save_fig("FIG019")  


# In[ ]:


painter = figureFromFrame(None, subplots=subnodeSpec, figsize=(15,20))
for (country,dfExtractOrig) in dtg :
    pop = dfExtractOrig["popData2019"][0]
    print(f"Country={country}, pop:{pop/1.0E6}M")
    dfExtract = dfExtractOrig.set_index("elapsedDays").copy()    
    dfExtract.loc[:,"deaths"] = dfExtract.loc[:,"deaths_weekly"]/dfExtract.loc[:,"popData2019"]*1.0E6/7
    painter.doPlot(df = dfExtract.loc[:,["deaths"]])
    painter.setAttrs(label=f"Days since {dateStart}",
                 title=f"Data from EU Data Portal: {country}",
                 legend=True,
                 xlabel=f"Days since {dateStart}",
                 ylabel="Daily events per million population"   )
        
    painter.advancePlotIndex()  
ImgMgr.save_fig("FIG019B")  


# In[ ]:


painter = figureFromFrame(None,  subplots=subnodeSpec, figsize=(15,20))
for (country,dfExtractOrig) in dtg :
    pop = dfExtractOrig["popData2019"][0]
    print(f"Country={country}, pop:{pop/1.0E6}M")
    dfExtract = dfExtractOrig.set_index("elapsedDays").copy()
    dfExtract.loc[:,"cumcases"] = dfExtract.loc[:,"cases_weekly"].sort_index().cumsum()/dfExtract.loc[:,"popData2019"]*1.0E6
    dfExtract.loc[:,"cumdeaths"] = dfExtract.loc[:,"deaths_weekly"].sort_index().cumsum()/dfExtract.loc[:,"popData2019"]*1.0E6
    dfExtract.loc[:,"cases"] = dfExtract.loc[:,"cases_weekly"]/dfExtract.loc[:,"popData2019"]*1.0E6/7
    dfExtract.loc[:,"deaths"] = dfExtract.loc[:,"deaths_weekly"]/dfExtract.loc[:,"popData2019"]*1.0E6/7
    painter.doPlot( df = dfExtract.loc[:,["cases","deaths","cumcases","cumdeaths"]],
                      colOpts={"cases": {"yscale":'log'},
                            "deaths": {"yscale":'log'},
                            "cumcases": {"yscale":'log'},
                            "cumdeaths": {"yscale":'log'},})
    painter.setAttrs(label=f"Days since {dateStart}",
                 title=f"Data from EU Data Portal\nstats for {country}",
                 legend=True,
                 xlabel=f"Days since {dateStart}",
                 ylabel="Daily events per million population"   )
    painter.advancePlotIndex()
ImgMgr.save_fig("FIG010")        


# In[ ]:





# In[ ]:




