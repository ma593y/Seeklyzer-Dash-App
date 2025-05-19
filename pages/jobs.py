import dash
from dash import html, dcc
import dash_bootstrap_components as dbc
import pandas as pd
from dash_ag_grid import AgGrid
import json
from dash import Input, Output, State, callback

# Register the page
dash.register_page(
    __name__,
    path='/jobs',
    title='Seeklyzer - Job Finder',
    name='Job Finder'
)

def load_job_data():
    """Load and preprocess job data from parquet file."""
    try:
        df = pd.read_parquet("data/preprocessed_seek_jobs_files/preprocessed_seek_jobs_plus_json.parquet")
        # Convert JSON columns to strings for display
        for col in df.columns:
            if df[col].dtype == 'object':
                df[col] = df[col].apply(lambda x: json.dumps(x) if isinstance(x, (dict, list)) else str(x))
        return df
    except Exception as e:
        print(f"Error loading data: {e}")
        return pd.DataFrame()

def create_job_grid():
    """Create and configure the AG Grid component for job listings."""
    df = load_job_data()
    if df.empty:
        return dbc.Alert("No data available", color="warning")
    
    # Filter for specific columns
    columns_to_show = [
        'Job Id', 'Role Id', 'Job Title', 'Work Arrangement', 
        'Work Type', 'Posting Date', 'Salary Range', 
        'Company Name', 'Advertiser Name', 'Location'
    ]
    df = df[columns_to_show]
    
    # Define column definitions
    columnDefs = [{"field": col, "filter": True, "sortable": True} for col in df.columns]
    
    # Add action column with both View on Seek and View Details buttons
    columnDefs.append({
        "field": "actions",
        "headerName": "Actions",
        "sortable": False,
        "filter": False,
        "cellRenderer": "ActionButtons",
        "width": "auto",
        "marginLeft": "10px",
        "marginRight": "10px",
        "flex": 0
    })
    
    return AgGrid(
        id="job-grid",
        rowData=df.to_dict("records"),
        columnDefs=columnDefs,
        defaultColDef={
            "resizable": True,
            "sortable": True,
            "filter": True,
            "minWidth": 100,
            "flex": 1,
        },
        dashGridOptions={
            "rowHeight": 48,
            "headerHeight": 48,
            "pagination": True,
            "paginationPageSize": 20,
        },
        style={"height": "700px", "width": "100%"},
    )

def create_job_details_modal():
    """Create the modal component for displaying job details."""
    return dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle("Job Details")),
        dbc.ModalBody(id="job-details-content"),
        dbc.ModalFooter(
            dbc.Button("Close", id="close-modal", className="ms-auto", n_clicks=0)
        ),
    ], id="job-details-modal", size="lg", is_open=False)

def create_job_details_content(row_data):
    """Create the content for the job details modal."""
    return [
        html.H4(row_data["Job Title"]),
        html.Hr(),
        html.Div([
            html.P([html.Strong("Company: "), row_data["Company Name"]]),
            html.P([html.Strong("Location: "), row_data["Location"]]),
            html.P([html.Strong("Work Type: "), row_data["Work Type"]]),
            html.P([html.Strong("Work Arrangement: "), row_data["Work Arrangement"]]),
            html.P([html.Strong("Salary Range: "), row_data["Salary Range"]]),
            html.P([html.Strong("Posting Date: "), row_data["Posting Date"]]),
        ])
    ]

# Layout with AG Grid and Modal
layout = dbc.Container([
    html.H1("Job Finder", className="text-center my-4"),
    create_job_grid(),
    create_job_details_modal()
], fluid=True)

@callback(
    Output("job-details-modal", "is_open"),
    Output("job-details-content", "children"),
    Input("job-grid", "cellRendererData"),
    Input("close-modal", "n_clicks"),
    State("job-details-modal", "is_open"),
)
def toggle_modal(cell_data, n_clicks, is_open):
    """Handle modal interactions for displaying job details."""
    ctx = dash.callback_context
    if not ctx.triggered:
        return is_open, []
    
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    # Handle modal close
    if trigger_id == "close-modal":
        return False, []
    
    # Handle job details view
    if trigger_id == "job-grid" and cell_data:
        if cell_data.get("value", {}).get("colId") == "details":
            row_data = cell_data.get("value", {}).get("data", {})
            if row_data:
                return True, create_job_details_content(row_data)
    
    return is_open, []