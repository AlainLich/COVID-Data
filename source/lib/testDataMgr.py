__author__ = 'Alain Lichnewsky'
__license__ = 'MIT License'
__version__ = '1.1'

from lib.DataMgr       import *
from DataMgrRdf        import *
from DataMgrJSON       import *
import lib.RDFandQuery as RDFQ

if __name__ == "__main__":
    import unittest
    import sys

    class DGTest(unittest.TestCase):
        """ First series of test concerns Covid data on DataGouv.fr
        """
        def test_baseLocal(self):
            """ Example using local information
            """

            dataFileVMgr = manageDataFileVersions("../data")
            print("Most recent versions of files in data directory:")
            for f in dataFileVMgr.listMostRecent() :
                print(f"\t{f}")


        def test_remote(self):
            """ Example using remote information
            """
            dataFileVMgr = manageAndCacheDataFilesFRDG("../data")
            dataFileVMgr.getRemoteInfo()
            # dataFileVMgr.pprintDataResources(bulk=True)
            dataFileVMgr.updatePrepare()
            dataFileVMgr.cacheUpdate()

        def test_remoteScavenger(self):
            """ Example of scavenging cache spac
            """
            opts= {}
            setDefaults(opts, {"forceCacheRecovery":False,
                                    'maxDirSz'     : 30*(2**10)**2},
                             manageAndCacheDataFilesFRDG.defaultOpts)
            DGTestPopDemo.defaultPop
            dataFileVMgr = manageAndCacheDataFilesFRDG("../data", **opts)
            dataFileVMgr.getRemoteInfo()
            # dataFileVMgr.pprintDataResources(bulk=True)
            dataFileVMgr.updatePrepare()
            dataFileVMgr.cacheUpdate()
            

        def test_pprint(self):
            """ Example of pretty printing of remote/cached information
            """
            dataFileVMgr = manageAndCacheDataFilesFRDG("../data")
            dataFileVMgr.getRemoteInfo( localOnly = True)
            dataFileVMgr.pprintDataItem( item="description")

        def test_pprint2(self):
            """ Example of pretty printing of remote/cached information
                Check situation where the `item` calls for  subfields 'name' and 'class'
                of  'organizations'
            """
            dataFileVMgr = manageAndCacheDataFilesFRDG("../data")
            dataFileVMgr.getRemoteInfo( localOnly = True)
            dataFileVMgr.pprintDataItem( item=".*org.*/^(name|class)$")

        def test_pprint3(self):
            """ Example of pretty printing of remote/cached information
                Check situation where the `item` calls for  subfields 'name' and 'class'
                of  'organizations'
            """
            dataFileVMgr = manageAndCacheDataFilesFRDG("../data")
            dataFileVMgr.getRemoteInfo( localOnly = True)

            dataFileVMgr.pprintDataItem( item="resource.*/(f.*|title.*)")

            
        def test_pprint4(self):
            """ Example of pretty printing of remote/cached information.
                Check situation where the `item` calls for all subfields of
                organizations
            """
            dataFileVMgr = manageAndCacheDataFilesFRDG("../data")
            dataFileVMgr.getRemoteInfo( localOnly = True)
            dataFileVMgr.pprintDataItem( item=".*org.*/.*")
            
            
        def test_dump(self):
            """ Example of pretty printing of remote/cached information
            """
            dataFileVMgr = manageAndCacheDataFilesFRDG("../data")
            dataFileVMgr.getRemoteInfo( localOnly = True)
            dataFileVMgr.pprintDataResources( bulk = True)

    class DGTestEU(unittest.TestCase):
        """ First series of test concerns Covid data on European Data portal
        """
        siteOpts= {"maxDirSz": 80*(2**10)**2}
        
        def test_baseLocal(self):
            """ Example using local information
            """

            dataFileVMgr = manageDataFileVersions("../dataEU", **DGTestEU.siteOpts)
            print("Most recent versions of files in data directory:")
            for f in dataFileVMgr.listMostRecent() :
                print(f"\t{f}")


        def test_remote(self):
            """ Example using remote information
            """
            dataFileVMgr = manageAndCacheDataFilesEU("../dataEU", **DGTestEU.siteOpts)
            dataFileVMgr.getRemoteInfo()
            # dataFileVMgr.pprintDataResources(bulk=True)
            #dataFileVMgr.updatePrepare()
            #dataFileVMgr.cacheUpdate()


        def test_pprint(self):
            """ Example of pretty printing of remote/cached information
            """
            dataFileVMgr = manageAndCacheDataFilesEU("../dataEU", **DGTestEU.siteOpts)
            dataFileVMgr.getRemoteInfo( localOnly = True)
            dataFileVMgr.pprintDataItem( item="description")

        def test_pprint2(self):
            """ Example of pretty printing of remote/cached information
                Check situation where the `item` calls for  subfields 'name' and 'class'
                of  'organizations'
            """
            dataFileVMgr = manageAndCacheDataFilesEU("../dataEU", **DGTestEU.siteOpts)
            dataFileVMgr.getRemoteInfo( localOnly = True)
            dataFileVMgr.pprintDataItem( item=".*org.*/^(name|class)$")

        def test_pprint3(self):
            """
            """
            dataFileVMgr = manageAndCacheDataFilesEU("../dataEU",  **DGTestEU.siteOpts)
            dataFileVMgr.getRemoteInfo( localOnly = True)

            dataFileVMgr.pprintDataItem( item="resul.*/dataset/.*", showVals=False)

        def test_pprint3b(self):
            """ Found (among others):
                     results:dataset:distribution_dcat:downloadURL_dcat::uri>@(0.0.0.0.0)	->	'https://opendata.ecdc.europa.eu/covid19/casedistribution/csv'
                     results:dataset:distribution_dcat:uri:(0.0.0.0):>>>'http://data.europa.eu/88u/distribution/260bbbde-2316-40eb-aec3-7cd7bfc2f590'
                     This was an interesting csv, however the meta information is not great! 
            """
            dataFileVMgr = manageAndCacheDataFilesEU("../dataEU", **DGTestEU.siteOpts)
            dataFileVMgr.getRemoteInfo( localOnly = True)

            dataFileVMgr.pprintDataItem( item="resul.*/dataset/distrib.*/(uri|descrip.*|.*url.*|.*download.*|title)/.*",
                                         showVals=True)

            
        def test_pprint4(self):
            """ Example of pretty printing of remote/cached information.
                Check situation where the `item` calls for all subfields of
                organizations
            """
            dataFileVMgr = manageAndCacheDataFilesEU("../dataEU", **DGTestEU.siteOpts)
            dataFileVMgr.getRemoteInfo( localOnly = True)
            dataFileVMgr.pprintDataItem( item="resul.*/dataset$$^ca.*/lang.*/.*", showVals=False)
            
            
        def test_dump(self):
            """ Example of pretty printing of remote/cached information
            """
            dataFileVMgr = manageAndCacheDataFilesEU("../dataEU", **DGTestEU.siteOpts)
            dataFileVMgr.getRemoteInfo( localOnly = True)
            dataFileVMgr.pprintDataResources( bulk = True, result=True, success=True)


        def test_help(self):
            """ Example of pretty printing of remote/cached help information
            """
            dataFileVMgr = manageAndCacheDataFilesEU("../dataEU", **DGTestEU.siteOpts)
            dataFileVMgr.getRemoteInfo( localOnly = True)
            dataFileVMgr.pprintDataResources( bulk = True, help= True, success=True)
            
    class DGTestRdfEU(unittest.TestCase):
        """ First series of test concerns Covid data on European Data portal
        """
        siteOpts= {"maxDirSz": 80*(2**10)**2}
        def test_baseLocal(self):
            """ Example using local information
            """

            dataFileVMgr = manageDataFileVersions("../dataEURdf", **DGTestRdfEU.siteOpts)
            print("Most recent versions of files in data directory:")
            for f in dataFileVMgr.listMostRecent() :
                print(f"\t{f}")


        def test_remote(self):
            """ Example using remote information
            """
            dataFileVMgr = manageAndCacheDataFilesRdfEU( "../dataEURdf",
                dumpMetaFile= "/tmp/dumpSPARQLresult.xml",
                **DGTestRdfEU.siteOpts)  #dump the SPARQL query response
            
            dataFileVMgr.getRemoteInfo()
            # dataFileVMgr.pprintDataResources(bulk=True)
            dataFileVMgr.updatePrepare()
            #dataFileVMgr.cacheUpdate()
            

        def test_XMLparse(self):
            """ Test the parsing of XML+SPARQL Response
            """
            optdict = {"--debug":None}
            xmlRDF="""<rdf:RDF xmlns:res="http://www.w3.org/2005/sparql-results#" xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
<rdf:Description rdf:nodeID="rset">
<rdf:type rdf:resource="http://www.w3.org/2005/sparql-results#ResultSet" />
    <res:resultVariable>DatasetTitle</res:resultVariable>
    <res:solution rdf:nodeID="r0">
      <res:binding rdf:nodeID="r0c0"><res:variable>DatasetTitle</res:variable><res:value xml:lang="en">COVID-19 documents on EUR-Lex</res:value></res:binding>
    </res:solution>
  </rdf:Description>
</rdf:RDF>
"""
            xmlParser = RDFQ.XMLtoRDF(optdict)
            xmlParser.parseQueryResult(inString=xmlRDF)
            ofn = "/tmp/testXMLParse.xml"
            xmlParser.outputSerial(ofn, serFmt="xml")
            sys.stderr.write(f"Wrote generated rdf (xml) on {ofn}\n")

        def test_XMLparse2(self):
            """ Test the parsing of XML+SPARQL Response
            """
            optdict = {"--debug":None}
            xmlRDF="""<rdf:RDF xmlns:res="http://www.w3.org/2005/sparql-results#" xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
<rdf:Description rdf:nodeID="rset">
<rdf:type rdf:resource="http://www.w3.org/2005/sparql-results#ResultSet" />
    <res:resultVariable>DatasetTitle</res:resultVariable>
    <res:resultVariable>Publisher</res:resultVariable>
    <res:resultVariable>ResourceDescription</res:resultVariable>
    <res:solution rdf:nodeID="r0">
      <res:binding rdf:nodeID="r0c0"><res:variable>DatasetTitle</res:variable><res:value xml:lang="en">COVID-19 documents on EUR-Lex</res:value></res:binding>
      <res:binding rdf:nodeID="r0c1"><res:variable>Publisher</res:variable><res:value rdf:resource="http://publications.europa.eu/resource/authority/corporate-body/PUBL"/></res:binding>
    </res:solution>
    <res:solution rdf:nodeID="r1">
      <res:binding rdf:nodeID="r1c0"><res:variable>DatasetTitle</res:variable><res:value xml:lang="en">COVID-19 documents on EUR-Lex</res:value></res:binding>
      <res:binding rdf:nodeID="r1c1"><res:variable>Publisher</res:variable><res:value rdf:resource="http://publications.europa.eu/resource/authority/corporate-body/PUBL"/></res:binding>
      <res:binding rdf:nodeID="r1c2"><res:variable>ResourceDescription</res:variable><res:value xml:lang="en">This page gives a non-exhaustive list of documents 
            </res:value></res:binding>
    </res:solution>
  </rdf:Description>
</rdf:RDF>
"""
            xmlParser = RDFQ.XMLtoRDF(optdict)
            xmlParser.parseQueryResult(inString=xmlRDF)
            ofn = "/tmp/testXMLParse.xml"
            xmlParser.outputSerial(ofn, serFmt="xml")
            sys.stderr.write(f"Wrote generated rdf (xml) on {ofn}\n")
            

            
    class DGTestPopDemo(unittest.TestCase):
            
        """ First series of test concerns demographic data on INSEE site
        """
        defaultPop = {
                   'CacheValidity':  12*60*60,       #cache becomes stale after 12 hours
                   'maxImportSz'  :  2*(2**10)**2,   #5 Mb: max size of individual file load
                   'maxDirSz'     :  100*(2**10)**2,  #100 Mb: max total cache directory size
                  }

        def test_remoteDF(self):
            """ Example using remote information with cached json
            """
            dataFileVMgr = manageAndCacheFilesDFrame("../dataPop",
                                                     ** DGTestPopDemo.defaultPop)
            dataFileVMgr.getRemoteInfo()
            # dataFileVMgr.pprintDataResources(bulk=True)
            dataFileVMgr.updatePrepare()
            dataFileVMgr.cacheUpdate()


    class DGTestUSACovidTracking(unittest.TestCase):            
        """ First series of test concerning https://covidtracking.com
        """
        defaultPop = {
                   'CacheValidity':  12*60*60,       #cache becomes stale after 12 hours
                   'maxImportSz'  :  2*(2**10)**2,   #5 Mb: max size of individual file load
                   'maxDirSz'     :  100*(2**10)**2,  #100 Mb: max total cache directory size
                  }

        def test_remoteDF(self):
            """ Example using remote information with cached json
            """
            dataFileVMgr = manageAndCacheFilesJSONHandwritten("../dataUSCovidTrack", **DGTestUSACovidTracking.defaultPop)
            dataFileVMgr.getRemoteInfo()
            dataFileVMgr.pprintDataResources(bulk=True)
            dataFileVMgr.updatePrepare()
            dataFileVMgr.cacheUpdate()

        def test_remoteDFnodefault(self):
            """ Example using remote information with cached json
            """
            dataFileVMgr = manageAndCacheFilesJSONHandwritten("../dataUSCovidTrack")
            dataFileVMgr.getRemoteInfo()
            dataFileVMgr.pprintDataResources(bulk=True)
            dataFileVMgr.updatePrepare()
            dataFileVMgr.cacheUpdate()
            

    class DGTestRegexp(unittest.TestCase):
        def chk(rex, s):
                  mobj = rex.match(s)
                  if mobj:
                      print(f"{s}\t->\t{mobj.groupdict()}")
                      return mobj.groupdict()
                  else:
                      print(f"{s}\tNOT RECOG")
                      return None

        def similar(dict1, dict2):
                if dict1 is None or dict2 is None:
                    return dict1 == dict2
                sk1 = set(dict1.keys())
                sk2 =  set(dict2.keys())
                retval = True
                for k in sorted(sk1&sk2):
                    if dict1[k] !=  dict2[k]:
                        print(f"difference for key {k} : {dict1[k]} {dict2[k]}")
                        retval=False
                return retval

        
        def test_rex1(self):
            rexList =  (
             """^(?P<hdr>.*[^\d])
               (( (?P<year>\d+)-(?P<month>\d+)-(?P<day>\d+)    # Year
                -(?P<hour>\d+)[h-](?P<minute>\d+)             # Time
               )|
                 ( (?P<pYear>\d{4})(?P<pMonth>\d{2})(?P<pDay>\d+) # Year yyyymmdd
                  -(?P<pTime>\d{6})                     # Time in format hhmmss (*)
               ))
              (?P<ftr>.*)$
             """,
              )

            strList = (
                ( "export-dataset-20200314-064905.csv", { 'hdr': 'export-dataset-', 
			'year': None, 'month': None, 'day': None, 
                        'hour': None, 'minute': None, 
                        'pYear': '2020', 'pMonth': '03', 'pDay': '14', 'pTime': '064905',
                        'ftr': '.csv'
                }),
                ( "InseeDep.xls",None),
                ( "InseeRegions.xls",None),
                ( "tags-2020-04-20-09-22.csv", {'hdr': 'tags-', 'year': '2020',
                                                'month': '04', 'day': '20', 'hour': '09',
                                                'minute': '22',
                                                'pTime': None,
                                                'ftr': '.csv'}),
                ( "donnees-hospitalieres-classe-age-covid19-2020-04-11-19h00.csv",
                              { 'hdr': 'donnees-hospitalieres-classe-age-covid19-',
                                'year': '2020', 'month': '04', 'day': '11',
                                'hour': '19', 'minute': '00',  'ftr': '.csv'})
             )

            
            for rexS in rexList:
              rex = re.compile(rexS, re.VERBOSE)
              print(rex)
              for s,verif in  strList:
                  answ = DGTestRegexp.chk(rex,s)
                  print(f"ANSW:\t{answ}\nREF\t{verif}\n")
                  self.assertTrue( DGTestRegexp.similar(answ,verif))


        def test_rexCompose(self):
            # here I am interested in splitting a string into 3 regexp
            # based on syntax re1$$re2$$re3 in such a way that a subregexp may
            # still contain a $

            rexList = ("lang$$en(?i)$$volume",                # realistic
                       "lang",                                # single component
                       "resul.*/.*data.*/lang.*/.*",       
                       "resource.*/(f.*|title.*)",
                       ".*org.*/^(name|class)$",
                                                              # I have this one ready
                       					      # keep it last!!!
                        """^(?P<hdr>.*[^\d])
               (( (?P<year>\d+)-(?P<month>\d+)-(?P<day>\d+)    # Year
                -(?P<hour>\d+)[h-](?P<minute>\d+)             # Time
               )|
                 ( (?P<pYear>\d{4})(?P<pMonth>\d{2})(?P<pDay>\d+) # Year yyyymmdd
                  -(?P<pTime>\d{6})                     # Time in format hhmmss 
               ))
              (?P<ftr>.*)$
             """,
            )
                  
            def tryReSplitCompile(reStr):
                rexs =  reStr.split("$$")
                print (f"\twe need to re.compile:{rexs}")
                comp = map ( rexTuple._tryReCompile  , rexs)
                return list(comp)
            
            for rexS in rexList:
                print(f"'{rexS}'")
                comps = tryReSplitCompile(rexS)
                for c in comps:
                    if  isinstance(c, list):
                        lc = map(lambda x: not isinstance(x,str), c)
                        print(f"->{len(c)}, {list(lc)}")
                    else:
                        print(f"Re.object: {c}")


        def test_rexTuple(self):
            # Now, test the class  rexTuple, which encapsulates our tuples
            # of regular expressions used when selecting data resources in json
            # structures (see  pprintDataResources)

            rexList = ("lang$$en(?i)$$volume",                # realistic
                       "lang",                                # single component
                       "resul.*/.*data.*/lang.*/.*",       
                       "resource.*/(f.*|title.*)",
                       ".*org.*/^(name|class)$",
                                                              # I have this one ready
                       					      # keep it last!!!
                        """^(?P<hdr>.*[^\d])
               (( (?P<year>\d+)-(?P<month>\d+)-(?P<day>\d+)    # Year
                -(?P<hour>\d+)[h-](?P<minute>\d+)             # Time
               )|
                 ( (?P<pYear>\d{4})(?P<pMonth>\d{2})(?P<pDay>\d+) # Year yyyymmdd
                  -(?P<pTime>\d{6})                     # Time in format hhmmss 
               ))
              (?P<ftr>.*)$
             """,
            )
                  
            for rexS in rexList:
                 print(f"'{rexS}'")
                 rt =  rexTuple(rexS)
                 print (f"\nrexS={rexS}\t->\t{rt}")

    class DGTestClassDef(unittest.TestCase):
          def test_1(self):
               dataFileVMgr = manageAndCacheDataFiles("../dataEU")
               ret= setOfSubClasses(dataFileVMgr)
               print( f"Subclasses:{ret}" )
               ret1= setOfSubClasses(manageAndCacheDataFiles)
               print( f"Subclasses:{ret1}" )
               self.assertEqual(ret, ret1, "Should be identical sets")
               
          def test_2(self):
               comp = checkDefaultCompat( manageAndCacheDataFiles)
               #self.assertEqual( comp , True) # test disabled for now, messages informative
               
    unittest.main()
    """ To run specific test use unittest cmd line syntax, eg.:
           python3 ../source/lib/testDataMgr.py   DGTest.test_pprint
                     DGTest
		     DGTestEU
                     DGTestRdfEU
                     DGTestPopDemo 
    		     DGTestRegexp
    		     DGTestUSACovidTracking
    		     DGTestUSACovidTracking.test_remoteDFnodefault
    """

