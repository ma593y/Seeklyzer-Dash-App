import re
from typing import Dict, List, Optional, Any
import dash
from dash import html, dcc, Input, Output, State, callback
import dash_bootstrap_components as dbc
import pandas as pd
from dash_ag_grid import AgGrid
import json
import os
from datetime import datetime, timedelta
import base64
import io

# Register the page
dash.register_page(
    __name__,
    path='/jobs',
    title='Seeklyzer - Job Finder',
    name='Job Finder'
)

def load_job_data() -> pd.DataFrame:
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

#############################################

from langchain_openai import OpenAI


# Extraction function using a single text template
def extract_filters(user_query: str) -> dict:
    base_prompt = """
    You are a data‐extraction assistant. A user will give you a free-text job-search query, and you must extract any filter values they mention for these six fields:

    • Job Title  
    • Work Arrangement  
    • Work Type  
    • Posting Date  
    • Company Name  
    • Location  

    Return exactly one JSON object with these keys:
    ```

    {{
    "job_title":         <string or null>,
    "work_arrangement":  <string or null>,
    "work_type":         <string or null>,
    "posting_date":      <string or null>,
    "company_name":      <string or null>,
    "location":          <string or null>
    }}

    ```

    Rules:
    1. **Job Title**, **Company Name**, **Location**: return the exact string(s) mentioned, or `null`.  
    2. **Work Arrangement**: normalize to one of `On-site`, `Remote`, or `Hybrid`; if multiple, comma-separate; else `null`.  
    3. **Work Type**: normalize to one of `Full time`, `Part time`, `Contract/Temp`, or `Casual/Vacation`; if multiple, comma-separate; else `null`.  
    4. **Posting Date**: 
    - If they say a single relative time (e.g. "2 days ago", "yesterday"), return the number of days ago as an integer (`0` = today, `1` = yesterday, etc.).
    - If unspecified, set to `null`.  
    5. If the user mentions multiple values for a field, join them with commas in a single string.  
    6. Do not output any extra keys, explanation, or formatting—only the JSON.

    Example:
    ```

    User query:
    "I'm hunting Hybrid UX Designer gigs, Full time or Contract/Temp, posted 2 days ago at Initech in New York."

    Returned JSON:
    {{
    "job_title":         "UX Designer",
    "work_arrangement":  "Hybrid, On-site"
    "work_type":         "Full time, Contract/Temp",
    "posting_date":      "2",
    "company_name":      "Initech",
    "location":          "New York"
    }}

    ```

    Now process the following input and extract the filters:

    User query:
    "{user_query}"
    """

    llm = OpenAI(temperature=0, openai_api_key=os.environ.get('OPENAI_API_KEY'))
    prompt = base_prompt.format(user_query=user_query)
    raw_output = llm.invoke(prompt)
    raw_output = raw_output.replace("Returned JSON:", "").strip()
    json_output = json.loads(raw_output)
    
    print(json.dumps(json_output, indent=4))
    
    return json_output

#############################################


def get_column_definitions() -> List[Dict[str, Any]]:
    return [
        {
            "field": "Job Id",
            "filter": True,
            "sortable": True,
            "width": 100,
            "minWidth": 80,
            "flex": 0
        },
        {
            "field": "Job Title",
            "filter": True,
            "sortable": True,
            "width": 270,
            "minWidth": 200,
            "flex": 2
        },
        {
            "field": "Advertiser Name",
            "headerName": "Company Name",
            "filter": True,
            "sortable": True,
            "width": 200,
            "minWidth": 150,
            "flex": 1
        },
        {
            "field": "Location",
            "filter": True,
            "sortable": True,
            "width": 150,
            "minWidth": 120,
            "flex": 1
        },
        {
            "field": "Work Type",
            "filter": True,
            "sortable": True,
            "width": 150,
            "minWidth": 150,
            "flex": 0
        },
        {
            "field": "Work Arrangement",
            "filter": True,
            "sortable": True,
            "width": 180,
            "minWidth": 180,
            "flex": 0
        },
        {
            "field": "Posting Date",
            "filter": True,
            "sortable": True,
            "width": 200,
            "minWidth": 200,
            "flex": 1
        },
        {
            "field": "actions",
            "headerName": "Actions",
            "sortable": False,
            "filter": False,
            "cellRenderer": "ActionButtons",
            "width": 200,
            "minWidth": 200,
            "flex": 1
        }
    ]

def create_job_grid(df: pd.DataFrame = None) -> AgGrid:
    if df is None:
        df = load_job_data()
    if df.empty:
        return dbc.Alert("No data available", color="warning")
    
    # Filter for specific columns
    columns_to_show = [
        'Job Id', 'Job Title', 'Work Arrangement', 
        'Work Type', 'Posting Date', 'Advertiser Name', 'Location'
    ]
    df = df[columns_to_show]
    
    return AgGrid(
        id="job-grid",
        rowData=df.to_dict("records"),
        columnDefs=get_column_definitions(),
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

def filter_dataframe(df: pd.DataFrame, filters: dict) -> pd.DataFrame:
    if not filters:
        return df
    
    filtered_df = df.copy()
    
    # Apply each filter if it exists
    if filters.get('job_title'):
        # Split job titles by comma and create a pattern that matches any of them
        job_titles = [title.strip() for title in filters['job_title'].split(',')]
        # Create a pattern that matches any of the job titles
        pattern = '|'.join(job_titles)
        filtered_df = filtered_df[filtered_df['Job Title'].str.contains(pattern, case=False, na=False)]
    
    if filters.get('work_arrangement'):
        arrangements = [arr.strip() for arr in filters['work_arrangement'].split(',')]
        filtered_df = filtered_df[filtered_df['Work Arrangement'].isin(arrangements)]
    
    if filters.get('work_type'):
        work_types = [wt.strip() for wt in filters['work_type'].split(',')]
        filtered_df = filtered_df[filtered_df['Work Type'].isin(work_types)]
    
    if filters.get('company_name'):
        filtered_df = filtered_df[filtered_df['Advertiser Name'].str.contains(filters['company_name'], case=False, na=False)]
    
    if filters.get('location'):
        # Split locations by comma and create a pattern that matches any of them
        locations = [loc.strip() for loc in filters['location'].split(',')]
        # Create a pattern that matches any of the locations
        pattern = '|'.join(locations)
        filtered_df = filtered_df[filtered_df['Location'].str.contains(pattern, case=False, na=False)]
    
    if filters.get('posting_date'):
        try:
            days_ago = int(filters['posting_date'])
            # Convert Posting Date column to datetime
            filtered_df['Posting Date'] = pd.to_datetime(filtered_df['Posting Date'])
            
            # If the dates are already timezone-aware, convert them to UTC
            if filtered_df['Posting Date'].dt.tz is not None:
                filtered_df['Posting Date'] = filtered_df['Posting Date'].dt.tz_convert('UTC')
            else:
                filtered_df['Posting Date'] = filtered_df['Posting Date'].dt.tz_localize('UTC')
            
            # Calculate the cutoff date (days_ago days from now) in UTC
            cutoff_date = pd.Timestamp.now(tz='UTC') - pd.Timedelta(days=days_ago)
            
            # Filter for jobs posted within the last X days
            filtered_df = filtered_df[filtered_df['Posting Date'] >= cutoff_date]
            
        except ValueError:
            print(f"Invalid posting_date value: {filters['posting_date']}")
    
    return filtered_df

def create_job_details_modal() -> dbc.Modal:
    return dbc.Modal([
        dbc.ModalHeader(
            dbc.ModalTitle("Job Details", className="text-primary"),
            close_button=True,
            className="border-bottom"
        ),
        dbc.ModalBody(
            id="job-details-content",
            className="p-4",
            style={"maxHeight": "70vh", "overflowY": "auto"}
        ),
        dbc.ModalFooter(
            dbc.Button(
                "Close",
                id="close-modal",
                className="ms-auto",
                color="secondary",
                n_clicks=0
            ),
            className="border-top"
        ),
    ], 
    id="job-details-modal",
    size="lg",
    is_open=False,
    backdrop="static",
    className="job-details-modal"
    )

from bs4 import BeautifulSoup

def replace_heading_with_strong(html_text):
    """
    Replace all heading tags (h1-h6) in the given HTML text by extracting their text
    and wrapping it in <strong> tags.

    :param html_text: HTML string containing heading tags
    :return: Modified HTML string with headings replaced by <strong>
    """
    soup = BeautifulSoup(html_text, 'html.parser')
    for level in range(1, 7):
        for tag in soup.find_all(f'h{level}'):
            strong_tag = soup.new_tag('strong')
            strong_tag.string = tag.get_text()
            tag.replace_with(strong_tag)
    return str(soup)

def create_job_details_content(row_data: Dict[str, Any]) -> List[html.Div]:
    # Get fresh data from the DataFrame
    df = load_job_data()
    job_id = row_data["Job Id"]
    job_data = df[df["Job Id"] == job_id].iloc[0]
    
    # Define sections and their fields
    sections = {
        "Basic Information": [
            ("Job ID", "Job Id"),
            ("Job Title", "Job Title"),
            # ("Role ID", "Role Id"),
            # ("Company", "Company Name"),
            ("Company", "Advertiser Name"),
            ("Location", "Location"),
            ("Work Type", "Work Type"),
            ("Work Arrangement", "Work Arrangement"),
            ("Salary Range", "Salary Range"),
            ("Posting Date", "Posting Date")
        ],
        "Job Overview": [
            ("Job Teaser", "Job Teaser"),
            ("Highlights", "Highlights")
        ],
        "Job Description": [
            ("Description", "Job Description")
        ]
    }
    
    content = []
    
    # Add job title at the top
    content.append(
        html.H4(job_data["Job Title"], className="mb-4 text-primary")
    )
    
    # Iterate through sections
    for section_title, fields in sections.items():
        section_content = []
        
        # Add fields that have data
        for label, field in fields:
            if field in job_data and job_data[field] and str(job_data[field]).strip():
                if field == "Highlights":
                    # Special handling for highlights
                    highlights = []
                    for i in range(1, 4):
                        highlight_key = f"Highlight Point {i}"
                        if highlight_key in job_data and job_data[highlight_key]:
                            highlights.append(
                                html.Div([
                                    html.I(className="fas fa-check-circle text-success me-2"),
                                    html.Span(job_data[highlight_key])
                                ], className="mb-2")
                            )
                    if highlights:
                        section_content.append(
                            html.Div([
                                html.H6(label, className="mb-3"),
                                html.Div(highlights, className="ms-3")
                            ])
                        )
                elif field == "Job Description":
                    # Special handling for Job Description to render HTML
                    section_content.append(
                        dcc.Markdown(
                            replace_heading_with_strong(job_data[field]),
                            className="job-description",
                            dangerously_allow_html=True
                        )
                    )
                else:
                    section_content.append(
                        html.Div([
                            html.Strong(f"{label}: ", className="text-muted"),
                            html.Span(str(job_data[field]))
                        ], className="mb-2")
                    )
        
        # Only add section if it has content
        if section_content:
            content.extend([
                html.Hr(className="my-4"),
                html.H5(section_title, className="mb-3 text-primary"),
                html.Div(section_content, className="ms-3")
            ])
    
    return content

# Layout with AG Grid and Modal
layout = dbc.Container([
    html.H1("Job Finder", className="text-center my-4"),
    dbc.Row([
        dbc.Col([
            dbc.InputGroup([
                dbc.Input(
                    id="search-input",
                    placeholder="Search jobs (e.g., 'Remote Software Engineer in New York posted last week')",
                    type="text",
                    className="form-control",
                    n_submit=0
                ),
                dbc.Button(
                    "Search",
                    id="search-button",
                    color="primary",
                    className="ms-2"
                ),
                dbc.Button(
                    "Clear",
                    id="clear-button",
                    color="secondary",
                    className="ms-2"
                ),
            ], className="mb-4")
        ], width=12)
    ]),
    dbc.Row([
        dbc.Col([
            html.Div([
                dbc.Button(
                    [html.I(className="fas fa-file-upload me-2"), "Upload Resume"],
                    id="collapse-resume-button",
                    className="mb-2",
                    color="primary",
                    n_clicks=0,
                    title="Upload Resume"
                ),
            ], className="text-center"),
            dbc.Collapse(
                dbc.Card(
                    dbc.CardBody([
                        dcc.Upload(
                            id='upload-resume',
                            children=html.Div([
                                'Drag and Drop or ',
                                html.A('Select Resume')
                            ]),
                            style={
                                'width': '100%',
                                'height': '60px',
                                'lineHeight': '60px',
                                'borderWidth': '1px',
                                'borderStyle': 'dashed',
                                'borderRadius': '5px',
                                'textAlign': 'center',
                                'margin': '10px 0',
                                'backgroundColor': '#f8f9fa',
                                'cursor': 'pointer'
                            },
                            multiple=False
                        ),
                        html.Div(id='resume-upload-status', className="mt-2")
                    ])
                ),
                id="collapse-resume",
                is_open=False,
            )
        ], width=12)
    ]),
    dbc.Spinner(
        html.Div(id="job-grid-container", children=create_job_grid()),
        spinner_style={"width": "3rem", "height": "3rem"},
        color="primary",
        type="border",
        fullscreen=False,
        delay_show=0
    ),
    create_job_details_modal()
], fluid=True)

@callback(
    [Output("job-grid-container", "children"),
     Output("search-input", "value")],
    [Input("search-button", "n_clicks"),
     Input("search-input", "n_submit"),
     Input("clear-button", "n_clicks")],
    State("search-input", "value"),
    prevent_initial_call=True
)
def update_grid(n_clicks, n_submit, clear_clicks, search_query):
    ctx = dash.callback_context
    if not ctx.triggered:
        return create_job_grid(), dash.no_update
    
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if trigger_id == "clear-button":
        return create_job_grid(), ""
    
    if not search_query:
        return create_job_grid(), dash.no_update
    
    filters = extract_filters(search_query)
    df = load_job_data()
    filtered_df = filter_dataframe(df, filters)
    
    return create_job_grid(filtered_df), dash.no_update

@callback(
    Output("job-details-modal", "is_open"),
    Output("job-details-content", "children"),
    Input("job-grid", "cellRendererData"),
    Input("close-modal", "n_clicks"),
    State("job-details-modal", "is_open"),
)
def toggle_modal(cell_data: Optional[Dict[str, Any]], n_clicks: int, is_open: bool) -> tuple[bool, List[html.Div]]:
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

@callback(
    [Output('upload-resume', 'children'),
     Output('resume-upload-status', 'children')],
    Input('upload-resume', 'contents'),
    State('upload-resume', 'filename')
)
def update_resume_status(contents, filename):
    if contents is None:
        return html.Div([
            'Drag and Drop or ',
            html.A('Select Resume')
        ]), ""
    
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    
    try:
        if filename.endswith('.pdf'):
            return html.Div([
                html.I(className="fas fa-check-circle text-success me-2"),
                f"Resume uploaded: {filename}"
            ], className="text-center"), ""
        elif filename.endswith('.docx') or filename.endswith('.doc'):
            return html.Div([
                html.I(className="fas fa-check-circle text-success me-2"),
                f"Resume uploaded: {filename}"
            ], className="text-center"), ""
        elif filename.endswith('.txt'):
            return html.Div([
                html.I(className="fas fa-check-circle text-success me-2"),
                f"Resume uploaded: {filename}"
            ], className="text-center"), ""
        else:
            return html.Div([
                html.I(className="fas fa-exclamation-circle text-danger me-2"),
                "Please upload a PDF, Word document, or text file"
            ], className="text-center text-danger"), ""
    except Exception as e:
        return html.Div([
            html.I(className="fas fa-exclamation-circle text-danger me-2"),
            "Error processing file"
        ], className="text-center text-danger"), ""

@callback(
    Output("collapse-resume", "is_open"),
    [Input("collapse-resume-button", "n_clicks")],
    [State("collapse-resume", "is_open")],
)
def toggle_resume_collapse(n, is_open):
    if n:
        return not is_open
    return is_open