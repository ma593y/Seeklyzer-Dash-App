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
        dbc.Button("Download Resume", id="download-button", color="secondary"),
        dcc.Download(id="download-text"),
        
        html.Div(id="save-alert-container", className="mt-2"),
        html.Div(id="download-alert-container", className="mt-2")
    ], className="text-center mt-3 mb-4"),
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
        os.makedirs("data/formatted_resumes_files", exist_ok=True)
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"data/formatted_resumes_files/resume_{timestamp}.txt"
        
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