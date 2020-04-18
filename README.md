# Simple python scripts to work with COVID-19 / SARS-cov-19 data provided by Santé publique France

The data sources used are located:
- https://www.data.gouv.fr/fr/datasets/donnees-hospitalieres-relatives-a-lepidemie-de-covid-19/
- https://www.data.gouv.fr/en/datasets/donnees-des-urgences-hospitalieres-et-de-sos-medecins-relatives-a-lepidemie-de-covid-19/


Mostly this consists of jupyter notebook(s), while python scripts are also provided
almost direct transpositions of the notebooks. This is supported by library modules.


## Aim:
There are many good and interesting contributions on the pages 
https://www.data.gouv.fr/fr/datasets/donnees-hospitalieres-relatives-a-lepidemie-de-covid-19
and
https://www.data.gouv.fr/en/datasets/donnees-des-urgences-hospitalieres-et-de-sos-medecins-relatives-a-lepidemie-de-covid-19/,
however this is a very straightforward piece of code, intended mostly to facilitate
access to the data for testing personal "what-if" hypotheses.

## Gallery

![Hospital data](./JupySessions/images/Chap01/FIG003.jpg)
![Hospital data according to sex](./JupySessions/images/Chap01/FIG004.jpg)
![Hospital outcomes per age](./JupySessions/images/Chap01/FIG005.jpg)
![Tests](./JupySessions/images/Chap01/FIG006.jpg)

## Functionality
- Jupyter notebook(s): display data 
- `DataGrouvFr` Python module :
-- manage a local repository with files from www.data.gouv.fr
  by handling file version/timestamp in file name
-- automate the transfer of files with badge "covid-19", maintain a local cache of
   information concerning these files 
- `figureHelpers.py` module:
-- some convenience tools to facilitate/automate making `matplotlib` figures.
(Also looking forwards towards ̀seaborn`... after some wait... )

   For more information on changes (and bugs), see the git log.

## install requirement
### Python
- This requires Python 3, and has been tested with Python 3.6.5, on a Linux
Ubuntu 18.04 LTS system.

- In the current version, the library is dependent on
some features from the IPython package, which comes with Jupyter. This constraint
may be removed in the future.

### Libraries
```
pip install -U -R requirements.txt

```



## Warning(s)
This is provided as is, see the LICENSE file.

## References
- https://github.com/alichnewsky/covid : basic script to work with the Novel Coronavirus (COVID-19) cases 
      dataset provided by JHU CSSE

https://www.academie-sciences.fr/fr/

   For more information on changes (and bugs), see the git log.

## install requirement
### Python
- This requires Python 3, and has been tested with Python 3.6.5, on a Linux
Ubuntu 18.04 LTS system.

- In the current version, the library is dependent on
some features from the IPython package, which comes with Jupyter. This constraint
may be removed in the future.

### Libraries
```
pip install -U -R requirements.txt

```



## Warning(s)
This is provided as is, see the LICENSE file.

## References
- https://github.com/alichnewsky/covid : basic script to work with the Novel Coronavirus (COVID-19) cases 
      dataset provided by JHU CSSE

- https://www.academie-sciences.fr/fr/: many references

- https://www.eficiens.com/coronavirus-statistiques/#evolution-contamination-france: well represented statistics