'''
 Specific setup for files imported from https://www.data.gouv.fr/fr/datasets/...
 
 Deals with the fact that the site features files with filenames containing date
 information; this module permits to check/load the latest version.

 Expectations:
    - local copies of relevant files are in a local directory
    - files can be downloaded from the www.data.gouv.fr site; local copies are
      made of the most recent versions
    - the remote site is checked after a prescribed duration
'''

__author__ = 'Alain Lichnewsky'
__license__ = 'MIT License'
__version__ = '1.0'

from   lib.utilities import *
import requests, sys, pprint, pickle, time
from   collections   import Iterable, Mapping
import urllib, hashlib

class manageDataFileVersions(object):
    """ For each file name in local directory, find which are different versions of same as 
        indicated in the file name with pattern yyyy-mm-dd-HHhMM. 
    """
    def __init__(self, dirpath="../data"):
        "dirpath is path relative current working directory"
        self.dirpath = dirpath
        if not os.path.isdir(dirpath):
            raise RuntimeError(f"Path {dirpath} not directory")
        self.options = {}
        self._walk()

    datedFileRex = re.compile("""^(?P<hdr>.*[^\d])
        (?P<year>\d+)-(?P<month>\d+)-(?P<day>\d+)  # Year
       -(?P<hour>\d+)h(?P<minute>\d+)             # Time
        (?P<ftr>.*)$""", re.VERBOSE)    
    
    def _walk(self):
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
               fls = ( int(mobj.groupdict()[z]) for z in  ('year', 'month', 'day','hour','minute') )
               date = datetime.datetime( *fls )
               gen  =  "!".join(map (lambda x: mobj.groupdict()[x] , ("hdr","ftr")))
               return (gen,date)
            else:
                return None
               
    def listMostRecent(self):
        return sorted([  k[1]   for k in self.genDir.values()])
    
    def getRecentVersion(self,file, default=None):
        if file not in self.filDir:
            if not default:
               raise RuntimeError(f"Unexpected file:'{file}'")
            elif default is True:
                return file
            else:
                return default
        else:
                return self.genDir[self.filDir[file][0]][1]

            
class manageAndCacheDataFiles(manageDataFileVersions):
    """ For a set of remote files, check whether we have a local version which 
        is up to date.
    """
    defaultOpts = {'HttpHDR': 'https://www.data.gouv.fr/api/1',
                   'ApiInqDataset': 'datasets',
                   'InqParmsDir' : {"badge":"covid-19", "page":0, "page_size":30},
                   'CacheValidity':  12*60*60  #cache becomes stale after 12 hours
                  }
    
    def __init__(self, dirpath="../data",**kwdOpts ):
        manageDataFileVersions.__init__(self, dirpath=dirpath)
        # by now, the base class initializer has obtained the local filesys information
        setDefaults(self.options, kwdOpts, manageAndCacheDataFiles.defaultOpts)


    def getRemoteInfo(self):
        # placeholder, need to check if get from cache or remote
        cacheValid = self._getFromCache()
        if not cacheValid:
            self._getRemoteProper()

    def _getFromCache(self):
        cacheFname = os.path.join(self.dirpath, ".cache")
        self.cacheFname = cacheFname
        valid = True
        if not os.path.isfile(cacheFname):
            valid = False
        else:
            mtime = os.path.getmtime(cacheFname)
            nowtime = time.time()
            elapsed = nowtime - mtime
            strElapsed = time.strftime("%Hh %Mm %Ss", time.gmtime(elapsed))
            if elapsed > self.options['CacheValidity']:
               print(f"Need to reload cache from remote,  stale after {strElapsed}")
               valid = false
            else:
               with open(self.cacheFname,"rb") as pikFile:
                  pickler = pickle.Unpickler( pikFile)
                  self.data = pickler.load()
                  print(f"Loaded pickle from {self.cacheFname}, loaded {strElapsed} ago ({len(self.data)} elts)")

        return valid
        
    def _getRemoteProper(self):
          url = "/".join( map (lambda x:self.options[x],('HttpHDR','ApiInqDataset')))
          resp = requests.get(url=url, params=self.options['InqParmsDir'])
          cde =resp.status_code

          # will return OK even if thing does not exist
          cdeTxt = requests.status_codes._codes[cde][0]
          print(f"URL/request={resp.url}\tStatus:{cde}:{cdeTxt}")

          self.data = resp.json()
          print(f"Obtained {len(self.data)} from remote")
          
          with open(self.cacheFname,"wb") as pikFile:
                  pickler = pickle.Pickler( pikFile)
                  pickler.dump(self.data)
                  print(f"Stored pickle in {self.cacheFname}")

    _resourceList = ('title','latest','last_modified', 'format', 'checksum' )
    def pprintDataResources(self, bulk=False) :
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


    def updatePrepare(self):
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
                  org     = indata['organization']['slug']
                  if format is None:
                      print(f"Skipping '{fname}' fmt:{format} mod:{modDate} org='{org}'")
                      continue
                  genDate = self.makeGenDate(fname)
                  if genDate is None:
                      gen,fdate = (None,None)
                      reason="ifAbsent"         # no generic id
                  else:
                      gen,fdate  = genDate
                      if gen in self.genDir:
                          reason="ifNewer"
                      else:
                          reason="noLocalCopy"
                  
                  updtList.append( { 'reason':reason,'fname':fname, 'url':url, 'org':org,
                                     'checksum':checksum, 'format': format,
                                     'modDate':modDate,'cachedDate':fdate, 'genKey': gen } )
          self.updtList = updtList



    cacheUpdtTimeRex = re.compile("""^
        (?P<year>\d+)-(?P<month>\d+)-(?P<day>\d+)         # Year
       .(?P<hour>\d+):(?P<minute>\d+):(?P<seconde>\d+)    # Time
         """, re.VERBOSE) 
    def cacheUpdate(self):
          prettyPrinter = pprint.PrettyPrinter(indent=4)
          updtList = self.updtList
          for entry in updtList:
              #print(f"ENTRY={entry}")
              if entry['reason'] == "noLocalCopy":
                  self._getFromRemote(None, **entry)

              elif entry['reason'] == "ifAbsent":
                  fname=os.path.join(self.dirpath,entry['fname'])
                  if not os.path.exists(fname):
                     self._getFromRemote(None, **entry)      

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
                       self._getFromRemote(remoteDT, **entry)

              else:
                  raise RuntimeError(f"Bad reason code: {entry['reason']}")
        
    def _getFromRemote(self,remoteDT,
                            reason=None,fname=None, url=None, org=None, checksum=None,
                            format=None, modDate=None, cachedDate=None, genKey=None):
         if remoteDT is None:
             print(f"remoteDT is None for reason:{reason} fname:{fname}\n!! !!")
         fullPathname = os.path.join(self.dirpath,fname)
         with urllib.request.urlopen(url) as furl :
              with open(fullPathname,"wb") as fwr : 
                   fwr.write(furl.read())
         print(f"Wrote file '{fullPathname}' from URL:'{url}'")

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
    
        
if __name__ == "__main__":
    import unittest
    import sys

    class DGTest(unittest.TestCase):
        def test_baseLocal(self):
            return
            dataFileVMgr = manageDataFileVersions()
            print("Most recent versions of files in data directory:")
            for f in dataFileVMgr.listMostRecent() :
                print(f"\t{f}")

            self.assertEqual( "a", "a")   #easy test

        def test_remote(self):

            dataFileVMgr = manageAndCacheDataFiles()
            dataFileVMgr.getRemoteInfo()
            # dataFileVMgr.pprintDataResources(bulk=True)
            dataFileVMgr.updatePrepare()
            dataFileVMgr.cacheUpdate()
            
            self.assertEqual( "a", "a")   #easy test


            
    unittest.main()
