# -*- coding: utf-8 -*-
#

__author__ = 'Alain Lichnewsky'
__license__ = 'MIT License'
__version__ = '1.1'

from   lib.utilities import *
import requests, sys, pprint, pickle, time, shutil
from   collections   import Iterable, Mapping
import urllib, hashlib

from lib.DataMgr import *
import lib.RDFandQuery as RDFQ

class manageAndCacheDataFilesRDF(  manageAndCacheDataFiles):         
    def __init__(self, dirpath,**kwdOpts ):
        """
         Arguments:
             cacheFname :   file name for caching meta information, here show rdf+xml
        """
        defaultOpts = {
            'cacheFname'   :  ".cache.rdf",
            'httpTimeOut'  :  1
                  }
        manageAndCacheDataFiles.__init__(self, dirpath=dirpath)
        # by now, the base class initializer has obtained the local filesys information
        setDefaults(self.options, kwdOpts, manageAndCacheDataFilesRDF.defaultOpts)

    def _getRemoteMeta(self):
          """ Read the metadata on selected files from the remote site, store
              it into the DIRPATH/.cache file, keep it in the self.data attribute as the
              python representation of a json

             This is redefined here to allow for an iterative process, yet TBD. This
             will permit to honor the LIMIT and OFFSET parameters in the SPARQL queries,
             as well as promoting a netiquette compliant behaviour wrt. the server
          """
          spaceAvail = self._spaceAvail(self.dirpath)
          if spaceAvail < 300*(2**10):
              print (f"spaceAvail={spaceAvail}, 300K required,  maxDirSz={self.options['maxDirSz']} ")
              raise RuntimeError(f"Insufficient space in {self.dirpath} to store cached metadata")
          self._getRemoteMetaFromServer()
          # we integrate the prepareMeta functions; need to detect if LIMIT was in effect
          # and possibly iterate here (merging RDF; also what do we put in the pickle ?)
          self.prepareMeta(fromCache=False)
          
          self.metadata["pickleTS"]= time.strftime("Pickled at :%Y-%m-%d %H:%M:%S",
                                                   time.gmtime(time.time()))          
          cacheFname = os.path.join(self.dirpath,  self.options['cacheFname'])          
          with open(cacheFname,"wb") as pikFile:
                  pickler = pickle.Pickler( pikFile)
                  pickler.dump(self.metadata)
                  pickler.dump(self.data)
                  print(f"Stored pickle in {cacheFname}")

          return True
    
        
    def _getRemoteMetaFromServer(self):

          query = self._buildSparql()
        
          if 'HttpRQT' in self.options and  self.options['HttpRQT'] != 'POST': 
              raise NotImplementedError("Only POST method available for RDF")
          else:
              url = "/".join( map (lambda x:self.options[x],
                                   ( x for x in ('HttpHDR','ApiInq')
                                        if x in self.options  )))
              resp = requests.post(url=url,
                                   headers=self.options[ 'ApiHeaders' ], 
                                   params={ 'query': query},
                                   timeout= self.options['httpTimeOut'])

          #https://requests.readthedocs.io/en/master/
          pp = pprint.PrettyPrinter(indent=4, width=60)
          print (f"HTTP response headers:{pp.pformat(resp.headers)}")
          print (f"HTTP request:{resp.request}\nHTTP request headers:{pp.pformat(resp.request.headers)}")
          self.metadata["HTTP:Hdr:rqt"]  = resp.request.headers
          self.metadata["HTTP:Hdr:resp"] = resp.headers
          
          cde =resp.status_code
          cdeTxt = requests.status_codes._codes[cde][0]

          # will return OK even if thing does not exist
          if cde >= 400:
               print(f"URL/request={resp.url}\tStatus:{cde}:{cdeTxt}")
               print(f"Request to get remote information failed, {self.options['cacheFname']} may be stale")
               return
          print(f"URL/request={resp.url}\tStatus:{cde}:{cdeTxt}")

          self.data = resp.content
          self.metadata["data:type"] =  "txt/xml+rdf"

    def prepareMeta(self, fromCache=True):
        """ This replaces the placeholder routine in the base class manageAndCacheBase.
            It gets a self.data that is basically a byte string with xml+rdf contents
            and initializes a QueryDispatcher accessible as self.dataQuery. We leave 
            self.data as is (which is a waste of space ... but should have no adverse 
            effect)
        """
        print (f"In prepareMeta ({self})\nself.metadata = {self.metadata}")
        optdict = {"--debug":"debug" in self.options and  self.options["debug"]}

        ofn = None
        if "cachefileRDF" in self.options:
            ofn =  self.options["cachefileRDF"]
        elif "cacheFname" in self.options:
            spl = os.path.splitext(self.options["cacheFname"])
            ofn = os.path.join(self.dirpath, spl[0]+".prdf" )
            self.options["cachefileRDF"] = ofn

        self.dataQuery = RDFQ.QueryDispatcher( optdict )
        if fromCache and os.path.isfile(ofn):
            # reloading the cached RDF
            self.dataQuery.inputSerial(ofn, serFmt="xml")
        else:
            #need to parse to obtain RDF from the XML response
            xmlParser = RDFQ.XMLtoRDF(optdict)            
            xmlParser.parseQueryResult(inString=self.data)
                
            if ofn is not None: 
                   xmlParser.outputSerial(ofn, serFmt="xml")
                   sys.stderr.write(f"Wrote generated rdf (xml) on {ofn}\n")
                   
            self.dataQuery.initFromXMLtoRDF( xmlParser, copy = None)
            
    def pprintDataResources(self, bulk=False) :
          """ Pretty print selected information on files from the rdf/rdflib; if parameter
              `bulk` is True, the full json information is also shown

              Need to consider the case where we have not been able to load the metadata
          """
          if not hasattr(self,"data"):
              print("No meta data available, pretty print impossible")
              return

          prettyPrinter = pprint.PrettyPrinter(indent=4)
          if isinstance(self.data, str):
              print (f"Well we have a string {self.data[:123]}....")
          elif isinstance(self.data, bytes):
              print (f"Well we have a byte string {self.data[:123].decode('utf-8') }....")
          else:
              print (f"Well we have a {type(self.data)}....")

          # this is crude!
          self.dataQuery.dump()


