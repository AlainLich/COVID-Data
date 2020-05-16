# -*- coding: utf-8 -*-
#

'''
Epidemiological models used for fitting/analyzing data. Derived classes
have increasing ability to handle variable parameters which may be optimized.

At this point, most capable is class  ̀SEIRYOpt3`.

'''

__author__ = 'Alain Lichnewsky'
__license__ = 'MIT License'
__version__ = '1.1'


import math
import numpy             as NP
import numpy.random      as RAND
import scipy.stats       as STATS
import pandas            as PAN
from scipy import sparse
from scipy import linalg
from scipy import integrate

from lib.basicUtils import toDict

class SEIRYModel(object):


    def __init__(self, t0 = 0,tF = 100, tDelta = 1):
        self.t0 = t0
        self.tF = tF
        self.tDelta  = tDelta

        self.tSteps = NP.arange(t0, tF, tDelta)


    def setInitial(self, 
                   i0 = 389/14.0e6,         # infected   Wuhan in paper
                   e0 = 318/14.0e6,         # exposed
                   r0 = 0,                  # recovered
                   q0 = 0,                  # quarantined
                   d0 = 0,                  # dead
                   p0 = 0,                  # insusceptibles
                   s0 = None                # susceptibles defaults to :1 -((i0 + e0 + r0)
        ):
        if s0 is None:
            s0 = 1 - (i0 + e0 + r0)         # susceptibles
        self.y0 = (s0 , e0, i0, q0, r0, d0, p0 )

        print(f"In setInitial: initial values for ODE")
        for (x,l) in ((i0,"i0: infected"), (e0,"e0: exposed"), (r0, "r0: recovered"),
                      (q0,"q0: quarantined"), (d0,"d0: dead"),
                      (p0,"p0: insusceptibles"), (s0, "s0: susceptibles")):
            print (f"\t{l}\t->\t{x}")
        

        
    def lambFn(t):          # estimated dates for change in policy/efficiency
       if t <20:
          return 0.02
       else:
          return 0.04
    
    def kappaFn(t):          # estimated dates for change in policy/efficiency
       if t<30:
          return 3.0e-2
       else:
          return 1.0e-2
        
    def setParms(self,
                 beta = 1,             # rate of exposition (in prop of susceptibles
                                       #meeting infected)
                 alpha = 0.085,         # rate of susceptibles becoming insusceptible
                 delta = 1/7.4,        # inverse average quarantine time
                 lambFn =  lambFn, # recovery/cure rate
                 kappaFn=  kappaFn, # mortality rate
                 gamma = 0.5            #  inverse average latent time 
                 ):
              """ Set internal parameters, will provide defaults for all arguments.
                  To selectively modify parameters, see method `adjustParms`
              """
              self.beta = beta
              self.alpha = alpha
              self.delta = delta
              self.lamb =  lambFn
              self.kappa = kappaFn
              self.gamma = gamma
             
    def adjustParms(self, kwdParmDict):
        """ Set internal parameters, only concern parameters appearing in arguments
            appearing in `kwdParmDict`
        """
        for k in kwdParmDict:
            if not hasattr(self,k):
                raise KeyError(f"Bad parms={k}")
            self.__setattr__(k,kwdParmDict[k])

    def showParms(self):
        print("--  "*3 + "parms")
        for p in ("beta","alpha", "delta", "lamb", "kappa", "gamma"):
            print(f"{p}\t->\t{self.__getattr__(p)}")
        print("--  "*6)

    def __getattr__(self,p):
        d = self.__dict__
        if p not in d:
            raise KeyError(f"Bad parms={p}")
        return d[p]

    def setattr(self,p,val):
        d = self.__dict__
        if p not in d:
            raise KeyError(f"Bad parms={p}")
        d[p]=val
    
    def FTY(self, y, t):
        """ The RHS in the ODE,  see the paper 
            "Epidemic analysis of COVID-19 in China by dynamical modeling" 
             (arxiv:2002.06563V1).
        """
        s, e, i, q, r, d, p  =  y
        dydt  = (- self.beta * s * i - self.alpha * s,          # s 
                   self.beta * s * i - self.gamma * e ,           # e
                   self.gamma * e    - self.delta*i,                 # i
                   self.delta * i    - ( self.lamb(t) + self.kappa(t) ) * q,    # q
                   self.lamb(t) * q,                            # r
                   self.kappa(t) * q,                           # d
                   self.alpha * s                            # p 
                )
        return dydt
        
    def solve(self):
        self.solY, self.psolDict = integrate.odeint( self.FTY, self.y0, self.tSteps,
                                                     full_output = True)
        self.solDF=PAN.DataFrame(self.solY)
        self.solDF.columns = ("susceptible", "exposed","infected", "quarantined",
                              "recovered", "dead", "insusceptible")
        self.solDF.index = self.tSteps

    def error(self, refTSteps, refY, columns):
        #   for now we suppose that refSol is computed with the same time steps
        #   than the problem solution, and that the solution is available.
        #   we also assume that these are vector in the reals ($R^n$)
        return ((refY - self.solDF.loc[:,columns])**2).sum()


