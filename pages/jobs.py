import dash
from dash import html, dcc, callback, dash_table, Input, Output, State
import dash_bootstrap_components as dbc
import pandas as pd
import os
from datetime import datetime

# Constants
DEFAULT_PAGE_SIZE = 10
PAGE_SIZE_OPTIONS = [
    {"label": "10 items", "value": "10"},
    {"label": "25 items", "value": "25"},
    {"label": "50 items", "value": "50"},
    {"label": "100 items", "value": "100"},
]

# Column configurations
DISPLAY_COLUMNS = [
    "Job Id", "Job Title", "Work Arrangement", "Work Type", 
    "Posting Date", "Salary Range", "Company Name", "Location", "Actions"
]

COLUMN_FORMATS = {
    "Job Title": "25%",
    "Company Name": "20%",
    "Location": "15%",
    "Work Type": "10%",
    "Work Arrangement": "10%",
    "Posting Date": "10%",
    "Salary Range": "10%",
    "Actions": "10%"
}

# Register the page
dash.register_page(
    __name__,
    path='/jobs',
    title='Seeklyzer - Job Finder',
    name='Job Finder'
)

def load_job_data():
    """Load and preprocess job data from parquet file."""
    file_path = "data/preprocessed_seek_jobs_files/preprocessed_seek_jobs_plus_json.parquet"
    if not os.path.exists(file_path):
        return pd.DataFrame({"Error": ["File not found. Please run the job preprocessing script first."]})
    
    try:
        df = pd.read_parquet(file_path)
        # Select only the columns we want to display
        columns = [col for col in DISPLAY_COLUMNS+["Job Url"] if col in df.columns]
        
        # Format dates if they exist
        if "Posting Date" in df.columns:
            df["Posting Date"] = pd.to_datetime(df["Posting Date"]).dt.strftime("%Y-%m-%d")
        
        return df[columns]
    except Exception as e:
        return pd.DataFrame({"Error": [f"Failed to load data: {str(e)}"]})

def create_job_modal_content(job):
    """Create the content for the job details modal."""
    if not job:
        return html.Div("No job data available", className="text-center p-4")
    
    # Helper function to safely get job data
    def get_job_value(key, default="N/A"):
        value = job.get(key, default)
        return value if value and value != "nan" else default
    
    return [
        dbc.Row([
            dbc.Col([
                html.H3(get_job_value("Job Title"), className="mb-3"),
                html.H5(get_job_value("Company Name"), className="text-muted mb-4"),
            ], width=12),
        ]),
        
        dbc.Row([
            dbc.Col([
                html.Div([
                    html.H5("Job Details", className="mb-3"),
                    dbc.ListGroup([
                        dbc.ListGroupItem([
                            html.Strong("Location: "),
                            get_job_value("Location")
                        ]),
                        dbc.ListGroupItem([
                            html.Strong("Work Type: "),
                            get_job_value("Work Type")
                        ]),
                        dbc.ListGroupItem([
                            html.Strong("Work Arrangement: "),
                            get_job_value("Work Arrangement")
                        ]),
                        dbc.ListGroupItem([
                            html.Strong("Posted: "),
                            get_job_value("Posting Date")
                        ]),
                        dbc.ListGroupItem([
                            html.Strong("Salary: "),
                            get_job_value("Salary Range")
                        ]),
                    ], flush=True),
                ], className="mb-4"),
            ], md=6),
            
            dbc.Col([
                html.Div([
                    html.H5("Highlights", className="mb-3"),
                    dbc.ListGroup([
                        dbc.ListGroupItem(get_job_value("Highlight Point 1")) if get_job_value("Highlight Point 1") != "N/A" else None,
                        dbc.ListGroupItem(get_job_value("Highlight Point 2")) if get_job_value("Highlight Point 2") != "N/A" else None,
                        dbc.ListGroupItem(get_job_value("Highlight Point 3")) if get_job_value("Highlight Point 3") != "N/A" else None,
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
                            children=get_job_value("Job Description", "No description available."),
                            dangerously_allow_html=True
                        )
                    ], style={
                        "maxHeight": "400px",
                        "overflowY": "auto",
                        "padding": "15px",
                        "border": "1px solid #dee2e6",
                        "borderRadius": "4px",
                        "backgroundColor": "#f8f9fa"
                    }),
                ], className="mb-4"),
            ], width=12),
        ]),
        
        dbc.Row([
            dbc.Col([
                html.Div([
                    html.Hr(),
                    html.A(
                        "View on Seek",
                        href=get_job_value("Job Url", "#"),
                        target="_blank",
                        rel="noopener noreferrer",
                        className="btn btn-primary mt-3"
                    ) if get_job_value("Job Url") != "N/A" else None,
                ], className="text-center"),
            ], width=12),
        ]),
    ]

# Layout
layout = dbc.Container([
    html.H1("Job Finder", className="text-center my-4"),
    
    # Hidden components for modal trigger
    dcc.Store(id="selected-job-id", data=None),
    
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
                debounce=True
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
                            options=PAGE_SIZE_OPTIONS,
                            value=str(DEFAULT_PAGE_SIZE),
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
    dcc.Store(id="page-store", data={"current_page": 0, "page_size": DEFAULT_PAGE_SIZE}),
    
], fluid=True)

@callback(
    Output("job-data-store", "data"),
    Output("job-data-status", "children"),
    Input("job-search-input", "value"),
    prevent_initial_call=False
)
def load_and_filter_data(search_term):
    """Load and filter job data based on search term."""
    df = load_job_data()
    
    if "Error" in df.columns:
        return None, dbc.Alert(df["Error"].iloc[0], color="danger", className="mt-3")
    
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
    """Update pagination state based on user interactions."""
    ctx = dash.callback_context
    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
    
    if current_state is None:
        current_state = {"current_page": 0, "page_size": DEFAULT_PAGE_SIZE}
    
    page_size = int(page_size)
    if page_size != current_state["page_size"]:
        return {"current_page": 0, "page_size": page_size}
    
    if not job_data:
        return current_state
    
    max_page = max(0, (len(job_data) - 1) // page_size)
    
    if trigger_id == "next-page-button" and current_state["current_page"] < max_page:
        current_state["current_page"] += 1
    elif trigger_id == "previous-page-button" and current_state["current_page"] > 0:
        current_state["current_page"] -= 1
    elif trigger_id == "job-data-store":
        current_state["current_page"] = 0
    
    return current_state

@callback(
    Output("page-indicator", "children"),
    Input("page-store", "data"),
    Input("job-data-store", "data")
)
def update_page_indicator(page_state, job_data):
    """Update the page indicator text."""
    if not job_data or not page_state:
        return "Page 1"
    
    current_page = page_state["current_page"] + 1
    total_pages = max(1, (len(job_data) - 1) // page_state["page_size"] + 1)
    
    return f"Page {current_page} of {total_pages}"

@callback(
    Output("job-table-container", "children"),
    Input("page-store", "data"),
    Input("job-data-store", "data")
)
def update_data_table(page_state, job_data):
    """Update the data table with paginated data."""
    if not job_data or not page_state:
        return html.Div("No data available. Please run the job preprocessing script first.")
    
    if len(job_data) == 0:
        return html.Div("No jobs found matching your search criteria.")
    
    page_size = page_state["page_size"]
    current_page = page_state["current_page"]
    
    start_idx = current_page * page_size
    end_idx = min(start_idx + page_size, len(job_data))
    page_data = job_data[start_idx:end_idx]
    
    if not page_data:
        return html.Div("No jobs available on this page. Try going back to page 1.")
    
    # Create the data table
    return dash_table.DataTable(
        id='job-listing-table',
        columns=[
            {"name": col, "id": col} for col in DISPLAY_COLUMNS if col != "Actions"
        ] + [{
            "name": "Actions",
            "id": "Actions",
            "type": "text",
            "presentation": "markdown"
        }],
        data=[{
            **row,
            "Actions": f'[View Details](#{row["Job Id"]}) | [View on Seek]({row.get("Job Url", "#")})'
        } for row in page_data],
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
            } for col_id, width in COLUMN_FORMATS.items() if col_id in DISPLAY_COLUMNS
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
        page_action='none',
        row_selectable=False,
        cell_selectable=True,
        selected_rows=[],
        tooltip_delay=0,
        tooltip_duration=None,
        css=[{
            'selector': '.dash-cell div.dash-cell-value',
            'rule': 'display: inline; white-space: inherit; overflow: inherit; text-overflow: inherit;'
        }],
        markdown_options={"html": True}
    )

@callback(
    Output("job-detail-modal", "is_open"),
    Output("job-modal-content", "children"),
    Output("selected-job-id", "data"),
    Input("job-listing-table", "active_cell"),
    Input("close-job-modal", "n_clicks"),
    State("job-data-store", "data"),
    State("job-detail-modal", "is_open"),
    State("page-store", "data"),
    prevent_initial_call=True
)
def handle_modal_interaction(active_cell, close_clicks, job_data, is_open, page_state):
    """Handle modal interactions based on table cell clicks."""
    ctx = dash.callback_context
    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
    
    if trigger_id == "close-job-modal":
        return False, dash.no_update, dash.no_update
    
    if trigger_id == "job-listing-table" and active_cell:
        if not job_data:
            return False, html.Div("No data available"), dash.no_update
        
        # Only proceed if the clicked cell is in the Actions column
        if active_cell["column_id"] != "Actions":
            return is_open, dash.no_update, dash.no_update
        
        # Get the row data for the clicked cell
        row_idx = active_cell["row"]
        page_size = page_state.get("page_size", 10)
        current_page = page_state.get("current_page", 0)
        
        # Calculate the actual index in the full dataset
        start_idx = current_page * page_size
        actual_idx = start_idx + row_idx
        
        if actual_idx >= len(job_data):
            return False, html.Div("Invalid job selection"), dash.no_update
        
        job = job_data[actual_idx]
        return True, create_job_modal_content(job), job["Job Id"]
    
    return is_open, dash.no_update, dash.no_update