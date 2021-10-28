#!/usr/bin/env python
# coding: utf-8

# #  Simple tool to analyze data from www.data.gouv.fr
# 
# **Note:** This is a Jupyter notebook which is also available as its executable export as a Python 3 script (therefore with automatically generated comments).

# # Libraries

# This is weird, apparently needed after transitionning to Ubuntu 21.04 Python 3.9.4, 
# there must be another dir lib competing ... so order has become important??

# In[ ]:


import sys,os
addPath= [os.path.abspath("../venv/lib/python3.9/site-packages/"),
          os.path.abspath("../source")]
addPath.extend(sys.path)
sys.path = addPath


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

# Some maths
from math import sqrt

import matplotlib        as MPL
import matplotlib.pyplot as PLT
# Add color
from matplotlib import cm
from matplotlib.colors import ListedColormap, LinearSegmentedColormap

import seaborn as SNS
SNS.set(font_scale=1)

import mpl_toolkits
import mpl_toolkits.mplot3d.axes3d
from mpl_toolkits.mplot3d.axes3d import get_test_data

# Python programming
from itertools import cycle
from time import time
import datetime

# Using pandas
import pandas as PAN
import xlrd


# In[ ]:


#from sklearn.svm import SVC
#from sklearn import linear_model
from sklearn import cluster


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
    import lib.basicDataCTE as DCTE
    from lib import figureHelpers as FHelp
    import libApp.appFrance as appFrance
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


checkSetup(chap="Vac02")
ImgMgr = ImageMgr(chapdir="Vac02")


# # Load Data

# ## Functions

# ## Load CSV and XLSX data from remote 
# The `dataFileVMgr` will manage a cache of data files in `../dataVaccin`, the data will be downloaded
# from www.data.gouv.fr using a request specified with tags and filtering file names and urls. The meta information is stored/cached  in `../dataVaccin/.data`
# as the pickle of a json.
# 
# We check what is in the cache/data directory; for each file, we identify the latest version, 
# and list this below to make sure. The file name will usually contain a time stamp; this has to do with 
# the version management/identification technique used when downloading from www.data.gouv.fr.
# 
# For the files used in this notebook, the latest version is used/loaded irrespective of the
# timestamp used in the notebook.

# In[ ]:


specOpts={ 'CacheValidity': 12*60*60, # normal caching period (seconds)
            'cacheFname': '.cache.vaccin.json',
            "dumpMetaFile" : "vaccin.meta.dump",
            "dumpMetaInfoFile" : "vaccin.metainfo.dump",
            'ApiInq'       : 'datasets',
            'InqParmsDir'  : {"tag":"covid"},
         }
rex = re.compile('.*vacsi-(v|tot)-(fra|reg|dep).*')
def uselFn(urqt):
    return rex.match(urqt.fname) or rex.match(urqt.url)


# Fichiers avec le nombre de personnes ayant reçu au moins une dose ou complètement 
# vaccinées, arrêté à la dernière date disponible :
#   - vacsi-tot-fra-YYYY-MM-DD-HHhmm.csv (échelle nationale)
#   - vacsi-tot-reg-YYYY-MM-DD-HHhmm.csv (échelle régionale)
#   - vacsi-tot-dep-YYYY-MM-DD-HHhmm.csv (échelle départementale)
# 
# 
# Fichiers avec le nombre quotidien de personnes ayant reçu au moins une dose, 
# par vaccin, et par date d’injection :
#   - vacsi-v-fra-YYYY-MM-DD-HHhmm.csv (échelle nationale)
#   - vacsi-v-reg-YYYY-MM-DD-HHhmm.csv (échelle régionale)
#   - vacsi-v-dep-YYYY-MM-DD-HHhmm.csv (échelle départementale)
# 
# Les vaccins sont codifiés de la façon suivante : 
# - 0 : Tous vaccins\n'
# - 1 : COMIRNATY Pfizer/BioNTech
# - 2 : Moderna
# - 3 : AstraZeneka
# - 4 : Janssen

# In[ ]:


dataFileVMgr = manageAndCacheDataFilesFRAPI("../dataVaccin", maxDirSz= 24*(2**10)**2,
                                            **specOpts)
dataFileVMgr.getRemoteInfo()
dataFileVMgr.updatePrepare()
dataFileVMgr.updateSelect(displayCount=40 ,  URqtSelector = uselFn)

dataFileVMgr.printUpdtList('fname') 
dataFileVMgr.printUpdtList('url')

dataFileVMgr.cacheUpdate()


# In[ ]:


last = lambda x: dataFileVMgr.getRecentVersion(x,default=True)


# In[ ]:


print("Most recent versions of files in data directory:")
for f in dataFileVMgr.listMostRecent() :
    print(f"\t{f}")


# This ensures we load the most recent version, so that it is not required to update the list 
# below. The timestamps shown in the following sequence will be update by the call to `getRecentVersion`.

# In[ ]:


dailyVacDep = last("vacsi-v-dep-2021-08-20-19h09.csv")
dailyVacFr  = last("vacsi-v-fra-2021-08-20-19h09.csv")
dailyVacReg = last("vacsi-v-reg-2021-08-20-19h09.csv")


# In[ ]:


S1 = set (dataFileVMgr.listMostRecent())
S2 =set((dailyVacFr,dailyVacDep, dailyVacReg ))
missing = S1. difference(S2)
if len(missing) > 0:
    print (f"Not exploited comparing with most recent files in ../dataVaccin:")
for f in missing:
    print(f"\t{f}")
    
metaSexeCsv = "../data/metadonnees-sexe.csv"
metaRegionsCsv="../data/regions-france.csv"
metaTranchesAgeCsv="../data/code-tranches-dage.csv"


# In[ ]:


ad  = lambda x: "../dataVaccin/"+x
S1 = set (map(ad, dataFileVMgr.listMostRecent(nonTS=True)))
S2 =set(( metaRegionsCsv, metaTranchesAgeCsv, metaSexeCsv ))
missing = S1. difference(S2)
if len(missing) > 0:
    print (f"Missing comparing with non timestamped files in ../data:")
    print ("These may eventually be exploited in other notebooks (e.g. COVID-MoreData-FromGouv)")
    for f in missing:
        print(f"\t{f}")


# Now load the stuff
# 

# In[ ]:


ad  = lambda x: "../data/"+x
adv  = lambda x: "../dataVaccin/"+x
data_dailyRegion = read_csvPandas(adv(dailyVacReg), error_bad_lines=False,sep=";" )
data_dailyDep    = read_csvPandas(adv(dailyVacDep), error_bad_lines=False,sep=";")
data_dailyFrance = read_csvPandas(adv(dailyVacFr), error_bad_lines=False,sep=";")

meta_Sexe    = read_csvPandas(metaSexeCsv, clearNaN=True, error_bad_lines=False,sep=";",header=0)
meta_Regions = read_csvPandas(metaRegionsCsv, clearNaN=True, error_bad_lines=False,sep=",")
meta_Ages    = read_csvPandas(metaTranchesAgeCsv, clearNaN=True, error_bad_lines=False,sep=";")


# ## Figure out data characteristics

# In[ ]:


def showBasics(data,dataName):
    print(f"{dataName:24}\thas shape {data.shape}")

dataListDescr = ((data_dailyRegion, "data_dailyRegion"), 
                  (data_dailyDep,"data_dailyDep"), 
                  (data_dailyFrance, "data_dailyFrance"),
                  (meta_Sexe,"meta_Sexe"),
                  (meta_Regions,'meta_Regions'),
                  (meta_Ages,'meta_Ages'))
    
for (dat,name) in dataListDescr:
    showBasics(dat,name)


# ### Focus on the recent period
# 
# In some displays, we may want to focus on the recent data, then the number of days is parametrized here.

# In[ ]:


nbLastDays=50


# ## Get some demographics data from INSEE
# For the time being, these data are obtained / loaded from Insee web site using a manual process and are placed in a different directory, therefore a distinct FileManager is used, and loading this data is done here; for more details see the notebook `Pop-Data-FromGouv.ipy`
# 
# Using the base version which **does not try to update** the "../dataPop" directory

# In[ ]:


dataFileVMgrInsee = manageDataFileVersions("../dataPop") 
inseeDepXLS           ="../dataPop/InseeDep.xls"
inseeDep            = read_xlsxPandas(inseeDepXLS, sheet_name=1, header=7)
inseeReg            = read_xlsxPandas(inseeDepXLS, sheet_name=0, header=7)


# Now we can display our demographics data (summarized)

# In[ ]:


display(inseeDep.iloc[:,4:].sum())
display(inseeReg.iloc[:,4:].sum())


# ## Let's do some graphics!

# ### Merge Vaccination and demographics data
# See the `Pop-Data-FromGouv.ipynb` notebook for more details on the demographics data obtained from
# INSEE (https://www.insee.fr/fr/accueil). 

# ## Whole France

# In[ ]:


vacFrf = data_dailyFrance.copy()
vac0Frf = vacFrf.loc[vacFrf.loc[:,'vaccin']==0,:].set_index("jour")


# Here, it would be a good idea to apply a low pass filter!!

# ## Split according to vaccine type
# see in a second step, not sure that I am really interested in vaccine type for now!

# In[ ]:


vaccNames= { 0 : 'All vaccines',
            1 : 'Pfizer/BioNTech',
            2 : 'Moderna',
            3 : 'Astra Zeneka',
            4 : 'Janssen'}


# In[ ]:


vac1Frf = vacFrf.set_index("jour")


# In[ ]:


vac1GrFrf=vac1Frf.groupby('vaccin')


# In[ ]:


subnodeSpec=(lambda i,j:{"nrows":i,"ncols":j})(*subPlotShape(len(vac1GrFrf),maxCol=2))


# ## Look at the distribution accross areas ('departements')
# 
# ### Basics

# Prepare the data for a database style join/merge, documented on https://pandas.pydata.org/pandas-docs/stable/user_guide/merging.html.
# First we need to establish "dep" as an index in our data: 

# In[ ]:


vacDepf = data_dailyDep.copy()
vacDepf.loc[:,"dep"] = vacDepf.loc[:,"dep"].apply(str) 
vacDepfV=vacDepf.set_index("vaccin")


# *At this date (26/9/21) the "dep" column contains a mix of integer and str encodings, which causes failure down the road (look a merge...); so we corrected this in second
# instruction above.*
# 
# Here we discover that for vaccine code 0 (all vaccines) the cumulative columns have not been filled!! As somebody said, *real data is often cause for 
# surprises*!! I correct this situation here, not *checking whether progessively summing daily contributions will give the same result*. 

# In[ ]:


for col in ('n_cum_dose1', 'n_cum_dose2'):
    vacDepfV.loc[0, col] = vacDepfV.loc[1, col].values
    for i in range(2,5):
        vacDepfV.loc[0, col] += vacDepfV.loc[i, col].values


# In[ ]:


vacDepf = vacDepfV.reset_index()


# Then we extract the demographic information and set index "dep" 

# In[ ]:


depStats = inseeDep.iloc[:,[2,3,7,8]].copy()
cols = depStats.columns.values
cols[0]="dep"
depStats.columns = cols
depStats.set_index("dep");


# Now we perform the merge, and group by date and 'départements': 

# In[ ]:


vacMerged = PAN.merge(vacDepf,depStats, on="dep" ) 
vacGrMerged=vacMerged.groupby(["dep","jour","vaccin"]).sum()


# In[ ]:


deps=depStats.iloc[:,0]
deps1=set(vacGrMerged.index.get_level_values(0))
sdiff = deps1-set(deps)
sdiffR = set(deps)-deps1

if len(sdiff) > 0:
    raise RuntimeError (f"Missing departements in depStats (pop stats):{sdiff}")

if len(sdiffR) > 0:
    raise RuntimeError(f"Non represented departements in vacGrMerged:{sorted(sdiffR)}")


# In[ ]:


