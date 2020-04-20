# coding: utf-8

# (C) A.Lichnewsky, 2018, 2020
#

__author__ = 'Alain Lichnewsky'
__license__ = 'MIT License'
__version__ = '1.0'


# This is a first attempt at writing a class (or set thereof) to perform a
# clean, train, eval cycle on some data for supervised learning
#
# This is mostly inspired by my first attempt with the Titanic Kaggle data set
#
# Credits:
#  Some of the graphics are inspired by code excerpts from
#    https://www.kaggle.com/poonaml/titanic-survival-prediction-end-to-end-ml-pipeline
#  (C) Poonam Ligade,  Titanic, title:"Survival Prediction End to End ML Pipeline"

#
#            ----------------------------------------
#


# Common toolkit imports
import numpy             as 	NP
import numpy.random      as 	RAND
import scipy.stats       as 	STATS
from   scipy             import sparse
from   scipy             import linalg

# Using scikit-learn
from   sklearn.preprocessing import StandardScaler, LabelEncoder, OneHotEncoder
# Using pandas
import pandas 		 as 	PAN

# To plot pretty figures
import matplotlib        as 	MPL
import matplotlib.pyplot as 	PLT
import seaborn 		 as 	SNS


# Python programming
from itertools import cycle
from time import time
from enum import Enum
from collections import Counter
from IPython.display import display

