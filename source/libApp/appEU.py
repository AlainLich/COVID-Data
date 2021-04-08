# coding: utf-8

# (C) A.Lichnewsky, 2021

__author__ = 'Alain Lichnewsky'
__license__ = 'MIT License'
__version__ = '1.0'


#
#  These are classes for displaying graphics related to data from Europe
#
#            ----------------------------------------
 
# Common imports
import math
import numpy             as NP
import numpy.random      as RAND
import scipy.stats       as STATS
from scipy import sparse
from scipy import linalg

# Python programming
from itertools import cycle
from time import time
import datetime

# Using pandas
import pandas as PAN

from lib.pandaUtils    import *
from lib.utilities     import *
from lib.figureHelpers import subPlotShape, figureFromFrame
from lib.basicUtils    import toDict

#
# We need a specialization of figureFromFrame for handling time series, which is
# more ad-hoc than lib.figureHelpers.figureTSFromFrame, in order to handle available data
#

class  figureTSFromFrameEU(figureFromFrame):
    """Make a figure from a time series from a DataFrame; 
          it is expected that the row index are dates in string.
          These are converted into the elapsed days from start of table, and represented
          in DateTime format.
          Keywords listed in defaultOpts are honored; 
              keyword dateTranslate permits to iron out date format inconsistencies,
                      like when I found in loaded data an index:  
                      "..., '2020-06-28', '2020-06-29', '27/06/2020', '28/06/2020', ...".
    """
    defaultOpts = {"dateFmt":'%Y-%m-%d',
                   "dateTranslate": True}
    def __init__(self, df, **kwdOpts):
        figureFromFrame.__init__(self, df, **kwdOpts)
        setDefaults(self.optd, kwdOpts, figureTSFromFrameEU.defaultOpts)
    
    def  preparePlot(self):
        self._dtToElapsed()
    
    def _dtToElapsed(self):
        self.df.origIndex = self.df.index
        if False:
           print(f"self.df:\n\t.columns:{self.df.columns}\n\t.index:{self.df.index}")
    
        if self.optd["dateTranslate"]:
           trDates= list( map (  figureTSFromFrameEU._dateTranslator,  self.df.index ))
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
            mobj =  figureTSFromFrameEU. dateTranslatorRegexp.match(dte)
            if mobj:
               mg = mobj.groups()
               return mg[2] + "-" + mg[1] + "-" + mg[0] 
            else:
                return dte
        except Exception as err:
            print(f"Unable to translate date {type(dte)}{dte}", file=sys.stderr)
            raise err






# This must be a class, since now the optional argument "countryDataAdapter" of
# class "perCountryFigure" accepts an object with method "prepareDF", but which
# might be stateful.
class EUSiteData(object):
    def __init__(self):
        pass

    # Do NOT move, cols[3:6] are referenced by number below!!
    #
    _selCols = ['country_code', 'population', 'indicator',
                'weekly_count', 'rate_14_day', 'cumulative_count',
                'date']

    def prepareDF(self,dataFrame):
        """ 
           Restructure the dataframe to take into account input DF format
           after January 2021
             1) exploit the column indicator whith values ("cases","deaths")
                 to add relevant columns
             2) merge entries corresponding to same date and country
             3) keeps the dataFrame so that initPainter does not need to specify it

             4) more specificities are described in README-Data.md, in particular
                death rate_14_day is specified for 1.0E5 pop whereas cases for 1.0E6 pop.

             After normalization, all the "rate" values we return are rates by day and 
             1.0E6 population; similarly cumulative rates "cumrate" are for 1.0E6 pop.
        """
        #print( f"dataFrame.columns={dataFrame.columns}", file=sys.stderr )
        dfExtract = dataFrame.set_index("elapsedDays").copy()
        
        #print(f"values in col indicator:"+str(sortedColIds(dfExtract,"indicator")))
        selcase=dfExtract.loc[:,"indicator"]=="cases"
        seldeath=dfExtract.loc[:,"indicator"]=="deaths"
        sub1 = dfExtract.loc[selcase,:]
        sub2 = dfExtract.loc[seldeath,:]
        
        selCols = EUSiteData._selCols             
        sub1 = sub1.loc[:,selCols].copy()
        sub2 = sub2.loc[:,selCols].copy()

        cols = selCols.copy()
        cols[3:6]=("cases","caserate","casescum" )
        sub1.columns=cols
        sub1.loc[:,"casescumrate"]  = sub1.loc[:,"casescum"]/sub1.loc[:,"population"]*1.0E6
        sub1.loc[:,"caserate"]  = sub1.loc[:,"caserate"]/14
        sub1.loc[:,"cases"]  = sub1.loc[:,"cases"]/14
        
        cols = selCols.copy()
        cols[3:6]=("deaths","deathrate","deathscum" )
        sub2.columns = cols
        sub2.loc[:,"deathrate"] = sub2.loc[:,"deathrate"]*10/14  #normalize for 1.0E6
        sub2.loc[:,"deathscumrate"] = sub2.loc[:,"deathscum"]/sub2.loc[:,"population"]*1.0E6
        sub2.loc[:,"deaths"]  = sub2.loc[:,"deaths"]/14
        
        subMerged=sub1.merge(sub2, how='left', on=("country_code","date"))

        return subMerged
        
# The figure making process is generalized into this class, facilitating coding
# graphics, and also enabling variants as derived classes, see if this simplifies
# things
#    
class perCountryFigure(object):
    """ This permits to make figures of data organized by country, it is expected that 
        derived classes will bring different selections and orderings; further 
        parametrization is also envisionned
    """
    class defaultCopyAdapter():
        def prepareDF(self,df,**kwargs):
            return df.copy()
                
    defaultOpts = {
         "breakCond" : lambda count, country : count > 30,
         "skipCond"  : lambda count, country : False,
         "countryDataAdapter" : defaultCopyAdapter(),
        }

    
    def __init__(self, dateStart = None, **kwdOpts):
        """
        Args: dateStart: date for starting the (X axis) timescale
              breakCond: function of count and country, if returns True building
                         loop is terminated
              IfCond: function of count and country, if returns False building
                         loop skips, count does not increment when skipping
              countryDataAdapter: object whose method prepareDF will be called on each
                         country dataframe to return an adapted frame. Default is a 
                         simple copy of the dataframe
        """
        self.dateStart = dateStart
        self.options = {}
        setDefaults(self.options, kwdOpts,  perCountryFigure.defaultOpts)
        self.figureClass = figureTSFromFrameEU
        
    def initPainter(self, subnodeSpec=None, figsize=(15,15), maxCol=6, colFirst=False):
        if subnodeSpec is None:
            subnodeSpec = self.subnodeSpec
        elif isinstance(subnodeSpec,int):
            self.subnodeSpec = (lambda i,j:{"nrows":i,"ncols":j})(
                                       *subPlotShape( subnodeSpec, maxCol=maxCol,
                                                       colFirst=colFirst))
            subnodeSpec = self.subnodeSpec
            
        self.painter = self.figureClass(None, subplots=subnodeSpec, figsize=figsize,
                                              dateTranslate = False )

    def skipIfCond(self, count, country):
        return self.options["skipCond"](count, country)

    def breakIfCond(self, count, country):
        return self.options["breakCond"](count, country)


    ## these are 2 functions to be used with mkImage, although user can
    ## make one as needed, first is the default used in mkImage
    def defaultSIPA(dateStart, country):
        return toDict (label=f"Days since {dateStart}",
                       title=f"Data from EU site: {country}",
                       legend=True,
                       xlabel=f"Days since {dateStart}",
                       ylabel="Events"
        )

    def perMillionSIPA(dateStart, country):
        return toDict (label=f"Days since {dateStart}",
                       title=f"Data from EU site: {country}",
                       legend=True,
                       xlabel=f"Days since {dateStart}",
                       ylabel="Events per million population"
        )

    
    def mkImage(self, groupedDF, plotCols, subImgPaintAttrs = defaultSIPA):
        """
            Argument subImgPaintAttrs is a function taking 2 args and 
            returning a dict with the keyword args for calling self.painter.setAttrs.
            Example ( and default provided above)
        """
        count = 0
        self.abbrevIssueList=[]
        dataConvEU = EUSiteData()
        for (country, dfExtractOrig) in groupedDF:
            if self.skipIfCond(count, country):
                continue
            count+=1
            if self.breakIfCond(count, country):
                break

            dataConv = self.options["countryDataAdapter"] 
            dfExtract = dataConv.prepareDF(dfExtractOrig)
            if False:
                print(  f"After preparation using {type(dataConv)}.prepareDF method\n"  
                  + f"Columns of dfExtract:{dfExtract.columns}",
                    file = sys.stderr )

            # set index correctly, it will be used by figureTSFromFrameEU._dtToElapsed
            dfExtract = dfExtract.set_index("date").copy()


            self.painter.doPlot(df = dfExtract.loc[:, plotCols] )
            self.painter.setAttrs(**subImgPaintAttrs(self.dateStart, country))
            self.painter.advancePlotIndex()  


