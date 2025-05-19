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
        'Job Id', 'Job Title', 'Work Arrangement', 
        'Work Type', 'Posting Date', 'Advertiser Name', 'Location'
    ]
    df = df[columns_to_show]
    
    # Define column definitions
    columnDefs = []
    for col in df.columns:
        if col == 'Advertiser Name':
            columnDefs.append({
                "field": col,
                "headerName": "Company Name",
                "filter": True,
                "sortable": True,
                "width": 200,
                "minWidth": 150,
                "flex": 1
            })
        elif col == 'Job Title':
            columnDefs.append({
                "field": col,
                "filter": True,
                "sortable": True,
                "width": 270,
                "minWidth": 200,
                "flex": 2
            })
        elif col == 'Location':
            columnDefs.append({
                "field": col,
                "filter": True,
                "sortable": True,
                "width": 150,
                "minWidth": 120,
                "flex": 1
            })
        elif col == 'Work Type':
            columnDefs.append({
                "field": col,
                "filter": True,
                "sortable": True,
                "width": 150,
                "minWidth": 150,
                "flex": 0
            })
        elif col == 'Work Arrangement':
            columnDefs.append({
                "field": col,
                "filter": True,
                "sortable": True,
                "width": 180,
                "minWidth": 180,
                "flex": 0
            })
        elif col == 'Posting Date':
            columnDefs.append({
                "field": col,
                "filter": True,
                "sortable": True,
                "width": 200,
                "minWidth": 200,
                "flex": 1
            })
        elif col == 'Job Id':
            columnDefs.append({
                "field": col,
                "filter": True,
                "sortable": True,
                "width": 100,
                "minWidth": 80,
                "flex": 0
            })
        else:
            columnDefs.append({
                "field": col,
                "filter": True,
                "sortable": True,
                "width": 150,
                "minWidth": 100,
                "flex": 1
            })
    
    # Add action column with both View on Seek and View Details buttons
    columnDefs.append({
        "field": "actions",
        "headerName": "Actions",
        "sortable": False,
        "filter": False,
        "cellRenderer": "ActionButtons",
        "width": 200,
        "minWidth": 200,
        "flex": 1
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
            "domLayout": "autoHeight",
            "animateRows": True,
            "rowSelection": "single",
            "enableCellTextSelection": True,
            "ensureDomOrder": True,
            "suppressCellFocus": False,
            "headerClass": "ag-header-cell-custom",
            "rowClass": "ag-row-custom"
        },
        style={
            "height": "700px",
            "width": "100%",
            "fontFamily": "Arial, sans-serif",
            "fontSize": "14px"
        },
        className="ag-theme-alpine",
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
    # Get fresh data from the DataFrame
    df = load_job_data()
    job_id = row_data["Job Id"]
    job_data = df[df["Job Id"] == job_id].iloc[0]
    
    return [
        html.H4(job_data["Job Title"]),
        html.Hr(),
        html.Div([
            html.P([html.Strong("Job ID: "), str(job_data["Job Id"])]),
            html.P([html.Strong("Role ID: "), str(job_data["Role Id"])]),
            html.P([html.Strong("Company: "), job_data["Company Name"]]),
            html.P([html.Strong("Advertiser: "), job_data["Advertiser Name"]]),
            html.P([html.Strong("Location: "), job_data["Location"]]),
            html.P([html.Strong("Work Type: "), job_data["Work Type"]]),
            html.P([html.Strong("Work Arrangement: "), job_data["Work Arrangement"]]),
            html.P([html.Strong("Posting Date: "), job_data["Posting Date"]]),
            html.P([html.Strong("Salary Range: "), job_data["Salary Range"]]),
            html.Hr(),
            html.H5("Job Teaser"),
            html.P(job_data["Job Teaser"]),
            html.Hr(),
            html.H5("Highlights"),
            html.P(job_data["Highlights"]),
            html.Div([
                html.P([html.Strong("Highlight 1: "), job_data["Highlight Point 1"]]),
                html.P([html.Strong("Highlight 2: "), job_data["Highlight Point 2"]]),
                html.P([html.Strong("Highlight 3: "), job_data["Highlight Point 3"]]),
            ]),
            html.Hr(),
            html.H5("Job Description"),
            html.P(job_data["Job Description"])
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