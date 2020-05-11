# -*- coding: utf-8 -*-
#

__author__ = 'Alain Lichnewsky'
__license__ = 'MIT License'
__version__ = '1.1'

from   lib.utilities import *
import requests, sys, pprint, pickle, time, shutil
from   collections   import Iterable, Mapping
import urllib, hashlib

import pandas 		 as 	PAN

from rdflib import Graph, Literal, BNode, Namespace,  RDF, URIRef
from rdflib.namespace import NamespaceManager

from lib.DataMgr import *
import lib.RDFandQuery as RDFQ
import lib.RdfEU       as RDFEU

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
          # For now, increase limit, and see what happens
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

          query = self._buildRemoteSparql()

          hasher = hashlib.sha256()
          self.metadata["HTTP:Query:Sparql"]=query
          hasher.update(query.encode('utf-8'))
          self.metadata["HTTP:Query:sha256"]= hasher.hexdigest()
          
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
        qhashFn = None
        if "cachefileRDF" in self.options:
            ofn =  self.options["cachefileRDF"]
        elif "cacheFname" in self.options:
            spl = os.path.splitext(self.options["cacheFname"])
            ofn = os.path.join(self.dirpath, spl[0]+".prdf" )
            qhashFn =  os.path.join(self.dirpath, spl[0]+".qhash" )
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
            if qhashFn is not None:
                with open(qhashFn,"w") as qhFile:
                    qhFile.write("QUERY:HASH-SHA256\n")
                    qhFile.write(self.metadata["HTTP:Query:sha256"])
                    qhFile.write("\n")              
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
        if not hasattr(self, "options"):
            self.options={}
        setDefaults(self.options, kwdOpts, manageAndCacheDataFilesRdfEU.defaultOpts)        
        manageAndCacheDataFilesRDF.__init__(self, dirpath=dirpath)
        # by now, the base class initializer has obtained the local filesys information
        setDefaults(self.options, kwdOpts, manageAndCacheDataFilesRdfEU.defaultOpts)
               

    def _buildRemoteSparql(self):
        """ Build SPARQL that will be shipped to remote site via protocol supported by
            OAI / OpenAPI-Specification  (https://github.com/OAI/OpenAPI-Specification/)


            *Note* : specifications in 
            `https://www.w3.org/TR/vocab-dcat/#Property:resource_update_date` apply to
             the EU euodp site. In particular:
                - 6.4.8 Property: update/modification date

                  An absent value MAY indicate that the item has never changed after its 
                  initial publication, or that the date of last modification is not known,
                  **or that the item is continuously updated**.

                  Concerning frequency, see 
                       - 6.6.2 : Property: frequency see dct:accrualPeriodicity
        	       - 9.1   : Temporal properties
        """
        # prepare for handling request customization
        print(f"In {self.__class__}._buildRemoteSparql\t available options:\n\t{sorted(self.options.keys())}")

        # for now a boiler plate request
        # to experiment : https://data.europa.eu/euodp/fr/linked-data
        rqt = """
PREFIX http: <http://www.w3.org/2011/http#>
PREFIX dcat: <http://www.w3.org/ns/dcat#>
PREFIX odp:  <http://data.europa.eu/euodp/ontologies/ec-odp#>
PREFIX dc: <http://purl.org/dc/terms/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>

SELECT distinct ?g ?title ?dsURI ?DatasetTitle ?Publisher ?dloadurl ?lang ?issue ?mod ?source ?sz ?frequency ?rissue ?fmt ?Resource ?ResourceDescription 
WHERE { GRAPH ?g { filter regex(?title, 'COVID', 'i'). 
                   FILTER langMatches( lang(?title), "EN" ).
                   ?dsURI    a        dcat:Dataset.
                   ?dsURI    dc:title ?title .
                   ?dsURI    dc:publisher   ?Publisher . 
                   ?dsURI    dc:title ?DatasetTitle . 
                   OPTIONAL { ?dsURI    dc:accrualPeriodicity   ?frequency . }
                   OPTIONAL { ?dsURI    dc:language ?lang. }
                   OPTIONAL { ?dsURI    dc:modified ?mod. }    # rare
                   OPTIONAL { ?dsURI    dc:issued   ?issued. }  # rare
                   ?dsURI    dcat:distribution ?Resource.
                   OPTIONAL { ?Resource dc:description ?ResourceDescription. }
                   OPTIONAL { ?Resource  dcat:downloadURL ?dloadurl. }
                   OPTIONAL { ?Resource  dcat:byteSize ?sz. }
                   OPTIONAL { ?Resource  dc:format     ?fmt . }
                   OPTIONAL { ?Resource  dc:issued     ?rissue. }
        }  
} 
  ORDER BY ?mod ?title ?fmt
  LIMIT 200
  OFFSET 0
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
 
          inStore =  sorted([  k   for k in self.genDir.values()])

          queryBuild = QueryBuildFindDownloads( nmgr=self.dataQuery.NMgr )
          query      = queryBuild.build()

          if  "debug" in self.options and  self.options["debug"]:
              print(f"About to query local db with SPARQL:\n{query}")

          queryReturns = self.dataQuery.query(query)

          if  "debug" in self.options and  self.options["debug"]:
              queryBuild.showReturns(queryReturns) 

          self.metaTable = queryBuild.tabulate(queryReturns)
          self.metaTable.columns = map(lambda x:str(x), self.metaTable.columns)
          self._mkUpdtlistFromTbl()

    _updtEntryFlds = ('reason', 'fname', 'url', 'org', 'checksum', 'format',
                         'modDate', 'cachedDate', 'filesize', 'genKey', 'frequency')
          
    def _mkUpdtlistFromTbl(self):
        # this shows the format of what we have to assemble
        #          updtList.append( { 'reason':reason,'fname':fname, 'url':url, 'org':org,
        #                                     'checksum':checksum, 'format': format,
        #                                     'modDate':modDate,'cachedDate':fdate,
        #                                     'filesize':filesize,'genKey': gen } )
        updtList = []
        mtable = self.metaTable.copy()
        
        #iterate over portions of table pertaining to same download URL
        gb = mtable.groupby('dloadurl')
        for (url,dfExtract) in gb:
            updtEnt = { x:None for x in manageAndCacheDataFilesRdfEU._updtEntryFlds}
            updtEnt['url'] = str(url)

            fn    = dfExtract['dsURI'][0].split("/")[-1]
            ftype = dfExtract['fmt'][0].split("/")[-1].lower()
            updtEnt['fname']  = fn + '.' + ftype
            updtEnt['genKey']  = fn + '.' + ftype
            updtEnt['format'] = ftype

            updtEnt['org']   =  str( dfExtract['Publisher'][0] )

            if "frequency" in  dfExtract.columns:
                x =  dfExtract['frequency'][0]
                qn = self.dataQuery.NMgr.qname(x)
                updtEnt['frequency'] = qn.split(':')[-1]
                reason = UpdateRqt.ReasonCde.FreqObsolete
            else:
                qn = None
                reason = UpdateRqt.ReasonCde.NoGeneric
            if "mod" in  dfExtract.columns:    
                mod =  dfExtract['mod'][0]
            else:
                mod = None
            print(f"qn='{qn}'\tmod={mod}")

            updtEntry =  UpdateRqt( reason,  updtEnt )
            updtList.append(updtEntry)
        
        
# ? reasons : "ifAbsent"  : no generic id:filename stripped of timestamp
#             "ifNewer"   : remote file is newer
#             "noLocalCopy": no file on board
# 
# * fname   : local file name
# * url     : download url
# * format  :
#   modDate :     rarely avail
#   cachedDate:   apparently unused at this point, could be date of file
#   org:Publisher
#   checksum : None
#   filesize: sz when avail ?
# * genKey : filename stripped of timestamp
        
        self.updtList = updtList
          

class QueryBuilder(object):
    """ A class to facilitate building queries against the RDF, will use subclasses
        for specialization/parametrization
    """
    def __init__(self, **kwdOpts):
        if "nmgr" in kwdOpts:
            self.NMgr = kwdOpts["nmgr"]
            if not isinstance( self.NMgr, NamespaceManager):
                raise RuntimeError(f'Bad type for arg nmgr: {type(self.NMgr)}')            
            
    def build(self):
        self.q =  QueryBuilder.pfxHdr + self._q
        return self.q

    def showReturns(self, returned):
          print(f"Query returned {len(returned)} entries")
          for x in returned:
              print(x)
              
    def tabulate(self, returned):
        """ return the query results in the form of a Panda.DataFrame
        """
        raise NotImplementedError("This method must be defined in a derived class")
    
    pfxHdr = """
