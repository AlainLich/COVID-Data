'''
Setup some utilities, very much related to our project of displaying figures
in Jupyter. 
'''

__author__ = 'Alain Lichnewsky'
__license__ = 'MIT License'
__version__ = '1.0'

# Sys import
import sys, os, re

# Python programming
from itertools import cycle
import time
import datetime
from   enum import Enum, IntFlag
from collections.abc import Iterable 

# Better formatting functions
from IPython.display import display, HTML

import warnings
warnings.filterwarnings('ignore')
print("For now, reduce python warnings, I will look into this later")

#using Matplotlib
import matplotlib        as MPL
import matplotlib.pyplot as PLT
import seaborn as SNS
SNS.set(font_scale=1)

# Using pandas
import pandas as PAN


class ImageMgr(object): 
    """ Ensures that the current image from matplotlib is stored in the appropriate
        per chapter subdirectory.

        usage: example:
               ImgMgr = ImageMgr(chapdir="Chap01"

    """
    def __init__(self, rootdir=".", chapdir="DefaultChap", imgtype="jpg"):
       
         self.project_root_dir = rootdir
         self.chapter_id=chapdir
         self.imgtype="."+imgtype
            
    def save_fig(self, fig_id, tight_layout=True):
       "Save the current figure"
       path = os.path.join(self.project_root_dir, "images", self.chapter_id, fig_id + self.imgtype)
       print("Saving figure", fig_id)
       if tight_layout:
          PLT.tight_layout()
       PLT.savefig(path, format='png', dpi=300)


# ## Check environment
# 
# It is expected that your working directory is named `JupySessions`, that it has
# subdirectories `images/*` where generated images may be stored to avoid overcrowding.
# At the same level as your working dir there should be directories
#   `../data` for storing input data and `../source` for python scripts, libraries,...
       
def checkSetup(chap = None):
    """
       Verifies that subdirectories are correctly positionned wrt. working dir 

       usage: example : checkSetup(chap="Chap01")
    """
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


def read_csvPandas(fname,clearNaN=False, **kwargs):
    """ Read a csv file, all keywords arguments permitted for pandas.read_csv 
        will be honored
    """
    df = PAN.read_csv(fname,**kwargs)
    if clearNaN:
        return df.dropna(how="all").dropna(axis=1)
    return df



def read_xlsxPandas(fname,clearNaN=False, **kwargs):
    """ Read a xlsx file, all keywords arguments permitted for pandas.read_csv 
        will be honored
    """
    df = PAN.read_excel(fname,**kwargs)
    if clearNaN:
        return df.dropna(how="all").dropna(axis=1)
    return df



def setDefaults(dict, optDict={}, defaultDict={}, tryDictKey=None):
    """
        Operates on dictionnaries; fills dict with optDict contents, adding defaults
        from defaultDict when absent

        If used, tryDictKey is expected to be a tuple (key,dd); if key is found 
        in dd (type==dict), then dd[key] is used as a dictionnary to fill dict; 
        otherwise this argument is ignored.
        optDict elements override  tryDictKey

        Examples are located in the test section at the end.
    """
    if tryDictKey is not None:
        dk,dd = tryDictKey
        if dk in dd:
             for (k,v) in dd[dk].items(): 
               dict[k] = v
    for (k,v) in optDict.items(): 
        dict[k] = v
    for  (k,v) in defaultDict.items():
        if k not in dict:
            dict[k] = v

def isclass(obj):
    """Return true if the object is a class.
    """
    return isinstance(obj, type)

def setOfSubClasses(obj):
   """ return the subclasses of a class or from the class of an instance
   """
   def subClassSet(cls):
       rSet = set( (cls,) )
       for c in cls.__subclasses__():
           rSet = rSet.union(subClassSet(c))
       return rSet

   if isclass(obj):
          return  subClassSet(obj)
   else:
          return  subClassSet(obj.__class__)

