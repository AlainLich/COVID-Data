#!/usr/bin/python3
# -*- coding: utf-8 -*-
# -*- mode: Python -*-
#
# (C) Alain Lichnewsky, 2019, 2020
#

__author__ = 'Alain Lichnewsky'
__license__ = 'MIT License'
__version__ = '1.0'

import sys
from sys import exit, exc_info, stdout, stderr, stdin

import collections
from collections import Iterable, Mapping
from copy import copy, deepcopy
import enum 
import re

import rdflib
from rdflib import XSD, util
from rdflib import Graph, Literal, BNode, Namespace,  RDF, URIRef
from rdflib.namespace import NamespaceManager
from lxml import etree 
import pyparsing

import lib.RDFNameSpaces as RDFNS

class WithRDFSerialize(object):
        """ Facilitate the utilization of an RDF database in the form of an RDFLib tree
        """        
        def __init__(self, doDebug = False):
             self.doDebug = doDebug
             self.rdfGraph = Graph()

             self.NMgr     = NamespaceManager(self.rdfGraph)
             for (k,v) in RDFNS.nsTable.items():
                     self.NMgr.bind(  k, v[1] )
             
        def dump(self):
             for s, p, o in self.rdfGraph:
                 print((s, p, o))
                 
        def outputSerial(self, filename, serFmt="n3"):
             if self.doDebug:
                 stderr.write(f"In WithRDFSerialize.outputSerial serializing to file {filename} graph len={len( self.rdfGraph)}\n")         
             self.rdfGraph.serialize(filename, format=serFmt)

        def inputSerialString(self,s,  serFmt="application/rdf+xml"):
             """  Loads data from a string, use inputSerial to input from
                  file.This handles the formats that RDFLib handles.

                  This handles a straight RDF+XML file, will not work with SPARQL Query Results XML Format
                  for which it is required to use a separate parser to translate first to RDF+XML. 
                  Such a parser is available as the method XMLtoRDF.parseQueryResult.
             """
             graph = self.rdfGraph
             sys.stderr.write("Reading rdf from string/bytes")
             if isinstance(s,bytes):
                try:
                    ds = s.decode("utf-8")                    
                    graph.parse( data = ds, format="xml" )
                except Exception as err:
                    dumpFname = "/tmp/dumpXMLRDF.txt"
                    print (f"An exception has occurred while parsing {serFmt}; input written to {dumpFname}:")
                    print (f"Error information:{err}")
                    fd = open(dumpFname,"w")
                    fd.write(ds)
                    fd.close()
                    raise err
             else:
                graph.parse( data = s , format=serFmt)
                     
             sys.stderr.write("[done]\n")
             if self.doDebug : print(f"Parsed from string/bytes of len={len(s)}")
             
        def inputSerial(self, filenames, serFmt="n3"):
             if isinstance(filenames, str):
                 parseMultipleIntoGraph(self.rdfGraph, [filenames], format=serFmt)
             elif isinstance(filenames, Iterable):     
                 parseMultipleIntoGraph(self.rdfGraph, filenames)
             elif filenames is None:
                 parseMultipleIntoGraph(self.rdfGraph, filenames, format=serFmt) 
             else:
                 raise RuntimeError(f"Ill typed filenames:{type(filenames)}'{filenames}'")

             if self.doDebug : print(f"Parsed {filenames}")



class XMLtoRDF(WithRDFSerialize):
    def __init__(self, optdict):

        if hasattr(self, "options"):
             setDefaults(self.options, optdict)
        else:
            self.options = optdict            

        self.internNodeCtr=0
        WithRDFSerialize.__init__(self, optdict["--debug"])
        for (k,v) in RDFNS.nsTable.items():
            if k == "xml":
                    continue
            etree.register_namespace(k, v[0])

    	    # some special identifiers
    ns_attributes= {"inid" : RDFNS.nsTable["N"][1].inid,
                    "text" : RDFNS.nsTable["N"][1].text,
                    "lang" : RDFNS.nsTable["X2R"][1].lang,
                    "nodeID" : RDFNS.nsTable["X2R"][1].nodeID,
                    "resource" : RDFNS.nsTable["X2R"][1].resource,                    
    }

    def parseQueryResult(self, inFileName=None, inString=None):
        """
          Inputs/Parses SPARQL Query Results XML Format into an RDFLib tree,
          from a file or a string. Result is made available in 
          attribute self.rdfGraph.

          To use this in order to initialize an instance of WithRDFSerialize,
          first input the textual data into self.data of the instance,
          then:
            xmlParser = RDFQ.XMLtoRDF(optdict)            
            xmlParser.parseQueryResult(inString=self.data)
            # transfer the rdflib tree resulting of the parse:
            self.dataQuery.initFromXMLtoRDF( xmlParser, copy = None)

          The rationale for flattening into triples is described on 
                ```https://www.w3.org/2001/10/stripes/ 
                   RDF: Understanding the Striped RDF/XML Syntax
                   Author: Dan Brickley (danbri@w3.org)
		```
        """
        if self.doDebug :
               if inFileName:
                       print(f"retrieving XML data from file {inFileName}")    
               else:
                       if isinstance(inString, str):
                           s = inString
                       else:
                           s = inString.decode('utf-8')
                       print(f"retrieving XML data from string '{s[:100]}'")
                       
                       dumpFname = "/tmp/dumpXMLRDF.txt"
                       print(f"Copied XML data string to file {dumpFname}")
                       with open(dumpFname,"w") as fd:
                         fd.write(s)
                         fd.close()

                        
        parser = etree.XMLParser(ns_clean=True, remove_blank_text=True, remove_comments=True)
        if inFileName is not None:
            self.tree = etree.parse(inFileName, parser)
        elif inString  is not None :
            self.tree = etree.fromstring(inString, parser)
        else:
            raise RuntimeError(f"You must specify either inFileName or inString (got {inFileName} and {inString})")

        self.items()
        
        lenErrlog = len(parser.error_log)
        print (f"Parser error log has len:{lenErrlog}")
        if lenErrlog > 0:
           print (f"Parser error log has len:{lenErrlog}")
           i = 0
           for err in parser.error_log:
               print (f"\tErr ({i}):\t{err}")
               i += 1
           print("+"*12 + "\n")
        if self.doDebug : self.dump()

       
    def dump(self):
       s = etree.tostring(self.tree, pretty_print=True)
       print(f"{s.decode('utf-8')}")

    def walk(self):
        for e in self.tree.iter():
             s =  etree.tostring(e, pretty_print=True)
             print(f"<{e.tag}>\t::=> {e.attrib}")
             sys.stdout.buffer.write(s)     # this handles utf8 chars

    def _keyToNSattrib_Clark(self, key):
        """  Sort out namespace issues, in particular when Clark notation is 
                 involved. 

            
        """
        retval = None
        if key[0] == "{":
            tag = etree.QName(key)
            if self.doDebug:
               print (f"_keyToNSattrib_Clark : key='{key}'\n\t => tag=({type(tag)})'{tag}'")
               print (f"\t\t\ttagNS:'{tag.namespace}'\ttabLOCAL:'{tag.localname}'")

            if tag.namespace in   RDFNS.nsTableInv:
                    shortNS =  RDFNS.nsTableInv[tag.namespace]
                    if tag.localname in XMLtoRDF.ns_attributes:
                        retval = XMLtoRDF.ns_attributes[tag.localname]
                    elif shortNS in  ("xml", "rdf", "res"):
                        retval = RDFNS.nsTable[shortNS][1][tag.localname]
                        
            if self.doDebug:
                print(f"In _keyToNSattrib_Clark key={key} tag.localname={tag.localname}, tag.namespace={tag.namespace}")
                print(f"\treturning: ({type(retval)}:{retval})")
                if retval == None:
                        print(f"TableInv={RDFNS.nsTableInv}")

        return retval

    def keyToNSattrib(self, key):
       
       ret=self._keyToNSattrib_Clark(key)
       if self.doDebug:
             print(f"keyToNSattrib entered with ({type(key)}{key})")
             print(f"\treceived from _keyToNSattrib:({type(ret)}{ret})")
       
       if not (ret is None):
            return ret

       if key in XMLtoRDF.ns_attributes:
                   return  XMLtoRDF.ns_attributes[key]
       
       raise NotImplementedError(f"Hum this started with key={key} and now ret={ret}")
    
    def items(self):
        """
          Iterates through subtrees of a node; sorts out some typing issue at the root.
        """
        if isinstance( self.tree, etree._Element):
                root = self.tree
        else:
                root = self.tree.getroot()
        for e in root:
            self.doItem(e)

    def doItem(self,e, recurDepth=0, lowerTList=None):
        """ Recursive descent parser, try to fill the predicate field of triples
            returns a pair :
                   - the root node of what has been generated
                   - a predicate to explain how this nodes fits into parent
        """
        def addGraph(triplet):
             dd = [ f"{type(xx)}{xx}" for xx in triplet]
             ee = '\n\t\t'.join(dd)
             try:
                self.rdfGraph.add( triplet )
             except Exception as err:
                print(f"failed attempt to add to graph node {triplet}")
                print(f"error: ({type(err)}):{err}")
                raise err

        if not isinstance(e, etree._Element):
                raise RuntimeError(f"Expected type:  lxml.etree._Element; real:{type(e)}")

        localNS = RDFNS.nsTable["N"][1]
        
        if lowerTList is None:
           lowerTList = []
        textList = []
        if recurDepth > 0:
           self.internNodeCtr+=1
           internNId = f"__in_{self.internNodeCtr:05}"
           # lowerTList.append("<@"+internNId+"@>")
           
        if self.doDebug :
           print(f"doItem (@{recurDepth}) called with elt of {type(e)}")
        
        if not isinstance (e.tag,str):
           print(f"Ignored e={e} of type:{type(e)}\n\tsince e.tag has non string type:,e.tag={e.tag}")
           return
           
        nd = BNode()
        tagWithNS =   self.keyToNSattrib(e.tag)
        insertAsPredicate =  tagWithNS 
        if self.doDebug:
                addGraph( (nd, RDF.type, tagWithNS ))

        # add information on node depth since flattening (probably for debugging mode)        
        if recurDepth > 0 and self.doDebug:
            addGraph( (nd,  self.keyToNSattrib("inid"), Literal(internNId)))
        
        if self.doDebug:
           print(f"\tTAG::<{e.tag}>\tdepth={recurDepth}\t::=> ATTRIB::{e.attrib} </>\n")
           print(f"\telt has keys:{sorted(e.keys())}")
           print(f"\ttext:{e.text}\n\ttail:'{e.tail}' ")
           #sp = "\ttoStr\t" +"\t\t>>".join( str(s).split("\n"))
           #if len(s) > 0 : sys.stdout.buffer.write(bytes(sp, 'utf8'))
           print("\tEND-TAG")

        # these are text elements
        if e.text:
            textList.append(e.text)
        if e.tail:
            lowerTList.append(e.tail)
            
        addGraph( (nd,  RDF.type, tagWithNS))
        if recurDepth > 0 and self.doDebug:
           addGraph( (nd,  localNS.nodeDepth, Literal(recurDepth)))

        # emit triples for attributes
        for (k,v) in e.attrib.items():
           kToNS = self.keyToNSattrib(k)
           if self.doDebug:
               print(f"Attribute k='{k}'\tv=({type(v)})'{v}'\n\t\tkToNS:({type(kToNS)})'{kToNS}'")
           addGraph( (nd, kToNS , Literal(v)))

        # deal recursively with children
        chs = e.findall("*")

        if chs is not None:
           reflist =  []
           for c in chs:
               if self.doDebug:   
                   print(f"\n**\telt_child: c={c}\ttype(c)={type(c)}")          
                   print(f"\telt_child\t==>\n\ttag={c.tag}\n\tattribs={c.attrib}\n\titems()=>{c.attrib.items()}")
               #recursive call
               (ref,suggestP) = self.doItem(c, recurDepth = recurDepth+1, lowerTList = textList)
               if suggestP is None:
                       addGraph( (nd, localNS.subnode, ref))
               else:
                       addGraph( (nd, suggestP, ref))
                       

        if self.doDebug:
            sep = '\n  t::\t'
            if len(textList) > 0:
                  print(f"\ttextlist={ textList}")
            if recurDepth == 0 and len(lowerTList) > 0:
                  print(f"\tlowerTList={ lowerTList}")

        if len(textList) > 0:
            addGraph( (nd,  self.keyToNSattrib("text"), Literal("".join(textList))))
        if  recurDepth == 0 and len(lowerTList) > 0:
            addGraph( (nd,  self.keyToNSattrib("text"), Literal("".join(lowerTList))))

        return ( nd,  insertAsPredicate)


             
def parseMultipleIntoGraph(graph, files, format=None ):
    if len(files) == 0 and stdin:
        sys.stderr.write("Reading from stdin as %s..." % f)
        graph.parse(sys.stdin, format=f)
        sys.stderr.write("[done]\n")
    else:
        size = 0
        for x in files:
            if format is None:
                format = util.guess_format(x)
            sys.stderr.write("Loading %s as %s... " % (x, format))
            graph.parse(x, format=format)
            sys.stderr.write("done.\t(%d triples)\n" %    (len(graph) - size ))
            size = len(graph)
    return size

class QueryFromRdf( WithRDFSerialize):
    def __init__(self, doDebug = False):
         WithRDFSerialize.__init__(self, doDebug=doDebug)

    def initFromXMLtoRDF(self, xtr, copy=False):
         """Initialize from an existing instance of  XMLtoRDF
            copy : "deepcopy" : perform a deep copy
                 : True : shallow copy
                   False/None : assign/alias
         """ 
         if not isinstance(xtr, XMLtoRDF):
                 raise RuntimeError(f"Initialization supported only from XMLtoRDF, received:{type(xtr)}")
         if copy == "deepcopy":
            self.rdfGraph = deepcopy(xtr.rdfGraph)
         elif copy:
            self.rdfGraph = copy(xtr.rdfGraph)
         else:
            self.rdfGraph = xtr.rdfGraph
            
class QueryDispatcher( QueryFromRdf):
    """ Add ability to perform SPARQL Queries
    """
    def __init__(self, optdict):
        QueryFromRdf.__init__(self, optdict)
        self.querySelectAllowed = {}
        self.queryPredefRex = { k:re.compile(v) for k,v in { \
                                "any"   : ".*",
                                "iduid" : ".*[Ii]d" 
                               }.items()}

    def query(self, q):
        try:
            ret = self.rdfGraph.query(q)
        except pyparsing.ParseException as err:
            sys.stderr.write(f"Parsing error on line:{err.lineno} and col:{err.col}\n")
            sys.stderr.write(f"Query:\n")
            qs = q.split("\n")
            i = 0
            for ql in qs:
                i+=1
                sys.stderr.write(f"{i:2}:{ql}\n")
            sys.stderr.write(f"\nError on line:{err.lineno} and col:{err.col}:\n")
            sys.stderr.write(f"\t{err.line}\n")
            sys.stderr.write("\t" + " " * (err.col-2) + "^!^\n")
            raise err
        except Exception as err:
            sys.stderr.write(f"An error has occurred while processing query\n{q}\n")
            raise err
        return ret
        
    rexSelectOpt = re.compile("^\(\?#([^)]+)\)(@?~?)")
    def dispatch(self,regexp, **optkeys):
        """This query applies to RDF files and queries predicate/values for predicates
           matching regexp; regexp is further encoded to select queries, lookup in docopt
           for this file!
        """
        if "printer" in optkeys:
           self.printer =  optkeys["printer"] 
        rm  =   QueryDispatcher.rexSelectOpt.match(regexp)
        if rm :
           gr = rm.groups()
           if len(gr) > 2 or ( len(gr)==2 and  gr[1] not in ('','@','~','@~')):
              print(f"checking regexp returns groups={gr} ")   
              raise RuntimeError("bad regexp argument %s" % regexp)
           opt = gr[0]
           if not opt in self.querySelectAllowed:
              raise  RuntimeError("bad selector option %s (allowed: %s)" % \
                                   (opt,QueryRDF.querySelectAllowed.keys()))
           else:
                negate =  gr[1] in ('~','@~')                
                usePredefRex =  len(gr)==2 and gr[1] in ('@','@~')
                #print (f"QueryDispatcher.dispatch predef={usePredefRex} neg={negate}")
                if usePredefRex:
                   predef = regexp[ (rm.span()[1]) : ]
                   if predef not in self.queryPredefRex:
                       raise  RuntimeError("bad predefined regexp  '%s' (allowed: %s)" \
                       %   (predef, self.queryPredefRex.keys()))
                   if self.doDebug:
                       print(f"using regexp '{self.queryPredefRex[predef]}' selector={predef} negate={negate}")    
                   return self.querySelectAllowed[opt](self.queryPredefRex[predef], negate) 
                else:
                    # here we do not need to extract, the opt has been hidden in a comment
                    rex = re.compile(regexp)
                    return self.querySelectAllowed[opt](rex, negate) 
        else:
           rex = re.compile(regexp)         
           return self.queryPredValDefault(rex)


