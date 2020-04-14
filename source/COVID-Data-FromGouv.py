#!/usr/bin/env python
# coding: utf-8

# #  Simple tool to analyze data from www.data.gouv.fr
# 
# 
# ## Web Sources
# https://www.data.gouv.fr/en/datasets/donnees-des-urgences-hospitalieres-et-de-sos-medecins-relatives-a-lepidemie-de-covid-19/
# 
# https://www.data.gouv.fr/fr/datasets/donnees-hospitalieres-relatives-a-lepidemie-de-covid-19/
# 

# # Libraries

# In[ ]:


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
import datetime

# Using pandas
import pandas as PAN
import xlrd


# In[ ]:


import warnings
warnings.filterwarnings('ignore')
print("For now, reduce python warnings, I will look into this later")


# ##  Save figures

# In[ ]:


class ImageMgr(object):
    def __init__(self, rootdir=".", chapdir="DefaultChap", imgtype="jpg"):
       
         self.PROJECT_ROOT_DIR = rootdir
         self.CHAPTER_ID=chapdir
         self.imgtype="."+imgtype
            
    def save_fig(self, fig_id, tight_layout=True):
       "Save the current figure"
       path = os.path.join(self.PROJECT_ROOT_DIR, "images", self.CHAPTER_ID, fig_id + self.imgtype)
       print("Saving figure", fig_id)
       if tight_layout:
          PLT.tight_layout()
       PLT.savefig(path, format='png', dpi=300)


# ## Check environment
# 
# It is expected that your working directory is named `JupySessions`, that it has subdirectories `images/*` 
# where generated images may be stored to avoid overcrowding. At the same level as your working dir
# there should be directories `../data` for storing input data and `../source` for python scripts, libraries,...

# In[ ]:


def checkSetup(chap = None):
    cwd = os.getcwd()
    dp, dir = os.path.split(cwd)
    if ( dir != 'JupySessions'):
       raise(RuntimeError("Installation incorrect, check that this executes in 'JupySessions' "))
    # Check subdirectory f'JupySessions/images/{chap}'
    if chap:
        img = os.path.join(dp,  'JupySessions', 'images', chap)
        if (not os.path.exists( img)):
          raise(RuntimeError("Installation incorrect, check that image dir exists at '%s'" % img ))
    # now check that the expected subdirectories are where expected
    for d in ('data','source'):
       ddir = os.path.join(dp,  d)
       if (not os.path.exists( ddir)):
          raise(RuntimeError("Installation incorrect, check that  dir '%s' exists at '%s'" % (d,ddir )))


# In[ ]:


checkSetup(chap="Chap01")
ImgMgr = ImageMgr(chapdir="Chap01")


# # Load Data

# ## Functions

# In[ ]:


def read_csvPandas(fname,clearNaN=False, **kwargs):
    """ Read a csv file, all keywords arguments permitted for pandas.read_csv 
        will be honored
    """
    df = PAN.read_csv(fname,**kwargs)
    if clearNaN:
        return df.dropna(how="all").dropna(axis=1)
    return df


# In[ ]:


def read_xlsxPandas(fname,clearNaN=False, **kwargs):
    """ Read a xlsx file, all keywords arguments permitted for pandas.read_csv 
        will be honored
    """
    df = PAN.read_excel(fname,**kwargs)
    if clearNaN:
        return df.dropna(how="all").dropna(axis=1)
    return df


# In[ ]:


class manageDataFileVersions(object):
    """ For each file name in directory, find which are different versions of same as 
        indicated in the file name with pattern yyyy-mm-dd-HHhMM, 
    """
    def __init__(self, dirpath="../data"):
        "dirpath is path relative current working directory"
        self.dirpath = dirpath
        if not os.path.isdir(dirpath):
            raise RuntimeError(f"Path {dirpath} not directory")
        self._walk()
    datedFileRex = re.compile("""^(?P<hdr>.*[^\d])
    (?P<year>\d+)-(?P<month>\d+)-(?P<day>\d+)  # Year
    -(?P<hour>\d+)h(?P<minute>\d+)             # Time
    (?P<ftr>.*)$""", re.VERBOSE)    
    
    def _walk(self):
        lfiles = os.listdir(self.dirpath)
        filDir={}
        genDir={}
        for lf in lfiles:
            mobj = manageDataFileVersions.datedFileRex.match(lf)
            if mobj:
               fls = ( int(mobj.groupdict()[z]) for z in  ('year', 'month', 'day','hour','minute') )
               date = datetime.datetime( *fls )
               gen  =  "!".join(map (lambda x: mobj.groupdict()[x] , ("hdr","ftr")))
               filDir[lf]=(gen,date)
               if gen in genDir:
                    if date > genDir[gen][0]:
                        genDir[gen] = (date,lf)
               else:
                    genDir[gen]= (date,lf, self.dirpath+"/"+lf)
        self.filDir = filDir
        self.genDir = genDir
        
    def listMostRecent(self):
        return sorted([  k[1]   for k in self.genDir.values()])
    
    def getRecentVersion(self,file, default=None):
        if file not in self.filDir:
            if not default:
               raise RuntimeError(f"Unexpected file:'{file}'")
            elif default is True:
                return file
            else:
                return default
        else:
                return self.genDir[self.filDir[file][0]][1]
    


