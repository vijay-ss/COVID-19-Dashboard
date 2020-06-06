"""MAIN APP"""

import flask
import os
import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from datetime import date, timedelta
#from wordcloud import WordCloud, STOPWORDS
#import matplotlib.pyplot as plt
#import base64

"""GATHER INPUT FILES"""

#import twitter_web_scrape
#df_tweets = pd.read_csv(r'data/covid_tweets.csv')
url = 'https://raw.githubusercontent.com/vijay-ss/COVID-19-Dashboard/master/data/covid_tweets.csv'
df_tweets = pd.read_csv(url, index_col=0, parse_dates=[0]).reset_index()


import ETL
countries_df = pd.read_csv(r'data/countries.csv')
global_daily_count = pd.read_csv(r'data/global_daily_count.csv')
global_melt = pd.read_csv(r'data/global_melt.csv')
canada_df = pd.read_csv(r'data/canada.csv')
canada_province = pd.read_csv(r'data/canada_by_province.csv')
daily_twitter_phrases = pd.read_csv(r'data/twitter_phrases.csv')

### Data Pre-processing ###

# Twitter EDA #todo move to separate file when twitterscraper is functioning
df_tweets['Category'] = df_tweets['compound'].apply(lambda x: 'Positive'if x > 0 else \
    ('Negative' if x < 0 else 'Neutral'))

# convert Date object to Datetime
countries_df['Date'] = pd.to_datetime(countries_df['Date'])
global_daily_count['Date'] = pd.to_datetime(global_daily_count['Date'])
global_melt['Date'] = pd.to_datetime(global_melt['Date'])
canada_df['Date'] = pd.to_datetime(canada_df['Date'])
canada_province['Date'] = pd.to_datetime(canada_province['Date'])

# Canada day over day
canada_province['Diff'] = canada_province.groupby('Province/State')['Confirmed'].diff(periods=1)

"""CREATE PLOTS"""

fig_area = px.area(global_melt
                   , x="Date"
                   , y="Count"
                   , color='Type'
                   # ,height=600
                   # ,width=900
                   , title='Worldwide Cases by Type'
                   , template='plotly_dark'
                   )
fig_area.update_layout(xaxis_rangeslider_visible=True)

# Time Series
fig_timeseries = px.line(x=countries_df['Date'].dt.strftime('%Y-%m-%d'),
                         y=countries_df["Confirmed"],
                         color=countries_df["Country"],
                         hover_name=countries_df["Country"],
                         line_shape="spline",
                         render_mode="svg",
                         template='plotly_dark'
                         )
fig_timeseries.update_layout(title="Timeline of Confirmed Cases",
                             xaxis_title="Date",
                             yaxis_title="Confirmed Cases",
                             legend_title="Country")

# Data input for Mapbox plot
formatted_gdf = countries_df.groupby(['Date', 'Country', 'Description', 'Lat', 'Long'])['Confirmed'].max().reset_index()
formatted_gdf['Date'] = formatted_gdf['Date'].dt.strftime('%m/%d/%Y')

# Mapbox
fig_mapbox = px.scatter_mapbox(
    mapbox_style='carto-darkmatter',
    title='Global Outbreak Map - Hover for Detailed Information',
    lat=formatted_gdf['Lat'],
    lon=formatted_gdf['Long'],
    hover_name=formatted_gdf['Description'],
    size=formatted_gdf['Confirmed'].pow(0.3),  # todo logarithmic scale
    range_color=[0, 4000],
    opacity=0.6,
    size_max=30,
    zoom=1.2,
    animation_frame=countries_df['Date'].astype(str),
    # center=go.layout.mapbox.Center(lat=14,lon=21),
    template='plotly_dark',
    color=formatted_gdf['Confirmed'],
    color_continuous_scale='portland',
    # color_discrete_sequence=px.colors.qualitative.Light24,
)
fig_mapbox.update_layout(autosize=True, coloraxis_showscale=False)

# Ontario Map
fig_can = px.line(x=canada_df['Date'],
                  y=canada_df["Confirmed"],
                  color=canada_df['Province/State'],
                  hover_name=canada_df['Province/State'],
                  line_shape="spline",
                  render_mode="svg",
                  template='plotly_dark'
                  )