colLabs = ("n_dose1", "n_dose2", "n_cum_dose1", "n_cum_dose2")
for lab in colLabs:
    vacGrMerged[lab+"_rate"] = vacGrMerged[lab]/vacGrMerged["Population totale"]*100


# In[ ]:


print(f"vacDepf.shape ={vacDepf.shape}")
print(f"depStats.shape={depStats.shape}")
print(f"vacMerged.shape={vacMerged.shape}")
print(f"vacGrMerged.shape={vacGrMerged.shape}")
print(f"data_dailyDep.shape={data_dailyDep.shape}")

print(f"vacMerged.columns:{vacMerged.columns}")
print(f"vacGrMerged.columns:{vacGrMerged.columns}")


# For now, look at daily statistics normalized by concerned population (unit= event per million people)

# Select `vaccin == 0` (all vaccine types), iterate on `dep` (if this is doable
# on a multi-index, note that `vacGrMerged` is a `pandas.core.frame.DataFrame`.)
# - https://stackoverflow.com/questions/53927460/select-rows-in-pandas-multiindex-dataframe is quite comprehensive on slicing multi-indices
# - we select `vaccin == 0` with `loc[slice(None),slice(None),0]` selector

# In[ ]:


vacAllPanda=vacGrMerged.loc[slice(None),slice(None),0]


# We take this opportunity to check that all departements are represented

# In[ ]:


deps=depStats.iloc[:,0]
deps1=set(vacAllPanda.index.get_level_values(0))
sdiff = deps1-set(deps)
if len(sdiff) > 0:
    raise RuntimeError (f"Missing departements in depStats (pop stats):{sdiff}")


# In[ ]:


vacGrMerged.loc[slice(None),slice(None),0].loc[:,('n_cum_dose1','n_cum_dose2') ].describe()


# We also make a dict to get information about a departement from its id as a string representing a number. There is an **issue** here since *code 976 (Mayotte) is missing,
# as well as code 975 (St Pierre et Miquelon)*. When this **blows up...** I will have to do something about it!!

# In[ ]:


depDict = {depStats.iloc[i,0]:i for i in range(depStats.shape[0])}


# This is how this works and this solves the mystery about 97X numbers!

# In[ ]:


depStats.iloc[list(depDict[f"{i}"] for i in range(971,975)) ,:]


# What corresponds to departement with number '976' (Mayotte), missing here, 
# remains to be seen... But at this point this is non blocking. Of course we used the trick of converting to a set
# to get the unique values used in the 'dep' multi-index level.

# And the graph can be readily generated:

# For vaccine coverage, we determine it on last day in table. 
# This implementation requires all departements to have entries for the last day!!
# 
# First we prepare by getting access to the vaccination rates:

# In[ ]:


lastDay=max(vacAllPanda.index.levels[1])
vaccAllLast=vacAllPanda.loc[(slice(None),lastDay),:]
vRates = vaccAllLast.loc[:, ('n_cum_dose1_rate','n_cum_dose2_rate')]


# ### Compare vaccination achievements accross departements

# <HTML><COLOR:'RED'></HTML>This figure need to be redone <HTML></COLOR></HTML>
#     as a point cloud, with no xlabels, improved xlabels,
# or as an X-Y cloud, possibly showing the label at each point (too cluttered?), also look at the graphs we want to make... (rates/population...)

# ### Mix vaccine and COVID Data on departemental level

# ##### Load and prepare COVID Data
# This has been copied from 'COVID-Data-FromGouv(-Later)', postfix 'D' is used to name
# objects, since they will be used with previously loaded data.

# In[ ]:


tagset1D = ({"tag":"covid"}, {"tag":"covid19"})
specOptsD={ 'cacheFname': '.cache.tag-covid.json',
           "dumpMetaFile" : "data-gouv-fr.meta.dump",
           "dumpMetaInfoFile" : "data-gouv-fr.metainfo.dump",
           'ApiInq'       : 'datasets',
           'ApiInqQuery'  : tagset1D,
           'InqParmsDir'  : {},
          }
