#!/usr/bin/env python
# coding: utf-8

import pandas as pd
import dash
from dash import html, dcc
from dash.dependencies import Input, Output
import plotly.express as px

app = dash.Dash(__name__)
app.config.suppress_callback_exceptions = True

# Load data
df = pd.read_csv('https://cf-courses-data.s3.us.cloud-object-storage.appdomain.cloud/IBMDeveloperSkillsNetwork-DV0101EN-SkillsNetwork/Data%20Files/Historical_Wildfires.csv')
df['Month'] = pd.to_datetime(df['Date']).dt.month_name()
df['Year']  = pd.to_datetime(df['Date']).dt.year

# Server export untuk deployment
server = app.server

# ── Layout ────────────────────────────────────────────────────────────────────
app.layout = html.Div(children=[

    html.H1('Australia Wildfire Dashboard',
            style={'textAlign': 'center', 'color': '#503D36', 'fontSize': 26}),

    # ── Controls ──────────────────────────────────────────────────────────────
    html.Div([
        html.Div([
            html.H2('Select Region:', style={'marginRight': '1em'}),
            dcc.RadioItems([
                {'label': 'New South Wales',    'value': 'NSW'},
                {'label': 'Northern Territory', 'value': 'NT'},
                {'label': 'Queensland',         'value': 'QL'},
                {'label': 'South Australia',    'value': 'SA'},
                {'label': 'Tasmania',           'value': 'TA'},
                {'label': 'Victoria',           'value': 'VI'},
                {'label': 'Western Australia',  'value': 'WA'},
            ], value='NSW', id='region', inline=True)
        ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '10px'}),

        html.Div([
            html.H2('Select Year:', style={'marginRight': '1em'}),
            dcc.Dropdown(df.Year.unique(), value=2005, id='year',
                         style={'width': '200px'})
        ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '20px'}),
    ], style={'padding': '0 20px'}),

    html.Hr(),

    # ── Section 1: Overview ───────────────────────────────────────────────────
    html.Div([
        html.H2('📊 Monthly Overview',
                style={'color': '#503D36', 'padding': '0 20px'}),
        html.Div([
            html.Div([], id='plot1'),
            html.Div([], id='plot2')
        ], style={'display': 'flex'}),
    ]),

    html.Hr(),

    # ── Section 2: Further Analysis ───────────────────────────────────────────
    html.Div([
        html.H2('🔍 Further Analysis',
                style={'color': '#503D36', 'padding': '0 20px'}),

        # Row 1: Tren tahunan + Perbandingan antar wilayah
        html.Div([
            html.Div([], id='plot3'),
            html.Div([], id='plot4')
        ], style={'display': 'flex'}),

        # Row 2: Scatter intensitas panas
        html.Div([], id='plot5'),
    ]),

], style={'fontFamily': 'Arial, sans-serif', 'maxWidth': '1400px', 'margin': '0 auto'})


# ── Callback ──────────────────────────────────────────────────────────────────
@app.callback(
    [Output('plot1', 'children'),
     Output('plot2', 'children'),
     Output('plot3', 'children'),
     Output('plot4', 'children'),
     Output('plot5', 'children')],
    [Input('region', 'value'),
     Input('year',   'value')]
)
def update_charts(input_region, input_year):

    # Filter data
    region_data = df[df['Region'] == input_region]
    y_r_data    = region_data[region_data['Year'] == input_year]

    # Plot 1: Pie — rata-rata luas kebakaran per bulan
    est_data = y_r_data.groupby('Month')['Estimated_fire_area'].mean().reset_index()
    fig1 = px.pie(est_data,
                  values='Estimated_fire_area',
                  names='Month',
                  title='{} : Monthly Average Estimated Fire Area in {}'.format(input_region, input_year))

    # Plot 2: Bar — rata-rata piksel vegetasi terbakar per bulan
    veg_data = y_r_data.groupby('Month')['Count'].mean().reset_index()
    fig2 = px.bar(veg_data,
                  x='Month', y='Count',
                  title='{} : Avg Count of Pixels for Presumed Vegetation Fires in {}'.format(input_region, input_year),
                  color='Count',
                  color_continuous_scale='Oranges')

    # Plot 3: Line — tren luas kebakaran tahunan
    yearly_trend = region_data.groupby('Year')['Estimated_fire_area'].mean().reset_index()
    fig3 = px.line(yearly_trend,
                   x='Year', y='Estimated_fire_area',
                   title='{} : Yearly Trend of Estimated Fire Area (All Years)'.format(input_region),
                   markers=True,
                   labels={'Estimated_fire_area': 'Avg Fire Area'})
    selected_year_val = yearly_trend[yearly_trend['Year'] == input_year]
    if not selected_year_val.empty:
        fig3.add_scatter(
            x=selected_year_val['Year'],
            y=selected_year_val['Estimated_fire_area'],
            mode='markers',
            marker=dict(color='red', size=12, symbol='star'),
            name='Selected Year'
        )

    # Plot 4: Bar — perbandingan rata-rata fire area antar wilayah
    year_data      = df[df['Year'] == input_year]
    region_compare = year_data.groupby('Region')['Estimated_fire_area'].mean().reset_index()
    region_compare['highlight'] = region_compare['Region'].apply(
        lambda x: 'Selected' if x == input_region else 'Other'
    )
    fig4 = px.bar(region_compare,
                  x='Region', y='Estimated_fire_area',
                  title='Region Comparison — Avg Fire Area in {}'.format(input_year),
                  color='highlight',
                  color_discrete_map={'Selected': '#e74c3c', 'Other': '#95a5a6'},
                  labels={'Estimated_fire_area': 'Avg Fire Area'},
                  category_orders={'Region': sorted(df['Region'].unique())})
    fig4.update_layout(showlegend=False)

    # Plot 5: Scatter — brightness vs radiative power
    fig5 = px.scatter(y_r_data,
                      x='Mean_estimated_fire_brightness',
                      y='Mean_estimated_fire_radiative_power',
                      color='Month',
                      size='Estimated_fire_area',
                      hover_data=['Month', 'Estimated_fire_area', 'Mean_confidence'],
                      title='{} {} : Fire Brightness vs Radiative Power (bubble size = fire area)'.format(input_region, input_year),
                      labels={
                          'Mean_estimated_fire_brightness': 'Fire Brightness (K)',
                          'Mean_estimated_fire_radiative_power': 'Radiative Power (MW)'
                      })
    fig5.update_layout(height=450)

    return [
        dcc.Graph(figure=fig1),
        dcc.Graph(figure=fig2),
        dcc.Graph(figure=fig3),
        dcc.Graph(figure=fig4),
        dcc.Graph(figure=fig5)
    ]


if __name__ == '__main__':
    app.run(debug=True)
