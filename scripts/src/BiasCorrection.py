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

def split_duplicates(input):
    duplicate_bool = input.index.duplicated()
    output1 = input.loc[~duplicate_bool,:]
    #output2 = input.loc[duplicate_bool,:]
    return output1

#Regional forecasts getting overwritten by global data intended for Tmin correction?
def read_forecast(date, config_list, grib_path):
    date = date.replace(hour=0,minute=0,second=0,microsecond=0)
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
        combined_data[column] = combined_data[column].str.extract('val=(.*)')[0].str.split(":",expand=True)[0].astype(float)

    combined_data.index = dt_ind
    combined_data.index = combined_data.index - datetime.timedelta(hours=8)
    combined_data.columns = All_obs.columns

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

def compute_mean_bias(forecast_data, obs_data, var, forecast_days, days_back):
    forecast = forecast_data.loc[(slice(None),var),:]
    obs = obs_data.loc[(var),:]
    for_ind = forecast.index
    date = max(for_ind.levels[0])
    forecast.index = forecast.index.set_levels(pd.to_datetime(for_ind.levels[-1]),level=-1)
    bias = obs.sub(forecast,level=2)
    bias = bias.dropna(how='all')
    bias_index = bias.index.to_frame()
    bias_index['ForecastDay'] = (bias_index.loc[:,2]-bias_index.loc[:,0]).dt.days
    bias_index['N'] = (date - bias_index.loc[:,0]).dt.days - bias_index['ForecastDay']
    ind = (bias_index['ForecastDay'].isin(forecast_days)) & (bias_index['N'].isin(days_back))
    mean_bias = bias.loc[ind,:].mean()

    return mean_bias


ostore = NRObjStoreUtil.ObjectStoreUtil()

ClimateObs_path = "models/data/climate_obs/ClimateDataOBS_2025.xlsm"

ostore.get_object(ClimateObs_path,ClimateObs_path)
ClimateObs = pd.read_excel(ClimateObs_path,sheet_name="ALL_DATA",index_col="DATE")

OBS = list()
#List of variables in ClimateOBS:
var_list = ["TX","TN","PP"]
#Loop through each variable:
for var in var_list:
    OBS.append(ClimateObs.filter(regex=f'-{var}').rename(columns = lambda x: x[0:3]))
All_obs = pd.concat(OBS,keys = var_list)
del OBS[:]

date = datetime.datetime.now()

grib_path = "cmc/summary_V2024"
daily_summary_path = 'ClimateFOR/cmc/daily_forecast_summary/'
obj_summary_list = ostore.list_objects(daily_summary_path ,return_file_names_only=True)
summary_dates = [datetime.datetime.strptime(os.path.splitext(os.path.basename(obj))[0], '%Y%m%d') for obj in obj_summary_list]
#days_back = min(abs((max(summary_dates) - date).days),6)
days_back = 10
config_list_P = [GetGribConfig.GribRegional_1(),GetGribConfig.GribGlobal_1()]
config_list_T = [GetGribConfig.GribRegional_2(),GetGribConfig.GribGlobal_2()]
datelist = pd.date_range(end=date, periods=days_back).tolist()
for dt in datelist:
    for_PC = read_forecast(date=dt,config_list=config_list_P,grib_path=grib_path)
    for_TA = read_forecast(date=dt,config_list=config_list_T,grib_path=grib_path)
    for_TA = split_duplicates(for_TA)
    #Precipitation computed 1am-1am in Excel, midnight to midnight here:
    PC_daily = for_PC.groupby(pd.Grouper(axis=0, freq = 'D')).sum()
    TX_daily = for_TA.groupby(pd.Grouper(axis=0, freq = 'D')).max()
    #TMin computed between 10 am previous day and 7 am.
    #Shift datetime index by 2 hours and compute Tmin between 00:00 and 09:00, equivalent to 10pm - 7am for the unshifted index:
    for_TA.index = for_TA.index + pd.Timedelta('2h')
    TN_daily = for_TA.between_time('00:00','9:00').groupby(pd.Grouper(axis=0, freq = 'D')).min()
    All_daily = pd.concat([TX_daily,TN_daily,PC_daily],keys = ['TX','TN','PC'])
    daily_summary_fpath = os.path.join(daily_summary_path,dt.strftime("%Y%m%d.csv"))
    df_to_objstore(All_daily,daily_summary_fpath)

forecast_list = list()
date = date.replace(hour=0,minute=0,second=0,microsecond=0)
datelist = pd.date_range(end=date, periods=6)
for dt in datelist:
    daily_summary_fpath = os.path.join(daily_summary_path,dt.strftime("%Y%m%d.csv"))
    forecast_list.append(objstore_to_df(daily_summary_fpath, index_col=[0,1]))
forecast_data = pd.concat(forecast_list,keys = datelist)
del forecast_list[:]

var = "TX"
TX_bias = compute_mean_bias(forecast_data,All_obs,'TX',range(0,3),range(1,4))
#Current day Tmin bias gets4x weight in bias calculation
TN_bias = compute_mean_bias(forecast_data,All_obs,'TN',range(0,4),range(0,3))
#forecast_TX_corr = forecast_TX.loc[date].add(mean_bias_TX)

#Obs has datetime index, forecast has regular index, causing issues?
test_TX = forecast_TX.loc[slice(datelist[0]),:]
test_TX = test_TX.droplevel(0)

#Save daily forecast summaries as csv files
#Check dates with grib files available vs csv summaries. Produce csv summaries for for all dates with data available


#Tmax reg bias: Most recent 3 biases from forecast day 1/2/3
