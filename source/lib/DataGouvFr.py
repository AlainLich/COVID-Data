'''
 Specific setup for files imported from https://www.data.gouv.fr/fr/datasets/...
 
 Deals with the fact that the site features files with filenames containing date
 information; this module permits to check/load the latest version.

 At this point this does not deal with downloading
'''

__author__ = 'Alain Lichnewsky'
__license__ = 'MIT License'
__version__ = '1.0'

from lib.utilities import *

class manageDataFileVersions(object):
    """ For each file name in directory, find which are different versions of same as 
        indicated in the file name with pattern yyyy-mm-dd-HHhMM, 
    """
    def __init__(self, dirpath="../data"):
        "dirpath is path relative current working directory"
        self.dirpath = dirpath
        if not os.path.isdir(dirpath):
            raise RuntimeError(f"Path {dirpath} not directory")
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
            mobj = manageDataFileVersions.datedFileRex.match(lf)
            if mobj:
               fls = ( int(mobj.groupdict()[z]) for z in  ('year', 'month', 'day','hour','minute') )
               date = datetime.datetime( *fls )
               gen  =  "!".join(map (lambda x: mobj.groupdict()[x] , ("hdr","ftr")))
               filDir[lf]=(gen,date)
               if gen in genDir:
                    if date > genDir[gen][0]:
                        genDir[gen] = (date,lf)
               else:
                    genDir[gen]= (date,lf, self.dirpath+"/"+lf)
        self.filDir = filDir
        self.genDir = genDir
        
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

            
