# input: csv/key.txt -- contains SerpAPI key obtainable from https://serpapi.com/
#        data/doi2esdt.json -- contains match of dataset DOI to ESDT
#        data/gscholar_search_terms.json - contains match of dataset ESDT name to search keywords
# output: 
#        data/google_organic_results_by_doi.json  - if DOI = True
#        data/google_organic_results_by_esdt.json - if DOI = False

from serpapi import GoogleSearch
import os
import sys
import json
from urllib.parse import urlsplit, parse_qsl
import re
import time
import datetime
import pandas as pd

key_file = open('csv/key.txt')
key = key_file.read()
key_file.close()
print(key)

doi2esdt_file = 'data/doi2esdt.json'
search_terms_file = 'data/gscholar_search_terms.json'

DOI = False     # True to search by dataset DOI, False to search by dataset ESDT name and keywords
if DOI:
    gscholar_results_file = 'data/google_organic_results_by_doi.json'
else:
    gscholar_results_file = 'data/google_organic_results_by_esdt.json'

def get_document_urls(esdt, query, gscholar_results):
  params = {
    "api_key": key,
    "engine": "google_scholar",
    "q": query,
    "hl": "en",         # search language
    "lr": "lang_en",    # return results only in English language
    "as_vis": "1"       # do not include citations
    #"as_ylo": "2020"   # specify start year of document published date
    #"as_yhi": "2023",  # specify end year of document published date
    #"start": "0"       # first page
  }

  search = GoogleSearch(params)
  page = 1
  loop_is_true = True
  while loop_is_true:
    
    search_results = search.get_dict()
    try:
        print(search_results['search_metadata']['status'])
    except:
        print(search_results['error'])
        exit()
    if 'organic_results' in search_results:
        if len(search_results['organic_results']) >= 1:
            results = search_results['organic_results']
        
            for result in results:
                result['ESDT'] = esdt
                if DOI:
                    result['DOI'] = doi
                gscholar_results.append(result)
        else: 
          return (gscholar_results)
    else: 
      return (gscholar_results)
        
    if 'serpapi_pagination' in search_results:
        if (not 'next' in search_results['serpapi_pagination']):
            loop_is_true = False
        else:
            search.params_dict.update(dict(parse_qsl(urlsplit(search_results["serpapi_pagination"]["next"]).query)))        
            print('Now on page ', page, 'of results for: ', query, ' | time: ', datetime.datetime.now())
            page += 1
    else:
        loop_is_true = False
  return (gscholar_results)


gscholar_results = list()

if DOI:
    with open(doi2esdt_file) as f:
        doi2esdt = json.load(f)
    dois = doi2esdt.keys()
    for doi in dois:
        print (doi)
        (gscholar_results) = get_document_urls(doi2esdt[doi], doi, gscholar_results)
else:
    with open(search_terms_file) as f:
        search_terms = json.load(f)
    for esdt in search_terms:
        query = search_terms[esdt]+' "NASA"'
        print(query)
        (gscholar_results) = get_document_urls(esdt, query, gscholar_results)

with open(gscholar_results_file, 'w') as output:
        json.dump(gscholar_results, output, indent=4) 