def checkDefaultCompat(cls):
    if not isclass(cls):
          cls = cls.__class__

    def checkCompat(cls, sublist):
        retval = True
        if hasattr(cls, "defaultOpts"):
          clsKeys=set(cls.defaultOpts.keys())
          for sub in sublist:
               if hasattr(sub, "defaultOpts"):
                  inter = clsKeys & set(sub.defaultOpts.keys())
                  if len(inter)>0:
                      print("Default opts of base and derived classes intersect ")
                      print(f"\tBase={cls} Derived={sub} \n\t intersection:{inter}")
                  retval = False
        return retval

    for sub in setOfSubClasses(cls).union((cls,)):
       propersub = setOfSubClasses(sub)-set((sub,)) 
       print(f"Check compat {sub} with {propersub}")
       return checkCompat(sub,propersub)
       
def spaceUsed(dirpath):
    """ Compute the used space by all files in directory, does not care about symlinks
        and links causing files to be counted several times. Size of directory entries
        proper not counted either.
    """
    used = 0
    for entry in os.scandir(dirpath):
        if entry.is_file():
            stat_result = entry.stat()
            used +=  stat_result.st_size
        elif entry.is_dir():
            used +=  spaceUsed(entry.path)
    return used


class rexTuple(object):
     """
         Used to encapsulate regexp, or set regexp as described in  _pprintDataItem:

         Item syntax is <field>('/'<field>)+, where each field is either a
              plain string, a regular expression for module `re` or a set of
              regular expressions
              - a set of (generalized) regular expressions corresponds to the syntax 
                <strOrRe>$$<strOrRe>[$$<strOrRe>] where strOrRe can be either a
                plain string or a regexp
              - a regexp is recognized by including one of the characters '*+()'
              - '/' is reserved as a field separator, must not be used inside a field
              - a field which is not a regexp (ie. a plain string) will be matched using
                equality
              
              A)Item matches the first substructure accessed by a list of nested
                identifiers (eg. nested in the representation of a json structure) 
                where the first field matches the first identifier,... etc
              B)When a set delimited by '$$' is used:
                  i)  the first matches an item, if not found, we stop here
                  ii) the search at same level is performed for all items that match
                      the second item
                  iii) for each the value associated with each item in ii) is screened
                      with the third pattern.

     """
     class TypeRex(Enum):
         REXSTR    = 1
         REX       = 2

     class TypeTuple(IntFlag):
         MATCH      = 1
         MLINK      = 2
         MLINKCHECK = 4

     def __init__(self, reStr): 
         self.numRex = 0
         self.tryReSplitCompile(reStr)

     def _rexCat(self, rex):
         if isinstance(rex, str):
             return rexTuple.TypeRex.REXSTR
         else:
             return rexTuple.TypeRex.REX

     def __str__(self):
         r = f"<{type(self)}>: l={self.numRex}, {self.rexTypes}, {self.rexList}"
         return r

     ppItemRex = re.compile("[*+()]")
     def _tryReCompile(s):
          retval = s
          if  rexTuple.ppItemRex.search(s):
              try:
                retval =  re.compile(s)
              except Exception as err:
                  print(f"Rejected regexp:'{s}': {err}")
                  retval = s
          return retval

     def tryReSplitCompile(self, reStr):
            rexs =  reStr.split("$$")
            print (f"\twe need to re.compile:{rexs}")
            comp = map (rexTuple._tryReCompile  , rexs)
            self.rexList  = list(comp)
            self.rexTypes = list( map ( self._rexCat, self.rexList ))
            self.numRex   = len( self.rexList )


     def genMatch(self,st, tm = TypeTuple.MATCH):
         nrex = (tm-1)
         if nrex == 3 :
             nrex=2
         if nrex >= self.numRex:
             raise RuntimeError(f"Requested tm={tm} not compatible with rexvector len={len(self.rexList)}=={self.numRex}")

         rex = self.rexList[nrex]
         if isinstance(rex,str):
             return rex == st
         else:
             return rex.match(st)

