# -*- coding: utf-8 -*-
#

__author__ = 'Alain Lichnewsky'
__license__ = 'MIT License'
__version__ = '1.1'

from lib.DataMgr import *

class manageAndCacheDataFilesJSON(  manageAndCacheDataFiles):
    defaultOpts = {
           'cacheFname'   :  ".cache.json",
           'httpTimeOut'  :  1
    }
    def __init__(self, dirpath,**kwdOpts ):
        """
         Arguments:
               - `HttpHDR` : header of http command, see your http API
               - `ApiInq`  : API argument
                 'ApiHeaders'   :  Extra Headers,
               - `InqParmsDir` : dict with command API parameters
               - `maxImportSz` : 5 Mb: max size of individual file load
               - `maxDirSz`    : 50 Mb: max total cache directory size (.cache file
                                 storing meta data is not accounted for systematically)
        """
        manageAndCacheDataFiles.__init__(self, dirpath=dirpath)
        # by now, the base class initializer has obtained the local filesys information
        setDefaults(self.options, kwdOpts, manageAndCacheDataFilesJSON.defaultOpts)
        
    def _getRemoteMetaFromServer(self):
          if 'HttpRQT' in self.options and  self.options['HttpRQT'] != 'POST': 
              url = "/".join( map (lambda x:self.options[x],('HttpHDR','ApiInq')))
              resp = requests.get(url=url, params=self.options['InqParmsDir'],
                                  timeout= self.options['httpTimeOut'])
          else:
              url = "/".join( map (lambda x:self.options[x],
                                   ( x for x in ('HttpHDR','ApiInqHdr','ApiInq')
                                        if x in self.options  )))
              resp = requests.post(url=url, headers=self.options[ 'ApiHeaders' ], 
                                   params=self.options['InqParmsDir'],
                                   timeout= self.options['httpTimeOut'])              
          cde =resp.status_code
          cdeTxt = requests.status_codes._codes[cde][0]

          # will return OK even if thing does not exist
          if cde >= 400:
               print(f"URL/request={resp.url}\tStatus:{cde}:{cdeTxt}")
               print(f"Request to get remote information failed, {self.options['cacheFname']} may be stale")
               return
          print(f"URL/request={resp.url}\tStatus:{cde}:{cdeTxt}")

          self.data = resp.json()
          self.metadata["data:type"] =  "python/json"

    _resourceList = ('title','latest','last_modified', 'format', 'checksum' )
    def pprintDataResources(self, bulk=False) :
          """ Pretty print selected information on files from the json; if parameter
              `bulk` is True, the full json information is also shown

              Need to consider the case where we have not been able to load the metadata
          """
          if not hasattr(self,"data"):
              print("No meta data available, pretty print impossible")
              return

          prettyPrinter = pprint.PrettyPrinter(indent=4)
          fileList=[]
          resourceSet = set()
          
          for indata in self.data['data']:
              for resources in indata['resources']:
                  resourceDict = {}
                  resourceSet |= set(resources.keys())
                  resourceDict.update({ x:resources[x]
                                        for x in  manageAndCacheDataFiles._resourceList})
                  resourceDict.update({'orgSlug':indata['organization']['slug']})
                  fileList.append(resourceDict)
                  resourceSet |=  set(('organization:slug',))

          print(f"There are {len( self.data['data'])} elts/organizations")
          print(f"      for a total of {len(fileList)} entries")

          if bulk:
              print("BULK DATA "+"** "*12 + "BULK DATA")
              print(prettyPrinter.pformat(self.data))
          print("++ "*12)
          print(f"Potential resources : {prettyPrinter.pformat(sorted(resourceSet))}")
          print(prettyPrinter.pformat(fileList))
          print("++ "*12+"\n")


      
class manageAndCacheDataFilesFRDG(  manageAndCacheDataFilesJSON):
    """ Manage a local repository extracted from www.data.gouv.fr:
        - extraction of the  list of files based on criteria conforming to
          the www.data.gouv.fr API
        - provided by base class:  caching,  local copies,

        For now examples are shown in the test section at end of file (`test_remote`)
    """
    defaultOpts = {'HttpHDR'      : 'https://www.data.gouv.fr/api/1',
                   'ApiInq'       : 'datasets',
                   'ApiHeaders'   : {},
                   'InqParmsDir'  : {"badge":"covid-19", "page":0, "page_size":30},
                   'CacheValidity':  12*60*60,  #cache becomes stale after 12 hours
                   'maxImportSz'  :  5*(2**10)**2,  #5 Mb: max size of individual file load
                   'maxDirSz'     :  50*(2**10)**2,  #50 Mb: max total cache directory size
                  }

    def __init__(self, dirpath,**kwdOpts ):
        """
         Arguments:
               - `HttpHDR` : header of http command, see your http API
               - `ApiInq`  : API argument
                 'ApiHeaders'   :  Extra Headers,
               - `InqParmsDir` : dict with command API parameters
               - `maxImportSz` : 5 Mb: max size of individual file load
               - `maxDirSz`    : 50 Mb: max total cache directory size (.cache file
                                 storing meta data is not accounted for systematically)
        """
        if not hasattr(self, "options"):
            self.options={}
        setDefaults(self.options, kwdOpts, manageAndCacheDataFilesFRDG.defaultOpts)
        manageAndCacheDataFilesJSON.__init__(self, dirpath=dirpath)
        # by now, the base class initializer has obtained the local filesys information
        setDefaults(self.options, kwdOpts, manageAndCacheDataFilesFRDG.defaultOpts)

    def pprintDataItem(self, item="description", showVals=True) :
          """ Pretty print selected information on files from the json.
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
              identifiers where the first field matches the first identifier,... etc
              B)When a set delimited by '$$' is used:
                  i)  the first matches an item, if not found, we stop here
                  ii) the search at same level is performed for all items that match
                      the second item
                  iii) for each the value associated with each item in ii) is screened
                      with the third pattern.
 
              See examples in derived classes
          """
          self.dataTopLev="data"
          self._pprintDataItem(item=item , showVals=showVals)

        
