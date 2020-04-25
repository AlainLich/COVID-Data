# coding: utf-8

__author__ = 'Alain Lichnewsky'
__license__ = 'MIT License'
__version__ = '1.0'

# (C) A.Lichnewsky, 2018, 2020
#

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
import basicDataCTE     as    BCTE
import basicUtils       as    BU
import lib.utilities    as    LIBU



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
class  DModelTest(ALTestFrame):
        def runTest(self):
            print ("IN DModelTest")
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
            

class GraphicTest(ALTestFrameGraphics):
    """ Here we perform test of Seaborn features and of functions derived from
                them; many tests inspired from Seaborn manual
    """
    def start(self):
        args = {}
        if "--wait" in arguments:
           print(f"arguments={arguments}")
           if "--wait" in arguments and  (arguments["--wait"] is not None ):
               args["pause"] =  int(arguments["--wait"])
           self._start(**args)
           
    def mkDF(addCat=None,**kwargs):
            """ Make a dataframe of floats
            """

            print(f'In mkDF arguments:{arguments}')

            ### pandas.DataFrame.apply: returns a <class 'pandas.core.series.Series'>
            ###                         w/o .info method etc
            ### Therefore applymap is used
            def strOrNan(x):
                if x < -0.5:
                    return NP.nan
                else:
                    return str(x)
                
            GraphicTest.randseed=981  # make output deterministic
            def myRandom():
                "This is my deterministic random function, good enough for generating test"
                GraphicTest.randseed = (GraphicTest.randseed+320)%1024
                return float(GraphicTest.randseed)/512 - 1.0
            od = {}
            LIBU.setDefaults(od, optDict=kwargs, defaultDict={'nc' : 5, 'nl':8,
                                                              'ai':1,'brand':0.1 })
            nc,nl,ai,brand = list(map(lambda x: od[x], ("nc","nl","ai","brand")))
            print(f"parms = {nc,nl,ai,brand}")
            print(od)
            array = [ ai*i + brand * myRandom() for i in range(0,nc*nl)]
            npA   = NP.array(array).reshape((nl,nc))
            df = PAN.DataFrame( npA,
                                index  = [ f"row{i:03}" for i in range(1,nl+1)],
                                columns= [ f"col{i:03}" for i in range(1,nc+1)]
                                )
            if addCat:
                 print("Miaou  (Meow ! )")
                 if "modulo" in kwargs and kwargs["modulo"]:
                      imod= kwargs["modulo"]
                      df.loc[:,"catCol"] = [ f"Meow{(i%imod):03}" for i in range(1,nl+1)]
                 else:
                      df.loc[:,"catCol"] = [ f"Meow{i:03}" for i in range(1,nl+1)]

                 if "modulo" in kwargs and kwargs["modulo"]:
                      imod= kwargs["modulo"]
                      df.loc["catRow",:nc] = [ f"Miaou{(i%imod):03}" for i in range(1,nc+1)]
                 else:
                      df.loc["catRow",:nc] = [ f"Miaou{i:03}" for i in range(1,nc+1)]
                 df.iloc[-1,-1] = "MIA-MEOW"
            return df

    def test_DF(self):
        self.start()
        df =  GraphicTest.mkDF(False, nl=30, ai=0.02, brand=1, modulo=4)
        print(f"test_DF\ndf={df}")
        df.info()


        # makes a figure with a subplot for each column showing an histogram of the column
        # here it is important that all values are numerical 
        df.hist(bins=5,figsize=(10,8),grid=False)
        self.show()
        
        self.start()

        # here we make a dataframe with categorical data
        df =  GraphicTest.mkDF(True, nl=30, ai=0.02, brand=1, modulo=4)

        # add a second categorical column
        df.loc[:,"modCol"]=  df.iloc[:-1,:].loc[:,"col001"].apply (lambda x: int(2.78*x) % 3)
        df.iloc[-1,-1]  =  "Added!"
        df1 = df.iloc[:-1,:]
        # plot a grid of histograms based on the 2 categorical cols of data in col001
        g = SNS.FacetGrid(df1, col="catCol", row="modCol", margin_titles=True)
        g.map(PLT.hist, "col001", color="green", bins=3, density=True);
        

        # plot a grid of scatter plots based on the 2 categorical cols of data in col001
        # could add hue and changing markers..
        g = SNS.FacetGrid(df1, col="catCol", row="modCol",  margin_titles=True)
        g.map(PLT.scatter, "col001", "col002", color="green");
        
        self.show()
        self._setAdd("SNS.FacetGrid","PLT.hist","PLT.scatter","PAN.DataFrame.hist")

    def test_DF1(self):
        self.start()
        # here we make a dataframe with categorical data
        df =  GraphicTest.mkDF(True, nl=30, ai=0.02, brand=1, modulo=4)
        # add a second categorical column
        df.loc[:,"modCol"]=  df.iloc[:-1,:].loc[:,"col001"]\
                                           .apply (lambda x: int(2.78*x) % 3)
        df.iloc[-1,-1]  =  "Added!"
        df1 = df.iloc[:-1,:]
        print(df1)
        df1.info()
        df1.describe()


        # Still find it difficult to understand what I have got:
        SNS.set(font_scale=1)
        g = SNS.catplot(x="col001", y="col002", col="catCol",
                    data=df1, saturation=.5,
                    kind="bar", ci=None, aspect=.6)
        ( g.set_axis_labels("", "Cat Col lab")
           .set_xticklabels(["Cats", "Chats"])
           .set_titles("{col_name} {col_var}")
           .set(ylim=(0, 1))
          .despine(left=True))  
        PLT.subplots_adjust(top=0.8)
        g.fig.suptitle('How a test was made up');

        self.show()
        self._setAdd("SNS.set", "SNS.catplot", "PLT.subplots_adjust")

    def test_1(self):
        self.start()
        df =  GraphicTest.mkDF()
        print(f"test_1\ndf={df}")
        df.info()
        PLT.figure()
        SNS.boxplot(df)

        PLT.figure()
        SNS.boxplot(x=df.loc["row002"])

        PLT.figure()
        SNS.boxplot(y=df.loc[:,["col003", "col001"]])

        PLT.figure()
        SNS.boxplot(x=df)

        PLT.figure()
        SNS.boxplot(y=df)

        self.show()

        # This does not look great!
        BCTE.doBoxPlots( df, ycols = ["col003", "col001"], xcols=["col002","col004"],
                         stripIt=True)
        self.show()

        self._setAdd("SNS.boxplot", "BCTE.doBoxPlots")
        
        
    def test_2(self):
        self._start()
        df =  GraphicTest.mkDF(True)
        print(f"test_2\ndf={df}")
        df.info()
        PLT.figure()
        ## make boxplots based on columns
        SNS.boxplot(data=df.iloc[:-1,:])
        self.show()
        
        self._setAdd("SNS.boxplot")

    @unittest.expectedFailure
    def test_2F(self):
        # same as   test_2, shows failure when there are non numerical data in column!
        self._start()
        df =  GraphicTest.mkDF(True)
        print(f"test_2\ndf={df}")
        df.info()
        PLT.figure()
        ## make boxplots based on columns
        SNS.boxplot(data=df)
        ## make boxplots based on lines (transpose)
        PLT.figure()
        SNS.boxplot(data=df.drop('catCol',axis=1).transpose())
        self.show()
        
        self._setAdd("SNS.boxplot")
        
        


    def test_3(self):
        self._start()
        df =  GraphicTest.mkDF(False)
        print(f"test_3\ndf={df}")
        df.info()

        snsDtl={"SNSBox+":{"xtickLabels":{"rotation":45}},
                "SNSStrip+":{"xtickLabels":{"rotation":45}}}
        PLT.figure()
        BCTE.boxStripPlot(data=df,x=None,y="col001",
                          title="Single box and pts, vertical")

        PLT.figure()
        BCTE.boxStripPlot(data=df,x="col002",y=None,
                          title="Single box and pts, horizontal")

        PLT.figure()
        BCTE.boxStripPlot(data=df,x=None,y=None,
                          title="Looks OK with boxes and points", **snsDtl)
        self.show()
        self._setAdd("BCTE.boxStripPlot")

        
    def test_4(self):
        self._start()
        df =  GraphicTest.mkDF(True, multiple=True)
        print(f"test_4\ndf={df}")
        df.info()

        BCTE. densityCatPlot(data=df,x=[f"col{i:03}" for i in range(1,6)], cats="catCol",
                             title = "Title",
                             legend = ("legend1", "legend2","legend3"))
        self.show()

        # Now, this tests the seaborn version, the following gives a 2D density
        #      https://seaborn.pydata.org/generated/seaborn.kdeplot.html
        SNS.kdeplot(df.iloc[:,0:2])

        self.show()
        self._setAdd("BCTE. densityCatPlot", "SNS.kdeplot")
        
#
#            ----------------------------------------
#			LAUNCHING TESTS 
#            ++++++++++++++++++++++++++++++++++++++++
#

__cmdspecs__  = """"
       testDataCTE : run tests under unittest environment

Usage: tesDataCTE  [ <testcase> ] [ --wait=<wait> ] [ --parm=<parm>]

Options:
     --parm=<parm>           pass parameter
     --wait=<wait>           pass parameter

     Here testcase is the optional testcase in the form of <class> or <class>.<method> 
     Please use the form --parm val   and NOT --parm=val
"""

from docopt import docopt

if __name__ == '__main__':
    # analyze command line args 
    arguments = docopt(__cmdspecs__)
    ALTestFrameGraphics.processDocoptArgs(arguments)
    
    # Now we need to remove docopt argv arguments which unittest.main() cannot handle 
    print ("Launching test with unittest package/framework")
    r= unittest.main()
    print ("RESULT=", r)


#            ----------------------------------------
#			Specializing tests
#            ++++++++++++++++++++++++++++++++++++++++
#
#   Use syntax:   <python>|<script>   <class>[.<method>]
#      eg.
#         python3 ../source/lib/testDataCTE.py  GraphicTest.test_boxplot
#
