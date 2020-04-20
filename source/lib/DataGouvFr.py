'''
 Facilitate the use of data from  https://www.data.gouv.fr

1) For downloaded files:
 
 Deals with the fact that the site exports/downloads files with filenames 
 containing date/timestamp information; this module permits to check/load 
 the latest version.

 Expectations:
    - local copies of relevant files are in a local directory

2) For direct/automated access to the site via its http API
    - files are downloaded from the www.data.gouv.fr site; local copies are
      made of the most recent versions. Directory of loaded information is
      kept locally, and refreshed after a prescribed duration
    - the remote site is checked for updates after a prescribed duration

TBD:
   - manage the local data directory as a cache
   - permit to access the descriptive information pertaining the cached files
   - documentation (wishful thinking?), also format so that doxygen output is
     nicer
'''

__author__ = 'Alain Lichnewsky'
__license__ = 'MIT License'
__version__ = '1.0'

from   lib.utilities import *
import requests, sys, pprint, pickle, time, shutil
from   collections   import Iterable, Mapping
import urllib, hashlib

class manageDataFileVersions(object):
    """ For each file name in local directory, find which are different versions of same as 
        indicated in the file name with pattern yyyy-mm-dd-HHhMM. 

    """
    def __init__(self, dirpath ):
        """
        Argument "dirpath" is compulsory, must designate a directory where local copies
                 of files will be / are cached. There is no default on purpose to
                 avoid unintentional tampering.
        """
        self.dirpath = dirpath
        if not os.path.isdir(dirpath):
            raise RuntimeError(f"Path {dirpath} not directory")
        self.options = {}
        self._walk()

    datedFileRex = re.compile(
             """^(?P<hdr>.*[^\d])
               (( (?P<year>\d+)-(?P<month>\d+)-(?P<day>\d+)    # Year
                -(?P<hour>\d+)[h-](?P<minute>\d+)             # Time
               )|
                 ( (?P<pYear>\d{4})(?P<pMonth>\d{2})(?P<pDay>\d+) # Year yyyymmdd
                  -(?P<pTime>\d{6})                     # Time in format hhmmss (*)
               ))
              (?P<ftr>.*)$
             """,
        re.VERBOSE)    

    #  (*) : format observed when downloading  from
    #        https://doc.data.gouv.fr/api/telecharger-un-catalogue-de-donnees/
    #
    #
    
    def _walk(self):
        """ (internal)
            Walk the file in the dirpath directory (no support for
            nested dirs at this point). Fill the filDir/genDir 
            directories where:
               - gendir is indexed by filenames with removed timestamps (gen),
		        permits access to most recent version
               - fildir is indexed by filename, gives access to gen and date
        """
        lfiles = os.listdir(self.dirpath)
        filDir={}
        genDir={}
        for lf in lfiles:
               genDate = self.makeGenDate(lf)
               if genDate is None: continue
               (gen,date) = genDate
               filDir[lf]=(gen,date)
               fpath = os.path.join( self.dirpath, lf)
               if (not gen in genDir) or ( date > genDir[gen][0] ):
                   genDir[gen] = (date,lf,fpath)

        self.filDir = filDir
        self.genDir = genDir

    def makeGenDate(self,filename):
            """Returns generic filename and file date if file name has std datestamp, 
              None otherwise
            """
            mobj = manageDataFileVersions.datedFileRex.match(filename)
            if mobj:
               gdict = mobj.groupdict()
               if 'pTime' in gdict and gdict['pTime']:
                   fls = list( int(gdict[z]) for z in  ('pYear', 'pMonth', 'pDay'))
                   hms = gdict['pTime']
                   fls.extend( map ( lambda x: int(hms[x:(x+2)]), (0,2,4)))
               else:
                   fls = ( int(gdict[z]) for z in  ('year', 'month', 'day','hour','minute'))
               date = datetime.datetime( *fls )
               gen  =  "!".join(map (lambda x: gdict[x] , ("hdr","ftr")))
               return (gen,date)
            else:
                return None
               
    def listMostRecent(self):
        """
            Returns sorted list of files which are in  the `dirpath` directory, 
            and which represent the most recent version of files with timestamps in the
            filename (we do not look into file attributes).
        """
        return sorted([  k[1]   for k in self.genDir.values()])
    
    def getRecentVersion(self,file, default=None):
        """
          Return the most recent name of a file; if not found will raise
          an exception unless a default is given
        """
        if file not in self.filDir:
            if not default:
               raise RuntimeError(f"Unexpected file:'{file}'")
            elif default is True:
                return file
            else:
                return default
        else:
                return self.genDir[self.filDir[file][0]][1]

class manageAndCacheBase(manageDataFileVersions):

    def __init__(self, dirpath,**kwdOpts ):
        manageDataFileVersions.__init__(self, dirpath=dirpath)
    
    def getRemoteInfo(self, localOnly=False):
        """ Load the information describing files on the remote site, either
            from a local cached copy (in file .cache), or by reloading after the 
            elapsed time specified by 'CacheValidity'

            Parameter localOnly specifies that remote cache should not be consulted
        """
        cacheValid = self._getFromCache(localOnly=localOnly)
        if not ( localOnly or cacheValid ):
             self._getRemoteProper()

    def _spaceAvail(self, dirpath) :
         """ Check the available space in the cache (`dirpath`) where data can be 
             stored, taking ̀maxDirSz` into account.
         """
         used = spaceUsed(dirpath)
         return self.options['maxDirSz'] - used

    def  cacheUpdate(self):
          """ Load files from remote if
                1)  file on remote ( as indicated in the periodically reloaded/otherwise 
                     cached)    is newer than local file
                2) file does not exist locally

              preparatory information is stored in attribute `updtList`, may be 
              None if it has not been posible to access the metadata on the remote
              server.
          """
          if  self.updtList is None:
              print (f"update of cache not possible, missing metadata and/or updt list")
              return None
          
          return self._cacheUpdate(effector=self._getFromRemote)
          
    def  verifyForCacheUpdate(self):
          self._requiredDiskSz = 0
          self._cacheUpdate(effector=self._sizeAccounter)
          if self._requiredDiskSz > 0:
              pass

    cacheUpdtTimeRex = re.compile("""^
        (?P<year>\d+)-(?P<month>\d+)-(?P<day>\d+)         # Year
       .(?P<hour>\d+):(?P<minute>\d+):(?P<seconde>\d+)    # Time
         """, re.VERBOSE) 
    def _cacheUpdate(self, effector):
          """ (internal) 
                Run the updtList, pass to the effector method entries that should
                be loaded. 
                There are 2 alternative effectors:
                  -  self._getFromRemote: actually obtains and stores the file
                  -  self._sizeAccounter: accumulates in self._requiredDiskSz the
                  required disk size to load all the files

                Condition for loading a file:
                1)  file on remote ( as indicated in the periodically reloaded/otherwise 
                     cached)    is newer than local file
                2) file does not exist locally
          """
          updtList = self.updtList
          for entry in updtList:
              #print(f"ENTRY={entry}")
              if entry['reason'] == "noLocalCopy":
                  effector(None, **entry)

              elif entry['reason'] == "ifAbsent":
                  fname=os.path.join(self.dirpath,entry['fname'])
                  if not os.path.exists(fname):
                     effector(None, **entry)      

              elif entry['reason'] == "ifNewer":
                  genEntry = self.genDir[entry['genKey']]
                  fname = genEntry[2]
                  mtime = os.path.getmtime(fname)
                  mtimeDT = datetime.datetime.fromtimestamp(mtime)
                  mobj = manageAndCacheDataFiles.cacheUpdtTimeRex.match(entry['modDate'])
                  if mobj:
                     fls = ( int(mobj.groupdict()[z])
                             for z in  ('year', 'month', 'day','hour','minute', 'seconde') )
                     remoteDT = datetime.datetime( *fls )
                  else:
                     raise RuntimeError(f"cannot parse date /{entry['modDate']}/")
                  if mtimeDT < remoteDT - datetime.timedelta(minutes=5):
                       effector(remoteDT, **entry)

              else:
                  raise RuntimeError(f"Bad reason code: {entry['reason']}")
        
    def _getFromRemote(self,remoteDT,
                            reason=None,fname=None, url=None, org=None, checksum=None,
                            format=None, modDate=None, cachedDate=None,
                            filesize=None, genKey=None):
         """ (internal) read from remote using API/http protocol
         """
         if remoteDT is None:
             print(f"remoteDT is None for reason:{reason} fname:{fname}\n!! !!")
         fullPathname = os.path.join(self.dirpath,fname)
         with urllib.request.urlopen(url) as furl :
              with open(fullPathname,"wb") as fwr : 
                   fwr.write(furl.read())
         print(f"Wrote file \t'{fullPathname}'\n\tfrom URL:'{url}'")

         chk = self. verifChecksum(fullPathname,checksum)
         if chk:
            # update the internal database (useful if same file encountered several times
            # with different timestamps) 
            self.filDir[fname]=(genKey,remoteDT)
            self.genDir[genKey] = (remoteDT, fname, fullPathname) 

            #print(f"FILDIR:{self.filDir}")
            #print(f"GENDIR:{self.genDir}")
         return chk
         
    def verifChecksum(self, filpath, checksum):
        """ (internal) verify the checksum if provided from remote (loaded dir. info)
        """
        if checksum == None:
            return
        if any(map( lambda x: not x in checksum, ('type','value'))):
            print(f"Type or value entry missing/incorrect in checksum:{checksum}")
            return False
        
        hashType=checksum['type']
        if hashType not in hashlib.algorithms_available:
            print(f"Checksum algorithm not available: {hashType} (avail={hashlib.algorithms_available})")
            return False
        
        hasher = hashlib.new(hashType)
        with open(filpath,"rb") as fread : 
                   hasher.update(fread.read())
        hashcode = hasher.hexdigest()

        hOK = hashcode == checksum['value']
        if not hOK:
            print(f"Bad checksum for {filpath} comp:{hashcode} reference:{checksum['value']}")
        return hOK
    
    def _sizeAccounter(self,remoteDT,
                            reason=None,fname=None, url=None, org=None, checksum=None,
                            format=None, modDate=None, cachedDate=None, genKey=None,
                            filesize=None):
         """ (internal) read from remote using API/http protocol
         """
         pass
     
