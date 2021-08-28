'''
Setup some utilities, very much related to our project of displaying figures
in Jupyter. 
'''

__author__ = 'Alain Lichnewsky'
__license__ = 'MIT License'
__version__ = '1.0'


# Sys import
import sys, os, re

# Using pandas and numpy (NP happens in matplotlib)
import pandas as PAN
import numpy  as NP
import math

# Python programming
from itertools import cycle
from collections import Iterable, Mapping

# My stuff
from lib.utilities import *
import matplotlib        as MPL
# reinitialize default matplotlib behaviour
svMPL_figsize = MPL.rcParams['figure.figsize']
MPL.rcParams['figure.figsize'] = [12, 10]

import matplotlib.pyplot as PLT
import seaborn as SNS
SNS.set(font_scale=1)

##
##  See example of utilisation after the classes
##
class  figureFromFrame(object):
    """ Make a figure from a DataFrame; 
        Keywords listed in defaultOpts are honored.

        Note that subplot spacing can be further adjusted by
        calling 'plt.subplots_adjust' with appropriate parameters,
        this can be done after figure generation.

    """
    defaultOpts = {"figsize":(8.0,6.0),"subplotIndex":1}
    
    # should we have a white list instead of a blacklist?    
    excludeFiltered = ("subplots", 'subplotIndex', 'dateTranslate')
    def __init__(self, df, **kwdOpts):
        self._setDf( df, NZOnly = False)
        self.optd={}
        self.diagnosticsHash={}  #directory for hashing emitted diagnostics to emit once
                                 #for now see usage in method _doLineAttrs; currently
                                 #counting, still need to figure out how to use count!
        self.lines = None
        setDefaults(self.optd, kwdOpts, figureFromFrame.defaultOpts)

        optdFilter = { z[0]:z[1] for z in self.optd.items()
                                 if z[0] not in figureFromFrame.excludeFiltered }


        self.subplotIndex = self.optd["subplotIndex"]
        if "subplots" in  self.optd :
            f,s = PLT.subplots(**(self.optd["subplots"]), **optdFilter)
            self.fig = f
            self.subplots = s
        else:
            f,s = PLT.subplots(**optdFilter)
            self.fig = f
            self.subplots = s

        self._setSubplot()

        
        #print(f"in figureFromFrame.__init__: self.fig:{type(self.fig)}")
        #print(f"                           : self.subplots:{type(self.subplots)}")
        #print(f"                           : self.currSub:{type(self.currSub)}")
        #print(f"                           : self.subplotIndex:{self.subplotIndex}")

    def _setDf(self,df, NZOnly=True):    
        if df is None:
            if  not NZOnly:
                self.df = None
        else:
              self.df   = df.copy()

    def setAttrs(self, **attrs):
        self._plotKwd(attrs)
        
    def __del__(self):
        # reinitialize default matplotlib behaviour
        MPL.rcParams['figure.figsize'] = svMPL_figsize

        
    def _setSubplot(self):
        if isinstance(self.subplots, NP.ndarray):    
            pos = self.subplotIndex -1
            if (pos < 0) or (pos >= self.subplots.size):
              raise RuntimeError(f"pos={pos} not within bounds")
            # row by row numbering 
            sz = self.subplots.shape[1]  
            self.currSub =  self.subplots[ pos//sz, pos%sz ]
        else:
            self.currSub =  self.subplots
            
    def advancePlotIndex(self,incr=1):
         if isinstance(self.subplots, NP.ndarray): 
             self.subplotIndex = 1 + (self.subplotIndex + (incr -1)) % self.subplots.size
             
        
    def _plotKwd(self,kwdOpts):
        """ handle keyword parameters pertaining to 
            - figure (x,y)labels, yscale, title, legend, 
            - forward keyword parameters that pertain to lines to _doLineAttrs
            - general documentation (including options) at 
              https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.plot.html
        """
        # plots an axis label
        if "xlabel" in kwdOpts:
           self.currSub.set_xlabel(kwdOpts["xlabel"]) 
        if "ylabel" in kwdOpts:
           self.currSub.set_ylabel(kwdOpts["ylabel"])
        if "title" in kwdOpts:
           self.currSub.set_title(kwdOpts["title"])
        if "yscale" in kwdOpts:
           self.currSub.set_yscale(kwdOpts["yscale"]) 

        self._doLineAttrs(kwdOpts)
        # sets our legend for our graph.
        if "legend"  in kwdOpts and kwdOpts["legend"]:          
           self.currSub.legend(self.df.columns,loc='best') ;


    def _doLineAttrs(self,kwdOpts):       
        """ handle keyword parameters pertaining to lines
            - linestyles are documented at:
               https://matplotlib.org/stable/gallery/lines_bars_and_markers/linestyles.html
            - markers at 
              https://matplotlib.org/stable/api/markers_api.html#module-matplotlib.markers

        """
        def assignOpt( kwdOpts, clab, l):
            def memoDiagnose(copDir, diagn):
                "TBD: This function should move to a library and be tested"
                diagnHash = hash( (clab, frozenset(copDir.keys())) )
                if diagnHash not in self.diagnosticsHash:
                    print(diagn, file = sys.stderr)
                    self.diagnosticsHash[diagnHash]=1
                else:
                    self.diagnosticsHash[diagnHash] += 1

            if 'colOpts' in kwdOpts:
                copDir =  kwdOpts['colOpts']
                if ( isinstance(copDir, dict)
                     and any(map(lambda x: len(x)==0, copDir.values()))):
                    memoDiagnose(copDir, "Not a good idea to have empty colOpts entries")
                    return

                if  clab in  copDir:
                     PLT.setp(l,  ** copDir[clab])
                else:
                    memoDiagnose(copDir,
                                 "In {type(self)}._doLineAttrs.assignOpt({type(clab)})"
                                 + f"\n\t{clab} not in {copDir.keys()}")

        cols = self.df.columns
        if self.lines is None:
            pass
        elif isinstance(self.lines,dict):
            for k in self.lines.keys():
                l = self.lines[k]
                assignOpt( kwdOpts, k , l)
        else:
            count = -1
            for l in self.lines:
                count += 1
                #p = PLT.getp(l, 'label')
                clab =    cols[count]
                assignOpt( kwdOpts, clab, l)

    def doPlot(self, df=None,  colOpts = {}, **kwdOpts):
        self. _setDf(df)
        if self.df is None:
            raise RuntimeError("By now you must have given me a DataFrame")
        self.preparePlot()
        colSel = self.df.columns
        
        postAttribs = ("yscale",)
        for c in colSel:
               if c in colOpts:
                    optd  = { k:v for (k,v) in colOpts[c].items() if k not in postAttribs}
                    poptd = { k:v for (k,v) in colOpts[c].items() if k  in postAttribs}
               else:
                    optd  = {}
                    poptd = {}
                    
        self._setSubplot()
        self.lines = self.currSub.plot(self.df,**optd);
        self._plotKwd(kwdOpts)
        self._plotKwd(poptd)
                
    def doPlotBycol(self, df=None, colSel=None, colOpts = {}, **kwdOpts):
        self._setDf(df)
        self._setSubplot()
        if self.df is None:
            raise RuntimeError("By now you must have given me a DataFrame")

        self.preparePlot()
        if colSel is None:
           colSel = self.df.columns
        chk = set(colSel)-set(self.df.columns)
        if len(chk)>0:
            raise RuntimeError(f"Unexpected col names in colSel={chk}")

        self.lines={}
        for c in colSel:
               if c in colOpts:
                    optd = colOpts[c]
               else:
                    optd = {}
               l = self.currSub.plot(self.df.loc[:,c], **optd);     
               self.lines[c]=l
        self._plotKwd(kwdOpts)

    def  preparePlot(self):
        pass


class  figureTSFromFrame(figureFromFrame):
    """Make a figure from a time series from a DataFrame; 
          it is expected that the row index are dates in string.
          These are converted into the elapsed days from start of table, and represented
          in DateTime format.

          Keywords listed in defaultOpts are honored; 
          - keyword 'dateTranslate' permits to iron out date format inconsistencies,
                      like when I found in loaded data an index:  
                      "..., '2020-06-28', '2020-06-29', '27/06/2020', '28/06/2020', ...".

         Note that subplot spacing can be further adjusted by
         calling 'plt.subplots_adjust' with appropriate parameters,
         this can be done after figure generation.

    """
    defaultOpts = {"dateFmt":'%Y-%m-%d',
                   "dateTranslate": True}
    def __init__(self, df, **kwdOpts):
        figureFromFrame.__init__(self, df, **kwdOpts)
        setDefaults(self.optd, kwdOpts, figureTSFromFrame.defaultOpts)
    
    def  preparePlot(self):
        self._dtToElapsed()
    
    def _dtToElapsed(self):
        self.df.origIndex = self.df.index
        if self.optd["dateTranslate"]:
           trDates= list( map (  figureTSFromFrame._dateTranslator,  self.df.index ))
        else:
            trDates = self.df.index

        self.dt = PAN.to_datetime(trDates, format=self.optd["dateFmt"]  )
        self.elapsedDays = self.dt - self.dt[0]
        self.df.index = self.elapsedDays.days

    dateTranslatorRegexp = re.compile("^(\d{2})/(\d{2})/(\d{4})$")
    def _dateTranslator(dte):
        """ This is used to mitigate data format inconsistencies which have been found in
            practice, .... a more sophisticated scheme will be put in place in case such
            things continue to pop up.
        """
        try:
            mobj =  figureTSFromFrame. dateTranslatorRegexp.match(dte)
            if mobj:
               mg = mobj.groups()
               return mg[2] + "-" + mg[1] + "-" + mg[0] 
            else:
                return dte
        except Exception as err:
            print(f"Unable to translate date {type(dte)}{dte}", file=sys.stderr)
            raise err
        
    # Two examples of using this class are given below:

##  Output and more details at https://github.com/AlainLich/COVID-Data

##  ------------------------------------------------------------  Example 2
##  painter = figureTSFromFrame(dm)
##  colOpts = {'dc_F': {"c":"r","marker":"v"},  
##             'dc_M': {"c":"b","marker":"v"},
##             'rea_F': {"c":"r","marker":"o", "linestyle":"--"},  
##             'rea_M': {"c":"b","marker":"o", "linestyle":"--"},
##             'rad_F': {"marker":"+"},
##             'rad_M': {"marker":"+"}
##            }
##  painter.doPlotBycol()
##  painter.setAttrs(colOpts = colOpts,
##                      xlabel  = f"Days since {painter.dt[0]}",
##                      title="Whole France\ / Hospital\n Male....",
##                 legend=True    ) 
##  display(meta_Hosp[[ "Colonne","Description_EN" ]])
##  ImgMgr.save_fig("FIG004")
##  
##  ------------------------------------------------------------  Example 2
##  colOpts = {'dc':  {"c":"b","marker":"v"},  
##             'rea': {"c":"r","marker":"o", "linestyle":"--"},  
##             'rad':  {"marker":"^"},
##             'hosp': {"marker":"+"}
##            }
##  
##  painter = figureTSFromFrame(None, subplots=subnodeSpec, figsize=(15,15))
##  for i in range(len(levAge)):
##      cat = ageClasses[i]
##      if cat < 90:
##          title = f"Age {cat-9}-{cat}"
##      else: 
##          title = "Age 90+"
##          
##      dfExtract = dhRAg.loc(axis=1)[:,cat]
##      # remove the now redundant information labeled 'cl_age90'
##      dfExtract.columns = dfExtract.columns.levels[0]
##      painter.doPlotBycol(dfExtract);
##      painter.setAttrs(colOpts = colOpts,
##                       xlabel  = f"Days since {painter.dt[0]}",
##                       title   = title,
##                       legend  = True    ) 
##      
##      
##      painter.advancePlotIndex()
##
##  PLT.subplots_adjust( bottom=0.1, top=0.9, 
##                       wspace=0.4,  hspace=0.4)
##  ImgMgr.save_fig("FIG005")          
##  ------------------------------------------------------------  END


def subPlotShape(n,colFirst=True, maxCol=10):
    """This returns the shape for displaying n subwindows in a 2D array presentation
       for now, maxCol works only if colFirst=True. 
       Preliminary, to be improved! 
    """
    sm1=min( math.floor(math.sqrt(n) + 0.5), maxCol)
    sm2=math.ceil(n/sm1)
    if colFirst:
       return (sm1,sm2)
    else:
        return (sm2,sm1)
    
