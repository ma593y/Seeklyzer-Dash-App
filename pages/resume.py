import base64
import io
import json
import re
import os
import datetime
import dash
import PyPDF2
from dash import html, dcc, callback, Input, Output, State
import dash_bootstrap_components as dbc
from langchain_xai import ChatXAI

# Import from components instead of from app
from components import create_processing_alert

# Register the page
dash.register_page(
    __name__,
    path='/resume',
    title='Seeklyzer - Resume Tool',
    name='Resume Tool'
)

# Define layout
layout = dbc.Container([
    html.H1("Resume Tool", className="text-center my-4"),
    html.H5("Upload > Parse > Format > Save / Download", className="text-center my-4"),
    
    dbc.Card([
        dbc.CardHeader([
            html.H4("Upload a PDF file", className="d-inline-block")
        ]),
        dbc.CardBody([
            dcc.Upload(
                id='upload-pdf',
                children=html.Div(
                    ['Drag and Drop or ', html.A('Select a PDF File')],
                    id='upload-content'
                ),
                style={
                    'width': '100%',
                    'height': '60px',
                    'lineHeight': '60px',
                    'borderWidth': '1px',
                    'borderStyle': 'dashed',
                    'borderRadius': '5px',
                    'textAlign': 'center',
                    'margin': '10px'
                },
                multiple=False
            ),
            html.Div(id="upload-alert-container", className="mt-2"),
            html.Div([
                dbc.Button("Parse Resume", id="parse-button", color="primary", className="mt-3")
            ], className="text-center"),
        ])
    ], className="mb-3"),
    
    dbc.Card([
        dbc.CardHeader([
            html.H4("Extracted Text", className="d-inline-block")
        ]),
        dbc.CardBody([
            html.Div(id="parse-alert-container", className="mb-2"),
            html.Div(id='output-content')
        ])
    ]),
    
    html.Div([
        dbc.Button("Format Text", id="format-button", color="info", className="mt-3")
    ], className="text-center mb-3"),
    
    # Store components for data management
    dcc.Store(id="raw-text-store"),
    dcc.Store(id="formatted-text-store"),
    
    dbc.Card([
        dbc.CardHeader([
            html.H4("Formatted Resume", className="d-inline-block")
        ]),
        dbc.CardBody([
            html.Div(id="format-alert-container", className="mb-2"),
            html.Div(id='formatted-content')
        ])
    ], className="mt-3 mb-3"),
    
    html.Div([
        dbc.Button("Save Resume", id="save-button", color="success", className="me-2"),
        dbc.Button("Download Resume", id="download-button", color="secondary", className="me-2"),
        dbc.Button("Extract Data", id="extract-json-button", color="primary"),
        dcc.Download(id="download-text"),
        
        html.Div(id="save-alert-container", className="mt-2"),
        html.Div(id="download-alert-container", className="mt-2")
    ], className="text-center mt-3 mb-4"),
    
    # New JSON Extraction section
    dbc.Card([
        dbc.CardHeader([
            html.H4("Extract Resume Data as JSON", className="d-inline-block")
        ]),
        dbc.CardBody([
            html.Div(id="json-extract-alert-container", className="mb-2"),
            html.Div(id='json-content', style={
                'maxHeight': '400px',
                'overflow': 'auto'
            })
        ])
    ], className="mt-4 mb-3"),
    
    # JSON Save and Download section
    html.Div([
        dbc.Button("Save JSON", id="save-json-button", color="success", className="me-2"),
        dbc.Button("Download JSON", id="download-json-button", color="secondary"),
        dcc.Download(id="download-json"),
        
        html.Div(id="save-json-alert-container", className="mt-2"),
        html.Div(id="download-json-alert-container", className="mt-2")
    ], className="text-center mt-3 mb-4"),
    
    # Add store for JSON data
    dcc.Store(id="json-data-store"),
], fluid=True)

