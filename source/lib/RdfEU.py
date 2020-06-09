#!/usr/bin/python3
# -*- coding: utf-8 -*-
# -*- mode: Python -*-


__author__ = 'Alain Lichnewsky'
__license__ = 'MIT License'
__version__ = '1.1'

import datetime as DTME

from rdflib import Namespace,  RDF, URIRef
from rdflib.namespace import NamespaceManager

"""
  All dependencies on encoding XML/RDF terms,
  including  
    - Dubli Core
    - Data Catalog Vocabulary (DCAT)
    - European  Data portal extensions
"""

"""
Values of Dublin Core™ Collection Description Frequency Vocabulary
    Triennial [freq:triennial]
    Biennial [freq:biennial]
    Annual [freq:annual]
    Semiannual [freq:semiannual]
    Three times a year [freq:threeTimesAYear]
*   Quarterly [freq:quarterly]
*   Bimonthly [freq:bimonthly]
*   Monthly [freq:monthly]
    Semimonthly [freq:semimonthly]
    Biweekly [freq:biweekly]
    Three times a month [freq:threeTimesAMonth]
*   Weekly [freq:weekly]
    Semiweekly [freq:semiweekly]
    Three times a week [freq:threeTimesAWeek]
*   Daily [freq:daily]
*   Continuous [freq:continuous]
    Irregular [freq:irregular]

Ref:
  https://www.w3.org/TR/vocab-dcat/#Property:dataset_frequency
  https://www.dublincore.org/specifications/dublin-core/collection-description/frequency/

"""

def isObsolete( dte, refDte=None, criterion="daily"):
    """ Decide if date `dte` is obsolete wrt. reference `refDte`, taking
        into account the criterion (daily, weekly,..)
    """
    crit = criterion.lower()
    
    if refDte is None:
        rdte = DTME.datetime.now()
    else:
        rdte = refDte
    
        
    if crit == "daily":
       retVal = dte < rdte - DTME.timedelta(days=1)
    elif crit == "weekly":
       retVal = dte < rdte - DTME.timedelta(days=7)
    elif crit == "monthly":
       retVal = dte < rdte - DTME.timedelta(days=30) # Approx!
    elif crit == "bimonthly":
       retVal = dte < rdte - DTME.timedelta(days=61) # Approx!
    elif crit == "quarterly":
       retVal = dte < rdte - DTME.timedelta(days=30*3+1) # Approx!
    elif crit in ( "annual", "yearly" ):
       retVal = dte < rdte - DTME.timedelta(days=365) # Approx!
    elif crit == "continuous":
       retVal = True


    else:
        raise NotImplementedError("Criterion {criterion} still TBD!!")

    return retVal

