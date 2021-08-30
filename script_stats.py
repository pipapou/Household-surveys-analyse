#import libraries
import os
import numpy as np
import pandas as pd
import sklearn as sl
import seaborn as sns
import statistics
from scipy import stats
from rasterstats import zonal_stats
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from osgeo import gdal
import geopandas as gpd
import rasterio as rsto
import shapefile as shp
from shapely.geometry import Point, Polygon
import descartes
import pyreadstat
import math

#path
path="your_path/"

#shp
gpd_Map_prov = gpd.read_file(path+'BFA_adm2.shp')
gpd_Map_reg = gpd.read_file(path+'BFA_adm1.shp')

gpd_Map_prov = gpd_Map_prov[['NAME_1','NAME_2','geometry']]
gpd_Map_prov = gpd_Map_prov.rename(columns={'NAME_1':"REGION",'NAME_2':"PROVINCE"})

gpd_Map_reg = gpd_Map_reg[['NAME_1','geometry']]
gpd_Map_reg = gpd_Map_reg.rename(columns={'NAME_1':"REGION"})

#epa data
data_epa_c = pd.read_excel(path+"data_epa_prov_9-18-c.xlsx")
data_epa_s = pd.read_excel(path+"data_epa_prov_9-18-s.xlsx")

data_epa_c_r = pd.read_excel(path+"data_epa_reg_9-18-c.xlsx")
data_epa_s_r = pd.read_excel(path+"data_epa_reg_9-18-s.xlsx")

data_epa_s_expl_src=pd.read_excel(path+"data_epa_prov_9-18-s_expl.xlsx")

#pretreatments
for i in data_epa_c.drop(['ANNEE','REGION','PROVINCE'],axis=1).columns.tolist():
    data_epa_c.rename(columns={i:i+"_epa"}, inplace=True)
for i in data_epa_s.drop(['ANNEE','REGION','PROVINCE'],axis=1).columns.tolist():
    data_epa_s.rename(columns={i:i+"_epa"}, inplace=True)
for i in data_epa_c_r.drop(['ANNEE','REGION'],axis=1).columns.tolist():
    data_epa_c_r.rename(columns={i:i+"_epa"}, inplace=True)
for i in data_epa_s_r.drop(['ANNEE','REGION'],axis=1).columns.tolist():
    data_epa_s_r.rename(columns={i:i+"_epa"}, inplace=True)

#hists FCS, HDDS, rCSI
#distrib fcs
data_epa_s.sca.hist(bins=50)
plt.xlabel("FCS", fontsize=15)
plt.ylabel("Frequency",fontsize=15)

#distrib hdds
data_epa_s.sda.hist(bins=50)
plt.xlabel("HDDS", fontsize=15)
plt.ylabel("Frequency",fontsize=15)

#distrib rcsi
data_epa_c.csi.hist(bins=50)
plt.xlabel("rCSI", fontsize=15)
plt.ylabel("Frequency",fontsize=15)

# temporal graph fcs
reg=["EST","BOUCLE DU MOUHOUN","BURKINA FASO"]
color=["b--","g--","black"]
fig,ax=plt.subplots(figsize=(8,8))
for i in range(len(reg)):
    temp=data_epa_s_r[data_epa_s_r.REGION==reg[i]]
    plt.plot(temp['ANNEE'],temp['sca_epa'],color[i],label=reg[i])
plt.legend(loc="best", prop={'size': 12})
plt.xlabel("Year", fontsize=15)
plt.ylabel("Food consumtion score",fontsize=15)
plt.xticks(np.arange(2009, 2018, 1))
plt.grid(True)

# temporal graph hdds
reg=["EST","BOUCLE DU MOUHOUN","BURKINA FASO"]
color=["b--","g--","black"]
fig,ax=plt.subplots(figsize=(8,8))
for i in range(len(reg)):
    temp=data_epa_s_r[data_epa_s_r.REGION==reg[i]]
    plt.plot(temp['ANNEE'],temp['sda_epa'],color[i],label=reg[i])
plt.legend(loc="best", prop={'size': 12})
plt.xlabel("Year", fontsize=15)
plt.ylabel("Household Dietary Diversity Score",fontsize=15)
plt.xticks(np.arange(2009, 2018, 1))
plt.grid(True)

#spacialization
crs={'init':'epsg:6326'}
geometry='geometry'

data_epa_s_r_ = data_epa_s_r[(data_epa_s_r.ANNEE>2013) & (data_epa_s_r.ANNEE<2018)]
gpd_epa_s_moy_r = pd.merge(data_epa_s_r_[['REGION','sda_epa','sca_inf_epa']].groupby(['REGION']).agg({'sda_epa':"mean",'sca_inf_epa':"mean"}).reset_index(),
                  gpd_Map_reg,how='left', on=['REGION'])
geo_epa_s_moy_r = gpd.GeoDataFrame(gpd_epa_s_moy_r,crs=crs,geometry=geometry)

data_epa_c_r_ = data_epa_c_r[(data_epa_c_r.ANNEE>2013) & (data_epa_s_r.ANNEE<2018)]
gpd_epa_c_moy_r = pd.merge(data_epa_c_r_[['REGION','csi_epa']].groupby(['REGION']).agg({'csi_epa':"mean"}).reset_index(),
                  gpd_Map_reg,how='left', on=['REGION'])