fig_can.update_layout(
    title="Timeline of Confirmed Cases - by Province",
    xaxis_title="Date",
    yaxis_title="Count",
    legend_title="Province"
)

# Ontario day over day
fig_dod = px.line(x=canada_province['Date'],
                  y=canada_province["Diff"],
                  color=canada_province['Province/State'],
                  hover_name=canada_province['Province/State'],
                  line_shape="linear",
                  render_mode="svg",
                  template='plotly_dark'
                  )
fig_dod.update_layout(
    title="Day over day - by Province",
    xaxis_title="Date",
    yaxis_title="Daily Delta",
    legend_title="Province"
)

# Twitter sentiment pie chart
fig_pie = go.Figure(data=[go.Pie(
    labels = df_tweets['Category'].unique(),
    values = df_tweets['Category'].value_counts(),
    hole=.3,
    pull=[0,0,0.1]
)])
fig_pie.update_layout(
title='Sentiment Mix of Covid-19 Related Tweets',
    template='plotly_dark'
)

# Twitter phrase
fig_phrase = go.Figure(data=[go.Table(columnwidth=[20, 60, 40],
                                      header=dict(values=list(daily_twitter_phrases.columns),
                                                  fill_color='rgb(29,161,242)',

                                                  font=dict(color='white', size=14),
                                                  align='left'),
                                      cells=dict(values=[daily_twitter_phrases.Rank, daily_twitter_phrases.Phrase,
                                                         daily_twitter_phrases.Frequency],
                                                 fill_color='rgb(245,248,250)',
                                                 font=dict(color='black', size=12),
                                                 align='left'))
                             ])
fig_phrase.update_layout(
    title='Most Common Tweet Contents from ' + (date.today() - timedelta(days=1)).strftime('%d %b, %Y'),
    template='plotly_dark')

# Twitter Word Cloud
# text = df_tweets.Tweet.values
#
# wordcloud = WordCloud(
# width = 400,
# height = 500,
# background_color = 'black',
# #mask = logo,
# stopwords = STOPWORDS).generate(str(text))
#
# fig = plt.figure(
# figsize = (4,3),
# facecolor = 'k',
# edgecolor = 'k')
# plt.imshow(wordcloud, interpolation = 'bilinear')
# plt.axis('off')
# plt.tight_layout(pad=0)
# plt.savefig('assets/twitter_wc.png')
#
# # Word Cloud image
# wc_img = 'assets/twitter_wc.png'
# encoded = base64.b64encode(open(wc_img, 'rb').read())

default_layout = {
    'autosize': True,
    'xaxis': {'title': None},
    'yaxis': {'title': None},
    'margin': {'l': 40, 'r': 20, 't': 40, 'b': 10},
    'paper_bgcolor': '#303030',
    'plot_bgcolor': '#303030',
    'hovermode': 'x',
}

# base color scheme
dash_colors = {
    'background': '#111111',
    'text': '#BEBEBE',
    'grid': '#333333',
    'red': '#BF0000',
    'red_bright': '#d7191c',
    'blue': '#466fc2',
    'green': '#5bc246',
    'orange': '5A9E6F'
}

# base margin style for each page
page_margin = {'marginLeft': '1.5%', 'marginRight': '1.5%', 'marginBottom': '.5%', 'marginTop': '.5%'}


def ticker_color(tick_value):
    if tick_value > 0:
        return dash_colors['red']
    else:
        return dash_colors['green']


# todo update function to include colors for all metric types

# Latest count per country for number plates
global_total = global_daily_count.join(
    global_daily_count[['Confirmed', 'Deaths', 'Recovered', 'Active']].pct_change(fill_method='ffill').add_suffix(
        '_pct'))
global_total = global_total[global_daily_count['Date'] == global_total['Date'].max()]
delta = global_daily_count[global_daily_count['Date'] == global_daily_count['Date'].max() - timedelta(days=1)]

'''BEGIN DASH APP'''

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.SLATE])
server = app.server
app.title = 'Covid-19 Tracker'

@server.route('/favicon.ico')
def favicon():
    return flask.send_from_directory(os.path.join(server.root_path, 'assets'), 'favicon.ico')

app.layout = html.Div(children=[
    html.H1(children='Covid-19 Interactive Tracker',
            style={'textAlign': 'center'}),

    html.Div(children='Data last updated: ' + global_daily_count['Date'].max().strftime('%Y-%m-%d') +
                      ' (Maintained by John Hopkins University)',
             style={'textAlign': 'center'}),

    #     html.Div([
    #         dbc.Tabs(children=[
    #             dbc.Tab(label="Tab 1", tab_id="tab-1"),
    #             dbc.Tab(label="Tab 2", tab_id="tab-2")
    #         ])
    #     ]
    # ),

    html.Div([
        dcc.Location(id='url', refresh=False),
        dbc.Button(dcc.Link('Global', href='/page-1'), id="global-button", color='primary', className="mr-1"),
        dbc.Button(dcc.Link('World News', href='/page-2'), id="news-button", color='primary', className="mr-1"),
        dbc.Button(dcc.Link('Ranking', href='/page-3'), id="top-button", color='primary', className="mr-1"),
        dbc.Button(dcc.Link('Canada', href='/page-4'), id="canada-button", color='primary', className="mr-1"),
        html.Div(id='page-content'),
        # html.Span(id='button-container')
    ], style={'textAlign': 'center', 'width': '100%', 'float': 'center', 'display': 'inline-block',
              'marginTop': '.5%'}),
]  # ,style={'background-image':'url("assets/background_image.png")'}
)

# html.Div([
#     dcc.Location(id='url', refresh=False),
#     #dcc.Link('Global',href='/page-1'),
#     #dcc.Link('Top',href='/page-2'),
#     dcc.Link('Canada',href='/page-3'),
#     html.Div(id='page-content'),
# ],style={'textAlign':'center','width':'100%','float':'center','display':'inline-block'})])

number_plates = html.Div(id='number-plate',
                         style={'marginLeft': '1.5%', 'marginRight': '1.5%', 'marginBottom': '.5%', 'marginTop': '.5%'},
                         children=[
                             html.Div(id='conf-ind',
                                      style={'width': '24.4%', 'marginRight': '.8%', 'display': 'inline-block',
                                             'padding': '1rem',
                                             'backgroundColor': dash_colors['background']},
                                      children=[html.P(style={'textAlign': 'center',
                                                              'color': dash_colors['red_bright'],
                                                              'fontSize': 20},
                                                       children='Confirmed Cases'),
                                                html.H3(style={'textAlign': 'center',
                                                               'fontWeight': 'bold', 'color': dash_colors['red_bright'],
                                                               'fontSize': 50},
                                                        children='{:,.0f}'.format(int(global_total['Confirmed']))),
                                                html.P(style={'textAlign': 'center',
                                                              'color': ticker_color(
                                                                  int(global_total['Confirmed']) - int(
                                                                      delta['Confirmed'])),
                                                              'fontSize': 20},
                                                       children='{0:+,d}'.format(
                                                           int(global_total['Confirmed']) - int(delta['Confirmed']))
                                                                + ' (' + global_total['Confirmed_pct'].map(
                                                           '{:+.2%}'.format) + ')'
                                                       )
                                                ],
                                      className='four columns'),

                             html.Div(id='death-ind',
                                      style={'width': '24.4%', 'marginRight': '.8%', 'display': 'inline-block',
                                             'padding': '1rem',
                                             'backgroundColor': dash_colors['background']},
                                      children=[html.P(style={'textAlign': 'center',
                                                              'color': dash_colors['red_bright'],
                                                              'fontSize': 20},
                                                       children='Deaths'),
                                                html.H3(style={'textAlign': 'center',
                                                               'fontWeight': 'bold', 'color': dash_colors['red_bright'],
                                                               'fontSize': 50},
                                                        children='{:,.0f}'.format(int(global_total['Deaths']))),
                                                html.P(style={'textAlign': 'center',
                                                              'color': dash_colors['red_bright'], 'fontSize': 20},
                                                       children='{0:+,d}'.format(
                                                           int(global_total['Deaths']) - int(delta['Deaths']))
                                                                + ' (' + global_total['Deaths_pct'].map(
                                                           '{:+.2%}'.format) + ')'
                                                       )
                                                ],
                                      className='four columns'),

                             html.Div(id='rec-ind',
                                      style={'width': '24.4%', 'marginRight': '.8%', 'display': 'inline-block',
                                             'padding': '1rem',
                                             'backgroundColor': dash_colors['background']},
                                      children=[html.P(style={'textAlign': 'center',
                                                              'color': dash_colors['red_bright'],
                                                              'fontSize': 20},
                                                       children='Recoveries'),
                                                html.H3(style={'textAlign': 'center',
                                                               'fontWeight': 'bold', 'color': dash_colors['red_bright'],
                                                               'fontSize': 50},
                                                        children='{:,.0f}'.format(int(global_total['Recovered']))),
                                                html.P(style={'textAlign': 'center',
                                                              'color': dash_colors['green'], 'fontSize': 20},
                                                       children='{0:+,d}'.format(
                                                           int(global_total['Recovered']) - int(delta['Recovered']))
                                                                + ' (' + global_total['Recovered_pct'].map(
                                                           '{:+.2%}'.format) + ')'
                                                       )
                                                ],
                                      className='four columns'),

                             html.Div(id='active-ind',
                                      style={'width': '24.4%', 'display': 'inline-block', 'padding': '1rem',
                                             'backgroundColor': dash_colors['background']},
                                      children=[html.P(style={'textAlign': 'center',
                                                              'color': dash_colors['red_bright'],
                                                              'fontSize': 20},
                                                       children='Active Cases'),
                                                html.H3(style={'textAlign': 'center',
                                                               'fontWeight': 'bold', 'color': dash_colors['red_bright'],
                                                               'fontSize': 50},
                                                        children='{:,.0f}'.format(int(global_total['Active']))),
                                                html.P(style={'textAlign': 'center',
                                                              'color': dash_colors['red_bright'], 'fontSize': 20},
                                                       children='{0:+,d}'.format(
                                                           int(global_total['Active']) - int(delta['Active']))
                                                                + ' (' + global_total['Active_pct'].map(
                                                           '{:+.2%}'.format) + ')'
                                                       )
                                                ],
                                      className='four columns')

                         ], className='row'
                         )

