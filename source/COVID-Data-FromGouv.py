#!/usr/bin/env python
# coding: utf-8

# # Sources web et contributions
# https://www.data.gouv.fr/en/datasets/donnees-des-urgences-hospitalieres-et-de-sos-medecins-relatives-a-lepidemie-de-covid-19/
# 
# https://www.data.gouv.fr/fr/datasets/donnees-hospitalieres-relatives-a-lepidemie-de-covid-19/
# 
# 
# https://github.com/alichnewsky/covid

# # Libraries

# In[1]:


# Sys import
import sys, os, re
# Common imports
import numpy             as NP
import numpy.random      as RAND
import scipy.stats       as STATS
from scipy import sparse
from scipy import linalg

# Better formatting functions
from IPython.display import display, HTML

import matplotlib        as MPL
import matplotlib.pyplot as PLT
import seaborn as SNS
SNS.set(font_scale=1)

# Python programming
from itertools import cycle
from time import time

# Using pandas
import pandas as PAN


# ## Check environment

# In[2]:


def checkSetup(chap = None):
    cwd = os.getcwd()
    dp, dir = os.path.split(cwd)
    if ( dir != 'JupySessions'):
       raise(RuntimeError("Installation incorrect, check that this executes in 'SkLearnTry' "))
    # Check subdirectory f'JupySessions/images/{chap}'
    if chap:
        img = os.path.join(dp,  'JupySessions', 'images', chap)
        if (not os.path.exists( img)):
          raise(RuntimeError("Installation incorrect, check that image dir exists at %s" % img ))
    # now check that the data is where it belongs
    ddir = os.path.join(dp,  'data')
    if (not os.path.exists( ddir)):
          raise(RuntimeError("Installation incorrect, check that data dir exists at %s" % ddir ))


# In[3]:


checkSetup()


# # Load Data

# ## Functions

# In[32]:


def read_csvPandas(fname,clearNaN=False, **kwargs):
    """ Read a csv file, all keywords arguments permitted for pandas.read_csv 
        will be honored
    """
    df = PAN.read_csv(fname,**kwargs)
    if clearNaN:
        return df.dropna(how="all").dropna(axis=1)
    return df


# ## Load from CSV 
# These csv have been downloaded before!

# In[127]:


dailyDepCsv = "../data/sursaud-covid19-quotidien-2020-04-11-19h00-departement.csv"
dailyRegionCsv = "../data/sursaud-covid19-quotidien-2020-04-11-19h00-region.csv"
hospAgeCsv = "../data/donnees-hospitalieres-classe-age-covid19-2020-04-11-19h00.csv"
hospNouveauCsv = "../data/donnees-hospitalieres-nouveaux-covid19-2020-04-11-19h00.csv"
hospCsv = "../data/donnees-hospitalieres-covid19-2020-04-11-19h00.csv"

metaHebdoCsv = "../data/metadonnee-urgenceshos-sosmedecin-covid19-hebdo.csv" 
metaQuotRegCsv = "../data/metadonnee-urgenceshos-sosmedecin-covid19-quot-reg.csv"
metaQuotFraCsv = "../data/metadonnee-urgenceshos-sosmedecin-covid19-quot-fra.csv" 
metaQuotCsv = "../data/metadonnee-urgenceshos-sosmedecin-covid19-quot.csv"


metaHospservices = "../data/metadonnees-services-hospitaliers-covid19.csv"
metaHospAge = "../data/metadonnees-donnees-hospitalieres-covid19-classes-age.csv"
metaHospIncid = "../data/metadonnees-hospit-incid.csv"
metaHosp = "../data/metadonnees-donnees-hospitalieres-covid19.csv"
metaHospEtabl = "../data/donnees-hospitalieres-etablissements-covid19-2020-04-11-19h00.csv"

metaSexeCsv = "../data/metadonnees-sexe.csv"
metaRegionsCsv="../data/regions-france.csv"
metaTranchesAgeCsv="../data/code-tranches-dage.csv"


# Now load the stuff

# In[131]:


meta_HospServices    = read_csvPandas(metaHospservices, clearNaN=True, error_bad_lines=False,sep=";", header=1)


# In[132]:


meta_HospServices


# In[266]:


data_dailyRegion = read_csvPandas(dailyRegionCsv, error_bad_lines=False,sep="," )
data_dailyDep    = read_csvPandas(dailyDepCsv, error_bad_lines=False,sep=",")
data_hospAge     = read_csvPandas(hospAgeCsv, error_bad_lines=False,sep=";")
data_hospNouveau = read_csvPandas(hospNouveauCsv, error_bad_lines=False,sep=";")
data_hosp        = read_csvPandas(hospCsv, error_bad_lines=False,sep=";")

meta_Hebdo   = read_csvPandas(metaHebdoCsv,     clearNaN=True, error_bad_lines=False,sep=";", header=2)
meta_QuotReg = read_csvPandas(metaQuotRegCsv, clearNaN=True, error_bad_lines=False,sep=";", header=1)
meta_QuotFra = read_csvPandas(metaQuotFraCsv, clearNaN=True, error_bad_lines=False,sep=";", header=1)
meta_Quot    = read_csvPandas(metaQuotCsv, clearNaN=True, error_bad_lines=False,sep=";", header=1)
meta_HospServices = read_csvPandas(metaHospservices, clearNaN=True, error_bad_lines=False,sep=";")
meta_HospAge      = read_csvPandas(metaHospAge, clearNaN=True, error_bad_lines=False,sep=";")
meta_HospIncid    = read_csvPandas(metaHospIncid, clearNaN=True, error_bad_lines=False,sep=";")
meta_Hosp         = read_csvPandas(metaHosp, clearNaN=True, error_bad_lines=False,sep=";")

