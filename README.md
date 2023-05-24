# GSDCDS
Google Scholar Dataset Citing Documents Search
## Description

This tool is used to obtain citations of published documents (journal and proceedings articles, book and book chapters, technical reports, etc) which are linked to the NASA ESDIS dataset DOIs. The tool searches Google Scholar by either dataset DOI or dataset metadata keywords taken from CMR.

Dataset metadata keywords always contain dataset unique name, called Earth Science Data Type (ESDT), seee [EOSDIS Glossary] (https://www.earthdata.nasa.gov/learn/glossary). ESDT and dataset Version identify unique dataset collection, which is assigned a DOI. When GScholar is searched by ESDT, the document citation is linked to that ESDT, which in turn can be linked to any combination of ESDT and Version (unless the document is examined to determine exact dataset version used in it).

GScholar is searched by the means of [SerpAPI] (https://serpapi.com/). To use SerpAPI one would need a subscription that in turn provides key for API access.

GScholar return results in the form of URLs. To convert these URLs to citations, the [Zotero translation server] (https://github.com/zotero/translation-server) is used. Zotero translation server needs to be run in background using Docker as follows to start or stop it:

```
docker run -d -p 1969:1969 --rm --name translation-server translation-server
docker kill translation-server
```

Once document citation is obtained, its DOI is used as a unique key for the document hash. Document DOIs are mapped to dataset DOIs and ESDT names to create dataset-to-document linkage.

### The folders contain the following:

* CMR: JSON files of dataset collectuon metadata obtained using [CMR API] (https://cmr.earthdata.nasa.gov/search/site/docs/search/api.html).
* data: output files
 1. gscholar_search_terms.json - contains metadata search terms per ESDT, it is output of create_gscholar_search_terms.py
 1. google_organic_results.json - output of either or gscholar_pull_by_doi.py or gscholar_pull_by_esdt.py. It contains a list of Google Scholar search results each mapped to either dataset DOI or ESDT
 1. google_organic_citations.json - output of gscholar_organic_citations.py
* csv:
 1. doi2esdt.csv - contains mapping of dataset DOI to its ESDT name, e.g. 10.5067/UO3Q64CTTS1U | AIRS3STD
 1. key.txt - contains SerpAPI key

## Tool execution sequence:

### Create search terms for GScholar search by ESDT and metadata keywords

Expects collection metadata in CMR/ directory pulled from [CMR API] (https://cmr.earthdata.nasa.gov/search/site/docs/search/api.html). Creates data/gscholar_search_terms.json which is further used by GScholar search by keywords.
```
python create_gscholar_search_terms.py
```

### Search Google Scholar by dataset DOI
Expects csv files in csv/ directory with mapping of dataset DOI to its ESDT name, e.g. 10.5067/UO3Q64CTTS1U | AIRS3STD. Executes the search by each dataset DOI and outputs results into data/google_organic_results.json. Needs SerpAPI key stored in the file csv/key.txt.

```
python gscholar_search_by_doi.py
```

### Search Google Scholar by dataset keywords
Takes as input data/gscholar_search_terms.json and outputs results into data/google_organic_results.json
```
python gscholar_search_by_esdt.py
```
