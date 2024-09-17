import dash
from dash import dcc, html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
import pandas as pd
import plotly.express as px
import json
import base64
import io

# Load the config from the JSON file
with open('dash.json', 'r') as f:
    config = json.load(f)

# Dash App setup
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.CYBORG])

# Layout with file upload and multiple graphs
app.layout = dbc.Container(
    [
        dbc.Row([ 
            dbc.Col(html.H1("Network Metrics Dashboard", style={"text-align": "center", "margin-top": "20px"}), width=12),
        ]),
        dbc.Row([ 
            dbc.Col([ 
                html.Label("Upload CSV File:", style={"margin-top": "20px"}), 
                dcc.Upload(
                    id='upload-csv',
                    children=html.Div(['Drag and Drop or ', html.A('Select a CSV File')]),
                    style={
                        'width': '100%', 'height': '60px', 'lineHeight': '60px', 
                        'borderWidth': '1px', 'borderStyle': 'dashed', 
                        'borderRadius': '5px', 'textAlign': 'center', 
                        'margin': '10px'
                    },
                    multiple=False
                ),
            ], width=12),
        ]),
        dbc.Row([ 
            dbc.Col(dcc.Graph(id='packet-loss-graph'), width=6), 
            dbc.Col(dcc.Graph(id='latency-graph'), width=6),
        ], style={"margin-top": "30px"}),  
        dbc.Row([ 
            dbc.Col(dcc.Graph(id='availability-graph'), width=12),
        ], style={"margin-top": "30px", "margin-bottom": "30px"}),
    ],
    fluid=True
)

# Data cleaning function
def clean_data(df):
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

# Callback function to handle file upload and update all graphs
@app.callback(
    [Output('packet-loss-graph', 'figure'),
     Output('latency-graph', 'figure'),
     Output('availability-graph', 'figure')],
    Input('upload-csv', 'contents'),
    State('upload-csv', 'filename')
)
def update_graphs(csv_content, filename):
    if csv_content is not None:
        # Read CSV from uploaded file
        content_type, content_string = csv_content.split(',')
        decoded = base64.b64decode(content_string)
        df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
        
        # Clean the data
        df = clean_data(df)
        
        # Packet Loss Graph
        packet_loss_fig = px.bar(
            df, x="Host_name", y="Packetloss(%)",
            title="Packet Loss Percentage by Host Name",
            labels={"Packetloss(%)": "Packet Loss (%)"},
            template="plotly_dark",
            color="Packetloss(%)",
            color_continuous_scale=["green", "yellow", "orange", "red"],
        )
        packet_loss_fig.update_layout(margin={"l": 40, "r": 20, "t": 40, "b": 30})

        # Latency Graph
        latency_fig = px.bar(
            df, x="Host_name", y="Latency(msec)",
            title="Latency by Host Name",
            labels={"Latency(msec)": "Latency (ms)"},
            template="plotly_dark",
            color="Latency(msec)",
            color_continuous_scale=["green", "yellow", "orange", "red"],
        )
        latency_fig.update_layout(margin={"l": 40, "r": 20, "t": 40, "b": 30})

        # Availability Graph
        availability_fig = px.bar(
            df, x="Host_name", y="Availability-%",
            title="Availability by Host Name",
            labels={"Availability-%": "Availability (%)"},
            template="plotly_dark",
            color="Availability-%",
            color_continuous_scale=["red", "orange", "yellow", "green"],
        )
        availability_fig.update_layout(margin={"l": 40, "r": 20, "t": 40, "b": 30})
        
        return packet_loss_fig, latency_fig, availability_fig
    
    # Return empty graphs if no file is uploaded
    return {}, {}, {}

if __name__ == '__main__':
    app.run_server(host='0.0.0.0', port=8080)
