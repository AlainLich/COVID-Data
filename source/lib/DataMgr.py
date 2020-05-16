# -*- coding: utf-8 -*-
#

'''
Facilitate the use of data from  multiple sites including:
                    - https://www.data.gouv.fr
                    - https://data.europa.eu/euodp

1) For downloaded files:
 
 Deals with the fact that the site exports/downloads files with filenames 
 containing date/timestamp information; this module permits to check/load 
 the latest version.

 Expectations:
    - local copies of relevant files are in a local directory

2) For direct/automated access to the site via its http API
    - files are downloaded from the sites
             + www.data.gouv.fr  
             + data.europa.eu/euodp
    - local copies are made of the most recent versions. Directory of loaded information is
      kept locally, and refreshed after a prescribed duration
    - the remote site is checked for updates after a prescribed duration

3) Local data cache:
   - manage the local data directory as a cache
   - permit to access the descriptive information pertaining the cached files

TBD:
   - documentation (wishful thinking?), also format so that doxygen output is
     nicer
'''

__author__ = 'Alain Lichnewsky'
__license__ = 'MIT License'
__version__ = '1.1'

from   lib.utilities import *
import requests, sys, pprint, pickle, time, shutil
from   collections   import Iterable, Mapping
from   enum import Enum, IntFlag

import urllib, hashlib

import lib.RDFandQuery as RDFQ
import lib.RdfEU       as RDFEU

class UpdateRqt(object):
    """
    Used to express a cache update request, which will likely be conditional.
    A list of such objects is built from the meta information and passed to  
    ̀cacheUpdate` and ̀_cacheUpdate`
    """

    class ReasonCde(Enum):
        NoGeneric    = 1    # no generic id: filename stripped of timestamp, use file mtime
        IsNewer      = 2    # remote file is newer: get it!
        NoLocalCopy  = 3    # no local copy, go and get it!
        FreqObsolete = 4    # check if the file mtime and the frequency imply obsolescence


    _validKwds = set( ('reason','fname','url','org', 'checksum','format',
                    'modDate', 'cachedDate', 'filesize', 'genKey', 'frequency') )
        
    def __init__(self, reason, kwdDict):
        bad = set(kwdDict.keys()) - UpdateRqt._validKwds
        if len (bad) > 0:
            raise RuntimeError(f"Bad keyword(s): {bad}")
        if not isinstance(reason, UpdateRqt.ReasonCde):
            raise RuntimeError(f"Bad type for reason code: {type(reason)}")
        self.reason = reason
        self.kwdDict= kwdDict

    def __getattr__(self,attr):
        if attr == "reason":
            return self.reason
        if attr in self.kwdDict:
            return self.kwdDict[attr]
        else:
            raise AttributeError(f"Object {type(self)} has no attribute '{attr}'")

    def __str__(self):
        return f"<{type(self)}>:[[ reason = {self.reason}; dict={self.kwdDict}]]"
        
class manageDataFileVersions(object):
    """ For each file name in local directory, find which are different versions of same as 
        indicated in the file name with pattern yyyy-mm-dd-HHhMM. 

    """
    def __init__(self, dirpath,**kwdOpts ):
        """
        Argument "dirpath" is compulsory, must designate a directory where local copies
                 of files will be / are cached. There is no default on purpose to
                 avoid unintentional tampering.
        """
        self.dirpath = dirpath
        if not os.path.isdir(dirpath):
            raise RuntimeError(f"Path {dirpath} not directory")

        #design of setDefaults is faulty TBD
        warnings.warn("Redesign of setDefaults TBD", DeprecationWarning)

        if hasattr(self, "options"):
             setDefaults(self.options, kwdOpts)
        else:
            self.options = kwdOpts
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
    
    def _walk(self, prepareCacheRecovery=False):
        """ (internal)
            Walk the file in the dirpath directory (no support for
            nested dirs at this point). 
           
            if prepareCacheRecovery==False: Fill the genDir directory where:
               - gendir is indexed by filenames with removed timestamps (gen),
		        permits access to most recent version
            otherwise, make list of files with equivalent generic name, informed
                        with date (from filestamp and possibly from disk),
                        this is returned to caller

            Note: filDir has been removed since we need to look into generic file 
                  names anyhow, since a scenario where we are given a non existing
                  filename for which equivalent (up to time stamp ) file exist.
        """
        lfiles = os.listdir(self.dirpath)
        genDir={}
        nonTSFiles={}
        for lf in lfiles:
               genDate = self.makeGenDate(lf)
               if genDate is None:
                   nonTSFiles[lf]=None  #using a dict, ctime might be of interest (TBD)
                   continue
               (gen,date) = genDate
               fpath = os.path.join( self.dirpath, lf)
               if not prepareCacheRecovery:
                    #here we keep the most recent only
                    if (not gen in genDir) or ( date > genDir[gen][0] ):
                        genDir[gen] = (date,lf,fpath)
               else:
                    #now we keep the whole stuff, interested in candidates victims
                    #to be scavenged
                    if (not gen in genDir):
                        genDir[gen] = []
                    statinfo=os.stat(fpath)
                    genDir[gen].append((date,lf,fpath,statinfo))
                    
        self.nonTSFiles = nonTSFiles
        if not prepareCacheRecovery:
            self.genDir = genDir
        else:
            return genDir
            
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
               
    def listMostRecent(self, nonTS=False):
        """
            Returns sorted list of files which are in  the `dirpath` directory:
            if nonTS == True:
               - which do not have "timestamps" in their file names
            else (default):
               - which represent the most recent version of files with timestamps in the
                 filename (we do not look into file attributes).
        """
        if nonTS:
            return sorted(self.nonTSFiles.keys())
        else:
            return sorted([  k[1]   for k in self.genDir.values()])
    
    def getRecentVersion(self,file, default=None):
        """
          Return the most recent name of a file; if not found will raise
          an exception unless a default is given. 

          Since the cache is being handled like a cache, the file may not be existing, 
          while a more recent version corresponding to the same generic id exists.
        """
        gen = self.makeGenDate(file)
        if gen is not None and gen[0] in self.genDir:
            nf = self.genDir[gen[0]][1]
            return nf
        if not default:
               raise RuntimeError(f"Unexpected file:'{file}'")
        elif default is True:
                return file
        else:
                return default

