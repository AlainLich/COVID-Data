# coding: utf-8

__author__ = 'Alain Lichnewsky'
__license__ = 'MIT License'
__version__ = '1.0'

# (C) A.Lichnewsky, 2018, 2020
#
# To support both python 2 and python 3
# from __future__ import division, print_function, unicode_literals

#  My own library organization (TBD: clean up ?)
import sys
import traceback
sys.path.append("pylib")
from UnitTest import *

# Common toolkit imports
import numpy             as 	NP
import numpy.random      as 	RAND
import scipy.stats       as 	STATS
from   scipy             import sparse
from   scipy             import linalg

# Using scikit-learn
import sklearn                                 as SKL
from sklearn import linear_model,  model_selection
from sklearn import ensemble, tree, discriminant_analysis, svm, naive_bayes
from sklearn import	neighbors
from sklearn.preprocessing import StandardScaler, LabelEncoder, OneHotEncoder

# Using pandas
import pandas 		 as 	PAN

# To plot pretty figures
import matplotlib        as 	MPL
import matplotlib.pyplot as 	PLT
import seaborn 		 as 	SNS


# Python programming
from itertools import cycle
import time as   TIME
from time import time
from enum import Enum
from  string import ascii_uppercase


import basicUtils as BU
from IPython.display import display
from basicDataCTE import dataModel
import  basicDataCTE 
import basicUtils       as    BU




#
#            ----------------------------------------
#			TEST FUNCTIONS
#            ++++++++++++++++++++++++++++++++++++++++
#

#
#
#            ----------------------------------------
#			TEST of Dataframe normalization functions
#            ++++++++++++++++++++++++++++++++++++++++
#
def test1():
    tframe = PAN.DataFrame([
        [12, True,  "aa",    "large" , 12.0 ],
        [1,  True,  "ab",    "large",  NP.NaN],
        [10, False, NP.NaN,  "avg",    34],
        [20, True,  12,      "avg",    -1],
        [21, True,  12,      "large",  NP.NaN],
        [22, True,  12,      "avg",    -23],
    ],
        columns=("vals", "truth", "mixed", "style", "valNAN")                  
    )

    print("Test data frame:")
    print(tframe)
    print("\nTest data frame info:")
    tframe.info()
    print("\nTest data frame (verbose) info:")
    tframe.info(verbose=True, memory_usage='deep', null_counts=True)
        
    print("\nDescription:")
    print(tframe.describe(include='all', percentiles= ( 0.5, 1)))
    
    print("\nDisplay:")
    display(tframe)


#            ----------------------------------------
#		Check multiple masking in views
#

    display(tframe.loc[:,"mixed"])
    mask1 =  tframe.loc[:,"mixed"].notna() 
    display(mask1)

    print("after droping all nas")
    tframe1 = tframe.dropna(axis="index")
    display(tframe1)
    print("after droping nas in col mixed and valNAN")
    tframe1 = tframe.dropna(axis="index", subset=("mixed","valNAN"))
    display(tframe1)
    print("after sequential droping nas in col mixed and valNAN")
    tframe1 = tframe.copy()
    tframe1.dropna(axis="index", subset=("valNAN",), inplace=True)
    tframe1.dropna(axis="index", subset=("mixed",), inplace=True)
    display(tframe1)
    print("Check that original frame not affected")
    display(tframe)
    
    
