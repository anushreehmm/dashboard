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

# Initialize a global variable to store uploaded CSV data
uploaded_data = pd.DataFrame()

# Layout with file upload, dropdown, and multiple graphs
app.layout = dbc.Container(
    [
        dbc.Row([ 
            dbc.Col(html.H1("Network Metrics Dashboard", style={"text-align": "center", "margin-top": "20px"}), width=12),
        ]),
        dbc.Row([ 
            dbc.Col([ 
                html.Label("Upload CSV File:", html_for="upload-csv", style={"margin-top": "20px"}), 
                dcc.Upload(
                    id='upload-csv',
                    children=html.Div(['Drag and Drop or ', html.A('Select a CSV File')]),
                    style={
                        'width': '100%', 'height': '60px', 'lineHeight': '60px', 
                        'borderWidth': '1px', 'borderStyle': 'dashed', 
                        'borderRadius': '5px', 'textAlign': 'center', 
                        'margin': '10px'
                    },
                    multiple=True
                ),
            ], width=12),
        ]),
        dbc.Row([ 
            dbc.Col([ 
                html.Label("Filter by Host Name:", html_for="hostname-dropdown", style={"margin-top": "20px"}), 
                dcc.Dropdown(
                    id='hostname-dropdown',
                    multi=True,
                    placeholder="Select Hostnames",
                    style={"color": "#000"}
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
        dbc.Row([ 
            dbc.Col(dbc.Button("Clear Uploaded Data", id="clear-data-btn", color="danger", style={"margin-top": "20px"}), width=12),
        ]),
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

# Combined callback to handle file uploads, update dropdown, and update graphs
@app.callback(
    [
        Output('hostname-dropdown', 'options'),
        Output('packet-loss-graph', 'figure'),
        Output('latency-graph', 'figure'),
        Output('availability-graph', 'figure')
    ],
    [
        Input('upload-csv', 'contents'),
        Input('clear-data-btn', 'n_clicks')
    ],
    [
        State('upload-csv', 'filename'),
        State('hostname-dropdown', 'value')
    ]
)
def update_dashboard(upload_csv_contents, clear_data_n_clicks, filenames, selected_hostnames):
    global uploaded_data

    # Handle file upload
    if upload_csv_contents:
        for content, name in zip(upload_csv_contents, filenames):
            content_type, content_string = content.split(',')
            decoded = base64.b64decode(content_string)
            df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
            print(f"Loaded data from {name}:")
            print(df.head())
            cleaned_df = clean_data(df)
            uploaded_data = pd.concat([uploaded_data, cleaned_df], ignore_index=True)
            print(f"Data after cleaning: {uploaded_data.head()}")

    # Handle clear data button
    if clear_data_n_clicks:
        uploaded_data = pd.DataFrame()  # Clear uploaded data
        return [], {}, {}, {}

    # Generate dropdown options
    if not uploaded_data.empty:
        unique_hostnames = uploaded_data['Host_name'].unique()
        dropdown_options = [{'label': hostname, 'value': hostname} for hostname in unique_hostnames]
    else:
        dropdown_options = []

    # Generate graphs
    if uploaded_data.empty or not selected_hostnames:
        return dropdown_options, {}, {}, {}

    filtered_df = uploaded_data[uploaded_data['Host_name'].isin(selected_hostnames)]

    # Packet Loss Graph
    packet_loss_fig = px.bar(
        filtered_df, x="Host_name", y="Packetloss(%)",
        title="Packet Loss Percentage by Host Name",
        labels={"Packetloss(%)": "Packet Loss (%)"},
        template="plotly_dark",
        color="Packetloss(%)",
        color_continuous_scale=["green", "yellow", "orange", "red"],
    )
    packet_loss_fig.update_layout(margin={"l": 40, "r": 20, "t": 40, "b": 30})

    # Latency Graph
    latency_fig = px.bar(
        filtered_df, x="Host_name", y="Latency(msec)",
        title="Latency by Host Name",
        labels={"Latency(msec)": "Latency (ms)"},
        template="plotly_dark",
        color="Latency(msec)",
        color_continuous_scale=["green", "yellow", "orange", "red"],
    )
    latency_fig.update_layout(margin={"l": 40, "r": 20, "t": 40, "b": 30})

    # Availability Graph
    availability_fig = px.bar(
        filtered_df, x="Host_name", y="Availability-%",
        title="Availability by Host Name",
        labels={"Availability-%": "Availability (%)"},
        template="plotly_dark",
        color="Availability-%",
        color_continuous_scale=["red", "orange", "yellow", "green"],
    )
    availability_fig.update_layout(margin={"l": 40, "r": 20, "t": 40, "b": 30})

    return dropdown_options, packet_loss_fig, latency_fig, availability_fig

if __name__ == '__main__':
    app.run_server(host='0.0.0.0', port=8080)
