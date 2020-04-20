#!/usr/bin/env python
# coding: utf-8

# # Analyze population data from www.data.gouv.fr and/or INSEE
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
    from lib.DataGouvFr    import *
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


checkSetup(chap="Chap02")
ImgMgr = ImageMgr(chapdir="Chap02")


# # Load Data

# ## Functions

# ## Load CSV and XLSX data from remote 
# The `dataFileVMgr` will manage a cache of data files in `../dataPop`.
# 
# We check what is in the cache/data directory; for each file, we identify the latest version, 
# and list this below to make sure. The file name will usually contain a time stamp; this has to do with 
# the version management/identification technique used when downloading from www.data.gouv.fr or INSEE
# 
# For the files used in this notebook, the latest version is used/loaded irrespective of the
# timestamp used in the notebook.
# 
# Consulted:
#   - https://www.insee.fr/fr/information/2410988
#   - https://www.insee.fr/fr/information/2008354
#   - https://www.insee.fr/fr/statistiques/4265429?sommaire=4265511#consulter  
#   - https://www.insee.fr/fr/statistiques/4265429?sommaire=4265511#documentation
#   - https://api.insee.fr/catalogue/
#   - https://api.insee.fr/catalogue/site/themes/wso2/subthemes/insee/pages/help.jag
# 

# In[ ]:


dataFileVMgr = manageAndCacheFilesDFrame("../dataPop")


# In[ ]:


print("Most recent versions of files in data directory:")
for f in dataFileVMgr.listMostRecent() :
    print(f"\t{f}")


# In[ ]:


last = lambda x: dataFileVMgr.getRecentVersion(x,default=True)


# This ensures we load the most recent version, so that it is not required to update the list 
# below. The timestamps shown in the following sequence will be update by the call to `getRecentVersion`.

# In[ ]:


exportDSCsv    = last("export-dataset-20200314-064905.csv")
tagsCsv        = last("tags-2020-04-20-09-22.csv")


# In[ ]:


S1 = set (dataFileVMgr.listMostRecent())
S2 =set((exportDSCsv ,tagsCsv   ))
missing = S1. difference(S2)
if len(missing) > 0:
    print (f"Missing comparing with most recent files in ../data:")
for f in missing:
    print(f"\t{f}")


# In[ ]:


metaInseeDepXLS     = "../dataPop/InseeDep.xls"  
metaInseeRegionsXLS = "../dataPop/InseeRegions.xls"


# Now load the stuff

# In[ ]:


ad  = lambda x: "../dataPop/"+x
data_exportDS = read_csvPandas(ad(exportDSCsv), error_bad_lines=False,sep=";" )
data_tags     = read_csvPandas(ad(tagsCsv), error_bad_lines=False,sep=";")


# In[ ]:


meta_InseeDep       = read_xlsxPandas(metaInseeDepXLS, error_bad_lines=False,sep=",")
meta_InseeReg       = read_xlsxPandas(metaInseeRegionsXLS, error_bad_lines=False,sep=",")


# Show the shape of the loaded data:

# In[ ]:


def showBasics(data,dataName):
    print(f"{dataName:24}\thas shape {data.shape}")

dataListDescr = ( (data_exportDS, "data_exportDS"),
                (data_tags, "data_tags"),
                (meta_InseeDep,"meta_InseeDep"),
                (meta_InseeReg,"meta_InseeReg"))
    
for (dat,name) in dataListDescr:
    showBasics(dat,name)


# In[ ]:


for (dat,name) in dataListDescr:
    if name[0:5]=="meta_": continue
    print(f"\nDescription of data in '{name}'\n")
    display(dat.describe().transpose())
    


# ## Find rows corresponding to regexp

# In[ ]:


from IPython.core.display import display, HTML
display(HTML("<style>.container { width:100% !important; }</style>"))


# In[ ]:


data_exportDS.loc[:10].values


# In[ ]:


df1 = data_exportDS
df1[df1['title'].str.contains(r'statis')]


# In[ ]:


def selmask(col,rex,addedSpec="(?i)",df=data_exportDS):
    msk = df[col].str.contains(rex+addedSpec)
    try:
       ret = df[msk]
    except Exception as err:
        # print(f"got into exception  {err}, type(msk) ={type(msk)}")
        # display(msk)
        msk[msk.isna()]=False
        ret = df[msk]
    return ret

def rowMatch(col, rex,addedSpec="(?i)"):
    sm=selmask(col,rex,addedSpec= addedSpec)
    msk=sm[sm==True]
    ret  = data_exportDS.iloc[msk.index]
    return ret
def showMatch(col,rex, maxr=400):
    s = rowMatch(col, rex)
    print(s.shape)
    display(s[:maxr])

def prMatch(col,rex, l=150):
    q = rowMatch(col,rex)
    print(q.shape)
    for v in q.loc[:,col]:
        print(v[:l])
    


# In[ ]:



showMatch('description','stat.*population.*')
prMatch('description','stat.*population.*')


# In[ ]:


showMatch('title','france')


# In[ ]:


showMatch('title','stat.*population.*')  


# In[ ]:


showMatch('slug','stat.*population.*')  


# In[ ]:


showMatch('description','population.*')


# pandas.DataFrame.filter: filter column labels
#   df1[df1['col'].str.contains(r'foo(?!$)')]