class  SEIRYOpt1(SEIRYModel):
    """
    This is a first attempt at fitting, with 1 parameter (beta), based on the
    data concerning recovered (only)
    """
    def __init__(self, beta, refT, refY):
        """ (Warning : quite specific to single parm beta) 
            Derived class used for parameter identification, has reference data
            for fitting in parameters 
              - refT
              - refY
            For now, all time scales have better be the same, no interpolation
            when computing the error.....
        """
        SEIRYModel.__init__(self)

        self. setInitial()   
        self.setParms(beta=beta) #this allows for non default beta ?
        self.refT = refT
        self.refY = refY
        
    def eval(self, beta):
        self.adjustParms(toDict( beta = beta )) # beta becomes an optim variable here!
        self.solve()
        return self.error(self.refT, self.refY, "recovered")
    
class  SEIRYOpt2(SEIRYModel):
    """
    This is a first attempt at fitting, with multiple parameters (beta, alpha, delta, 
    gamma)  based on the  data concerning recovered (only)
    This has reference data for fitting in parameters 
              - refT
              - refY
    For now, all time scales have better be the same, no interpolation
    when computing the error.....
    """
    def __init__(self, parmDict,refT, refY):
        SEIRYModel.__init__(self)

        self. setInitial()   
        self.setParms()
        self.adjustParms(parmDict)
        self.refT = refT
        self.refY = refY
        
    def eval(self, pV):
        if pV is not None:
           self.adjustParms(toDict(beta=pV[0], alpha=pV[1], delta=pV[2], gamma=pV[3]) ) 
        self.solve()
        return self.error(self.refT, self.refY, "recovered")
    

class  SEIRYOpt3(SEIRYModel):
    """
    This fits, with multiple parameters (beta, alpha, delta, gamma)  based on the  
    data concerning multiple elements of the result vector.
    This has reference data for fitting in parameters 
              - refT
              - refY : dataFrame where columns are the reference vectors, 
                       column names are also used for identification in result
    For now, all time scales have better be the same, no interpolation
    when computing the error.....

    This class makes the assumption that the column names of the solution
    components are identical in refY and in the solution produced and 
    found in self.solDF
    """
    def __init__(self, parmDict,refT, refY,initial={}, **kwdParms):
        SEIRYModel.__init__(self,**kwdParms)
        if not isinstance(refY, PAN.DataFrame):
            sys.stderr.write(f"Got refY with type {type(refY)}\n")
            raise RuntimeError(f"parameter refY is expected to be a DataFrame")
        self. setInitial(**initial)   
        self.setParms()
        self.adjustParms(parmDict)
        self.refT = refT
        self.refY = refY
        
    def error(self, refTSteps, refY):
        #   for now we suppose that refSol is computed with the same time steps
        #   than the problem solution, and that the solution is available.
        #   we also assume that these are vector in the reals ($R^n$)
        
        accum = 0.0
        if isinstance( self.solDF, PAN.DataFrame):
            for col in refY.columns:
                accum += ((refY.loc[:,col] - self.solDF.loc[:,col])**2).sum()
        else:
            for icol in range(0, refY.shape[1]):
                accum += ((refY.iloc[:,icol] - self.solDF.loc[:,icol])**2).sum()
                
        return accum
    
    def eval(self, pV):
        if pV is not None:
           self.adjustParms(toDict( beta=pV[0], alpha=pV[1], delta=pV[2], gamma=pV[3] ) )
        self.solve()
        return self.error(self.refT, self.refY)
    
    
