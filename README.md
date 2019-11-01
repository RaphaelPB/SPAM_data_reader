# SPAM_data_reader
Read IFPRI and IIASA SPAM global data at the scale of user defined shapefiles and crop groups.
SPAM 2010 data is available at https://www.mapspam.info/data/. SPAM data contains global gridded data for area, yield and production for 42 crops and 4 production systems (irrigated, rainfed high input, rainfed low input and rainfed subsitence). 

## Requierments
 You need python with the following libraries: pandas, geopandas, rasterstats and numpy
 
## Usage
* Download this repository
* Place your desired shapefiles in the _Shapefiles_ folder - **the projection needs to be EPSG:4326 - WGS84** - default shapefiles of the Zambezi River Basin are in this repository for you to test the script
* Open the excel file _SPAM_metadata.xlsx_ - in the sheet _SHAPEFILES_ insert your shapefiles' name and the id to be used (replace default 'catchments' and 'countries' shapefiles)
* Run the _SPAM_data_reader.py_ script - the first time, the script needs to download SPAM data (see _Options_ to avoid this), hence it might take some time depending on your connection
* Go to the _Ouptputs_ folder and look at the output files

## Options
You can customize different options in the _SPAM_metadata.xlsx_ file, a complete description of the options is available within the excel file:
* _SHAPEFILES_: define which shapefiles should be used
* _SPAMvars_: define which variables should be compiled, convert units, data source and download options
* _SPAMcrops_: define which crops should be compiled
* _SPAMtechs_: define which technologies (/production system) should be compiled
* _GROUPcrops_: define your own crop groups to reframe SPAM data
* _EXPORT_: define the outputs and csv files options
* _INFO_: define an Info message to be attached in the output excel files

## Outputs
All outputs are found in the _Outputs_ folder (or user-defined folder):
* _SPAM_yourshapefile.csv_: csv file with the raw SPAM data at the level of your shapefile
* _SPAM_yourshapefile_cropgroups.csv_: same as previous for user defined crop groups instead of SPAM crops
* _SPAM_yourshapefile_summarized.xlsx_: excel file with the SPAM data at the level of your shapefile as 2D Tables, area and production are summed, yield is as a weighted average (by harvested area)
* _SPAM_yourshapefile_cropgroups_summarized.xlsx_: same as previous for user defined crop groups instead of SPAM crops

## Author
Raphael Payet-Burin (rapp@env.dtu.dk)
