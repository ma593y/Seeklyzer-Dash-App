import dash
from dash import html, dcc, callback, dash_table, Input, Output, State
import dash_bootstrap_components as dbc
import pandas as pd
import os
from datetime import datetime

# Register the page
dash.register_page(
    __name__,
    path='/jobs',
    title='Seeklyzer - Job Finder',
    name='Job Finder'
)

# Function to load the data
def load_job_data():
    file_path = "data/preprocessed_seek_jobs_files/preprocessed_seek_jobs_plus_json.parquet"
    if os.path.exists(file_path):
        try:
            df = pd.read_parquet(file_path)
            # Select only the columns we want to display
            columns = [
                "Job Id", "Role Id", "Job Title", "Work Arrangement", "Work Type", 
                "Posting Date", "Salary Range", "Company Name", "Advertiser Name", 
                "Location", "Job Teaser", "Highlights", "Highlight Point 1", 
                "Highlight Point 2", "Highlight Point 3", "Job Description", "Job Url"
            ]
            # Only keep columns that exist in the DataFrame
            columns = [col for col in columns if col in df.columns]
            
            # Format dates if they exist
            if "Posting Date" in df.columns:
                df["Posting Date"] = pd.to_datetime(df["Posting Date"]).dt.strftime("%Y-%m-%d")
            
            return df[columns]
        except Exception as e:
            print(f"Error loading parquet file: {e}")
            return pd.DataFrame({"Error": [f"Failed to load data: {e}"]})
    else:
        print(f"File not found: {file_path}")
        return pd.DataFrame({"Error": ["File not found. Please run the job preprocessing script first."]})

# Layout
layout = dbc.Container([
    html.H1("Job Finder", className="text-center my-4"),
    
    # File status alert
    html.Div(id="job-data-status"),
    
    # Search and filter controls
    dbc.Row([
        dbc.Col([
            dbc.Input(
                id="job-search-input",
                type="text",
                placeholder="Search jobs...",
                className="mb-3",
                debounce=True  # Enable debouncing for better performance
            ),
        ], width=12),
    ]),
    
    # Data table with loading spinner
    dbc.Spinner(
        html.Div(id="job-table-container", className="mb-4"),
        color="primary",
        type="border",
        fullscreen=False
    ),
    
    # Pagination controls
    dbc.Row([
        dbc.Col([
            dbc.Row([
                # Page size selector
                dbc.Col([
                    dbc.InputGroup([
                        dbc.InputGroupText("Page Size"),
                        dbc.Select(
                            id="page-size-selector",
                            options=[
                                {"label": "10 items", "value": "10"},
                                {"label": "25 items", "value": "25"},
                                {"label": "50 items", "value": "50"},
                                {"label": "100 items", "value": "100"},
                            ],
                            value="10",
                            className="flex-grow-0",
                            style={"width": "120px"}
                        ),
                    ], className="mb-3 justify-content-center"),
                ], width="auto", className="me-3"),
                
                # Navigation buttons
                dbc.Col([
                    dbc.InputGroup([
                        dbc.Button("Previous", id="previous-page-button", color="secondary", outline=True),
                        dbc.InputGroupText(id="page-indicator", children="Page 1"),
                        dbc.Button("Next", id="next-page-button", color="secondary", outline=True),
                    ], className="mb-3 justify-content-center"),
                ], width="auto"),
            ], justify="center"),
        ], width=12, className="text-center"),
    ]),
    
    # Job details modal
    dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle("Job Details")),
        dbc.ModalBody(id="job-modal-content"),
        dbc.ModalFooter(
            dbc.Button("Close", id="close-job-modal", className="ms-auto", n_clicks=0)
        ),
    ], id="job-detail-modal", size="xl", is_open=False),
    
    # Store components for state management
    dcc.Store(id="job-data-store"),
    dcc.Store(id="page-store", data={"current_page": 0, "page_size": 10}),
    
], fluid=True)

# Callback to load and store job data
@callback(
    Output("job-data-store", "data"),
    Output("job-data-status", "children"),
    Input("job-search-input", "value"),
    prevent_initial_call=False
)
def load_and_filter_data(search_term):
    df = load_job_data()
    
    if "Error" in df.columns:
        return None, dbc.Alert(df["Error"].iloc[0], color="danger", className="mt-3")
    
    # Filter data if search term is provided
    if search_term:
        # Convert all columns to string for searching
        df_str = df.astype(str)
        # Search across all columns
        mask = df_str.apply(lambda x: x.str.contains(search_term, case=False, na=False)).any(axis=1)
        filtered_df = df[mask]
        
        if len(filtered_df) == 0:
            return df.to_dict('records'), dbc.Alert(
                f"No results found for '{search_term}'. Showing all {len(df)} jobs instead.", 
                color="warning", 
                className="mt-3"
            )
        
        return filtered_df.to_dict('records'), dbc.Alert(
            f"Found {len(filtered_df)} jobs matching '{search_term}'", 
            color="success", 
            className="mt-3"
        )
    
    return df.to_dict('records'), dbc.Alert(
        f"Loaded {len(df)} jobs. Use the search box to filter results.", 
        color="info", 
        className="mt-3",
        dismissable=True
    )

# Callback to update pagination state
@callback(
    Output("page-store", "data"),
    [
        Input("next-page-button", "n_clicks"),
        Input("previous-page-button", "n_clicks"),
        Input("page-size-selector", "value"),
        Input("job-data-store", "data")
    ],
    State("page-store", "data"),
    prevent_initial_call=True
)
def update_pagination(next_clicks, prev_clicks, page_size, job_data, current_state):
    # Get the ID of the component that triggered the callback
    ctx = dash.callback_context
    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
    
    # Initialize state if it doesn't exist
    if current_state is None:
        current_state = {"current_page": 0, "page_size": 10}
    
    # Update page size if changed
    page_size = int(page_size)
    if page_size != current_state["page_size"]:
        current_state["page_size"] = page_size
        current_state["current_page"] = 0  # Reset to first page
        return current_state
    
    # Handle navigation buttons
    if trigger_id == "next-page-button" and job_data:
        max_page = max(0, (len(job_data) - 1) // page_size)
        if current_state["current_page"] < max_page:
            current_state["current_page"] += 1
    
    elif trigger_id == "previous-page-button":
        if current_state["current_page"] > 0:
            current_state["current_page"] -= 1
    
    # If job data changes, reset to first page
    elif trigger_id == "job-data-store":
        current_state["current_page"] = 0
    
    return current_state

# Callback to update the page indicator
@callback(
    Output("page-indicator", "children"),
    Input("page-store", "data"),
    Input("job-data-store", "data")
)
def update_page_indicator(page_state, job_data):
    if not job_data or not page_state:
        return "Page 1"
    
    current_page = page_state["current_page"] + 1  # 1-indexed for display
    total_pages = max(1, (len(job_data) - 1) // page_state["page_size"] + 1)
    
    return f"Page {current_page} of {total_pages}"

# Callback to update the data table
@callback(
    Output("job-table-container", "children"),
    Input("page-store", "data"),
    Input("job-data-store", "data")
)
def update_data_table(page_state, job_data):
    if not job_data or not page_state:
        return html.Div("No data available. Please run the job preprocessing script first.")
    
    if len(job_data) == 0:
        return html.Div("No jobs found matching your search criteria.")
    
    page_size = page_state["page_size"]
    current_page = page_state["current_page"]
    
    # Calculate start and end indices for current page
    start_idx = current_page * page_size
    end_idx = min(start_idx + page_size, len(job_data))
    
    # Get data for current page
    page_data = job_data[start_idx:end_idx]
    
    # Check if page_data is empty (this could happen if pagination state is inconsistent)
    if not page_data:
        return html.Div("No jobs available on this page. Try going back to page 1.")
    
    # Display shorter preview versions of certain columns
    display_columns = [
        "Job Id", "Job Title", "Work Arrangement", "Work Type", 
        "Posting Date", "Salary Range", "Company Name", "Location"
    ]
    
    # Create a list of available columns from actual data
    available_columns = list(page_data[0].keys())
    # Only keep columns that are in our display list and in the available data
    display_columns = [col for col in display_columns if col in available_columns]
    
    # Define column formatting
    column_formats = {
        "Job Title": "25%",
        "Company Name": "20%",
        "Location": "15%",
        "Work Type": "10%",
        "Work Arrangement": "10%",
        "Posting Date": "10%",
        "Salary Range": "10%",
    }
    
    # Create the data table
    return dash_table.DataTable(
        id='job-listing-table',
        columns=[{"name": col, "id": col} for col in display_columns],
        data=page_data,
        style_table={'overflowX': 'auto'},
        style_cell={
            'textAlign': 'left',
            'padding': '8px',
            'overflow': 'hidden',
            'textOverflow': 'ellipsis',
            'whiteSpace': 'nowrap',
        },
        style_cell_conditional=[
            {
                'if': {'column_id': col_id},
                'width': width
            } for col_id, width in column_formats.items() if col_id in display_columns
        ],
        style_header={
            'backgroundColor': 'rgb(230, 230, 230)',
            'fontWeight': 'bold',
            'border': '1px solid black'
        },
        style_data_conditional=[
            {
                'if': {'row_index': 'odd'},
                'backgroundColor': 'rgb(248, 248, 248)'
            },
            {
                'if': {'state': 'active'},
                'backgroundColor': 'rgb(230, 230, 230)',
                'border': '1px solid rgb(0, 0, 0)'
            },
            {
                'if': {'state': 'selected'},
                'backgroundColor': 'rgb(200, 200, 200)',
                'border': '1px solid rgb(0, 0, 0)'
            }
        ],
        page_action='none',  # We're handling pagination ourselves
        row_selectable='single',
        selected_rows=[],
        tooltip_delay=0,
        tooltip_duration=None,
        css=[{
            'selector': '.dash-cell div.dash-cell-value',
            'rule': 'display: inline; white-space: inherit; overflow: inherit; text-overflow: inherit;'
        }]
    )

# Callback to open job details modal when a row is selected
@callback(
    Output("job-detail-modal", "is_open"),
    Output("job-modal-content", "children"),
    Input("job-listing-table", "selected_rows"),
    Input("close-job-modal", "n_clicks"),
    State("job-data-store", "data"),
    State("page-store", "data"),
    State("job-detail-modal", "is_open"),
    prevent_initial_call=True
)
def toggle_job_modal(selected_rows, close_clicks, job_data, page_state, is_open):
    ctx = dash.callback_context
    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
    
    # Close modal button clicked
    if trigger_id == "close-job-modal":
        return False, dash.no_update
    
    # Row selected
    elif trigger_id == "job-listing-table" and selected_rows:
        if not job_data or not page_state:
            return False, html.Div("No data available")
        
        # Calculate the actual index in the full dataset
        page_size = page_state["page_size"]
        current_page = page_state["current_page"]
        row_idx = current_page * page_size + selected_rows[0]
        
        if row_idx >= len(job_data):
            return False, html.Div("Invalid selection")
        
        # Get the selected job data
        job = job_data[row_idx]
        
        # Create the modal content with better formatting
        content = [
            dbc.Row([
                dbc.Col([
                    html.H3(job.get("Job Title", "No Title"), className="mb-3"),
                    html.H5(job.get("Company Name", "N/A"), className="text-muted mb-4"),
                ], width=12),
            ]),
            
            dbc.Row([
                dbc.Col([
                    html.Div([
                        html.H5("Job Details", className="mb-3"),
                        dbc.ListGroup([
                            dbc.ListGroupItem([
                                html.Strong("Location: "),
                                job.get("Location", "N/A")
                            ]),
                            dbc.ListGroupItem([
                                html.Strong("Work Type: "),
                                job.get("Work Type", "N/A")
                            ]),
                            dbc.ListGroupItem([
                                html.Strong("Work Arrangement: "),
                                job.get("Work Arrangement", "N/A")
                            ]),
                            dbc.ListGroupItem([
                                html.Strong("Posted: "),
                                job.get("Posting Date", "N/A")
                            ]),
                            dbc.ListGroupItem([
                                html.Strong("Salary: "),
                                job.get("Salary Range", "N/A")
                            ]),
                        ], flush=True),
                    ], className="mb-4"),
                ], md=6),
                
                dbc.Col([
                    html.Div([
                        html.H5("Highlights", className="mb-3"),
                        dbc.ListGroup([
                            dbc.ListGroupItem(job.get("Highlight Point 1", "")) if job.get("Highlight Point 1") else None,
                            dbc.ListGroupItem(job.get("Highlight Point 2", "")) if job.get("Highlight Point 2") else None,
                            dbc.ListGroupItem(job.get("Highlight Point 3", "")) if job.get("Highlight Point 3") else None,
                        ], flush=True),
                    ], className="mb-4"),
                ], md=6),
            ], className="mb-4"),
            
            dbc.Row([
                dbc.Col([
                    html.Div([
                        html.H5("Job Description", className="mb-3"),
                        html.Div([
                            dcc.Markdown(
                                children=job.get("Job Description", "No description available."),
                                dangerously_allow_html=True
                            )
                        ], style={"maxHeight": "400px", "overflowY": "auto", "padding": "15px", "border": "1px solid #dee2e6", "borderRadius": "4px"}),
                    ], className="mb-4"),
                ], width=12),
            ]),
            
            # Job URL if available
            dbc.Row([
                dbc.Col([
                    html.Div([
                        html.Hr(),
                        html.A("View on Seek", href=job.get("Job Url", "#"), target="_blank",
                              className="btn btn-primary mt-3") if "Job Url" in job else None,
                    ], className="text-center"),
                ], width=12),
            ]),
        ]
        
        return True, content
    
    return is_open, dash.no_update