# In[ ]:


def setDefaults(dict, optDict, defaultDict):
    for (k,v) in optDict.items():
        dict[k] = v
    for  (k,v) in defaultDict.items():
        if k not in dict:
            dict[k] = v


# In[ ]:


class  figureTSFromFrame(object):
    """Make a figure from a time series from a DataFrame; 
          it is expected that the row index are dates in string.
          These are converted into the elapsed days from start of table, and represented
          in DateTime format.
          Keywords listed in defaultOpts are honored.
    """
    defaultOpts = {"dateFmt":'%Y-%m-%d', "figsize":(10,10)}
    def __init__(self, df, **kwdOpts):
        self.df   = df.copy()
        self.optd = {}
        setDefaults(self.optd, kwdOpts, figureTSFromFrame.defaultOpts)
        self._dtToElapsed()
        
    def _dtToElapsed(self):
        self.df.origIndex = self.df.index
        self.dt = PAN.to_datetime(self.df.index, format=self.optd["dateFmt"]  )
        self.elapsedDays = self.dt - self.dt[0]
        self.df.index = self.elapsedDays.days
        
    def doPlot(self, **kwdOpts):   
        PLT.figure(figsize=self.optd["figsize"])
        PLT.plot(self.df);
        self._plotKwd(kwdOpts)
        
    def doPlotBycol(self, colSel=None, colOpts = {}, **kwdOpts):
        if colSel is None:
           colSel = self.df.columns
        chk = set(colSel)-set(self.df.columns)
        if len(chk)>0:
            raise RuntimeError(f"Unexpected col names in colSel={chk}")
        
        PLT.figure(figsize=self.optd["figsize"])
        for c in colSel:
               if c in colOpts:
                    optd = colOpts[c]
               else:
                    optd = {}
               
               PLT.plot(self.df.loc[:,c], **optd); 
        self._plotKwd(kwdOpts)
        
    def _plotKwd(self,kwdOpts):
        # plots an axis label
        if "xlabel" in kwdOpts:
           PLT.xlabel(kwdOpts["xlabel"]) 
        if "ylabel" in kwdOpts:
           PLT.ylabel(kwdOpts["ylabel"])
        if "title" in kwdOpts:
           PLT.title(kwdOpts["title"])
        # sets our legend for our graph.
        if "legend"  in kwdOpts and kwdOpts["legend"]:          
           PLT.legend(self.df.columns,loc='best') ;


# Two examples of using this class is given below:
# - a simple one (the <ImgMgr> is defined above, it shows that the plot may be output to file)
# ```
# painter = figureTSFromFrame(dfGr)
# painter.doPlot(xlabel=f"Days since {painter.dt[0]}",
#                title="Whole France/Data ER + SOS-medecin\nAll age groups",legend=True  )
# ImgMgr.save_fig("FIG002")
# ```
# 
# - a more sophisticated case, where line styles are defined:    
# ```
# painter = figureTSFromFrame(dm)
# colOpts = {'dc_F': {"c":"r","marker":"v"},  
#            'dc_M': {"c":"b","marker":"v"},
#            'rea_F': {"c":"r","marker":"o", "linestyle":"--"},  
#            'rea_M': {"c":"b","marker":"o", "linestyle":"--"},
#            'rad_F': {"marker":"+"},
#            'rad_M': {"marker":"+"}
#           }
# painter.doPlotBycol(colOpts = colOpts,
#                     xlabel  = f"Days since {painter.dt[0]}",
#                title="Whole France\ / Hospital\n Male / Female\n:Daily patient status (ICU,Hosp) / Accumulated (discharged, dead)",
#                legend=True    ) 
#                ```

# ## Load from CSV 
# These csv have been downloaded before!; We check what is in the data directory; for each file, we
# identify the latest version, and list this below to make sure. This has to do with the version
# management technique (apparently) used at www.data.gouv.fr.

# In[ ]:


dataFileVMgr = manageDataFileVersions()
print("Most recent versions of files in data directory:")
for f in dataFileVMgr.listMostRecent() :
    print(f"\t{f}")


# In[ ]:


last = lambda x: dataFileVMgr.getRecentVersion(x,default=True)
dailyDepCsv    = last("sursaud-covid19-quotidien-2020-04-11-19h00-departement.csv")
dailyRegionCsv = last("sursaud-covid19-quotidien-2020-04-11-19h00-region.csv")
dailyFranceCsv = last("sursaud-covid19-quotidien-2020-04-12-19h00-france.csv")
dailyXlsx      = last("sursaud-covid19-quotidien-2020-04-12-19h00.xlsx")
weeklyCsv      = last("sursaud-covid19-hebdomadaire-2020-04-08-19h00.csv")

hospAgeCsv     = last("donnees-hospitalieres-classe-age-covid19-2020-04-11-19h00.csv")
hospNouveauCsv = last("donnees-hospitalieres-nouveaux-covid19-2020-04-11-19h00.csv")
hospCsv        = last("donnees-hospitalieres-covid19-2020-04-11-19h00.csv")
hospEtablCsv   = last("donnees-hospitalieres-etablissements-covid19-2020-04-12-19h00.csv")

S1 = set (dataFileVMgr.listMostRecent())
S2 =set((dailyDepCsv,dailyRegionCsv,dailyFranceCsv, dailyXlsx, weeklyCsv, 
         hospAgeCsv, hospNouveauCsv, hospCsv,  hospEtablCsv ))
missing = S1. difference(S2)
if len(missing) > 0:
    print (f"Missing comparing with most recent files in ../data:")
for f in missing:
    print(f"\t{f}")
    
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
# 

# In[ ]:


ad  = lambda x: "../data/"+x
data_dailyRegion = read_csvPandas(ad(dailyRegionCsv), error_bad_lines=False,sep="," )
data_dailyDep    = read_csvPandas(ad(dailyDepCsv), error_bad_lines=False,sep=",")
data_dailyFrance = read_csvPandas(ad(dailyFranceCsv), error_bad_lines=False,sep=",")
data_daily       = read_xlsxPandas(ad(dailyXlsx), error_bad_lines=False,sep=",")
data_weekly      = read_csvPandas(ad(weeklyCsv), error_bad_lines=False,sep=",")

data_hospNouveau = read_csvPandas(ad(hospNouveauCsv), error_bad_lines=False,sep=";")
data_hosp        = read_csvPandas(ad(hospCsv), error_bad_lines=False,sep=";")
data_hospAge          = read_csvPandas(ad(hospAgeCsv), error_bad_lines=False,sep=";")
data_hospEtabl        = read_csvPandas(ad(hospEtablCsv), error_bad_lines=False,sep=";")

meta_Hebdo       = read_csvPandas(metaHebdoCsv,     clearNaN=True, error_bad_lines=False,sep=";", header=2)
meta_QuotReg     = read_csvPandas(metaQuotRegCsv, clearNaN=True, error_bad_lines=False,sep=";", header=1)
meta_QuotFra     = read_csvPandas(metaQuotFraCsv, clearNaN=True, error_bad_lines=False,sep=";", header=1)
meta_Quot        = read_csvPandas(metaQuotCsv, clearNaN=True, error_bad_lines=False,sep=";", header=1)
meta_HospServices = read_csvPandas(metaHospservices, clearNaN=True, error_bad_lines=False,sep=";")
meta_HospAge      = read_csvPandas(metaHospAge, clearNaN=True, error_bad_lines=False,sep=";")
meta_HospIncid    = read_csvPandas(metaHospIncid, clearNaN=True, error_bad_lines=False,sep=";")
meta_Hosp         = read_csvPandas(metaHosp, clearNaN=True, error_bad_lines=False,sep=";")

meta_Sexe = read_csvPandas(metaSexeCsv, clearNaN=True, error_bad_lines=False,sep=";",header=0)
meta_Regions = read_csvPandas(metaRegionsCsv, clearNaN=True, error_bad_lines=False,sep=",")
meta_Ages    =  read_csvPandas(metaTranchesAgeCsv, clearNaN=True, error_bad_lines=False,sep=";")


# ## Figure out data characteristics

# In[ ]:


def showBasics(data,dataName):
    print(f"{dataName:24}\thas shape {data.shape}")