import lib.basicUtils       as BU
import lib.utilities        as LIBU
class dataModel(object):
    """ 
       This class hides a DataFrame for managing and visualizing a DataFrame.
       The idea is that the DataFrame is to be prepared for a machine learning task.
    """
    # Class constants
    class DM(Enum):
        NORM  = 1 >> 1 # normalized Dataframe (owned copy, possibly modified/normalized)
        REF   = 1 >> 0 # reference  Dataframe (reference to DataFrame passed at init)
    
    # Methods
    def __init__(self, dframe, **kwargs):
        """
         The class keeps a reference to a DataFrame
          - recognized keyword args:
           - targetCol	name of a column in dframe that should be used as a target, 
                        otherwise name "target" is used. It will be decided later if
                        the column may be provided separately

         Examples:
        """
        if "targetCol" in kwargs:
            self.__targetCol = targetCol
        else:
            self.__targetCol = "target"

        self.__dframe = dframe

    def keys(self,**kwargs):
        """ return the keys (columns) of DataFrame
              keyword args
                which :  <DM object> specifying for which data frame, by default
			it will output the   dataframe passed at __init__       
        """
        if ("which" in kwargs) and kwargs["which"] == dataModel.DM.NORM:
            return self.__normDFrame.keys()
        else:
            return self.__dframe.keys()

    def getFrame(self,**kwargs):
        """ return a reference to the contained/referenced dataframe 
              keyword 
                which :  <DM object> specifying for which data frame, by default
			it will output the   dataframe passed at __init__       
                copy  : if True, returns a copy
        """
        if ("which" in kwargs) and kwargs["which"] == dataModel.DM.NORM:
            df = self.__normDFrame
        else:
            df = self.__dframe

        if ("copy" in kwargs) and kwargs["copy"]:
             return df.copy()
        else:
             return df

    def shape(self, which = DM.REF):
        """ Helper function to access shape
        """
        return  self.getFrame(which=which).shape

    def columns(self, which = DM.REF):
        """ Helper function to access columns
        """
        return  self.getFrame(which=which).columns

    def index(self, which = DM.REF):
        """ Helper function to access index
        """
        return  self.getFrame(which=which).index
    
    def DFApply(self, fn, **kwargs):
        """
          Apply a function to the DataFrame
          keyword
               which = <DM object>
        """
        if ("which" in kwargs) and kwargs["which"] == dataModel.DM.NORM:
            return fn(self.__normDFrame)
        else:
            return fn(self.__dframe)
        
    def showNulls(self,**kwargs):
        """ Prints number of nulls in column of dataframe
            keyword
               which = <DM object>
        """
        if ("which" in kwargs) and kwargs["which"] == dataModel.DM.NORM:
            df = self.__normDFrame
        else:
            df = self.__dframe
        
        print("Number of nulls per col.")
        display(df.isnull().sum())

    def outlier_detect(self,n=2,cols=(),**kwargs):        
      """
        Perform outlier detection using Tukey method
        Arguments:
           - df   : dataframe
           - n    : nb of outlier
           - cols : list of column names
        returns:
           indices of rows with n or more outliers
      """
      if ("which" in kwargs) and kwargs["which"] == dataModel.DM.NORM:
            df = self.__normDFrame
      else:
            df = self.__dframe
      
      return outlier_detect(df,n=n,cols=cols,**kwargs)

    def outlierLocate(self, n=2, cols=None, **kwargs):
       """
        Return excerpts of rows with outliers determined using Tukey method
        Arguments:
           - n    : min nb of outlier on a row for detection
           - cols : list of column names to restrict outlier detection (must ensure
                    only numerical is kept)
        keywords:
           showCols = if used, must be True
        returns:
               excerpts of this dataframe showing outliers, other values may be 
               represented as     NaNs
       """
       if ("which" in kwargs) and kwargs["which"] == dataModel.DM.NORM:
            df = self.__normDFrame
       else:
            df = self.__dframe
       if cols==None:
           cs = df.columns
       else:
           cs = cols
       return outlierLocate(df, n=n, cols=cs, **kwargs)
  
    def __validate_rowMask(self, df,mask):
        """
        private function
        validate a row mask passed by user
        Note: might be expanded later to check that NaNs have been resolved (masked or
              replaced), alternatively value imputer may be used, see Imputer class in 
              scikit-learn
        """
        if type(mask) != NP.ndarray or mask.dtype != NP.bool:
            print("Expecting mask of type numpy.ndarray dtype=numpy.bool")
            raise RuntimeError("in dataModel.normalize, binary row mask type incorrect")
        if len(mask) != df.shape[0]:
            raise RuntimeError("in dataModel.normalize, binary row mask length incorrect")

    def __doNormCol(self, specs):
        """ Exclusive normalization modes (a column may only specify one of those:
             - OneHot
             - Category  (sub kwd values gives list of values for encoding!!)
             - MeanVar
             - Apply : applies a user provided function to generate new values 
                      (see examples at bottom of source file)

            Prior to normalization, missing value replacement is provided using 
            specifier "MissingInput" with strategies:
                   dropNA: drop the line with NA
                   avgNA : replace NA entries with average
        """
        for ck in  specs:
            spec=specs[ck]
            if "MissingInput" in spec:
                print("Processing NAs in column:", ck," with specs:", spec)
                if ("dropNA" in spec["MissingInput"]) and spec["MissingInput"]["dropNA"]:
                    if ( not ("InPlace" in spec["MissingInput"])
                         or
                         not spec["MissingInput"]["InPlace"]):
                       raise RuntimeError("Only Inplace=True is provided at this time")
                    self.__normDFrame.dropna(axis="index", subset=(ck,), inplace=True)
                elif ("avgNA" in spec["MissingInput"]) and spec["MissingInput"]["avgNA"]:
                    if ( not ("InPlace" in spec["MissingInput"])
                         or
                         not spec["MissingInput"]["InPlace"]):
                       raise RuntimeError("Only Inplace=True is provided at this time")
                    m = self.__normDFrame.loc[:,ck].mean()
                    self.__normDFrame.loc[:,ck].fillna(value=m,inplace=True)
                elif ("fillNA" in spec["MissingInput"]) and spec["MissingInput"]["fillNA"]:
                    if ( not ("InPlace" in spec["MissingInput"])
                         or
                         not spec["MissingInput"]["InPlace"]):
                       raise RuntimeError("Only Inplace=True is provided at this time")
                    v = spec["MissingInput"]["fillValue"]
                    self.__normDFrame.loc[:,ck].fillna(value=v,inplace=True)
                    print ("MissingInput, filled NAs in col", ck, "with values", v)
                else:
                    raise RuntimeError("Only MissingInput strategies provided:dropNA,avgNA,fillNA")
                    ### Other replacement strategies TBD!!!!                    

        for ck in  specs:
            spec=specs[ck]
            print("Normalizing column:", ck," with specs:", spec)
            if (type(spec) != dict):
                 raise RuntimeError("Specification is not a dict:%s"%spec)
            ct = NP.sum([ x in spec for x in ("MeanVar", "Category","OneHot")])
            if ct > 1:
                 raise RuntimeError("in  dataModel.normalize, exclusive specifiers used")

            if "MissingInput" in spec:
                pass  # done previously in separate loop

            if "MeanVar" in spec:
                scaler = StandardScaler()
                dta = self.__normDFrame.loc[:,ck].values.reshape(-1,1)
                scaler.fit(dta)
                if ("InPlace" in spec) and spec["InPlace"]:
                    self.__normDFrame.loc[:,ck] = scaler.transform(dta)
                else:
                    self.__normDFrame.loc[:,spec["ColInsert"]] = scaler.transform(dta)
                    
            if "Category" in spec:
                scaler = LabelEncoder()
                if "values" in spec:
                    valueSet = spec["values"]
                else:
                    valueSet = self.__normDFrame.loc[:,ck].values.unique()
                scaler.fit(valueSet)
                dta = self.__normDFrame.loc[:,ck].values
                if ("InPlace" in spec) and spec["InPlace"] :
                    self.__normDFrame.loc[:,ck] = scaler.transform(dta)
                else:
                    self.__normDFrame.loc[:,spec["ColInsert"]] = scaler.transform(dta)

            if "OneHot" in spec:
                scaler = OneHotEncoder()
                if "values" in spec:
                    valueSet = PAN.Series(spec["values"])
                    scaler.fit(valueSet.values.reshape(-1,1))
                else:
                    valueSet = NP.unique(self.__normDFrame.loc[:,ck].values)
                    scaler.fit(valueSet.reshape([-1,1]))
                
                dta = self.__normDFrame.loc[:,ck].values.reshape(-1,1)                
                if ("InPlace" in spec) and spec["InPlace"] :
                     raise RuntimeError("in  dataModel.normalize, OneHotEncoding not compat with InPlace ")
                else:
                    repl = scaler.transform(dta).toarray()
                    #  watch, repl has type numpy.ndarray
                    print("\n+++\nreplacement has type:", type(repl), "\tshape=")
                    if ( len(spec["ColInsert"]) < repl.shape[1]):
                        raise RuntimeError("in  dataModel.normalize, OneHotEncoding need more column names for insertion ")
                    for i in range(0, repl.shape[1]):
                       print("Inserting in col:", spec["ColInsert"][i] )
                       self.__normDFrame.loc[:, spec["ColInsert"][i] ] = repl[:,i]

            if "Apply" in spec:
                if "Map" in spec and spec["Map"]:
                    r = list( map( spec["Apply"],  self.__normDFrame.loc[:,ck].values))
                else:
                    r = spec["Apply"](self.__normDFrame.loc[:,ck].values)
                if ("InPlace" in spec) and spec["InPlace"] :
                    self.__normDFrame.loc[:,ck] = r
                else:
                    self.__normDFrame.loc[:,spec["ColInsert"]] = r
                
            
    def normalize(self, **kwargs):
        """
          make a copy from (a possibly restricted set of columns of ) __dframe.
          A copy is kept in __normDFrame.

         Keyword arguments:
            cols	= columns to select
            colNorm     = columns to normalize (with normalization process)
            rowsMask    = mask for selecting rows, do we need to do this or keep a set
                          of rowmasks
            add         = if True, then we are applying additional normalization steps
                          to the object

        Please look at the examples/test at the end of the source file for more
        details on colNorm parametrization. Roughly:
           colNorm = dict with entries (keys, spec)
                    key :  name of a column
                    spec  dict with (key,values) as follows
                          ColInsert: iterable col names of columns to insert
                          Category: use category encoder
        		  OneHot:   use one-hot encoder
        		  MeanVar:  mean value encoder
        	          MissingInput: dict 
        				   dropNA : drop lines containing NA in 
                                                    specified col
        				   InPlace: in fact this is implied..
        """
        if "add"  in kwargs and kwargs["add"]:
            if 'colNorm' in kwargs:
                self.__doNormCol(kwargs['colNorm'])
            return
        
        if "cols" in kwargs:
            cls =  kwargs["cols"]
            if "rowsMask" in kwargs:
                msk = kwargs["rowsMask"]
                self.__validate_rowMask( self.__dframe, msk )
                self.__normDFrame     = self.__dframe.loc[msk].loc[:,cls].copy()
            else:
                self.__normDFrame     = self.__dframe.loc[:,cls].copy()
        else:
            if "rowsMask" in kwargs:
                msk = kwargs["rowsMask"]
                self.__validate_rowMask( self.__dframe, msk )
                self.__normDFrame     = self.__dframe.loc[msk].copy()
            else:
                self.__normDFrame     = self.__dframe.copy()

        # __doNormCol deals with NaNs and missing data before it attempts to normalize,
        #       some encoders/fit do not tolerate NaN        
        if 'colNorm' in kwargs:
            self.__doNormCol(kwargs['colNorm'])

    def describe(self,**kwargs):
        """ Print statistical summary of columns of dataframe.
            Accepts same keywords as PAN.DataFrame.describe
        keyword
               which = <DM object>
        recall that keywords may be passed to PAN.DataFrame.describe
            e.g.   include="all" describe all columns, including non numerical
                          =["O"] describe categorical columns
        """
        if ("which" in kwargs) and kwargs["which"] == dataModel.DM.NORM:
            df = self.__normDFrame
        else:
            df = self.__dframe
            
        selArgs = dict( (c,kwargs[c]) for c in kwargs if c!="which")
        return df.describe(**selArgs)

    
    def hist( self, **kwargs):
        """
           Shows histograms of columns
           keyword args: include those of PAN.DataFrame.hist
              - bins : number of bins in histogram(s)
              - other graphic/matplotlib keywords (figsize,...)
              - which = <DM object>
        """
        if ("which" in kwargs) and kwargs["which"] == dataModel.DM.NORM:
            df = self.__normDFrame
        else:
            df = self.__dframe
        df.hist(**kwargs)

    def facetGridGeneric(self, pltProc = PLT.scatter ,
                               stripAlso=(), **kwargs):

        print("In facetGridGeneric, kwargs=",kwargs)
        stripArgs = ["xcol","ycol","gridX", "gridY", "title",
                     "SNSArgs","PLTArgs", "PLTpargs", "SNSpargs",
                     "which"]
        stripArgs.extend(stripAlso)
        
        fargs =  dict( (k,v) for k,v in kwargs.items() if ( k not in stripArgs ))

       

        SNSArgs  = BU.addKwdDict(kwargs, "SNSArgs")
        SNSpargs = BU.addKwdDict(kwargs, "SNSpargs",default=[])
        PLTArgs  = BU.addKwdDict(kwargs,"PLTArgs")
        PLTpargs = BU.addKwdDict(kwargs,"PLTpargs",default=[])

        if ("which" in kwargs) and kwargs["which"] == dataModel.DM.NORM:
            df = self.__normDFrame
        else:
            df = self.__dframe
           
        g = SNS.FacetGrid(df, *SNSpargs, **SNSArgs,  **fargs)
        g = g.map(pltProc,    *PLTpargs, **PLTArgs,  **fargs).add_legend()

        PLT.subplots_adjust(top=0.8)
        g.fig.suptitle(kwargs["title"])
        
    def facetGridScatter(self, **kwargs):
        """
          Display a subplot grid with scatterplots of conditional relationships
          Arguments:
            hue= column name of categorical data which will be represented in hue param
            col= column name of categorical data, where all values will receive separate 
                plot
            xcol= column name for x axis in plots (continuous data)
            ycol= column name for y axis in plots (continuous data)
            title = string representing title
            SNSArgs = additional arguments for call to SNS.FacetGrid
            PLTArgs = additional arguments for call to PLT.scatter
            other keyword args passed to both of these functions
	  Keywords:
           - which = <DM object>
        """
        stripAlso = ("row","col","xcol","ycol")
        fargs =  dict( (k,v) for k,v in kwargs.items() if ( k not in  stripAlso ))
        SNSArgs  = BU.addKwdDict(kwargs, "SNSArgs")
        SNSArgs["row"] = kwargs["row"]
        SNSArgs["col"] = kwargs["col"]

        SNSpargs = BU.addKwdDict(kwargs, "SNSpargs",default=[])

        PLTArgs  = BU.addKwdDict(kwargs,"PLTArgs")

        PLTpargs = BU.addKwdDict(kwargs,"PLTpargs", default=[])
        PLTpargs.extend((kwargs["xcol"],  kwargs["ycol"]))

        return self.facetGridGeneric(PLT.scatter,
                                     stripAlso=("hue","col", "xcol", "ycol"),
                                     SNSpargs=SNSpargs, PLTpargs=PLTpargs,
                                     SNSArgs=SNSArgs, PLTArgs=PLTArgs,
                                     **fargs)



    def facetGridHist(self, **kwargs):
        """
          Display a subplot grid with histograms of selected categorical data
          Arguments:
            row= column name of categorical data  where all values will be separated 
                 in individual histograms
            col= column name of categorical data, where all values will be separated 
                 in individual histograms
            hcol= column name for quantity to appear in histograms
            title = string representing title
            SNSArgs = additional arguments for call to SNS.FacetGrid
            PLTArgs = additional arguments for call to PLT.hist and PLT.subplots
	  Keywords:
           - which = <DM object>

          Note: row, col, hue form the row, column, or hue dimensions of the grid.
                They must be categorical or discrete.
        """
        stripAlso = ("row","col","hcol","hcolor", "hue","SNSArgs","PLTArgs" )
        fargs =  dict( (k,v) for k,v in kwargs.items() if ( k not in  stripAlso ))


        SNSArgs  = BU.addKwdDict(kwargs, "SNSArgs")
        SNSArgs["col"] = kwargs["col"]
        SNSArgs["row"] = kwargs["row"]        

        SNSpargs = BU.addKwdDict(kwargs, "SNSpargs",default=[])

        PLTArgs  = BU.addKwdDict(kwargs,"PLTArgs", default= {"edgecolor":"w"})
        PLTArgs["color"]= kwargs["hcolor"]

        PLTpargs = BU.addKwdDict(kwargs,"PLTpargs", default=[])
        PLTpargs.extend((kwargs["hcol"], ))
        
        return self.facetGridGeneric(PLT.hist,
                                     stripAlso=("row","col", "hcol", "hcolor"),
                                     SNSpargs=SNSpargs, PLTpargs=PLTpargs,
                                     SNSArgs=SNSArgs, PLTArgs=PLTArgs,
                                     **fargs)

    def facetGridPlot(self, **kwargs):
        """
          Display a subplot grid with histograms of selected categorical data
          Arguments:
            row= column name of categorical data  where all values will be separated 
                 in individual histograms
            col= column name of categorical data, where all values will be separated 
                 in individual histograms
            hcol= column name for quantity to appear in histograms
            hue = draw separate curves of different colors against this category
            title = string representing title
            SNSArgs = additional arguments for call to SNS.FacetGrid
                      may be used to pass "hue" spec
            PLTArgs = additional arguments for call to SNS.distplot and PLT.subplots
                      in particular 
				hist=False to suppress the histogram
                                rug= True  to show samples x-coordinate
				bins= nb of bins
				kde=False : suppress curve
                       more info https://seaborn.pydata.org/tutorial/distributions.html 
	  Keywords:
           - which = <DM object>

          Note: row, col, hue form the row, column, or hue dimensions of the grid.
                They must be categorical or discrete.
        """
        stripAlso = ("row","col","hcol","hcolor", "hue","SNSArgs","PLTArgs" )
        fargs =  dict( (k,v) for k,v in kwargs.items() if ( k not in  stripAlso ))


        SNSArgs  = BU.addKwdDict(kwargs, "SNSArgs")
        SNSArgs["col"] = kwargs["col"]
        SNSArgs["row"] = kwargs["row"]
        if "hue" in kwargs:
            SNSArgs["hue"] = kwargs["hue"]

        SNSpargs = BU.addKwdDict(kwargs, "SNSpargs",default=[])

        PLTArgs  = BU.addKwdDict(kwargs,"PLTArgs", default= {})
        PLTArgs["color"]= kwargs["hcolor"]

        PLTpargs = BU.addKwdDict(kwargs,"PLTpargs", default=[])
        PLTpargs.extend((kwargs["hcol"], ))
        
        return self.facetGridGeneric(SNS.distplot,
                                     stripAlso=("row","col", "hcol", "hcolor"),
                                     SNSpargs=SNSpargs, PLTpargs=PLTpargs,
                                     SNSArgs=SNSArgs, PLTArgs=PLTArgs,
                                     **fargs)
        

    #          +++++++++++++++++++++++++++++++++
    #		These are ordinary functions !!!
    #          +++++++++++++++++++++++++++++++++
        
