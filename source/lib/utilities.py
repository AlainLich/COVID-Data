'''
Setup some utilities, very much related to our project of displaying figures
in Jupyter. 
'''

__author__ = 'Alain Lichnewsky'
__license__ = 'MIT License'
__version__ = '1.0'

# Sys import
import sys, os, re

# Python programming
from itertools import cycle
from time import time
import datetime

# Better formatting functions
from IPython.display import display, HTML

import warnings
warnings.filterwarnings('ignore')
print("For now, reduce python warnings, I will look into this later")

#using Matplotlib
import matplotlib        as MPL
import matplotlib.pyplot as PLT
import seaborn as SNS
SNS.set(font_scale=1)

# Using pandas
import pandas as PAN


class ImageMgr(object): 
    """ Ensures that the current image from matplotlib is stored in the appropriate
        per chapter subdirectory.

        usage: example:
               ImgMgr = ImageMgr(chapdir="Chap01"

    """
    def __init__(self, rootdir=".", chapdir="DefaultChap", imgtype="jpg"):
       
         self.project_root_dir = rootdir
         self.chapter_id=chapdir
         self.imgtype="."+imgtype
            
    def save_fig(self, fig_id, tight_layout=True):
       "Save the current figure"
       path = os.path.join(self.project_root_dir, "images", self.chapter_id, fig_id + self.imgtype)
       print("Saving figure", fig_id)
       if tight_layout:
          PLT.tight_layout()
       PLT.savefig(path, format='png', dpi=300)


# ## Check environment
# 
# It is expected that your working directory is named `JupySessions`, that it has
# subdirectories `images/*` where generated images may be stored to avoid overcrowding.
# At the same level as your working dir there should be directories
#   `../data` for storing input data and `../source` for python scripts, libraries,...
       
def checkSetup(chap = None):
    """
       Verifies that subdirectories are correctly positionned wrt. working dir 

       usage: example : checkSetup(chap="Chap01")
    """
    cwd = os.getcwd()
    dp, dir = os.path.split(cwd)
    if ( dir != 'JupySessions'):
       raise(RuntimeError("Installation incorrect, check that this executes in 'JupySessions' "))
    # Check subdirectory f'JupySessions/images/{chap}'
    if chap:
        img = os.path.join(dp,  'JupySessions', 'images', chap)
        if (not os.path.exists( img)):
          raise(RuntimeError("Installation incorrect, check that image dir exists at '%s'" % img ))
    # now check that the expected subdirectories are where expected
    for d in ('data','source'):
       ddir = os.path.join(dp,  d)
       if (not os.path.exists( ddir)):
          raise(RuntimeError("Installation incorrect, check that  dir '%s' exists at '%s'" % (d,ddir )))


def read_csvPandas(fname,clearNaN=False, **kwargs):
    """ Read a csv file, all keywords arguments permitted for pandas.read_csv 
        will be honored
    """
    df = PAN.read_csv(fname,**kwargs)
    if clearNaN:
        return df.dropna(how="all").dropna(axis=1)
    return df


# In[ ]:


def read_xlsxPandas(fname,clearNaN=False, **kwargs):
    """ Read a xlsx file, all keywords arguments permitted for pandas.read_csv 
        will be honored
    """
    df = PAN.read_excel(fname,**kwargs)
    if clearNaN:
        return df.dropna(how="all").dropna(axis=1)
    return df



def setDefaults(dict, optDict, defaultDict):
    """
        Operates on dictionnaries; fills dict with optDict contents, adding defaults
        from defaultDict when absent
    """
    for (k,v) in optDict.items(): 
        dict[k] = v
    for  (k,v) in defaultDict.items():
        if k not in dict:
            dict[k] = v