class manageAndCacheDataFilesRdfEU(  manageAndCacheDataFilesRDF):
    """ Manage a local repository extracted from www.data.gouv.fr:
        - extraction of the  list of files based on criteria conforming to the
          European Open Data standards provided by:
          https://app.swaggerhub.com/apis/EU-Open-Data-Portal/eu-open_data_portal/0.8.0
          https://data.europa.eu/euodp/fr/Sample_REST_requests

        - provided by base class:  caching,  local copies,

        For now examples are shown in the test section at end of file (`test_remote`)
    """
    defaultOpts = {'HttpRQT'      :  "POST",
                   'HttpHDR'      : 'https://data.europa.eu/euodp/',
                   'ApiInq'       : 'sparqlep',
                   'ApiHeaders'   :  {"Accept": "application/rdf+xml",   
                                      "Content-Type":"application/rdf+xml"},
                   'CacheValidity':  12*60*60,       #cache becomes stale after 12 hours
                   'maxImportSz'  :  5*(2**10)**2,   #5 Mb: max size of individual file load
                   'maxDirSz'     :  50*(2**10)**2,  #50 Mb: max total cache directory size
                   "showMetaData" : True,
                   'cacheFname'   : '.cache.rdf',
    }

    def __init__(self, dirpath,**kwdOpts ):
        """
         Arguments:
               - `HttpHDR` : header of http command, see your http API
               - `ApiInq`  : API argument
               - `InqParmsDir` : dict with command API parameters
               - `maxImportSz` : 5 Mb: max size of individual file load
               - `maxDirSz`    : 50 Mb: max total cache directory size (.cache file
                                 storing meta data is not accounted for systematically)
        """
        manageAndCacheDataFilesRDF.__init__(self, dirpath=dirpath)
        # by now, the base class initializer has obtained the local filesys information
        setDefaults(self.options, kwdOpts, manageAndCacheDataFilesRdfEU.defaultOpts)
               

    def _buildSparql(self):
        # prepare for handling request customization
        print(f"In {self.__class__}._buildSparql\t available options:\n\t{sorted(self.options.keys())}")

        # for now a boiler plate request
        rqt = """PREFIX dcat: <http://www.w3.org/ns/dcat#>
PREFIX odp:  <http://data.europa.eu/euodp/ontologies/ec-odp#>
PREFIX dc: <http://purl.org/dc/terms/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>

SELECT  ?DatasetTitle  ?Publisher ?ResourceDescription 
WHERE { graph ?g  {?DatasetURI    a        dcat:Dataset; 
                   dc:publisher   ?Publisher; 
                   dc:title ?DatasetTitle; 
                   dc:language ?lang;
                   dc:modified ?mod;
                   dcat:distribution ?Resource. 
                   ?Resource dc:description ?ResourceDescription. 
        FILTER (regex(?DatasetTitle,"covid", "i")) 
      }
  } LIMIT 10

## Experiment : https://data.europa.eu/euodp/fr/linked-data

"""

        
        return rqt

    def updatePrepare(self):
          """ select files to be loaded from remote. Loading is done only if
                1)  file on remote ( as indicated in the periodically reloaded/otherwise 
                     cached)    is newer than local file
                2) file does not exist locally

              preparatory information is stored in attribute `updtList`
          """
          if not hasattr(self,"dataQuery"):
              print("No meta data available in self.dataQuery, update preparation impossible")
              raise RuntimeError("no meta information (RDF form) in self.dataQuery")
              # self.updtList = None          #kept from more permissive times ?
              # return None

          inStore =  sorted([  k   for k in self.genDir.values()])
          updtList=[]

# this shows the format of what we have to assemble
#          updtList.append( { 'reason':reason,'fname':fname, 'url':url, 'org':org,
#                                     'checksum':checksum, 'format': format,
#                                     'modDate':modDate,'cachedDate':fdate,
#                                     'filesize':filesize,'genKey': gen } )
          
          self.updtList = updtList

if False:          

          for indata in self.data['data']:
              for resources in indata['resources']:
                  fname   = resources['title']
                  url     = resources['latest']
                  checksum   = resources['checksum']
                  format     = resources['format']
                  modDate = resources['last_modified']
                  filesize= resources['filesize']
                  org     = indata['organization']['slug']
                  if format is None:
                      print(f"Skipping '{fname}' fmt:{format} mod:{modDate} org='{org}'")
                      continue
                  genDate = self.makeGenDate(fname)
                  if genDate is None:
                      gen,fdate = (None,None)
                      reason="ifAbsent"         # no generic id:filename without timestamp
                  else:
                      gen,fdate  = genDate
                      if gen in self.genDir:
                          reason="ifNewer"
                      else:
                          reason="noLocalCopy"
                  
                  updtList.append( { 'reason':reason,'fname':fname, 'url':url, 'org':org,
                                     'checksum':checksum, 'format': format,
                                     'modDate':modDate,'cachedDate':fdate,
                                     'filesize':filesize,'genKey': gen } )
          self.updtList = updtList


          