def boxStripPlot(**kwargs):
        """
           Display overlayed boxplot and stripplot.
           Arguments
             data: a dataframe
             x, y : names of variables in ``data``
             title    = string representing title
             SNSBox   = additional arguments for call to SNS.boxplot
             SNSStrip = additional arguments for call to SNS.stripplot
             PLTArgs  = additional arguments for call to PLT.*

           Note: in library x,y,hue can be passed as vectors, here only as column
                   names in ``data``, moreover  hue must be passd in SNSBox and/or SNSStrip
        """

        stripArgs = ("data", "x", "y", "title","SNSBox","SNSStrip","PLTArgs","which")
        fargs =  dict( (k,v) for k,v in kwargs.items() if ( k not in stripArgs ))
        if (not "SNSBox" in kwargs.keys()):
           SNSBox= { }
        else:
           SNSBox= kwargs["SNSBox"]

        if (not "SNSStrip" in kwargs.keys()):
           SNSStrip= { "jitter":True, "edgecolor":"gray", "color":"red" }
        else:
           SNSStrip= kwargs["SNSStrip"]

        if (not "PLTArgs" in kwargs.keys()):
           PLTArgs=  {"fontsize":12}
        else:
           PLTArgs= kwargs["PLTArgs"]

        ax = SNS.boxplot(x=kwargs["x"], y=kwargs["y"], 
                         data=kwargs["data"],**SNSBox)
        ax = SNS.stripplot(x=kwargs["x"], y=kwargs["y"],
                   data=kwargs["data"], **SNSStrip)
        PLT.title(kwargs["title"],**PLTArgs,**fargs)

def densityCatPlot( **kwargs):
        """
           Display the density of a feature broken down by another feature's category 
           Arguments
             data     = a dataframe
             x        = name of a variable/column in ``data``
             cats     = name of a variable/column in ``data`
             title    = string representing title
             legend   = iterable with legends for ident plots
             PLTArgs  = additional arguments for call to plot, other kwd args passed to
                       PLT.title and PLT.xlabel

             Note: in library x,y,hue can be passed as vectors, here only as column
                   names in ``data``, moreover  hue must be passd in SNSBox and/or SNSStrip
        """

        stripArgs = ("data", "x", "cats", "title", "legend", "PLTArgs", "which")
        fargs =  dict( (k,v) for k,v in kwargs.items() if ( k not in stripArgs ))
        if (not "PLTArgs" in kwargs.keys()):
           PLTArgs=  {"fontsize":12}
        else:
           PLTArgs= kwargs["PLTArgs"]

        data =  kwargs["data"]
        cats =  kwargs["cats"]
        x    =  kwargs["x"]
        
        categs = data.loc[:, cats].astype('category').cat.categories
        for cg in categs:
            data.loc[:, x][ data.loc[:, cats] == cg].plot(kind='kde', **PLTArgs)    

        # plots an axis lable
        PLT.xlabel(x, **fargs)    
        PLT.title( kwargs["title"],  **fargs)
        # sets our legend for our graph.
        PLT.legend(kwargs["legend"], loc='best') ;

#		++++++++++++++++++++++++++++++++++
#  		This might provide a better/nicer categorical plot TBD!!!
#		++++++++++++++++++++++++++++++++++
#g = sns.kdeplot(train["Age"][(train["Survived"] == 0) & (train["Age"].notnull())], color="Red", shade = True)
#g = sns.kdeplot(train["Age"][(train["Survived"] == 1) & (train["Age"].notnull())], ax =g, color="Blue", shade= True)
#g.set_xlabel("Age")
#g.set_ylabel("Frequency")
#g = g.legend(["Not Survived","Survived"])
#		++++++++++++++++++++++++++++++++++++++++++++++

        
def corrHeatMap(**kwargs):
        """
           Display the density of a feature broken down by another feature's category 
           Arguments
             data     = a dataframe
             title    = string representing title
             PLTArgs  = additional arguments for call to plot, other kwd args passed to
                       PLT.title and PLT.xlabel
             SNSArgs  = additional arguments for call to SNS.heatmap
             Note: in library x,y,hue can be passed as vectors, here only as column
                   names in ``data``, moreover  hue must be passd in SNSBox and/or SNSStrip
        """

        stripArgs = ("data", "x", "cats", "title", "legend", "PLTArgs", "SNSArgs", "which")
        fargs =  dict( (k,v) for k,v in kwargs.items() if ( k not in stripArgs ))
        if (not "PLTArgs" in kwargs.keys()):
           PLTArgs=  {"figsize":(10, 10)}
        else:
           PLTArgs= kwargs["PLTArgs"]
        if (not "SNSArgs" in kwargs.keys()):
           SNSArgs=  {"cmap":'YlGnBu',"linecolor":"white"}
        else:
           SNSArgs= kwargs["SNSArgs"]

        data = kwargs["data"]
        corr=data.corr()
        PLT.figure(**PLTArgs)

        SNS.heatmap(corr, vmax=.8, linewidths=0.01,
                    square=True,annot=True,**SNSArgs)
        PLT.title( kwargs["title"], **fargs);

