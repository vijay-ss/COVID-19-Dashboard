import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
#import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from datetime import date, timedelta

"""GATHER INPUT FILES"""
import twitter_web_scrape
df_tweets = pd.read_csv(r'data/covid_tweets.csv')

import ETL
countries_df = pd.read_csv(r'data/countries.csv')
global_daily_count = pd.read_csv(r'data/global_daily_count.csv')
global_melt = pd.read_csv(r'data/global_melt.csv')
canada_df = pd.read_csv(r'data/canada.csv')
canada_province = pd.read_csv(r'data/canada_by_province.csv')


### Data Pre-processing ###

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
              ,x="Date"
              ,y="Count"
              ,color='Type'
              #,height=600
              #,width=900
              ,title='Worldwide Cases by Type'
              ,template='plotly_dark'
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
fig_timeseries.update_layout(title = "Timeline of Confirmed Cases",
    xaxis_title = "Date",
    yaxis_title = "Confirmed Cases",
    legend_title = "Country")

# Data input for Mapbox plot
formatted_gdf = countries_df.groupby(['Date','Country','Description','Lat','Long'])['Confirmed'].max().reset_index()
formatted_gdf['Date'] = formatted_gdf['Date'].dt.strftime('%m/%d/%Y')

# Mapbox
fig_mapbox = px.scatter_mapbox(
    mapbox_style='carto-darkmatter',
    title='Global Outbreak Map - Hover for Detailed Information',
    lat=formatted_gdf['Lat'],
    lon=formatted_gdf['Long'],
    hover_name=formatted_gdf['Description'],
    size=formatted_gdf['Confirmed'].pow(0.3), #todo logarithmic scale
    range_color=[0, 4000],
    opacity=0.6,
    size_max=30,
    zoom=1.2,
    animation_frame=countries_df['Date'].astype(str),
    # center=go.layout.mapbox.Center(lat=14,lon=21),
    template='plotly_dark',
    color=formatted_gdf['Confirmed'],
    color_continuous_scale='portland',
    #color_discrete_sequence=px.colors.qualitative.Light24,
    )
fig_mapbox.update_layout(autosize=True,coloraxis_showscale=False)

#Ontario Map
fig_can = px.line(x=canada_df['Date'],
        y=canada_df["Confirmed"],
        color=canada_df['Province/State'],
        hover_name=canada_df['Province/State'],
        line_shape="spline",
        render_mode="svg",
        template='plotly_dark'
)
fig_can.update_layout(
    title = "Timeline of Confirmed Cases - by Province",
    xaxis_title = "Date",
    yaxis_title = "Count",
    legend_title = "Province"
)

#Ontario day over day
fig_dod = px.line(x=canada_province['Date'],
        y=canada_province["Diff"],
        color=canada_province['Province/State'],
        hover_name=canada_province['Province/State'],
        line_shape="linear",
        render_mode="svg",
        template='plotly_dark'
)
fig_dod.update_layout(
    title = "Day over day - by Province",
    xaxis_title = "Date",
    yaxis_title = "Daily Delta",
    legend_title = "Province"
)

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
    'orange':'5A9E6F'
}

def ticker_color(tick_value):
    if tick_value > 0:
        return dash_colors['red']
    else:
        return dash_colors['green']
# todo update function to include colors for all metric types

# Latest count per country for number plates
global_total = global_daily_count.join(global_daily_count[['Confirmed','Deaths','Recovered','Active']].pct_change(fill_method='ffill').add_suffix('_pct'))
global_total = global_total[global_daily_count['Date'] == global_total['Date'].max()]
delta = global_daily_count[global_daily_count['Date'] == global_daily_count['Date'].max() - timedelta(days=1)]

'''BEGIN DASH APP'''

external_stylesheets = ['https://codepen.io/unicorndy/pen/GRJXrvP.css','https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css']

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.SLATE]
                )
# https://dash-bootstrap-components.opensource.faculty.ai/docs/themes/
server = app.server
app.title = 'nCov-19'

app.layout = html.Div(children=[
    html.H1(children='Covid-19 Interactive Tracker',
            style={'textAlign':'center'}),

    html.Div(children='Data last updated: ' + global_daily_count['Date'].max().strftime('%Y-%m-%d') +
                      ' (Maintained by John Hopkins University)',
             style={'textAlign':'center'}),

#     html.Div([
#         dbc.Tabs(children=[
#             dbc.Tab(label="Tab 1", tab_id="tab-1"),
#             dbc.Tab(label="Tab 2", tab_id="tab-2")
#         ])
#     ]
# ),

    html.Div([
        dcc.Location(id='url', refresh=False),
        dbc.Button(dcc.Link('Global',href='/page-1'), id="global-button", color='primary', className="mr-1"),
        dbc.Button(dcc.Link('World News', href='/page-2'), id="news-button", color='primary', className="mr-1"),
        dbc.Button(dcc.Link('Ranking',href='/page-3'), id="top-button", color='primary', className="mr-1"),
        dbc.Button(dcc.Link('Canada',href='/page-4'), id="canada-button", color='primary', className="mr-1"),
        html.Div(id='page-content'),
        #html.Span(id='button-container')
    ],style={'textAlign':'center','width':'100%','float':'center','display':'inline-block','marginTop':'.5%'}),
]#,style={'background-image':'url("assets/background_image.png")'}
)

    # html.Div([
    #     dcc.Location(id='url', refresh=False),
    #     #dcc.Link('Global',href='/page-1'),
    #     #dcc.Link('Top',href='/page-2'),
    #     dcc.Link('Canada',href='/page-3'),
    #     html.Div(id='page-content'),
    # ],style={'textAlign':'center','width':'100%','float':'center','display':'inline-block'})])

