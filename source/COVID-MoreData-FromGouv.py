#!/usr/bin/env python
# coding: utf-8

# #  Simple tool to analyze data from www.data.gouv.fr
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


checkSetup(chap="Chap01")
ImgMgr = ImageMgr(chapdir="Chap01")


# # Load Data

# ## Functions

# ## Load CSV and XLSX data from remote 
# The `dataFileVMgr` will manage a cache of data files in `../data`, the data will be downloaded
# from www.data.gouv.fr using a request for datasets with badge '`covid-19`' if a more recent
# version is present on the remote site. The meta information is stored/cached  in `../data/.data`
# as the pickle of a json.
# 
# We check what is in the cache/data directory; for each file, we identify the latest version, 
# and list this below to make sure. The file name will usually contain a time stamp; this has to do with 
# the version management/identification technique used when downloading from www.data.gouv.fr.
# 
# For the files used in this notebook, the latest version is used/loaded irrespective of the
# timestamp used in the notebook.

# In[ ]:


dataFileVMgr = manageAndCacheDataFilesFRDG("../data",  maxDirSz= 80*(2**10)**2)
dataFileVMgr.getRemoteInfo()
dataFileVMgr.updatePrepare()
dataFileVMgr.cacheUpdate()


# In[ ]:


dataFileVMgr.showMetaData()


# In[ ]:


print("Most recent versions of files in data directory:")
for f in dataFileVMgr.listMostRecent() :
    print(f"\t{f}")


# In[ ]:


last = lambda x: dataFileVMgr.getRecentVersion(x,default=True)


# This ensures we load the most recent version, so that it is not required to update the list 
# below. The timestamps shown in the following sequence will be update by the call to `getRecentVersion`.

# In[ ]:


dailyDepCsv    = last("sursaud-covid19-quotidien-2020-04-11-19h00-departement.csv")
dailyRegionCsv = last("sursaud-covid19-quotidien-2020-04-11-19h00-region.csv")
dailyFranceCsv = last("sursaud-covid19-quotidien-2020-04-12-19h00-france.csv")
dailyXlsx      = last("sursaud-covid19-quotidien-2020-04-12-19h00.xlsx")
weeklyCsv      = last("sursaud-covid19-hebdomadaire-2020-04-08-19h00.csv")

hospAgeCsv     = last("donnees-hospitalieres-classe-age-covid19-2020-04-11-19h00.csv")
hospNouveauCsv = last("donnees-hospitalieres-nouveaux-covid19-2020-04-11-19h00.csv")
hospCsv        = last("donnees-hospitalieres-covid19-2020-04-11-19h00.csv")
hospEtablCsv   = last("donnees-hospitalieres-etablissements-covid19-2020-04-12-19h00.csv")
weeklyLabCsv   = last("donnees-tests-covid19-labo-hebdomadaire-2020-04-16-10h47.csv")
dailyLabCsv    = last("donnees-tests-covid19-labo-quotidien-2020-04-17-19h00.csv")


S1 = set (dataFileVMgr.listMostRecent())
S2 =set((dailyDepCsv,dailyRegionCsv,dailyFranceCsv, dailyXlsx, weeklyCsv, 
         hospAgeCsv, hospNouveauCsv, hospCsv,  hospEtablCsv, weeklyLabCsv, dailyLabCsv  ))
missing = S1. difference(S2)
if len(missing) > 0:
    print (f"Missing comparing with most recent files in ../data:")
for f in missing:
    print(f"\t{f}")
                
metaHebdoCsv = "../data/metadonnee-urgenceshos-sosmedecins-covid19-hebdo.csv" 
metaQuotRegCsv = "../data/metadonnee-urgenceshos-sosmedecin-covid19-quot-reg.csv"
metaQuotFraCsv = "../data/metadonnee-urgenceshos-sosmedecin-covid19-quot-fra.csv" 
metaQuotDepCsv = "../data/metadonnee-urgenceshos-sosmedecins-covid19-quot-dep.csv"
metaQuotCsv = "../data/metadonnee-urgenceshos-sosmedecin-covid19-quot.csv"
        
metaHospservices = "../data/metadonnees-services-hospitaliers-covid19.csv"
metaHospAge      = "../data/metadonnees-donnees-hospitalieres-covid19-classes-age.csv"
metaHospIncid    = "../data/metadonnees-hospit-incid.csv"
metaHospNouveau  = "../data/metadonnees-donnees-hospitalieres-covid19-nouveaux.csv"
metaHosp         = "../data/metadonnees-donnees-hospitalieres-covid19.csv"
metaHospEtabl    = "../data/donnees-hospitalieres-etablissements-covid19-2020-04-11-19h00.csv"

metaAideEntr     = "../data/metadonnees-aides-aux-entreprises.csv"
metaNivExcDC     = "../data/metadonnees-niveaux-exces-mortalite-covid19.csv"
metaDepist       = "../data/metadonnees-tests-depistage-covid19.csv"

