# -*- coding: utf-8 -*-
from a_Model import ModelIt
from flask import render_template, request, redirect
from app import app
import pymysql as mdb
import pandas as pd
import numpy as np
import sys
sys.path.append("../scripts")
from db_mongo import * 
from sklearn import cluster
from sklearn.preprocessing import StandardScaler
import json 

@app.route('/')

@app.route('/input')
def dh_input():
	return render_template("input.html")

@app.route('/input_error')
def dh_input_error():
  return render_template("input_error.html")

@app.route('/output')
def dh_output():
	burr = request.args.get('burr')
	burro = burr.replace('-','+')
	burr = burr.replace('-',' ')
	mprce = request.args.get('mprce')
	mbth = request.args.get('mbth')
	bed = request.args.get('bed')

	# connect to database
	db=MongoClient().dogh

	# query filtering on borough
	alst=db.apts.find(SON([('borough',burro.lower())]))
	pdf=pd.DataFrame.from_dict([aa for aa in alst])
	alst=db.rest_bar.find(SON([('borough',burr)]))
	da_pdf=pd.DataFrame.from_dict([aa for aa in alst])
	alst=db.hotel.find(SON([('borough',burr)]))
	dh_pdf=pd.DataFrame.from_dict([aa for aa in alst])

	da_pdf['addr_lat'] = da_pdf['latlon'].apply(lambda x: x[0]) 
	da_pdf['addr_lon'] = da_pdf['latlon'].apply(lambda x: x[1]) 
	dh_pdf['addr_lat'] = dh_pdf['latlon'].apply(lambda x: x[0]) 
	dh_pdf['addr_lon'] = dh_pdf['latlon'].apply(lambda x: x[1]) 
	sub = pdf[pdf.score > -1000.0]
	sub = sub[sub.listPrice.astype(float) < np.float(mprce)]

	sub.bedrooms=sub.listBed.astype(float)
	sub.bathrooms=sub.listBath.astype(float)
	sub = sub[sub.listBath >= np.float(mbth)]
	sub = sub[sub.listBed == np.float(bed)]
	print('lensub',len(sub),sub.listPrice)
	if len(sub) <=1: 
		return redirect('input_error')

	# sort by score and take top 48
	aa = sub.sort(['score'], ascending=[False])[0:48]
	fapts = []

	# cluster using sci-kit learn's DBSCAN
	sdf = aa.ix[:,['listGeoLon','listGeoLat']]
	dbscan = cluster.DBSCAN(eps=0.25, min_samples=4)
	X = StandardScaler().fit_transform(sdf.values)
	dft = dbscan.fit(X)
	clabs= list(dft.labels_)
	n_clusters_ = len(set(clabs)) - (1 if -1 in clabs else 0)

	# for each cluster find centroid and query for nearby pois
	aa['cluster_label']=clabs 
	aa=aa[aa.cluster_label <= 4]
	poi_types = {'store':1,'hotel':2,'rest_bar':3,'vet':4}
	clab_col = {-1:'box white',0:'box blue',1:'box red',
		2:'box green',3:'box orange',4:'box purple'}
	opdf = pd.DataFrame()
	for cl in range(np.min([n_clusters_,5])):
		caa = aa[aa.cluster_label==cl]
		avlat = np.mean(caa['latlon'].apply(lambda x: x[0]))
		avlon = np.mean(caa['latlon'].apply(lambda x: x[1]))
		tpdf = pd.DataFrame()
		print(avlat,avlat)
		for poi in poi_types.keys():
			tmp = geoNearQuery([avlon,avlat],poi,0.75,db)['results']
			tpdf = tpdf.append(pd.DataFrame.from_dict([tt['obj'] for tt in tmp]))
		tpdf['cluster_label']=cl
		opdf=opdf.append(tpdf)
		opdf['poi_typen'] = opdf['poi_type'].apply(lambda x: poi_types[x])

	# for each cluster find centroid and query for nearby pois
	for resi in aa.index: 
		address = aa.ix[resi,'address'].strip()
		score = str(aa.ix[resi,'score'])[0:5]
		bedrms = aa.ix[resi,'listBed']
		bthrms = aa.ix[resi,'listBath']
		price  = np.int(aa.ix[resi,'listPrice'])
		sqft = aa.ix[resi,'listSqFt']
		clab = clab_col[aa.ix[resi,'cluster_label']]
		fapts.append(dict(title=address,score=score,bedrms=bedrms,clab=clab,
			bthrms=bthrms,price=price,sqft=sqft,nclust=n_clusters_ ))

	lats = list(aa.listGeoLat.astype(np.float))
	lons = list(aa.listGeoLon.astype(np.float))
	listID = list(aa.listID.astype(np.int))
	listAdd = list(aa['address'].apply(lambda x: x.encode('UTF-8')).values)
	jlistAdd = json.dumps(listAdd)
	dalats = list(da_pdf.addr_lat.astype(np.float))
	dalons = list(da_pdf.addr_lon.astype(np.float))
	dhlats = list(dh_pdf.addr_lat.astype(np.float))
	dhlons = list(dh_pdf.addr_lon.astype(np.float))

	opdf['addr_lat'] = opdf['latlon'].apply(lambda x: x[0])
	opdf['addr_lon'] = opdf['latlon'].apply(lambda x: x[1])

	cpoi = list(opdf.poi_typen.values)
	cyurl = list(opdf['yurl'].apply(lambda x: x.encode('UTF-8')).values)
	cname = list(opdf['name'].apply(lambda x: x.encode('UTF-8')).values)
	jcyurl = json.dumps(cyurl)
	jcname = json.dumps(cname)

	clats = list(opdf.addr_lat.values)
	clons = list(opdf.addr_lon.values)
	cclst = list(opdf.cluster_label.values)

  	return render_template("output.html",fapts=fapts, clabs=clabs, 
	mlat=np.median(dhlats), mlon=np.median(dhlons),
  	lats=lats,lons=lons, dalats=dalats, dalons=dalons,listID =listID,
	dhlats=dhlats, dhlons=dhlons, nclust=n_clusters_,
	cpoi=cpoi, cyurl=jcyurl, cname=jcname, listAdd = jlistAdd,
	clats=clats, clons=clons,cclst=cclst)

def index_template():
	user = { 'nickname': 'qpo' } 
	return render_template("index.html",
		title = 'Home', user = user)
