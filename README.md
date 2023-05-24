# GSDCDS
Google Scholar Dataset Citing Documents Search
## Description

This tool is used to obtain citations of published documents (journal and proceedings articles, book and book chapters, technical reports, etc) which are linked to the NASA ESDIS dataset DOIs. The tool searches Google Scholar by either dataset DOI or dataset metadata keywords taken from CMR.

Dataset metadata keywords always contain dataset unique name, called Earth Science Data Type (ESDT), see [EOSDIS Glossary](https://www.earthdata.nasa.gov/learn/glossary). ESDT and dataset Version identify unique dataset collection, which is assigned a DOI. When GScholar is searched by ESDT, the document citation is linked to that ESDT, which in turn can be linked to any combination of ESDT and Version (unless the document is examined to determine exact dataset version used in it).

GScholar is searched by the means of [SerpAPI](https://serpapi.com/). To use SerpAPI one would need a subscription that in turn provides key for API access.

GScholar return results in the form of URLs. To convert these URLs to citations, the [Zotero translation server](https://github.com/zotero/translation-server) is used. Zotero translation server needs to be run in background using Docker as follows to start or stop it:

```
docker pull zotero/translation-server
docker run -d -p 1969:1969 --rm --name translation-server translation-server
docker kill translation-server
```

Once document citation is obtained, its DOI is used as a unique key for the document hash. Document DOIs are mapped to dataset DOIs and ESDT names to create dataset-to-document linkage.

### The folders contain the following:

* CMR: JSON files of dataset collectuon metadata obtained using [CMR API](https://cmr.earthdata.nasa.gov/search/site/docs/search/api.html).
* data: 
  + doi2esdt.json - contains mapping of dataset DOI to its ESDT name
  + gscholar_search_terms.json - contains metadata search terms per ESDT, it is output of create_gscholar_search_terms.py
  + google_organic_results_by_doi.json and google_organic_results_by_esdt.json - output of gscholar_search.py. It contains a list of Google Scholar search results each mapped to dataset ESDT and DOI
  + google_citations_by_doi.json and google_citations_by_esdt.json - output of gscholar_citations.py
  + zotero_citations_by_doi.json and zotero_citations_by_esdt.json - output of zotero_citations.py
* csv:
  + key.txt - contains SerpAPI key

## Tool execution sequence:

### Create search terms for GScholar search by ESDT and metadata keywords

Expects collection metadata in CMR/ directory pulled from [CMR API](https://cmr.earthdata.nasa.gov/search/site/docs/search/api.html). Creates data/gscholar_search_terms.json which is further used by GScholar search by keywords.
```
python create_gscholar_search_terms.py
```

### Search Google Scholar by dataset DOI or by dataset ESDT and keywords
Input is data/doi2esdt.json containing mapping of dataset DOI to its ESDT name or data/gscholar_search_terms.json containing mapping of dataset ESDT and keywords. Executes the search by each dataset DOI or ESDT and outputs results into data/google_organic_results_by_doi.json or data/google_organic_results_by_esdt.json. Needs SerpAPI key stored in the file csv/key.txt.

```
python gscholar_search.py
```

### Process Google Scholar results to combine results with the same URL, exclude PDFs and pre-prints, and determine document DOI from URL, when possible
Takes as input data/google_organic_results_by_doi.json or data/google_organic_results_by_esdt.json and outputs data/google_citations_by_doi.json or data/google_citations_by_esdt.json
```
python gscholar_citations.py
```
### Process Google Scholar URLs using Zotero Translation server to map Google Scholar URLs to citations
Takes as input either data/google_citations_by_doi.json or data/google_citations_by_esdt.json and outputs data/zotero_citations_by_doi.json or data/zotero_citations_by_esdt.json. The script obtains Zotero content for each URL and extracts document DOI from it. Then it removes citations for which DOIs cannot be found and combines duplicate entries that have the same document DOI. For each citation Crossref is queried to obtain document type and then removes the citations with undesired document types (specified in the script). Finally, fo the citations that miss the publication year, the year is obtained by Crossref query.
```
python zotero_citations.py
```