metaSexeCsv = "../data/metadonnees-sexe.csv"
metaRegionsCsv="../data/regions-france.csv"
metaTranchesAgeCsv="../data/code-tranches-dage.csv"


# In[ ]:


fSolDep_csv = "../data/fonds-solidarite-volet-1-departemental.csv"
fSolDep_xls= "../data/fonds-solidarite-volet-1-departemental.xlsx"
fSolRegNaf_csv= "../data/fonds-solidarite-volet-1-regional-naf.csv"
fSolRegNaf_xls= "../data/fonds-solidarite-volet-1-regional-naf.xls"
indicExcesDCStand_csv= "../data/indicateur-niveaux-exces-mortalite-standardise.csv"
indicExcesDCDep_csv= "../data/niveaux-exces-mortalite-covid19-dep.csv"
indicExcesDCReg_csv= "../data/niveaux-exces-mortalite-covid19-reg.csv"
incoherent_hebdo_xls= "../data/sursaud-covid19-hebdomadaire-incoherence-01042020.xlsx"
incoherent_quot_xls= "../data/sursaud-covid19-quotidien-incoherence-01042020.xlsx"


# In[ ]:


ad  = lambda x: "../data/"+x
S1 = set (map(ad, dataFileVMgr.listMostRecent(nonTS=True)))
S2 =set((metaHebdoCsv, metaQuotRegCsv,  metaQuotFraCsv, metaQuotCsv, metaQuotDepCsv,
         metaHospservices, metaHospAge, metaHospIncid, metaHosp,  metaHospEtabl, metaRegionsCsv, 
         metaTranchesAgeCsv, metaAideEntr,  metaNivExcDC,  metaDepist, metaHospNouveau,
         fSolDep_csv, fSolDep_xls, fSolRegNaf_csv, fSolRegNaf_xls,
         indicExcesDCStand_csv, indicExcesDCDep_csv, indicExcesDCReg_csv,  
         incoherent_hebdo_xls, incoherent_quot_xls))
missing = S1. difference(S2)
if len(missing) > 0:
    print (f"Missing comparing with non timestamped files in ../data:")
for f in missing:
    print(f"\t{f}")


# Now load the stuff
# 

# In[ ]:


ad  = lambda x: "../data/"+x

data_fSolDep= read_xlsxPandas(fSolDep_xls)
data_fSolRegNaf= read_xlsxPandas(fSolRegNaf_xls)
data_indicExcesDCStand= read_csvPandas(indicExcesDCStand_csv,error_bad_lines=False,sep=";")
data_indicExcesDCDep= read_csvPandas(indicExcesDCDep_csv,error_bad_lines=False,sep=";")
data_indicExcesDCReg= read_csvPandas(indicExcesDCReg_csv,error_bad_lines=False,sep=";")
data_incoherent_hebdo= read_xlsxPandas(incoherent_hebdo_xls)
data_incoherent_quot= read_xlsxPandas(incoherent_quot_xls)

meta_Hebdo       = read_csvPandas(metaHebdoCsv,     clearNaN=True, error_bad_lines=False,sep=";", header=2)
meta_QuotReg     = read_csvPandas(metaQuotRegCsv, clearNaN=True, error_bad_lines=False,sep=";", header=1)
meta_QuotFra     = read_csvPandas(metaQuotFraCsv, clearNaN=True, error_bad_lines=False,sep=";", header=1)
meta_QuotDepCsv   = read_csvPandas(metaQuotDepCsv, clearNaN=True, error_bad_lines=False,sep=";", header=1)
meta_Quot        = read_csvPandas(metaQuotCsv, clearNaN=True, error_bad_lines=False,sep=";", header=1)
meta_HospServices = read_csvPandas(metaHospservices, clearNaN=True, error_bad_lines=False,sep=";")
meta_HospAge      = read_csvPandas(metaHospAge, clearNaN=True, error_bad_lines=False,sep=";")
meta_HospIncid    = read_csvPandas(metaHospIncid, clearNaN=True, error_bad_lines=False,sep=";")
meta_Hosp         = read_csvPandas(metaHosp, clearNaN=True, error_bad_lines=False,sep=";")
meta_HospNouveau  = read_csvPandas(metaHospNouveau, clearNaN=True, error_bad_lines=False,sep=";")

meta_AideEntr    = read_csvPandas(metaAideEntr, clearNaN=True, error_bad_lines=False,sep=",")  
meta_NivExcDC    = read_csvPandas(metaNivExcDC, clearNaN=True, error_bad_lines=False,sep=";")
meta_Depist      = read_csvPandas(metaDepist, clearNaN=True, error_bad_lines=False,sep=";")

meta_Sexe = read_csvPandas(metaSexeCsv, clearNaN=True, error_bad_lines=False,sep=";",header=0)
meta_Regions = read_csvPandas(metaRegionsCsv, clearNaN=True, error_bad_lines=False,sep=",")
meta_Ages    =  read_csvPandas(metaTranchesAgeCsv, clearNaN=True, error_bad_lines=False,sep=";")