class manageAndCacheBase(manageDataFileVersions):

    def __init__(self, dirpath,**kwdOpts ):
        manageDataFileVersions.__init__(self, dirpath=dirpath, **kwdOpts)
        avl= self._spaceAvail(dirpath)
        margin  = self.options['maxDirSz'] * 0.1
        if avl < margin  :
            success = self.cacheSpaceRecovery(  margin - avl)
            if not success:
                raise RuntimeError(f"Cache space in {dirpath} insufficient, check manually")
            
    def getRemoteInfo(self, localOnly=False):
        """ Load the information describing files on the remote site, either
            from a local cached copy (in file .cache), or by reloading after the 
            elapsed time specified by 'CacheValidity'

            Parameter localOnly specifies that remote cache should not be consulted

            If self.options["dumpMetaFile"] is defined and is a file name, the
            bulk data, representing the meta/directory information loaded from 
            the remote site (in self.data) is output to that file.

            If self.options["dumpMetaInfoFile"] is defined and is a file name, the
            meta data (in self.metadata if available) is output to that file. This 
            represents information elaborated from "dumpMetaFile".

            Precise description of cached information (is/should be) described
            in derived classes.
        """
        cacheValid = self._getMetaFromCache(localOnly=localOnly)

        #  _getRemoteMeta deals with fetching from the remote site; it has 2 options:
        #          -   rely on prepareMeta to make the meta info available
        #                   and return False
        #          -   perform the prepareMeta functions and return True
        #   Rationale: when _getRemoteMeta operates in an iterative fashion
        #              it might be simpler to integrate prepareMeta functions
        #              an example is when using LIMIT + OFFSET in SPARQL
        fullyPrepared = False
        if not ( localOnly or cacheValid ):
             fullyPrepared = self._getRemoteMeta()
        if not fullyPrepared:
             self.prepareMeta( fromCache = cacheValid or localOnly )

        if "dumpMetaFile" in self.options and self.options["dumpMetaFile"]:
            dumpFname = self.options["dumpMetaFile"]
            with open(dumpFname,"w") as fd:
               fd.write(self.data.decode('utf-8'))               
               fd.close()
               sys.stderr.write( f"Per options['dumpMetaFile'], wrote data in file {dumpFname}\n" )

        if "dumpMetaInfoFile" in self.options and self.options["dumpMetaInfoFile"]:
            dumpFname = self.options["dumpMetaInfoFile"]
            if hasattr(self, "metadata"):
                with open(dumpFname,"w") as fd:
                    prettyPrinter = pprint.PrettyPrinter(indent=4)
                    fd.write(prettyPrinter.pformat(self.metadata))
                    fd.write("\n")
                    fd.close()
                    sys.stderr.write( f"Per options['dumpMetaInfoFile'], wrote meta data in file {dumpFname}\n" )
            else: 
                 sys.stderr.write( f"Request options['dumpMetaInfoFile'] not granted, not avail")
        
    def prepareMeta(self, fromCache=True):
        """ This is a do nothing routine, it may be used by a derived class that 
            needs to postprocess self.data after it being obtained externally or
            reloaded from cache.

            This routine receives information in the fromCache argument in case
            its behaviour depends on source. Normally the routine may use:
              - self.metadata["data:type"]
              - self.data : the data that needs to be adjusted

            The parameter fromCache will be True unless the cache has just been reloaded
            from remote
        """
        pass
    
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
                3) there is enough available disk space to stores all the
                   files

              Preparatory information is stored in attribute `updtList`, may be 
              None if it has not been possible to access the metadata on the remote
              server.
          """
          if  self.updtList is None:
              print (f"update of cache not possible, missing metadata and/or updt list")
              return None

          # we first evaluate requirement aggressively using the marginPercent arg
          updtReq = self.verifyForCacheUpdate()
          if updtReq > 0 or "forceCacheRecovery" in self.options:
              success = self.cacheSpaceRecovery(updtReq)
              # now try to accomodate the update, not taking margin into account
              updtReq = self.verifyForCacheUpdate( marginPercent=0.15 )
          if  updtReq <= 0 or success :
              return self._cacheUpdate(effector=self._getFromRemote)
          else:
              raise RuntimeError(f"Unable to recover enough disk space (req:{updtReq} bytes)")
    def  cacheSpaceRecovery(self, requiredSpace, keepNFiles=2):
         """
         Walk disk space in self.dirPath, try to recover `requiredSpace`, if true
         declare success by returning True, othewise return False.

         There might be further parametrization of cache management tactics...
         """
         def mbytes(n):
             m = n/((2**10)**2)
             return f"{m:.3f}Mb"
         if  "forceCacheRecovery" in self.options:
             warnings.warn("Forced cache recovery because of option 'forceCacheRecovery'")
         print( f"In cacheSpaceRecovery, looking for {requiredSpace} bytes" )
         fileDir = self._walk( prepareCacheRecovery=True)

         print ("Printing genDir collected for preparing Cache Recovery")
         totRecup = 0
         self.scavengeList = []
         for genEl in sorted(fileDir.keys()):
             els = list(sorted(fileDir[genEl], key=lambda x: x[0], reverse=True ))
             recup=[]
             totfiles = 0
             i = 0
             for el in els:
                   i += 1
                   fsize = el[3].st_size
                   totfiles +=  fsize
                   el =(*el, fsize)
                   if i > keepNFiles :
                       recup.append((fsize, el[2]))

             if len(recup ) >= 1:
                  print(f"\nGen.File:\t'{genEl}'\n\tTo be scavenged:")
                  for i in range(0,len(recup)):
                      recEl = recup[i]
                      print (f"\t\t{mbytes(recEl[0])}\t'{recEl[1]}'")
                      totRecup += recEl[0]
                      self.scavengeList.append(recEl[1])
                  print ("\tKept")
                  for i in range(0,min(keepNFiles, len(recup))):
                    print (f"\t\t{mbytes(els[i][3].st_size)}\t'{els[i][2]}'")

         
         success =  totRecup >= requiredSpace
         self._removeScavengeList()
         if not success:
             print( f"Recovered {totRecup} from cache, which is insufficient required:{requiredSpace}" )
         return success      

    def _removeScavengeList(self):
        for file in self.scavengeList:
            os.remove(file)
            #TBD update self.availOnDisk
         
    def  verifyForCacheUpdate(self, marginPercent=0.10):
          """ returns the amount of disk space that need to be recovered to proceed,
              0 if enough space is available
              -   the argument marginPercent permits to make cache recovery more aggressive
                  before entering the _cacheUpdate method. 

              NOTE: To be coherent, we should also refuse to download/keep files that 
                    exceed the max available size once loaded (this may be necessary since
                    some sites may not indicate expected file size in meta, and/or the 
          	    indicated size may be deceptive! (TBD?)
          """
          self._requiredDiskSz = 0
          self._cacheUpdate(effector=self._sizeAccounter)
          self.availOnDisk = self._spaceAvail(self.dirpath)
          if self._requiredDiskSz > 0:
              avail = self.availOnDisk - int( marginPercent * self.options['maxDirSz'])
              print( f"in verifyForCacheUpdate avail={avail} required={self._requiredDiskSz}" )
              if  self._requiredDiskSz >  avail:
                  return  self._requiredDiskSz -  avail
          return 0    

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
              if entry.reason == UpdateRqt.ReasonCde.NoLocalCopy :
                  effector(None, entry)

              elif entry.reason == UpdateRqt.ReasonCde.NoGeneric:
                  fname=os.path.join(self.dirpath,entry.fname)
                  if not os.path.exists(fname):
                     effector(None, entry)      

              elif entry.reason == UpdateRqt.ReasonCde.IsNewer:
                  genEntry = self.genDir[entry.genKey]
                  fname = genEntry[2]
                  mtime = os.path.getmtime(fname)
                  mtimeDT = datetime.datetime.fromtimestamp(mtime)
                  mobj = manageAndCacheDataFiles.cacheUpdtTimeRex.match(entry.modDate)
                  if mobj:
                     fls = ( int(mobj.groupdict()[z])
                             for z in  ('year', 'month', 'day','hour','minute', 'seconde') )
                     remoteDT = datetime.datetime( *fls )
                  else:
                     raise RuntimeError(f"cannot parse date /{entry.modDate}/")
                  if mtimeDT < remoteDT - datetime.timedelta(minutes=5):
                       effector(remoteDT, entry)
                       
              elif entry.reason == UpdateRqt.ReasonCde.FreqObsolete:
                  mtime = os.path.getmtime( os.path.join( self.dirpath, entry.fname))
                  obsolete =  RDFEU.isObsolete( datetime.datetime.fromtimestamp(mtime),
                                                criterion = entry.frequency)
                  if obsolete:
                       effector(datetime.datetime.now(), entry)
                      
              else:
                  raise RuntimeError(f"Bad reason code: {entry.reason}")
        
    def _getFromRemote(self,remoteDT, rqt ):
         """ (internal) read from remote using API/http protocol
         """
         if remoteDT is None:
             print( f"remoteDT is None for reason:{rqt.reason} fname:{rqt.fname}\n!! !!")
         fullPathname = os.path.join(self.dirpath,rqt.fname)
         print( f"About to load file {fullPathname}, available space is {self.availOnDisk}")
         with urllib.request.urlopen(rqt.url) as furl :
              with open(fullPathname,"wb") as fwr : 
                   fwr.write(furl.read())
                   wrSz = fwr.tell()
         print(f"Wrote file \t'{fullPathname}'\n\tfrom URL:'{rqt.url}'")

         self.availOnDisk -=  wrSz
         if self.availOnDisk < 0:
             print(f"Loading {fullPathname} requires {wrSz} bytes")
             raise RuntimeError(f"Loading file {fullPathname} has exceeded avail cache space")
         chk = self. verifChecksum(fullPathname,rqt.checksum)
         if chk:
            # update the internal database (useful if same file encountered several times
            # with different timestamps) 
            self.genDir[rqt.genKey] = (remoteDT, rqt.fname, fullPathname) 

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
    """ Manage a local repository extracted from a site returning meta information:
        - specialization for the format of the meta file AND the format for the
          internal representation (JSON (list of dict)+ / RDF (rdflib) ) is done
          in derived classes, we will stay generic here.
        - site specialization done in derived class
        - caching of this information, the remote site is consulted only
          after a parametrized delay 
        - for local copies of files, permits to access the most recent version 
          as indicated in base class
        - management of the local cache directory  (removal of redundant files)

        For now examples are shown in the test section at end of file (`test_remote`)
    """
    defaultOpts = {
                   'CacheValidity':  12*60*60,  #cache becomes stale after 12 hours
                   'maxImportSz'  :  5*(2**10)**2,  #5 Mb: max size of individual file load
                   'maxDirSz'     :  50*(2**10)**2,  #50 Mb: max total cache directory size
                   'httpTimeOut'  :  1
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
        self.metadata   = {"options":self.options}
        
    def _getMetaFromCache(self, localOnly):
        """ (internal) Read from the cached file (a pickle of a json)
        """
        cacheFname = os.path.join(self.dirpath,  self.options["cacheFname"] )
        valid = True
        if not os.path.isfile(cacheFname):
            valid = False
            if localOnly:
                raise RuntimeError(f"No cache ({cacheFname}) to reload information locally")
        else:
            mtime = os.path.getmtime(cacheFname)
            nowtime = time.time()
            elapsed = nowtime - mtime
            elapsedStr = strElapsed(elapsed)
            if elapsed > self.options['CacheValidity'] and  not  localOnly:
               print(f"Need to reload cache from remote,  stale after {elapsedStr}")
               valid = False
        if valid:
               with open(cacheFname,"rb") as pikFile:
                  pickler = pickle.Unpickler( pikFile)
                  self.metadata = pickler.load()
                  self.data = pickler.load()
                  print(f"Loaded pickle from {cacheFname}, loaded {elapsedStr} ago ({len(self.data)} elts)")
                  if "showMetaData" in self.options and self.options["showMetaData"]:
                      self.showMetaData()
        return valid

    def showMetaData(self):
        """ Permits to print meta data pertaining to the operation of this code,
            in practice this amounts to pretty printing a dictionnary with all options
            used plus other details
        """
        prettyPrinter = pprint.PrettyPrinter(indent=4, width=150)
        print(f"cache metadata:{prettyPrinter.pformat(self.metadata)}")
    
    def _getRemoteMeta(self):
          """ Read the metadata on selected files from the remote site, store
              it into the DIRPATH/.cache file, keep it in the self.data attribute as the
              python representation of a json
          """
          spaceAvail = self._spaceAvail(self.dirpath)
          requiredSpace = 2000*(2**10)
          if spaceAvail < requiredSpace:
              success = self.cacheSpaceRecovery(  requiredSpace )
              if not success:
                  spaceAvail = self._spaceAvail(self.dirpath)
                  print (f"spaceAvail={spaceAvail}, {int(requiredSpace/(2**10))}K required,  maxDirSz={self.options['maxDirSz']} ")
                  raise RuntimeError(f"Insufficient space in {self.dirpath} to store cached metadata")

          self._getRemoteMetaFromServer()
          self.metadata["pickleTS"]= time.strftime("Pickled at :%Y-%m-%d %H:%M:%S",
                                                   time.gmtime(time.time()))
          
          cacheFname = os.path.join(self.dirpath,  self.options['cacheFname'])          
          with open(cacheFname,"wb") as pikFile:
                  pickler = pickle.Pickler( pikFile)
                  pickler.dump(self.metadata)
                  pickler.dump(self.data)
                  print(f"Stored pickle in {cacheFname}")
                  wrSz = pikFile.tell()

          if not hasattr( self, "availOnDisk" ):
               self.availOnDisk = self._spaceAvail(self.dirpath)
          self.availOnDisk -=  wrSz
          if self.availOnDisk < 0:
             print(f"Storing {cacheFname} requires {wrSz} bytes")
             raise RuntimeError(f"Storing file {fullPathname} has exceeded avail cache space")        
          return False
       
    def _getRemoteMetaFromServer(self):  
        raise NotImplementedError("This method should be defined in derived class!")
    
    _resourceList = ('title','latest','last_modified', 'format', 'checksum' )

    def pprintDataResources(self, bulk=False) :
        raise NotImplementedError("This method should be defined in derived class!")


    def _pprintDataItem(self, item="description", showVals=True) :
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
          #   self.dataTopLev: specifies where to look for the data items in the
          #         returned datastructure representing json. Expect it to
          #         be defined in a derived class.

          if not hasattr(self, "dataTopLev"):
             raise RuntimeError("A derived class must define attribute dataTopLev")
          sdata = self.data
          if  "debug" in self.options:
             if isinstance(sdata[self.dataTopLev], dict):
                print (f"\t\tdata[dataTopLev].keys = {sdata[self.dataTopLev].keys()} ")
             elif isinstance(sdata[self.dataTopLev], Iterable):
                for elt in sdata[self.dataTopLev]:
                    print (f"\t\t\telt.keys = {elt.keys()} ")

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
                      dolist=list( filter ( lambda x:  spec.genMatch(x),
                                            sorted(jsonDict.keys())))
                      if  isinstance(spec,Iterable) and len(spec)>=2:
                          dolist1 = list( filter ( lambda x:  spec[1].genMatch(x),
                                            sorted(jsonDict.keys())))
                          print(f"***\ndolist  := {dolist}\ndolist1 := {dolist1}\n***")
                          dolist = dolist1
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

                  #print (f"Dolist:{dolist}")
                  #raise "HO"
                  for el in dolist:
                      if isinstance(jsonDict,dict):
                          if el in  jsonDict:
                              json =  jsonDict[el]
                              if len (specList) == 1:
                                 if showVals:
                                     vp = "\t->\t"+prettyPrinter.pformat( json )
                                 else:
                                     vp=f"\t@skip:{len(str(json))}Bytes@"
                                 print(f"{zskip[skip]}{':'.join(prefix)}:{el}>@({'.'.join(r)})"+vp)
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
                                  if kl.genMatch(el):
                                      raise RuntimeError(f"\tDo something for {kl}")
                      #print(f"{'+++'.join(prefix)}##")

                                  
          prettyPrinter = pprint.PrettyPrinter( indent=4, width=150, compact=True)
          itemList      = rexTupleList(item)
          if (isinstance( sdata[ self.dataTopLev ], dict)):
              top =  ( sdata[ self.dataTopLev ], )
          else:
              top =  sdata[ self.dataTopLev ]
          recurse(itemList, top, prettyPrinter )

        
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
                      reason = UpdateRqt.ReasonCde.NoGeneric # no generic id:filename without timestamp
                  else:
                      gen,fdate  = genDate
                      if gen in self.genDir:
                          reason = UpdateRqt.ReasonCde.IsNewer
                      else:
                          reason = UpdateRqt.ReasonCde.NoLocalCopy

                  kd = {'fname':fname, 'url':url, 'org':org, 'checksum':checksum, 
                	  'format': format,'modDate':modDate,'cachedDate':fdate,
                          'filesize':filesize,'genKey': gen } 
                  updtList.append( UpdateRqt(reason, kd))
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
        if not hasattr(self, "options"):
            self.options={}
        setDefaults(self.options, kwdOpts, manageAndCacheDataFiles.defaultOpts)
        manageAndCacheBase.__init__(self, dirpath=dirpath)
        # by now, the base class initializer has obtained the local filesys information
        setDefaults(self.options, kwdOpts, manageAndCacheDataFiles.defaultOpts)

    def getRemoteInfo(self, localOnly=False):
        """ Load the information describing files on the remote site, from a local cached
            copy (in file .cache)
            Parameter localOnly specifies that remote metadata should not be consulted
        """
        raise RuntimeError("Still TBD")
         
