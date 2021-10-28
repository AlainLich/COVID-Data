__author__ = 'Alain Lichnewsky'
__license__ = 'MIT License'
__version__ = '1.1'

from lib.DataMgr       import *
from DataMgrRdf        import *
from DataMgrJSON       import *
import lib.RDFandQuery as RDFQ

import re

# ------------------------------------------------------------------------------
#
# Note: This has been moved here since I reimplemented with a yield/generator mechanism,
#       which is faster
#
# ------------------------------------------------------------------------------

class listOrSingleIteratorOld:
    """ return a generator:
           1) if obj is a real iterable (not a string): return iteratively elts
           2) if obj is None: stop iteration
           3) return obj and stop iterating thereafter
    """
    def __init__(self, obj):
        self.obj = obj
        self.isNone = self.obj is None
        self.isIter = not isinstance(obj, (str, bytes, dict)) and isinstance(obj, Iterable)
        self.index = 0
        
    def __iter__(self):
        return self
     
    def __next__(self):
        if self.isNone :
            raise StopIteration()
        elif not self.isIter:
            self.isNone =  True
            return self.obj
        else:
            self.index+=1
            if self.index <= len(self.obj):
                return self.obj[self.index-1]

        raise StopIteration()
    
# ------------------------------------------------------------------------------


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


    class DGTestFRAPI(unittest.TestCase):
        """ Series of test concerning FRAPI (more API for the French site)
        """        
        siteOpts= {"maxDirSz": 100*(2**10)**2}

#       Probably not interesting
#       'GET' 'https://www.data.gouv.fr/api/1/datasets/badges/&size=10'


#        # returns list of tags, with score= count, may want to use for further
#        # enquiry
#       'GET' 'https://www.data.gouv.fr/api/1/tags/suggest/?q=covid&size=8' 


        
        def test_rqtbuilder0(self):
            """ Test for generating HTTP request
                'GET' 'https://www.data.gouv.fr/api/1/datasets/?tag=spf&page=0&page_size=20'

                This tests the defaults in defaultOpts
            """
            specOpts={}
            dataFileVMgr = manageAndCacheDataFilesFRAPI("./data4debug",
                                                        **DGTestFRAPI.siteOpts, **specOpts)
            testGenTarget="'GET' 'https://www.data.gouv.fr/api/1/datasets/?tag=spf&page=0&page_size=20'"
            print(f"\n\nExpected genHTTP Target={testGenTarget}", file=sys.stderr)
            dataFileVMgr.getRemoteInfo()

        def test_rqtbuilder1(self):
            """ Test for generating HTTP request
                'GET' 'https://www.data.gouv.fr/api/1/datasets/?tag=spf&page=0&page_size=20'

                This substitutes almost indentical values to the defaults in defaultOpts
            """
            specOpts={'ApiInq'       : 'datasets',
                      'InqParmsDir'  : {"tag":"spf"},
                      'cacheFname': '.cache.rqtTest1.json'}
            dataFileVMgr = manageAndCacheDataFilesFRAPI("./data4debug",
                                                        **DGTestFRAPI.siteOpts, **specOpts)
            testGenTarget="'GET' 'https://www.data.gouv.fr/api/1/datasets/?tag=spf&page=0&page_size=20'"
            print(f"\n\nExpected genHTTP Target={testGenTarget}", file=sys.stderr)
            dataFileVMgr.getRemoteInfo()

        def test_rqt1analyze(self):
            """ Test analyzing cached metadata from  test_rqtbuilder1(

            """
            specOpts={ 'cacheFname': '.cache.rqtTest1.json',
                       "dumpMetaFile" : "rqtTest1.meta.dump",
                       "dumpMetaInfoFile" : "rqtTest1.metainfo.dump"
                      }
            dataFileVMgr = manageAndCacheDataFilesFRAPI("./data4debug",
                                                        **DGTestFRAPI.siteOpts, **specOpts )
            dataFileVMgr.getRemoteInfo(localOnly = True)
            

        def test_rqtbuilder2(self):
            """ Test for generating HTTP request
                'GET' 'https://www.data.gouv.fr/api/1/datasets/?tag=covid&page=0&page_size=20' 
                 'GET' 'https://www.data.gouv.fr/api/1/datasets/?tag=covid19&page=0&page_size=20' 

                 Note the syntax in specOpts['InqParmsDir'], introducing a list
            """
            tagset1 = ({"tag":"covid"}, {"tag":"covid19"})
            # larger tagset from test4: does not uncover more 'sursaud' datasets
            tagset2 = (
                {'tag' : 'covid'},
                {'tag' : 'covid-19'},
                {'tag' : 'covid19'},
                {'tag' : 'covid19france'},
                {'tag' : 'covid2019'},
                {'tag' : 'covid-en-france'},
                {'tag' : 'covidep'},
                {'tag' : 'covidfrance'},
                {'tag' : 'covidom'},
                {'tag' : 'covidreport'},
                {'tag' : 'covid-tracker'},
                {'tag' : 'covidtracker'},
                {'tag' : 'covidtracker-fr'},
                {'tag' : 'covid-trocqueur'}
                     )
            specOpts={'ApiInq'       : 'datasets',
                      'ApiInqQuery'  : tagset1,
                      'InqParmsDir'  : {},
                      'cacheFname': '.cache.rqtTest2.json'}
            dataFileVMgr = manageAndCacheDataFilesFRAPI("./data4debug",
                                                        **DGTestFRAPI.siteOpts, **specOpts)
            testGenTarget= "\n\t".join((
                "'GET' 'https://www.data.gouv.fr/api/1/datasets/?tag=covid&page=0&page_size=20'", 
                "'GET' 'https://www.data.gouv.fr/api/1/datasets/?tag=covid19&page=0&page_size=20'"            ))
            print(f"\n\nExpected genHTTP Target=\n\t{testGenTarget}", file=sys.stderr)
            dataFileVMgr.getRemoteInfo()

        def test_rqt2analyze(self):
            """ Test analyzing cached metadata from  test_rqtbuilder2(

            """
            specOpts={ 'cacheFname': '.cache.rqtTest2.json',
                       "dumpMetaFile" : "rqtTest2.meta.dump",
                       "dumpMetaInfoFile" : "rqtTest2.metainfo.dump"
                      }
            rex = re.compile('(.*sursaud|^donnees-hospitalieres).*')
            def uselFn(urqt):
                return rex.match(urqt.fname) or rex.match(urqt.url)

            
            dataFileVMgr = manageAndCacheDataFilesFRAPI("./data4debug",
                                                        **DGTestFRAPI.siteOpts, **specOpts )
            dataFileVMgr.getRemoteInfo(localOnly = True)
            #dataFileVMgr.pprintDataResources(bulk=True)
            dataFileVMgr.updatePrepare()            
            dataFileVMgr.updateSelect(displayCount=100 ,  URqtSelector = uselFn)
            
            l = '\n\t'.join( x.fname for x in dataFileVMgr.updtList)
            print(f"Selection: fnames:\n{l}", file=sys.stderr)
            l = '\n\t'.join( x.url for x in dataFileVMgr.updtList)
            print(f"Selection: urls:\n{l}", file=sys.stderr)

            dataFileVMgr.printUpdtList('fname') 
            dataFileVMgr.printUpdtList('url') 
            
        def test_rqt2loadit(self):
            """ Test loading into cache from selected information from Data.Gouv.fr

            """
            specOpts={ 'cacheFname': '.cache.rqtTest2.json',
                       "dumpMetaFile" : "rqtTest2.meta.dump",
                       "dumpMetaInfoFile" : "rqtTest2.metainfo.dump"
                      }
            rex = re.compile('.*sursaud.*')
            def uselFn(urqt):
                return rex.match(urqt.fname) or rex.match(urqt.url)

            
            dataFileVMgr = manageAndCacheDataFilesFRAPI("./data4debug",
                                                        **DGTestFRAPI.siteOpts, **specOpts )
            dataFileVMgr.getRemoteInfo(localOnly = True)
            #dataFileVMgr.pprintDataResources(bulk=True)
            dataFileVMgr.updatePrepare()            
            dataFileVMgr.updateSelect(displayCount=10 ,  URqtSelector = uselFn)
            dataFileVMgr.cacheUpdate()
            
        def test_rqtbuilder3(self):
            """ Test for generating HTTP request
                # check, suggest may perform keyword completion
                  'GET' 'https://www.data.gouv.fr/api/1/datasets/suggest/?q=covid&size=10'


            """
            specOpts={'ApiInq'       : 'datasets/suggest',
                      'ApiInqQuery'  : {'q':'covid'},
                      'InqParmsDir'  : {"size":200},
                      'cacheFname': '.cache.rqtTest3.json'}
            dataFileVMgr = manageAndCacheDataFilesFRAPI("./data4debug",
                                                        **DGTestFRAPI.siteOpts, **specOpts)
            testGenTarget="'GET' 'https://www.data.gouv.fr/api/1/datasets/suggest/?q=covid&size=10'"
            print(f"\n\nExpected genHTTP Target={testGenTarget}", file=sys.stderr)
            dataFileVMgr.getRemoteInfo()

        def test_rqt3analyze(self):
            """ Test analyzing cached metadata from  test_rqtbuilder3(

            """
            specOpts={ 'cacheFname': '.cache.rqtTest3.json',
                       "dumpMetaFile" : "rqtTest3.meta.dump",
                       "dumpMetaInfoFile" : "rqtTest3.metainfo.dump"
                      }
            dataFileVMgr = manageAndCacheDataFilesFRAPI("./data4debug",
                                                        **DGTestFRAPI.siteOpts, **specOpts )
            dataFileVMgr.getRemoteInfo(localOnly = True)

            
        def test_rqtbuilder4(self):
            """ Test for generating HTTP request
                returns list of tags, with score= count, may want to use for further
                enquiry
                'GET' 'https://www.data.gouv.fr/api/1/tags/suggest/?q=covid&size=8' 
            """
            specOpts={'ApiInq'       : 'tags/suggest',
                      'ApiInqQuery'  : {'q':'covid'},
                      'InqParmsDir'  : {"size":'40'},
                      'cacheFname': '.cache.rqtTest4.json'}
            dataFileVMgr = manageAndCacheDataFilesFRAPI("./data4debug",
                                                        **DGTestFRAPI.siteOpts, **specOpts )
            testGenTarget="'GET' 'https://www.data.gouv.fr/api/1/tags/suggest/?q=covid&size=8'"
            print(f"\n\nExpected genHTTP Target={testGenTarget}", file=sys.stderr)
            dataFileVMgr.getRemoteInfo()

        def test_rqt4analyze(self):
            """ Test analyzing cached metadata from  test_rqtbuilder4(

            """
            specOpts={ 'cacheFname': '.cache.rqtTest4.json',
                       "dumpMetaFile" : "rqtTest4.meta.dump",
                       "dumpMetaInfoFile" : "rqtTest4.metainfo.dump"
                      }
            dataFileVMgr = manageAndCacheDataFilesFRAPI("./data4debug",
                                                        **DGTestFRAPI.siteOpts, **specOpts )
            dataFileVMgr.getRemoteInfo(localOnly = True)

        def test_rqtbuilder5(self):
            """ Test for generating HTTP request
                returns list of tags, with score= count, may want to use for further
                enquiry
                'GET' 'https://www.data.gouv.fr/api/1/tags/suggest/?q=covid&size=8' 
            """
            specOpts={'ApiInq'       : 'tags/suggest',
                      'ApiInqQuery'  : {'q':'covid'},
                      'InqParmsDir'  : ({"size":'8'},{"size":'14'}),
                      'cacheFname': '.cache.rqtTest5.json' }
            dataFileVMgr = manageAndCacheDataFilesFRAPI("./data4debug",
                                                        **DGTestFRAPI.siteOpts, **specOpts )
            testGenTarget= "\n\t".join(("'GET' 'https://www.data.gouv.fr/api/1/tags/suggest/?q=covid&size=8'",
                            "'GET' 'https://www.data.gouv.fr/api/1/tags/suggest/?q=covid&size=12'"))
            print(f"\n\nExpected genHTTP Target=\n\t{testGenTarget}", file=sys.stderr)
            dataFileVMgr.getRemoteInfo()


        def test_rqt5analyze(self):
            """ Test analyzing cached metadata from  test_rqtbuilder5(

            """
            specOpts={ 'cacheFname': '.cache.rqtTest5.json',
                       "dumpMetaFile" : "rqtTest5.meta.dump",
                       "dumpMetaInfoFile" : "rqtTest5.metainfo.dump"
                      }
            dataFileVMgr = manageAndCacheDataFilesFRAPI("./data4debug",
                                                        **DGTestFRAPI.siteOpts, **specOpts )
            dataFileVMgr.getRemoteInfo(localOnly = True)

            
        def test_rqtbuilder6(self):
            """ Test for generating HTTP request
                returns list of tags, with score= count, may want to use for further
                enquiry
                'GET' 'https://www.data.gouv.fr/api/1/tags/suggest/?q=covid&size=8' 
            """
            specOpts={'ApiInq'       : 'tags/suggest',
                      'ApiInqQuery'  : ({'q':'covid'},{'q':'covid19'}),
                      'InqParmsDir'  : ({"size":'8'},{"size":'20'}),
                      'cacheFname': '.cache.rqtTest6.json'}
            dataFileVMgr = manageAndCacheDataFilesFRAPI("./data4debug",
                                                        **DGTestFRAPI.siteOpts, **specOpts )
            testGenTarget= "\n\t".join(("'GET' 'https://www.data.gouv.fr/api/1/tags/suggest/?q=covid&size=8'",
                            "'GET' 'https://www.data.gouv.fr/api/1/tags/suggest/?q=covid&size=12'",
                            "'GET' 'https://www.data.gouv.fr/api/1/tags/suggest/?q=covid19&size=8'",
                            "'GET' 'https://www.data.gouv.fr/api/1/tags/suggest/?q=covid19&size=12'"))
            print(f"\n\nExpected genHTTP Target=\n\t{testGenTarget}", file=sys.stderr)
            dataFileVMgr.getRemoteInfo()
            
        def test_rqt6analyze(self):
            """ Test analyzing cached metadata from  test_rqtbuilder6(

            """
            specOpts={ 'cacheFname': '.cache.rqtTest6.json',
                       "dumpMetaFile" : "rqtTest6.meta.dump",
                       "dumpMetaInfoFile" : "rqtTest6.metainfo.dump"
                      }
            dataFileVMgr = manageAndCacheDataFilesFRAPI("./data4debug",
                                                        **DGTestFRAPI.siteOpts, **specOpts )
            dataFileVMgr.getRemoteInfo(localOnly = True)


        def test_rqt7get(self):
            """ Test getting files with vaccination counts
            """
            specOpts={ 'CacheValidity': 12*60*60, # normal caching period (seconds)
                        'cacheFname': '.cache.vaccin.json',
                       "dumpMetaFile" : "vaccin.meta.dump",
                       "dumpMetaInfoFile" : "vaccin.metainfo.dump",
                       'ApiInq'       : 'datasets',
                       'InqParmsDir'  : {"tag":"covid"},
                      }
            
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# Try to be more selective

#From dataVaccin/vaccin.meta.dump

#  Fichiers avec le nombre de personnes ayant reçu au moins une dose ou complètement 
#  vaccinées, arrêté à la dernière date disponible :
#  - vacsi-tot-fra-YYYY-MM-DD-HHhmm.csv (échelle nationale)
#  - vacsi-tot-reg-YYYY-MM-DD-HHhmm.csv (échelle régionale)
#  - vacsi-tot-dep-YYYY-MM-DD-HHhmm.csv (échelle départementale)
#

#Fichiers avec le nombre quotidien de personnes ayant reçu au moins une dose, 
#par vaccin, et par date d’injection :
#  - vacsi-v-fra-YYYY-MM-DD-HHhmm.csv (échelle nationale)
#  - vacsi-v-reg-YYYY-MM-DD-HHhmm.csv (échelle régionale)
#  - vacsi-v-dep-YYYY-MM-DD-HHhmm.csv (échelle départementale)

# Les vaccins sont codifiés de la façon suivante : 
# 0 : Tous vaccins\n'
# 1 : COMIRNATY Pfizer/BioNTech
# 2 : Moderna
# 3 : AstraZeneka
# 4 : Janssen

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


            rex = re.compile('.*vacsi-v-(fra|reg|dep).*')
            def uselFn(urqt):
                return rex.match(urqt.fname) or rex.match(urqt.url)

            
            dataFileVMgr = manageAndCacheDataFilesFRAPI("./dataVaccin",
                                                        **DGTestFRAPI.siteOpts, **specOpts )
            dataFileVMgr.getRemoteInfo(localOnly = True)
            #dataFileVMgr.pprintDataResources(bulk=True)
            dataFileVMgr.updatePrepare()            
            dataFileVMgr.updateSelect(displayCount=100 ,  URqtSelector = uselFn)
            
            l = '\n\t'.join( x.fname for x in dataFileVMgr.updtList)
            print(f"Selection: fnames:\n{l}", file=sys.stderr)
            l = '\n\t'.join( x.url for x in dataFileVMgr.updtList)
            print(f"Selection: urls:\n{l}", file=sys.stderr)

            dataFileVMgr.printUpdtList('fname') 
            dataFileVMgr.printUpdtList('url')
            
            dataFileVMgr.cacheUpdate()


    class DGTestFRGeneral(unittest.TestCase):
        """ Series of test concerning obtaining various forms of information from
            the French site...
        """        
        siteOpts= {"maxDirSz": 100*(2**10)**2}
        def test_insee_eco(self):
            """ Test getting files with vaccination counts
            """
            specOpts={ 'CacheValidity': 12*60*60, # normal caching period (seconds)
                        'cacheFname': '.cache.insee.json',
                       "dumpMetaFile" : "insee.meta.dump",
                       "dumpMetaInfoFile" : "insee.metainfo.dump",
                       'ApiInq'       : 'datasets',
                       'InqParmsDir'  : {"tag":"covid"},
                      }
            #### NOTE: NOT FINAL TBD!!!!
            #
            # tag to be tried :: 'etat-civil' 'demographie' 'population' 'recensement'
            # tag economie => aboutit au MINEFI (MEFR ces temps ci!)
            #
	    # TAGS to be evaluated from
            #      https://www.data.gouv.fr/fr/datasets/comptabilite-nationale/
            # apu
            # consommation
            # deficit
            # depense-publique
            # dette-publique
            # emploi
            # fbcf
            # finance-publique
            # pib
            # pouvoir-d-achat
            # productivite
            # valeur-ajoutee
            
            # PIB
            #https://www.data.gouv.fr/en/datasets/les-produits-interieurs-bruts-regionaux/
            #
            #How to access this systematically??
            #https://www.insee.fr/fr/statistiques/4277596?sommaire=4318291
            #
            rex = re.compile('.*vacsi-v-(fra|reg|dep).*')
            def uselFn(urqt):
                return rex.match(urqt.fname) or rex.match(urqt.url)

            
            dataFileVMgr = manageAndCacheDataFilesFRAPI("./data4debug",
                                                        **DGTestFRAPI.siteOpts, **specOpts )
            dataFileVMgr.getRemoteInfo(localOnly = True)
            #dataFileVMgr.pprintDataResources(bulk=True)
            dataFileVMgr.updatePrepare()            
            dataFileVMgr.updateSelect(displayCount=100 ,  URqtSelector = uselFn)
            
            l = '\n\t'.join( x.fname for x in dataFileVMgr.updtList)
            print(f"Selection: fnames:\n{l}", file=sys.stderr)
            l = '\n\t'.join( x.url for x in dataFileVMgr.updtList)
            print(f"Selection: urls:\n{l}", file=sys.stderr)

            dataFileVMgr.printUpdtList('fname') 
            dataFileVMgr.printUpdtList('url')
            
            dataFileVMgr.cacheUpdate()

            
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

    class DGTestYield(unittest.TestCase):
          def test1(self):
              for el in listOrSingleIterator((1,2,3)):
                  print(f"Iterating with returned el={el}", file = sys.stderr)
          def test1Old(self):
              for el in listOrSingleIteratorOld((1,2,3)):
                  print(f"Iterating with returned el={el}", file = sys.stderr)
          def test2(self):
              for el in listOrSingleIterator(range(0,11,2)):
                  print(f"Iterating with returned el={el}", file = sys.stderr)
          def test2Old(self):
              for el in listOrSingleIteratorOld(range(0,11,2)):
                  print(f"Iterating with returned el={el}", file = sys.stderr)
          def test3(self):
              sum=0.0
              n=1100000
              for el in listOrSingleIterator(range(0,n)):
                  sum+=el
              print(f"test3: sum={sum}", file= sys.stderr)
              assert(sum==n*(n-1)/2)
          def test3Old(self):
              sum=0.0
              n=1100000
              for el in listOrSingleIteratorOld(range(0,n)):
                  sum+=el
              print(f"test3Old: sum={sum}", file= sys.stderr)
              assert(sum==n*(n-1)/2)
          def test3b(self):
              sum=0.0
              n=10
              for el in listOrSingleIterator(range(0,n)):
                  sum+=el
              print(f"test3: sum={sum}", file= sys.stderr)
              assert(sum==n*(n-1)/2)

          def test4(self):
              for el in listOrSingleIterator("tyty"):
                  print(f"Iterating with returned el={el}", file = sys.stderr)
                  
          def test5(self):
              for el in listOrSingleIterator([f"tyty{e}" for e in range(10)]):
                  print(f"Iterating with returned el={el}", file = sys.stderr)

          def test6(self):
              for el in listOrSingleIterator((f"tyty{e}" for e in range(10))):
                  print(f"Iterating with returned el={el}", file = sys.stderr)                  
          def test7(self):
              for el in listOrSingleIterator({f"tyty{e}":e for e in range(10)}):
                  print(f"Iterating with returned el={el}", file = sys.stderr)              
                  
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