# Import all your callbacks from the original app.py
@callback(
    Output('upload-content', 'children'),
    Output('upload-pdf', 'style'),
    Output('upload-alert-container', 'children'),
    Input('upload-pdf', 'contents'),
    State('upload-pdf', 'filename'),
    prevent_initial_call=True
)
def update_upload_area(contents, filename):
    """Updates the upload area UI based on file selection and provides feedback via alerts."""
    if contents is None:
        print("[UPLOAD] No file selected")
        return ['Drag and Drop or ', html.A('Select a PDF File')], {
            'width': '100%',
            'height': '60px',
            'lineHeight': '60px',
            'borderWidth': '1px',
            'borderStyle': 'dashed',
            'borderRadius': '5px',
            'textAlign': 'center',
            'margin': '10px'
        }, None
    
    print(f"[UPLOAD] File selected: {filename}")
    
    if filename.lower().endswith('.pdf'):
        print("[UPLOAD] Valid PDF file detected")
        return [html.I(className="fas fa-file-pdf me-2"), f"Selected: {filename}"], {
            'width': '100%',
            'height': '60px',
            'lineHeight': '60px',
            'borderWidth': '2px',
            'borderStyle': 'solid',
            'borderColor': 'green',
            'borderRadius': '5px',
            'textAlign': 'center',
            'margin': '10px',
            'backgroundColor': '#f0fff0'
        }, dbc.Alert(
            f"PDF file '{filename}' selected successfully. Click 'Parse Resume' to extract text.",
            className="text-center",
            color="success",
            dismissable=True,
            is_open=True,
            duration=4000
        )
    else:
        print(f"[UPLOAD] Invalid file type: {filename}")
        return [html.I(className="fas fa-exclamation-triangle me-2"), f"Selected: {filename} (Not a PDF file)"], {
            'width': '100%',
            'height': '60px',
            'lineHeight': '60px',
            'borderWidth': '2px',
            'borderStyle': 'solid',
            'borderColor': '#ff7b00',
            'borderRadius': '5px',
            'textAlign': 'center',
            'margin': '10px',
            'backgroundColor': '#fff9f0'
        }, dbc.Alert(
            f"Warning: '{filename}' is not a PDF file. Only PDF files are supported.",
            className="text-center",
            color="warning",
            dismissable=True,
            is_open=True,
            duration=6000
        )

# Add all your other resume-related callbacks from app.py
# Parse callback
@callback(
    Output('output-content', 'children'),
    Output('raw-text-store', 'data'),
    Output('parse-alert-container', 'children'),
    Input('parse-button', 'n_clicks'),
    State('upload-pdf', 'contents'),
    State('upload-pdf', 'filename'),
    prevent_initial_call=True
)
def update_output(n_clicks, content, filename):
    """Processes the uploaded PDF file to extract text content with feedback."""
    if content is None:
        print("[PARSE] No file content available")
        return html.P("Please upload a PDF file before parsing.", className="text-center"), "", dbc.Alert(
            "No file selected. Please upload a PDF first.",
            className="text-center",
            color="danger",
            dismissable=True,
            is_open=True,
            duration=4000
        )

    if not filename.lower().endswith('.pdf'):
        print(f"[PARSE] File {filename} is not a PDF")
        return html.P("Please upload a PDF file.", className="text-center"), "", dbc.Alert(
            f"'{filename}' is not a PDF file. Please select a valid PDF.",
            className="text-center",
            color="warning",
            dismissable=True,
            is_open=True,
            duration=4000
        )
    
    print(f"[PARSE] Processing file: {filename}")
    
    try:
        content_type, content_string = content.split(',')
        decoded = base64.b64decode(content_string)
        print(f"[PARSE] Decoded {len(decoded)} bytes of data")
        
        pdf_file = io.BytesIO(decoded)
        reader = PyPDF2.PdfReader(pdf_file)
        page_count = len(reader.pages)
        print(f"[PARSE] PDF has {page_count} pages")
        
        text = ""
        for page_num in range(page_count):
            page = reader.pages[page_num]
            page_text = page.extract_text()
            text += page_text + "\n\n"
        
        text = re.sub(r'\s+', ' ', text).strip()
        print(f"[PARSE] Extracted {len(text)} characters")

        if text:
            success_alert = dbc.Alert(
                [
                    html.I(className="fas fa-check-circle me-2"),
                    f"Successfully extracted {len(text)} characters from {page_count} page{'s' if page_count != 1 else ''}."
                ],
                className="text-center",
                color="success",
                dismissable=True,
                is_open=True,
                duration=4000
            )
            
            return html.Div([
                html.H5(f"Filename: {filename}"),
                html.Hr(),
                html.Pre(text, style={
                    'whiteSpace': 'pre-wrap',
                    'wordBreak': 'break-word',
                    'maxHeight': '500px',
                    'overflow': 'auto'
                })
            ]), text, success_alert
        else:
            print("[PARSE] No text extracted from PDF")
            return html.P("No text could be extracted from this PDF. It may be scanned or contain only images."), "", dbc.Alert(
                "This PDF doesn't contain extractable text. It may be a scanned document or image-based PDF.",
                color="warning",
                dismissable=True,
                is_open=True,
                duration=6000
            )
    
    except Exception as e:
        print(f"[PARSE] Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return html.Div([
            html.H5("Error processing the file"),
            html.P(str(e))
        ]), "", dbc.Alert(
            [
                html.I(className="fas fa-exclamation-triangle me-2"), 
                f"Error processing PDF: {str(e)}"
            ],
            className="text-center",
            color="danger",
            dismissable=True,
            is_open=True,
            duration=8000
        )

# Format processing alert callback
@callback(
    Output('format-alert-container', 'children'),
    Input('format-button', 'n_clicks'),
    State('raw-text-store', 'data'),
    prevent_initial_call=True
)
def show_format_processing_alert(n_clicks, raw_text):
    """Shows a processing alert immediately when format button is clicked."""
    if raw_text:
        return create_processing_alert("Formatting resume with AI, please wait...")
    return dash.no_update

# Modify the format text callback to use a different output target:
@callback(
    Output('formatted-content', 'children'),
    Output('formatted-text-store', 'data'),
    Output('format-alert-container', 'children', allow_duplicate=True),
    Input('format-button', 'n_clicks'),
    State('raw-text-store', 'data'),
    prevent_initial_call=True
)
def format_text(n_clicks, raw_text):
    """Formats resume text using the ChatXAI API with detailed status feedback."""
    print("[FORMAT] Formatting request received")
    
    if not raw_text:
        print("[FORMAT] No raw text available")
        return html.P("No text available to format. Please parse a resume first.", className="text-center"), "", dbc.Alert(
            "No text to format. Please upload and parse a resume first.",
            className="text-center",
            color="warning",
            dismissable=True,
            is_open=True,
            duration=4000
        )
    
    try:
        print(f"[FORMAT] Processing {len(raw_text)} characters")
        
        # Show processing message at the beginning
        processing_message = f"Processing {len(raw_text)} characters with Grok-3-mini model..."
        
        api_key = os.environ.get("XAI_API_KEY")
        if not api_key:
            print("[FORMAT] API key missing")
            return html.Div([
                html.H5("API Key Missing"),
                html.P("Please set the XAI_API_KEY environment variable.")
            ]), "", dbc.Alert(
                [
                    html.I(className="fas fa-key me-2"),
                    "API Key not found. Please set the XAI_API_KEY environment variable to enable formatting."
                ],
                className="text-center",
                color="danger",
                dismissable=True,
                is_open=True,
                duration=0  # No auto-dismiss for this critical error
            )
        
        chat_xai = ChatXAI(api_key=api_key, model="grok-3-mini-beta", temperature=0, max_tokens=4096)
        
        start_time = datetime.datetime.now()
        
        # Don't create an unused processing alert here
        print("[FORMAT] Started processing with AI model")
        
        prompt = (
            "Format the following resume text into a clear, structured plain-text outline. "
            "Don't assume or add anything by yourself. "
            "Return resume between the following dividers: '---RESUME-START---' and '---RESUME-END---'\n\n"
            f"{raw_text}"
        )
        
        messages = [
            ("system", "You are an assistant that formats resumes."),
            ("human", prompt)
        ]
        
        response = chat_xai.invoke(messages)
        
        end_time = datetime.datetime.now()
        duration = (end_time - start_time).total_seconds()
        print(f"[FORMAT] Processing completed in {duration:.2f} seconds")
        
        formatted_text = response.content
        
        if "---RESUME-START---" in formatted_text and "---RESUME-END---" in formatted_text:
            formatted_text = formatted_text.split("---RESUME-START---")[1].split("---RESUME-END---")[0].strip()
            print(f"[FORMAT] Extracted {len(formatted_text)} characters of formatted text")
        else:
            print("[FORMAT] Warning: Response dividers not found")
        
        return html.Div([
            html.Pre(formatted_text, style={
                'whiteSpace': 'pre-wrap',
                'wordBreak': 'break-word',
                'maxHeight': '500px',
                'overflow': 'auto'
            }),
            html.Div(f"Processing time: {duration:.2f} seconds", className="text-muted mt-2 text-end small")
        ]), formatted_text, dbc.Alert(
            [
                html.I(className="fas fa-check-circle me-2"),
                f"Resume formatted successfully in {duration:.2f} seconds using Grok-3-mini model."
            ],
            className="text-center",
            color="success",
            dismissable=True,
            is_open=True,
            duration=5000
        )
    
    except Exception as e:
        print(f"[FORMAT] Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return html.Div([
            html.H5("Error formatting the text"),
            html.P(str(e))
        ]), "", dbc.Alert(
            [
                html.I(className="fas fa-exclamation-circle me-2"),
                f"Error during formatting: {str(e)}"
            ],
            className="text-center",
            color="danger",
            dismissable=True,
            is_open=True,
            duration=8000
        )

# Save resume callback
@callback(
    Output("save-alert-container", "children"),
    Input("save-button", "n_clicks"),
    State("formatted-text-store", "data"),
    prevent_initial_call=True
)
def save_resume(n_clicks, formatted_text):
    """Saves the formatted resume text to a local file."""
    print("[SAVE] Save request received")
    
    if not formatted_text:
        print("[SAVE] No formatted text available")
        return dbc.Alert(
            "No text available to save. Please parse and format a resume first.",
            className="text-center",
            color="danger",
            dismissable=True,
            is_open=True,
            duration=3000
        )
    
    try:
        os.makedirs("resumes", exist_ok=True)
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"resumes/resume_{timestamp}.txt"
        
        with open(filename, "w", encoding="utf-8") as f:
            f.write(formatted_text)
        
        print(f"[SAVE] Saved to {filename}")
        return dbc.Alert(
            "Resume saved successfully!",
            className="text-center",
            color="success",
            dismissable=True,
            is_open=True,
            duration=3000
        )
    except Exception as e:
        print(f"[SAVE] Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return dbc.Alert(
            f"Error saving file: {str(e)}",
            className="text-center",
            color="danger",
            dismissable=True,
            is_open=True,
            duration=3000
        )

# Download resume callback
@callback(
    Output("download-alert-container", "children"),
    Output("download-text", "data"),
    Input("download-button", "n_clicks"),
    State("formatted-text-store", "data"),
    prevent_initial_call=True
)
def download_resume(n_clicks, formatted_text):
    """Prepares formatted resume text for client-side download with enhanced feedback."""
    print("[DOWNLOAD] Download request received")
    
    if not formatted_text:
        print("[DOWNLOAD] No formatted text available")
        return dbc.Alert(
            [
                html.I(className="fas fa-exclamation-triangle me-2"),
                "No text available to download. Please parse and format a resume first."
            ],
            className="text-center",
            color="danger",
            dismissable=True,
            is_open=True,
            duration=3000
        ), dash.no_update
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"resume_{timestamp}.txt"
    print(f"[DOWNLOAD] Preparing file '{filename}' with {len(formatted_text)} characters")
    
    return dbc.Alert(
        [
            html.I(className="fas fa-download me-2"),
            f"Downloading '{filename}' ({len(formatted_text)} characters)"
        ],
        className="text-center",
        color="success",
        dismissable=True,
        is_open=True,
        duration=4000
    ), dict(content=formatted_text, filename=filename)

# # JSON Extraction callback
# @callback(
#     Output('json-content', 'children'),
#     Output('json-data-store', 'data'),
#     Output('json-extract-alert-container', 'children'),
#     Input('extract-json-button', 'n_clicks'),
#     State('formatted-text-store', 'data'),
#     prevent_initial_call=True
# )
# def extract_json_data(n_clicks, formatted_text):
#     """Extracts structured data from the formatted resume text using AI."""
#     print("[EXTRACT JSON] Extraction request received")
    
#     if not formatted_text:
#         print("[EXTRACT JSON] No formatted text available")
#         return html.P("No formatted text available for JSON extraction. Please format a resume first.", className="text-center"), "", dbc.Alert(
#             "No data to extract. Please parse and format a resume first.",
#             className="text-center",
#             color="warning",
#             dismissable=True,
#             is_open=True,
#             duration=4000
#         )
    
#     try:
#         print(f"[EXTRACT JSON] Processing {len(formatted_text)} characters")
        
#         api_key = os.environ.get("XAI_API_KEY")
#         if not api_key:
#             print("[EXTRACT JSON] API key missing")
#             return html.Div([
#                 html.H5("API Key Missing"),
#                 html.P("Please set the XAI_API_KEY environment variable.")
#             ]), "", dbc.Alert(
#                 [
#                     html.I(className="fas fa-key me-2"),
#                     "API Key not found. Please set the XAI_API_KEY environment variable."
#                 ],
#                 className="text-center",
#                 color="danger",
#                 dismissable=True,
#                 is_open=True,
#                 duration=0  # No auto-dismiss for this critical error
#             )
        
#         # Initialize ChatXAI
#         chat_xai = ChatXAI(api_key=api_key, model="grok-3-mini-beta", temperature=0, max_tokens=4096)
        
#         start_time = datetime.datetime.now()
#         print("[EXTRACT JSON] Started processing with AI model")
        
#         # Create system and human messages with the JSON extraction prompt
#         messages = [
#             ("system", "You are an assistant that extracts structured data from resumes in JSON format."),
#             ("human", f"""
#             Analyze the resume below and extract the following details in a structured JSON format. Use a step-by-step reasoning process to ensure accuracy.
            
#             Details to extract:
#             - Skills (list of skills)
#             - Experience (total years, list of responsibilities)
#             - Education (degree and field)
#             - Certifications (list of certifications)
#             - Other details (e.g., location, soft skills)

#             Resume:
#             {formatted_text}

#             Output only the JSON object:
#             {{
#                 "skills": [str],
#                 "experience": {{"years": float or null, "responsibilities": [str]}},
#                 "education": {{"degree": str or null, "field": str or null}},
#                 "certifications": [str],
#                 "other_details": [str]
#             }}
#             """)
#         ]

#         # Make the API call directly
#         response = chat_xai.invoke(messages)
        
#         end_time = datetime.datetime.now()
#         duration = (end_time - start_time).total_seconds()
#         print(f"[EXTRACT JSON] Processing completed in {duration:.2f} seconds")
        
#         # Get the response content
#         json_text = response.content
        
#         # Try to extract just the JSON part if there's any surrounding text
#         try:
#             # Find JSON-like content using regex (looking for content between curly braces)
#             import re
#             json_match = re.search(r'({[\s\S]*})', json_text)
#             if json_match:
#                 json_text = json_match.group(1)
#                 print("[EXTRACT JSON] Extracted JSON structure from response")
            
#             # Parse the JSON text to ensure it's valid
#             json_data = json.loads(json_text)
#             json_output = json.dumps(json_data, indent=4)
#             print(f"[EXTRACT JSON] Successfully parsed JSON with {len(json_data)} top-level keys")
#         except json.JSONDecodeError:
#             print("[EXTRACT JSON] Could not parse JSON from response")
#             # Fall back to displaying the raw response
#             json_data = {"raw_response": json_text}
#             json_output = json_text
        
#         return html.Div([
#             dcc.Markdown(f"```json\n{json_output}\n```", 
#                          style={'backgroundColor': '#f8f9fa', 'padding': '10px', 'borderRadius': '5px'}),
#             html.Div(f"Processing time: {duration:.2f} seconds", className="text-muted mt-2 text-end small")
#         ]), json_data, dbc.Alert(
#             [
#                 html.I(className="fas fa-check-circle me-2"),
#                 f"Data extracted with AI in {duration:.2f} seconds using Grok-3-mini model."
#             ],
#             className="text-center",
#             color="success",
#             dismissable=True,
#             is_open=True,
#             duration=4000
#         )
    
#     except Exception as e:
#         print(f"[EXTRACT JSON] Error: {str(e)}")
#         import traceback
#         traceback.print_exc()
#         return html.Div([
#             html.H5("Error extracting JSON data"),
#             html.P(str(e))
#         ]), "", dbc.Alert(
#             [
#                 html.I(className="fas fa-exclamation-circle me-2"),
#                 f"Error during JSON extraction: {str(e)}"
#             ],
#             className="text-center",
#             color="danger",
#             dismissable=True,
#             is_open=True,
#             duration=8000
#         )

# JSON extract processing alert callback
@callback(
    Output('json-extract-alert-container', 'children'),
    Input('extract-json-button', 'n_clicks'),
    State('formatted-text-store', 'data'),
    prevent_initial_call=True
)
def show_json_extract_processing_alert(n_clicks, formatted_text):
    """Shows a processing alert immediately when extract button is clicked."""
    if formatted_text:
        return create_processing_alert("Extracting resume data as JSON with AI, please wait...")
    return dash.no_update

# Then modify the extract_json_data callback to use allow_duplicate=True
@callback(
    Output('json-content', 'children'),
    Output('json-data-store', 'data'),
    Output('json-extract-alert-container', 'children', allow_duplicate=True),
    Input('extract-json-button', 'n_clicks'),
    State('formatted-text-store', 'data'),
    prevent_initial_call=True
)
def extract_json_data(n_clicks, formatted_text):
    """Extracts structured data from the formatted resume text using AI."""
    print("[EXTRACT JSON] Extraction request received")
    
    if not formatted_text:
        print("[EXTRACT JSON] No formatted text available")
        return html.P("No formatted text available for JSON extraction. Please format a resume first.", className="text-center"), "", dbc.Alert(
            "No data to extract. Please parse and format a resume first.",
            className="text-center",
            color="warning",
            dismissable=True,
            is_open=True,
            duration=4000
        )
    
    try:
        print(f"[EXTRACT JSON] Processing {len(formatted_text)} characters")
        
        api_key = os.environ.get("XAI_API_KEY")
        if not api_key:
            print("[EXTRACT JSON] API key missing")
            return html.Div([
                html.H5("API Key Missing"),
                html.P("Please set the XAI_API_KEY environment variable.")
            ]), "", dbc.Alert(
                [
                    html.I(className="fas fa-key me-2"),
                    "API Key not found. Please set the XAI_API_KEY environment variable."
                ],
                className="text-center",
                color="danger",
                dismissable=True,
                is_open=True,
                duration=0  # No auto-dismiss for this critical error
            )
        
        # Initialize ChatXAI
        chat_xai = ChatXAI(api_key=api_key, model="grok-3-mini-beta", temperature=0, max_tokens=4096)
        
        start_time = datetime.datetime.now()
        print("[EXTRACT JSON] Started processing with AI model")
        
        # Create system and human messages with the JSON extraction prompt
        messages = [
            ("system", "You are an assistant that extracts structured data from resumes in JSON format."),
            ("human", f"""
            Analyze the resume below and extract the following details in a structured JSON format. Use a step-by-step reasoning process to ensure accuracy.
            
            Details to extract:
            - Skills (list of skills)
            - Experience (total years, list of responsibilities)
            - Education (degree and field)
            - Certifications (list of certifications)
            - Other details (e.g., location, soft skills)

            Resume:
            {formatted_text}

            Output only the JSON object:
            {{
                "skills": [str],
                "experience": {{"years": float or null, "responsibilities": [str]}},
                "education": {{"degree": str or null, "field": str or null}},
                "certifications": [str],
                "other_details": [str]
            }}
            """)
        ]

        # Make the API call directly
        response = chat_xai.invoke(messages)
        
        end_time = datetime.datetime.now()
        duration = (end_time - start_time).total_seconds()
        print(f"[EXTRACT JSON] Processing completed in {duration:.2f} seconds")
        
        # Get the response content
        json_text = response.content
        
        # Try to extract just the JSON part if there's any surrounding text
        try:
            # Find JSON-like content using regex (looking for content between curly braces)
            import re
            json_match = re.search(r'({[\s\S]*})', json_text)
            if json_match:
                json_text = json_match.group(1)
                print("[EXTRACT JSON] Extracted JSON structure from response")
            
            # Parse the JSON text to ensure it's valid
            json_data = json.loads(json_text)
            json_output = json.dumps(json_data, indent=4)
            print(f"[EXTRACT JSON] Successfully parsed JSON with {len(json_data)} top-level keys")
        except json.JSONDecodeError:
            print("[EXTRACT JSON] Could not parse JSON from response")
            # Fall back to displaying the raw response
            json_data = {"raw_response": json_text}
            json_output = json_text
        
        return html.Div([
            dcc.Markdown(f"```json\n{json_output}\n```", 
                         style={'backgroundColor': '#f8f9fa', 'padding': '10px', 'borderRadius': '5px'}),
            html.Div(f"Processing time: {duration:.2f} seconds", className="text-muted mt-2 text-end small")
        ]), json_data, dbc.Alert(
            [
                html.I(className="fas fa-check-circle me-2"),
                f"Data extracted with AI in {duration:.2f} seconds using Grok-3-mini model."
            ],
            className="text-center",
            color="success",
            dismissable=True,
            is_open=True,
            duration=4000
        )
    
    except Exception as e:
        print(f"[EXTRACT JSON] Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return html.Div([
            html.H5("Error extracting JSON data"),
            html.P(str(e))
        ]), "", dbc.Alert(
            [
                html.I(className="fas fa-exclamation-circle me-2"),
                f"Error during JSON extraction: {str(e)}"
            ],
            className="text-center",
            color="danger",
            dismissable=True,
            is_open=True,
            duration=8000
        )

# Save JSON callback
@callback(
    Output("save-json-alert-container", "children"),
    Input("save-json-button", "n_clicks"),
    State("json-data-store", "data"),
    prevent_initial_call=True
)
def save_json(n_clicks, json_data):
    """Saves the extracted JSON data to a file."""
    print("[SAVE JSON] Save request received")
    
    if not json_data:
        print("[SAVE JSON] No JSON data available")
        return dbc.Alert(
            "No JSON data available to save. Please extract JSON data first.",
            className="text-center",
            color="danger",
            dismissable=True,
            is_open=True,
            duration=3000
        )
    
    try:
        os.makedirs("json_resumes", exist_ok=True)
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"json_resumes/resume_{timestamp}.json"
        
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(json_data, f, ensure_ascii=False, indent=4)
        
        print(f"[SAVE JSON] Saved to {filename}")
        return dbc.Alert(
            "Resume data saved as JSON successfully!",
            className="text-center",
            color="success",
            dismissable=True,
            is_open=True,
            duration=3000
        )
    except Exception as e:
        print(f"[SAVE JSON] Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return dbc.Alert(
            f"Error saving JSON file: {str(e)}",
            className="text-center",
            color="danger",
            dismissable=True,
            is_open=True,
            duration=3000
        )

# Download JSON callback
@callback(
    Output("download-json-alert-container", "children"),
    Output("download-json", "data"),
    Input("download-json-button", "n_clicks"),
    State("json-data-store", "data"),
    prevent_initial_call=True
)
def download_json(n_clicks, json_data):
    """Prepares extracted JSON data for client-side download."""
    print("[DOWNLOAD JSON] Download request received")
    
    if not json_data:
        print("[DOWNLOAD JSON] No JSON data available")
        return dbc.Alert(
            [
                html.I(className="fas fa-exclamation-triangle me-2"),
                "No JSON data available to download. Please extract JSON data first."
            ],
            className="text-center",
            color="danger",
            dismissable=True,
            is_open=True,
            duration=3000
        ), dash.no_update
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"resume_{timestamp}.json"
    print(f"[DOWNLOAD JSON] Preparing file '{filename}' with {len(json.dumps(json_data))} bytes")
    
    return dbc.Alert(
        [
            html.I(className="fas fa-download me-2"),
            f"Downloading JSON data as '{filename}'"
        ],
        className="text-center",
        color="success",
        dismissable=True,
        is_open=True,
        duration=4000
    ), dict(content=json.dumps(json_data, ensure_ascii=False, indent=4), filename=filename)