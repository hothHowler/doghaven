import pymongo
import pandas as pd
from dogh import *
import multiprocessing as mp

from pymongo import MongoClient
import geojson
from bson.son import SON
import pymongo
from pymongo import MongoClient, GEO2D, GEOSPHERE
import pandas as pd 
from scipy.stats.mstats import zscore

def rawScoreInverseDistWeight(docs): 
	dsts = [doc['dis'] for doc in docs['results']]
	return np.mean(np.sqrt(1./np.array(dsts)))

def rawScoreSimple(docs): 
	ndocs = docs['stats']['objectsLoaded']
	if ndocs == 0: 
		return 0.0
	else: 
		tmp = ndocs/docs['stats']['avgDistance']	
		if not np.isfinite(tmp): 
			print('nan',tmp)
			return 0.0
		return tmp 

def geoNearQuery(lonlat,poi_type,dthsh,db):
	docs = db.command(SON([('geoNear', poi_type), 
			('near',lonlat),
			('spherical','true'),
			('maxDistance',dthsh/6371),
			('num',100000)]))
	return docs

def aveZscore(borough): 
	db=MongoClient().dogh
	lst=db.apts.find(SON([('borough',borough)]))
	for ll in lst: 
		avez = np.mean([ll['zscore_hotel'],ll['zscore_parks'],
						ll['zscore_store'],ll['zscore_vet'],
						ll['zscore_rest_bar']])
		ll['score'] = avez 
		db.apts.update({'_id':ll['_id']},{"$set":ll},upsert=False)
	return 1

def scoreApartments(borough, poi_type, dthsh=1.60934, plt_smry = False): 
	db=MongoClient().dogh
	lst=db.apts.find(SON([('borough',borough)]))
	print(poi_type)
	raw_scores = []
	for lstng in lst: 
		lonlat=lstng['loc']
		docs = geoNearQuery(lonlat,poi_type,dthsh,db)
		raw_scores.append(rawScoreSimple(docs))
	zscores = zscore(raw_scores)
	lst.rewind()
	for lstng,zscr in zip(lst,zscores):
		lstng['zscore_'+poi_type]=zscr		
		db.apts.update({'_id':lstng['_id']},{"$set":lstng},upsert=False)	
	return 1

def df2mongo_collection(ipdf,collection_name): 
	db = MongoClient().dogh
	db[collection_name].create_index([("loc", GEO2D)])

	if (type(ipdf.iloc[0]['latlon'])==tuple):
		ipdf=ipdf[ipdf.latlon.apply(lambda x: x[0])!=-10000]
		ipdf.insert(0,'loc', ipdf['latlon'].apply(lambda x: [x[1],x[0]]))
	if (type(ipdf.iloc[0]['latlon'])==dict): 
		ipdf.insert(0,'loc', ipdf['latlon'].apply(lambda x: [x['longitude'],x['latitude']]))

	ipdf.index = range(len(ipdf))
	plst = [pd.DataFrame(ipdf.iloc[ii]).to_dict()[ii] for ii in ipdf.index]
	for doc in plst: 
		db[collection_name].insert(doc)

def df2mongo2dsphere_collection(ipdf,collection_name): 
	db = MongoClient().dogh
	db[collection_name].create_index([("loc", GEOSPHERE)])

	if (type(ipdf.iloc[0]['latlon'])==tuple):
		ipdf=ipdf[ipdf.latlon.apply(lambda x: x[0])!=-10000]
		ipdf.insert(0,'loc', ipdf['latlon'].apply(lambda x: [x[1],x[0]]))
	if (type(ipdf.iloc[0]['latlon'])==dict): 
		ipdf.insert(0,'loc', ipdf['latlon'].apply(lambda x: [x['longitude'],x['latitude']]))

	ipdf.index = range(len(ipdf))
	plst = [pd.DataFrame(ipdf.iloc[ii]).to_dict()[ii] for ii in ipdf.index]
	for doc in plst: 
		db[collection_name].insert(doc)

def main(): 

	# yelp 
	fls = glob.glob('../data/yelp/*.pk')
	typ = ['rest_bar','vet','store','hotel']

	for fl,ty in zip(fls,typ):	
		print(fl,ty)	
		ypdf = pd.read_pickle(fl)
		ypdf['addr_zip'] = ypdf['address'].apply(lambda x: x.split()[-1])
		ypdf['borough']=ypdf['addr_zip'].apply(get_bur)
		ypdf=ypdf[ypdf['addr_zip']!='NY']
		ypdf=ypdf[ypdf['addr_zip']!='None']
		ypdf=ypdf[ypdf['borough']!='None']
		ypdf['latlon'] = ypdf['latlon'].apply(lambda x: (x['latitude'],x['longitude']))
		ypdf['poi_type'] = ty
		ypdf=ypdf[ypdf.name!='Ad']
		ypdf = ypdf.drop_duplicates()
		df2mongo_collection(ypdf,ty)

	# nyc 

	parks = pd.read_csv('../data/nyc_opendata/DPR_ParksProperties_001.csv')
	parks['googloc'] = parks['SIGNNAME'].apply(lambda x: dogh_geolocate_google(x+',NY'))
	parks['latlon'] = parks['googloc'].apply(lambda x: (x[0],x[1]))	
	parks['poi_type'] = 'park'
	parks['name'] = parks['SIGNNAME']
	df2mongo_collection(parks,'nyc')



if __name__ == '__main__':
    main()