geo_epa_c_moy_r = gpd.GeoDataFrame(gpd_epa_c_moy_r,crs=crs,geometry=geometry)

#map FCS
data=geo_epa_s_moy_r
var='sca_inf_epa'
r = mpatches.Patch(color='#ff8b73', label='More than 10%')
j = mpatches.Patch(color='#fcdf79', label='Between 5% and 10%')
v = mpatches.Patch(color='#b4f05d', label='Less than 5%')
fig,ax=plt.subplots(figsize=(15,15))
data.plot(ax=ax, linewidth=0.4, edgecolor='black')
data[data[var]>0.1].plot(ax=ax,color="#ff8b73")
data[(data[var]>0.05) & (data[var]<=0.1)].plot(ax=ax,color="#fcdf79")
data[data[var]<=0.05].plot(ax=ax,color="#b4f05d")
data.apply(lambda x: ax.annotate(s=x.REGION, xy=x.geometry.centroid.coords[0], ha='center'),axis=1)
plt.legend(loc="best", prop={'size': 12},handles=[r,j,v])

#map HDDS
data=geo_epa_s_moy_r
var='sda_epa'
r = mpatches.Patch(color='#ff8b73', label='HDDS low: [0 - 5[')
j = mpatches.Patch(color='#fcdf79', label='HDDS limit: [5 - 5.75[')
v = mpatches.Patch(color='#b4f05d', label='HDDS acceptable: ≥ 5.75')
fig,ax=plt.subplots(figsize=(15,15))
data.plot(ax=ax, linewidth=0.4, edgecolor='black')
data[data[var]<5].plot(ax=ax,color="#ff8b73")
data[(data[var]>=5) & (data[var]<5.75)].plot(ax=ax,color="#fcdf79")
data[data[var]>=5.75].plot(ax=ax,color="#b4f05d")
data.apply(lambda x: ax.annotate(s=x.REGION, xy=x.geometry.centroid.coords[0], ha='center'),axis=1)
plt.legend(loc="best", prop={'size': 12},handles=[r,j,v])

#map rCSI
data=geo_epa_c_moy_r
var='csi_epa'
r = mpatches.Patch(color='#b4f05d', label='rCSI acceptable: [0 - 0.75[')
j = mpatches.Patch(color='#fcdf79', label='rCSI limit: [0.75 - 2.25[')
v = mpatches.Patch(color='#ff8b73', label='rCSI high: ≥ 2.25')
fig,ax=plt.subplots(figsize=(15,15))
data.plot(ax=ax, linewidth=0.4, edgecolor='black')
data[data[var]<0.75].plot(ax=ax,color="#b4f05d")
data[(data[var]>=0.75) & (data[var]<2.25)].plot(ax=ax,color="#fcdf79")
data[data[var]>=2.25].plot(ax=ax,color="#ff8b73")
data.apply(lambda x: ax.annotate(s=x.REGION, xy=x.geometry.centroid.coords[0], ha='center'),axis=1)
plt.legend(loc="best", prop={'size': 12},handles=[r,j,v])

#correlations with proxies

data_epa_s_expl=pd.merge(data_epa_s_expl_src,data_epa_c,how='inner', on=['ANNEE','REGION','PROVINCE'])

#normalization (centered reduced) Proxies
for i in range(2): # années n, n-1
    for j in range(5,11): # mois de mai à octobre
        data_epa_s_expl['ndvi_m{0}t-{1}'.format(j,i)]=data_epa_s_expl.filter(regex='ndvi_.*{0}\(.*t-{1}'.format(j,i)).max(axis=1)
        data_epa_s_expl['pluie_m{0}t-{1}'.format(j,i)]=data_epa_s_expl.filter(regex='pluie_.*{0}\(.*t-{1}'.format(j,i)).sum(axis=1)
        data_epa_s_expl['mais_m{0}t-{1}'.format(j,i)]=data_epa_s_expl.filter(regex='mais_.*{0}\(.*t-{1}'.format(j,i))
for i in range(2): # années n, n-1
    for j in range(5,11): # mois de mai à octobre
        for temp in ['ndvi','pluie','mais']:
            data_epa_s_expl[temp+'_norm{0}t-{1}'.format(j,i)]=(data_epa_s_expl[temp+'_m{0}t-{1}'.format(j,i)]-data_epa_s_expl.filter(regex=temp+'_m').stack().mean())/data_epa_s_expl.filter(regex=temp+'_m').stack().std()
for i in range(2): # années n, n-1
    for temp in ['ndvi','pluie','mais']:
        data_epa_s_expl[temp+'_normt-{0}'.format(i)]=data_epa_s_expl.filter(regex=temp+'_norm.*t-{0}'.format(i)).mean(axis=1)

#normalization (centered reduced) SA indicators
for i in ['sca','sda','csi']:
    data_epa_s_expl[i+'_norm']=(data_epa_s_expl[i]-data_epa_s_expl[i].mean())/data_epa_s_expl[i].std()

data_epa_s_expl=data_epa_s_expl.filter(regex='norm')

# calculate the correlation matrix
pd.concat([data_epa_s_expl[['sca_norm','sda_norm','csi_norm']],data_epa_s_expl.filter(regex='normt')],axis=1).corr()