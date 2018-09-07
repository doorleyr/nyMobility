#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Sep  3 10:44:22 2018

@author: doorleyr
"""
import json
import urllib.request
import pandas as pd

def getCensusData(variables, key, url, forStr):
    fullUrl=url+'key='+key+'&get='+variables+'&for='+forStr
    with urllib.request.urlopen(fullUrl) as url:
        data=json.loads(url.read().decode())
    df=pd.DataFrame(data[1:],columns=data[0])
    return df

key = '7a25a7624075d46f112113d33106b6648f42686a'
acs_16_url = 'https://api.census.gov/data/2016/acs/acs5?'
variables='NAME,group(B01001)'

#First we need the list of tracts so we can construct a query 
# for all BGs within these tracts
for_tract_manhattan = 'tract:*&in=state:36&in=county:061'
dfTracts=getCensusData(variables, key, acs_16_url, for_tract_manhattan)
tractList=dfTracts['tract']

#create an empty dataframe, then loop through each tract 
#and get the data for each BG in that tract
df = pd.DataFrame()
for t in tractList:
    forStr="block%20group:*&in=state:36&in=county:061&in=tract:"+t
    bgDf=getCensusData(variables, key, acs_16_url, forStr)
    df=df.append(bgDf)


#Working example
#https://api.census.gov/data/2013/acs5?get=B01001_001E&for=block%20group:*&in=state:06&in=county:061&in=tract:*&key=7a25a7624075d46f112113d33106b6648f42686a

#Using groups:
#https://api.census.gov/data/2016/acs/acs5?get=NAME,group(B01001)&for=tract:*&in=state:36&key=7a25a7624075d46f112113d33106b6648f42686a

#Using block group geography
#https://api.census.gov/data/2016/acs/acs5?get=NAME,group(B01001)&for=block%20group:*&in=state:36&in=county:061&in=tract:*

#for one tract only
#https://api.census.gov/data/2016/acs/acs5?get=NAME,group(B01001)&for=block%20group:*&in=state:36&in=county:061&in=tract:000100