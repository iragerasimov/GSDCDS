'''
Start Zotero translation server in Docker:
    docker pull zotero/translation-server
    docker run -d -p 1969:1969 --rm --name translation-server translation-server
To stop zotero translation server:
    docker kill translation-server

For each Google Scholar result query Zotero translation server by either document URL or DOI, when available. 
Determine the document DOI from Zotero output
def add_zotero_output(g_citations)

Remove citations for which no DOIs were found
def remove_citations_without_dois(g_citations)

Combine citations with the same document DOI
def combine_duplicates(g_citations)

Obtain document type from Crossref
def add_crossref_type(g_citations)

Remove citations with undesired document types
def remove_citations_based_on_type(g_citations)

For document citations that miss year, retrieve year from Crossref
get_year_from_crossref(g_citations)

'''

import os
import json
import re 
from crossref.restful import Works, Etiquette

#set my_etiquette for crossref API. It helps filter unusual requests, and contact if necessary.
project_name = 'NASA EOSDIS Dataset DOI References Collection'
version = 'V1'
organization = 'NASA GES DISC'
email = 'irina.gerasimov@nasa.gov'
my_etiquette = Etiquette(project_name, version, organization, email)
works = Works(etiquette=my_etiquette)

DOI = True #False     # set to False if input results by ESDT search
# provide names of input and output files
if DOI:
    google_citations = 'data/google_citations_by_doi.json'
    zotero_citations = 'data/zotero_citations_by_doi.json'
else:
    google_citations = 'data/google_citations_by_esdt.json'
    zotero_citations = 'data/zotero_citations_by_esdt.json'

# define types of documents to remove from Google results
ignore_type_list = [ # list of publication types to ignore
        'peer-review',
        'posted-content',
        'component',
        'dataset'
    ]

def remove_citations_without_dois(g_citations):
    '''
    if after running Zotero translation server citation DOI is still not determined then remove it from g_citations and add it to g_citations_no_do list
    return g_citations, g_citations_no_doi
    '''
    g_citations_no_doi = list()
    remove_index = list()
    for i,g in enumerate(g_citations):
       if g['pub_doi'] == '':
          g_citations_no_doi.append(g)
          remove_index.append(i)
    remove_index.sort()
    for e in reversed(remove_index): 
        del g_citations[e] # remove the citations that have empty pub_doi
    return g_citations, g_citations_no_doi

def combine_duplicates(g_citations):
    ''' combines duplicates '''
    g_unique_dois = set()
    for g in g_citations:
        g_unique_dois.add(g['pub_doi'].upper())
    g_unique_results = list()
    for doi in list(g_unique_dois):
        g_unique_results.append({
            'result_id' : list(),
            'URL': list(),
            'pub_doi' : doi,
            'refs' : set()
        })
    for g in g_citations:
        for g_unique in g_unique_results:
            if g['pub_doi'].upper() == g_unique['pub_doi'].upper():
                g_unique['result_id'].append(g['result_id'])
                g_unique['URL'].append(g['URL'])
                g_unique['author'] = g['author']
                g_unique['year'] = g['year']
                g_unique['title'] = g['title']
                g_unique['zotero'] = g['zotero']
                if DOI:
                    for doi in g['DOIs']:
                        g_unique['refs'].add(doi)
                else:
                    for esdt in g['ESDTs']:
                        g_unique['refs'].add(esdt)
    for g in g_unique_results:
        if DOI:
            g['DOIs'] = list(g['refs'])
        else:
            g['ESDTs'] = list(g['refs'])
        del g['refs']
    return g_unique_results

def add_zotero_output_by_url(g):
    url=g['URL']
    print(url)
    g['zotero'] = {}
    if re.search('pure.mpg.de', url) or re.search('gfzpublic.gfz-potsdam.de', url):
        return g
    stream = os.popen('curl -d \"'+url+'\" -H \'Content-Type: text/plain\' http://127.0.0.1:1969/web')
    output = stream.read()
    print(output)
    if re.match('No items returned from any translator', output):
        return g
    try:
        json_object = json.loads(output)
        if re.search('ShieldSquare Captcha', json_object[0]['title']):
            return g
        g['zotero'] = json_object[0]
        if g['zotero'].get('DOI', ''):
            g['pub_doi'] = g['zotero']['DOI']
        elif g['zotero'].get('extra', '') and re.search('DOI', g['zotero']['extra']):
            resp = re.search(r'(10\.\d+.*)$', g['zotero']['extra'])
            if resp: 
                g['pub_doi'] = resp[0]
        if g['zotero'].get('date' ,''):
            g['year'] = re.search(r'\d{4}', g['zotero']['date'])[0]
    except:
        pass
    return g

def add_zotero_output_by_doi(g):
    if not g['pub_doi']:
        return g
    stream = os.popen('curl -d \"'+g['pub_doi']+'\" -H \'Content-Type: text/plain\' http://127.0.0.1:1969/search')
    output = stream.read()
    print(output)
    if re.match('No items returned from any translator', output):
        return g
    try:
        json_object = json.loads(output)
        g['zotero'] = json_object[0]
        if g['zotero'].get('DOI', ''):
            g['pub_doi'] = g['zotero']['DOI']
        elif g['zotero'].get('extra', '') and re.search('DOI', g['zotero']['extra']):
            resp = re.search(r'(10\.\d+.*)$', g['zotero']['extra'])
            if resp:
                g['pub_doi'] = resp[0]
        if g['zotero'].get('date' ,''):
            g['year'] = re.search(r'\d{4}', g['zotero']['date'])[0]
    except:
        pass
    return g


def add_zotero_output(g_citations):
    for i,g in enumerate(g_citations):
        if g.get('zotero', '') and len(g['zotero']):
            if re.match(r'webpage', g['zotero']['itemType']) and len(g['pub_doi']):
                g = add_zotero_output_by_doi(g)
            continue
        else:
            g = add_zotero_output_by_url(g)
            if len(g['zotero']) and not re.match(r'webpage', g['zotero']['itemType']):
                continue
        if g['pub_doi']:
            g = add_zotero_output_by_doi(g)
    return g_citations

def add_crossref_type(g_citations):
    for i,g in enumerate(g_citations):
        if g.get('Type', ''):
            continue
        g['Type'] = ""
        pub_doi = None
        if g.get('DOI', ''):
            pub_doi = g['DOI']
        else:
            pub_doi = g['pub_doi']
        if pub_doi:
            try:
                g['Type'] = works.doi(pub_doi)['type']
            except:
                print('Cannot get Crossref type for '+pub_doi)
                continue
    return g_citations

def remove_citations_based_on_type(g_citations):
    g_cleaned = list()
    for i,g in enumerate(g_citations):
        if not g.get('Type', ''):
            g_cleaned.append(g)
            continue
        if g['Type'] not in ignore_type_list:
            g_cleaned.append(g)

    return g_cleaned

def get_year_from_crossref(g_citations):
    works = Works(etiquette=my_etiquette)
    for i,g in enumerate(g_citations):
        if len(g['year']):
            continue
        try:
            g['year'] = str(works.doi(g['DOI'])['created']['date-parts'][0][0])
        except:
            continue
    return g_citations

with open(google_citations) as gs_file:
  g_citations = json.load(gs_file)


# For each Google Scholar result query Zotero translation server by either document URL or DOI, when available
g_citations = add_zotero_output(g_citations)

# remove citations for which no DOIs were found
(g_citations, g_citations_no_doi) = remove_citations_without_dois(g_citations) 

# combine citations with the same document DOI
g_citations = combine_duplicates(g_citations)

# obtain document type from Crossref
g_citations = add_crossref_type(g_citations)

# remove citations with undesired document types
g_citations = remove_citations_based_on_type(g_citations)

# for document citations that miss year, retrieve year from Crossref
g_citations = get_year_from_crossref(g_citations)

with open(zotero_citations, 'w') as output:
  json.dump(g_citations, output, indent=4)