PREFIX http: <http://www.w3.org/2011/http#>
PREFIX dcat: <http://www.w3.org/ns/dcat#>
PREFIX xsd:  <http://www.w3.org/2001/XMLSchema#>
PREFIX rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX res:  <http://www.w3.org/2005/sparql-results#>
PREFIX odp:  <http://data.europa.eu/euodp/ontologies/ec-odp#>
PREFIX dc:   <http://purl.org/dc/terms/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX N:    <http://localhost/added>
PREFIX X2R:  <http://localhost/XMLattToRDF>
"""

class QueryBuildFindDownloads(QueryBuilder):
    def __init__(self, **kwdOpts):
         QueryBuilder.__init__(self, **kwdOpts)
         self.q =  QueryBuildFindDownloads._q

    _q = """   # Walk solution sets from the top
SELECT distinct ?solNodeId ?bindId ?varname ?value  ?pred ?pvalue
WHERE { ?parent  res:solution        ?sol .
        ?sol     X2R:nodeID          ?solNodeId.
        ?sol     res:binding         ?bind .
        ?bind    X2R:nodeID          ?bindId.
        ?bind    res:variable        ?var  .
        ?var     N:text              ?varname .
        ?bind    res:value           ?val .
        ?val     ?pred               ?pvalue .
        OPTIONAL { ?val     N:text              ?value . }

        # The following constrains to entries which have a downloadURL
        ?sol     res:binding         ?chkBind.
        ?chkBind res:variable        ?chkVar.
        ?chkVar  N:text              ?chkVarname . 
        FILTER   regex(?chkVarname,'^(dloadurl)$','i') .
} 
  ORDER BY ?solNodeId ?bindId ?varname ?value ?pred ?pvalue
"""


    def tabulate(self, returned):
        """ return the query results in the form of a Panda.DataFrame
        """
        curSolNId = None
        curBindId = None
        df = PAN.DataFrame()

        rowAsDict = {}
        for r in returned:
            solNodeId, bindId, varname, value,  pred, pvalue  = r

            if solNodeId != curSolNId:
                if len(rowAsDict) != 0:
                    df = df.append(rowAsDict, ignore_index=True)
                curSolNId = solNodeId
                rowAsDict = {}

            qn = self.NMgr.qname(pred)
            if qn == 'rdf:type':
                    continue
            col = varname
            if col in rowAsDict or qn not in  ("N:text", "X2R:resource" ):
               qns = qn.split(":")[-1]
               col = varname+"@"+qns
               
            rowAsDict[col] = pvalue

        if len(rowAsDict) != 0:
            df = df.append(rowAsDict, ignore_index=True)

        return df
    

  



  