rexD = re.compile('(.*sursaud|^donnees-hospitalieres).*')
def uselFnD(urqt):
                return rexD.match(urqt.fname) or rexD.match(urqt.url)


# In[ ]:


dataFileVMgrD = manageAndCacheDataFilesFRAPI("../data", maxDirSz= 170*(2**10)**2,
                                            **specOptsD)
dataFileVMgrD.getRemoteInfo()
dataFileVMgrD.updatePrepare()
dataFileVMgrD.updateSelect(displayCount=40 ,  URqtSelector = uselFnD)
dataFileVMgrD.cacheUpdate()


# In[ ]:


lastD = lambda x: dataFileVMgrD.getRecentVersion(x,default=True)


# In[ ]:


print("Most recent versions of files in data directory:")
for f in dataFileVMgrD.listMostRecent() :
    print(f"\t{f}")


# In[ ]:


dailyDepCsv    = lastD("sursaud-corona-quot-dep-2021-04-08-21h20.csv")
hospNouveauCsv = lastD("donnees-hospitalieres-nouveaux-covid19-2020-04-11-19h00.csv")
adD  = lambda x: "../data/"+x
data_dailyDep    = read_csvPandas(adD(dailyDepCsv), error_bad_lines=False,sep=";")
data_hospNouveau = read_csvPandas(adD(hospNouveauCsv), error_bad_lines=False,sep=";")


# We use `nbDaysFilter` for averaging daily data when such filtering is needed.
# There is a parameter `nbLastDays` above for representing recent data; for avoiding issues with week ends, make this a multiple of 7.

# In[ ]:


nbDaysFilter=7


# In[ ]:


hndDf = data_hospNouveau.set_index( ["dep","jour"]).copy()

print(f"hnDf:\n\tcolumn names:{hndDf.columns.values}"
      +f"\n\tmulti-index names:{hndDf.index.names}")


# Check that in this table, all departements use same set of dates, and store it in `hndDateList`:

# In[ ]:


hndDfG=hndDf.groupby(['dep'])
hndDateList=None
for dep in hndDfG:
    gg=hndDfG.get_group(dep[0]).copy()
    if hndDateList is None:
        hndDateList=gg.reset_index('jour')['jour'].values
    else:
        assert  (hndDateList ==  gg.reset_index('jour')['jour'].values).all()


# Now, we run the same process for the `data_dailyDep` frame! 
# *But there is an issue here!*

# In[ ]:


dDf=data_dailyDep
dDfTypes=set( dDf.loc[:,'dep'].apply(type))
print(f"column 'dep' contains data with types {dDfTypes}")
for t in dDfTypes:
    cc = dDf.loc[:,'dep'].apply(lambda x: isinstance(x,t))
    print(f"Count of {t} :  {cc.sum()}")
set(dDf.loc[:,'dep'].values)
def cvFun(x):
    if isinstance(x,int):
        return f"{x:02d}"
    return x
depColAsStr=dDf.loc[:,'dep'].apply(cvFun)


# In[ ]:


for x in set(depColAsStr.values):
    if x not in depDict:
        print(f"There is a departement code not in depDict:{x}")


# We correct the table nevertheless, and hope for the best(?)

# In[ ]:


dDf.loc[:,'dep'] = depColAsStr


# In[ ]:


dDf=data_dailyDep.set_index(["dep","sursaud_cl_age_corona",'date_de_passage'] ).copy()

print(f"dDf:\n\tcolumn names:{dDf.columns.values}"
      +f"\n\tmulti-index names:{dDf.index.names}")


# This is a check that all departement's data are relative the same dates! Seems
# weird, but this has permitted to diagnose that there was a mix of integer and string
# data in the "dep" column (string needed because of Corsica 2A and 2B codes!!!)

# In[ ]:


dDfG=dDf.groupby(['dep', "sursaud_cl_age_corona"])
dDateList=None
for dep in dDfG:
    gg=dDfG.get_group(dep[0]).copy().reset_index('date_de_passage')['date_de_passage'].values
    if dDateList is None:
        dDateList=gg
    else:
        if len(gg)!= len (dDateList):
            print(f"Different number of dates for dep={dep[0]}; was:{len(dDateList)}"+
                  f" This one: {len(gg)}")