class manageAndCacheDataFiles( manageAndCacheBase):
    """ Manage a local repository extracted from www.data.gouv.fr:
        - extraction of the  list of files based on criteria conforming to
          the www.data.gouv.fr API
        - caching of this information, the remote site is consulted only
          after a parametrized delay 
        - for local copies of files, permits to access the most recent version 
          as indicated in base class
        - management of the local cache directory (TBD: remove redundant files)

        For now examples are shown in the test section at end of file (`test_remote`)
    """
    defaultOpts = {'HttpHDR'      : 'https://www.data.gouv.fr/api/1',
                   'ApiInq'       : 'datasets',
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
               - `InqParmsDir` : dict with command API parameters
               - `maxImportSz` : 5 Mb: max size of individual file load
               - `maxDirSz`    : 50 Mb: max total cache directory size (.cache file
                                 storing meta data is not accounted for systematically)
        """
        manageAndCacheBase.__init__(self, dirpath=dirpath)
        # by now, the base class initializer has obtained the local filesys information
        setDefaults(self.options, kwdOpts, manageAndCacheDataFiles.defaultOpts)


    def _getFromCache(self, localOnly):
        """ (internal) Read from the cached file (a pickle of a json)
        """
        cacheFname = os.path.join(self.dirpath, ".cache")
        self.cacheFname = cacheFname
        valid = True
        if not os.path.isfile(cacheFname):
            valid = False
            if localOnly:
                raise RuntimeError(f"No cache ({cacheFname}) to reload information locally")
        else:
            mtime = os.path.getmtime(cacheFname)
            nowtime = time.time()
            elapsed = nowtime - mtime
            strElapsed = time.strftime("%Hh %Mm %Ss", time.gmtime(elapsed))
            if elapsed > self.options['CacheValidity'] and  not  localOnly:
               print(f"Need to reload cache from remote,  stale after {strElapsed}")
               valid = False
        if valid:
               with open(self.cacheFname,"rb") as pikFile:
                  pickler = pickle.Unpickler( pikFile)
                  self.data = pickler.load()
                  print(f"Loaded pickle from {self.cacheFname}, loaded {strElapsed} ago ({len(self.data)} elts)")

        return valid
        
    def _getRemoteProper(self):
          """ Read the metadata on selected files from the remote site, store
              it into the DIRPATH/.cache file, keep it in the self.data attribute as the
              python representation of a json
          """
          spaceAvail = self._spaceAvail(self.dirpath)
          if spaceAvail < 300*(2**10):
              print (f"spaceAvail={spaceAvail}, 300K required,  maxDirSz={self.options['maxDirSz']} ")
              raise RuntimeError(f"Insufficient space in {self.dirpath} to store cached metadata")
          
          url = "/".join( map (lambda x:self.options[x],('HttpHDR','ApiInq')))
          resp = requests.get(url=url, params=self.options['InqParmsDir'])
          cde =resp.status_code
          cdeTxt = requests.status_codes._codes[cde][0]

          # will return OK even if thing does not exist
          if cde >= 400:
               print(f"URL/request={resp.url}\tStatus:{cde}:{cdeTxt}")
               print("Request to get remote information failed, self.cacheFname may be stale")
               return
          print(f"URL/request={resp.url}\tStatus:{cde}:{cdeTxt}")

          self.data = resp.json()
          
          with open(self.cacheFname,"wb") as pikFile:
                  pickler = pickle.Pickler( pikFile)
                  pickler.dump(self.data)
                  print(f"Stored pickle in {self.cacheFname}")

          
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

    ppItemRex = re.compile("[*+()]")
    def pprintDataItem(self, item="description") :
          """ Pretty print selected information on files from the json.
              Item syntax is <field>('/'<field>)+, where each field is either a
              plain string or a regular expression for module `re`.
              - a regexp is recognized by including one of the characters '*+()'
              - '/' is reserved as a field separator, must not be used inside a field
              - a field which is not a regexp will be matched using equality
              
              Item matches the first substructure accessed by a list of nested
              identifiers where the first field matches the first identifier,... etc

              See examples in the test section.
               
          """
          def tryReCompile(s):
              retval = s
              if manageAndCacheDataFiles.ppItemRex.search(s):
                  try:
                    retval =  re.compile(s)
                  except Exception as err:
                      print(f"Rejected regexp:'{s}': {err}")
                      retval = s
              return retval

          def matchIfRex(spec,x):
              if isinstance(spec,str):
                  retval = spec == x
              else:
                  retval = spec.match(x) != None
              return retval
              
          if not isinstance(item,str):
              raise RuntimeError(f"Parm item is not string: {type(item)}")

          def recurse(specList, jsonSubList, prettyPrinter, prefix=[], rid=[]):
              #print(f"\nIn recurse specList={specList} prefix={prefix}")
              recnum = 0
              skip=False
              zskip={False:"",True:"\n"}
              for jsonDict in jsonSubList:
                  if isinstance(jsonDict,str):
                      print(f"{':'.join(prefix)}:({'.'.join(rid)}):>>>"+prettyPrinter.pformat( jsonDict))
                      return
                  spec =  specList[0]
                  if isinstance(spec,str) and spec in jsonDict:
                      dolist = (spec,)
                  elif isinstance(jsonDict,dict):
                      dolist=list( filter ( lambda x:  matchIfRex(spec,x),
                                            sorted(jsonDict.keys())))
                  elif jsonDict is None:
                      print(f"{':'.join(prefix)}\t->\t None")
                      return
                  elif isinstance(jsonDict, Iterable):
                        dolist= (spec,)
                  else:
                      print(f"Weird jsonDict: {type(jsonDict)}\t->{jsonDict}")
                      return

                  r=rid.copy()
                  r.append(str(recnum))
                  recnum+=1
                  skip = True
                  
                  for el in dolist:
                      if isinstance(jsonDict,dict):
                          if el in  jsonDict:
                              json =  jsonDict[el]
                              if len (specList) == 1:
                                 print(f"{zskip[skip]}{':'.join(prefix)}::{el}>@({'.'.join(r)})\t->\t"+prettyPrinter.pformat( json ))
                                 if skip:
                                     skip=False
                                                                 
                              elif  len (specList) > 1:
                                 pfx = prefix.copy()
                                 pfx.append(el)
                                 if isinstance(json,list):
                                    recurse(specList[1:], json, prettyPrinter, prefix=pfx, rid=r)
                                 else:    
                                    recurse(specList[1:], [json], prettyPrinter, prefix=pfx,rid=r)
                                 #print(f"{'--'.join(prefix)}@@")
                      else:
                          for lstEl in jsonDict:
                              for kl  in lstEl.keys():
                                  if el == kl or el.match(kl):
                                      raise RuntimeError(f"\tDo something for {kl}")
                      #print(f"{'+++'.join(prefix)}##")

                                  
          prettyPrinter = pprint.PrettyPrinter(indent=4)
          itemList = list( map ( tryReCompile, item.split("/")))
          recurse(itemList, self.data['data'],prettyPrinter )

          
    def updatePrepare(self):
          """ select files to be loaded from remote. Loading is done only if
                1)  file on remote ( as indicated in the periodically reloaded/otherwise 
                     cached)    is newer than local file
                2) file does not exist locally

              preparatory information is stored in attribute `updtList`
          """
          if not hasattr(self,"data"):
              print("No meta data available, update preparation impossible")
              self.updtList = None
              return None

          inStore =  sorted([  k   for k in self.genDir.values()])
          filStore =  sorted([  k   for k in self.filDir.values()])
          
          updtList=[]
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

class manageAndCacheFilesDFrame( manageAndCacheBase):
    """ Manage a local repository where the meta data comes from a DataFrame (in
        practice loaded from a CSV or an XLS(X)
        - extraction of the  list of files from a csv/xls into panda dataframe
        - for local copies of files, permits to access the most recent version 
          as indicated in base class
        - management of the local cache directory (TBD: remove redundant files)

        For now examples are shown in the test section at end of file (`test_remote`)
    """ 
    defaultOpts = {'CacheValidity':  12*60*60,  #cache becomes stale after 12 hours
                   'maxImportSz'  :  5*(2**10)**2,  #5 Mb: max size of individual file load
                   'maxDirSz'     :  50*(2**10)**2,  #50 Mb: max total cache directory size
                  }
    
    def __init__(self, dirpath,**kwdOpts ):
        """
         Arguments:
               - 'CacheValidity'
               - `maxImportSz` : 5 Mb: max size of individual file load
               - `maxDirSz`    : 50 Mb: max total cache directory size (.cache file
                                 storing meta data is not accounted for systematically)
        """
        manageAndCacheBase.__init__(self, dirpath=dirpath)
        # by now, the base class initializer has obtained the local filesys information
        setDefaults(self.options, kwdOpts, manageAndCacheDataFiles.defaultOpts)

    def getRemoteInfo(self, localOnly=False):
        """ Load the information describing files on the remote site, from a local cached
            copy (in file .cache)
            Parameter localOnly specifies that remote metadata should not be consulted
        """
        raise RuntimeError("Still TBD")
         
if __name__ == "__main__":
    import unittest
    import sys

    class DGTest(unittest.TestCase):
        """ First series of test concerns Covid data 
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
            dataFileVMgr = manageAndCacheDataFiles("../data")
            dataFileVMgr.getRemoteInfo()
            # dataFileVMgr.pprintDataResources(bulk=True)
            dataFileVMgr.updatePrepare()
            dataFileVMgr.cacheUpdate()
            

        def test_pprint(self):
            """ Example of pretty printing of remote/cached information
            """
            dataFileVMgr = manageAndCacheDataFiles("../data")
            dataFileVMgr.getRemoteInfo( localOnly = True)
            dataFileVMgr.pprintDataItem( item="description")

        def test_pprint2(self):
            """ Example of pretty printing of remote/cached information
                Check situation where the `item` calls for  subfields 'name' and 'class'
                of  'organizations'
            """
            dataFileVMgr = manageAndCacheDataFiles("../data")
            dataFileVMgr.getRemoteInfo( localOnly = True)
            dataFileVMgr.pprintDataItem( item=".*org.*/^(name|class)$")

        def test_pprint3(self):
            """ Example of pretty printing of remote/cached information
                Check situation where the `item` calls for  subfields 'name' and 'class'
                of  'organizations'
            """
            dataFileVMgr = manageAndCacheDataFiles("../data")
            dataFileVMgr.getRemoteInfo( localOnly = True)

            dataFileVMgr.pprintDataItem( item="resource.*/(f.*|title.*)")

            
        def test_pprint4(self):
            """ Example of pretty printing of remote/cached information.
                Check situation where the `item` calls for all subfields of
                organizations
            """
            dataFileVMgr = manageAndCacheDataFiles("../data")
            dataFileVMgr.getRemoteInfo( localOnly = True)
            dataFileVMgr.pprintDataItem( item=".*org.*/.*")
            
            
        def test_dump(self):
            """ Example of pretty printing of remote/cached information
            """
            dataFileVMgr = manageAndCacheDataFiles("../data")
            dataFileVMgr.getRemoteInfo( localOnly = True)
            dataFileVMgr.pprintDataResources( bulk = True)


    class DGTestPopDemo(unittest.TestCase):
            
        """ First series of test concerns demographic data 
        """
        defaultPop = {
                   'CacheValidity':  12*60*60,       #cache becomes stale after 12 hours
                   'maxImportSz'  :  2*(2**10)**2,   #5 Mb: max size of individual file load
                   'maxDirSz'     :  100*(2**10)**2,  #100 Mb: max total cache directory size
                  }

        def test_remoteDF(self):
            """ Example using remote information with cached json
            """
            dataFileVMgr = manageAndCacheFilesDFrame("../dataPop", ** DGTestPopDemo.defaultPop)
            dataFileVMgr.getRemoteInfo()
            # dataFileVMgr.pprintDataResources(bulk=True)
            dataFileVMgr.updatePrepare()
            dataFileVMgr.cacheUpdate()

            

    class DGTestRegexp(unittest.TestCase):
            
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
            
            for rexS in rexList:
              rex = re.compile(rexS, re.VERBOSE)
              print(rex)
              for s,verif in  strList:
                  answ = chk(rex,s)
                  print(f"ANSW:\t{answ}\nREF\t{verif}\n")
                  self.assertTrue(similar(answ,verif))
                  
    unittest.main()
    """ To run specific test use unittest cmd line syntax, eg.:
           python3 ../source/lib/DataGouvFr.py   DGTest.test_pprint
                     DGTest
                     DGTestPopDemo DGTestPopDemo
    		     DGTestRegexp
    """

