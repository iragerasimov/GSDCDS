# input: JSON files in CMR/ directory acquired using https://cmr.earthdata.nasa.gov/search/site/docs/search/api.html
# output: data/gscholar_search_terms.json

import glob
import json
import re
import pandas as pd

cmr_dir = './CMR/'
metadata_files = glob.glob(cmr_dir+'*.json')
queries = {}

for metadata_file in metadata_files:
  with open(metadata_file) as f:
    metadata = json.load(f)
  (ShortName, query) = ('', '')
  for citation in metadata["CollectionCitations"]:
    ShortName = citation["SeriesName"]
    if not queries.get(ShortName, ''):
      if re.search(r'(\_|\-)', ShortName):
        alias = re.sub(r'(\_|\-)', ' ', ShortName)
        query = '("'+ShortName+'" | "'+alias+'") ('
      else:
        query = '"'+ShortName+'" ('
  if queries.get(ShortName, ''):
    continue
  for platform in metadata["Platforms"]:
    query = query+' "'+platform["ShortName"]+'" |'
    if re.search(r'(\_|\-)', platform["ShortName"]):
      alias = re.sub(r'(\_|\-)', ' ', platform["ShortName"])
      query = query+' "'+alias+'" |'
    for instrument in platform["Instruments"]:
      if not re.search(r'NOT APPLICABLE', instrument["ShortName"]):
        query = query+' "'+instrument["ShortName"]+'" |'
  for project in metadata["Projects"]:
    if not re.search(r'\"{project["ShortName"]}\"', query):
      query = query+' "'+project["ShortName"]+'" |'

  query = re.sub(r'\|$', ')', query)
  queries[ShortName] = query

with open("data/gscholar_search_terms.json", "w") as f:
  json.dump(queries, f, indent=4)