# #### Extract last days values
# Last days values are averaged over a period of time, as parametrized
# by `nbDaysFilter`, and this is represented in `hndLDays`. 
# For now, we are using the data from 
# `donnees-hospitalieres-nouveaux-covid19.*` (`hndDf`); this is consistent with
# per departement graphs in `COVID-Data-FromGouv-Later`.

# In[ ]:


display(hndDf.describe())
display(dDf.describe())


# In[ ]:


hndDfG=hndDf.groupby('dep')
dataAsDict={}
for (dep,depTb) in hndDfG:
    #print(f"dep={dep} {depTb.shape}")
    ll = depTb.iloc[-nbDaysFilter:, :]
    llm = ll.mean()
    dataAsDict[dep] = llm
    #print(f"{llm}")
hndLDays=PAN.DataFrame.from_dict(dataAsDict, orient='index')


# #### Prepare and Merge data 
# 
# Here we want to merge with other data:
# - need population count in the various territories
# - need vaccination data
# 
# First, we embark on getting vaccination data averaged over the last `nbDaysFilter`
# days; the dates are listed in `lastDays`.
# 
# A quite comprehensive treatment of selection with multi-indices appears in
# https://stackoverflow.com/questions/53927460/select-rows-in-pandas-multiindex-dataframe . All considered, I decide to use selection with a binary mask built over the index:

# In[ ]:


v=vacDepf.set_index(["vaccin", "dep", "jour"]).loc[0, slice(None),slice(None)]
lastDays=v.loc["01"].index.values[-nbDaysFilter:]
print(f"list of lastDays: {lastDays}")
assert len(lastDays) == nbDaysFilter


# In[ ]:


vSelLast=v[v.index.get_level_values('jour').map(lambda x: x in lastDays)]
print(f"vSelLast has\tshape={vSelLast.shape},"
      +f"\n\t\tnb departement chunks:{vSelLast.shape[0] / nbDaysFilter}")


# For each département:
# - we compute averages over `nbDaysFilter` last days for the vaccine delivery, which needs low pass filtering to avoid day to day variation and systematic variation on week ends
# - use vaccine cumulative data from the last day, since it is already a summation.

# In[ ]:


vSelLastG=vSelLast.groupby('dep')
dataAsDict={}
for (dep,depTb) in vSelLastG:
    ll = depTb.iloc[-nbDaysFilter:, :]
    llm = ll.mean()
    for c in ("n_cum_dose1","n_cum_dose2"):
        llm[c] = depTb.iloc[-1:, :].loc[:,c]
    dataAsDict[dep] = llm
vacDepAvg=PAN.DataFrame.from_dict(dataAsDict, orient='index')


# In[ ]:


vacDepAvg


# Codes **missing** in `depDict` (it was loaded from Data originating at Insee??!!, **Check**)
# - 975 : St Pierre et Miquelon
# - 976 : Mayotte
# - 977 : St Barthelemy
# - 978 : St Martin

# Now, we embark on merging..
# - `vacDepAvg` : vaccination average over last days
# - `hndLDays`  : incidence average over last days
# - `depStats`  : population statistics (with some missing entries!!)
# 
# 

# In[ ]:


depStatIdx=depStats.copy().set_index('dep')
depStatIdx


# Now we need to use a 3 way merge of indexed data in `depStatIdx`, `hndLDays` and `vacDepAvg`

# In[ ]:


def substFirstColname(tble,name):
    l = [name]
    l.extend(tble.columns.values[1:])
    tble.columns=l


# In[ ]:


t1=depStatIdx.reset_index()
t2=hndLDays.reset_index()
t3=vacDepAvg.reset_index()
substFirstColname(t2,"dep")
substFirstColname(t3,"dep")


# In[ ]:


vacM1 = PAN.merge(t1, t2, on="dep" ) 
vacDepMerged=PAN.merge(vacM1, t3, on="dep" ) 
vacGrMerged=vacMerged.groupby(["dep","jour","vaccin"]).sum()


