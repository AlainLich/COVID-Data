# Resolution of EU Site SPARQL related bug

This was found around early April 2021, it may have occurred a few days
before. This notice is kept for documentation purposes.

## Error message

~~~
Status:500:internal_server_error
Please check http request code above; if transient network/server issue, just retry!
Additional information received:
<p>Virtuoso 42000 Error The estimated execution time 6469 (sec) exceeds the limit of 400 (sec).
~~~

**Cause**: the SPARQL request requires too much processing.

**Remark**: this limit was not exceeded until end march 2021, development was done
on older release, see below for release information.


### Information from data.europa.eu
Concerning the arrangement of information from the EU portal,
  - The API is at "https://data.europa.eu/euodp"
  - useful information is found at 
	- https://data.europa.eu/euodp/fr/developerscorner
    - https://app.swaggerhub.com/apis/EU-Open-Data-Portal/eu-open_data_portal/0.8.0#/admin/packageSearchPost
    - https://www.datacareer.de/blog/eu-open-data-portal-api/


  - Information concerning the SPARQL database (schema update ? size ? encoding):
    1. The release notes are dated 14 July 2020 (After I did my development and
       tested)
       https://joinup.ec.europa.eu/collection/semantic-interoperability-community-semic/solution/dcat-application-profile-data-portals-europe/release/201-0
    2. A complete list of the releases,  issues and their resolution can be found on the 
       DCAT-AP GitHub
       https://github.com/SEMICeu/DCAT-AP/tree/master/releases/2.0.1
	   ( ** see issues / label:release:2.0.1-june2020 ** )
	   
#### Interactive access and trials

  1) "https://data.europa.eu/euodp"
     As shown on the ‘Linked data’ page, a graphical user interface is 
     provided to enter your SPARQL queries. You can enter a request at
     https://data.europa.eu/euodp/en/linked-data
	 
	 


## Response:

1. simplified SPARQL, removing several properties

~~~
PREFIX dcat: <http://www.w3.org/ns/dcat#>
PREFIX odp:  <http://data.europa.eu/euodp/ontologies/ec-odp#>
PREFIX dc: <http://purl.org/dc/terms/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>


SELECT distinct ?g ?title ?dsURI ?DatasetTitle ?Publisher ?Resource 
                    ?ResourceDescription ?frequency ?lang ?mod ?issued ?sz ?dloadurl
WHERE { GRAPH ?g { filter regex(?title, '^COVID.*data', 'i'). 
                   FILTER langMatches( lang(?title), "EN" ).
                   ?dsURI    a    dcat:Dataset.
                   ?dsURI    dc:title ?title .
                   ?dsURI    dc:publisher   ?Publisher . 
                   ?dsURI    dc:title ?DatasetTitle . 
                   ?dsURI    dcat:distribution ?Resource.
                   OPTIONAL { ?dsURI    dc:accrualPeriodicity   ?frequency . }
                   OPTIONAL { ?dsURI    dc:language ?lang. }
                   OPTIONAL { ?dsURI    dc:modified ?mod. }    # rare
                   OPTIONAL { ?dsURI    dc:issued   ?issued. }  # rare
                   OPTIONAL { ?Resource dc:description ?ResourceDescription. }
                   OPTIONAL { ?Resource  dcat:downloadURL ?dloadurl. }
                   OPTIONAL { ?Resource  dcat:byteSize ?sz. }
        }  
} 
  ORDER BY ?title
  LIMIT 100
  OFFSET 0
~~~


2. decided to derive the missing file extension from the file name and/or the
   last directory component of url (apparently redundant on that site)


## Keep in mind (for the developper)

3. if it is required to do more specific request,  the following works: 
~~~

PREFIX dcat: <http://www.w3.org/ns/dcat#>
PREFIX odp:  <http://data.europa.eu/euodp/ontologies/ec-odp#>
PREFIX dc: <http://purl.org/dc/terms/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>

SELECT distinct ?g ?o WHERE { 
  GRAPH ?g {
    ?s dc:title ?o.
    FILTER ( STR(?o) = "Nomenclature .... Units") .
    #filter regex(?o, 'Statistics', 'i') 
  } 
  } 
  LIMIT 10
  
~~~

*Concerning SPARQL*, see https://www.w3.org/TR/rdf-sparql-query/


## TBD
1. process list of files to be loaded, remove multiple representations of same file
   with different extensions
2. note that this must be compatible with all sites, including the French OpenData
