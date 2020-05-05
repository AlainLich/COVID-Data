#!/usr/bin/python3
# -*- coding: utf-8 -*-
# -*- mode: Python -*-

__author__ = 'Alain Lichnewsky'
__license__ = 'MIT License'
__version__ = '1.1'

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
#
# (C) Alain Lichnewsky, 2019, 2020
#
# Notes: 1) This includes derived work based on a rdflib utility module (copied/frozen)
#           (from rdflib distribution) in
#                lib/python3.6/site-packages/rdflib/tools/rdf2dot.py
#           and  lib/python3.6/site-packages/rdflib/extras/external_graph_libs.py
#
#           More licensing information on https://github.com/RDFLib/rdflib, 
#           Copyright (c) 2002-2017, RDFLib Tea
#
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

import sys
from sys import exit, exc_info, stdout, stderr, stdin

import collections
from collections import Iterable, Mapping

import enum 
import re

from docopt import docopt

import cgi
import codecs

import networkx as NX
import pygraphviz as PYGVIZ
import rdflib
from rdflib import XSD
from rdflib import util
from rdflib import Graph, Literal, BNode, Namespace,  RDF, URIRef
from rdflib.namespace import NamespaceManager


LABEL_PROPERTIES = [rdflib.RDFS.label,
                    rdflib.URIRef("http://purl.org/dc/elements/1.1/title"),
                    rdflib.URIRef("http://xmlns.com/foaf/0.1/name"),
                    rdflib.URIRef("http://www.w3.org/2006/vcard/ns#fn"),
                    rdflib.URIRef("http://www.w3.org/2006/vcard/ns#org")
                    ]

XSDTERMS = [
    XSD[x] for x in (
        "anyURI", "base64Binary", "boolean", "byte", "date",
        "dateTime", "decimal", "double", "duration", "float", "gDay", "gMonth",
        "gMonthDay", "gYear", "gYearMonth", "hexBinary", "ID", "IDREF",
        "IDREFS", "int", "integer", "language", "long", "Name", "NCName",
        "negativeInteger", "NMTOKEN", "NMTOKENS", "nonNegativeInteger",
        "nonPositiveInteger", "normalizedString", "positiveInteger", "QName",
        "short", "string", "time", "token", "unsignedByte", "unsignedInt",
        "unsignedLong", "unsignedShort")]

EDGECOLOR = "blue"
NODECOLOR = "black"
ISACOLOR = "black"
def rdf2dot(g, stream, opts=None):
    """
    Convert the RDF graph to DOT; writes the dot output to the stream
    This function accepts a g == None input, which would indicate an empty graph,
    in which case it does nothing!
    """
    if g is None:
       return
    
    if opts is None:
       opts={}
    fields = collections.defaultdict(set)
    nodes = {}

    def node(x):

        if x not in nodes:
            nodes[x] = "node%d" % len(nodes)
        return nodes[x]

    def label(x, g):

        for labelProp in LABEL_PROPERTIES:
            l = g.value(x, labelProp)
            if l:
                return l

        try:
            return g.namespace_manager.compute_qname(x)[2]
        except:
            return x

    def formatliteral(l, g):
        #sys.stderr.write(f"In formatliteral type(l)={type(l)} \n\t\tl='{l}'\n")
        v = cgi.escape(elision(l,maxl=40))
        if l.datatype:
            return '&quot;%s&quot;^^%s' % (v, qname(l.datatype, g))
        elif l.language:
            return '&quot;%s&quot;@%s' % (v, l.language)
        return '&quot;%s&quot;' % v

    def qname(x, g):
        try:
            q = g.compute_qname(x)
            return q[0] + ":" + q[2]
        except:
            return x

    def color(p):
        return "BLACK"

    stream.write("digraph { \n rankdir=LR;\n node [ fontname=\"DejaVu Sans\" ] ; \n")

    for s, p, o in g:
        sn = node(s)
        if p == rdflib.RDFS.label:
            continue
        if isinstance(o, (rdflib.URIRef, rdflib.BNode)):
            on = node(o)
            opstr = "\t%s -> %s [ color=%s, label=< <font point-size='10' " + \
                    "color='#336633'>%s</font> > ] ;\n"
            stream.write(opstr % (sn, on, color(p), qname(p, g)))
        else:
            fields[sn].add((qname(p, g), formatliteral(o, g)))

    for u, n in list(nodes.items()):
        stream.write("# %s %s\n" % (u, n))
        f = ["<tr><td align='left'>%s</td><td align='left'>%s</td></tr>" %
             x for x in sorted(fields[n])]
        opstr = "%s [ shape=none, color=%s label=< <table color='#666666'" + \
                " cellborder='0' cellspacing='0' border='1'><tr>" + \
                "<td colspan='2' bgcolor='grey'><B>%s</B></td></tr><tr>" + \
                "<td href='%s' bgcolor='#eeeeee' colspan='2'>" + \
                "<font point-size='10' color='#6666ff'>%s</font></td>" + \
                "</tr>%s</table> > ] \n"
        stream.write(opstr % (n, NODECOLOR, label(u, g), u, u, "".join(f)))

    stream.write("}\n")

    # select the most proper elision function depending on output desired,
    # this will evolve into an option
if True:
 def elision(s, maxl=40):
     if len(s) < maxl:
         return s
     else:
         return s[0:maxl-10]+"..."+s[-7:]
else:
 def elision(s, maxl=20):
    if len(s) < maxl:
        return s
    else:
        return "**too long removed**"

    
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
#  this part is derived from
#  lib/python3.6/site-packages/rdflib/extras/external_graph_libs.py
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
#
_identity = lambda x : x
def _rdflib_to_networkx_graph(
        graph,
        nxgraph,
        calc_weights,
        edge_attrs,
        transform_s=_identity, transform_o=_identity):
    """Helper method for multidigraph, digraph and graph.

    Modifies nxgraph in-place!

    Arguments:
        graph: an rdflib.Graph.
        nxgraph: a networkx.Graph/DiGraph/MultiDigraph.
        calc_weights: If True adds a 'weight' attribute to each edge according
            to the count of s,p,o triples between s and o, which is meaningful
            for Graph/DiGraph.
        edge_attrs: Callable to construct edge data from s, p, o.
           'triples' attribute is handled specially to be merged.
           'weight' should not be generated if calc_weights==True.
           (see invokers below!)
        transform_s: Callable to transform node generated from s.
        transform_o: Callable to transform node generated from o.
    """
    assert callable(edge_attrs)
    assert callable(transform_s)
    assert callable(transform_o)
    for s, p, o in graph:
        ts, to = transform_s(s), transform_o(o)  # apply possible transformations
        data = nxgraph.get_edge_data(ts, to)
        if data is None or isinstance(nxgraph, NX.MultiDiGraph):
            # no edge yet, set defaults
            data = edge_attrs(s, p, o)
            if calc_weights:
                data['weight'] = 1
            nxgraph.add_edge(ts, to, **data)
        else:
            # already have an edge, just update attributes
            if calc_weights:
                data['weight'] += 1
            if 'triples' in data:
                d = edge_attrs(s, p, o)
                data['triples'].extend(d['triples'])


def rdflib_to_networkx_digraph(
        graph,
        calc_weights=True,
        edge_attrs=lambda s, p, o: {'triples': [(s, p, o)]},
        **kwds):
    """Converts the given graph into a networkx.DiGraph.

    As an rdflib.Graph() can contain multiple edges between nodes, by default
    adds the a 'triples' attribute to the single DiGraph edge with a list of
    all triples between s and o.
    Also by default calculates the edge weight as the length of triples.

    Args:
        graph: a rdflib.Graph.
        calc_weights: If true calculate multi-graph edge-count as edge 'weight'
        edge_attrs: Callable to construct later edge_attributes. It receives
            3 variables (s, p, o) and should construct a dictionary that is
            passed to networkx's add_edge(s, o, **attrs) function.

            By default this will include setting the 'triples' attribute here,
            which is treated specially by us to be merged. Other attributes of
            multi-edges will only contain the attributes of the first edge.
            If you don't want the 'triples' attribute for tracking, set this to
            `lambda s, p, o: {}`.

    Returns:
        networkx.DiGraph

    """
    if not isinstance(graph, rdflib.Graph):
      raise RuntimeError(f"Expected an rdflib.Graph, received {type(graph)}")
    
    dg = NX.DiGraph()
    _rdflib_to_networkx_graph(graph, dg, calc_weights, edge_attrs, **kwds)
    return dg
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# End of part derived from lib/python3.6/site-packages/rdflib/extras/external_graph_libs.py
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


class NodeRenamer(object):
    def __init__(self, sharedDicts, doInsert=True, **keywds):
        if not isinstance(sharedDicts,  SharedDictPair):
           raise RuntimeError(f"Argument sharedDicts has wrong type {type(sharedDicts)}")
        self.sharedDicts = sharedDicts
        self.doInsert    = doInsert
        self.keywds = keywds

    def rename(self,elt):
        return  self.sharedDicts.rename(elt, doInsert=self.doInsert)

    def revRename(self, nm, **keyArgs):
        return self.sharedDicts.revRename(nm, **keyArgs)

    def printSharedDicts(self,file=None):
        self.sharedDicts.printSharedDicts(file=file)

    def checkSharedDicts(self):
        self.sharedDicts.checkSharedDicts()    
        