# Depending on the data we compute occurrences per million population or as percentage of population.

# In[ ]:


colLabs = ( 'incid_hosp', 'incid_rea', 'incid_dc', 'incid_rad',
            'n_dose1', 'n_dose2', 
           'n_cum_dose1', 'n_cum_dose2')
for lab in colLabs[:6]:
    vacDepMerged[lab+"_perM"] = vacDepMerged[lab]/vacDepMerged["Population totale"]*1.0e6
for lab in colLabs[6:]:
    vacDepMerged[lab+"_perC"] = vacDepMerged[lab]/vacDepMerged["Population totale"]*100    


# In[ ]:


print(vacDepMerged.describe().loc["mean",:].iloc[2:])


# In[ ]:


vd=vacDepMerged.describe().loc[['mean','std']]
for c in vd.columns[2:]:
    print(f"{c:20s} mean={vd.loc['mean',c]:7.2e}\tstd={vd.loc['std',c]:7.2e}")


# #### Analyse and make graphics

# In[ ]:


vacDepMerged


# Matplotlib parametrization:
# - Use more `matplotlib`related `kwargs`. 
# - We use a color which conveys information about the departement's population.
# - Adopt a common coloring scheme
# - Set size of scatterplot markers

# In[ ]:


colormap = cm.get_cmap('brg', 32)

vdm=vacDepMerged
popRel=vdm.loc[:,'Population totale'] / max(vdm.loc[:,'Population totale'])
colors=colormap(popRel)
size = 2+150*popRel.map(sqrt)
alpha=0.5


# May be it is clearer in 3D!

# In[ ]:


## Older version

vdm=vacDepMerged
fig, ax1 = PLT.subplots(figsize=(8,8))
ax = fig.add_subplot(1, 1, 1, projection='3d')

x=vdm.loc[:,"incid_dc_perM"]
y=vdm.loc[:,"n_cum_dose2_perC"]
z=popRel

ax.scatter(x, y, z, c = colors, 
              s = 2*size, marker="o")

ax.set_xlabel('Death per Million per Day')
ax.set_ylabel('Dose2 percentage')
ax.set_zlabel('Population relative max')
ImgMgr.save_fig("FIG315")


# ## Scikit used for classification
# 
# First we adapt the data by entering the relative population  size of the departement in column `PopRel`.

# In[ ]:


selcols=[vacDepMerged.columns[3]]
selcols.extend(vacDepMerged.columns[14:])
vdm=vacDepMerged.loc[:,selcols].copy()
vdm.loc[:,'PopRel'] = vdm.loc[:,'Population totale'] / max(vdm.loc[:,'Population totale'])


# This means that the area of the dots is (roughly) proportional to the population.

# In[ ]:


sizes = 16*(150*vdm.loc[:,'PopRel']).map(lambda x: max(0.1,sqrt(x)))

nbClusters=5
figAdaptKM = FHelp.FigAdapter_KMeans(fitData = vdm, nbClusters = nbClusters)
figSc3D = FHelp.FigFrom3DScatterPlot( adapter = figAdaptKM, data = vdm, figsize=(8,8),
                                    sizes = sizes)

            # this fits the data and prepares the figure
figSc3D( xcol="incid_dc_perM",
         ycol="n_cum_dose2_perC", 
         zcol='PopRel',
         xlabel="death per million",
         ylabel="cum vaccine dose 2 percent",
         zlabel="population relative max",
         title="Segmentation based on all data\ncolors=auto, area~population")

ImgMgr.save_fig("FIG316")


# ## Try to obtain improved classification
# Here, we try to improve classification, in particular by preprocessing, normalizing data and the like.
# After all we have all Scikit abilities at hand:
# - documented at https://scikit-learn.org/stable/modules/classes.html#module-sklearn.preprocessing
#   - https://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.StandardScaler.html#sklearn.preprocessing.StandardScaler
# - The user guide is available at https://scikit-learn.org/stable/modules/preprocessing.html#preprocessing-scaler
# 
# 
# Some information may be gleaned from 
# - https://stackoverflow.com/questions/20027645/does-kmeans-normalize-features-automatically-in-sklearn
#   - a practical example is shown at https://stackoverflow.com/questions/57507584/feature-scaling-for-kmeans-algorithm
# 
# 
# ### Use data standardisation

