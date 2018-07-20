"""
Setup:
- install virtualenv using `pip install virtualenv`
- cd into this directory and create a virtual env `virtualenv avgCraig`
- activate the virtual env using `source virtualenv/bin/activate`
- install the third party libraries needed: 
    - `pip install requests BeautifulSoup`
- tweak the CL_* constant vars below to your liking
- run this script using `python avgCraig.py`
"""

import requests
from bs4 import BeautifulSoup as bs4

# Disable annoying SSL warnings
import requests.packages.urllib3

requests.packages.urllib3.disable_warnings()

# Modify these to your liking...
CL_DOMAIN = "chicago"
CL_SUBDOMAIN = "wcl"  # West Chicago land
CL_SEARCH_QUERY = "aurora"
CL_NUM_BEDROOMS = "2"
CL_MIN_BATHROOMS = "1"

# The maximum amount of results to query for
CL_MAX_RESULTS = 1000


def query_craigslist(start_index: int) -> str:
    url = f'https://{CL_DOMAIN}.craigslist.org/search/{CL_SUBDOMAIN}/apa?' \
            f'query={CL_SEARCH_QUERY}' \
            f'&min_bedrooms={CL_NUM_BEDROOMS}&max_bedrooms={CL_NUM_BEDROOMS}' \
            f'&min_bathrooms={CL_MIN_BATHROOMS}&max_bathrooms={CL_MIN_BATHROOMS}' \
            f'&s={start_index}'

    print(f'Querying Craigslist at {url}')
    raw_html = requests.get(url)
    return raw_html.text


def should_keep_querying(raw_html: str) -> bool:
    txt = bs4(raw_html, 'html.parser')
    range_to = int((txt.find(attrs={'class': "rangeTo"})).string)
    total_count = int((txt.find(attrs={'class': "totalcount"})).string)

    if total_count > range_to:
        # Theres still more results to show...check to make sure its not bigger than our max
        if range_to < CL_MAX_RESULTS:
            return True
    return False


def parse_out_eligible_apts(raw_html, all_apts_rows, include_nearby=True):
    txt = bs4(raw_html, 'html.parser')

    if include_nearby:
        apts = txt.findAll(attrs={'class': "result-row"})
    else:
        # Don't include "nearby" results which CL sometimes includes at the bottom of results
        nearby = txt.find(attrs={'class': 'ban nearby'})
        apts = nearby.findAllPrevious(attrs={'class': "result-row"})

    for a in apts:
        all_apts_rows.append(a)


def get_average(l):
    avg_price = sum(l) / float(len(l))
    return '{:,.2f}'.format(avg_price)


def get_median(lst):
    lst = sorted(lst)
    if len(lst) < 1:
        return 0
    if len(lst) % 2 == 1:
        median = lst[((len(lst) + 1) // 2) - 1]
        return '{:,.2f}'.format(median)
    else:
        median = float(sum(lst[(len(lst) // 2) - 1:(len(lst) // 2) + 1])) / 2.0
        return '{:,.2f}'.format(median)


def find_prices(results):
    prices = []
    for rw in results:
        price = rw.find('span', {'class': 'result-price'})
        if price is not None:
            price = float(price.text.strip('$'))
            prices.append(price)
    return prices


def do_analytics(apts):
    # Print out the search parameters first
    print(f'Analyzing {len(apts)} apartments with the following parameters:')
    print(f'\tSearch Query: \"{CL_SEARCH_QUERY}\"')
    print(f'\tBedrooms: {CL_NUM_BEDROOMS}')
    print(f'\tBathrooms: {CL_MIN_BATHROOMS}\n')

    # Look at the prices
    prices = find_prices(apts)
    print(f'Average Price: ${get_average(prices)}')
    print(f'Median Price: ${get_median(prices)}')
    print("\nDone")


def get_apts():
    """
    Queries Craiglist and parses out the eligible apartment HTML rows
    Returns: A list of HTML rows parsed by BS4

    """
    cl_start_index = 0
    all_apartments = []

    cl_raw_html = query_craigslist(cl_start_index)
    parse_out_eligible_apts(cl_raw_html, all_apartments)

    while should_keep_querying(cl_raw_html):
        cl_start_index += 100
        cl_raw_html = query_craigslist(cl_start_index)
        parse_out_eligible_apts(cl_raw_html, all_apartments)

    return all_apartments


# MAIN
all_apts = get_apts()
do_analytics(all_apts)
