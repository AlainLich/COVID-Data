# Information on Data Sets

## Goal
As time advances, we become aware of more and more sets of information and data;
this page enables to:
  1. keep comments in what we find and on potential exploitation plans.
  2. give indications of format changes that have been noticed

## TOC
<!--TOC-->

- [Information on Data Sets](#information-on-data-sets)
  - [Goal](#goal)
  - [TOC](#toc)
    - [From https://www.data.gouv.fr](#from-httpswwwdatagouvfr)
    - [From https://data.europa.eu/euodp/](#from-httpsdataeuropaeueuodp)

<!--TOC-->


### From https://www.data.gouv.fr
 - Adding information on vaccination, this is being done in August 2021,
   1. Overall, this is done in `COVID-Data-FromGouv-Vaccins.ipynb`
     + this includes a fair amount of technicalities concerning Pandas for 
	   which 
	   https://stackoverflow.com/questions/53927460/select-rows-in-pandas-multiindex-dataframe 
	   has a quite comprehensive explanation on slicing multi-indices...
	   
   1. test `DGTestFRAPI.test_rqt7get` has been added to `source/lib/testDataMgr.py`,
      mostly to check method for discovering the relevant files/data
	  
   1. There are numerous remarks on the provided data and how it needs to be prepared in
      `COVID-Data-FromGouv-Vaccins.ipynb`.
	  
 - Summer 2021:
   1. There have been changes (labeling,..), making update by API searching 
      on `badge`not feasible; however searching  on `tag` and `slug`do work. 
   1. We have responded by
      + widening the set of supported API requests, therefore
        introducing object class `manageAndCacheDataFilesFRAPI`
	  + adding some interrogation capabilities
   1. See the tests (file `source/lib/testDataMgr.py` `DGTestFRAPI.*`) 
      or the example in Jupyter files
 - <B>Change in file names (April 2021)</B>
   The following files have been introduced in replacement
    + sursaud-corona-quot-dep-2021-04-08-21h20.csv 
	  - replaces sursaud-covid19-quotidien-2020-04-11-19h00-departement.csv
    + sursaud-corona-quot-reg-2021-04-03-19h33.csv
	  - replaces sursaud-covid19-quotidien-2020-04-11-19h00-region.csv
	   
 - <B>Change in file format</B>
       + concerning the above CSV files the separator was changed to `;`

### From https://data.europa.eu/euodp/
 - <B>At this time (Summer 2021), access to this site is not supported (due to an
     issue in the utilisation of the SPARQL access point).</B>
 - <B>Change in data  format</B>:
   + starting 17/12/2020, data started being collected in weekly format, the
     files including weekly data from beginning of 2020. The files are being adapted,
	 support of the new format is expected around April 15th.
   + covid-19-coronavirus-data.json is apparently not being extended after Jan 14th, 2021
   + New files:
     - dataEURdf/covid-19-coronavirus-data-daily-up-to-14-december-2020.csv
     - dataEURdf/covid-19-coronavirus-data-weekly-from-17-december-2020.csv
 
 - <B>Data description</B>:
   +  https://www.ecdc.europa.eu/en/publications-data/data-national-14-day-notification-rate-covid-19:
   
      <I>Data on 14-day notification rate of new COVID-19 cases and
      deaths</I>: The downloadable data file contains information on the
      14-day notification rate of newly reported COVID-19 cases per 100 000
      population and the 14-day notification rate of reported deaths per
      million population by week and country. Each row contains the
      corresponding data for a certain day and per country. The file is
      updated weekly. You may use the data in line with ECDC’s copyright
      policy.
	  
   + https://www.ecdc.europa.eu/sites/default/files/documents/2021-01-13_Variable_Dictionary_and_Disclaimer_national_weekly_data.pdf :
   
     rate_14_day 14-day notification rate of reported COVID-19 cases per 100 000 population
	 OR 14-day notification rate of reported deaths per 1 000 000 population
 

#### Misc.
 - news-and-press-releases-on-covid-19-pandemic-from-the-european-medicines-agency-ema.html 
   Interesting review from **European Medicines Agency**
