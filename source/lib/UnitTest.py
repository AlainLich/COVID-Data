# -*- coding: utf-8 -*-
# (C) A.Lichnewsky, 2011, 2013, 2018  
#
__author__ = 'Alain Lichnewsky'
__license__ = 'MIT License'
__version__ = '1.0'


import sys
import types
import unittest
from contextlib import redirect_stdout, redirect_stderr

import matplotlib.pyplot as 	PLT


class testInOut:
    """ Object specifying inputs and expected result of a function call
    """
    def __init__(self, inargs=(), kwargs={}, out=None, exception=Exception):
        """
        arguments:
             - inargs = input positional arguments
	     - kwargs = input keyword arguments
             - out    = expected result (default None)
             - exception = type of exception to be generated/expected
        """
        self._inargs = inargs
        self._kwargs = kwargs
        self._out= out
        self._except = exception

    def inargs(self):
        return self._inargs

    def kwargs(self):
        return self._kwargs

    def expect(self):
        return self._out

    def exception(self):
        return self._except

class ALTestFrame(unittest.TestCase):
    """
     Make a number of trials specified by a list, check outcome (either compare== or
     failure (exception)
    """
    
    def applyTestList(self, list, func, redirect=False):
        """ apply a series of tests, specified by a testInOut object
        """
        for l in list:
            if redirect:
              if type(redirect)== type(""):
                       rf = redirect
              else:
                       rf = "/tmp/redirect.txt"
              print("Redirecting stdout and stderr to ", rf)
              with open(rf, "a") as f:
                with redirect_stdout(f):
                   with redirect_stderr(f):
                         res = func( *l.inargs(),**l.kwargs() )
            else:
                         res = func( *l.inargs(),**l.kwargs() )
            print ( "TEST:\t"           +repr(l.inargs())+repr(l.kwargs())+
                          " ==>> "      + repr(res) +
                          "\t expect("  + repr(l.expect()) +")" )
            self.assertEqual( res , l.expect(), 'incorrect result')

            
    def applyTestListFail(self, list, func, redirect=False):
        """ apply a series of tests, specified by a testInOut object, where failure
            is expected. The raised exception is checked wrt. specified expected exception
        """
        for l in list:
            with self.assertRaises(l.exception()):
              if redirect:
                if type(redirect)== type(""):
                       rf = redirect
                else:
                       rf = "/tmp/redirect.txt"
                print("Redirecting stdout and stderr to ", rf)
                with open( rf, "a") as f:
                        with redirect_stdout(f):
                          with redirect_stderr(f):
                           res = func( *l.inargs(),**l.kwargs() )
              else:
                     res = func( *l.inargs(),**l.kwargs() )

              print ( "TEST (expect Failure):\t"  +
                                    repr(l.inargs())+repr(l.kwargs()) +
                                    " ==>> "+ repr(res) +
                                    "\t expect("+ repr(l.expect()) +")" )
                
class ALTestFrameGraphics( ALTestFrame):
    def processDocoptArgs(arguments):
        """
         Assist with procession command line arguments before entering
         ̀unittest.main`, by clearing arguments managed by docopt.
        """
        for arg in arguments.keys() :
            if arg in  sys.argv:
                idx = sys.argv.index(arg)
                l= sys.argv[:idx]
                l. extend(sys.argv[idx+2:])
                sys.argv = l        
    
    def _start(self, **kwdParms):
        """ Help derived class honor the pause command line option,
            permits to pass the wait time in a "pause" keyword arg.
        """
        if not hasattr(self, "testedSet" ):
            print("In  GraphicTest.SetUp")
            self.testedSet=set()
        # honor the --wait command line parameter    
        if "pause" not in kwdParms  or not isinstance( kwdParms["pause"], int):
          self.__pauseParm = None
        else:
          self.__pauseParm = int( kwdParms["pause"])
            
    def __del__(self):
        print(f"\n***\nset of tested functions:{self.testedSet}\n")

    def _setAdd(self, *args):
        """ Add a function to the list of tested functions for reporting in __del
        """
        for x in args:
             self.testedSet.add(x)

    def show(self, **kwdargs):
        """ Show matplotlib figure for a limited duration if self.__pauseParm > 0
        """
        if  self.__pauseParm is not None and self.__pauseParm > 0:
            PLT.show(  block=False)
            PLT.pause( self.__pauseParm )
            PLT.close()
        else:
            PLT.show(block=True)

          

if __name__ == '__main__':
     ##### ce qui suit est un exemple d'utilisation
        
     def double(fld, *ignore):
            print("Coucou stdout fld=",fld)
            print("Coucou stderr fld=",fld, file=sys.stderr)
            return fld * 2
     
        
     class SMTestCase(ALTestFrame):
                def runTest(self):
                        print ("IN runTest")
                        self.testConversions()
                        self.testFailConversions()
                        

                def testConversions(self):
                        ltest = (
                                testInOut( (1,)   , out=2,),
                                testInOut( (2.0,) , out=4.0,),
                                )
                        self.applyTestList(ltest,  double,redirect=True)

                def testFailConversions(self):
                        ltest = (
                                testInOut( ()     , out=2,),
                                testInOut( None   , out=4, exception=TypeError),
                                )
                        self.applyTestListFail(ltest,  double, redirect=True)

                        
if __name__ == '__main__':
    print ("Launching test with unittest package/framework")
    r= unittest.main()
    print ("RESULT=", r)
