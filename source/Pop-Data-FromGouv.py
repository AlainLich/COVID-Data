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
    from lib.pandaUtils    import *
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
# Downloaded:
#   
#   - https://www.insee.fr/fr/statistiques/fichier/1893198/estim-pop-dep-sexe-gca-1975-2020.xls
#   - https://www.insee.fr/fr/statistiques/fichier/1893198/estim-pop-dep-sexe-aq-1975-2020.xls
#   - https://www.insee.fr/fr/statistiques/fichier/1893198/evolution-population-dep-2007-2020.xls
#   - https://www.insee.fr/fr/statistiques/fichier/1893198/estim-pop-nreg-sexe-gca-1975-2020.xls
#   - https://www.insee.fr/fr/statistiques/fichier/1893198/estim-pop-nreg-sexe-aq-1975-2020.xls
#   - https://www.insee.fr/fr/statistiques/fichier/1893198/evolution-population-nreg-2007-2020.xls

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
exportORGCsv    = last("export-organization-20200314-065744.csv")
tagsCsv        = last("tags-2020-04-20-09-22.csv")


# In[ ]:


S1 = set (dataFileVMgr.listMostRecent())
S2 =set((exportDSCsv ,tagsCsv,  exportORGCsv ))
missing = S1. difference(S2)
if len(missing) > 0:
    print (f"Missing comparing with most recent files in ../data:")
    for f in missing:
        print(f"\t{f}")


# In[ ]:


metaCodeTranchesAgeCSV ="../dataPop/code-tranches-dage.csv" 

estimPopDepSxXLS      ="../dataPop/estim-pop-dep-sexe-aq-1975-2020.xls"
estimPopDepSxGXLS     ="../dataPop/estim-pop-dep-sexe-gca-1975-2020.xls"
estimPopRegSxXLS      ="../dataPop/estim-pop-nreg-sexe-aq-1975-2020.xls"
estimPopRegSxGXLS     ="../dataPop/estim-pop-nreg-sexe-gca-1975-2020.xls"
evolPopDepXLS         ="../dataPop/evolution-population-dep-2007-2020.xls"
evolPopRegXLS         ="../dataPop/evolution-population-nreg-2007-2020.xls"

inseeDepXLS           ="../dataPop/InseeDep.xls"


# Now load the stuff

# In[ ]:


ad  = lambda x: "../dataPop/"+x
data_exportDS = read_csvPandas(ad(exportDSCsv), error_bad_lines=False,sep=";" )
data_tags     = read_csvPandas(ad(tagsCsv), error_bad_lines=False,sep=";")
data_exportORG= read_csvPandas(ad(exportORGCsv), error_bad_lines=False,sep=";")


# In[ ]:


metaCodeTranchesAge = read_csvPandas(metaCodeTranchesAgeCSV, error_bad_lines=False,sep=";")
estimPopDepSx       = read_xlsxPandas(estimPopDepSxXLS, error_bad_lines=False,sep=",")
estimPopDepSxG      = read_xlsxPandas(estimPopDepSxGXLS, error_bad_lines=False,sep=",")
estimPopRegSxX      = read_xlsxPandas(estimPopRegSxXLS , error_bad_lines=False,sep=",")
estimPopRegSxG      = read_xlsxPandas(estimPopRegSxGXLS, error_bad_lines=False,sep=",")
evolPopDep          = read_xlsxPandas(evolPopDepXLS , error_bad_lines=False,sep=",")       
evolPopReg          = read_xlsxPandas(evolPopRegXLS , error_bad_lines=False,sep=",")      

inseeDep            = read_xlsxPandas(inseeDepXLS, error_bad_lines=False,sep=",", sheet_name=1, header=7)
inseeReg            = read_xlsxPandas(inseeDepXLS, error_bad_lines=False,sep=",", sheet_name=0, header=7)


# Show the shape of the loaded data:

# In[ ]:


def showBasics(data,dataName):
    print(f"{dataName:24}\thas shape {data.shape}")

dataListDescr = ( (data_exportDS, "data_exportDS"),
                (data_tags, "data_tags"),
                (data_exportORG,"data_exportORG"),
                (metaCodeTranchesAge,"metaCodeTranchesAge"),
                (estimPopDepSx ,"estimPopDepSx "),
                (estimPopDepSxG,"estimPopDepSxG"),
                (estimPopRegSxX,"estimPopRegSxX"),
                (estimPopRegSxG,"estimPopRegSxG"),
                (evolPopDep,"evolPopDep"),
                (evolPopReg,"evolPopReg"),
                (inseeDep,"inseeDep"),
                (inseeReg,"inseeReg")
                )
    
for (dat,name) in dataListDescr:
    showBasics(dat,name)


# In[ ]:


for (dat,name) in dataListDescr:
    if name[0:5]=="meta_": continue
    print(f"\nDescription of data in '{name}'\n")
    display(dat.describe().transpose())
    


# ## Explore the INSEE export-dataset-\*.csv
# 
# ### Use utilities to find rows corresponding to regexp

# In[ ]:


#from IPython.core.display import display, HTML
#display(HTML("<style>.container { width:100% !important; }</style>"))


# In[ ]:


data_exportDS.loc[:2].values


# In[ ]:


df1 =  DfMatcher(data_exportDS)


# In[ ]:



df1.showMatch('description','stat.*population.*')
df1.prMatch('description','stat.*population.*')


# ### Now look at population statistics
# #### Landed at the wrong place
# I like the western seaside, but this was not the target!

# In[ ]:


interesting = df1.rowMatch('slug','recensement.*population-population$') 


# In[ ]:


interesting.loc[:, ['url', 'title']].values


# In[ ]:


interesting.values


# ## Explore population from INSEE files
# See above for the files and how they may be found. 

# In[ ]:


evolPopDep          


# Comments to be exploited later:
# - evolPopReg           
# - estimPopbeDepSx      
# - estimPopDepSxG     
# - estimPopRegSxX     
# - estimPopRegSxG      

# In[ ]:


metaCodeTranchesAge  


# In[ ]:


inseeReg


# In[ ]:


inseeDep


# In[ ]:


inseeDep.iloc[:,2:].sum()


# In[ ]:


inseeReg.iloc[:,4:].sum()


# In[ ]:




