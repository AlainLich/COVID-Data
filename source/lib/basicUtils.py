# coding: utf-8

# (C) A.Lichnewsky, 2018

__author__ = 'Alain Lichnewsky'
__license__ = 'MIT License'
__version__ = '1.0'


#
#  These are utilities for working on Pandas, Scikit-learn etc.. environments
#
#            ----------------------------------------
#


# Common toolkit imports
import numpy             as 	NP
import numpy.random      as 	RAND
import scipy.stats       as 	STATS
from   scipy             import sparse
from   scipy             import linalg
import scipy.linalg      as     LIN


# To plot pretty figures
import matplotlib        as 	MPL
import matplotlib.pyplot as 	PLT
import seaborn 		 as 	SNS


# Using pandas
import pandas 		 as 	PAN


# Python programming
from itertools import cycle
from time import time
from enum import Enum
from datetime import date
import os
import re
#
#            ----------------------------------------
#			Singletons
#            ++++++++++++++++++++++++++++++++++++++++
#

class SingletonBase(object):
    """ This is a singleton base class, derived classes generate different singletons!!!

        See http://python-3-patterns-idioms-test.readthedocs.io/en/latest/Singleton.html
        for more ideas.
    """
    __instance = None
    __inited = None
    def __new__(cls,**kwargs):
            if not cls.__instance :
                    cls.__instance = {}
            if  cls in cls.__instance:
                    return  cls.__instance[cls]
            o = super (SingletonBase, cls).__new__(cls)
            cls.__instance[cls] = o 
            return o
    
    def __init__(self, doPrint=False, abortRemaining=None):
            if not DebugState.__inited:
                    # Mecanisme singleton
                     DebugState.__inited=1


#
#            ----------------------------------------
#
class ScoreKeeper(PAN.DataFrame):
    """ Define a score keeper DataFrame, extending class PAN.DataFrame
        Example:
           myScores = ScoreKeeper()
           myScores.enter("Run2", "Idiot", 0.8, 0.1, 80,100, 20, 200)
           display(myScores)
    """
    
    def __init__(self,**kwargs):
        """
          This init supplies default columns for the collected data frame.
        """
        #
        # Note:when coding, beware of __getattr__ and the like defined in parent class
        #
        if "columns" in kwargs :
            PAN.DataFrame.__init__(self, **kwargs)
        else:
            defaultCols = [ "Run",  "Method", "Parms",
                            "scoreTrain", "scoreMyTest",
                            "CorrectTrain", "TotalTrain", 
                            "CorrectTest", "TotalTest"]
            PAN.DataFrame.__init__(self, columns=defaultCols, **kwargs)
        
    def enter(self,*args):
        """ Enter a dataframe row, should be conformant to columns defined
        """
        self.loc[self.shape[0]]=args

class Scorer(object):
    """
        Equip a ScoreKeeper object with an entry procedure;
        This avoids having to hide the ScoreKeeper in the customize entry proc

        See tests below for examples of use. (Doc TBD!!)
    """
    def __init__(self,sk,entryproc = lambda df,*a: df.enter(*a),**kwargs):
        self.scoreKeeper = sk
        self.enterProc   = entryproc
        self.options     = kwargs

    def enter(self,*args):
        """
          Enter data in the hidden ScoreKeeper (1 dataframe row)
        """
        self.enterProc(self.scoreKeeper,*args)

    def __str__(self):
        """
         This permits to use DataFrame printing
        """
        return str(self.scoreKeeper)

    def __getattr__(self,name):
        """
         This permits to use DataFrame methods on the (not so hidden dataframe)
        """
        return self.scoreKeeper. __getattr__(name)

    # Permit to call the Scorer (equivalent to self.enter), so that the
    # Scorer may be passed when a function is expected
    def __call__(self,*pargs,**kwargs):
        return self.enterProc(self.scoreKeeper,*pargs,**kwargs)
#
#            ----------------------------------------
#		Convenience functions
#            ----------------------------------------
#
        
def read_csvPandas(fname,**kwargs):
    """ Read a csv file, all keywords arguments permitted for pandas.read_csv will be 
        honored.

        kwd arguments:
            bump_index :  increase the DataFrame index by this value

        Note: this may be used to ensure that indices in test and train dataframes are distinct,
              thereby facilitating their inclusion in the same DataFrame
    """
    if "bump_index" in kwargs:
      kwd = { k:v for (k,v) in kwargs.items() if k != "bump_index"}
      df = PAN.read_csv(fname,**kwd)
      df.index +=   kwargs["bump_index"]
    else:
      df = PAN.read_csv(fname,**kwargs)
    return df


def sortedCorrs(df,col,func=NP.abs,funclabel="func", corrlabel="corr"):
    """ Output correlations sorted based on the result of applying a function
        arguments
         df:         dataframe
         col:        column in df
         func:       function to generate a column of (preprocessed) data which is used for
                     sorting. Default: NP.abs
         funclabel : label for the added col
         corrlabel : label for the correlation col
    """
    corrs = df.corr()[col]
    return ( PAN.DataFrame([corrs, func(corrs)], index=[corrlabel, funclabel])
         .T
         .sort_values(by=funclabel,ascending = False))



#
#            ----------------------------------------
#		Persistent data collection
#            ----------------------------------------
#
import pickle 
import io
class ParameterCollector(SingletonBase):
    """ This is a singleton class, for collecting permanent data in a directory.
        
    """

    def __init__(self, fileRepo="/tmp/REPO", idRepo=None, idVersion=None,
                       retrieve=False):
        """
            arguments:
              - retrieve: 
                   if True, then fileRepo is the exact file name
                      False, filename is generated from fileRepo, idRepo, idVersion

              - fileRepo :  filename (full path) to be postfixed with
                            idRepo and idversion, file type postfix .pkl
              - idRepo   :  varying id part in file name, default: date
              - idVersion:  version id part in file name
        """
        SingletonBase.__init__(self)
        self.fileRepo = fileRepo
        if not retrieve:
            if idRepo == None:
                self.idRepo= date.today().isoformat()
            else:
                self.idRepo = idRepo

            if idVersion:
                self.idRepo+= "_" + str(idVersion)

            print("Repo id:", self.idRepo,"\tfile name:", self.fileRepo)
            self.theDict = { "file" : self.fileRepo,
                             "idRepo":self.idRepo}
        else:
            self.theDict = { "file" : self.fileRepo,
                             "restoreDate" : date.today().isoformat()
                           }
            
    def addDict(self,k,v):
        """
         arguments:
           - k : key
           - v : value
        """
        self.theDict[k] = v
         
    def keys(self):
        return self.theDict.keys()

    def save(self):
        fname = self.fileRepo+self.idRepo+".pkl"
        print ("Pickle dump in file:", fname)
        with io.open(fname, mode="wb") as file:
           pickle.dump(self.theDict, file, protocol=pickle.HIGHEST_PROTOCOL)

    def restore(self):
        fname = self.fileRepo
        print ("Pickle restore from file:", fname)
        with io.open(fname, mode="rb") as file:
           self.theDict=pickle.load(file)

        self.theDict[ "restoreDate" ] = date.today().isoformat()
                           
    def __getattr__(self,key):
        if key in  self.theDict:
            return self.theDict[key]
        raise (AttributeError("Key: %s not available in this object's dict" % key))

    def __getitem__(self,key):
        """ In some situations key may not be suitable for the __getattr__ syntax
        """
        return self. __getattr__(key)


class ParameterAccessor(object):
    """ This is a class for retrieving permanent data in a directory.
        It is compatible with ParameterCollector, but not a singleton,
        so that multiple accessors may coexist (also with a ParameterCollector)
    """

    def __init__(self, fileRepo="/tmp/REPO"):
        """
            arguments:
              - fileRepo :  filename (full path) to be postfixed with
                            idRepo and idversion, file type postfix .pkl
        """
        self.fileRepo = fileRepo
        self.theDict  = {}
                     
    def keys(self):
        return self.theDict.keys()

    def restore(self):
        fname = self.fileRepo
        print ("Pickle restore from file:", fname)
        with io.open(fname, mode="rb") as file:
           self.theDict=pickle.load(file)

        self.theDict[ "restoreDate" ] = date.today().isoformat()
                           
    def __getattr__(self,key):
        if key in  self.theDict:
            return self.theDict[key]
        raise (AttributeError("Key: %s not available in this object's dict" % key))

    def __getitem__(self,key):
        """ In some situations key may not be suitable for the __getattr__ syntax
        """
        return self. __getattr__(key)

#
#	     ------------------------------------------------------------
#		Print data collected from various structures
#	     ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

def printMethodDetailsFromCollect(df, count=5,
                                  sortCol="Mean Test CVError",
                                  methodCol="Method",
				  parmCol="Parms"):
  """ Print method performance details from DataFrame
       df : dataframe
       count : max number of printed items
       sortCol,  methodCol, parmCol : column names in df
  """
  rpa = df['GridMethodComparison'].sort_values(by=sortCol, ascending=False)
  rp= rpa.head( count )
  for i in range(rp.shape[0]):
    print ( "%30s\tTest Acc. Mean=%f" % ( rp.iloc[i,:].loc[methodCol],
                                          rp.iloc[i,:].loc[sortCol]))
    ps = rp.iloc[i,:].loc[parmCol]
    #print("ps has type:", type(ps), "\t and value:", ps)
    if isinstance( ps, str):
        ps = eval(ps)
    for  k,v in sorted( ps.items(), key=lambda x:x[0] ):
        print("\t%30s\t%s" % (k,v))
    print("+-"*20,"\n")

def printMethodSpecFromListDict(ld, count=None):
    """ Print dictionaries of the form { key : {key : val,...}...}
    """
    keys = sorted(ld.keys())
    if count:
      if len(keys) > count:
         keys=keys[0:count]
    for key in keys:
      print (key)
      for  k,v in sorted( ld[key].items(), key=lambda x:x[0] ):
          print("\t%30s\t%s" % (k,v))
      print("+-"*20,"\n")

def printMethImportanceFDict(d):
    """ 
        Print dictionnaries of the form {key : (importance, std),....}
    """
    for k in sorted(d.keys(), key=lambda x : d[x][0] , reverse=True ):
        print ("%20s\t%8.4f   \t[%8.4f, %8.4f]" % (k , d[k][0], d[k][0] - d[k][1] , d[k][0] + d[k][1]   ))
        
#
#            ----------------------------------------
#			Low Level Graphics
#            ++++++++++++++++++++++++++++++++++++++++
#

def minmaxNNA(v):
    """ given an iterable, will return a tuple with the min and max of the
        non null (NP.isnan) values
    """
    w  = list(filter(lambda x : not NP.isnan(x),v))
    return (min(w),max(w))

class bbox(object):
   """
       Manipulate bounding boxes in 2D
   """
   def __init__(self, *args):
       """
           2 args: 2 iterables for x and y values, will get min max excluding nulls
           4 args: minX,maxX,minY,maxY
       """
       if len(args)==2:
           self.minX, self.maxX = minmaxNNA(args[0])
           self.minY, self.maxY = minmaxNNA(args[1])
       elif  len(args)==4:
           self.minX, self.maxX,self.minY, self.maxY = args
       else:
           raise RuntimeError("Bad argument list:", args)

   def get(self):
       return (self.minX, self.maxX,  self.minY, self.maxY)

   def __add__(self, b):
        self.minX = min(self.minX, b.minX)
        self.maxX = max(self.maxX, b.maxX)
        self.minY = min(self.minY, b.minY)
        self.maxY = max(self.maxY, b.maxY)
        return self


# plot line defined by intercept+slope ie a*x+b
def pltLine(a,b, bbox = None, printOnly = False):
     if type(bbox) == type(None):
        xmin,xmax=PLT.xlim()
        ymin,ymax=PLT.ylim()
     else:
        xmin,xmax,ymin,ymax = bbox

     if a > 0:
          xmi = (ymin-b)/a
          xma = (ymax-b)/a
     elif a <0 :
          xmi = (ymax-b)/a
          xma = (ymin-b)/a
     else:
          PLT.plot((xmin,xmax),(b, b) , color="g")
          return
    
     xmin = max( xmin, xmi)
     xmax = min( xmax, xma)
     if not printOnly:
        PLT.plot((xmin,xmax),(a*xmin + b, a*xmax +b) , color="g")
    
#
#            ----------------------------------------
#			Graphics
#            ++++++++++++++++++++++++++++++++++++++++
#

fignum = 0

def ndimScatterPlots(N,df, colorLab="colorsNms",  styleLab=None,**kwargs):
    """ Draws a grid of scatter plots
        Arguments
           - N        :  number of configuration axes, the grid is parametrized by
		        (i,j) 0<= i < j < N

           - df       :  data frame, value axes are columns (by number 0 <= i,j < N )

           - colorLab :  label of column of df to be used to represent category (usually
                         as a result of a classification

           - styleLab  : labell of column of df to be used to select style of scatter obj.  
           - styleLabel : legend labels explaining style attributes
           - title
    """
    global fignum   #figure numbering for saving to file
    
    pairs = [ (i,j) for i in range(0,N) for j in range(0,N) if i < j ]
    fig=PLT.figure()
    color= ( 'b', 'g', 'r', 'c', 'm', 'y', 'k', 'w' )
    markerList=("o","v","+","<",">")

    for (i,j) in pairs:
       ax=fig.add_subplot(N-1,N-1, (N-1)*i+j)
       
       if not styleLab:
            df.plot.scatter(x = i,y = j,
                            c = [ color[ cc % len(color) ] for cc in df.loc[:,colorLab]],
                            ax = ax)
       else:
           styles = df.loc[:,styleLab].unique()  # May be the caller should do this ?
           styles.sort()                         #
    
           istyl = -1           
           for s in styles:
              istyl += 1
              msk = df.loc[:,styleLab] == s
              dk = df.keys()
              ax.scatter( df.loc[msk, dk[i]],
                          df.loc[msk, dk[j]], 
                          c=[ color[ int(cc)%len(color) ] for cc in df.loc[ msk, colorLab]],
                          marker=markerList[istyl])
              ax.legend( [ kwargs["StyleLabel"][i] for i in styles] )
               
       PLT.xlabel("x_"+str(i))
       PLT.ylabel("x_"+str(j))
       if "title" in kwargs:
           PLT.title (kwargs["title"])
    PLT.subplots_adjust( hspace=0.75,  wspace=0.75)
    PLT.draw()

    fileName = "/tmp/SVFIG_"+str(fignum)
    PLT.savefig(fileName)
    print("figure written in ", fileName)
    fignum += 1
    
#
#            --------------------------------------------------
#			Files and directories, File lists
#            ++++++++++++++++++++++++++++++++++++++++++++++++++
#
def selFilesDirPat(dir, pat, full=False):
    """ Select files in a directory(dir) that match a pattern (pat).
        If full is True, return path to file
    """
    lfiles = os.listdir(dir)
    lfiles.sort()

    regexp = re.compile(pat)
    fnsel = filter(lambda s: regexp.match(s),lfiles)
    if full:
        fnsel = map(lambda s: os.path.join(dir,s), fnsel)
    return list(fnsel)

def datePathFn(path):
    """ Given pathname for a file , return a pair of the pathname and 
        the modification date
    """
    return (path, os.path.getmtime(path))

def assocByDate(l1, l2, tol=0.01 ):
   """ Given 2 lists of pairs (filename, date) return  a pair (assoc, reject)
       where in assoc: a pair of files one from the first list, the other from 
       the second with approximately matching dates.
       tol: tolerance for data comparisons
   """
   ls1 = sorted(  map(datePathFn, l1),  key=lambda x:x[1])
   ls2 = sorted(  map(datePathFn, l2),  key=lambda x:x[1])
   pos1, pos2 = 0,0
   assoc = []
   reject = []
   while pos1 < len(ls1) and pos2 < len(ls2):
        if abs(ls1[pos1][1] - ls2[pos2][1]) < tol:
            assoc.append( (ls1[pos1],ls2[pos2]) )
            pos1 += 1
            pos2 += 1
        elif ls1[pos1][1] < ls2[pos2][1]:
            pos1 += 1
            reject.append(ls1[pos1-1])
        else:
            pos2 += 1
            reject.append(ls2[pos2-1])
   ret = map ( lambda x : (x[0][0], x[1][0], x[0][1] ) , assoc)
   return (ret,reject)

#
#            ----------------------------------------
#			Very low level...
#            ++++++++++++++++++++++++++++++++++++++++
#

def genLabn(n,s):
    """ Generate nth string label from a char set s
    """
    l = len(s)
    m = n
    g =""
    go = True
    while go:
        c= m % l
        g = s[c] + g
        m=m//l
        go = m > 0 
        m-= 1
    return g

def genLabs(n,s):
    """ Generate nth string label from a char set s
    """
    return [ genLabn(i,s) for i in range(0,n)]

def rangeStr(st, i,j):
    """
    Generate a list of labels st+str(k) for k in range(i,j)
    """
    return [ st+str(x) for x in range(i,j)]

def collectDict(**kwargs):
    """ return a dict initialized with kwargs.

        Essentially a syntactic helper, allows to say
        "collectDict(a=1, b=b)"
        instead of:
        {'a':1, 'b':b}
    """
    return kwargs

def toDict(**kwargs):
    return kwargs


#
#            ----------------------------------------
#	      Poke in class / inheritance attributes
#            ++++++++++++++++++++++++++++++++++++++++
#

def checkObjectAttributes(obj, attrList, printOpt=False):
    """ 
      Arguments:
         - obj : object which __dict__ will be searched
         - list: list of pairs (attribute name, attribute type)
                 if len == 1, attribute type omitted, no type check 
         - printOpt: a string to prefix "checked OK" messages 
    """

    for p in attrList:
        if p[0] not in obj.__dict__:
            raise RuntimeError("Attribute not found:",p)
        if len(p)>1 and p[1] != type(obj.__dict__[p[0]]):
            raise RuntimeError("Attribute type incorrect: expect:",p,
                               "\n\t\t\tfound:",  type(obj.__dict__[p[0]]) )
        if printOpt:
            print(printOpt," for:", p)

#
#            ----------------------------------------
#			Debug state / Print state
#            ++++++++++++++++++++++++++++++++++++++++
#


class DebugState(SingletonBase):
    """ This is a singleton class
    """    
    def __init__(self, doPrint=False, abortRemaining=None):
        SingletonBase.__init__(self)
        self.doPrint = doPrint
        self.abortRemaining = abortRemaining

    def abortCount(self):
            """
               Count abort events, when self.abortRemaining is a number, decrement,
               returns True when abort count exceeded (must stop, probably via sys.exit())
            """
            if self.abortRemaining != None:
                self.abortRemaining -= 1
                return self.abortRemaining <= 0
            return False
                
#
#            ----------------------------------------
#			Low level .....
#            ++++++++++++++++++++++++++++++++++++++++
#

def addKwdDict(fromKws, key, default={}):
        if (not key in fromKws):
            return default.copy()
        else:
            return fromKws[key]

#
#            ----------------------------------------
#			Model versioning
#            ++++++++++++++++++++++++++++++++++++++++
#
class FeatureStrat(Enum):
    """
     This Enum is used to describe the level of sophistication in the Features selected
     or constructed. This caracterises the model. It has been put here since multiple
     files and notebooks may refer to this
    """
    NoMod      = 0             # keep data tables as they are
    SimpleMod  = 2             # simple mods (started here)
    MoreMod    = 4
    MoreModA   = 5        
    MoreModB   = 6        
    MoreModC   = 7        
    MoreModD   = 8
    MoreModE   = 9
    MoreModF   = 10
    MoreModG   = 11
    MoreModH   = 12
    MoreModI   = 14
    MoreModJ   = 15
    
    FullMod    = 20
    # These are really for convenience
    def __lt__(self,b):
        return self.value < b.value
    def __le__(self,b):
        return self.value <= b.value
    def __gt__(self,b):
        return self.value > b.value
    def __ge__(self,b):
        return self.value >= b.value
    def __eq__(self,b):
        return self.value == b.value
    def __ne__(self,b):
        return self.value != b.value


#
#            ------------------------------------------------------------
#			Collecting information about data utilisation
#            ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
#

class DataUtilizationMgr(object):
    """
        This class facilitates keeping track on how the data was utilised,
        this is intended to facilitate managing data to avoid unneeded dependencies
    """

    def __init__(self):
        """ Internally the data is kept in the following way:
            key = identifying string
                = data = list of dict with keys
                            - var : string name of originating variable 
                                   (or possibly csv file  name)
			    - 
			    - shape :  shape of full var
                            - cols: if exists and non void: columns were restricted in this
        			    utilisation, contains a list of columns. 
			    - mask: row mask or series mask
        """
        self.__dict = {}
        self.elisionLim = 30


    def add(self, key, **kwargs):
        """ Enter a key and the corresponding data dict
        """
        if key in self.__dict:
            self.__dict[key].append(kwargs) 
        else:
            self.__dict[key] = [kwargs,]

        
    def __setitem__(self,key,kwDict):
        """ Syntactic helper for method 'add'
        """
        self.add(key,**kwDict)


    def __str__(self):
        """ Emit the string representation of the entire information, ready
            to be printed with "\n" and "\t".
            The key "mask" gets a special treatment: conversion to binary and 
            elision in accordance with object variable self.elisionLim
        """
        ll = []
        for k in sorted(self.__dict.keys()):
          cl = [str(k),"\t->\t"]
          first = True
          for el in (self.__dict[k]):
              if not first:
                  cl.append("\t\t")
              else:
                  first=False
              cl.append(self.__str(el))
              cl.append("\n")
          cl.append("\n")
          ll.append("".join(cl))
        return "".join(ll)

    def __str(self, eldict):
        cl = []
        for k in sorted( eldict.keys() ):
            if k != "mask":
                cl.append( str(k)+ "=" + self.elide(str(eldict[k])))
            else:
               tfs = eldict[k]
               ltfs = len(tfs)
               if (ltfs > self.elisionLim):
                  nc = int((self.elisionLim-3)/2)
                  p1 = (self.elisionLim-3) % 2
                  cl.append( str(k)+ "=" +fmtTrueFalse(tfs[:nc+p1]) + "."*3 +
                                          fmtTrueFalse(tfs[ltfs-nc:])) 
               else:
                   cl.append( str(k) + "=" +  fmtTrueFalse(tfs))
        return ":  " + str.join(",\t", cl  )


    def elide(self, s):
        """ Perform string elision
        """
        ls = len(s)
        if ls > self.elisionLim:
            nc = int((self.elisionLim-3)/2)
            p1 = (self.elisionLim-3) % 2
            return s[:nc+p1] + "."*3 + s[ls-nc:]
        return s


       
def fmtTrueFalse(v):
     "Utility function for method __str"
     def fn(a):
         if a :
             return "1"
         else:
             return "0"

     return "".join(map(fn, v))

    