def simpleHeatMap(**kwargs):
        """
           Display the density of a feature broken down by another feature's category 
           Arguments
             data     = a dataframe
             title    = string representing title
             PLTArgs  = additional arguments for call to plot, other kwd args passed to
                       PLT.title and PLT.xlabel
             SNSArgs  = additional arguments for call to SNS.heatmap
             Note: in library x,y,hue can be passed as vectors, here only as column
                   names in ``data``, moreover  hue must be passd in SNSBox and/or SNSStrip
        """

        stripArgs = ("data", "x", "cats", "title", "legend", "PLTArgs", "SNSArgs", "which")
                     
        fargs =  dict( (k,v) for k,v in kwargs.items() if ( k not in stripArgs ))
        PLTArgs=  {}
        LIBU.setDefaults(PLTArgs,  tryDictKey= ("PLTArgs", kwargs),
                     	      defaultDict= {"figsize":(10, 10)})
        SNSArgs= {}
        LIBU.setDefaults(SNSArgs, tryDictKey= ("SNSArgs", kwargs),
        		     defaultDict={"cmap":'YlGnBu',"linecolor":"white",
                                          "vmax":0.8, "vmin":0.0, "linewidths":0.01,})
        data = kwargs["data"]
        PLT.figure(**PLTArgs)

        SNS.heatmap(data, 
                    square=True,annot=True,**SNSArgs)
        PLT.title( kwargs["title"], **fargs);