number_plates = html.Div(id='number-plate',
             style={'marginLeft':'1.5%','marginRight':'1.5%','marginBottom':'.5%','marginTop':'.5%'},
             children=[
                 html.Div(id='conf-ind',
                          style={'width':'24.4%','marginRight':'.8%','display':'inline-block','padding':'1rem',
                                 'backgroundColor':dash_colors['background']},
                          children=[html.P(style={'textAlign':'center',
                                                  'color':dash_colors['red_bright'],
                                                  'fontSize':20},
                                           children='Confirmed Cases'),
                                    html.H3(style={'textAlign':'center',
                                                   'fontWeight':'bold','color': dash_colors['red_bright'],'fontSize':50},
                                            children='{:,.0f}'.format(int(global_total['Confirmed']))),
                                    html.P(style={'textAlign':'center',
                                                  'color': ticker_color(int(global_total['Confirmed']) - int(delta['Confirmed'])),
                                                  'fontSize':20},
                                           children='{0:+,d}'.format(int(global_total['Confirmed']) - int(delta['Confirmed']))
                                           + ' (' + global_total['Confirmed_pct'].map('{:+.2%}'.format) +')'
                                           )
                                    ],
                          className='four columns'),

                 html.Div(id='death-ind',
                          style={'width':'24.4%','marginRight':'.8%','display':'inline-block','padding':'1rem',
                                 'backgroundColor':dash_colors['background']},
                          children=[html.P(style={'textAlign':'center',
                                                  'color':dash_colors['red_bright'],
                                                  'fontSize':20},
                                           children='Deaths'),
                                    html.H3(style={'textAlign':'center',
                                                   'fontWeight':'bold','color': dash_colors['red_bright'],'fontSize':50},
                                            children='{:,.0f}'.format(int(global_total['Deaths']))),
                                    html.P(style={'textAlign': 'center',
                                                  'color': dash_colors['red_bright'], 'fontSize': 20},
                                           children='{0:+,d}'.format(int(global_total['Deaths']) - int(delta['Deaths']))
                                           + ' (' + global_total['Deaths_pct'].map('{:+.2%}'.format) +')'
                                           )
                                    ],
                          className='four columns'),

                 html.Div(id='rec-ind',
                          style={'width': '24.4%', 'marginRight': '.8%','display':'inline-block','padding':'1rem',
                                 'backgroundColor':dash_colors['background']},
                          children=[html.P(style={'textAlign': 'center',
                                                  'color': dash_colors['red_bright'],
                                                  'fontSize':20},
                                           children='Recoveries'),
                                    html.H3(style={'textAlign': 'center',
                                                   'fontWeight': 'bold', 'color': dash_colors['red_bright'],'fontSize':50},
                                            children='{:,.0f}'.format(int(global_total['Recovered']))),
                                    html.P(style={'textAlign': 'center',
                                                  'color': dash_colors['green'], 'fontSize': 20},
                                           children='{0:+,d}'.format(int(global_total['Recovered']) - int(delta['Recovered']))
                                           + ' (' + global_total['Recovered_pct'].map('{:+.2%}'.format) +')'
                                           )
                                    ],
                          className='four columns'),

                 html.Div(id='active-ind',
                          style={'width': '24.4%','display':'inline-block','padding':'1rem',
                                 'backgroundColor':dash_colors['background']},
                          children=[html.P(style={'textAlign': 'center',
                                                  'color': dash_colors['red_bright'],
                                                  'fontSize':20},
                                           children='Active Cases'),
                                    html.H3(style={'textAlign': 'center',
                                                   'fontWeight': 'bold', 'color': dash_colors['red_bright'],'fontSize':50},
                                            children='{:,.0f}'.format(int(global_total['Active']))),
                                    html.P(style={'textAlign': 'center',
                                                  'color': dash_colors['red_bright'], 'fontSize': 20},
                                           children='{0:+,d}'.format(int(global_total['Active']) - int(delta['Active']))
                                           + ' (' + global_total['Active_pct'].map('{:+.2%}'.format) +')'
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

df_ranking = countries_df[countries_df['Date'] == countries_df['Date'].max()].groupby(['Country'])['Confirmed','Deaths','Recovered','Active'].sum().sort_values('Confirmed',ascending=False).reset_index()
df_ranking['Rank'] = df_ranking.index + 1
df_ranking = df_ranking[['Rank','Country','Confirmed','Deaths','Recovered','Active']]
df_ranking[['Confirmed','Deaths','Recovered','Active']] = df_ranking[['Confirmed','Deaths','Recovered','Active']].astype(int).applymap('{:,}'.format)

page_3_layout = html.Div([
    html.Div(id='page-3'),
    html.Div(html.H2('Global Ranking - Top 20'),style={'backgroundColor': dash_colors['background'],'padding':'.5rem'}),
    html.Div(dbc.Table.from_dataframe(df_ranking.head(20),striped=True, bordered=True, hover=True),
             style={'marginTop':'.5%'})
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
# width:107.7,#height=600,#width=1845
news_feedx = html.Div([
    #html.Div(id='page-2'),
    html.Div(id='news',
             style={'marginLeft': '1.5%', 'marginRight': '1.5%', 'marginBottom': '.5%', 'marginTop': '.5%'},
             children=[
                 html.Div(html.Iframe(id='rss',
                                 src='https://www.rssdog.com/index.php?url=https%3A%2F%2Fwww.aljazeera.com%2Fxml%2Frss%2Fall.xml&mode=html&showonly=&maxitems=0&showdescs=1&desctrim=0&descmax=0&tabwidth=100%25&showdate=1&linktarget=_blank&bordercol=transparent&headbgcol=transparent&headtxtcol=%23ffffff&titlebgcol=transparent&titletxtcol=%23ffffff&itembgcol=transparent&itemtxtcol=%23ffffff&ctl=0',
                                 #src='https://www.rssdog.com/index.php?url=https%3A%2F%2Fwww.cbc.ca%2Fcmlink%2Frss-world&mode=html&showonly=&maxitems=0&showdescs=1&desctrim=0&descmax=0&tabwidth=100%25&showdate=1&linktarget=_blank&bordercol=transparent&headbgcol=transparent&headtxtcol=%23ffffff&titlebgcol=transparent&titletxtcol=%23ffffff&itembgcol=transparent&itemtxtcol=%23ffffff&ctl=0',
                                 style={'width':'100%','height':'42rem','display':'inline-block', 'border':'none'}),
                          style={'width':'49.6%'}),
                 html.Div(dbc.Table.from_dataframe(df_tweets[['Handle','Date','Tweet']],striped=True, bordered=True, hover=True,className='table-info',
                                                   style={'width':'100%'}),
                          style={'width':'49.6%','height':'42rem','display':'inline-block','marginLeft':'.7%','overflowY':'auto'}
                 )
             ],className='row')
])
# todo figure out how to scale the twitter table

newsfeed_div_style = {
    "position": "fixed", #static #relative
    "width": "23.7%",
    'height': '30rem',
    'marginLeft': '1.5%',
    'marginRight': '1.5%',
    'marginBottom': '.5%',
    'marginTop': '.5%',
    "padding": "1rem",
    "background-color": dash_colors['background'],
    'display': 'block'
}

twitter_div_style = {
    "position": "fixed",
    "width": "72.5%",
    'height': '22rem',
    'marginLeft': '26%',
    'marginRight': '1.5%',
    'marginBottom': '.5%',
    'marginTop': '.5%',
    "padding": "1rem",
    "background-color": dash_colors['background'],
    #'overflowY': 'auto',
    'display': 'block'

}

news_feed = html.Div([
    html.H2('News Feed'),
    html.Div(html.Iframe(id='rss',
                         src='https://www.rssdog.com/index.php?url=https%3A%2F%2Fwww.aljazeera.com%2Fxml%2Frss%2Fall.xml&mode=html&showonly=&maxitems=0&showdescs=1&desctrim=0&descmax=0&tabwidth=100%25&showdate=1&linktarget=_blank&bordercol=transparent&headbgcol=transparent&headtxtcol=%23ffffff&titlebgcol=transparent&titletxtcol=%23ffffff&itembgcol=transparent&itemtxtcol=%23ffffff&ctl=0',
                         #src='https://www.rssdog.com/index.php?url=https%3A%2F%2Fwww.cbc.ca%2Fcmlink%2Frss-world&mode=html&showonly=&maxitems=0&showdescs=1&desctrim=0&descmax=0&tabwidth=100%25&showdate=1&linktarget=_blank&bordercol=transparent&headbgcol=transparent&headtxtcol=%23ffffff&titlebgcol=transparent&titletxtcol=%23ffffff&itembgcol=transparent&itemtxtcol=%23ffffff&ctl=0',
                         style={'width':'100%','height':'25rem', 'border':'none'}),
                          )
   ],style=newsfeed_div_style
)

content = html.Div([
    html.Div(html.H2('Related Tweets'), style={'backgroundColor': dash_colors['background'],'padding':'.5rem'}),
    html.Div(id='tweets',
             children=[
                 dbc.Table.from_dataframe(df_tweets[['Handle','Date','Tweet']],striped=True, bordered=True, hover=True, className='table-info', size='sm'),
             ], style={'height': '15rem','marginTop':'.5%','overflowY':'scroll'})
], style=twitter_div_style)

# Display correct page based on user selection
@app.callback(Output('page-content', 'children'),
              [Input('url', 'pathname')])
def display_page(pathname):
    if pathname == '/page-1':
        return number_plates, page_1_layout
    elif pathname == '/page-2':
        return number_plates, news_feed, content
    elif pathname == '/page-3':
        return number_plates, page_3_layout
    elif pathname == '/page-4':
        return number_plates, page_4_layout
    else:
        return number_plates, news_feed, content


if __name__ == '__main__':
    app.run_server()