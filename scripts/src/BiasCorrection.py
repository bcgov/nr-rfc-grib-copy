import datetime
import os
import NRUtil.NRObjStoreUtil as NRObjStoreUtil
import pandas as pd
import GetGribConfig


def objstore_to_df(objpath,onprem=False, **kwargs):
    filename = objpath.split("/")[-1]
    filetype = filename.split(".")[-1]
    if onprem:
        local_path = objpath
    else:
        local_folder = 'raw_data/temp_file'
        if not os.path.exists(local_folder):
            os.makedirs(local_folder)
        local_path = os.path.join(local_folder,filename)
        ostore.get_object(local_path=local_path, file_path=objpath)
    match filetype:
        case 'csv':
            output = pd.read_csv(local_path, **kwargs)
        case 'parquet':
            output = pd.read_parquet(local_path, **kwargs)
        case 'txt':
            output = pd.read_csv(local_path, **kwargs)
    if not onprem:
        os.remove(local_path)

    return output

def df_to_objstore(df, objpath, onprem=False):
    filename = objpath.split("/")[-1]
    filetype = filename.split(".")[-1]
    if onprem:
        local_path = objpath
    else:
        local_folder = 'raw_data/temp_file'
        if not os.path.exists(local_folder):
            os.makedirs(local_folder)
        local_path = os.path.join(local_folder,filename)
    match filetype:
        case 'csv':
            df.to_csv(local_path)
        case 'parquet':
            df.to_parquet(local_path)
    if not onprem:
        ostore.put_object(local_path=local_path, ostore_path=objpath)
        os.remove(local_path)


def read_forecast(date, config_list, grib_path):
    date = datetime.datetime.now().replace(hour=0,minute=0,second=0,microsecond=0)
    #Listof grib configs used to download data:
    #Create datetime index (UTC) of datetimes for the forecast data:
    dt_ind = []
    for config in config_list:
        start_dt = date + datetime.timedelta(hours=int(config.model_number))
        for hr in config.iteratorlist:
            dt_ind.append(start_dt + datetime.timedelta(hours=hr))

    forecast_summary_basepath = grib_path
    forecast_summary_path = os.path.join(forecast_summary_basepath,date.strftime("%Y%m%d"))
    extract_code = config_list[0].extract_code
    key_list = list(config_list[0].extract_params_object.get_wgrib_params(extract_code))
    combined_data = None
    for key in key_list:
        objpath = f"{forecast_summary_path}/{key}_V2024.txt"
        raw_data = objstore_to_df(objpath=objpath, header=None)
        if not isinstance(combined_data, pd.DataFrame):
            combined_data = raw_data
        else:
            raw_data.columns = combined_data.columns[-1]+raw_data.columns+1
            combined_data = combined_data.join(raw_data)

    val_cols = combined_data.iloc[0].str.contains("val")
    combined_data = combined_data[val_cols.index[val_cols]]
    for column in combined_data:
        combined_data[column] = combined_data[column].str.extract('val=(.*(?=:lon))').astype(float)

    combined_data.index = dt_ind
    combined_data.index = combined_data.index - datetime.timedelta(hours=8)
    combined_data.columns = OBS["PP"].columns

    match extract_code:
        case "P":
            #precip units are kg/(m^2 s) = mm/s. Multiple by 3600s/hr * hrs to get mm
            dt = (combined_data.index.diff().seconds).to_list()
            dt[0] = dt[1]
            combined_data = combined_data.mul(dt, axis='index')
        case "T":
            #Convert Kelvin to Celsius:
            combined_data = combined_data.add(-273.15, axis='index')

    return combined_data



ostore = NRObjStoreUtil.ObjectStoreUtil()

ClimateObs_path = "models/data/climate_obs/ClimateDataOBS_2025.xlsm"

ostore.get_object(ClimateObs_path,ClimateObs_path)
ClimateObs = pd.read_excel(ClimateObs_path,sheet_name="ALL_DATA",index_col="DATE")

OBS = dict()
#List of variables in ClimateOBS:
var_list = ["TX","TN","PP"]
#Loop through each variable:
for var in var_list:
    OBS.update({var: ClimateObs.filter(regex=f'-{var}')})
    OBS[var].columns = OBS[var].columns.str.replace(f"-{var}","")

date = datetime.datetime.now()
grib_path = "cmc/summary_V2024"
config_list = [GetGribConfig.GribRegional_1(),GetGribConfig.GribGlobal_1()]
for_PC = read_forecast(date=date,config_list=config_list,grib_path=grib_path)
config_list = [GetGribConfig.GribRegional_2(),GetGribConfig.GribGlobal_2()]
for_TA = read_forecast(date=date,config_list=config_list,grib_path=grib_path)

#Precipitation computed 1am-1am in Excel, midnight to midnight here:
PC_daily = for_PC.groupby(pd.Grouper(axis=0, freq = 'D')).sum()
TX_daily = for_TA.groupby(pd.Grouper(axis=0, freq = 'D')).max()
#TMin computed between 10 am previous day and 7 am.
#Shift datetime index by 2 hours and compute Tmin between 00:00 and 09:00, equivalent to 10pm - 7am for the unshifted index:
for_TA.index = for_TA.index + pd.Timedelta('2h')
TN_daily = for_TA.between_time('00:00','9:00').groupby(pd.Grouper(axis=0, freq = 'D')).min()

All_daily = pd.concat([TX_daily,TN_daily,PC_daily],keys = ['TX','TN','PC'])

daily_summary_path = 'tmp/ClimateFOR/cmc/daily_forecast_summary/'
daily_summary_fpath = os.path.join(daily_summary_path,date.strftime("%Y%m%d.csv"))
All_daily.to_csv(daily_summary_fpath)

test_read = pd.read_csv(daily_summary_fpath, index_col=[0,1])


#Save daily forecast summaries as csv files
#Check dates with grib files available vs csv summaries. Produce csv summaries for for all dates with data available


#Tmax reg bias: Most recent 3 biases from forecast day 1/2/3
