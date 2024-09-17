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
uploaded_data = {}

# Layout with file upload, dropdown, and multiple graphs
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
                    multiple=True
                ),
            ], width=12),
        ]),
        dbc.Row([ 
            dbc.Col([ 
                html.Label("Filter by Host Name:", style={"margin-top": "20px"}), 
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

# Callback to handle file upload and update hostnames
@app.callback(
    Output('hostname-dropdown', 'options'),
    Input('upload-csv', 'contents'),
    State('upload-csv', 'filename')
)
def update_hostnames(csv_content, filename):
    global uploaded_data
    if csv_content is not None:
        for content, name in zip(csv_content, filename):
            content_type, content_string = content.split(',')
            decoded = base64.b64decode(content_string)
            df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
            cleaned_df = clean_data(df)
            uploaded_data[name] = cleaned_df  # Save cleaned data in global variable

        # Get unique hostnames for the dropdown
        combined_df = pd.concat(uploaded_data.values(), ignore_index=True)
        unique_hostnames = combined_df['Host_name'].unique()

        return [{'label': hostname, 'value': hostname} for hostname in unique_hostnames]

    return []

# Callback to update graphs based on selected hostnames
@app.callback(
    [Output('packet-loss-graph', 'figure'),
     Output('latency-graph', 'figure'),
     Output('availability-graph', 'figure')],
    Input('hostname-dropdown', 'value')
)
def update_graphs(selected_hostnames):
    global uploaded_data
    if not uploaded_data or not selected_hostnames:
        return {}, {}, {}

    # Filter data based on selected hostnames
    combined_df = pd.concat(uploaded_data.values(), ignore_index=True)
    filtered_df = combined_df[combined_df['Host_name'].isin(selected_hostnames)]

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
    
    return packet_loss_fig, latency_fig, availability_fig

# Callback to clear uploaded data and reset the graphs
@app.callback(
    [Output('packet-loss-graph', 'figure'),
     Output('latency-graph', 'figure'),
     Output('availability-graph', 'figure'),
     Output('hostname-dropdown', 'options')],
    Input('clear-data-btn', 'n_clicks')
)
def clear_uploaded_data(n_clicks):
    global uploaded_data
    if n_clicks:
        uploaded_data = {}  # Clear uploaded data
        return {}, {}, {}, []
    return {}, {}, {}, []

if __name__ == '__main__':
    app.run_server(host='0.0.0.0', port=8080)
