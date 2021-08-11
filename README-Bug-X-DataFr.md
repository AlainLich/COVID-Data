# Chasing changes in data.gouv.fr's behaviour

## TOC
<!--TOC-->

- [Chasing changes in data.gouv.fr's behaviour](#chasing-changes-in-datagouvfrs-behaviour)
  - [TOC](#toc)
  - [Symptom](#symptom)
    - [First findings:](#first-findings)
  - [Information about data.gouv.fr](#information-about-datagouvfr)
    - [Tags related to covid](#tags-related-to-covid)
    - [Obsolete data](#obsolete-data)
  - [Changes and additions](#changes-and-additions)
    - [Specifying API requests](#specifying-api-requests)
    - [Changes](#changes)
    - [For consideration](#for-consideration)
    - [Tests](#tests)
- [References](#references)

<!--TOC-->


## Symptom
Around august 2021, the data portion of the `.cache.json`came back empty, 
entailing:
 - no data update in the cache and
 - no data addition, complaint about non exploited data and the like
 
 
### First findings:
1. **badges** (not tags) 'covid' or 'covid-19' do not work, not used to 
   label COVID related stuff
1. API offers more resources like `datasets/suggest`	 
	 
## Information about data.gouv.fr
### Tags related to covid

1. Tags starting with `covid`, are obtained as shown, score gives numbers of entries
~~~
curl -X 'GET' https://www.data.gouv.fr/api/1/tags/suggest/?q=covid&size=8 \
   -H 'accept: application/json'

[{"score": 39.0, "text": "covid"}, 
 {"score": 89.0, "text": "covid19"}, 
 {"score": 89.0, "text": "covid-19"}, 
 {"score": 89.0, "text": "covid2019"}, 
 {"score": 6.0, "text": "covidfrance"}, 
 {"score": 3.0, "text": "covidtracker"}, 
 {"score": 19.0, "text": "covid19france"}, 
 {"score": 4.0, "text": "covid-tracker"}]
~~~

1. Tag 'spf' also interesting, designates "Sante Publique France" 

1. using API `datasets/?tag=` may result in a large JSON file
   ~~~
   curl -X 'GET' 'https://www.data.gouv.fr/api/1/datasets/?tag=covid&page=0&page_size=20'
        -H 'accept: application/json'  
   curl -X 'GET' 'https://www.data.gouv.fr/api/1/datasets/?tag=spf&page=0&page_size=20' 
       -H 'accept: application/json'  
   ~~~


### Obsolete data 
Some data has become obsolete, otherwise some indexing method are not available 
anymore for the data I am looking for
  + Obsolescence
    1. `donnees-tests-covid19-labo...`
	 
	   > Depuis le 29 mai 2020, ce jeu de données n'est plus mis à jour.
	   > Le système d’information national (SIDEP) de dépistage du Covid-19 est
	   > désormais le système qui fait référence. Vous pouvez retrouver les données
	   > de résultats de tests sur le jeu de données "Données relatives aux résultats
	   > des tests virologiques COVID-19".

       + New data: 
		https://www.data.gouv.fr/fr/datasets/donnees-relatives-aux-resultats-des-tests-virologiques-covid-19/
		with tags 	coronavirus, covid-19, covid19, depistage, si-dep
        and files
		+ sp-pos-heb-2020-07-01-19h15.xlsx   
		+ sp-pos-heb-fra-2021-08-09-19h06.csv  
		+ sp-pos-heb-dep-2021-08-09-19h06.csv   
		+ sp-pos-quot-reg-2021-08-09-19h06.csv
        + sp-pos-quot-2020-07-03-19h15.xlsx  
		+ sp-pos-heb-reg-2021-08-09-19h06.csv  
		+ sp-pos-quot-fra-2021-08-09-19h06.csv  
		+ sp-pos-quot-dep-2021-08-09-19h05.csv

  + indexing
    1. `datasets/badges`: not available anymore for `covid`, compare code
	    in classes  `manageAndCacheDataFilesFRAPI` and  `manageAndCacheDataFilesFRDG`
## Changes and additions
  
### Specifying API requests
1. In the classes developped here
   + In lib.DataMgrJSON, options ApiInq, ApiHeaders, InqParmsDir permit to
     perform API http request

   ~~~
   class manageAndCacheDataFilesFRDG ( manageAndCacheDataFilesJSON)
   defaultOpts = {'HttpHDR'      : 'https://www.data.gouv.fr/api/1',
                    'ApiInq'       : 'datasets',
                   'ApiHeaders'   : {},
                   'InqParmsDir'  : {"badge":"covid-19", "page":0, "page_size":30}, ...
   ~~~

### Changes
1. We add a derived class able to handle selection starting from a list of tags.

   `self.rqtParms` is list of pairs: (APIInq, APIParm) 
    1. _getRemoteMetaFromServer will assemble and execute 1 request per list elt
	2. The result will be assembled/merged in a list (there are some issues
	   still unresolved with this approach)
	3. each HTTP request is formed:
	   +  HttpHDR (see elsewhere)
	   +  Expansion of APIInq
	   +  Expansion of  APIParm
		
1. Request list generation
   - done in ` manageAndCacheDataFilesFRAPI._getRemoteMetaFromServer`
   - uses a parameter generator (built with yield) and the assembly capabilities
	 of the `requests` Python package ( see https://docs.python-requests.org/en/master/)
	 using methods `get` or `post`
   - **Note**: it may make sense to move this function to the parent class, however
     this may require that we have the ability to do a full review of tests (*and
	 there are problems in EURdf...*)

1. Parametrization of the cache file (.cache.json), was already available via
   option  '`cacheFname`'. 
   
   Now that we have general requests it might be appropriate to use different 
   cache files (and even to memoize based on the request's hash?)
   
   
1. Dump / formatted dump / interrogation of (cached) json   
   +  method `getRemoteInfo` has parameter `localOnly`(default False)
   +  Dump Cached info using option parameters 
      ~~~
      { 'cacheFname': '.cache.rqtTest6.json',
        "dumpMetaFile" : "rqtTest6.meta.dump",
        "dumpMetaInfoFile" : "rqtTest6.metainfo.dump"
      }
      ~~~
	  
   +  See how the meta information dumped can be used, eg. as a json?
   
   
1. What happens after we have loaded the cached data? 
   + normal sequence is 
     ~~~
     dataFileVMgr.updatePrepare()
     dataFileVMgr.cacheUpdate()
     ... = dataFileVMgr.getRecentVersion(x,default=..)
     ~~~
	 
   + adding a method `updateSelect` which operates on (and modifies) `self.updtList`	 
   
   
### For consideration

1. Issues:
   + Bad Checksum indication:
     + improved error message
	 + need to add a feature for disabling checksum verification 
     Bad checksum for ../data/donnees-hospitalieres-covid19-2021-08-08-19h05.csv 
	    comp:e3e838acde3ce0880d9257d04cca118985852931 
		reference:c974f46509e985d6ffecc3e6e0e6e2afe94a564d


   
### Tests
Adding tests in testDataMgr.py, to cover a (small) list of API capabilities

1. Test  0: Default -> tag 'spf'

   + OK tag, data does not seem well transfered to cache file (?)
   + **Note** went through a timeout error, error message does not show url, could be
	 improved

1. Test  1: tag 'spf'
   + After analysis: sursaud does not appear
   + OK tag, data seems transfered to cache file, may have issue there with outer
	 list
		 
1. Test  2 : tag sets 
   + smaller tagset :        tag : (covid,covid19) Uncovers 5 sursaud files
          OK, adjusted timeout
		  
   + larger tagset :  Uncovers 5 sursaud files, seems that the smaller tagset is 
		  sufficient
     ~~~
     egrep "'url.*sursaud" data4debug/rqtTest2.meta.dump  |sort |uniq
     egrep "'title.*sursaud" data4debug/rqtTest2.meta.dump  |sort |uniq   
     ~~~

   + further analysis is done **in this test** calling method `updatePrepare`.
     + missing information in `UpdateRqt`
	   1. distinguished org and orgslug (what about org. page or uri?)
	   1. used to `url` mean `latest`, now both are transmitted

1. Test  3 : datasets/suggest: q=covid
   + brings 126 pages, with very synthetic information, not size limited 
		  (size parameter)
     ~~~
     grep page  data4debug/rqtTest3.meta.dump  |sort
     grep slug  data4debug/rqtTest3.meta.dump  |sort 
     ~~~

   + can check all different with `uniq | wc`

1. Test  4 : tags/suggest:
   + brings 14 tags possibilities, not size limited (changed size parameter)

1. Tests 5:  tags/suggest: 
   + test 2 sizes, really a test of list handling in specOpts
     ~~~
     sed -e 's/.*text//;s/}.*//' data4debug/rqtTest5.meta.dump |sort |uniq|wc
     ~~~


1. Tests 6: tags suggest 2 sizes, 2 strings (prefix) 
   + really a test same result   (after sed stripping, sorting..)



# References

1. Modele Microsoft Imperial College
https://github.com/mrc-ide/covid-sim


1. Suivi
  - https://www.data.gouv.fr/en/posts/les-nouveautes-data-gouv-fr-de-lete-2020/
  - Vous pouvez retrouver dans cet article les principales évolutions.
    Au programme :

    1. L’arrivée des pages inventaires ;
    1. L’intégration de schema.data.gouv.fr à data.gouv.fr ;
    1. Un guide sur les référentiels de données ;
    1. Plus de synergies entre api.gouv.fr et data.gouv.fr ; 
	   + voir aussi https://api.gouv.fr/les-api/api_data_gouv
	   + https://api.gouv.fr/documentation/api_data_gouv
	   
    1. La refonte et l’extension du système de recommandations.

  - En plus, pour faciliter la recherche et la découverte des jeux de données pertinents, 
    les pages index sont mises en place
    https://www.data.gouv.fr/fr/pages/donnees-coronavirus/