meta_Sexe = read_csvPandas(metaSexeCsv, clearNaN=True, error_bad_lines=False,sep=";",header=0)
meta_Regions = read_csvPandas(metaRegionsCsv, clearNaN=True, error_bad_lines=False,sep=",")
meta_Ages    =  read_csvPandas(metaTranchesAgeCsv, clearNaN=True, error_bad_lines=False,sep=";")


# ## Figure out data characteristics

# In[171]:


def showBasics(data,dataName):
    print(f"{dataName:24}\thas shape {data.shape}")

dataListDescr = ((data_dailyRegion, "data_dailyRegion"), 
                  (data_dailyDep,"data_dailyDep"), 
                  (data_hospAge,"data_hospAge"),
                  (data_hospNouveau,"data_hospNouveau"),
                  (data_hosp,"data_hosp"),
                  (meta_Hebdo,"meta_Hebdo"),
                  (meta_QuotReg,"meta_QuotReg"),
                  (meta_QuotFra,"meta_QuotFra"),
                  (meta_Quot,"meta_Quot"),
                  (meta_HospServices,"meta_HospServices"),
                  (meta_HospAge,"meta_HospAge"),
                  (meta_HospIncid,"meta_HospIncid"),
                  (meta_Hosp,"meta_Hosp"),
                  (meta_Sexe,"meta_Sexe"),
                  (meta_Regions,'meta_Regions'),
                  (meta_Ages,'meta_Ages'))
    
for (dat,name) in dataListDescr:
    showBasics(dat,name)


# In[172]:


for (dat,name) in dataListDescr:
    if name[0:5]=="meta_": continue
    print(f"\nDescription of data in '{name}'\n")
    display(dat.describe().transpose())


# In[173]:


for (dat,name) in dataListDescr:
    if name[0:5]!="meta_": continue
    print(f"\nMeta data in '{name}'\n")
    display(dat)


# ## Bon, et si on faisait un peu de graphiques

# ### Données de  urgences hospitalières et de SOS médecins 
# Df: dailyRegion ( file sursaud-covid19-quotidien)
# #### Structure the data

# Select age category '0', thus getting all ages

# In[174]:


def select_Ages(df, ageGroup='0'):
    return df.loc[df['sursaud_cl_age_corona'] == ageGroup]
def select_AllAges(df):
    return select_Ages(df)


# In[175]:


def groupRegions(df):
    return df.groupby('date_de_passage')


# In[237]:


gr_all_age_regions = groupRegions(select_AllAges(data_dailyRegion)).sum()


# In[240]:


gr_all_age_regions.columns 


# Concerning the date field, move to a date-time format, and then convert the index into elapsed days from
# start of table; I do this into a copy of the table, since I may need the original.

# In[257]:


dfGr = PAN.DataFrame(gr_all_age_regions.copy(), columns=gr_all_age_regions.columns[1:])
dt = PAN.to_datetime(dfGr.index,format='%Y-%m-%d' )
elapsedDays = dt - dt[0]
dfGr.index = elapsedDays.days
PLT.figure(figsize=(10,10))
PLT.plot(dfGr);

 # plots an axis lable
PLT.xlabel(f"Days since {dt[0]}")    
PLT.title("All age groups");
# sets our legend for our graph.
PLT.legend(dfGr.columns,loc='best') ;
PAN.set_option('display.max_colwidth', None)
display(meta_QuotReg[[ "Colonne","Description_FR" ]])


# ### Hospital data
# DF: hospNouveau  File: donnees-hospitalieres-nouveaux-covid19

# In[298]:


gr_all_data_hospNouveau=data_hospNouveau.groupby('jour').sum()
dfGrHN = PAN.DataFrame(gr_all_data_hospNouveau)
dt = PAN.to_datetime(dfGrHN.index,format='%Y-%m-%d' )
elapsedDays = dt - dt[0]
dfGrHN.index = elapsedDays.days

PLT.figure(figsize=(10,10))
PLT.plot(dfGrHN);
 # plots an axis lable
PLT.xlabel(f"Days since {dt[0]}")    
PLT.title("Daily variation in patient status");
# sets our legend for our graph.
PLT.legend(dfGrHN.columns,loc='best') ;
PAN.set_option('display.max_colwidth', None)
display(meta_HospServices[[ "Colonne","Description_EN" ]])
display(meta_HospIncid[[ "Colonne","Description_EN" ]])


# In[299]:


gr_all_data_hosp=data_hosp.loc[data_hosp["sexe"] == 0 ].groupby('jour').sum()
cols = [ c for c in gr_all_data_hosp.columns if c != 'sexe']
dfGrH = PAN.DataFrame(gr_all_data_hosp[cols])
dt = PAN.to_datetime(dfGrH.index,format='%Y-%m-%d' )
elapsedDays = dt - dt[0]
dfGrH.index = elapsedDays.days

PLT.figure(figsize=(10,10))
PLT.plot(dfGrH);
 # plots an axis lable
PLT.xlabel(f"Days since {dt[0]}")    
PLT.title("Daily patient status (ICU,Hosp) / Accumulated (discharged, dead)");
# sets our legend for our graph.
PLT.legend(dfGrH.columns,loc='best') ;
PAN.set_option('display.max_colwidth', None)
display(meta_Hosp[[ "Colonne","Description_EN" ]])


# In[ ]:




