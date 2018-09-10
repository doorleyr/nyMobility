#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Sep  5 17:25:14 2018

@author: doorleyr
"""

import pandas as pd
import json
from shapely.geometry import Point, shape

def get_location(longitude, latitude, regions_json, name): 
    # for a given lat and lon, and a given geojson, find the name of the feature into which the latLon falls
    point = Point(longitude, latitude)
    for record in regions_json['features']:
        polygon = shape(record['geometry'])
        if polygon.contains(point):
            return record['properties'][name]
    return 'None'

#get communties geojson
communities=json.load(open('./spatialData/communityDistrictsManhattanOnly.geojson'))
ntas=json.load(open('./spatialData/Neighborhood Tabulation Areas.geojson'))
nycCounties=json.load(open('./spatialData/nycCounties.geojson'))
nj=json.load(open('./spatialData/newJersey.geojson'))
#get OD data
commuting=pd.read_csv('./od_data/tract2TractCommuting_NY.csv', skiprows=2)
#commuting['RESIDENCE']=commuting.apply(lambda row: str(row['RESIDENCE']).split(',')[0], axis=1)
#commuting['WORKPLACE']=commuting.apply(lambda row: str(row['WORKPLACE']).split(',')[0], axis=1)
commuting=commuting[~commuting['Workers 16 and Over'].isnull()]
commuting['Workers 16 and Over']=commuting.apply(lambda row: float(str(row['Workers 16 and Over']).replace(',',"")), axis=1)# in case there are commas for separating 000s
#get tracts geojson
tracts=json.load(open('./spatialData/2010 Census Tracts.geojson'))
tractsManhattan=tracts.copy()
#tractsManhattan['features']=[f for f in tracts['features'] if f['properties']['COUNTY']=='061']
tractsManhattan['features']=[f for f in tracts['features'] if f['properties']['boro_name']=='Manhattan']
#get the full list of origins and destination names
allTracts=set(commuting['RESIDENCE']).union(set(commuting['WORKPLACE']))
#tractNamesGeo=[tractsManhattan['features'][i]['properties']['NAME'] for i in range(len(tractsManhattan['features']))]
tractNamesGeo=[tractsManhattan['features'][i]['properties']['ctlabel'] for i in range(len(tractsManhattan['features']))]

#create empty dict of name to custom zones
#check if name contains New Jersey: map to NJ
#if not, check if not in New York County: map to the boro name
# if in NY county, look up the tract in the geojson and map to the ntaname
# OR get the tract centroid and find which community district its in
tracts2Comms={}
tracts2Nhoods={}
for t in allTracts:
    if 'New Jersey' in t:
        tracts2Comms[t]='New Jersey'
        tracts2Nhoods[t]='New Jersey'
    elif 'New York County' not in t:
        tracts2Comms[t]=t.split(', ')[1]
        tracts2Nhoods[t]=t.split(', ')[1]
    else:
#        tracts2Comms[t]=getLocation()
        tractNum=t.split(',')[0].split(' ')[2]
        tractInd=tractNamesGeo.index(tractNum)
#        tracts2Nhoods[t]=tractsManhattan['features'][tractInd]['properties']['ntaname']
        tractCentroid=shape(tractsManhattan['features'][tractInd]['geometry']).centroid
        comm=get_location(tractCentroid.x, tractCentroid.y, communities, 'Name')
        nHood=get_location(tractCentroid.x, tractCentroid.y, ntas, 'ntaname')
        if comm=='None':
            print(t)
            if tractNum =='309':
                comm='Bronx County'  #exception: this census tract is actually in New York County but not considered part of any of the Manhattan community districts
        if nHood=='None':
            print('nHood')
            print(t)
        tracts2Comms[t]=comm
        tracts2Nhoods[t]=nHood
        
commuting['oComm']=commuting.apply(lambda row: tracts2Comms[row['RESIDENCE']], axis=1)
commuting['dComm']=commuting.apply(lambda row: tracts2Comms[row['WORKPLACE']], axis=1)
commuting['oNhood']=commuting.apply(lambda row: tracts2Nhoods[row['RESIDENCE']], axis=1)
commuting['dNhood']=commuting.apply(lambda row: tracts2Nhoods[row['WORKPLACE']], axis=1)
#commuting['simpleMode']=commuting.apply(lambda row: cpttModeDict[row['Means of Transportation 18']], axis=1)

odComms=pd.crosstab(commuting['oComm'], commuting['dComm'], commuting['Workers 16 and Over'], aggfunc="sum").fillna(0)
odNHoods=pd.crosstab(commuting['oNhood'], commuting['dNhood'], commuting['Workers 16 and Over'], aggfunc="sum").fillna(0)
odComms.to_csv('./results/od_communityDistricts.csv')
odNHoods.to_csv('./results/od_neighbourhoods.csv')

odCommsMode=commuting.groupby(by=['oComm', 'dComm', 'Means of Transportation 18'], as_index=False).sum()
odNHoodsMode=commuting.groupby(by=['oNhood', 'dNhood', 'Means of Transportation 18'], as_index=False).sum()

#create a geojson including all the zones for the community district aggregation
geoOutComms=nycCounties.copy()
geoOutComms['features']=[]
for g in nycCounties['features']:
    if g['properties']['NAME']+' County' in odComms.columns.values:
        geoOutComms['features'].append({'properties':{'Name': g['properties']['NAME']+' County', 'type':'County'}, 'geometry': g['geometry']})
for c in communities['features']:
    if c['properties']['Name'] in odComms.columns.values:
        geoOutComms['features'].append({'properties':{'Name': c['properties']['Name'], 'type':'Community'}, 'geometry': c['geometry']})
geoOutComms['features'].append({'properties':{'Name': 'New Jersey', 'type':'State'}, 'geometry': nj['features'][0]['geometry']})

#create a geojson including all the zones for the nta aggregation
geoOutNHoods=nycCounties.copy()
geoOutNHoods['features']=[]
for g in nycCounties['features']:
    if g['properties']['NAME']+' County' in odNHoods.columns.values:
        geoOutNHoods['features'].append({'properties':{'Name': g['properties']['NAME']+' County', 'type':'County'}, 'geometry': g['geometry']})
for c in ntas['features']:
    if c['properties']['ntaname'] in odNHoods.columns.values:
        geoOutNHoods['features'].append({'properties':{'Name': c['properties']['ntaname'], 'type':'Neighbourhood'}, 'geometry': c['geometry']})
geoOutNHoods['features'].append({'properties':{'Name': 'New Jersey', 'type':'State'}, 'geometry': nj['features'][0]['geometry']})

#geoOutNHoods=nycCounties.copy()
#geoOutNHoods['features']=[g for g in nycCounties['features'] if g['properties']['NAME']+' County' in odNHoods.columns.values]
#for c in ntas['features']:
#    if c['properties']['ntaname'] in odNHoods.columns.values:
#        geoOutNHoods['features'].extend([c])
#geoOutNHoods['features'].extend([nj['features'][0]])

json.dump(geoOutComms, open('./results/allZonesComms.geojson', 'w'))
json.dump(geoOutNHoods, open('./results/allZonesNHoods.geojson', 'w'))
odCommsMode.to_csv('./results/od_communityDistricts_byMode.csv')
odNHoodsMode.to_csv('./results/od_neighbourhoods_byMode.csv')