def doBoxPlots(data,ycols, xcols= (), stripIt=False):
    """
        data =  dataframe
        ycols=  columns to show
        xcols=  columns into which to break down
        stripIt : if True add a stripPlot showing datapoints
    """
    for ycol in ycols:
      for xcol in xcols:
        if stripIt:
           boxStripPlot( data = data, y=ycol,x=xcol,title="%s/%s"%(ycol,xcol) )
        else:
          SNS.boxplot(data = data, y=ycol, x=xcol)
        PLT.show()
        
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++        
#   Outlier detection
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++        

def outlier_detect(df,n=2,cols=None, **kwargs):        
      """
        Perform outlier detection using Tukey method
        Arguments:
           - df   : dataframe
           - n    : nb of outlier
           - cols : list of column names
        keywords:
           showCols = also return the columns,
           TukeyCoef = coefficient used in Tukey's method default=1.5 (outlier) whereas
                       3.0 means "far out" 
                       see https://en.wikipedia.org/wiki/Outlier#Detection
        returns:
               indices of rows with n or more outliers
           if  showCols = True:
               tuple first: indices of rows with n or more outliers
                     table showing for each row the column
        Credits:
         Yassine GhouzamTitanic Top 4% with ensemble modeling       
         https://www.kaggle.com/yassineghouzam/titanic-top-4-with-ensemble-modeling
      """
      outlier_indices = []
      if cols == None or len(cols)==0:
          doCols = df.columns
      else:
          doCols = cols
      if "TukeyCoef" in kwargs:
          coefTukey =  kwargs["TukeyCoef"]
      else:
          coefTukey = 1.5
          
      for col in doCols:
        Q1 = NP.percentile(df[col], 25)
        Q3 = NP.percentile(df[col],75)
        IQR = Q3 - Q1         # Interquartile range (IQR)
        
        outlier_step = coefTukey * IQR
        
        # Determine a list of indices of outliers for feature col
        outlier_list_col = df[(df[col] < Q1 - outlier_step) | (df[col] > Q3 + outlier_step )].index
        
        # append the found outlier indices for col to the list of outlier indices 
        outlier_indices.append(outlier_list_col)

      # select observations containing more than 2 outliers
      outlier_indicesDF = PAN.DataFrame(NP.zeros( (df.shape[0],len(doCols)) ))
      for i in range(0,len(outlier_indices)):
          ilst = outlier_indices[i]
          outlier_indicesDF.iloc[list(ilst),i] = +1

      multiple_outlier_rows =      outlier_indicesDF.sum(axis=1) >= n
      if "showCols" in kwargs:
          return ( multiple_outlier_rows,
                   outlier_indicesDF.loc[multiple_outlier_rows,:]!=0)
      else:
          return multiple_outlier_rows

