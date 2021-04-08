#!/usr/bin/env python
# coding: utf-8

# #  Simple tool to analyze data from https://data.europa.eu/
# 
# The EU Open Data Portal (EU ODP) aims to encourage the use of EU datasets for building third-party applications.
# 
# **Notes:** 
# 1. This is a Jupyter notebook which is also available as its executable export as a Python 3 script (therefore with automatically generated comments).
# 2. This version adapts to a significant change in format occurring early 2021: data was kept daily until 14 Dec 2020 and weekly thereafter. 
# 3. The update corresponding to the change in data format is expected around April 15th, 2021 ...*  since I became aware of this change rather late*.

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
    from lib.pandaUtils    import *
    from libApp.appEU      import *

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


dataFileVMgr = manageAndCacheDataFilesRdfEU( "../dataEURdf", maxDirSz= 180*(2**10)**2)
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


covidDataEUCsv = last("covid-19-coronavirus-data-weekly-from-17-december-2020.csv")
data_covidDataEU  = read_csvPandas(covidDataEUCsv , error_bad_lines=False,sep="," )


# Explanations and description about this file is found at https://data.europa.eu/euodp/en/data/dataset/covid-19-coronavirus-data-weekly-from-17-december-2020:
# 
# https://www.ecdc.europa.eu/en/publications-data/data-national-14-day-notification-rate-covid-19:
# Data on 14-day notification rate of new COVID-19 cases and deaths
# The downloadable data file contains information on the 14-day notification rate of newly reported COVID-19 cases per 100 000 population and the 14-day notification rate of reported deaths per million population by week and country. Each row contains the corresponding data for a certain day and per country. The file is updated weekly. You may use the data in line with ECDC’s copyright policy.
# https://www.ecdc.europa.eu/sites/default/files/documents/2021-01-13_Variable_Dictionary_and_Disclaimer_national_weekly_data.pdf
# rate_14_day 14-day notification rate of reported COVID-19 cases per 100
# 000 population OR 14-day notification rate of reported
# deaths per 1 000 000 population
# 
# 
# 
# After the transformation to weekly data, check that numbers are really weekly, dates appear in 'DateRep' and also in 'year_week' in distinct formats. Checked weekly results with "StopCovid" application at https://www.gouvernement.fr/info-coronavirus/tousanticovid (still factor 2 discrepancy ?) .

# In[ ]:


msk= (data_covidDataEU.loc[:,'country'] == 'France') & (data_covidDataEU.loc[:,'indicator'] == 'cases')
data_covidDataEU[msk].iloc[-10:].describe()


# In[ ]:


data_covidDataEU[msk].iloc[-10:]


# In[ ]:


msk= (data_covidDataEU.loc[:,'country'] == 'France') & (data_covidDataEU.loc[:,'indicator'] == 'deaths')
data_covidDataEU[msk].iloc[:].describe()


# In[ ]:


data_covidDataEU.columns


# This seems necessary, since there were NaNs in the "geoId" column

# In[ ]:


for coln in ( "country_code", "country"):
    si = sortedColIds(data_covidDataEU, coln)
    print(f"{coln:30}-> {len(si)} elts")


# **New with version of data input** (2021, found this late in April):
# Now we have to make do with "year_week" information in the form "yyyy-ww", as opposed to format="%d/%m/%Y".  Acceptable format documented at https://docs.python.org/3/library/datetime.html#strftime-and-strptime-behavior.
# Appropriate format is "%Y-%W-%w" where "%w" is day of week information.
# 
# You need also define start day:
# ~~~
# a = pd.to_datetime('2017_01_0',format = '%Y_%W_%w')
# print (a)
# 2017-01-08 00:00:00
# ~~~

# ### Lets visualize data from this *new* dataFrame

# In[ ]:


data_covidDataEU["date"] = PAN.to_datetime(data_covidDataEU.loc[:,"year_week"]+"-1", format="%Y-%W-%w")
dateStart = data_covidDataEU["date"].min()
dateEnd   = data_covidDataEU["date"].max() 
dateSpan  = dateEnd - dateStart 
print(f"Our statistics span {dateSpan.days+1} days, start: {dateStart} and end {dateEnd}")

data_covidDataEU["elapsedDays"] = (data_covidDataEU["date"] - dateStart).dt.days


# In[ ]:


def prepareDataPerCountry(df, continent=None, minPop=None, maxPop=None):
 dt = df.copy()
 dt = dt.set_index("continent")
 sel = True
 if continent is not None:
    sel = dt.index == continent
 if minPop is not None:
    sel = sel & (dt.loc[:,"population"]>= minPop)
 if maxPop is not None:
    sel = sel & (dt.loc[:,"population"]>= maxPop)
    
 dtx = dt[sel]   
 dtg = dtx.groupby("country")
 return dtg


# In[ ]:


dtg = prepareDataPerCountry(data_covidDataEU, continent="Asia")
myEUConverter = EUSiteData()
argDict = { "breakCond" : lambda count, country : count > 45,
            "countryDataAdapter" :myEUConverter }

myFig =  perCountryFigure(**argDict )

plotCols = ( "cases", "deaths")

myFig.initPainter( subnodeSpec=45, maxCol=3)
myFig.mkImage( dtg, plotCols)
 


# This is too detailed, let's specialize for the larger countries.

# In[ ]:


dtg = prepareDataPerCountry(data_covidDataEU, continent="Europe", minPop=2e7)
myEUConverter = EUSiteData()
argDict = { "breakCond" : lambda count, country : count > 12, 
            "countryDataAdapter":myEUConverter}
myFig =  perCountryFigure(**argDict )

plotCols = ( "cases", "deaths")

myFig.initPainter( subnodeSpec=12, maxCol=3)
myFig.mkImage( dtg, plotCols)
ImgMgr.save_fig("FIG001")


# In[ ]:


dtg = prepareDataPerCountry(data_covidDataEU, continent="Europe", minPop=2e7)
myEUConverter = EUSiteData()
argDict = { "breakCond" : lambda count, country : count > 12, 
            "countryDataAdapter":myEUConverter}
myFig =  perCountryFigure(**argDict )

plotCols = ( "deaths",)

myFig.initPainter( subnodeSpec=12, maxCol=3)
myFig.mkImage( dtg, plotCols)
ImgMgr.save_fig("FIG002") 


# In[ ]:


dtg = prepareDataPerCountry(data_covidDataEU, continent="Europe", minPop=2e7)
myEUConverter = EUSiteData()
argDict = { "breakCond" : lambda count, country : count > 12, 
            "countryDataAdapter":myEUConverter}
myFig =  perCountryFigure(**argDict )

plotCols = ( "cases", "deathscum")

myFig.initPainter( subnodeSpec=12, maxCol=3)
myFig.mkImage( dtg, plotCols)
ImgMgr.save_fig("FIG003")


# In[ ]:


dtg = prepareDataPerCountry(data_covidDataEU, continent="Europe", minPop=2e7)
myEUConverter = EUSiteData()
argDict = { "breakCond" : lambda count, country : count > 12, 
            "countryDataAdapter":myEUConverter}
myFig =  perCountryFigure(**argDict )

plotCols = ( "caserate", "deathscumrate")

myFig.initPainter( subnodeSpec=12, maxCol=3)
myFig.mkImage( dtg, plotCols,  subImgPaintAttrs = perCountryFigure.perMillionSIPA )
ImgMgr.save_fig("FIG004")


# In[ ]:


dtg = prepareDataPerCountry(data_covidDataEU, continent="Europe", minPop=2e7)
myEUConverter = EUSiteData()
argDict = { "breakCond" : lambda count, country : count > 12, 
            "countryDataAdapter":myEUConverter}
myFig =  perCountryFigure(**argDict )

plotCols = ( "deathrate",)

myFig.initPainter( subnodeSpec=12, maxCol=3)
myFig.mkImage( dtg, plotCols,  subImgPaintAttrs = perCountryFigure.perMillionSIPA )
ImgMgr.save_fig("FIG005")


# ### Look at the largest countries

# In[ ]:


dtg = prepareDataPerCountry(data_covidDataEU, minPop=15e7)
myEUConverter = EUSiteData()
argDict = { "breakCond" : lambda count, country : count > 15, 
            "countryDataAdapter":myEUConverter}
myFig =  perCountryFigure(**argDict )

plotCols = ( "cases", "deaths")

myFig.initPainter( subnodeSpec=15, maxCol=3)
myFig.mkImage( dtg, plotCols)
ImgMgr.save_fig("FIG021")


# In[ ]:


dtg = prepareDataPerCountry(data_covidDataEU, minPop=15e7)
myEUConverter = EUSiteData()
argDict = { "breakCond" : lambda count, country : count > 15, 
            "countryDataAdapter":myEUConverter}
myFig =  perCountryFigure(**argDict )

plotCols = ( "deaths",)

myFig.initPainter( subnodeSpec=15, maxCol=3)
myFig.mkImage( dtg, plotCols)
ImgMgr.save_fig("FIG022") 


# In[ ]:


dtg = prepareDataPerCountry(data_covidDataEU, minPop=15e7)
myEUConverter = EUSiteData()
argDict = { "breakCond" : lambda count, country : count > 15, 
            "countryDataAdapter":myEUConverter}
myFig =  perCountryFigure(**argDict )

plotCols = ( "cases", "deathscum")

myFig.initPainter( subnodeSpec=15, maxCol=3)
myFig.mkImage( dtg, plotCols)
ImgMgr.save_fig("FIG023")


# In[ ]:


dtg = prepareDataPerCountry(data_covidDataEU, minPop=15e7)
myEUConverter = EUSiteData()
argDict = { "breakCond" : lambda count, country : count > 15, 
            "countryDataAdapter":myEUConverter}
myFig =  perCountryFigure(**argDict )

plotCols = ( "caserate", "deathscumrate")

myFig.initPainter( subnodeSpec=15, maxCol=3)
myFig.mkImage( dtg, plotCols,  subImgPaintAttrs = perCountryFigure.perMillionSIPA )
ImgMgr.save_fig("FIG024")


# In[ ]:


dtg = prepareDataPerCountry(data_covidDataEU,  minPop=15e7)
myEUConverter = EUSiteData()
argDict = { "breakCond" : lambda count, country : count > 15, 
            "countryDataAdapter":myEUConverter}
myFig =  perCountryFigure(**argDict )

plotCols = ( "deathrate",)

myFig.initPainter( subnodeSpec=15, maxCol=3)
myFig.mkImage( dtg, plotCols,  subImgPaintAttrs = perCountryFigure.perMillionSIPA )
ImgMgr.save_fig("FIG025")


# In[ ]:





# In[ ]:





# In[ ]:




