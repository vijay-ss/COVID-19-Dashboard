"""DATA PRE-PROCESSING"""

import pandas as pd
import datetime as dt

# import raw daily files from JHU CSSE github
url_1 = 'https://raw.githubusercontent.com/datasets/covid-19/master/data/time-series-19-covid-combined.csv'
url_2 = 'https://raw.githubusercontent.com/datasets/covid-19/master/data/countries-aggregated.csv'
url_3 = 'https://raw.githubusercontent.com/datasets/covid-19/master/data/key-countries-pivoted.csv'
url_4 = 'https://raw.githubusercontent.com/datasets/covid-19/master/data/worldwide-aggregated.csv'

# import raw daily tweet file from GSU github
url_tweet = 'https://raw.githubusercontent.com/thepanacealab/covid19_twitter/master/dailies/' + \
            (dt.date.today() - dt.timedelta(days=2)).strftime('%Y-%m-%d') + '/' + \
            (dt.date.today() - dt.timedelta(days=2)).strftime('%Y-%m-%d') + \
            '_top1000trigrams.csv'

# convert to dataframes
time_series = pd.read_csv(url_1, index_col=0,parse_dates=[0]).reset_index()
countries = pd.read_csv(url_2, index_col=0,parse_dates=[0]).reset_index()
countries_pv = pd.read_csv(url_3, index_col=0,parse_dates=[0]).reset_index()
ww_agg = pd.read_csv(url_4, index_col=0,parse_dates=[0]).reset_index()
daily_twitter_phrases = pd.read_csv(url_tweet, index_col=0,parse_dates=[0]).reset_index()

# convert date objects to pandas datetime
countries['Date'] = pd.to_datetime(countries['Date'])
countries_pv['Date'] = pd.to_datetime(countries_pv['Date'])
time_series['Date'] = pd.to_datetime(time_series['Date'])
ww_agg['Date'] = pd.to_datetime(ww_agg['Date'])

# A df of all countries, incl co-ordinates for map
# A cleaner country df, without province/state but includes lat and long for mapping purposes
countries_df = time_series.copy()
countries_df.rename(columns={"Country/Region": "Country"}, inplace=True)
countries_df.fillna(0, inplace=True)
countries_df.drop(['Province/State'], axis=1, inplace=True)
countries_df['Active'] = countries_df['Confirmed'] - countries_df['Recovered']


countries_df = countries_df.groupby(['Date', 'Country'], as_index=False).agg({'Lat': 'mean',
                                                                       'Long': 'mean',
                                                                       'Confirmed': 'sum',
                                                                       'Deaths': 'sum',
                                                                       'Recovered': 'sum',
                                                                       'Active':'sum'
                                                                     })

# update country centroid which are spread due to provinces/colonies
countries_df.loc[countries_df['Country'] == 'US', 'Lat'] = 39.810489
countries_df.loc[countries_df['Country'] == 'US', 'Long'] = -98.555759

countries_df.loc[countries_df['Country'] == 'France', 'Lat'] = 46.2276
countries_df.loc[countries_df['Country'] == 'France', 'Long'] = 2.2137

countries_df.loc[countries_df['Country'] == 'United Kingdom', 'Lat'] = 55.3781
countries_df.loc[countries_df['Country'] == 'United Kingdom', 'Long'] = -3.4360

countries_df.loc[countries_df['Country'] == 'Denmark', 'Lat'] = 56.2639
countries_df.loc[countries_df['Country'] == 'Denmark', 'Long'] = 9.5018

countries_df.loc[countries_df['Country'] == 'Netherlands', 'Lat'] = 52.1326
countries_df.loc[countries_df['Country'] == 'Netherlands', 'Long'] = 5.2913

countries_df.loc[countries_df['Country'] == 'Canada', 'Lat'] = 59.050000
countries_df.loc[countries_df['Country'] == 'Canada', 'Long'] = -112.833333

countries_df['Active'] = countries_df['Confirmed'] - countries_df['Recovered'] - countries_df['Deaths']

# Description for map
countries_df['Description'] = countries_df['Country'] + '<br>' \
+ 'Confirmed: ' + countries_df['Confirmed'].astype(int).map('{:,.0f}'.format) + '<br>' \
+ 'Deaths: ' + countries_df['Deaths'].astype(int).map('{:,.0f}'.format) + '<br>' \
+ 'Recovered: ' + countries_df['Recovered'].astype(int).map('{:,.0f}'.format) + '<br>' \
+ 'Active: ' + countries_df['Active'].astype(int).map('{:,.0f}'.format)
#countries_df = countries_df.assign(logCumConf = np.where(countries_df['Confirmed'] > 0, np.log(countries_df['Confirmed']) / np.log(2), 0))

# Total daily counts grouped by country/overall
national_daily_count = countries_df.groupby(['Date','Country'])['Confirmed','Deaths','Recovered','Active'].sum().reset_index()
global_daily_count = countries_df.groupby(['Date'])['Confirmed','Deaths','Recovered','Active'].sum().reset_index()
global_melt = global_daily_count.melt(id_vars=['Date'],
                                      value_vars=['Recovered','Deaths','Active','Confirmed'],
                                      var_name='Type',value_name='Count'
                                      )

# Data for Canada - by province
canada_df = time_series.copy()
canada_df = canada_df[canada_df['Country/Region'] == 'Canada'].reset_index(drop=True)
canada_df.rename(columns={"Country/Region": "Country"}, inplace=True)
canada_df.fillna(0, inplace=True)
canada_df['Active'] = canada_df['Confirmed'] - canada_df['Recovered'] - canada_df['Deaths']

# Canada day over day
p = canada_df.groupby(['Date','Province/State'])['Confirmed'].sum().reset_index()
p['Diff'] = p.groupby('Province/State')['Confirmed'].diff(periods=1)

# Twitter phrase: rename columns
daily_twitter_phrases.rename(columns={'gram':'Phrase', 'counts':'Frequency'}, inplace=True)
daily_twitter_phrases['Rank'] = daily_twitter_phrases.index + 1
daily_twitter_phrases = daily_twitter_phrases[['Rank', 'Phrase', 'Frequency']]

#export to csv files
countries_df.to_csv('data/countries.csv', index=False)
global_daily_count.to_csv('data/global_daily_count.csv', index=False)
global_melt.to_csv('data/global_melt.csv', index=False)
canada_df.to_csv('data/canada.csv', index=False)
p.to_csv('data/canada_by_province.csv', index=False)
daily_twitter_phrases.to_csv('data/twitter_phrases.csv', index=False)