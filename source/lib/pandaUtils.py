"""
   Facilitate my usage of Pandas

   Preferred the Python library's warning to the deprecation decorator
   https://stackoverflow.com/questions/2536307/decorators-in-the-python-standard-lib-deprecated-specifically
   For library's version https://docs.python.org/3.6/library/warnings.html#warnings.warn
"""

__author__ = 'Alain Lichnewsky'
__license__ = 'MIT License'
__version__ = '1.0'


import sys
import warnings                    # look at 
import pandas as PAN

# we use IPython's display function
from IPython.display import display, HTML
from IPython import get_ipython

def deprecation(message):
    warnings.warn(message, DeprecationWarning, stacklevel=1)

def rowMatch(df, col,rex,addedSpec="(?i)"):
    """
       Select rows in a DataFrame using a regular expression as mask. The 
       difficulty is that we may need to work with NA/NaN which are not
       allowed in masks
    """
    msk = df[col].str.contains(rex+addedSpec)
    try:
       ret = df[msk]
    except Exception as err:
        # print(f"got into exception  {err}, type(msk) ={type(msk)}")
        # display(msk)
        msk[msk.isna()]=False
        ret = df[msk]
    return ret

def selmask(df, col, rex,addedSpec="(?i)"):
    """
     Same as rowMatch, deprecated!
    """
    deprecation("I changed my mind")
    sm=rowMatch(df, col,rex,addedSpec= addedSpec)
    return sm

def showMatch(df, col,rex, maxr=400):
    """
       Display the result of rowMatch
    """
    s = rowMatch(df, col, rex)
    print(s.shape)
    display(s[:maxr])

def prMatch(df, col,rex, l=150):
    """
       Print the result of rowMatch
    """
    q = rowMatch(df, col,rex)
    print(q.shape)
    for v in q.loc[:,col]:
        print(v[:l])

class DfMatcher(object):
        """ For utilisation examples, see the test section at the bottom
        """
        def __init__(self,df):
            self.df = df
            
        def selmask(self, col,rex,addedSpec="(?i)"):
            return selmask(self.df, col,rex,addedSpec=addedSpec)

        def rowMatch(self, col, rex,addedSpec="(?i)"):
            return rowMatch(self.df, col, rex,addedSpec=addedSpec)
            
        def showMatch(self, col,rex, maxr=400):
             return showMatch(self.df, col,rex, maxr=maxr)

        def prMatch(self, col,rex, l=150):
             return prMatch(self.df, col,rex, l=l)

def DFIndexDaysElapsed( df, newDteCol="dteStr", format='%Y-%m-%d'):
    """ Given a DataFrame df, where the index is a date represented as strings
        with given format, reindex df with days elapsed since the date in the
        first row. The original index, in string form, is moved to the
        column indicated in argument newDteCol.

        The DataFrame is modified in place, the function returns None
    """
    origIndex = df.index
    dt = PAN.to_datetime( df.index, format=format )
    elapsedDays =   dt - dt[0]
    df.index =  elapsedDays.days
    df.loc[ : , newDteCol] = origIndex


def sortedColIds(df,col):
    """ Given a dataframe and a column name, which should contain string ids,
        it returns the  sorted list of unique values in that column. 

        Useful in preparation for moving these values to index/colname. 
    """
    t = df.loc[:,col].unique()
    return sorted([ x  for x in t if isinstance(x, str) ])

    
if __name__ == "__main__":
    import unittest
    import sys
    import numpy as NP

    class PandaTest(unittest.TestCase):
        randseed=0
        def mkDwithNAN(option=0):
            """ Make a dataframe of strings with some proportion of Nans for
                testing purposes
            """
            ### pandas.DataFrame.apply: returns a <class 'pandas.core.series.Series'>
            ###                         w/o .info method etc
            ### Therefore applymap is used
            def strOrNan(x):
                if x < -0.5:
                    return NP.nan
                else:
                    return str(x)
                
            PandaTest.randseed=981  # make output deterministic

            def myRandom():
                "This is my deterministic random function, good enough for generating test"
                PandaTest.randseed = (PandaTest.randseed+320)%1024
                return float(PandaTest.randseed)/512 - 1.0

            array = [ myRandom() for i in range(0,15)]
            npA   = NP.array(array).reshape((5,3))
            df = PAN.DataFrame( npA,
                                index=['a', 'c', 'e', 'f', 'h'],
                                columns=['one', 'two', 'three']
                                )
            if option == 1 :
               dfr1 = df.reindex(['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h'])
               dfr = dfr1.applymap(strOrNan)
               # print( f"\nReindexed Dataframe dfr built for test:\n{type(dfr)}\n{dfr}\n")
               return dfr
                 
            df  = df.applymap(strOrNan)

            if False:
              print( f"\nDataframe df built for test:\n{type(df)}\n{df}\n")
              print(f"\ndf (str applymapped) (type:{type(df)}):")
              df.info()            

              print( f"\nNA distribution:\n{df.isna()}\n")
              print( f"\n mkDwithNAN Returning df (all transformations in place)")
            
            return df

        
        def test_1(self):
            print("\n**\tTest 1")
            dfm =  DfMatcher( PandaTest.mkDwithNAN())
            x = dfm.df.loc[:,'two']

            r = dfm.selmask("two","[.][1-4]")
            self.assertEqual(r.iloc[0,0],"-0.458984375")
            self.assertTrue( (r.index == ["a","f","h"]).all() )
            r = dfm.selmask("two","^-")
            self.assertTrue( (r.index == ["e","f","h"]).all() )

            
            r = dfm.rowMatch("two","[.][1-4]")
            self.assertTrue( (r.index == ["a","f","h"]).all() )
            r = dfm.rowMatch("two","^-")
            self.assertTrue( (r.index == ["e","f","h"]).all() )

            dfm.prMatch("two","[.][1-4]")
            dfm.showMatch("two","[.][1-4]")

        def test_1r(self):
            print("\n**\tTest 1r")
            dfm =  DfMatcher( PandaTest.mkDwithNAN(option=1))
            dfm.df.info()

            r = dfm.selmask("two","[.][1-4]")
            self.assertEqual(r.iloc[0,0],"-0.458984375")
            self.assertTrue( (r.index == ["a","f","h"]).all() )
            r = dfm.selmask("two","^-")
            self.assertTrue( (r.index == ["e","f","h"]).all() )


            r = dfm.rowMatch("two","[.][1-4]")
            self.assertEqual(r.iloc[0,0],"-0.458984375")
            self.assertTrue( (r.index == ["a","f","h"]).all() )

            r = dfm.rowMatch("two","^-")
            self.assertTrue( (r.index == ["e","f","h"]).all() )

            dfm.prMatch("two","[.][1-4]")
            dfm.showMatch("two","[.][1-4]")

            #  Composition
            c=DfMatcher(dfm.rowMatch("two","[.][1-4]")).rowMatch("one",".*")
            d=DfMatcher(dfm.rowMatch("two","[.][1-4]")).rowMatch("three","9.*15")
            self.assertTrue(c.loc["a","one"], '-0.458984375')
            self.assertTrue(d.loc["h","three"], '0.291015625')
            
    unittest.main()
    """ To run specific test use unittest cmd line syntax, eg.:
           python3  <pythonfile>.py   PandaTest.<TestMethod>
    """
        
