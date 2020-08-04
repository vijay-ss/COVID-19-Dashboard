"""MAIN APP"""

import dash
import dash_table
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from datetime import date, timedelta
import base64

"""GATHER INPUT FILES"""

# import twitter_web_scrape
# df_tweets = pd.read_csv(r'data/covid_tweets.csv')
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
df_tweets['Category'] = df_tweets['compound'].apply(lambda x: 'Positive' if x > 0 else \
    ('Negative' if x < 0 else 'Neutral'))

# convert Date object to Datetime
countries_df['Date'] = pd.to_datetime(countries_df['Date'])
global_daily_count['Date'] = pd.to_datetime(global_daily_count['Date'])
global_melt['Date'] = pd.to_datetime(global_melt['Date'])
canada_df['Date'] = pd.to_datetime(canada_df['Date'])
canada_province['Date'] = pd.to_datetime(canada_province['Date'])

# Canada day over day
canada_province['Diff'] = canada_province.groupby('Province/State')['Confirmed'].diff(periods=1)

# Ranked Countries by confirmed
df_ranking = countries_df[countries_df['Date'] == countries_df['Date'].max()].groupby(['Country'])[
    'Confirmed', 'Deaths', 'Recovered', 'Active'].sum().sort_values('Confirmed', ascending=False).reset_index()
df_ranking['Rank'] = df_ranking.index + 1
df_ranking = df_ranking[['Rank', 'Country', 'Confirmed', 'Deaths', 'Recovered', 'Active']]
df_ranking[['Confirmed', 'Deaths', 'Recovered', 'Active']] = df_ranking[
    ['Confirmed', 'Deaths', 'Recovered', 'Active']].astype(int).applymap('{:,}'.format)
    
t10 = df_ranking['Country'].head(10).to_list()

df_ts_t10 = countries_df[countries_df['Country'].isin(t10)]

"""CREATE PLOTS"""

fig_area = px.area(global_melt
                   , x="Date"
                   , y="Count"
                   , color='Type'
                   # ,height=600
                   # ,width=900
                   , title='Timeline of Worldwide Cases - by Type'
                   , template='plotly_dark'
                   )
fig_area.update_layout(xaxis_rangeslider_visible=True)

# Pie chart of confirmed
# fig_pie_conf = px.pie(countries_df[countries_df['Date'] == countries_df['Date'].max()].groupby(['Country'])[
#     'Confirmed', 'Deaths', 'Recovered', 'Active'].sum().sort_values('Confirmed', ascending=False).reset_index().head(20), 
# values='Confirmed', 
# names='Country',
# template='plotly_dark')

# Time Series
fig_timeseries = px.line(x=df_ts_t10['Date'].dt.strftime('%Y-%m-%d'),
                         y=df_ts_t10["Confirmed"],
                         color=df_ts_t10["Country"],
                         hover_name=df_ts_t10["Country"],
                         line_shape="spline",
                         render_mode="svg",
                         template='plotly_dark'
                         )
fig_timeseries.update_layout(title="Timeline of Top 10 Countries",
                             xaxis_title="Date",
                             yaxis_title="Confirmed Cases",
                             legend_title="Country")

# Data input for Mapbox plot
formatted_gdf = countries_df.groupby(['Date', 'Country', 'Description', 'Lat', 'Long'])['Confirmed'].max().reset_index()
formatted_gdf['Date'] = formatted_gdf['Date'].dt.strftime('%m/%d/%Y')

# Mapbox
fig_mapbox = px.scatter_mapbox(
    mapbox_style='carto-darkmatter',
    title='Global Outbreak Map - select date using slider below',
    lat=formatted_gdf['Lat'],
    lon=formatted_gdf['Long'],
    hover_name=formatted_gdf['Description'],
    #size=np.where(formatted_gdf['Confirmed'] > 0, np.ceil(np.log(formatted_gdf['Confirmed'])), 0),
    size=formatted_gdf['Confirmed'].pow(0.3),
    range_color=[0, 150000],
    opacity=0.6,
    size_max=30,
    zoom=1.3,
    animation_frame=countries_df['Date'].astype(str),
    # center=go.layout.mapbox.Center(lat=14,lon=21),
    template='plotly_dark',
    color=formatted_gdf['Confirmed'],
    color_continuous_scale='Portland',
    # color_discrete_sequence=px.colors.qualitative.Light24,
)
fig_mapbox.update_layout(autosize=True, coloraxis_showscale=True,
coloraxis_colorbar=dict(
    title='Confirmed Cases'
)
)

# Ontario Map
fig_can = px.line(x=canada_df['Date'],
                  y=canada_df["Confirmed"],
                  color=canada_df['Province/State'],
                  hover_name=canada_df['Province/State'],
                  line_shape="spline",
                  render_mode="svg",
                  template='plotly_dark',
                  color_discrete_sequence=px.colors.qualitative.Bold
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
                  template='plotly_dark',
                  color_discrete_sequence=px.colors.qualitative.Bold

                  )
fig_dod.update_layout(
    title="Day over day - by Province",
    xaxis_title="Date",
    yaxis_title="Daily Delta",
    legend_title="Province"
)

# Twitter sentiment pie chart
fig_pie = go.Figure(data=[go.Pie(
    labels=df_tweets['Category'].unique(),
    values=df_tweets['Category'].value_counts(),
    hole=.3,
    pull=[0, 0, 0.1]
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
    'white': '#fff',
    'grid': '#333333',
    'red': '#BF0000',
    'red_bright': '#d7191c',
    'blue': '#466fc2',
    'green': '#5bc246',
    'orange': '5A9E6F'
}

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
    # "padding": "1rem",
    # "background-color": dash_colors['background'],
}

# base margin style for each page
page_margin = {'marginLeft': '1.5%', 'marginRight': '1.5%', 'marginBottom': '.5%', 'marginTop': '.5%'}


def ticker_color(tick_value):
    if tick_value > 0:
        return dash_colors['red']
    else:
        return dash_colors['green']


def ticker_color_rec(tick_value):
    if tick_value > 0:
        return dash_colors['green']
    else:
        return dash_colors['blue']


# todo update function to include colors for all metric types

# Latest count per country for number plates
global_total = global_daily_count.join(
    global_daily_count[['Confirmed', 'Deaths', 'Recovered', 'Active']].pct_change(fill_method='ffill').add_suffix(
        '_pct'))
global_total = global_total[global_daily_count['Date'] == global_total['Date'].max()]
delta = global_daily_count[global_daily_count['Date'] == global_daily_count['Date'].max() - timedelta(days=1)]

# Icons for about page
twitter_icon = 'twitter_icon.png'
linkedin_icon = 'linkedin_icon.png'
email_icon = 'email_icon.png'
github_icon = 'github_icon.png'

encoded_twitter = base64.b64encode(open(twitter_icon, 'rb').read())
encoded_linkedin = base64.b64encode(open(linkedin_icon, 'rb').read())
encoded_email = base64.b64encode(open(email_icon, 'rb').read())
encoded_github = base64.b64encode(open(github_icon, 'rb').read())


about_app = html.Div(
    children=[
        html.P('''
        This interactive dashboard is aimed at providing users with a daily summary of the global situation 
        on Covid-19. It is intended for those seeking a concise breakdown of the numbers, without the constant news 
        updates. There is also a snapshot for Canadian cases, and can be expanded to other regions in the future as necessary.
        '''),
        html.P('''
        This dashboard demonstrates the power of Open Source data combined with the python
        Plotly-Dash libraries, with the ability to display powerful visualizations to the end user.
        '''),
        html.P('''
        This particular dashboard is optimized for viewing on a desktop environment due to the nature of the interactive
        plots. Mobile viewing is possible, however not optimal.
        '''),
        html.P('''
        All source data is available in the links below - as well as the Github repository. 
        Credit is given to the following teams for proving the respective data:
        '''),
        html.Ul([
            html.Li('John Hopkins University - Dataset for Covid-19 cases'),
            html.Li('Georgia State University - Common twitter mentions for Covid-19')
        ]),
        html.P('''
        A special thanks also goes out to the front-line medical teams who are tirelessly fighting to flatten the 
        curve.
        '''),
        html.Ul([
            html.Li(html.A('John Hopkins University CSSE dataset',
                           href='https://github.com/CSSEGISandData/COVID-19', target='_blank')),
            html.Li(html.A('Georgia State University Panacea Lab Twitter dataset',
                           href='https://github.com/thepanacealab/covid19_twitter', target='_blank')),
            html.Li(html.A('Open Source Dashboard Code',
                           href='https://github.com/vijay-ss/COVID-19-Dashboard', target='_blank'))
        ]),
        html.Div(id='contact-info', children=[
            html.Img(src='data:image/png;base64,{}'.format(encoded_linkedin.decode())),
            html.A('Linkdin', href='https://www.linkedin.com/in/vijay-ss/', target='_blank'),
            html.A(' '),
            html.Img(src='data:image/png;base64,{}'.format(encoded_twitter.decode())),
            html.A('Twitter', href='https://twitter.com/df_vijay', target='_blank'),
            html.A(' '),
            html.Img(src='data:image/png;base64,{}'.format(encoded_github.decode()),
                     style={'max-width': '48px', 'max-height': '48px'}),
            html.A(' '),
            html.A('Github', href='https://github.com/vijay-ss', target='_blank'),
            html.A(' '),
            html.Img(src='data:image/png;base64,{}'.format(encoded_email.decode()),
                     style={'max-width': '40px', 'max-height': '40px'}),
            html.A(' '),
            html.A('Email', href='mailto:vijay_saddi@outlook.com', target='_blank'),
        ], style={'textAlign': 'center'},
        ),
    ]
)

'''BEGIN DASH APP'''

external_stylesheets = ['https://codepen.io/unicorndy/pen/GRJXrvP.css',
                        'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css']

external_scripts = [{
    'type': 'text/javascript',
    'src': '//s7.addthis.com/js/300/addthis_widget.js#pubid=ra-5edbdf00d020a898'
}]

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.SLATE], external_scripts=external_scripts)
server = app.server
app.title = 'Covid-19 Tracker'

app.layout = html.Div(children=[
    html.H1(children='Covid-19 Interactive Tracker',
            style={'textAlign': 'center'}),

    html.Div(children='Data last updated: ' + global_daily_count['Date'].max().strftime('%Y-%m-%d') +
                      ' (Maintained by John Hopkins University)',
             style={'textAlign': 'center'}),


    html.Div([
        dcc.Location(id='url', refresh=False),
        dbc.Button(dcc.Link('World', href='/page-1'), id="global-button", color='primary', className="mr-1"),
        dbc.Button(dcc.Link('Map', href='/page-2'), id="map-button", color='primary', className="mr-1"),
        dbc.Button(dcc.Link('News', href='/page-3'), id="news-button", color='primary', className="mr-1"),
        dbc.Button(dcc.Link('Canada', href='/page-4'), id="canada-button", color='primary', className="mr-1"),
        dbc.Button('About', id='open', active=False),
        dbc.Modal([
            # the contents should all be stored in a Div
            dbc.ModalHeader(children=[html.P('Covid-19 Open Source Interactive Dashboard')],
                            style={'margin': '0 auto'}),
            dbc.ModalBody(children=[about_app]),
            dbc.ModalFooter(dbc.Button('Close', id='close', className='ml-auto', size='sm'))
        ], id='modal', size='lg', scrollable=True, centered=True, autoFocus=True),
        html.Div(id='page-content'),
        # html.Span(id='button-container')
    ], style={'textAlign': 'center', 'width': '100%', 'float': 'center', 'display': 'inline-block',
              'marginTop': '.5%'}),
]  # ,style={'background-image':'url("assets/background_image.png")'}
)

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
                                                              'color': ticker_color_rec(int(global_total['Recovered']) - int(delta['Recovered'])), 'fontSize': 20},
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
                                                              'color': ticker_color(int(global_total['Active']) - int(delta['Active'])), 'fontSize': 20},
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
])