dataListDescr = ((data_dailyRegion, "data_dailyRegion"), 
                  (data_dailyDep,"data_dailyDep"), 
                  (data_hospAge,"data_hospAge"), 
                  (data_dailyFrance, "data_dailyFrance"),
                  (data_daily,"data_daily"),
                  (data_weekly , "data_weekly "),
                  (data_hospNouveau,"data_hospNouveau"),
                  (data_hosp,"data_hosp"),
                  (data_hospAge,"data_hospAge"),
                  (data_hospEtabl,"data_hospEtabl"),
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


# ## Let's do some graphics!

# ### Données de  urgences hospitalières et de SOS médecins 
# Df: dailyRegion ( file sursaud-covid19-quotidien)
# #### Structure the data

# Select age category '0', thus getting all ages

# In[ ]:


def select_Ages(df, ageGroup='0'):
    return df.loc[df['sursaud_cl_age_corona'] == ageGroup]
def select_AllAges(df):
    return select_Ages(df)


# In[ ]:


def groupByDate(df):
    return df.groupby('date_de_passage')


# First, I work with the dailyRegion data, summing up for all regions.

# In[ ]:


gr_all_age_regions = groupByDate(select_AllAges(data_dailyRegion)).sum()
checkRepresentedRegions(data_dailyRegion, print=True);


# In[ ]:


dfGr = PAN.DataFrame(gr_all_age_regions.copy(), columns=gr_all_age_regions.columns[1:])
painter = figureTSFromFrame(dfGr)
painter.doPlot(xlabel=f"Days since {painter.dt[0]}",
               title="Whole France/Data ER + SOS-medecin\nAll age groups",legend=True  )

        
PAN.set_option('display.max_colwidth', None)
display(meta_QuotReg[[ "Colonne","Description_FR" ]])
ImgMgr.save_fig("FIG002")


# Then, I look at the national data, as represented in `data_dailyFrance` and `data_daily`

# In[ ]:


print(f"data_daily: {data_daily.shape}")
print(f"{','.join(data_daily.columns)}")
display(data_daily.describe())
display(data_daily[:5])

print("data_dailyFrance:  {data_dailyFrance.shape}")
print(f"{','.join(data_dailyFrance.columns)}")
display(data_dailyFrance.describe())
display(data_dailyFrance[:5])


# ### Hospital data
# DF: hospNouveau  File: donnees-hospitalieres-nouveaux-covid19

# In[ ]:


gr_all_data_hospNouveau=data_hospNouveau.groupby('jour').sum()
dfGrHN = PAN.DataFrame(gr_all_data_hospNouveau)
painter = figureTSFromFrame(dfGrHN)
painter.doPlot(xlabel=f"Days since {painter.dt[0]}",
               title="Whole France (Hospital)\nDaily variation in patient status",
               legend=True  ) 

PAN.set_option('display.max_colwidth', None)
display(meta_HospIncid[[ "Colonne","Description_EN" ]])


# In[ ]:


gr_all_data_hosp=data_hosp.loc[data_hosp["sexe"] == 0 ].groupby('jour').sum()
cols = [ c for c in gr_all_data_hosp.columns if c != 'sexe']
dfGrH = PAN.DataFrame(gr_all_data_hosp[cols])
painter = figureTSFromFrame(dfGrH)
painter.doPlot(xlabel=f"Days since {painter.dt[0]}",
               title="Whole France / Hospital\n:Daily patient status (ICU,Hosp) / Accumulated (discharged, dead)",
               legend=True  ) 
display(meta_Hosp[[ "Colonne","Description_EN" ]])
ImgMgr.save_fig("FIG003")


# In[ ]:


data_hosp_DepSex=data_hosp.set_index(["dep","sexe"])
data_hosp_DepSex[data_hosp_DepSex.index.get_level_values(1)!=0]

d1 = data_hosp_DepSex[data_hosp_DepSex.index.get_level_values(1)==1]
d2 = data_hosp_DepSex[data_hosp_DepSex.index.get_level_values(1)==2]

d1s=d1.groupby("jour").sum()
d2s=d2.groupby("jour").sum()

dm= PAN.concat([d1s,d2s], axis=1)
cols1 = list(map (lambda x: x+"_M", d1s.columns))
cols2 = list(map (lambda x: x+"_F", d2s.columns))
dm.columns = (*cols1,*cols2)


# In[ ]:


dm.loc[:, 'hosp_M']


# In[ ]:


painter = figureTSFromFrame(dm)
colOpts = {'dc_F': {"c":"r","marker":"v"},  
           'dc_M': {"c":"b","marker":"v"},
           'rea_F': {"c":"r","marker":"o", "linestyle":"--"},  
           'rea_M': {"c":"b","marker":"o", "linestyle":"--"},
           'rad_F': {"marker":"+"},
           'rad_M': {"marker":"+"}
          }
painter.doPlotBycol(colOpts = colOpts,
                    xlabel  = f"Days since {painter.dt[0]}",
               title="Whole France\ / Hospital\n Male / Female\n:Daily patient status (ICU,Hosp) / Accumulated (discharged, dead)",
               legend=True    ) 
display(meta_Hosp[[ "Colonne","Description_EN" ]])
ImgMgr.save_fig("FIG004")


# In[ ]:




