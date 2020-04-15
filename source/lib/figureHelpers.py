'''
Setup some utilities, very much related to our project of displaying figures
in Jupyter. 
'''

__author__ = 'Alain Lichnewsky'
__license__ = 'MIT License'
__version__ = '1.0'


# Sys import
import sys, os, re

# Using pandas
import pandas as PAN

# Python programming
from itertools import cycle

# My stuff
from lib.utilities import *
import matplotlib        as MPL
import matplotlib.pyplot as PLT
import seaborn as SNS
SNS.set(font_scale=1)

##
##  See example after the classes
##
class  figureFromFrame(object):
    """ Make a figure from a DataFrame; 
        Keywords listed in defaultOpts are honored.
    """
    defaultOpts = {"figsize":(10,10)}
    def __init__(self, df, **kwdOpts):
        self.df   = df.copy()
        self.optd={}
        setDefaults(self.optd, kwdOpts, figureFromFrame.defaultOpts)
        if "subplots" in kwdOpts:
            f,s = PLT.subplots(**(kwdOpts["subplots"]), **self.optd)
            self.fig = f
            self.subplots = s
        else:
            f,s = PLT.subplots(**self.optd)
            self.fig = f
            self.subplots = s
            self.currSub =  s
        print(f"in figureFromFrame.__init__: self.fig:{type(self.fig)}")
        print(f"                           : self.subplots:{type(self.subplots)}")
        print(f"                           : self.currSub:{type(self.currSub)}")
        
    def doPlot(self, **kwdOpts):   
        self.currSub.plot(self.df);
        self._plotKwd(kwdOpts)
        
    def _plotKwd(self,kwdOpts):
        # plots an axis label
        if "xlabel" in kwdOpts:
           self.currSub.set_xlabel(kwdOpts["xlabel"]) 
        if "ylabel" in kwdOpts:
           self.currSub.set_ylabel(kwdOpts["ylabel"])
        if "title" in kwdOpts:
           self.currSub.set_title(kwdOpts["title"])
        # sets our legend for our graph.
        if "legend"  in kwdOpts and kwdOpts["legend"]:          
           self.currSub.legend(self.df.columns,loc='best') ;   
        
    def doPlotBycol(self, colSel=None, colOpts = {}, **kwdOpts):
        if colSel is None:
           colSel = self.df.columns
        chk = set(colSel)-set(self.df.columns)
        if len(chk)>0:
            raise RuntimeError(f"Unexpected col names in colSel={chk}")
        
        for c in colSel:
               if c in colOpts:
                    optd = colOpts[c]
               else:
                    optd = {}
               
               self.currSub.plot(self.df.loc[:,c], **optd); 
        self._plotKwd(kwdOpts)


# In[ ]:


class  figureTSFromFrame(figureFromFrame):
    """Make a figure from a time series from a DataFrame; 
          it is expected that the row index are dates in string.
          These are converted into the elapsed days from start of table, and represented
          in DateTime format.
          Keywords listed in defaultOpts are honored.
    """
    defaultOpts = {"dateFmt":'%Y-%m-%d'}
    def __init__(self, df, **kwdOpts):
        figureFromFrame.__init__(self, df)
        setDefaults(self.optd, kwdOpts, figureTSFromFrame.defaultOpts)
        self._dtToElapsed()
        
    def _dtToElapsed(self):
        self.df.origIndex = self.df.index
        self.dt = PAN.to_datetime(self.df.index, format=self.optd["dateFmt"]  )
        self.elapsedDays = self.dt - self.dt[0]
        self.df.index = self.elapsedDays.days
        


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