# table = html.Div([
#     html.Div(dash_table.DataTable
#     (id='interactive-table',
#     data=df_ranking.to_dict('records'),
#     columns=[{"name": i, "id": i, 'deletable': True, 'selectable': True} for i in df_ranking.columns],
#     style_header={'backgroundColor': 'rgb(30, 30, 30)','fontWeight': 'bold' },
#     style_cell={'backgroundColor': '#3A3F44','color': dash_colors['text'],'maxWidth': 0,'fontSize':14},
#     style_table={'maxHeight': '350px','overflowY': 'auto'},
#     style_data_conditional=[{'if': {'row_index': 'even'},'backgroundColor': '#272B30',}],
#     style_cell_conditional=[
#         {'if': {'column_id': 'Rank'},'width': '10%'},
#         {'if': {'column_id': 'Country'},'width': '26%'},
#         {'if': {'column_id': 'Confirmed'},'width': '16%'},
#         {'if': {'column_id': 'Deaths'},'width': '11%'},
#         {'if': {'column_id': 'Recovered'},'width': '16%'},
#         {'if': {'column_id': 'Active'},'width': '16%'}
#         ],
#         editable=False,
#                             filter_action="native",
#                             sort_action="native",
#                             sort_mode="single",
#                             row_selectable="single",
#                             row_deletable=False,
#                             selected_columns=[],
#                             selected_rows=[],
#                             page_current=0,
#                             page_size=1000, 
#     ))
# ], style={'marginLeft': '1.5%', 'marginRight': '1.5%', 'marginBottom': '.5%', 'marginTop': '.5%',
# 'backgroundColor': dash_colors['background']})

world_map =  html.Div([
    html.Div(id='world-map',
    style={'marginLeft': '1.5%', 'marginRight': '1.5%', 'marginBottom': '.5%', 'marginTop': '.5%'},
    children=[html.Div(dcc.Graph(id='global-outbreak', figure=fig_mapbox, style={'height': 800}))
    ])
    ])

# table_dbc = html.Div([
#     html.Div(id='styled-table'),
#     html.Div(html.H2('Top 20 Confirmed as of '+ global_daily_count['Date'].max().strftime('%b %e, %Y')),
#              style={'backgroundColor': dash_colors['background'], 'padding': '.5rem'}),
#     html.Div(dbc.Table.from_dataframe(df_ranking.head(20), striped=True, bordered=True, hover=True),
#              style={'marginTop': '.5%'})
# ], style={'marginLeft': '1.5%', 'marginRight': '1.5%', 'marginBottom': '.5%', 'marginTop': '.5%'})

table = html.Div([
    html.Div(id='styled-table'),
    html.Div(html.H2('Ranking by Confirmed Cases as of '+ global_daily_count['Date'].max().strftime('%b %e, %Y')),
             style={'backgroundColor': dash_colors['background'], 'padding': '.5rem'}),
    html.Div([
        dash_table.DataTable(id='datatable-interactivity',
            data=df_ranking.to_dict('records'),
            columns=[{"name": i, "id": i, "deletable": False, "selectable": True} for i in df_ranking.columns],
        #fixed_rows={'headers': True, 'data':0},
        style_header={'backgroundColor': 'rgb(30,30,30)','fontWeight': 'bold'},
        style_table={'maxHeight': '500px','overflowY': 'auto', 'overflowX': 'false'},
        style_data={'whiteSpace': 'normal', 'height': 'auto',},
        style_data_conditional=[{'if': {'row_index': 'even'}, 'backgroundColor': '#272B30'}],
        style_cell_conditional=[
            {'if': {'column_id': 'Rank'},'width': '8%'},
            {'if': {'column_id': 'Country'},'width': '25%'},
            {'if': {'column_id': 'Confirmed'},'width': '15%'},
            {'if': {'column_id': 'Deaths'},'width': '15%'},
            {'if': {'column_id': 'Recovered'},'width': '15%'},
            {'if': {'column_id': 'Active'},'width': '15%'},
            ],
        style_cell={'backgroundColor': '#272B30', 'color': dash_colors['white'], 
        'maxWidth': 0, 'fontSize':16, 'textAlign': 'center', 'font-family': 'Segoe UI'},
        editable=False,
        filter_action="native",
        sort_action="native",
        sort_mode="single",
        #column_selectable="single",
        #row_selectable="single",
        row_deletable=False,
        selected_columns=[],
        selected_rows=[],
        #page_action="native",
        page_current= 0,
        page_size= 1000,
        style_as_list_view=True
        )
        ])
        ], 
        style={'marginLeft': '1.5%', 'marginRight': '1.5%', 'marginBottom': '.5%', 'marginTop': '.5%', 'height': '650px'},
className='six columns'
)

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

news_feed_layout = html.Div(id='news-page', style=page_margin, children=[
    html.Div(id='rss-feed',
             children=[
                 html.H2('News Feed'),
                 html.Div(html.Iframe(id='rss',
                                      src='https://www.rssdog.com/index.php?url=https%3A%2F%2Fwww.aljazeera.com%2Fxml%2Frss%2Fall.xml&mode=html&showonly=&maxitems=0&showdescs=1&desctrim=0&descmax=0&tabwidth=100%25&showdate=1&linktarget=_blank&bordercol=transparent&headbgcol=transparent&headtxtcol=%23ffffff&titlebgcol=transparent&titletxtcol=%23ffffff&itembgcol=transparent&itemtxtcol=%23ffffff&ctl=0',
                                      # src='https://www.rssdog.com/index.php?url=https%3A%2F%2Fwww.cbc.ca%2Fcmlink%2Frss-world&mode=html&showonly=&maxitems=0&showdescs=1&desctrim=0&descmax=0&tabwidth=100%25&showdate=1&linktarget=_blank&bordercol=transparent&headbgcol=transparent&headtxtcol=%23ffffff&titlebgcol=transparent&titletxtcol=%23ffffff&itembgcol=transparent&itemtxtcol=%23ffffff&ctl=0',
                                      style={'width': '100%', 'height': '49rem', 'border': 'none', 'padding': '.5rem'}),
                          )
             ], style=newsfeed_div_style),
    html.Div(id='twitter',
             children=[
                 html.Div(html.H2('Related Tweets'),
                          style={'backgroundColor': dash_colors['background'], 'padding': '.5rem'}),
                 html.Div(id='tweets',
                          children=[
                              dbc.Table.from_dataframe(df_tweets[['Handle', 'Date', 'Tweet']], striped=True,
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

# datatable
@app.callback(
    Output('datatable-interactivity', 'style_data_conditional'),
    [Input('datatable-interactivity', 'selected_columns')]
)
def update_styles(selected_columns):
    return [{
        'if': { 'column_id': i },
        'background_color': '#D2F3FF'
    } for i in selected_columns]

# Info modal window
@app.callback(
    Output("modal", "is_open"),
    [Input("open", "n_clicks"), Input("close", "n_clicks")],
    [State("modal", "is_open")],
)
def toggle_modal(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open


# Display correct page based on user selection
@app.callback(Output('page-content', 'children'),
              [Input('url', 'pathname')])
def display_page(pathname):
    if pathname == '/page-1':
        return number_plates, page_1_layout, table
    elif pathname == '/page-2':
        return number_plates, world_map
    elif pathname == '/page-3':
        return number_plates, news_feed_layout
    elif pathname == '/page-4':
        return number_plates, page_4_layout
    else:
        return number_plates, page_4_layout #page_1_layout, table

if __name__ == '__main__':
    app.run_server()