def outlierLocate(df, n=2, cols=None, **kwargs):
    """
        Return excerpts of rows with outliers determined using Tukey method
        Arguments:
           - df   : dataframe
           - n    : min nb of outlier on a row for detection
           - cols : list of column names to restrict outlier detection (must ensure
                    only numerical is kept)
        keywords:
           showCols = if used, must be True
        returns:
               excerpts of df showing outliers, other values may be represented as
               NaNs
    """
    outIdx,outCols = outlier_detect(df, n=n,cols=cols, showCols=True )

    def myFun(msk,fd,tc, outCols):
        idx = msk.name
        mtc = [ tc[i] for i in range(0,len(msk)) if msk[i]]
        c= fd.loc[idx,mtc]   
        return c

    outs =[ myFun(outCols.iloc[i,:],df,cols,outCols) for i in range(0,outCols.shape[0])]
    outDF=PAN.DataFrame(outs)
    return outDF

def displayOutliers(dm, maxOutliers, cols=(), txt="", **kwargs):
    """  display the rows having  maxOutliers or more outliers in a dataframe.
         Arguments
           dm = data fraùe
           maxOutliers
           cols = if specified, restrict to said columns
           txt: prefix in emitted intro printout
         kwords
           head : limit the dataframe output to this number of rows
    """
    outIdx,outCols = dm.outlier_detect(n=maxOutliers,cols= cols, showCols=True )
    print(txt, "there are ",NP.sum(outIdx), " rows with", maxOutliers,
          "or more outliers")
    f = dm.getFrame().loc[outIdx,:]
    if "head" in kwargs:
        f = f.head(kwargs["head"])
    display(f)


    
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++        
#  Detect non normalized data, look for numeric columns
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++        
def numericCols(df):
    """ List numeric columns of pandas DataFrame
    """
    numerics = ['int16', 'int32', 'int64', 'float16', 'float32', 'float64']
    return df.select_dtypes(include=numerics).columns

def nonNumericCols(df):
    """ List non numeric columns of pandas DataFrame
    """
    return [c for c in df.columns if c not in numericCols(df)]


def farNormalized(df, f1=10, f2=5):
    """ Find columns that are far from normalized, may be combined with outlier search
    """
    d   = df.describe()
    am  = NP.abs(d.loc["mean",:])
    ast = NP.abs(d.loc["std",:] -1.0)
    mmsk = am > f1
    smsk = ast > f2
    return d.loc[ :, NP.logical_or(mmsk,smsk)].iloc[:4,:]
    
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++        
#   Various helper functions
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++        
def mklegendForCat(data, col, colstat, formatStr= "%s %d mean=%6.2f std=%.2f"):
    """ Make a series of legend strings for the split of a dataframe along a 
        categorical column
        Arguments:
           data: dataframe
           col : categorical column
           colstat : column for which the legends will contain mean and std
    """
    legends=[]
    for fc in sorted(data.loc[:,col].unique()):
      msk = data.loc[:,col]==fc
      m=data.loc[msk,colstat].mean()
      s=data.loc[msk,colstat].std()
      lstr=formatStr % (col, fc,m,s)
      legends.append(lstr)
    return legends
