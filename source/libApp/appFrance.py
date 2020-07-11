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


# Help with meta data
# I encountered some surprises, `checkRepresentedRegions` shows unknown codes which do
# occur in some files!

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



# The figure making process is generalized into this class, facilitating coding
# graphics, and also enabling variants as derived classes
#

#This deals with data from emergency rooms and SOS medecin
#Données de  urgences hospitalières et de SOS médecins

class UrgenceSOSDataFig(object):
    def __init__(self, dateStart=None):
         self.dateStart = dateStart


    def initPainter(self, dataFrame = None,
                            single =  True,  colSelectRex = None,
                            subnodeSpec=None,
                            figsize=(15,15), maxCol=6, colFirst=False):    
    
        if single:
            dfGr = self.colSelect(dataFrame, frex = colSelectRex)
            self.painter = figureTSFromFrame(dfGr,figsize=(12,8))
              
        else:
            pass
              
    def colSelect (self, dataframe, frex=None):
        dfGrCols = dataframe.columns.map(lambda x: frex.match(x) is not None ) 
        selcols  = dataframe.columns[dfGrCols]
        dfGr = PAN.DataFrame(dataframe.copy(), columns=selcols)
        return dfGr


    def mkImage(self, label=None, title=None, legend=True, xlabel=None):
        self.painter.doPlot()
        self.painter.setAttrs(label=label, title=title, legend=legend, xlabel=xlabel)
        
    

