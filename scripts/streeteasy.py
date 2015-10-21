# trying to get html of things from
import urllib2
from bs4 import BeautifulSoup
import matplotlib.pyplot as plt
from wordcloud import WordCloud, STOPWORDS
import itertools
import time
from time import mktime
from datetime import datetime
import pandas as pd
import numpy as np
import glob
from db_mongo import *
import mechanize

def readparse(inputurl):
    # return bs4 parsed html page
    #rsp = urllib2.urlopen(inputurl)
    rsp = mechanize.urlopen(inputurl)
    html = rsp.read()
    prsd = BeautifulSoup(html)
    return prsd

def get_datalayer_script(html):
    # get script tag corresponding to datalayer from google tagmanager
    allscript = html.find_all('script')
    for thisscript in allscript:
        txt = thisscript.get_text()
        if txt.find('dataLayer') != -1:
            return txt
    print('Error: no script tag matches data layer')
    return -1


def datalayer_script2dict(txt):
    # convert script tag to python list by modifying string and evaluating
    sloc = txt.find("dataLayer")
    eloc = txt.find(";\n")
    txt = txt[sloc:eloc]
    txt = txt.replace('null', '"None"')
    txt = txt.replace('false', 'False')
    txt = txt.replace('true', 'True')
    exec(txt)
    return dataLayer


def list2pdf(dataLayer):
    # convert recovered list to a pandas dataframe
    slst = dataLayer[0]['searchResultsListings']
    d1 = slst.pop('1')
    d1['data'] = {'jnk': 'jnk'}
    pdf = pd.DataFrame.from_dict(d1)
    # flatten the lists within the lists to avoid
    # replication of rows in pandas dataframe
    for jj in slst:
        dj = slst[jj]
        dj['data'] = {'jnk': 'jnk'}
        ss = pd.DataFrame.from_dict(slst[jj])
        pdf = pdf.append(ss)
    return(pdf)


def read_strpage(nurl):
    print(nurl)
    html = readparse(nurl)
    # loop through
    dltxt = get_datalayer_script(html)
    dllst = datalayer_script2dict(dltxt)
    pdf = list2pdf(dllst)
    return pdf


def streeteasy_scrape(borough, pricecap):
    nurlb = 'http://streeteasy.com/pet-friendly-rentals/' + \
        borough + '/status:open%7Cprice:-' + pricecap
    nurl = nurlb + '?page=1'
    print(nurl)
    rn = 0
    print('here')
    html = readparse(nurl)

    dltxt = get_datalayer_script(html)
    dllst = datalayer_script2dict(dltxt)

    nn = dllst[0]['searchResults']
    pdf = list2pdf(dllst)

    # if more than one page loop throuh pages and append
    print(nn, len(pdf))
    if nn > len(pdf):
        npgs = nn / len(pdf)
        print(range(npgs)[2:])
        for jj in range(npgs - 1):
            print(jj, npgs)
            time.sleep(np.abs(2.5 + 10 * np.random.randn(1)[0]))
            nurl = nurlb + '?page=' + str(jj + 2)
            print(nurl)
            opdf = read_strpage(nurl)
            pdf = pdf.append(opdf)
    return(pdf)


def streeteasy_get_urls(nurl):
    html = readparse(nurl)
    ss = html.find_all('a', {"data-gtm-listing-type": "rental"})
    urls = []
    adds = []
    for lstng in ss:
        slst = str(lstng).split()
        stxt = lstng.get_text()
        for wrd in slst:
            if (wrd.startswith('href') and not
                    wrd.endswith('img')):
                urls.append('http://streeteasy.com/' + wrd[6:-1])
                adds.append(stxt)
    return urls, adds


def streeteasy_scrape_urls(urls, addys):
    allst = []
    print('all', urls, addys)
    for lstng, addr in zip(urls, addys):
        print('-----', lstng, addr)
        dly = 0
        time.sleep(dly + abs(0.2 * scipy.randn(1)))
        try:
            html = readparse(lstng)
        except:
            continue
        dltxt = get_datalayer_script(html)
        dllst = datalayer_script2dict(dltxt)[0]
        dllst['address'] = addr
        allst.append(dllst)
    return pd.DataFrame.from_dict(allst)


def streeteasy_scrape_listings(borough, pref='http://streeteasy.com/pet-friendly-rentals/'):
    # get list of urls
    nurlb = pref + borough + '/status:open%7Cprice:'
    nurlb = nurlb + '-' + str(15000)
    nurl = nurlb + '?page=1'

    html = readparse(nurl)

    dltxt = get_datalayer_script(html)
    dllst = datalayer_script2dict(dltxt)

    lurls, adds = streeteasy_get_urls(nurl)
    pdf = streeteasy_scrape_urls(list(lurls), list(adds))

    nn = dllst[0]['searchResults']

    # if more than one page loop throuh pages and append
    print(nn, len(pdf))
    if nn > len(pdf):
        npgs = nn / len(pdf)
        print(range(npgs)[2:])
        for jj in range(npgs - 1):
            print(jj, npgs)
            time.sleep(np.abs(5. + 15 * np.random.randn(1)[0]))
            nurl = nurlb + '?page=' + str(jj + 2)
            print(nurl)
            lurls, adds = streeteasy_get_urls(nurl)
            opdf = streeteasy_scrape_urls(list(lurls), list(adds))
            pdf = pdf.append(opdf)
    return(pdf)

def spdstack(inlst):
    fl = inlst.pop()
    pdl = pd.read_pickle(fl)
    pdl['borough'] = lb
    for fl in inlst:
        tmp = pd.read_pickle(fl)
        pdl = pdl.append(tmp)
    return pdl

def main():

	# scrape apartment listings for each listed borough
	boroughs = ['bronx']
	suff ='_10-16_0-15000.pk'
	ddir = '../data/streeteasy/raw/'
	for bor in boroughs:
	    apdf = streeteasy_scrape_listings(
	        bor.lower(), pref='http://streeteasy.com/for-rent/')
	    apdf.to_pickle(ddir + bor.lower() + suff)

	# insert apartments into mongo db 
	sfils = glob.glob(ddir+'*'+suff)
	apdf = spdstack(sfils)
	apdf = apdf.drop_duplicates()
	apdf['poi_type'] = 'apt'	
	apdf['latlon'] = zip(apdf.listGeoLat, apdf.listGeoLon)
	apdf = apdf[np.isfinite(apdf.listGeoLat)]
	jnk = df2mongo2dsphere_collection(apdf, 'apts')

	# score aparements by poi type
	poi_types = ['hotel', 'parks', 'rest_bar', 'store', 'vet']
	boroughs = ['queens', 'brooklyn',
	            'staten+island', 'manhattan', 'bronx']

	for ptyp in poi_types:
	    for bors in boroughs:
	        jnk = scoreApartments(bors, ptyp)

	# average scores for each poi type
	for bors in boroughs:
	    jnk = aveZscore(bors)

if __name__ == '__main__':
    main()
