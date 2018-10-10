#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Sep 25 11:34:59 2018

@author: doorleyr
"""

import pandas as pd
import re
from collections import OrderedDict
from sklearn import tree
import graphviz
import numpy as np
import matplotlib.pyplot as plt
from sklearn.tree import _tree

def tree_to_code(tree, feature_names):
    # takes a fitted decision tree and outputs a python function
    with open('results/modeChoice.py', 'w') as the_file: 
        the_file.write('def predictModeProbs():\n')
        tree_ = tree.tree_
        feature_name = [
            feature_names[i] if i != _tree.TREE_UNDEFINED else "undefined!"
            for i in tree_.feature
        ]
        def recurse(node, depth):
            indent = "    " * (depth)
            if tree_.feature[node] != _tree.TREE_UNDEFINED:
                name = feature_name[node]
                threshold = tree_.threshold[node]
#                print ("{}if {} <= {}:".format(indent, name, threshold))
                the_file.write("{}if {} <= {}:\n".format(indent, name, threshold))
                recurse(tree_.children_left[node], depth + 1)
                the_file.write("{}else:  # if {} > {}\n".format(indent, name, threshold))
#                print ("{}else:  # if {} > {}".format(indent, name, threshold))
                recurse(tree_.children_right[node], depth + 1)
            else:
                n_samples=sum([int(v) for v in tree_.value[node][0]])
                the_file.write("{}return {}\n".format(indent, [round(v/n_samples,2) for v in tree_.value[node][0]]))
#                print ("{}return {}".format(indent, [int(v) for v in tree_.value[node][0]]))
        recurse(0, 1)
    
def findPattern(sched, regPatterns):
    # takes a sequence of activities and maps it to one of the pre-defined motifs
    for r in reversed(regPatterns):
        #checking the most complex first
        if r.match(sched):
            return regPatterns[r]
    if sched=='h':
        return 1
    else:
        return 0

cbsa='35620' # New York-ish

whyDict={
        # map NHTS activities to a simpler list of activities
        1:'h',2:'h',
        3:'w',4:'w',5:'w',
        6:'o',
        7:'t',
        8:'w',
        9:'o',10: 'o',11: 'o',12: 'o',13: 'o',14: 'o',
        15: 'o',16: 'o',17: 'o',18: 'o',19: 'o',97: 'o'}

modeDict={
        # map NHTS modes to a simpler list of modes
        # 0: drive, 1: cycle, 2: walk, 3: PT
        -7:-99,-8:-99,-9:-99,
        1:2,
        2:1,
        3:0,4:0,5:0,6:0,
        7:-99,
        8:0,9:0,
        10:3,11:3,12:3,13:3,14:3,15:3,16:3,
        17:0,18:0,
        19:3,20:3,
        97:-99}

regPatterns=OrderedDict()
#define the motifs and create regular expressions to represent them
# Based on http://projects.transportfoundry.com/trbidea/schedules.html
regPatterns[re.compile('(h-)+h')]=1 #'home'
regPatterns[re.compile('(h-)+w-h')]=2#'simpleWork'
regPatterns[re.compile('(h-)+w-(w-)+h')]=3 #'multiPartWork'
regPatterns[re.compile('(h-)+o-h')]= 4#'simpleNonWork'
regPatterns[re.compile('(h-)+o-(o-)+h')]=5 #'multiNonWork'
regPatterns[re.compile('(h-)+o-([wo]-)*w-h')]=6 #'compToWork'
regPatterns[re.compile('(h-)+w-([wo]-)*o-h')]=7 #'compFromWork'
regPatterns[re.compile('(h-)+o-([wo]-)*w-([wo]-)*o-h')]=8 #'compToFromWork'
regPatterns[re.compile('(h-)+w-([wo]-)*o-([wo]-)*w-h')]=9 #'compAtWork'  

# simplest version of each pattern
patternDict={1:'H',
             2: 'HWH',
             3: 'HWWH',
             4: 'HOH',
             5: 'HOOH',
             6: 'HOWH',
             7: 'HWOH',
             8: 'HOWOH',
             9: 'HWOWH'}   

# define the number of people in each occupation type for each block type in the library
blocks={'block_1':
            {'occupationCat_1':100, 'occupationCat_2':100, 'occupationCat_3':100, 'occupationCat_4':100},
        'block_2':
            {'occupationCat_1':200, 'occupationCat_2':300, 'occupationCat_3':400, 'occupationCat_4':500},
        'block_3':
            {'occupationCat_1':500, 'occupationCat_2':300, 'occupationCat_3':200, 'occupationCat_4':100}
        }  

maxDepth=3 # the max number of if statements to decide on a mode choice

# need to download the NHTS 2017 v1.1 csv files from: 
# https://nhts.ornl.gov/
trips=pd.read_csv('./nhts/trippub.csv')
persons=pd.read_csv('nhts/perpub.csv')

#NHTS variables:
#TRPMILES: shortest path distance from GMaps
#EDUC: educational attainment
#HHFAMINC: HH income
#HHVEHCNT: vehicle count (HH)
#HH_CBSA: core-based stat area (35620: New York-Newark-Jersey City, NY-NJ-PA, 14460: Boston-Cambridge-Newton)
#HOMEOWN: home ownership
#PRMACT: primary activity previous week (employment school etc.)
#R_AGE_IMP: age (imputed)
#TRAVDAY: day of week, 1: Sunday, 7: Sat
#TRPTRANS: mode
#WHYFROM: trip origin purpose
#WHYTO: Trip Destination Purpose
#OCCAT:	Job category

########################## Clean and prepare the NHTS data ######################################

# get subset of data for New York, New Jersey and Newark urban areas
trips_nnn=trips.loc[((trips['HH_CBSA']==cbsa) & (trips['HBHUR']=='U'))]# ny, nj, newark, Urban
trips_nnn['uniquePersonId']=trips_nnn.apply(lambda row: str(row['HOUSEID'])+'_'+str(row['PERSONID']), axis=1)
trips_nnn=trips_nnn[(trips_nnn['WHYTO']>0)&(trips_nnn['WHYFROM']>0)]

#remove small number of trip legs which were just for changing mode of transportation
trips_nnn_nTrans=trips_nnn[((trips_nnn['WHYTO']!=7) & (trips_nnn['WHYFROM']!=7))]

# map nhts activities to simple list of activities
trips_nnn_nTrans['whyToMapped']=trips_nnn_nTrans.apply(lambda row: whyDict[row['WHYTO']], axis=1)
trips_nnn_nTrans['whyFromMapped']=trips_nnn_nTrans.apply(lambda row: whyDict[row['WHYFROM']], axis=1)

persons['uniquePersonId']=persons.apply(lambda row: str(row['HOUSEID'])+'_'+str(row['PERSONID']), axis=1)
persons_nnn=persons.loc[persons['uniquePersonId'].isin(trips_nnn_nTrans['uniquePersonId'])]

#remove records with unknown variables that we need
persons_nnn=persons_nnn.loc[persons_nnn['HHFAMINC']>=0]
persons_nnn=persons_nnn.loc[persons_nnn['PRMACT']>=0] 
persons_nnn=persons_nnn.loc[persons_nnn['LIF_CYC']>=0]
persons_nnn=persons_nnn.loc[persons_nnn['OCCAT']>=0]
#only keep people whose travel diary was on a weekday
persons_nnn=persons_nnn.loc[persons_nnn['TRAVDAY'].isin([2,3,4,5,6])]

# get the daily activity schedule for each person using the regular expressions
daySched={}
for id in set(trips_nnn_nTrans['uniquePersonId']):
    mappedSched=[trips_nnn_nTrans.loc[trips_nnn_nTrans['uniquePersonId']==id]['whyFromMapped'].iloc[0]]
    mappedSched.extend(trips_nnn_nTrans.loc[trips_nnn_nTrans['uniquePersonId']==id]['whyToMapped'].tolist())
#    schedule=list(filter(lambda a: a != 7, schedule)) # remove changes in transportation
#    assume each day starts at home
    if not mappedSched[0]=='h':
        mappedSched.insert(0, 'h')
    if not mappedSched[-1]=='h':
         mappedSched.extend(['h'])
    strSched='-'.join(mappedSched)
    schedPattern=findPattern(strSched, regPatterns)
    daySched[id]=schedPattern

# add the day schedule to the persons and trips dataframes
trips_nnn_nTrans['daySched']= trips_nnn_nTrans.apply(lambda row: daySched[row['uniquePersonId']], axis=1) 
persons_nnn['daySched']=persons_nnn.apply(lambda row: daySched[row['uniquePersonId']], axis=1)

# add the motif (simplest example of the mobility pattern) to the persons and trips dataframes
persons_nnn['motif']=persons_nnn.apply(lambda row: patternDict[row['daySched']], axis=1)
trips_nnn_nTrans['motif']=trips_nnn_nTrans.apply(lambda row: patternDict[row['daySched']], axis=1)

personsSimple=persons_nnn[['HHFAMINC', 'LIF_CYC',  'OCCAT', 'R_AGE_IMP']]
personsSimple=personsSimple.rename(columns={'HHFAMINC':'hh_income', 'LIF_CYC':'hh_lifeCycle',  'OCCAT':'occupation_type', 'R_AGE_IMP':'age'})
personsSimple=pd.concat([personsSimple, pd.get_dummies(persons_nnn['motif'], prefix='motif')],  axis=1)

######### Create the synthetic population based on the block characteristics ############### 

simPop=pd.DataFrame()
for b in blocks:
    for typ, N in blocks[b].items():
        occat=int(typ.split('_')[1])
        sample=personsSimple.loc[personsSimple['occupation_type']==occat].sample(n=N, replace=True)
        sample['block']=b
        simPop=simPop.append(sample)
simPop=simPop.reset_index(drop=True)        
simPop.to_csv('results/simPop.csv')

######################### Mode Choice Decision Tree ###################################
trips_nnn_nTrans=trips_nnn_nTrans.rename(columns={'HHFAMINC':'hh_income', 'LIF_CYC':'hh_lifeCycle',  'R_AGE_IMP':'age', 'TRPMILES': 'trip_leg_miles'})
dtFeats= ['hh_income', 'hh_lifeCycle', 'age',  'trip_leg_miles']

trips_nnn_nTrans=trips_nnn_nTrans.merge(persons_nnn, how='left', on='uniquePersonId', suffixes=('', '_copy'))
trips_nnn_nTrans['simpleMode']=trips_nnn_nTrans.apply(lambda row: modeDict[row['TRPTRANS']], axis=1)
trips_nnn_nTrans=trips_nnn_nTrans.loc[trips_nnn_nTrans['simpleMode']>=0]

catVars=['motif']
for cv in catVars:
    newDummies=pd.get_dummies(trips_nnn_nTrans[cv], prefix=cv)
    trips_nnn_nTrans=pd.concat([trips_nnn_nTrans, newDummies],  axis=1)
    dtFeats.extend(newDummies.columns.tolist())

dtData=trips_nnn_nTrans[dtFeats]


clf_mode = tree.DecisionTreeClassifier(max_depth=maxDepth, class_weight='balanced')            
clf_mode = clf_mode.fit(np.array(dtData), np.array(trips_nnn_nTrans['simpleMode']))
# vis importance
plt.figure(figsize=(18, 16))    
plt.bar(range(len(clf_mode.feature_importances_)), clf_mode.feature_importances_)
plt.xticks(range(len(clf_mode.feature_importances_)), dtFeats, rotation=45)

dot_data = tree.export_graphviz(clf_mode, out_file='results/treeModeSimple.dot',feature_names=dtFeats,  
                         class_names=['drive', 'cycle', 'walk', 'PT'],  
                         filled=True, rounded=True,  
                         special_characters=True) 
with open('results/treeModeSimple.dot') as f:
    dot_graph = f.read()
g=graphviz.Source(dot_graph)
g.render(filename='results/treeModeSimple')

tree_to_code(clf_mode, dtFeats)
 