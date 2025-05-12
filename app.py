import base64
import io
import re
import dash
from dotenv import load_dotenv
from dash import html, dcc, callback, Input, Output, State
import dash_bootstrap_components as dbc
import PyPDF2
from langchain_xai import ChatXAI
import os
import datetime


# Load environment variables from .env file
load_dotenv()


# Initialize the Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# App layout
app.layout = dbc.Container([
    html.H1("Seeklyzer - Resume: Uploading > Parsing > Formatting > Saving", className="text-center my-4"),
    
    dbc.Card([
        dbc.CardBody([
            html.H4("Upload a PDF file", className="card-title"),
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
            # Add Parse Resume button
            html.Div([
                dbc.Button("Parse Resume", id="parse-button", color="primary", className="mt-3")
            ], className="text-center"),
        ])
    ], className="mb-3"),
    
    dbc.Card([
        dbc.CardHeader("Extracted Text"),
        dbc.CardBody([
            html.Div(id='output-content')
        ])
    ]),
    
    # Centered Format Text button
    html.Div([
        dbc.Button("Format Text", id="format-button", color="info", className="mt-3")
    ], className="text-center mb-3"),
    
    # Store the raw text for formatting
    dcc.Store(id="raw-text-store"),
    
    # Store the formatted text
    dcc.Store(id="formatted-text-store"),
    
    # New card to display formatted text
    dbc.Card([
        dbc.CardHeader("Formatted Resume"),
        dbc.CardBody([
            html.Div(id='formatted-content')
        ])
    ], className="mt-3 mb-3"),
    
    # Save and Download buttons below Formatted Resume
    html.Div([
        dbc.Button("Save Resume", id="save-button", color="success", className="me-2"),
        dbc.Button("Download Resume", id="download-button", color="secondary"),
        dcc.Download(id="download-text")
    ], className="text-center mt-3 mb-4")
], fluid=True)

# Callback to update upload area with selected filename
@callback(
    Output('upload-content', 'children'),
    Output('upload-pdf', 'style'),
    Input('upload-pdf', 'contents'),
    State('upload-pdf', 'filename'),
    prevent_initial_call=True
)
def update_upload_area(contents, filename):
    if contents is None:
        return ['Drag and Drop or ', html.A('Select a PDF File')], {
            'width': '100%',
            'height': '60px',
            'lineHeight': '60px',
            'borderWidth': '1px',
            'borderStyle': 'dashed',
            'borderRadius': '5px',
            'textAlign': 'center',
            'margin': '10px'
        }
    
    if filename.lower().endswith('.pdf'):
        # PDF file selected - show green border
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
            'backgroundColor': '#f0fff0'  # Light green background
        }
    else:
        # Non-PDF file selected - show warning border
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
            'backgroundColor': '#fff9f0'  # Light orange background
        }

# Callback to process uploaded file when button is clicked
@callback(
    Output('output-content', 'children'),
    Output('raw-text-store', 'data'),
    Input('parse-button', 'n_clicks'),
    State('upload-pdf', 'contents'),
    State('upload-pdf', 'filename'),
    prevent_initial_call=True
)
def update_output(n_clicks, content, filename):
    if content is None:
        return html.P("Please upload a PDF file before parsing."), ""

    if not filename.lower().endswith('.pdf'):
        return html.P("Please upload a PDF file."), ""
    
    try:
        # Decode the base64 encoded content
        content_type, content_string = content.split(',')
        decoded = base64.b64decode(content_string)

        print(f"Decoded content length: {len(decoded)} bytes")
        print(f"Filename: {filename}")
        
        # Read the PDF file
        pdf_file = io.BytesIO(decoded)
        reader = PyPDF2.PdfReader(pdf_file)
        
        # Extract text from all pages
        text = ""
        for page_num in range(len(reader.pages)):
            page = reader.pages[page_num]
            text += page.extract_text() + "\n\n"
        
        text = re.sub(r'\s+', ' ', text).strip()  # Clean up the text
        print(f"Extracted text length: {len(text)} characters")

        if text:
            return html.Div([
                html.H5(f"Filename: {filename}"),
                html.Hr(),
                html.Pre(text, style={
                    'whiteSpace': 'pre-wrap',
                    'wordBreak': 'break-word',
                    'maxHeight': '500px',
                    'overflow': 'auto'
                })
            ]), text
        else:
            return html.P("No text could be extracted from this PDF. It may be scanned or contain only images."), ""
    
    except Exception as e:
        return html.Div([
            html.H5("Error processing the file"),
            html.P(str(e))
        ]), ""

# Callback to format text
@callback(
    Output('formatted-content', 'children'),
    Output('formatted-text-store', 'data'),
    Input('format-button', 'n_clicks'),
    State('raw-text-store', 'data'),
    prevent_initial_call=True
)
def format_text(n_clicks, raw_text):
    if not raw_text:
        return html.P("No text available to format. Please parse a resume first."), ""
    
    try:
        # Initialize the ChatXAI client
        # Note: In a production app, you should use environment variables or a secure method to store API keys
        api_key = os.environ.get("XAI_API_KEY")
        if not api_key:
            return html.Div([
                html.H5("API Key Missing"),
                html.P("Please set the XAI_API_KEY environment variable.")
            ]), ""
        
        chat_xai = ChatXAI(api_key=api_key, model="grok-3-mini-beta", temperature=0, max_tokens=4096)
        
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
        formatted_text = response.content
        
        # Extract the resume between the dividers
        if "---RESUME-START---" in formatted_text and "---RESUME-END---" in formatted_text:
            formatted_text = formatted_text.split("---RESUME-START---")[1].split("---RESUME-END---")[0].strip()
        
        return html.Div([
            html.Pre(formatted_text, style={
                'whiteSpace': 'pre-wrap',
                'wordBreak': 'break-word',
                'maxHeight': '500px',
                'overflow': 'auto'
            })
        ]), formatted_text
    
    except Exception as e:
        return html.Div([
            html.H5("Error formatting the text"),
            html.P(str(e))
        ]), ""

# Callback to save resume
@callback(
    Output("save-button", "children"),
    Input("save-button", "n_clicks"),
    State("formatted-text-store", "data"),
    prevent_initial_call=True
)
def save_resume(n_clicks, formatted_text):
    if not formatted_text:
        return "No Text to Save"
    
    try:
        # Create a resumes directory if it doesn't exist
        os.makedirs("resumes", exist_ok=True)
        
        # Generate filename based on timestamp
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"resumes/resume_{timestamp}.txt"
        
        # Save the file
        with open(filename, "w", encoding="utf-8") as f:
            f.write(formatted_text)
        
        return "✓ Saved"
    except Exception as e:
        print(f"Error saving resume: {e}")
        return "Save Failed"

# Callback to download resume
@callback(
    Output("download-text", "data"),
    Input("download-button", "n_clicks"),
    State("formatted-text-store", "data"),
    prevent_initial_call=True
)
def download_resume(n_clicks, formatted_text):
    if not formatted_text:
        return dash.no_update
    
    # Generate filename based on timestamp
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    return dict(content=formatted_text, filename=f"resume_{timestamp}.txt")

if __name__ == '__main__':
    app.run(debug=True)