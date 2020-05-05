#!/usr/bin/python3
# -*- coding: utf-8 -*-
# -*- mode: Python -*-


__author__ = 'Alain Lichnewsky'
__license__ = 'MIT License'
__version__ = '1.1'


from rdflib import Namespace,  RDF, URIRef
from rdflib.namespace import NamespaceManager


nsParms = (
    ("xml",    "http://www.w3.org/XML/1998/namespace"),
    # these are the Dublin Core definitions
    ("DCore" , "http://purl.org/dc/elements/1.1/"),
    
    # these are the rdf definitions
    ("rdf"   , "http://www.w3.org/1999/02/22-rdf-syntax-ns#"),

    # SPARQL Query Results XML Format
    ("res"   , "http://www.w3.org/2005/sparql-results#"),

    # These are likely to be used by the european open data portal
    ("dcat",   "http://www.w3.org/ns/dcat#"),
    ("odp",    "http://data.europa.eu/euodp/ontologies/ec-odp#"),
    ("xsd",    "http://www.w3.org/2001/XMLSchema#"),
    ("foaf",   "http://xmlns.com/foaf/0.1/"),
    
    # namespace for my own additions (in intermediate XML)
    ("N"     , "http://localhost/added"),

    # namespace for using XML attribute names as rdf properties
    ("X2R"   , "http://localhost/XMLattToRDF"),
    )



nsTable    = { x[0]: (x[1], Namespace(x[1]) )  for x in nsParms}
nsTableInv = { x[1]: x[0]  for x in nsParms}
