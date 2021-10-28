'''
Setup some utilities, very much related to our project of displaying figures
in Jupyter. 
'''

__author__ = 'Alain Lichnewsky'
__license__ = 'MIT License'
__version__ = '1.0'


# Sys import
import sys, os, re
from abc import ABC

# Using pandas and numpy (NP happens in matplotlib)
import pandas as PAN
import numpy  as NP
import math

# Python programming
from itertools import cycle
from collections.abc import Iterable, Mapping, Callable

# My stuff
from lib.utilities import *

# Matplotlib
import matplotlib        as MPL
# Add color
from matplotlib import cm as CM
from matplotlib.colors import ListedColormap, LinearSegmentedColormap
# Enable 3D
import mpl_toolkits.mplot3d.axes3d
from mpl_toolkits.mplot3d.axes3d import get_test_data

# reinitialize default matplotlib behaviour
svMPL_figsize = MPL.rcParams['figure.figsize']
MPL.rcParams['figure.figsize'] = [12, 10]

import matplotlib.pyplot as PLT

import seaborn as SNS
SNS.set(font_scale=1)

## Scikit_Learn ** Remains to be seen if I want to require sklearn on all applications
##              ** or if I need to modularize differently (TBD)
try:
    from sklearn import cluster
    import sklearn.preprocessing as SKPREPRO
    SKLEARN_AVAIL = True
except Exception as err:
    print ("Scikit Learn not available, some functionality may be unavailable")
    SKLEARN_AVAIL = False
    
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
        
        self.colSel = None        # Keep track of selected columns

        
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
        self._plotKwd(attrs, cols =  self.colSel)
        
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
             
        
    def _plotKwd(self,kwdOpts, cols=None):
        """ cols = list of columns to be put in legend, if None, all columns in df
                   are used
            kwdOpts: handle keyword parameters pertaining to 
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
           
        title = kwdOpts.get("title",None)
        if  title is not None :
           self.currSub.set_title(title)
           
        if "yscale" in kwdOpts:
           self.currSub.set_yscale(kwdOpts["yscale"]) 

        self._doLineAttrs(kwdOpts)
        
        # sets our legend for our graph.
        if cols is None:
            cols= self.df.columns
            
        if kwdOpts.get("legend", None):
           self.currSub.legend(cols,loc='best') ;


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
                                 f"In {type(self)}._doLineAttrs.assignOpt({type(clab)})"
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
        self.colSel = colSel
        
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
        self._plotKwd(kwdOpts, cols=colSel)

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
figureTSFromFrame.examples = """

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
"""


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
    
class FigFromBase(ABC):
    """
      Make composed figure, in a superposed or separate figures
    """
    def __init__(self,**kwargs):
        defaults = {'singleSubplot' : False,
                    'figsize': (8,4),
                    'title':"**",
                    'Do3d':False
                    }
        self.kwargs = defaults | kwargs
        if  self.kwargs['Do3d']:
           self.fig, ax1 = PLT.subplots(figsize = self.kwargs['figsize'])
           self.ax1 = self.fig.add_subplot(1, 1, 1, projection='3d') 
        elif self.kwargs['singleSubplot']:
           self.fig, self.ax1 = PLT.subplots(1,1,figsize=self.kwargs['figsize'])
           self.ax2 = self.ax1
        else:
           self.fig, (self.ax1, self.ax2) = PLT.subplots(1,2,figsize=self.kwargs['figsize'])


    def runAdapter(self,**kwargs):
        if 'adapter' in kwargs:
            kwargs |= kwargs['adapter'](self, **kwargs)
            #print(f"After adapter kwargs.keys={kwargs.keys()}")
            
        return kwargs
           
class FigFromRegressionPlot(FigFromBase):
    """
      Makes a figure composed of a scatter map and a regression, either
      in 2 subplots or superposed if keyword arg 'singleSubplot' is True
    """
    
    def __init__(self,**kwargs):
        """
            Most keyword args can be overriden/complemented in methods
            Keyword args: 
             - data: a Panda dataframe
             - xcol (rep. ycol) : name of column designation for x (resp. y) values
             - sizes: vector of sizes for representing the scatter plot markers
             - colors: vector of colors for scatter plot markers 
             - robust: (default True) : use a robust fitting method
             - singleSubplot (default True) : superpose  plots
             - adapter: permits to pass a derivative of FigAdapter, which __call__ method
                        will return a dict used to modify or complement kwargs
        """
        defaults = {'robust' : True,
                    'singleSubplot' : True,
                    'figsize': (8,4),
                    'alpha': 0.5, 
                    'title':"**FigFromRegression"}
        
        FigFromBase.__init__(self, ** defaults | kwargs)
        
        
    def __call__(self, **kwargs ):
        kwargs = self.kwargs | kwargs
        kwargs = self.runAdapter(**kwargs)
            
        xcol = kwargs['xcol']
        ycol = kwargs['ycol']
        robust = kwargs['robust']
        sizes = kwargs['sizes']
        colors = kwargs['colors']
        alpha =  kwargs['alpha']
        title = kwargs['title']
        
        data =  kwargs['data']
        
        SNS.regplot(data=data, x=xcol, y = ycol, scatter= False, robust=robust,
                    truncate=True, ax=self.ax1)
              
        plt=data.plot( x=xcol, y=ycol, s= sizes, c=colors, alpha=alpha,
                       kind='scatter',
                       title=title, 
                       ax=self.ax2)


class FigFrom3DScatterPlot(FigFromBase):
    """
      Makes a figure as a 3D scatter plot, presenting attributes as color and
      size.
    """
    
    def __init__(self,**kwargs):
        """
            Most keyword args can be overriden/complemented in methods
            Keyword args: 
             - data: a Panda dataframe
             - xcol (rep. ycol, zcol) : name of column designation for x (resp. y, z) values
             - sizes: vector of sizes for representing the scatter plot markers
             - colors: vector of colors for scatter plot markers 
             - adapter: permits to pass a derivative of FigAdapter, which __call__ method
                        will return a dict used to modify or complement kwargs
        """
        defaults = {'singleSubplot' : True,
                    'figsize': (8,4),
                    'alpha': 0.5, 
                    'title':None,
                    'Do3d':True}
        
        FigFromBase.__init__(self, ** defaults | kwargs)
        
        
    def __call__(self, **kwargs ):
        kwargs = self.kwargs | kwargs
        kwargs = self.runAdapter(**kwargs)
            
        xcol = kwargs['xcol']
        ycol = kwargs['ycol']
        zcol = kwargs['zcol']
        xlabel = kwargs.get('xlabel', 'x')
        ylabel = kwargs.get('ylabel', 'y')
        zlabel = kwargs.get('zlabel', 'z')
        
        data = kwargs['data']
        
        x=data.loc[:, xcol]
        y=data.loc[:, ycol]
        z=data.loc[:, zcol]

        sizes = kwargs['sizes']
        colors = kwargs['colors']
        alpha =  kwargs['alpha']
        title = kwargs['title']

        print(f"type colors:{type(colors)}", file=sys.stderr)
        
        self.ax1.scatter(x, y, z, c = colors, s = sizes, marker="o")

        self.ax1.set_xlabel(xlabel)
        self.ax1.set_ylabel(ylabel)
        self.ax1.set_zlabel(zlabel)
        
        if title is not None:
            self.ax1.set_title(title)

class FigAdapter(ABC):
    """
     Adapter class for FigFromRegressionPlot

     Keyword arguments:
         scaler: apply  preprocessor scaling to input data, the scaled data is only used
                 in adapter.
                 values: None (default) : no scaling
                         "standard"     : apply StandardScaler from sklearn.preprocessing

    """
    def __init__(self, **kwargs):
        self.kwargs = kwargs

    def __call__(self, figObj, figArgDict):
        return {}

    def dfNormalize(self, df):
        scalerSpec = self.kwargs.get("scaler", None)
        if scalerSpec is None:
            return df
        elif scalerSpec == "standard":
            scaler = SKPREPRO.StandardScaler()
            dfNorm = PAN.DataFrame(scaler.fit_transform(df.copy()))
            print (f"In {type(self)}.dfNormalize"+
                   f"returning\n{dfNorm.describe()}", file = sys.stderr)
            return dfNorm
        else:
            raise NotImplementedError(f"Bad scaler spec:{scalerSpec}")
            
class FigAdapter_KMeans(FigAdapter):
    """
     Adapter class for FigFromRegressionPlot, supporting data preparation by 
     kmeans clustering

     Attributes: the following attributes are externally visible/usable
         kmeans : an sklearn.cluster.KMeans object, fit after the __call__ method's
                  execution
         kolors : proposed colors from colormap, based on values in self.k_means.labels_
                  whereas the colormap conforms to the parameter passed to __call__
         kwargs:  kwargs passed at class initialization, possibly modified henceforth
         k_means_fit : if True, the adapter will not fit, this means that the fit has been
                  made; this permits to (re)use an already fit adapter, or
                  by setting to False to cause a new fit. It is also possible that several
                  figures share an adapter, to display multiple aspects of the data.
                  ** TBD ** see if a more general is_fit attribute should be initialized
                            in __init__
         scaler: see in base class
    """
    def __init__(self, **kwargs):
        defaults = {
            'nbClusters':4,
            }
        FigAdapter.__init__(self,**( defaults|kwargs))
        self.k_means = None
        self.k_means_fit = False
        
    def __call__(self, figObj, **figArgDict):
        """
          kwargs:
            - figObj : a FigFromRegressionPlot object, the dataframe is extracted
                        by key 'data'
            - clusterCols : dataframe columns to be used for clustering
            - colormap : colormap to be used, defaults to 'brg' (see matplotlib colormaps)
        """
        print(f"figObj.kwargs['data'].shape = {figObj.kwargs['data'].shape}",
              file=sys.stderr)
        print(f"figArgDict keys={figArgDict.keys}", file= sys.stderr)


        df =self.dfNormalize( figObj.kwargs['data'])
        
        clusterCols = figArgDict.get('clusterCols',  df.columns)
        colormap = figArgDict.get('colormap')
        if clusterCols is None:
            raise RuntimeError("No default or value provided for clusterCols")
        if colormap is None:
            colormap = CM.get_cmap('brg', 32)
        
        if self.k_means is  None:
            nbClusters = self.kwargs['nbClusters']            
            self.k_means = cluster.KMeans(n_clusters = nbClusters)
            
        dfExtract = df.loc[:,clusterCols]
        if not self.k_means_fit:
            if 'fitData' in self.kwargs:
                fitData = self.kwargs['fitData']
            else:
                print(f"Using all data for fitting, shape={df.shape}", file=sys.stderr)
                fitData = df

            self.k_means.fit(fitData)
            print(f"In {type(self)}.__call__: fitted j  KMeans classifier",
                      file=sys.stderr  )

            # "colors" keyword
            colors = figArgDict.get("colors",None)
            if colors is None:
                self.kolors=colormap((1+self.k_means.labels_)/(nbClusters+3))
            elif isinstance(colors, Callable):
                self.kolors=colors(self.k_means.labels_)
            else:
                raise RuntimeError(f"Wrong type for colors keyword arg:{type(colors)}")


            # "sizes" keyword
            sizes = figArgDict.get("sizes",None)
            if sizes is None:
                sizes = 30
            elif isinstance(sizes, Callable):
                sizes =sizes(self.k_means.labels_)
            elif isinstance(sizes, Iterable):
                pass
            else:
                raise RuntimeError(f"Wrong type for sizes keyword arg:{type(sizes)}")

            
        return {'sizes' : sizes,
                'colors': self.kolors
                }
    