class EdgeAttrDict(NodeRenamer):
    "Callable class to be used in rdflib_to_networkx_digraph arg  edge_attrs"

    def __init__(self, sharedDicts, **keywds):
       NodeRenamer.__init__(self,sharedDicts, **keywds ) 
    

    def __call__(self, s, p, o):
        ro = self.rename(o)
        rs = self.rename(s)
        return {'triples': [(rs, p, ro)]}


        
class ObjectTransformer(NodeRenamer):
    "Callable class to be used in  _rdflib_to_networkx_graph transform_o"

    def __init__(self, sharedDicts, **keywds):
        NodeRenamer.__init__(self, sharedDicts, **keywds)

    def __call__(self, o):       
        return self.rename(o)

        
class SubjectTransformer(ObjectTransformer):
    "Callable class to be used in _rdflib_to_networkx_graph transform_s"

    def __init__(self, sharedDicts, **keywds):
          ObjectTransformer.__init__(self,  sharedDicts, **keywds)          
class SharedDictPair(object):
    def __init__(self):
        self._ndNameDict = {}
        self._nameNdDict = {}
        self._nodeCount  = 0
        self._litCount   = 0

    def rename(self,elt,doInsert=False, **keyArgs):
        if isinstance(elt,rdflib.term.BNode ):
           if elt in self._ndNameDict:
              return self._ndNameDict[elt]
           elif   "subst" in keyArgs:
              return keyArgs["subst"]
           elif doInsert:
              self._nodeCount += 1
              s = f"Node{self._nodeCount:04}"
              self._ndNameDict[elt]= s
              self._nameNdDict[s]= elt
              return s
           else:
              raise KeyError(f"Bad key (Node): '{elt}'")   
        elif isinstance(elt,rdflib.term.Literal ):
           if elt in self._ndNameDict:
              return self._ndNameDict[elt]
           elif     "subst" in keyArgs:
              return   keyArgs["subst"] 
           elif doInsert:
              self._litCount += 1
              s = f"Lit{self._litCount:04}"
              self._ndNameDict[elt]= s
              self._nameNdDict[s]= elt
              return s
           else:
              raise KeyError(f"Bad key (Literal): '{elt}'") 
        elif isinstance(elt, rdflib.term.URIRef ):
              return elt      
        else:
              sys.stderr.write(f"In  {type(self)},\t elt<{type(elt)}>\t=\t'{elt}'\n")
              raise RuntimeError(f"Unexpected type for elt: {type(elt)}")

    def search(self,elt):
        return self.rename(elt, doInsert=False, subst=None)
              
    def revRename(self,nm, **keyArgs):
        if nm in  self._nameNdDict:
           return self._nameNdDict[nm]
        if "subst" in keyArgs:
           return   keyArgs["subst"]
        raise KeyError(f"Bad key (Reverse): '{nm}'; keyArg 'subst' not used")
           
    def revSearch(self,nm):
        return self.revRename(nm,subst=None)       

    def printSharedDicts(self, file=None):
        if file is None:
           fd=sys.stderr
        else:
           fd = file
        for f in (self._nameNdDict, self._ndNameDict):   
            fd.write("- * "*20 + "\n")
            for k in sorted( f.keys() ):
                fd.write(f"({type(k)}){k}\t=>'{f[k]}'\n")
            fd.write("* + "*20 + "\n\n")

    def checkPresent(entry, where="both"):
        retval = 0
        if where in ("both","direct"):
           if entry in self._nameNdDict:
              sys.stderr.write("Entry {entry} not absent from direct( name -> Node)")
              retval += 1
        if where in ("both","reverse"):
           if entry in self._ndNameDict:
              sys.stderr.write("Entry {entry} not absent from reverse (Node -> name)")
              retval += 2 
        return retval
    def checkSharedDicts(self):
        dictList =  (self._nameNdDict, self._ndNameDict)
        errs = 0
        for i in (0,1):
           d1 =  dictList[i]
           d2 =  dictList[(i+1)%2]
           for (k,v) in d1.items():
              if  d2[v] != k :
                  errs+=1
                  sys.stderr.write(f"Error at k='{k}', v='{v}'\t reverse:'{d2[v]}' != '{k}'\n")
                  sys.stderr.write(f" reverse   '{d2[v]}' maps to '{d1[d2[v]]}'\n")
        sys.stderr.write(f"Checked shared dicts: {errs} errors (dict sizes={len(self._nameNdDict)},{len( self._ndNameDict)})\n")
        if errs > 0:
           errfd  = open("/tmp/dictErrors","w")
           self.printSharedDicts(file=errfd)
           raise RuntimeError("Incompatible graph translation dictionaries, see files in /tmp")

class RdflibToNxGraphPair(object):

    def __init__(self, sharedDictPair=None):
        if sharedDictPair is None:
            self.sharedDicts = SharedDictPair()
        else:
            if not isinstance(sharedDictPair, SharedDictPair):
               raise RuntimeError(f"Invalid sharedDictPair type:{type(sharedDictPair)}")
            self.sharedDicts = sharedDictPair
           
    def mkNxGraph(self,g):
            self.do_edge_attrs     =   EdgeAttrDict(self.sharedDicts)
            self.do_object_trans   =   ObjectTransformer(self.sharedDicts)
            self.do_subject_trans  =   SubjectTransformer(self.sharedDicts)
            self.rdfGraph          =  g
            self.nxGraph = rdflib_to_networkx_digraph(g,
                                                 edge_attrs=   self.do_edge_attrs,
                                                 transform_s=  self.do_subject_trans,
                                                 transform_o=  self.do_object_trans  )
            return self.nxGraph
if False:
  # This code is specific to some other project, needs adaptation/or being dropped
  # Kept around in case it might prove handy
  # see "uid" etc...
  raise NotImplementedError("Code needs adaptation !! TBD ?")
  class SubgraphSelector(object):
    def __init__(self, rdfGraph, nxGraph, nodeRenamer, nodeStyleBNode=True):
        self.g = rdfGraph
        self.nxGraph = nxGraph
        self.nodeRenamer = nodeRenamer
        self.nodeStyleBNode = nodeStyleBNode
        if not (     isinstance(rdfGraph,Graph)
                and isinstance( nxGraph,  NX.classes.digraph.DiGraph)
                and isinstance( nodeRenamer,  NodeRenamer) ):
            sys.stderr.write(f"In  SubgraphSelector rdfGraph:{type(rdfGraph)}\tnxGraph:{type(nxGraph)}\tnodeRenamer:{type(nodeRenamer)}\n")
            raise RuntimeError(f"Wrong argument type")

    #specsDecKeys    = ("uid", "puid","frex","trex" )
    #specsDecDtls    = ("dist","sym", "selmeth")
    specsDecodeKwds = (* specsDecKeys, *specsDecDtls )
    def _specsDecode(self, specs):
        if isinstance(specs,dict):
           specdir =  self._specsFromDict(specs)
        else:
            #  Specs :
            #          uid=val
            #          puid=val
            #          frex=regexp (without chars ``='' or ``:'') 
            #          trex=regexp (without chars ``='' or ``:'') 
            #          dist=val
            #          sym=true|false
            specdir = { z[0]:z[1] for z in map( lambda x:  x.split("="), specs.split(":")) }

        badSpec = [z for z in specdir.keys() if z not in SubgraphSelector.specsDecodeKwds]
        if len(badSpec) > 0:
           raise RuntimeError("Bad specification(s) entered:{', '.join(sorted(badSpec))}")

        kwdl = [ x for x in specdir.keys() if x in SubgraphSelector.specsDecKeys ]
        if len(kwdl) == 1 :  
           (key,kval) = ( kwdl[0], specdir[kwdl[0]])
        elif len(kwdl) == 0:
           (key,kval)=  (None, None)
        else:
           raise RuntimeError(f"Multiple kwd specifications is ambiguous, conflict:{kwdl}")
        
        if "dist" in specdir:
            dist =  int(specdir["dist"])
        else:
            dist = 4
    
        if "sym" in specdir:
           sym = specdir["dist"].lower() == "true"
        else:
           sym = False
        if "selmeth" in specdir:
            selmeth =  specdir["selmeth"]
        else:
           selmeth = None    
        return(key, kval, dist, sym, selmeth)    
    def _specsFromDict(self,specs):
        return specs
              
    def _buildQuery(self, key, kval):
        queryKeys = {"uid": "Uid", "puid":"PersonUid", "frex":"Filename", "trex":"Text"}
        if key not in queryKeys:
           allowedKeys = sorted(queryKeys.keys())
           sys.stderr.write(f"key='{key}' not in {allowedKeys}")
           raise RuntimeError(f"invalid select graph specication: '{specs}'")
        debugPrint = False
        if key == "frex":
           filterClause=f"FILTER regex(?val,\"{kval}\")"
           kval="?val"
           debugPrint = True
        elif key == "trex":
           filterClause=f"FILTER regex(?val,\"{kval}\")"
           kval="?val"
           debugPrint = True
        else:
           filterClause=""
           kval="'" + kval + "'"

        querybase = """    PREFIX ns1:<http://localhost/added> 
                       PREFIX rdf:<http://www.w3.org/1999/02/22-rdf-syntax-ns#>
                       PREFIX dc:<http://purl.org/dc/elements/1.1/>
             SELECT DISTINCT ?rtype ?a ?key ?val
             WHERE { 
             ?a  rdf:type       ?rType .
                 ?a  ns1:%s         %s   .
                 %s }   
                  ORDER BY   ?rtype ?a   ?val            
        """
        query  = querybase  % ( queryKeys[key], kval, filterClause)

        if key == "trex": 
             queryAlt = querybase % ("Literal" , kval, filterClause)
             query    = (query, queryAlt)
        if debugPrint:
           if isinstance(query,str):     
                print (f"Query is : {query}")          
           else:
                print("Queries are:")     
                for q in query:
                   print(f"{q}\n")
        return query
    def _graphSelectExtract(self, qresult, dist, sym, selmeth,
                                  resultType=NX.classes.digraph.DiGraph):

        sys.stderr.write(f"In  _graphSelectExtract selmeth={selmeth} len(qresult)={len(qresult)}\n")
        subNxCombi = None
        rdfNodes   = list( set( [ row[1] for row in qresult] ) )
        for rdfNode in rdfNodes:
             if self.nodeStyleBNode:
                nodeId =  rdfNode
             else:
                nodeId = self.nodeRenamer.rename(rdfNode)
             if not nodeId in self.nxGraph:
                     sys.stderr.write(f"Node nodeId:{nodeId} not found\n ")
                     sys.stderr.write(f"Nodes are {[ n  for n in self.nxGraph ] }\n")
                     sys.stderr.write(f"Probable wrong use of init parameter nodeStyleBNode={nodeStyleBNode}\n")
             if selmeth is None or selmeth == "maxdist":
                 subNxG = NX.ego_graph(self.nxGraph, nodeId,radius=dist,undirected=sym)
             elif  selmeth == "sameCC":
                 sys.stderr.write(f"\tlooking near node nodeId={nodeId}; rdfNode={rdfNode} \n")
                 subNxG =    self._get_weakly_connected_comp(nodeId) 
             else:
                raise RuntimeError("Bad selmeth value:'{selmeth}'")

             if subNxCombi is None:
                subNxCombi = subNxG
             else:
                subNxCombi = NX.compose( subNxG, subNxCombi )
        if resultType !=  rdflib.graph.Graph:
           return subNxCombi
        
        selGraph = rdflib.Graph()
        if not  subNxCombi is None:       
            nxKeptNd  = subNxCombi.nodes()
            rdfKeptNd = list(map (lambda x: self.nodeRenamer.revRename(x,subst=None)  ,nxKeptNd ))
            for (s,p,o) in self.g:
                if s in  rdfKeptNd:
                    selGraph.add( (s,p,o))
        
        return selGraph
    def _get_weakly_connected_comp(self,nxNode):
        for cc in NX.weakly_connected_components(self.nxGraph):
            if nxNode in cc:
               return self.nxGraph.subgraph(cc.copy())
        return None
    def selectSubgraph(self, specs = None, doDebug=False,
                             resultType=NX.classes.digraph.DiGraph,  **keyArgs  ):
        (key, kval, dist, sym, selmeth)  = self. _specsDecode( specs )
        query = self._buildQuery( key, kval)
        if doDebug:
            sys.stderr.write(f"Query submitted:{query}\n")
        if isinstance(query, str):
           qresult = self.g.query(query)
        else:
           qresult = []
           for q in query:
              qr = self.g.query(q)
              qresult.extend(qr)

        if qresult is None or len(qresult) == 0:
            if doDebug or True:
                sys.stderr.write(f"In selectSubgraph empty result from query\n\t{query}")
            return None
        return self._graphSelectExtract( qresult, dist, sym, selmeth, resultType =resultType )
    def selectSubgraphNX(self,specs = None, doDebug=False,  **keyArgs):
        return self.selectSubgraph(specs=specs, doDebug=doDebug,
                                   resultType = NX.classes.digraph.DiGraph, **keyArgs )
    def selectSubgraphRDF(self,specs = None, doDebug=False,  **keyArgs): 
        return self.selectSubgraph( specs=specs, doDebug=doDebug,
                                    resultType = rdflib.graph.Graph, **keyArgs )

