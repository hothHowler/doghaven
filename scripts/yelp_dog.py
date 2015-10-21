# trying to get html of things from 
import urllib2 
from bs4 import BeautifulSoup
from wordcloud import WordCloud, STOPWORDS
import itertools
import time
from datetime import datetime
import pandas as pd 
import numpy as np
from geopy.geocoders import Nominatim 
import scipy 
import glob
import resource
import scrapy
import json
import mechanize
from math import * 
import time

def readparse(inputurl):
# return bs4 parsed html page
    np.random.rand(1)
    #rsp = urllib2.urlopen(inputurl)
    rsp = mechanize.urlopen(inputurl)
    htmlo = rsp.read()
    prsd = BeautifulSoup(htmlo)
    return prsd

def get_datalayer_script(html):
# get script tag corresponding to datalayer from google tagmanager
    allscript = html.find_all('script')
    for thisscript in allscript: 
        txt = thisscript.get_text()
        if txt.find('dataLayer')!=-1: 
            return txt
    print('Error: no script tag matches data layer')
    return -1       

def datalayer_script2list(txt): 
# convert script tag to python list by modifying string and evaluating
    sloc = txt.find("dataLayer")    
    eloc = txt.find(";\n")
    print(eloc)
    txt = txt[sloc:eloc]
    txt = txt.replace('null','"None"')
    txt = txt.replace('false','"False"')
    txt = txt.replace('true','"True"')    
    exec(txt)
    return dataLayer

def list2pdf(dataLayer):
# convert recovered list to a pandas dataframe
    slst = dataLayer[0]['searchResultsListings']
    d1 = slst.pop('1')
    d1['data']={'jnk':'jnk'}
    pdf = pd.DataFrame.from_dict(d1) 
    # flatten the lists within the lists to avoid 
    # replication of rows in pandas dataframe
    for jj in slst:     
        dj = slst[jj]
        dj['data']={'jnk':'jnk'}
        ss = pd.DataFrame.from_dict(slst[jj])
        pdf = pdf.append(ss)
    return(pdf)
    
def read_strpage(nurl): 
    print(nurl)
    html = readparse(nurl)
    # loop through 
    dltxt = get_datalayer_script(html) 
    dllst = datalayer_script2list(dltxt)
    pdf = list2pdf(dllst)   
    return pdf



def geocode_w(txt):
    time.sleep(16+scipy.randn(1))
    geoloc = Nominatim()
    print(txt)
    cded = geoloc.geocode(txt)
    geoloc = 0 
    return cded

def add2latlon(pdf): 
    #geoloc = Nominatim()
    #pdf['latlon'] = pdf['address'].apply(geocode_w)
    latlons = []
    adds = pdf['address'].values
    for jtxt in adds:
        print(jtxt)
        time.sleep(32+abs(3.*scipy.randn(1)))
        geoloc = Nominatim()
        latlons.append(geoloc.geocode(jtxt))
        geoloc = 0        
    pdf['latlon']=latlons
    return pdf

def get_lat_lons(html): 
    # get bisness url given yelp html having 
    # searched for a type of business in a certain area
    allscript = html.find_all('a',{"class":"biz-name"})    
    allbizurl = []
    for atag in allscript:         
        ss = 'http://www.yelp.com'+atag['href']
        thisisad = ss.find('adredir?ad_')
        if thisisad==-1:
            allbizurl.append(ss)
    return allbizurl

def get_bizurlinfo(bizurl):
    print(bizurl)
    time.sleep(4+2.*np.abs(np.random.randn(1)))
    html = readparse(bizurl)    
    if len(html) > 4:
        btitle = html.find_all('h1')[0].contents
        baddy = html.find_all('address')[0].contents    
        bizid = html.find_all('meta',{"name":"yelp-biz-id"})[0]['content']
    else:
        return None,"Ad", "None"
    # withouth the ".strip()" here, the "\n" newline 
    # characters will chew up memory fast causing faliure for long scrapes
    return bizid, btitle[0].strip(), baddy[0].strip()