#            ----------------------------------------
#		Back to testing
#
    
    print("\nPresenting in a dataModel:")
    myModel = dataModel(tframe)
    myModel.showNulls()

    print("\nNormalizing")
    print("\nKeep 3 rows, 2 cols")

    myModel.normalize(rowsMask=NP.array([True, True, False, False, False, True]),
                      cols=("truth","mixed"))
    myModel.DFApply(print)
 
    print("\nKeep all rows, 2 cols")
    myModel.normalize( cols=("truth","mixed"), colNorm={"truth": {} })
    myModel.DFApply(print)

    print("\nKeep all rows, all cols")
    myModel.normalize( colNorm={ "truth": {"OneHot"  : True,
                                           "ColInsert":("NEW-Truth-1","NEW-Truth-2")  },
                                 "style": {"Category": True, "InPlace" : False  ,
                                           "ColInsert":"NEW-Style",
                                           "values": ("large","avg","small","bizar","zarbi")},
                                 "vals":  {"MeanVar" : True, "ColInsert":"NEW-Vals"},
                                 "mixed": {"MissingInput": {"dropNA"  : True,
                                                            "InPlace" : True}},
                                 "valNAN": {"MissingInput": {"avgNA"  : True,
                                                            "InPlace" : True}}
    })
    myModel.DFApply(print, which=dataModel.DM.NORM)

    myModel.normalize( add=True, colNorm={
                              "NEW-Style": {
                                  "OneHot"  : True,
                                  "ColInsert":("NEW-Style-1","NEW-Style-2","NEW-Style-3"),
                                  "values":(0,1,2)
                          }})
    myModel.DFApply(print, which=dataModel.DM.NORM)
    
    
    print("\nTackle NaNs")
    myModel.normalize( cols=("vals","valNAN"),
                       colNorm={"vals":{ "MeanVar" : True,
                                         "ColInsert":"NEW-Vals"},
    				"valNAN" :{ "MissingInput": {"dropNA"  : True,
                                                             "InPlace" : True},
                                            "MeanVar" : True,
                                            "ColInsert":"NEW-Vals"}
                		})

    print("Normalisaton by applying a user provided function")
    def see(*args,**kwargs):
        " This function allows to understand how it is called... "
        print("In function see, args=", args,"\ttype(args)=",type(args),
              "\tkwargs=",**kwargs)
        return [ str(x)[0] for x in args[0]]

    def seemap( *args,**kwargs):
        " This function allows to understand how it is called... "
        print("In function seemap, args=", args,"\ttype(args)=",type(args),
              "\tkwargs=",**kwargs)
        return  str(args[0])[0]

    def seemap2( arg,**kwargs):
        " This function has a single argument, simpler to use in practice "
        print("In function seemap2, arg=", arg,"\ttype(arg)=",type(arg),
              "\tkwargs=",**kwargs)
        return  str(arg)[0]

    myModel.normalize( colNorm={ "mixed": {"Apply":seemap2,
                                           "Map": True,
                                           "ColInsert":"NEW-mixed"},
                                  "style": {"Apply":see,
                                           "ColInsert":"NEW-style"}
        })
        
    print("Original dataframe")
    myModel.DFApply(print)
    print("Normalized dataframe")
    myModel.DFApply(print, which = dataModel.DM.NORM)

    myModel.normalize( colNorm={ "mixed": {"Apply":seemap,
                                           "Map": True,
                                           "ColInsert":"NEW-mixed"},
                                  "style": {"Apply":see,
                                           "ColInsert":"NEW-style"}
        })
    print("Normalized dataframe")
    myModel.DFApply(print, which = dataModel.DM.NORM)
    
    
    
    print(id (myModel.getFrame()))
    print(id (myModel.getFrame(which= dataModel.DM.NORM)))
    print(id (myModel.getFrame(copy=True)))
    print(id (myModel.getFrame(which= dataModel.DM.NORM,copy=True )))

    print(id (myModel.getFrame()))
    print(id (myModel.getFrame(which= dataModel.DM.NORM)))
    print(id (myModel.getFrame(copy=True)))
    print(id (myModel.getFrame(which= dataModel.DM.NORM,copy=True )))

#            ----------------------------------------
#		Check multiple masking in views
#

    mask1 =  tframe["mixed"] == NP.NaN
    tframe1 = tframe[~mask1]
    display(tframe1)

#
#		Experiment with FunctionTransformer:
#			..... not very useful as far as I understand
# 

    from sklearn.preprocessing import FunctionTransformer
    def see(*args,**kwargs):
        print("In function see, args=", *args, "\tkwargs=",**kwargs)
        return 1
    
    transformer = FunctionTransformer(see)
    r = transformer.transform(tframe.loc[:,["vals","truth"]])
    print(r)

#
#               Outlier detection
#
    N=5
    M=10
    zmat = PAN.DataFrame(NP.ones((M,N)))
    zmat.loc[0,3] = 10000
    zmat.loc[2,1] = 10000
    zmat.loc[2,0] = 10000
    zmat.loc[8,2] = 20000
    zmat.loc[8,4] = 20000
    zmat.loc[8,3] = 20000
    zmat.loc[M-1,N-1] = 30000
    zframe =dataModel( zmat)
    print(zframe.getFrame().shape)
    display(zframe)
    display(zframe.outlier_detect())
    display(zframe.outlier_detect(showCols=True))
    display(zframe.outlier_detect(showCols=True,cols=(2,3,4)))
    
    display(zframe.outlierLocate(n=4,showCols=True,cols=(2,3,4)))



#
#            ----------------------------------------
#			TEST Frame
#            ++++++++++++++++++++++++++++++++++++++++
#
class SMTestCase(ALTestFrame):
        def runTest(self):
            print ("IN runTest")
            #executes any member which name starts with test, don't bother
            #calling

        def testOK(self):
            ltest = (testInOut( ()   , out=None ),
            )
            self.applyTestList(ltest,  test1,redirect=True)

        def testFail(self):
            ltest = (
                testInOut( ()   , out=(), exception=TypeError),
            )
            self.applyTestListFail(ltest,
                                   1,
                                   redirect=True)
            
#
#            ----------------------------------------
#			LAUNCHING TESTS 
#            ++++++++++++++++++++++++++++++++++++++++
#

if __name__ == '__main__':

    print ("Launching test with unittest package/framework")
    r= unittest.main()
    print ("RESULT=", r)