class manageAndCacheDataFilesEU(  manageAndCacheDataFilesJSON):
    """ Manage a local repository extracted from www.data.gouv.fr:
        - extraction of the  list of files based on criteria conforming to
          the www.data.gouv.fr API
        - provided by base class:  caching,  local copies,

        For now examples are shown in the test section at end of file (`test_remote`)
    """
    defaultOpts = {'HttpRQT'      :  "POST",
                   'HttpHDR'      : 'https://data.europa.eu/euodp/',
                   'ApiInqHdr'    : 'data/apiodp/action',
                   'ApiInq'       : 'package_search',
                   'ApiHeaders'   :  {"accept": "application/json",
                                      "Content-Type":"application/json"},
                   'InqParmsDir'  : {"q":"covid","rows":20},
                   'CacheValidity':  12*60*60,  #cache becomes stale after 12 hours
                   'maxImportSz'  :  5*(2**10)**2,  #5 Mb: max size of individual file load
                   'maxDirSz'     :  50*(2**10)**2,  #50 Mb: max total cache directory size
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
        manageAndCacheDataFilesJSON.__init__(self, dirpath=dirpath)
        # by now, the base class initializer has obtained the local filesys information
        setDefaults(self.options, kwdOpts, manageAndCacheDataFilesEU.defaultOpts)

    def pprintDataItem(self, item="description", showVals=True) :
         """ Pretty print selected information on files from the json.
              Item syntax is <field>('/'<field>)+, where each field is either a
              plain string or a regular expression for module `re`.
              - a regexp is recognized by including one of the characters '*+()'
              - '/' is reserved as a field separator, must not be used inside a field
              - a field which is not a regexp will be matched using equality
              
              Item matches the first substructure accessed by a list of nested
              identifiers where the first field matches the first identifier,... etc

              Concerning the arrangement of information from the EU portal,
              - The API is at "https://data.europa.eu/euodp"
              - useful information is found at 
	        -- https://data.europa.eu/euodp/fr/developerscorner
                -- https://app.swaggerhub.com/apis/EU-Open-Data-Portal/eu-open_data_portal/0.8.0#/admin/packageSearchPost
                -- https://www.datacareer.de/blog/eu-open-data-portal-api/

              See examples in the test section.               
         """
         self.dataTopLev="result"
         self._pprintDataItem(item = item, showVals = showVals ) 

            
         
    def pprintDataResources(self, bulk=False, **keywds) :
          """ Pretty print selected information on files from the json; if parameter
              `bulk` is True, the full json information is also shown

              Need to consider the case where we have not been able to load the metadata
          """
          if not hasattr(self,"data"):
              print("No meta data available, pretty print impossible")
              return

          prettyPrinter = pprint.PrettyPrinter(indent=4)
          fileList=[]
          resourceSet = set()
          for key in sorted(self.data.keys()):
              print(f"'{key}'\t-> type(@):{type(self.data[key])}")

          if 'help' in keywds and keywds['help'] and "help" in self.data:
             if isinstance( self.data['help'] , Iterable):
                 for el in  self.data['help']:
                     sys.stderr.write(el)
             else:
                 sys.stderr.write( self.data['help'])
                 
          for kwd in ('success',):
              print (f"\nContents for {kwd}")
              if kwd in keywds and keywds[kwd] and kwd in self.data:
                  print(prettyPrinter.pformat(self.data[kwd]))

          if 'result' in keywds and keywds['result'] and "result" in self.data:
               res = self.data['result']
               print(f"type(self.data['result']) ={type(res)}" )
               if isinstance(res,dict):
                       print ( f"self.data['result'] keys: {sorted(res.keys())}" )
               else:
                   raise RuntimeError(f"Unexpected type for data: {type(res)}, (dict required)")
          