class perCountryFigureTSF(perCountryFigure):
    """ 
       This derived class considers figureTSFEU instead of figureFromFrame, therefore 
       enabling an ad-hoc x-axis time index.
    """ 
    defaultOpts = {
         "breakCond" : lambda count, country : count > 30,
         "skipCond"  : lambda count, country : False,
        }
    def __init__(self, dateStart = None, **kwdOpts):
        """
        Args: 
             - managed by base class
              dateStart: date for starting the (X axis) timescale
              breakCond: function of count and country, if returns True building
                         loop is terminated
              IfCond: function of count and country, if returns False building
                         loop skips, count does not increment when skipping
        """
        perCountryFigure.__init__(self, dateStart = dateStart, **kwdOpts)
        setDefaults(self.options, kwdOpts,  perCountryFigure.defaultOpts)

        # this causes a figureTSFromFrameEU to be used
        self.figureClass = figureTSFromFrameEU
            

if __name__ == "__main__":
    import unittest
    import sys

    covidDataEUCsv = "dataEURdf/covid-19-coronavirus-data-weekly-from-17-december-2020.csv"
    
    class DGTestEU(unittest.TestCase):

        def commonTest(figureClass):
            data_covidDataEU  = read_csvPandas( covidDataEUCsv,
                                                error_bad_lines=False, sep="," )

            print( f"Loaded {covidDataEUCsv}", file = sys.stderr)            


            data_covidDataEU["date"] = PAN.to_datetime(
                data_covidDataEU.loc[:,"year_week"]+"-1",
                format="%Y-%W-%w")



            dateStart = data_covidDataEU["date"].min()
            dateEnd   = data_covidDataEU["date"].max() 
            dateSpan  = dateEnd - dateStart 
            print( f"Our statistics span {dateSpan.days+1} days, start: {dateStart}" +
                   f" and end {dateEnd}" )
            data_covidDataEU["elapsedDays"] = (data_covidDataEU["date"] - dateStart).dt.days


            dt  = data_covidDataEU.copy()
            dt = dt.set_index("continent")
            dtx = dt[dt.index == "Europe"]
            dtg = dtx.groupby("country")

            myDataAdapter = EUSiteData()
            myFig =  figureClass( countryDataAdapter = myDataAdapter)
            plotCols = ( "cases", "deaths")
            myFig.initPainter( subnodeSpec=15, maxCol=3)
            myFig.mkImage( dtg, plotCols)
                
            print("Test1 ended OK", file = sys.stderr)            

        def test1(self):
            DGTestEU.commonTest(perCountryFigure)
            
        def test2(self):
            DGTestEU.commonTest(perCountryFigureTSF)

            
    # .............................................................................
            
    print ("Launching test with unittest package/framework")
    r= unittest.main()
    print ("RESULT=", r)
