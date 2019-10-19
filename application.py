import base64
import time
import io
import gpxpy
import os

import dash
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html

import pandas as pd
import numpy as np

import chart_studio.plotly as py
import plotly.graph_objects as go
import plotly.io as pio
import plotly.express as px
pio.templates.default = "ggplot2"


app = dash.Dash()
application = app.server

app.layout = html.Div([

                html.Div([
                    html.H1(children='GPX File 3D Plotter (10 MB File Limit)',style={'textAlign': 'center'}),
   
                        
                    html.H3("Upload Files"),
                    dcc.Upload(
                        id='upload-data',
                        children=html.Div([
                            'Drag and Drop or ',
                            html.A('Select Files')
                        ]),
                        style={
                            'width': '95%',
                            'height': '60px',
                            'lineHeight': '60px',
                            'borderWidth': '1px',
                            'borderStyle': 'dashed',
                            'borderRadius': '5px',
                            'textAlign': 'center',
                            'margin': '10px',
                            'padding':'5px',

                        },
                        multiple=False)
                ]),
                
                html.Div([                       
                        html.Label('Z-data Values for Colorbar Scale (Optional)',
                            style={'display':'table-cell','font-weight':'bold'}),                   
                        dcc.Input(id='zmin',type='number',placeholder='z minimum',
                            style={'display':'table-cell','padding':'10px'}),
                        dcc.Input(id='zmax',type='number',placeholder="z maximum",
                            style={'display':'table-cell','padding':'10px'}),
                              
                    ],        
                    style={'display':'vertical-block','font-family':'Trebuchet MS, sans-serif','padding':'5px'}
                ),
                
                html.Div([
                            html.Label('Select Z-data for Colorscale',style={'font-weight':'bold'}),
                            dcc.Dropdown(id='z-data',
                                        multi = False,
                                        placeholder='Filter Column')
                ],
                style={'width':'25%','display': 'inline-block','padding':'5px','vertical-align': 'top'}
                ),
                
                html.Div(id="graph-val"),
                html.Div(id='df0', style={'display': 'none'}),
                html.Div(id='df1',style={'display': 'none'}),
            ],
            style={'font-family':'Trebuchet MS, sans-serif','border':'3px outset','padding':'5px','background-color':'#f5f5f5'}
            )

def parsegpx(contents):
    points2 = list()
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)

    with io.StringIO(decoded.decode('utf-8')) as gpxfile:
        gpx = gpxpy.parse(gpxfile)
        for track in gpx.tracks:
            for segment in track.segments:
                for point_idx,point in enumerate(segment.points):
                    dict = {'Timestamp': point.time,
                            'Latitude': point.latitude,
                            'Longitude': point.longitude,
                            'Elevation': point.elevation,
                            'Speed':segment.get_speed(point_idx)
                            }
                    points2.append(dict)
    return points2

@app.callback(Output('df0','children'),
              [Input('upload-data', 'contents')
              ])

def update_output(content):
    if content is not None:
        df = pd.DataFrame(parsegpx(content))
        return df.to_json()
    else:
        return [{}]

@app.callback(Output('z-data', 'options'),
              [Input('df0','children')
              ])

def zopts(data):
        df = pd.read_json(data)
        return [{'label': i, 'value': i} for i in df.columns]

@app.callback(Output('graph-val', 'children'),
              [Input('df0', 'children'),
               Input('zmin', 'value'),
               Input('zmax', 'value'),
               Input('z-data', 'value') 
              ])

def graph(data,zmin,zmax,zdata):

    df = pd.read_json(data)

    return dcc.Graph(
                figure = go.Figure(
                    data=[go.Scatter3d(
                        x=df['Longitude'], y=df["Latitude"], z=df['Elevation'],mode='markers',
                        marker=dict(
                            size=6,
                            color=df[zdata],
                            colorscale='jet',
                            cmin = zmin,
                            cmax = zmax,
                            showscale=True
                        )
                    )],
                    
               layout = go.Layout(
                    scene={    
                        'xaxis':{'title':'Longitude'},
                        'yaxis':{'title':'Latitude'},
                        'zaxis':{'title':'Elevation (ft)'}
                        
                    },
                    margin={'t': 5,'b':5},
               
                    ),

                ),
                style = {'height':'750px'}
            )

if __name__ == '__main__':
    app.run_server(port=8080)