def strElapsed(t):
    """ 
    Read a time duration in seconds, output a format : "xxh yym zzs" 
    Use in situations where time.strftime is not satisfactory (outputs output hours up to 
    24 and then need to go to day (offset by 1)
    """
    s = int(t) %60
    m = int(t/60) %60
    h = int(t/(60*60))
    return f"{h}h {m}m {s}s"
         
class rexTupleList(object):
    """ Encapsulate a list of rexTuple as representing a 'xxx/xxx/xx' expression
        as described above
    """
    def __init__(self, s):
        self.lstRex = list( map ( rexTuple, s.split("/")))

    def __getitem__(self,idx):
        return  self.lstRex[idx]

    def __len__(self):
        return len(self.lstRex)

    
def entryIsIterable(dict,entry):
    return isIterable(dict.get(entry))

def isIterable(e):
    """ Variant that excludes None, as well as (byte) strings""" 
    return ( e is not None
             and not isinstance(e,(str,bytes))
             and isinstance(e, Iterable)) 

def isList(e):
    """ Variant that excludes None, as well as (byte) strings""" 
    return ( e is not None
             and not isinstance(e,(str,bytes))
             and isinstance(e, list)) 
    
class listOrSingleIterator:
    """ return a generator:
           1) if obj is a real iterable (not a string): return iteratively elts
           2) if obj is None: stop iteration
           3) return obj and stop iterating thereafter
    """
    # ------------------------------------------------------------
    # Note: For implementing this within the yield/generator mechanism, see
    #        http://www.dabeaz.com/finalgenerator/FinalGenerator.pdf
    #
    #       Based on my measurements, this is twice as fast as the Old class
    # ------------------------------------------------------------
    def __init__(self, obj):
        self.obj = obj
        self.isIter = not isinstance(obj, (str, bytes, dict)) and isinstance(obj, Iterable)
        
        if self.isIter:
            def delegate():
                # Make a generator from the iterable
                yield from self.obj            
            self.iterator = delegate()
        else:
            self.isNone = self.obj is None
            
    def __iter__(self):
        return self
     
    def __next__(self):
        if self.isIter:
            return next(self.iterator)
        elif self.obj is None :
            pass
        elif not self.isNone:
            self.isNone =  True
            return self.obj

        raise StopIteration()

    
if __name__ == "__main__":
    import unittest
    import sys

    class TestDefaults(unittest.TestCase):

        def test1(self):
            d1  = {}
            d2  = {}
            d3  = {}
            d4  = {}
            opt1 = {1:1, 2:2}
            opt2= {1:1, 2:2, 'tyty':"ahhh"}
            default = {'tyty':'toto'}

            setDefaults(d1,opt1,default)
            self.assertEqual(d1, {1: 1, 2: 2, 'tyty': 'toto'} )
            setDefaults(d2,opt2,default)
            self.assertEqual(d2, {1: 1, 2: 2, 'tyty': 'ahhh'} )

            setDefaults(d3, tryDictKey=("opt", {"opt":{'tyty':'ohh'}}) )
            self.assertEqual(d3, {'tyty': 'ohh'} )
            setDefaults(d4, tryDictKey=("opt", {"opt":{'tyty':'ohh'}}),
                            optDict=opt2)
            self.assertEqual(d4, {'tyty': 'ahhh', 1:1, 2:2} )
            

    class TestTime(unittest.TestCase):

        def test1(self):
            nowtime = time.time()
            mtime   = os.path.getmtime("/usr")
            elapsed =  nowtime - mtime
            str1 = time.strftime("(%d days) %Hh %Mm %Ss", time.gmtime(elapsed))
            str2 = strElapsed(elapsed)
            print(f"elapsed={elapsed}\t str1={str1} str2={str2}")
            
    unittest.main()
    """ To run specific test use unittest cmd line syntax, eg.:
           python3 ../source/lib/utilities.py   DGTest.test_pprint

    """
