# -*- coding: utf-8 -*-
"""
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Recondite v0.2 by @argotechnica / corysalveson@gmail.com
http://github.com/argotechnica/recondite
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
DONE: Gather Item IDs using API search functionality with e.g. following URL:
    https://www.wikidata.org/w/api.php?format=json&formatversion=2&action=query
        &list=search&srprop=sectiontitle|snippet&srsearch=Descartes, René

Store each list of results on a per-row basis, reshaping/unstacking/whatever
the dataframe to get it tidy, i.e. one row of input for each result option
returned.

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
DONE: Get claims for all entities, in 50-count batches (or 500 if having bot
status). Use this URL: https://www.wikidata.org/w/api.php?action=
    wbgetentities&format=json&formatversion=2&props=claims&ids=Q140412|Q142644

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
DONE: Gather labels for everything returned: item search results, as well as
the items which constitute properties that were returned, in 50-item batches
(or 500-item batches if bot status) with something like this URL:
    https://www.wikidata.org/w/api.php?format=json&formatversion=2
        &action=wbgetentities&props=labels&languages=en
        &ids=Q100|Q10001|Q1000717

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
TODO: Check current revision of "All Properties" page; if doesn't match cached
version, download a new copy of the full list:
    https://www.wikidata.org/w/api.php?format=json&formatversion=2
        &action=query&titles=Wikidata:Database_reports/List_of_properties/all
        &prop=info
    https://www.wikidata.org/w/api.php?format=json&formatversion=2
        &action=query&titles=Wikidata:Database_reports/List_of_properties/all
        &prop=revisions&rvprop=content

This will be used in combination with the user-defined list of what property
IDs should be compared, to look up label names used later on. For now, here's
the master translation list (focused on Person data):
    P31   instance of
    P21   sex or gender
    P19   place of birth
    P569  date of birth
    P20   place of death
    P570  date of death
    P734  family name
    P735  given name
    P742  pseudonym
    P106  occupation

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
TODO: There would be a fancy way of reshaping this into having as many
arbitrary value-columns as needed, then at some point in this mix looking up
all the property names to get prettier columns. But for this project,
I need to just get it done quicker. Just identify which props you want
and put those into dedicated columns plz. E.g.: http://stackoverflow.com/
questions/25100224/how-to-get-a-list-of-all-wikidata-properties

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""

from requests import get
from time import sleep
import pandas
from bs4 import BeautifulSoup


# Set a polite user agent per [1]
headers = {
    'User-Agent': 'Recondite/0.2 (corysalveson@gmail.com)',
    'From': 'corysalveson@gmail.com'
    }

# Hard-code base URL for JSON format v2 and Max Lag of 3 seconds. See: [1]
api_base_url = ('https://www.wikidata.org/w/api.php?'
                'format=json&formatversion=2&maxlag=5&')


def api_call(url, headers=headers, tries=0):
    """
    A recursive wrapper function for calling the API in a way that notices if
    maxlag has been triggered, waits, and tries again, to a maximum of 5 total
    attempts.
    """
    if tries == 5:  # if already tried 5 times (total 6 attempts), quit
        # TODO: gracefully log/notifythat max retry of 5 has been tripped
        print('TOO MANY ATTEMPTS - ABORTING')
        return None

    print('querying base URL using api_call, tries = ' + str(tries))
    r = get(url, headers=headers)
    data = r.json()

    if data.get('error'):
        if data['error'].get('code') == 'maxlag':
            print('got a maxlag error, waiting and trying again')
            tries += 1
            sleep(10 * tries)  # sleep for 10 seconds, then 20, etc.
            return(api_call(url, headers, tries))

    print('returning data from api_call')
    return(data)


def api_search_items(terms):
    """
    The normal way of getting Wikidata Item IDs is to use the "wbgetentities"
    action [2], however this expects exact data. Instead, api_search_items()
    uses the "query" action to do a fuzzier search, like what you'd get if you
    searched manually via the search box, returning just Item IDs and snippets.
    """
    print('searching... ' + str(terms))
    sleep(2)
    try:
        terms = ' '.join(terms.split())
        url = api_base_url + ('action=query'
                              '&list=search'
                              '&srprop=sectiontitle|snippet'
                              '&srlimit=50'
                              '&srsearch=' + terms)
        print('calling api_call() with url: ' + str(url))
        return(api_call(url))
    except:
        return(dict())


def parse_item_results(search_results, fp=None):
    """
    Expects a dataframe such that the final column is called "results" and all
    other columns should be repeated on a row-by-row basis for each individual
    result parsed from the multi-result results lists.

    TODO: Currently trying to filter out "false positives" by matching IDs at
    the end. Should make the "false positives" accept a list, and change
    to a kind of "in" search function.
    """
    corecols = len(list(search_results))-1
    items = pandas.concat([search_results.drop(['results'], axis=1),
                           search_results['results'].
                           apply(pandas.Series)['query'].
                           apply(pandas.Series)['search']], axis=1)
    items = pandas.concat([items.drop(['search'], axis=1),
                           items['search'].apply(pandas.Series)], axis=1)
    items = pandas.melt(items, id_vars=list(items)[:corecols],
                        value_vars=list(items)[corecols:], value_name='result')
    items.dropna(subset=['result'], inplace=True)
    items = pandas.concat([items.drop(['result'], axis=1),
                           items['result'].apply(pandas.Series)], axis=1)
    items.drop(['variable', 'ns'], axis=1, inplace=True)
    items['snippet'] = items['snippet'].apply(lambda x: BeautifulSoup(x,
                                              'lxml').get_text().
                                              replace('\n', '; '))
    if(fp):
        items = items[items[fp] != items['title']]
    return(items)


def api_get_item_claims(items):
    """
    Use wbgetentities action to get claims information for a list of item IDs.
    Focus is on getting raw data safely and storing it for later use, in
    batches of 50 with conservative pauses in between pulls. Actual parsing
    and whatnot of claims happens elsewhere because if something in such
    further steps fails, we don't want to have to start the data pull all over
    again.
    """
    claims = dict()

    ids = list(items['title'].unique())
    terms = []
    for i in range(0, len(ids), 50):
        terms.append(ids[i: i+50])

    try:
        for i in terms:
            url = api_base_url + ('action=wbgetentities'
                                  '&props=claims'
                                  '&languages=en'
                                  '&ids=' + '|'.join(i))

            cache = api_call(url)

            for key, value in cache['entities'].items():
                print('  parsing: ' + str(key))
                claims[key] = value['claims']

            sleep(2)
        return(claims)
    except:
        print('ERROR, aborting api_get_item_claims')
        return(cache)


def parse_claim_properties(claims, props='P31'):
    """
    Pass in some claims data as produced by api_get_item_claims(), as well as
    a comma-separated list of properties (default is to just pull P31, which
    is like "item type" or something like that), return a dictionary of
    item IDs as keys and simple property ID: property value dictionaries as
    values. Currently dumping some troubleshooting info to terminal; known
    quirk right now is that some items on Wikidata have claims defined
    with "unkonwn value" set as the value. These currently error out, which is
    fine for now but should be fixed later.

    TODO: Handle "Unknown Value" values more gracefully (currently errors out.)
    """
    properties = dict()
    for itemid, propdict in claims.items():
        for propid, values in propdict.items():
            if str(propid) in props.split(','):
                try:
                    properties[itemid] = dict()
                    proptype = values[0]['mainsnak']['datavalue']['type']
                    if proptype == 'wikibase-entityid':
                        properties[itemid][propid] = values[0]['mainsnak']['datavalue']['value']['id']
                    elif proptype == 'time':
                        properties[itemid][propid] = \
                            str(values[0]['mainsnak']['datavalue']['value']['time'])[1:5]
                except:
                    print(str(itemid) + ':' + str(propid) +
                          '(' + str(proptype) + '):💀')
    return(properties)

def api_get_labels(items, claims):
    """
    Both "items" and the values of properties of items are items represented
    in API results as Item IDs. This function takes raw items and claims data,
    finds all unique Item IDs represented by the set, then looks up all
    English names for those IDs and returns it as a nice dictionary.
    """
    labels = dict()
    # Initialize the ID list as a set, because Python automatically maintains
    # sets as unique values only.
    ids = set()

    # Add item IDs from all the items
    ids.update(items['title'].unique())

    # Add item IDs from all property values of all claims of all items
    for itemid, properties in claims.items():
        for propid, propvalue in properties.items():
            if str(propvalue)[:1] == 'Q':
                ids.add(str(propvalue))

    # Batch in counts of 50 for querying the API
    ids = list(ids)
    terms = []
    for i in range(0, len(ids), 50):
        terms.append(ids[i: i+50])

    try:
        for i in terms:
            url = api_base_url + ('action=wbgetentities'
                                  '&props=labels'
                                  '&languages=en'
                                  '&ids=' + '|'.join(i))
            cache = api_call(url)

            for key, value in cache['entities'].items():
                try:
                    labels[key] = value['labels']['en']['value']
                except:
                    1
            # break  # for testing purposes
            sleep(2)
        return(labels)
    except:
        print('ERROR, aborting api_get_item_claims')
        return(cache)