page_1_layout = html.Div([
    html.Div(id='page-1'),
    html.Div(id='global-trending',
             style={'marginLeft': '1.5%', 'marginRight': '1.5%', 'marginBottom': '.5%', 'marginTop': '.5%'},
             children=[
                 html.Div(dcc.Graph(id='global-melt', figure=fig_area),
                          style={'width': '49.6%', 'display': 'inline-block', 'marginRight': '.8%'}),
                 html.Div(dcc.Graph(id='time-series', figure=fig_timeseries),
                          style={'width': '49.6%', 'display': 'inline-block'})
             ], className='row'),

    html.Div(id='world-map',
             style={'marginLeft': '1.5%', 'marginRight': '1.5%', 'marginBottom': '.5%', 'marginTop': '.5%'},
             children=[html.Div(dcc.Graph(id='global-outbreak', figure=fig_mapbox, style={'height': 800}))
                       ])
])

df_ranking = countries_df[countries_df['Date'] == countries_df['Date'].max()].groupby(['Country'])[
    'Confirmed', 'Deaths', 'Recovered', 'Active'].sum().sort_values('Confirmed', ascending=False).reset_index()
df_ranking['Rank'] = df_ranking.index + 1
df_ranking = df_ranking[['Rank', 'Country', 'Confirmed', 'Deaths', 'Recovered', 'Active']]
df_ranking[['Confirmed', 'Deaths', 'Recovered', 'Active']] = df_ranking[
    ['Confirmed', 'Deaths', 'Recovered', 'Active']].astype(int).applymap('{:,}'.format)

page_3_layout = html.Div([
    html.Div(id='page-3'),
    html.Div(html.H2('Global Ranking - Top 20'),
             style={'backgroundColor': dash_colors['background'], 'padding': '.5rem'}),
    html.Div(dbc.Table.from_dataframe(df_ranking.head(20), striped=True, bordered=True, hover=True),
             style={'marginTop': '.5%'})
], style={'marginLeft': '1.5%', 'marginRight': '1.5%', 'marginBottom': '.5%', 'marginTop': '.5%'})

page_4_layout = html.Div([
    html.Div(id='page-4'),
    html.Div(id='canada-trending',
             style={'marginLeft': '1.5%', 'marginRight': '1.5%', 'marginBottom': '.5%', 'marginTop': '.5%'},
             children=[
                 html.Div(dcc.Graph(id='canada', figure=fig_can),
                          style={'width': '49.6%', 'display': 'inline-block', 'marginRight': '.8%'}),
                 html.Div(dcc.Graph(id='dod', figure=fig_dod),
                          style={'width': '49.6%', 'display': 'inline-block'})
             ], className='row')
])

# https://www.cbc.ca/cmlink/rss-world
# todo figure out how to scale the twitter table

newsfeed_div_style = {
    "width": "24.4%",
    'height': '53rem',
    "padding": "1rem",
    "background-color": dash_colors['background'],
    'display': 'block',
}

twitter_div_style = {
    "width": "74.8%",
    'height': '22rem',
    'marginLeft': '.8%',
    #"padding": "1rem",
    #"background-color": dash_colors['background'],
}

news_feed_layout = html.Div(id='news-page', style=page_margin, children=[
    html.Div(id='rss-feed',
             children=[
                 html.H2('News Feed'),
                 html.Div(html.Iframe(id='rss',
                                      src='https://www.rssdog.com/index.php?url=https%3A%2F%2Fwww.aljazeera.com%2Fxml%2Frss%2Fall.xml&mode=html&showonly=&maxitems=0&showdescs=1&desctrim=0&descmax=0&tabwidth=100%25&showdate=1&linktarget=_blank&bordercol=transparent&headbgcol=transparent&headtxtcol=%23ffffff&titlebgcol=transparent&titletxtcol=%23ffffff&itembgcol=transparent&itemtxtcol=%23ffffff&ctl=0',
                                      #src='https://www.rssdog.com/index.php?url=https%3A%2F%2Fwww.cbc.ca%2Fcmlink%2Frss-world&mode=html&showonly=&maxitems=0&showdescs=1&desctrim=0&descmax=0&tabwidth=100%25&showdate=1&linktarget=_blank&bordercol=transparent&headbgcol=transparent&headtxtcol=%23ffffff&titlebgcol=transparent&titletxtcol=%23ffffff&itembgcol=transparent&itemtxtcol=%23ffffff&ctl=0',
                                      style={'width': '100%', 'height': '49rem', 'border': 'none', 'padding': '.5rem'}),
                          )
             ], style=newsfeed_div_style),
    html.Div(id='twitter',
             children=[
                 html.Div(html.H2('Related Tweets'),
                          style={'backgroundColor': dash_colors['background'], 'padding': '.5rem'}),
                 html.Div(id='tweets',
                          children=[
                              dbc.Table.from_dataframe(df_tweets[['Handle', 'Date', 'Tweet']].sample(frac=1),
                                                       striped=True,
                                                       bordered=True, hover=True, className='table-info', size='sm')]
                          , style={'height': '15.5rem', 'overflowY': 'auto', 'padding': '1rem',
                                   "background-color": dash_colors['background']}),

                 html.Div(html.P(' '), style={'backgroundColor': dash_colors['background'], 'padding': '.5rem'}),
                 html.Div(html.H2('Sentiment Analysis'),
                          style={'backgroundColor': dash_colors['background'], 'marginTop': '1%'}),
                 html.Div(id='sentiment', children=[
                     html.Div(dcc.Graph(id='twitter-pie', figure=fig_pie),
                              style={'display': 'inline-block', 'width': '50%', 'marginLeft': '1%'}),
                     html.Div(dcc.Graph(id='twitter-phrases', figure=fig_phrase),
                              style={'display': 'inline-block', 'width': '47%', 'marginLeft': '1%'})

                 ], className='row')
             ], style=twitter_div_style)
], className='row')

# html.Div(html.Img(id='word-cloud', src='data:image/png;base64,{}'.format(encoded.decode())),
#          style={'display': 'inline-block', 'width': '30%'})


# Display correct page based on user selection
@app.callback(Output('page-content', 'children'),
              [Input('url', 'pathname')])
def display_page(pathname):
    if pathname == '/page-1':
        return number_plates, page_1_layout
    elif pathname == '/page-2':
        return number_plates, news_feed_layout
    elif pathname == '/page-3':
        return number_plates, page_3_layout
    elif pathname == '/page-4':
        return number_plates, page_4_layout
    else:
        return number_plates, page_1_layout


if __name__ == '__main__':
    app.run_server()
