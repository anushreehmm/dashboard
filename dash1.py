#!/usr/bin/env python
# coding: utf-8

# In[6]:


import dash
from dash import dcc, html
import plotly.express as px
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output
import pandas as pd
import json
import glob
import os

# Load the config from the JSON file
with open('dash.json', 'r') as f:
    config = json.load(f)

thresholds = config['service_agreements']

# Data cleaning function
def clean_data(file_path):
    df = pd.read_csv(file_path)
    df = df.drop([0, 1, 2, 3, 4], axis=0)
    df = df.reset_index(drop=True)
    df = df.drop(columns=['Unnamed: 2', 'Unnamed: 3'])
    df = df.rename(columns={
        'Unnamed: 0': 'Host_name', 
        'Unnamed: 1': 'IP_address', 
        'Unnamed: 4': 'Availability-%', 
        'Unnamed: 5': 'Latency(msec)', 
        'Unnamed: 6': 'Packetloss(%)'
    })
    df['Packetloss(%)'] = pd.to_numeric(df['Packetloss(%)'], errors='coerce')
    df['Availability-%'] = pd.to_numeric(df['Availability-%'], errors='coerce')
    df['Latency(msec)'] = pd.to_numeric(df['Latency(msec)'], errors='coerce')
    df = df.dropna(subset=['Packetloss(%)', 'Availability-%', 'Latency(msec)'])
    return df

# Folder containing CSV files
folder_path = r'C:\Users\AnushreeHM\Downloads\ibus'

# Get list of all CSV files in the folder
file_list = glob.glob(os.path.join(folder_path, '*.csv'))

# Load and clean each file
dataframes = [clean_data(file_path) for file_path in file_list]

# Combine all DataFrames into one
df = pd.concat(dataframes, ignore_index=True)

# Dash App setup
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.CYBORG])

# List of unique hostnames for dropdown filter
hostnames = df['Host_name'].unique()

app.layout = dbc.Container(
    [
        dbc.Row([
            dbc.Col(html.H1("Network Metrics Dashboard", style={"text-align": "center", "margin-top": "20px"}), width=12),
        ]),
        dbc.Row([
            dbc.Col([
                html.Label("Filter by Host Name:", style={"margin-top": "20px"}),
                dcc.Dropdown(
                    id='hostname-dropdown',
                    options=[{'label': name, 'value': name} for name in hostnames],
                    multi=True,
                    value=hostnames[:5],
                    placeholder="Select Hostnames",
                    style={"color": "#000"}
                ),
            ], width=12),
        ]),
        dbc.Row([
            dbc.Col(
                dcc.Graph(id='packet-loss-graph'), 
                width=6
            ),
            dbc.Col(
                dcc.Graph(id='latency-graph'), 
                width=6
            ),
        ], style={"margin-top": "30px"}),
        dbc.Row([
            dbc.Col(
                dcc.Graph(id='availability-graph'), 
                width=12
            ),
        ], style={"margin-top": "30px", "margin-bottom": "30px"}),
    ], 
    fluid=True
)

# Functions for color mapping based on thresholds from the config
def get_packet_loss_color(value, service='taj'):
    thresholds = config['service_agreements'][service]['packet_loss_threshold']
    if value > thresholds['critical']:
        return 'red'
    elif value > thresholds['warning']:
        return 'orange'
    elif value > thresholds['caution']:
        return 'yellow'
    else:
        return 'green'

def get_latency_color(value, service='taj'):
    thresholds = config['service_agreements'][service]['latency_threshold']
    if value > thresholds['critical']:
        return 'red'
    elif value > thresholds['warning']:
        return 'orange'
    elif value > thresholds['caution']:
        return 'yellow'
    else:
        return 'green'

def get_availability_color(value, service='taj'):
    thresholds = config['service_agreements'][service]['availability_threshold']
    if value > thresholds['critical']:
        return 'red'
    elif value > thresholds['warning']:
        return 'orange'
    elif value > thresholds['caution']:
        return 'yellow'
    else:
        return 'green'

# Callback function to update graphs dynamically based on dropdown selection
@app.callback(
    [Output('packet-loss-graph', 'figure'),
     Output('latency-graph', 'figure'),
     Output('availability-graph', 'figure')],
    [Input('hostname-dropdown', 'value')]
)
def update_graphs(selected_hostnames):
    filtered_df = df[df['Host_name'].isin(selected_hostnames)]

    # Packet Loss Graph
    packet_loss_fig = px.bar(
        filtered_df,
        x="Host_name",
        y="Packetloss(%)",
        title="Packet Loss Percentage by Host Name",
        labels={"Packetloss(%)": "Packet Loss (%)"},
        template="plotly_dark",
        color="Packetloss(%)",
        color_continuous_scale=["green", "yellow", "orange", "red"],
    )
    packet_loss_fig.update_layout(margin={"l": 40, "r": 20, "t": 40, "b": 30})

    # Latency Graph
    latency_fig = px.bar(
        filtered_df,
        x="Host_name",
        y="Latency(msec)",
        title="Latency by Host Name",
        labels={"Latency(msec)": "Latency (ms)"},
        template="plotly_dark",
        color="Latency(msec)",
        color_continuous_scale=["green", "yellow", "orange", "red"],
    )
    latency_fig.update_layout(margin={"l": 40, "r": 20, "t": 40, "b": 30})

    # Availability Graph
    availability_fig = px.bar(
        filtered_df,
        x="Host_name",
        y="Availability-%",
        title="Availability by Host Name",
        labels={"Availability-%": "Availability (%)"},
        template="plotly_dark",
        color="Availability-%",
        color_continuous_scale=["red", "orange", "yellow", "green"],
    )
    availability_fig.update_layout(margin={"l": 40, "r": 20, "t": 40, "b": 30})

    return packet_loss_fig, latency_fig, availability_fig

if __name__ == '__main__':
    app.run_server(debug=True, port=int(os.environ.get("PORT", 8080)))



# In[ ]:




