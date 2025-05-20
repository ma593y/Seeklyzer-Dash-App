import re
import time
from typing import Dict, List, Optional, Any
import dash
from dash import html, dcc, Input, Output, State, callback
import dash_bootstrap_components as dbc
from langchain_xai import ChatXAI
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
                try:
                    # Try to parse if it's already a string representation of JSON
                    df[col] = df[col].apply(lambda x: json.loads(x) if isinstance(x, str) and x.strip().startswith('{') else x)
                except:
                    # If parsing fails, keep as is
                    pass
        print("Available columns:", df.columns.tolist())
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
    
    # Debug print
    print("Job data columns:", job_data.index.tolist())
    print("Extracted Details available:", "Extracted Details" in job_data)
    print("Extracted Details content:", job_data["Extracted Details"])
    
    # Define sections and their fields
    sections = {
        "Basic Information": [
            ("Job ID", "Job Id"),
            ("Job Title", "Job Title"),
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
    
    # Create accordion items for each section
    accordion_items = []
    
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
                        html.Div([
                            dcc.Markdown(
                                children=replace_heading_with_strong(job_data[field]),
                                className="job-description",
                                dangerously_allow_html=True
                            )
                        ])
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
            accordion_items.append(
                dbc.AccordionItem(
                    section_content,
                    title=section_title,
                    item_id=f"section-{section_title.lower().replace(' ', '-')}",
                    className="border-0"
                )
            )
    
    # Handle Extracted Details separately
    if "Extracted Details" in job_data and job_data["Extracted Details"]:
        try:
            extracted_details = job_data["Extracted Details"]
            if isinstance(extracted_details, str):
                extracted_details = json.loads(extracted_details)
            
            section_content = []
            
            # Process each category
            categories = {
                "Key Responsibilities & Duties": "key_responsibilities_duties",
                "Essential Qualifications & Experience": "essential_qualifications_experience",
                "Skills & Competencies": "skills_competencies"
            }
            
            for label, field in categories.items():
                if field in extracted_details and extracted_details[field]:
                    items = []
                    for item in extracted_details[field]:
                        bullet_point = item.get('bullet_point', '')
                        assessment = item.get('assessment_instructions', '')
                        
                        item_content = html.Div([
                            html.Div([
                                html.I(className="fas fa-circle text-primary me-2"),
                                html.Span(bullet_point)
                            ], className="mb-2"),
                            html.Div([
                                html.I(className="fas fa-info-circle text-info me-2"),
                                html.Span(assessment, className="text-muted")
                            ], className="ms-4 mb-3")
                        ])
                        items.append(item_content)
                    
                    if items:
                        section_content.append(
                            html.Div([
                                html.H6(label, className="mb-3"),
                                html.Div(items, className="ms-3")
                            ])
                        )
            
            if section_content:
                accordion_items.append(
                    dbc.AccordionItem(
                        section_content,
                        title="Extracted Details",
                        item_id="section-extracted-details",
                        className="border-0"
                    )
                )
        except Exception as e:
            print(f"Error processing Extracted Details: {e}")

    # Add Resume Assessment section
    accordion_items.append(
        dbc.AccordionItem(
            html.Div([
                html.Div(id="resume-assessment-content", children=[
                    html.Div([
                        html.I(className="fas fa-file-alt text-primary me-2"),
                        html.Span("Upload your resume to see how well it matches this job's requirements")
                    ], className="text-center p-4")
                ])
            ]),
            title="Resume Assessment",
            item_id="section-resume-assessment",
            className="border-0"
        )
    )
    
    # Create the accordion with all items
    content.append(
        dbc.Accordion(
            accordion_items,
            active_item=[f"section-{title.lower().replace(' ', '-')}" for title in sections.keys()] + ["section-extracted-details", "section-resume-assessment"],
            className="mt-3",
            always_open=True
        )
    )
    
    return content

def assess_resume_against_requirements(resume_text: str, job_requirements: dict) -> dict:
    print(resume_text)
    print(job_requirements)

    ########################################################################################
    # This is a template that will be enhanced with actual XAI implementation

    # Initialize ChatXAI
    chat_xai = ChatXAI(api_key=os.environ.get("XAI_API_KEY"), model="grok-3-mini-beta", temperature=0, max_tokens=4096)
    print("ChatXAI initialized with grok-3-mini-beta model")
    
    system_prompt = "You are an expert in IT recruitment and resume evaluation, with deep knowledge of IT roles, skills, and qualifications. Your role is to objectively and accurately assess resumes against job descriptions, following provided instructions precisely. Use a professional, concise, and neutral tone, ensuring all outputs are structured as specified, typically in JSON format. Base your assessments solely on the provided job description JSON and resume text, without making external assumptions or adding unverified information. Handle errors gracefully, returning clear JSON error messages for invalid or missing inputs. Maintain consistency with standard IT recruitment practices, focusing on relevancy, technical accuracy, and alignment with job requirements."
    human_prompt = f"""

    You are an expert in resume evaluation for IT roles. Your task is to assess a provided resume against a JSON-formatted IT job description (JD) containing three sections: `key_responsibilities_duties`, `essential_qualifications_experience`, and `skills_competencies`. Each section is a list of objects with `bullet_point` (the requirement) and `assessment_instructions` (guidance for resume evaluation). For each bullet point, assign a relevancy score between 0 and 1 (continuous scale, e.g., 0.3, 0.7) based on how well the resume matches the requirement, using the assessment instructions. Calculate a score out of 100 for each section by averaging the bullet point scores and multiplying by 100. Compute an overall score out of 100 by averaging the section scores. Follow the instructions below to ensure accurate, concise, and practical assessment, focusing on IT-specific context as seen in real-world recruitment:

    1. **Key Responsibilities / Duties**
    - For each bullet point (e.g., "Develop web applications using Python"), use the assessment instructions (e.g., "Review the resume's work experience for roles or projects involving Python") to evaluate the resume's work experience, projects, or achievements.
    - Assign a relevancy score (0-1) based on specificity and alignment:
        - 0.8-1.0: Explicit match (e.g., resume lists exact task or outcome).
        - 0.5-0.7: Partial match (e.g., related experience or similar outcomes).
        - 0.1-0.4: Minimal relevance (e.g., broad experience but not specific).
        - 0: No relevant experience or outcomes.
    - Consider quantifiable achievements (e.g., "improved performance by 15%") when assessing outcomes.

    2. **Essential Qualifications & Experience**
    - For each bullet point (e.g., "Essential: Bachelor's in Computer Science" or "Preferred: 5+ years in cloud administration"), use the assessment instructions to check the resume's education, certifications, work history, or projects.
    - Assign a relevancy score (0-1):
        - Essential qualifications: 0.8-1.0 for full match, 0.5-0.7 for partial (e.g., related degree), 0.1-0.4 for minimal relevance, 0 for absent.
        - Preferred qualifications: 0.5-0.7 for full match, 0.3-0.4 for partial, 0 for absent (lower weight to reflect preference).
    - For experience, evaluate duration and relevance (e.g., 6 years for 5+ years required scores higher than 3 years).

    3. **Skills & Competencies**
    - For each bullet point (e.g., "Hard Skills: Python, AWS" or "Soft Skills: Problem-solving, Agile teamwork"), use the assessment instructions to check the resume's skills section, job descriptions, or achievements.
    - Assign a relevancy score (0-1):
        - Hard Skills: 0.8-1.0 for exact skills, 0.5-0.7 for related skills (e.g., Java for Python), 0.1-0.4 for general technical skills, 0 for none.
        - Soft Skills: 0.8-1.0 for explicit evidence (e.g., "Led Agile team"), 0.5-0.7 for implied (e.g., general teamwork), 0.1-0.4 for weak evidence, 0 for none.
    - Consider multiple skills in a single bullet point (e.g., "Python, AWS") by averaging their individual relevancy.

    **Output Format**:
    Provide the assessment results in JSON format with four keys:
    - `key_responsibilities_duties`: List of objects with `bullet_point`, `assessment_instructions`, and `relevancy_score` (0-1).
    - `essential_qualifications_experience`: List of objects with `bullet_point`, `assessment_instructions`, and `relevancy_score` (0-1).
    - `skills_competencies`: List of objects with `bullet_point`, `assessment_instructions`, and `relevancy_score` (0-1).
    - `scores`: Object with `key_responsibilities_duties_score`, `essential_qualifications_experience_score`, `skills_competencies_score` (each out of 100), and `overall_score` (average of section scores, out of 100).

    Ensure all strings are properly escaped to avoid JSON formatting issues. Round relevancy scores to two decimal places and section/overall scores to one decimal place. If the resume or JD JSON is missing or invalid, return a JSON object with a single key `error` describing the issue. Ensure the tone is professional and the assessment is concise, reflecting standard IT recruitment practices.

    **Example Output**:

    ```json
    {{
    "key_responsibilities_duties": [
        {{
        "bullet_point": "Develop and maintain web applications using Node.js",
        "assessment_instructions": "Review the resume's work experience for roles or projects involving Node.js or similar web development technologies.",
        "relevancy_score": 0.90
        }},
        {{
        "bullet_point": "Ensure network security through regular audits and updates",
        "assessment_instructions": "Look for achievements in the resume's work experience related to network security or audits, such as implementing security protocols.",
        "relevancy_score": 0.80
        }}
    ],
    "essential_qualifications_experience": [
        {{
        "bullet_point": "Essential: Bachelor's degree in Information Technology or related field",
        "assessment_instructions": "Check the resume's education section for a Bachelor's degree in IT or a related field.",
        "relevancy_score": 1.00
        }},
        {{
        "bullet_point": "Essential: 3+ years in software development or network administration",
        "assessment_instructions": "Review the resume's work history to confirm at least 3 years in relevant software development or network administration roles.",
        "relevancy_score": 0.80
        }},
        {{
        "bullet_point": "Preferred: Master's degree in Computer Science",
        "assessment_instructions": "Check the resume's education section for a Master's degree in Computer Science.",
        "relevancy_score": 0.70
        }},
        {{
        "bullet_point": "Preferred: Experience with cloud-based environments like AWS or Azure",
        "assessment_instructions": "Look for cloud-related experience (e.g., AWS, Azure) in the resume's work history or projects.",
        "relevancy_score": 0.60
        }}
    ],
    "skills_competencies": [
        {{
        "bullet_point": "Hard Skills: Node.js, AWS, firewall management",
        "assessment_instructions": "Check the resume's skills section or job descriptions for proficiency in Node.js, AWS, and firewall management.",
        "relevancy_score": 0.90
        }},
        {{
        "bullet_point": "Soft Skills: Problem-solving, technical communication, Agile teamwork",
        "assessment_instructions": "Look for evidence in the resume's job duties or achievements, such as resolving technical issues, communicating with stakeholders, or working in Agile teams.",
        "relevancy_score": 0.75
        }}
    ],
    "scores": {{
        "key_responsibilities_duties_score": 85.0,
        "essential_qualifications_experience_score": 77.5,
        "skills_competencies_score": 82.5,
        "overall_score": 81.7
    }}
    }}
    ```

    **Error Output Examples**:

    ```json
    {{
    "error": "Both a valid JSON job description and a resume are required for assessment"
    }}
    ```

    ```json
    {{
    "error": "Invalid JSON format in job description"
    }}
    ```

    **Input**:
    ============JOB DESCRIPTION JSON============
    {job_requirements}
    ============JOB DESCRIPTION JSON============
    ============RESUME============
    {resume_text}
    ============RESUME============

    **Task**:
    Analyze the provided JSON-formatted IT job description and resume text. Assess the resume against each bullet point in the JD JSON, assigning a relevancy score (0-1) based on the assessment instructions. Calculate section scores (average bullet point scores × 100) and an overall score (average section scores). Output the results in JSON format with bullet point scores, section scores, and the overall score. If the input is missing or invalid, return a JSON error object.

    """

    messages = [
        ("system", system_prompt),
        ("human", human_prompt)
    ]

    # Make the API call directly
    print("Sending request to ChatXAI API...")
    start_time = time.time()
    response = chat_xai.invoke(messages)
    processing_time = time.time() - start_time
    print(f"Response received in {processing_time:.2f} seconds")
    print(response.content)
    return response.content
    ########################################################################################

    return {
        "overall_match_score": 0.0,
        "category_scores": {
            "key_responsibilities": 0.0,
            "qualifications": 0.0,
            "skills": 0.0
        },
        "detailed_assessment": {
            "key_responsibilities": [],
            "qualifications": [],
            "skills": []
        },
        "missing_requirements": {
            "key_responsibilities": [],
            "qualifications": [],
            "skills": []
        },
        "recommendations": []
    }

@callback(
    Output("resume-assessment-content", "children"),
    [Input("resume-store", "data"),
     Input("job-details-modal", "is_open")],
    [State("job-grid", "cellRendererData")],
    prevent_initial_call=True
)
def update_resume_assessment(resume_data, is_modal_open, cell_data):
    if not is_modal_open or not resume_data or not cell_data:
        return html.Div([
            html.I(className="fas fa-file-alt text-primary me-2"),
            html.Span("Upload your resume to see how well it matches this job's requirements")
        ], className="text-center p-4")
    
    try:
        # Get job requirements from the current job
        job_id = cell_data.get("value", {}).get("data", {}).get("Job Id")
        if not job_id:
            return html.Div("Error: Could not find job details", className="text-danger")
        
        df = load_job_data()
        job_data = df[df["Job Id"] == job_id].iloc[0]
        
        if "Extracted Details" not in job_data:
            return html.Div("Error: Job requirements not available", className="text-danger")
        
        # Get resume content from stored data
        content_string = resume_data['content']
        if ',' in content_string:
            content_type, content_string = content_string.split(',', 1)
        else:
            content_string = content_string
        
        decoded = base64.b64decode(content_string)
        
        # Convert resume to text
        resume_text = decoded.decode('utf-8')
        
        # Get job requirements
        job_requirements = job_data["Extracted Details"]
        if isinstance(job_requirements, str):
            job_requirements = json.loads(job_requirements)
        
        # Assess resume against requirements
        assessment_response = assess_resume_against_requirements(resume_text, job_requirements)
        
        # Parse the assessment response as JSON
        try:
            assessment = json.loads(assessment_response)
        except json.JSONDecodeError:
            print(f"Error parsing assessment response: {assessment_response}")
            return html.Div([
                html.I(className="fas fa-exclamation-circle text-danger me-2"),
                html.Span("Error processing resume assessment")
            ], className="text-center text-danger p-4")
        
        # Create assessment display
        return html.Div([
            # Overall match score
            html.Div([
                html.H5("Overall Match Score", className="mb-3"),
                html.Div([
                    html.Div([
                        html.Div(
                            className="progress-bar bg-success",
                            style={"width": f"{assessment['scores']['overall_score']}%"}
                        )
                    ], className="progress", style={"height": "25px"}),
                    html.Div(
                        f"{assessment['scores']['overall_score']}%",
                        className="text-center mt-2"
                    )
                ], className="mb-4")
            ]),
            
            # Category scores
            html.Div([
                html.H5("Category Scores", className="mb-3"),
                html.Div([
                    html.Div([
                        html.Strong("Key Responsibilities: "),
                        f"{assessment['scores']['key_responsibilities_duties_score']}%"
                    ], className="mb-2"),
                    html.Div([
                        html.Strong("Qualifications: "),
                        f"{assessment['scores']['essential_qualifications_experience_score']}%"
                    ], className="mb-2"),
                    html.Div([
                        html.Strong("Skills: "),
                        f"{assessment['scores']['skills_competencies_score']}%"
                    ], className="mb-2")
                ], className="ms-3")
            ], className="mb-4"),
            
            # Detailed assessment
            html.Div([
                html.H5("Detailed Assessment", className="mb-3"),
                html.Div([
                    html.Div([
                        html.H6("Key Responsibilities", className="mb-2"),
                        html.Div([
                            html.Div([
                                html.I(className="fas fa-circle text-primary me-2"),
                                html.Span(item["bullet_point"]),
                                html.Div([
                                    html.I(className="fas fa-info-circle text-info me-2"),
                                    html.Span(f"Match: {item['relevancy_score']*100:.1f}%", className="text-muted")
                                ], className="ms-4")
                            ], className="mb-2")
                            for item in assessment["key_responsibilities_duties"]
                        ], className="ms-3")
                    ], className="mb-3"),
                    
                    html.Div([
                        html.H6("Qualifications", className="mb-2"),
                        html.Div([
                            html.Div([
                                html.I(className="fas fa-circle text-primary me-2"),
                                html.Span(item["bullet_point"]),
                                html.Div([
                                    html.I(className="fas fa-info-circle text-info me-2"),
                                    html.Span(f"Match: {item['relevancy_score']*100:.1f}%", className="text-muted")
                                ], className="ms-4")
                            ], className="mb-2")
                            for item in assessment["essential_qualifications_experience"]
                        ], className="ms-3")
                    ], className="mb-3"),
                    
                    html.Div([
                        html.H6("Skills", className="mb-2"),
                        html.Div([
                            html.Div([
                                html.I(className="fas fa-circle text-primary me-2"),
                                html.Span(item["bullet_point"]),
                                html.Div([
                                    html.I(className="fas fa-info-circle text-info me-2"),
                                    html.Span(f"Match: {item['relevancy_score']*100:.1f}%", className="text-muted")
                                ], className="ms-4")
                            ], className="mb-2")
                            for item in assessment["skills_competencies"]
                        ], className="ms-3")
                    ], className="mb-3")
                ])
            ])
        ])
        
    except Exception as e:
        print(f"Error in resume assessment: {e}")
        return html.Div([
            html.I(className="fas fa-exclamation-circle text-danger me-2"),
            html.Span("Error processing resume assessment")
        ], className="text-center text-danger p-4")

# Layout with AG Grid and Modal
layout = dbc.Container([
    # Add dcc.Store for resume data
    dcc.Store(id='resume-store', storage_type='local'),
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
    [Input('resume-store', 'data'),
     Input('upload-resume', 'contents')],
    [State('upload-resume', 'filename')]
)
def update_resume_status(resume_data, contents, filename):
    ctx = dash.callback_context
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else None
    
    # If triggered by resume-store (page load or resume data change)
    if trigger_id == 'resume-store':
        if resume_data:
            return html.Div([
                html.I(className="fas fa-check-circle text-success me-2"),
                f"Resume uploaded: {resume_data['filename']}"
            ], className="text-center"), ""
        return html.Div([
            'Drag and Drop or ',
            html.A('Select Resume')
        ]), ""
    
    # If triggered by new upload
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
    [Output('upload-resume', 'children', allow_duplicate=True),
     Output('resume-upload-status', 'children', allow_duplicate=True),
     Output('resume-store', 'data')],
    Input('upload-resume', 'contents'),
    State('upload-resume', 'filename'),
    prevent_initial_call=True
)
def store_resume_data(contents, filename):
    if contents is None:
        return dash.no_update, dash.no_update, None
    
    content_type, content_string = contents.split(',')
    
    try:
        if filename.endswith(('.pdf', '.docx', '.doc', '.txt')):
            resume_data = {
                'filename': filename,
                'content': content_string,
                'content_type': content_type
            }
            return dash.no_update, dash.no_update, resume_data
        else:
            return dash.no_update, dash.no_update, None
    except Exception as e:
        return dash.no_update, dash.no_update, None

@callback(
    Output("collapse-resume", "is_open"),
    [Input("collapse-resume-button", "n_clicks")],
    [State("collapse-resume", "is_open")],
)
def toggle_resume_collapse(n, is_open):
    if n:
        return not is_open
    return is_open