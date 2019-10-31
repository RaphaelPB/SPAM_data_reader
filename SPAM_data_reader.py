# -*- coding: utf-8 -*-
"""
SPAM_data_reader reads and reframes SPAM data according to user's shapefiles and user defined crop groups
SPAM_data_reader is free software: you can redistribute it and/or modify it under the terms of the 
GNU General Public License version 3 (GPLv3) as published by the Free Software Foundation,
SPAM_data_reader is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. 
See the GNU General Public License for more details. You should have received a copy of the GNU General Public License 
along with SPAM_data_reader. If not, see http://www.gnu.org/licenses/.
Copyright 2019 Technical University of Denmark
Copyright 2019 COWI A/S
@author: raphael payet-burin (rapp@env.dtu.dk)
"""

#Libraries
import pandas as pd
import numpy as np
import geopandas as gpd
import os
from rasterstats import zonal_stats
import urllib.request
import zipfile

#OPTIONS
#ALL OPTIONS ARE TO BE SET IN EXCEL FILE 'SPAM_metadata.xlsx' - ADVANCED USER ONLY MAY CUSTOMIZE THE SCRIPT
#LOAD DATA
dirname = os.path.abspath(os.path.dirname(__file__))
optfile='SPAM_metadata.xlsx' #File containing options and SPAM metadata
skpr=10 #Size of header describing inputs in optfile
#Export options
export=pd.read_excel(optfile,sheet_name='EXPORTS', skiprows=skpr, engine='xlrd', index_col=[0]).to_dict()['export']
#Shapefiles
nshape=pd.read_excel(optfile,sheet_name='SHAPEFILES', skiprows=skpr, engine='xlrd')['nshape'].values
shapename=pd.read_excel(optfile,sheet_name='SHAPEFILES', skiprows=skpr, engine='xlrd', index_col=[0]).to_dict()['shapename']
shapeIDname=pd.read_excel(optfile,sheet_name='SHAPEFILES', skiprows=skpr, engine='xlrd', index_col=[0]).to_dict()['shapeIDname']
#Crops
ncrop=pd.read_excel(optfile,sheet_name='SPAMcrops', skiprows=skpr, engine='xlrd')['scrop'].values
cropignore=pd.read_excel(optfile,sheet_name='SPAMcrops', skiprows=skpr, engine='xlrd', index_col=[0]).to_dict()['cropignore']
ncrop=[c for c in ncrop if cropignore[c]!=1]
cropname=pd.read_excel(optfile,sheet_name='SPAMcrops', skiprows=skpr, engine='xlrd', index_col=[0]).to_dict()['cropname']
gcrop=pd.read_excel(optfile,sheet_name='GROUPcrops', skiprows=skpr, engine='xlrd')['gcrop'].values
cropgroup=pd.read_excel(optfile,sheet_name='GROUPcrops', skiprows=skpr, engine='xlrd', index_col=[0])
#Technologies
ntech=pd.read_excel(optfile,sheet_name='SPAMtechs', skiprows=skpr, engine='xlrd')['stech'].values
techignore=pd.read_excel(optfile,sheet_name='SPAMtechs', skiprows=skpr, engine='xlrd', index_col=[0]).to_dict()['techignore']
ntech=[t for t in ntech if techignore[t]!=1]
techname=pd.read_excel(optfile,sheet_name='SPAMtechs', skiprows=skpr, engine='xlrd', index_col=[0]).to_dict()['techname']
#Variables
nvar =pd.read_excel(optfile,sheet_name='SPAMvars', skiprows=skpr, engine='xlrd')['svar'].values
varignore=pd.read_excel(optfile,sheet_name='SPAMvars', skiprows=skpr, engine='xlrd', index_col=[0]).to_dict()['varignore']
nvar=[v for v in nvar if varignore[v]!=1]
varname=pd.read_excel(optfile,sheet_name='SPAMvars', skiprows=skpr, engine='xlrd', index_col=[0]).to_dict()['varname']
varfolder=pd.read_excel(optfile,sheet_name='SPAMvars', skiprows=skpr, engine='xlrd', index_col=[0]).to_dict()['varfolder']
unit_conv_factor=pd.read_excel(optfile,sheet_name='SPAMvars', skiprows=skpr, engine='xlrd', index_col=[0]).to_dict()['unit_conv_factor']
new_var_unit=pd.read_excel(optfile,sheet_name='SPAMvars', skiprows=skpr, engine='xlrd', index_col=[0]).to_dict()['new_var_unit']
#download variables settings
varurl=pd.read_excel(optfile,sheet_name='SPAMvars', skiprows=skpr, engine='xlrd', index_col=[0]).to_dict()['varurl']
vardownload=pd.read_excel(optfile,sheet_name='SPAMvars', skiprows=skpr, engine='xlrd', index_col=[0]).to_dict()['vardownload']
#Info
info=pd.read_excel(optfile,sheet_name='INFO', skiprows=skpr, engine='xlrd', index_col=[0])
#%%d Define functions
#download spam data
def download_SPAM(var):
    if not os.path.exists(varfolder[var]) and vardownload[var]==1: #Only downloads if folder does not exist AND download is requested by user
        print('Downloading data for '+varname[var])
        url = varurl[var]
        path_to_zip=varfolder[var]+'.zip'
        urllib.request.urlretrieve(url, path_to_zip)
        print('Unzipping data for '+varname[var])
        with zipfile.ZipFile(path_to_zip, 'r') as zip_ref:
            zip_ref.extractall(varfolder[var])
    if os.path.exists(varfolder[var]) and vardownload[var]==1:
        print(varname[var]+' data folder was found to exist and was hence not downloaded')

#custom mean function for yields - taking into account specificties of the SPAM rasters
def mymean(x): 
    npx=np.array(x)
    npx[npx==-1]=np.nan # By default no data values are -1 (to verify load the raster with raster=rasterio.open(path), then type raster.nodatavals)
    npx[npx==0]=np.nan # For the Yield, 0 values can be assumed as no data (otherwise mean yield is draged down)
    return np.nanmean(npx)
    #return np.quantile(npx,0.9) #alternative - use a quantile: 0.9 = Yield higher than 90% of found yields will be used (not as extreme as using max)

#load raster into panda dataframe for a specific crop, technology and variable according to given shapefile
def load_raster_data(pdata,crop,tech,var,shapefile): #
    raster_name = 'spam2010V1r1_global_'+str(var)+'_'+str(crop)+'_'+str(tech)+'.tif'
    raster_path = os.path.join(dirname,varfolder[var],raster_name)
    if var != 'Y':  #For Area and Production we sum
        pdata.loc[idx[:,crop,tech],var]=pd.DataFrame(zonal_stats(vectors=shapefile['geometry'], raster=raster_path, all_touched=False, stats='sum'))['sum'].values
    else: #For Yield we average (or custom) ('max' stats is not used but an argument needs to be passed)
        pdata.loc[idx[:,crop,tech],var]=pd.DataFrame(zonal_stats(vectors=shapefile['geometry'], raster=raster_path, all_touched=False, stats='max', add_stats={'mymean':mymean}))['mymean'].values

#%% Export functions to csv and xlsx
def export_spam(SPAM,cropindex,export,shape):
    print('Exporting '+shape+' results')
    #Entire data to csv
    if export['csv files']==1:
        path=os.path.join(export['folder'],'SPAM_'+shape+'.csv') #export path
        SPAM.to_csv(path,sep=export['csvsepdec'][0],decimal=export['csvsepdec'][1],index=True)
    #Export to xlsx
    if export['xlsx files']==1:
        path=os.path.join(export['folder'],'SPAM_'+shape+'_summarized.xlsx') #export path
        writer = pd.ExcelWriter(path, engine='openpyxl')
    #INFOsheet - general information
        info.to_excel(writer, sheet_name='information')
    #Cropsheet - key indicators for every crop
        pcrop=pd.DataFrame(index=cropindex,dtype=float)
        if len(cropindex)==len(cropname.values()):
            pcrop['full name']=cropname.values()
        for tech in ntech:
            for var in nvar:
                colname=techname[tech]+' '+varname[var]+' '+new_var_unit[var]
                if var=='Y': #for yield weighted average(by harvested area) of all shapes is used
                    temp=pd.DataFrame(columns=['Y','H'],dtype=float)
                    temp['Y']=SPAM.loc[idx[:,:,tech],'Y']
                    temp['H']=SPAM.loc[idx[:,:,tech],'H']
                    temp['Y']=temp['Y']*temp['H']
                    temp=temp.sum(level='ncrop')
                    temp['Y']=temp['Y']/temp['H']
                    pcrop[colname]=temp['Y']
                else: # for production and area, sum of all shapes is used
                    pcrop[colname]=SPAM.loc[idx[:,:,tech],var].sum(level='ncrop')
        pcrop.to_excel(writer, sheet_name='crops')    
    #Shape sheet - key indicators for every shape unit
        pcatch=pd.DataFrame(index=nshapeid,dtype=float)
        for tech in ntech:
            for var in nvar:
                if var != 'Y': #Averaged yield through different crops does not make sense
                    colname=techname[tech]+' '+varname[var]+' '+new_var_unit[var]
                    pcatch[colname]=SPAM.loc[idx[:,:,tech],var].sum(level='nshapeid')
        pcatch['main irrigated crop']=[SPAM.loc[idx[c,:,'I'],'H'].idxmax()[1] for c in nshapeid]
        pcatch['main rainfed crop']=[SPAM.loc[idx[c,:,'R'],'H'].idxmax()[1] for c in nshapeid]
        pcatch.to_excel(writer, sheet_name='catchments')   
    #Other stats - 2D tables with crop and shape
        for tech in ntech:
            for var in nvar:
                sheet_name=varname[var].replace(' ','')+'_'+techname[tech].replace(' ','') #sheet name accept no spaces or special carcters
                SPAM.loc[idx[:,:,tech],var].reset_index(level='ntech',drop=True).unstack().to_excel(writer, sheet_name=sheet_name) 
        #Save
        writer.save()

#%% Reframe SPAM data according to user defined crop group
def reframe(SPAM):
    def groupcrops(crop): #Finds user defined cropgroup of a SPAM crop
        return cropgroup[cropgroup.eq(crop).any(1)].index[0]
    sp2=SPAM
    sp2.reset_index('ncrop', inplace=True) #put ncrop as column
    sp2['ncrop']=sp2['ncrop'].apply(groupcrops) #create a column with the crop group for each crop
    sp2.set_index('ncrop', append=True, inplace=True) #move the crop group to index
    sp2['Y']=sp2['Y']*sp2['H'] #prepare the weighted average yield (by harvested area)
    sp2=sp2.groupby(level=['nshapeid','ntech','ncrop']).sum() #group by and sum - will sum all 'rows' with same indexes (same crop group)
    sp2['Y']=sp2['Y']/sp2['H'] #weighted average yield wyield=sum(yield_c*A_c)/sum(A_c) where c iterates through crops belonging to a group
    sp2=sp2.swaplevel('ntech','ncrop') #place crops like in original dataset
    return sp2

#%%Compile all SPAM data rasters
print('Welcome to SPAM_data_reader')
#Download data if requiered
for var in nvar:
    download_SPAM(var) #download data if requiered by user AND specified data folder does not exist
#Go through shapes
for shape in nshape:
    print('Processing '+shape+' shapefile')
    #load shape
    shapepath = os.path.join(dirname,'Shapefiles',shapename[shape]+('.shp' if '.shp' not in shapename[shape] else ''))
    shapefile = gpd.read_file(shapepath)
    nshapeid=shapefile[shapeIDname[shape]].values
    #generate index and dataframe
    mindex=pd.MultiIndex.from_product([nshapeid,ncrop,ntech], names=['nshapeid', 'ncrop','ntech'])
    idx=pd.IndexSlice #slicer for dataframe
    SPAM=pd.DataFrame(index=mindex,columns=nvar,dtype=float)
    #Iterate through variables, crops and technologies
    for var in nvar:
        for crop in ncrop:
            for tech in ntech:
                load_raster_data(SPAM,crop,tech,var,shapefile)
    #Unit conversion
    for var in nvar:
        SPAM[var]=SPAM[var]*unit_conv_factor[var]
    #Exports
    #create export directory if does not exist
    if not os.path.exists(export['folder']): 
        os.makedirs(export['folder'])
    #export SPAM reformulated data
    export_spam(SPAM,ncrop,export,shape)
    #generate and export SPAM data according to user defined crop groups
    if export['group crops']==1:
        SPAM2=reframe(SPAM)
        export_spam(SPAM2,gcrop,export,shape+'_cropgroups')
