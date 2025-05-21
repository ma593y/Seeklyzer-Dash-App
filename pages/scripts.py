import dash
from dash import html, dcc, Input, Output, State, callback
import dash_bootstrap_components as dbc
import subprocess
import os
import json
from datetime import datetime
import sys

# Get the path to the virtual environment's Python interpreter
venv_python = os.path.join(os.path.dirname(sys.executable), 'python.exe')

# Register the page
dash.register_page(
    __name__,
    path='/scripts',
    title='Seeklyzer - Scripts',
    name='Scripts'
)

# Layout
layout = dbc.Container([
    html.H1("Data Processing Scripts", className="text-center my-4"),
    
    # Center content with 60% width
    dbc.Row([
        dbc.Col([
            # Script 1: Job Fetching and Preprocessing
            dbc.Card([
                dbc.CardHeader([
                    html.H4("Step 1: Fetch and Preprocess Job Data", className="mb-0 text-center")
                ]),
                dbc.CardBody([
                    html.P([
                        "This script fetches job listings from the API and preprocesses them into a structured format.",
                        html.Br(),
                        "Output files will be saved in the 'data/preprocessed_seek_jobs_files/' directory."
                    ], className="mb-3 text-center"),
                    html.Div([
                        dbc.Button(
                            [html.I(className="fas fa-play me-2"), "Run Script"],
                            id="run-fetch-script",
                            color="primary",
                            className="mb-3"
                        )
                    ], className="text-center"),
                    html.Div(id="fetch-script-output", className="mt-3")
                ])
            ], className="mb-4"),
            
            # Script 2: JSON Extraction
            dbc.Card([
                dbc.CardHeader([
                    html.H4("Step 2: Extract Job Details", className="mb-0 text-center")
                ]),
                dbc.CardBody([
                    html.P([
                        "This script processes the preprocessed job data to extract structured information from job descriptions.",
                        html.Br(),
                        "Requires Step 1 to be completed first."
                    ], className="mb-3 text-center"),
                    html.Div([
                        dbc.Button(
                            [html.I(className="fas fa-play me-2"), "Run Script"],
                            id="run-extract-script",
                            color="primary",
                            className="mb-3",
                            disabled=True
                        )
                    ], className="text-center"),
                    html.Div(id="extract-script-output", className="mt-3")
                ])
            ])
        ], width=6)  # Set width to 6 (50% of 12 columns) and center it
    ], justify="center"),  # Center the row
    
    # Store for script status
    dcc.Store(id='script-status-store', data={
        'fetch_completed': False,
        'extract_completed': False
    })
], fluid=True)

@callback(
    [Output("fetch-script-output", "children"),
     Output("run-extract-script", "disabled"),
     Output("script-status-store", "data")],
    Input("run-fetch-script", "n_clicks"),
    State("script-status-store", "data"),
    prevent_initial_call=True
)
def run_fetch_script(n_clicks, status):
    if not n_clicks:
        return dash.no_update, dash.no_update, dash.no_update
        
    try:
        # Run the script using the virtual environment's Python interpreter
        process = subprocess.Popen(
            [venv_python, 'script_seek_jobs_fetching_preprocessing.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Get output
        stdout, stderr = process.communicate()
        
        # Check if script completed successfully
        if process.returncode == 0:
            # Update status
            status['fetch_completed'] = True
            
            # Create success message
            output = html.Div([
                html.Div([
                    html.I(className="fas fa-check-circle text-success me-2"),
                    "Script completed successfully!"
                ], className="alert alert-success"),
                html.Div([
                    html.H6("Output:", className="mt-3"),
                    html.Pre(stdout, className="bg-light p-3 rounded")
                ])
            ])
            
            return output, False, status
        else:
            # Create error message
            output = html.Div([
                html.Div([
                    html.I(className="fas fa-exclamation-circle text-danger me-2"),
                    "Script failed!"
                ], className="alert alert-danger"),
                html.Div([
                    html.H6("Error:", className="mt-3"),
                    html.Pre(stderr, className="bg-light p-3 rounded")
                ])
            ])
            
            return output, True, status
            
    except Exception as e:
        # Create error message
        output = html.Div([
            html.Div([
                html.I(className="fas fa-exclamation-circle text-danger me-2"),
                "Error running script!"
            ], className="alert alert-danger"),
            html.Div([
                html.H6("Error:", className="mt-3"),
                html.Pre(str(e), className="bg-light p-3 rounded")
            ])
        ])
        
        return output, True, status

@callback(
    Output("extract-script-output", "children"),
    Input("run-extract-script", "n_clicks"),
    State("script-status-store", "data"),
    prevent_initial_call=True
)
def run_extract_script(n_clicks, status):
    if not n_clicks or not status.get('fetch_completed'):
        return dash.no_update
        
    try:
        # Run the script using the virtual environment's Python interpreter
        process = subprocess.Popen(
            [venv_python, 'script_seek_jobs_assessment_json_extraction.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Get output
        stdout, stderr = process.communicate()
        
        # Check if script completed successfully
        if process.returncode == 0:
            # Update status
            status['extract_completed'] = True
            
            # Create success message
            output = html.Div([
                html.Div([
                    html.I(className="fas fa-check-circle text-success me-2"),
                    "Script completed successfully!"
                ], className="alert alert-success"),
                html.Div([
                    html.H6("Output:", className="mt-3"),
                    html.Pre(stdout, className="bg-light p-3 rounded")
                ])
            ])
            
            return output
        else:
            # Create error message
            output = html.Div([
                html.Div([
                    html.I(className="fas fa-exclamation-circle text-danger me-2"),
                    "Script failed!"
                ], className="alert alert-danger"),
                html.Div([
                    html.H6("Error:", className="mt-3"),
                    html.Pre(stderr, className="bg-light p-3 rounded")
                ])
            ])
            
            return output
            
    except Exception as e:
        # Create error message
        output = html.Div([
            html.Div([
                html.I(className="fas fa-exclamation-circle text-danger me-2"),
                "Error running script!"
            ], className="alert alert-danger"),
            html.Div([
                html.H6("Error:", className="mt-3"),
                html.Pre(str(e), className="bg-light p-3 rounded")
            ])
        ])
        
        return output

@callback(
    Output("fetch-script-output", "children", allow_duplicate=True),
    Input("run-fetch-script", "n_clicks"),
    prevent_initial_call=True
)
def show_fetch_processing(n_clicks):
    if not n_clicks:
        return dash.no_update
        
    return html.Div([
        html.Div([
            html.I(className="fas fa-spinner fa-spin me-2"),
            "Processing... Please wait."
        ], className="alert alert-info")
    ])

@callback(
    Output("extract-script-output", "children", allow_duplicate=True),
    Input("run-extract-script", "n_clicks"),
    prevent_initial_call=True
)
def show_extract_processing(n_clicks):
    if not n_clicks:
        return dash.no_update
        
    return html.Div([
        html.Div([
            html.I(className="fas fa-spinner fa-spin me-2"),
            "Processing... Please wait."
        ], className="alert alert-info")
    ])