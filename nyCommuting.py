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

#cpttModeDict={'drive':['Car, truck, or van -- Drove alone',
#             'Car, truck, or van -- In a 2-person carpool',
#            'Car, truck, or van -- In a 3-person carpool',
#            'Car, truck, or van -- In a 4-person carpool',
#            'Car, truck, or van -- In a 5-or-6-person carpool',
#            'Car, truck, or van -- In a 7-or-more-person carpool',
#            'Motorcycle'],
#'bus': ['Bus or trolley bus'],
#'subway': ['Subway or elevated'],
#'rail': ['Railroad'],
#'cycle': ['Bicycle'],
#'taxi': ['Taxicab'],
#'walk':['Walked'],
#'home':['Worked at home']}

#get communties geojson
communties=json.load(open('./spatialData/communityDistrictsManhattanOnly.geojson'))
ntas=json.load(open('./spatialData/Neighborhood Tabulation Areas.geojson'))
#get OD data
commuting=pd.read_csv('./od_data/tract2TractCommuting_NY.csv', skiprows=2)
#commuting['RESIDENCE']=commuting.apply(lambda row: str(row['RESIDENCE']).split(',')[0], axis=1)
#commuting['WORKPLACE']=commuting.apply(lambda row: str(row['WORKPLACE']).split(',')[0], axis=1)
commuting=commuting[~commuting['Workers 16 and Over'].isnull()]
commuting['Workers 16 and Over']=commuting.apply(lambda row: float(str(row['Workers 16 and Over']).replace(',',"")), axis=1)# in case there are commas for separating 000s
#get tracts geojson
#tracts=json.load(open('/Volumes/GoogleDrive/My Drive/Fulbright/CooperH/spatialData/census2010TractsOfficial.geojson'))
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
        comm=get_location(tractCentroid.x, tractCentroid.y, communties, 'Name')
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

#odCommsMode=commuting.groupby(['oComm', 'dComm', 'Means of Transportation 18']).
      