# ## Figure out data characteristics

# In[ ]:


def showBasics(data,dataName):
    print(f"{dataName:24}\thas shape {data.shape}")

dataListDescr = ((data_fSolDep, "data_fSolDep"),
                 (data_fSolRegNaf, "data_fSolRegNaf"),
                 (data_indicExcesDCStand, "data_indicExcesDCStand"),
                 (data_indicExcesDCDep, "data_indicExcesDCDep"),
                 (data_indicExcesDCReg, "data_indicExcesDCReg"),
                 (data_incoherent_hebdo, "data_incoherent_hebdo"),
                 (data_incoherent_quot, "data_incoherent_quot"),
                 (meta_AideEntr,  "meta_AideEntr"), 
                 (meta_NivExcDC, "meta_NivExcDC"),
                 (meta_Depist,     "meta_Depist"),    
                  (meta_Hebdo,"meta_Hebdo"),
                  (meta_QuotReg,"meta_QuotReg"),
                  (meta_QuotFra,"meta_QuotFra"),
                  (meta_Quot,"meta_Quot"),
                  (meta_QuotDepCsv,"meta_QuotDepCsv"),
                  (meta_HospServices,"meta_HospServices"),
                  (meta_HospAge,"meta_HospAge"),
                  (meta_HospIncid,"meta_HospIncid"),
                  (meta_HospNouveau, "meta_HospNouveau"), 
                  (meta_Hosp,"meta_Hosp"),
                  (meta_Sexe,"meta_Sexe"),
                  (meta_Regions,'meta_Regions'),
                  (meta_Ages,'meta_Ages'))
    
for (dat,name) in dataListDescr:
    showBasics(dat,name)


# ### Help with meta data
# Of course I encountered some surprises, see `checkRepresentedRegions` issue with unknown codes which
# did occur in some files!

# In[ ]:


def checkRepresentedRegions(df,col='reg',**kwOpts):
    "list regions represented in a dataframe, if kwd print=True, will print list of code->string"
    regs = set(df[col])
    if "print" in kwOpts:
        for r in regs:
            extract = meta_Regions[ meta_Regions['code_region'] == r]
            # print (f"r={r}\t{extract}\t{extract.shape}")
            if extract.shape[0] == 0:
                lib = f"**Unknown:{r}**"
            else:
                lib=extract.iloc[0]. at ['nom_region']
            print(f"Region: code={r}\t->{lib}")
    return regs


# In[ ]:


for (dat,name) in dataListDescr:
    if name[0:5]=="meta_": continue
    print(f"\nDescription of data in '{name}'\n")
    display(dat.describe().transpose())


# In[ ]:


for (dat,name) in dataListDescr:
    if name[0:5]!="meta_": continue
    print(f"\nMeta data in '{name}'\n")
    display(dat)


# ## Get some demographics data from INSEE
# For the time being, these data are obtained / loaded from Insee web site using a manual process and are placed in a different directory, therefore a distinct FileManager is used, and loading this data is done here; for more details see the notebook `Pop-Data-FromGouv.ipy`
# 
# Using the base version which does not try to update the "../dataPop" directory

# In[ ]:


dataFileVMgrInsee = manageDataFileVersions("../dataPop") 
inseeDepXLS           ="../dataPop/InseeDep.xls"
inseeDep            = read_xlsxPandas(inseeDepXLS, sheet_name=1, header=7)
inseeReg            = read_xlsxPandas(inseeDepXLS, sheet_name=0, header=7)


# Now we can display our demographics data (summarized)

# In[ ]:


display(inseeDep.iloc[:,4:].sum())
display(inseeReg.iloc[:,4:].sum())


# # Look at the newer tables

# In[ ]:


display(data_fSolDep.info())
display(data_fSolDep.describe())
display(data_fSolDep[:10])


# In[ ]:


display(data_fSolRegNaf.info())
display(data_fSolRegNaf.describe())
display(data_fSolRegNaf[:10])


# In[ ]:


meta_NivExcDC


# In[ ]:


display( data_indicExcesDCStand.info())
display( data_indicExcesDCStand.describe())
display( data_indicExcesDCStand[:10])


# In[ ]:


display(data_indicExcesDCDep.info())
display(data_indicExcesDCDep.describe())
display(data_indicExcesDCDep[:10])


# In[ ]:


display(data_indicExcesDCReg.info())
display(data_indicExcesDCReg.describe())
display(data_indicExcesDCReg[:10])


# In[ ]:


display( data_incoherent_hebdo.info())
display( data_incoherent_hebdo.describe())
display( data_incoherent_hebdo[:10])


# In[ ]:


display( data_incoherent_quot.info()) 
display( data_incoherent_quot.describe()) 
display( data_incoherent_quot[:10]) 


# In[ ]:




