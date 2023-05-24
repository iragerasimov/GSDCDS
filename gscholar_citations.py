# Process Google Scholar organic results to:
#  - Exclude preprints
#  - Exclude URLs to PDF files
#  - Determine DOIs from the URLs of copernicus, nature, ametsoc
#  - Combine results that have the same GoogleScholar result URL 

import os
import sys
import json
import re
import time
import datetime
import pandas as pd
import unicodedata              # used to transform unicode to ascii such as '\u2026' to '...'
from bs4 import BeautifulSoup   # used together with unescape to remove html tags such as &lt;
from html import unescape       # used together with unescape to remove html tags such as &lt;

EXCLUDE_PREPRINTS = True	# do not process GScholar results if their "link" contains "preprint" string
EXCLUDE_PDF = True	        # do not process GScholar results if they are "type": "Pdf" or their link contains ".pdf" string

DOI = True      # set to False if processing Google Organic results by ESDT

# provide names of input and output files
if DOI:
    google_organic_results = 'data/google_organic_results_by_doi.json'
    google_citations = 'data/google_citations_by_doi.json'
else:
    google_organic_results = 'data/google_organic_results_by_esdt.json'
    google_citations = 'data/google_citations_by_esdt.json'

with open(google_organic_results) as gs_file:
  gscholar_results = json.load(gs_file)

def find_citation_by_id (result_id, organic_citations):
  for citation in organic_citations:
    if citation['result_id'] == result_id:
      return citation
  return None

organic_citations = []
index = 0
for result in gscholar_results:
  # check if this result_id is already in organic_citations
  citation = find_citation_by_id(result['result_id'], organic_citations)
  if citation:
    if DOI:
      citation['DOIs'].append(result['DOI'])
    citation['ESDTs'].append(result['ESDT'])
    continue

  title = result['title']
  (author, year, pub_doi, link) = ('', '', '', '')
  pub_info = result['publication_info']['summary']
  pub_info = BeautifulSoup(unescape(pub_info), 'lxml').text
  pub_info =  unicodedata.normalize('NFKD', pub_info).encode('ascii', 'ignore').decode('ascii')

  try:
    author = result['authors'][0]['name']
  except:
    try: 
      author = re.match(r'^((?:\S+\s+){1}[^\r\n\t\f\v ,]+).*',pub_info).group(1)
    except:
      author = ''

  try:
    year = ''.join(re.findall(r'\s+(\d{4})\s+',pub_info)[0])  # articles from 1980 and later
  except:
    year = ''

  if result.get('type'):
    resp = re.search(r'Pdf', result['type'])
    if resp and EXCLUDE_PDF:
      continue
  
  if result.get('link'):
    if re.search(r'\.pdf', result['link']) and EXCLUDE_PDF:
      continue
    resp = re.search(r'preprint', result['link'])
    if resp and EXCLUDE_PREPRINTS:
      continue
    link = result['link']
    resp = re.search(r'\/(10\.\d+.*)$', result['link'])
    if resp:
      pub_doi = resp[0]
      pub_doi = re.sub(r'(\/full|\/meta|\.pdf|\.abstract|\.short|\&.*|\/download|\/html|\?.*|\#.*|\;|\)|\/$|\.$)','',pub_doi)
    elif re.search(r'copernicus\.org', result['link']):
      resp = re.search(r'\//(\S+)\.copernicus\.org\/articles\/(\d+)\/(\d+)\/(\d+)', result['link'])
      if resp:
        pub_doi = '10.5194/'+resp[1]+'-'+resp[2]+'-'+resp[3]+'-'+resp[4]
    elif re.search(r'nature\.com\/articles\/', result['link']):
      resp = re.search(r'nature\.com\/articles\/(\S+)', result['link'])
      if resp:
        pub_doi = '10.1038/'+resp[1]
        pub_doi = re.sub(r'(\?.*|\/briefing.*)', '', pub_doi)
        pub_doi = re.sub(r'%E2%80%', '-', pub_doi)
        resp = re.match(r'10.1038\/sdata(\d{4})(\d+)', pub_doi)
        if resp:
          pub_doi = '10.1038/sdata.'+resp[1]+'.'+resp[2]
        # https://www.nature.com/articles/s41558%E2%80%92019%E2%80%920592%E2%80%928 should translate to 10.1038/s41558-019-0592-8
        # https://www.nature.com/articles/s41586%E2%80%93020%E2%80%932780%E2%80%930 should translate to 10.1038/s41586-020-2780-0
    elif re.search(r'journals\.ametsoc\.org', result['link']):
      resp=re.search(r'\/((\w+|\.+|\-+|_+)*)\.xml', result['link'])
      if resp:
        pub_doi = '10.1175/'+resp[1]
        pub_doi = re.sub(r'_1', '.1', pub_doi)
        if not re.search(r'-', pub_doi):
          resp=re.match(r'10.1175\/(\w+)(d|D)(\d{2})(\d{4})', pub_doi)
          if resp:
            pub_doi = '10.1175/'+resp[1]+'-'+resp[2]+'-'+resp[3]+'-'+resp[4]+'.1'
    if pub_doi:
      pub_doi=re.sub(r'^\/', '', pub_doi)
      pub_doi=re.sub(r'(\/|\;|\)|\.|\.full)$', '', pub_doi)
      if re.search(r'elementa', pub_doi):
        pub_doi = re.sub(r'\/\d+$', '', pub_doi)
  citation = {
      'result_id'	: result['result_id'],
      'URL'		: link,
      'pub_doi'		: pub_doi,
      'author'	 	: author,
      'year'		: year,
      'title'		: title
     }
  if DOI:
    citation['DOIs'] = [result['DOI']]
  citation['ESDTs'] = [result['ESDT']]
  organic_citations.append(citation)
  index += 1

with open(google_citations, 'w') as output:
  json.dump(organic_citations, output, indent=4)