# In[ ]:


sizes = 16*(150*vdm.loc[:,'PopRel']).map(lambda x: max(0.01,sqrt(x)))

nbClusters=5
figAdaptKM = FHelp.FigAdapter_KMeans(fitData = vdm.iloc[:,1:], nbClusters = nbClusters, 
                                     scaler="standard")

colormap = CM.get_cmap('brg', 32)
# lambda is used to defer evaluation of the labels
lambdaColors = lambda x : colormap((1+ figAdaptKM.k_means.labels_)/nbClusters)
lambdaSize =  sizes

figSc3D = FHelp.FigFrom3DScatterPlot( adapter = figAdaptKM, data = vdm, 
                                      figsize=(8,8))

            # this fits the data and prepares the figure
figSc3D( xcol="incid_dc_perM",
         ycol="n_cum_dose2_perC", 
         zcol='PopRel',
         colors = lambdaColors,
         sizes =  lambdaSize,
         xlabel="death per million",
         ylabel="cum vaccine dose 2 percent",
         zlabel="population relative max",
         title="Segmentation based on all data")

ImgMgr.save_fig("FIG317")


# ### Do not fit based on population data

# In[ ]:


sizes = 16*(150*vdm.loc[:,'PopRel']).map(lambda x: max(0.01,sqrt(x)))

nbClusters=5
figAdaptKM = FHelp.FigAdapter_KMeans(fitData = vdm.iloc[:,1:-1], 
                                     nbClusters = nbClusters, 
                                     scaler="standard")

colormap = CM.get_cmap('brg', 32)
# lambda is used to defer evaluation of the labels
lambdaColors = lambda x : colormap((1+ figAdaptKM.k_means.labels_)/nbClusters)
lambdaSize =  sizes

figSc3D = FHelp.FigFrom3DScatterPlot( adapter = figAdaptKM, data = vdm, 
                                      figsize=(8,8))

            # this fits the data and prepares the figure
figSc3D( xcol="incid_dc_perM",
         ycol="n_cum_dose2_perC", 
         zcol='PopRel',
         colors = lambdaColors,
         sizes =  lambdaSize,
         xlabel="death per million",
         ylabel="cum vaccine dose 2 percent",
         zlabel="population relative max",
         title="Segmentation based on all data\nexcept population")

ImgMgr.save_fig("FIG318")


# In[ ]:


fitCols=list(range(1,4))
fitCols.extend(range(5,7))

sizes = 16*(150*vdm.loc[:,'PopRel']).map(lambda x: max(0.01,sqrt(x)))

nbClusters=5
figAdaptKM = FHelp.FigAdapter_KMeans(fitData = vdm.iloc[:,fitCols], 
                                     nbClusters = nbClusters, 
                                     scaler="standard")

colormap = CM.get_cmap('brg', 32)
# lambda is used to defer evaluation of the labels
lambdaColors = lambda x : colormap((1+ figAdaptKM.k_means.labels_)/nbClusters)
lambdaSize =  sizes

figSc3D = FHelp.FigFrom3DScatterPlot( adapter = figAdaptKM, data = vdm, 
                                      figsize=(8,8))

            # this fits the data and prepares the figure
figSc3D( xcol="incid_dc_perM",
         ycol="n_cum_dose2_perC", 
         zcol='incid_hosp_perM',
         colors = lambdaColors,
         sizes =  lambdaSize,
         xlabel="death per million",
         ylabel="cum vaccine dose 2 percent",
         zlabel="incid hosp perM",
         title="Segmentation based on incidence- + vaccine-")

ImgMgr.save_fig("FIG319")


# In[ ]:


vdm.iloc[:,fitCols]


# In[ ]:




