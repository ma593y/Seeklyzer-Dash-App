import json
import os
import time
from dotenv import load_dotenv
from langchain_xai import ChatXAI
import pandas as pd
from tqdm import tqdm
import concurrent.futures
from functools import partial

# Load environment variables
load_dotenv()
print("Environment variables loaded")

api_key = os.environ.get("XAI_API_KEY")
if not api_key:
    print("WARNING: XAI_API_KEY not found in environment variables")


def extract_job_description(job_details: str) -> dict:
    """
    Extract structured data from a job description using ChatXAI.
    
    Args:
        job_details (str): The job description text.
        
    Returns:
        dict: Extracted structured data in JSON format.
    """
    print(f"Processing job description ({len(job_details)} characters)...")
    
    # Initialize ChatXAI
    chat_xai = ChatXAI(api_key=api_key, model="grok-3-mini-beta", temperature=0, max_tokens=4096)
    print("ChatXAI initialized with grok-3-mini-beta model")

    # Create system and human messages with the JSON extraction prompt
    messages = [
        ("system", "You are an assistant that extracts structured data from job descriptions in JSON format."),
        ("human", f"""
        Analyze the job description below and extract the following details in a structured JSON format. Use a step-by-step reasoning process to ensure accuracy.

        Details to extract:
        - Job title
        - Skills (required and preferred, as lists of concise technical skill names)
        - Experience (years required, list of responsibilities)
        - Education (degree and field)
        - Certifications (list of required certifications)
        - Other requirements (e.g., location, soft skills)
         
        For the skills section:
        - Extract only specific technical skills, programming languages, frameworks, tools, platforms, and technologies (e.g., 'Python', 'AWS', 'Docker').
        - List each skill as a concise string, splitting combined skills into individual items (e.g., 'Python, FastAPI, ORM' becomes ['Python', 'FastAPI', 'ORM']).
        - Exclude non-technical skills (e.g., 'problem-solving', 'teamwork', 'Agile/Scrum') and descriptive phrases (e.g., 'debugging and improving performance issues').
        - Categorize skills as 'required' or 'preferred' based on the job description's explicit sections.

        Job Description:
        {job_details}

        Output only the JSON object:
        {{
            "title": str,
            "skills": {{"required": [str], "preferred": [str]}},
            "experience": {{"years": float or null, "responsibilities": [str]}},
            "education": {{"degree": str or null, "field": str or null}},
            "certifications": [str],
            "other_requirements": [str]
        }}
        """)
    ]

    # Make the API call directly
    print("Sending request to ChatXAI API...")
    start_time = time.time()
    response = chat_xai.invoke(messages)
    processing_time = time.time() - start_time
    print(f"Response received in {processing_time:.2f} seconds")
    
    # Try to validate JSON before returning
    try:
        # Check if it's already a dict or if it needs parsing
        if isinstance(response.content, str):
            # Try to parse the JSON to validate it
            print(json.dumps(json.loads(response.content), indent=4))
            print("-" * 50)
            print("Successfully validated JSON response")
    except json.JSONDecodeError:
        print("WARNING: Response may not be valid JSON")
    
    return response.content


def process_job_descriptions():
    """
    Process job descriptions from a parquet file, extract structured data,
    and save to a new parquet file.
    """
    print("Starting job description processing...")
    
    input_file="data/preprocessed_seek_jobs_files/preprocessed_seek_jobs.parquet"
    output_file="data/preprocessed_seek_jobs_files/preprocessed_seek_jobs_plus_json.parquet"
    
    # Check if input file exists
    if not os.path.exists(input_file):
        print(f"ERROR: Input file not found: {input_file}")
        return None
    
    print(f"Loading data from {input_file}...")
    # Load the parquet file
    df = pd.read_parquet(input_file)
    print(f"Loaded dataframe with {len(df)} rows and {len(df.columns)} columns")
    
    # Create a new column for the extracted data
    df['Extracted Details'] = None
    
    # Process each job description in parallel
    print(f"Processing {len(df)} job descriptions in parallel...")
    start_time = time.time()
    successful_extractions = 0
    
    # Define a worker function for parallel processing
    def process_single_job(i, dataframe):
        try:
            job_details = dataframe.loc[i, 'Job Details']
            if isinstance(job_details, str) and job_details.strip():
                print(f"\nProcessing job #{i+1}/{len(dataframe)}")
                extracted_json = extract_job_description(job_details)
                return i, extracted_json, True
            else:
                print(f"Skipping row {i}: Empty or invalid job details")
                return i, None, False
        except Exception as e:
            print(f"ERROR processing row {i}: {str(e)}")
            return i, None, False
    
    # Use max_workers appropriate for your CPU (e.g., 3-4 for typical systems)
    max_workers = 16  # Adjust based on your system capabilities
    
    # DEBUG MODE: Process only a subset during development
    debug_mode = False  # Set to False for full processing
    indices_to_process = range(1) if debug_mode else range(len(df))
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Create a partial function with the dataframe argument bound
        worker_func = partial(process_single_job, dataframe=df)
        
        # Process jobs in parallel
        results = list(executor.map(worker_func, indices_to_process))
    
    # Update the dataframe with results
    for i, extracted_json, success in results:
        if success:
            df.loc[i, 'Extracted Details'] = extracted_json
            successful_extractions += 1
    
    # Calculate processing statistics
    total_time = time.time() - start_time
    print(f"\nProcessing summary:")
    print(f"- Total jobs: {len(df)}")
    print(f"- Successfully processed: {successful_extractions}")
    print(f"- Failed: {len(df) - successful_extractions}")
    print(f"- Total time: {total_time:.2f} seconds")
    
    # Save the updated dataframe to new files
    print(f"Saving results to {output_file}...")
    df.to_parquet(output_file, index=False)
    
    excel_output = output_file.replace('.parquet', '.xlsx')
    print(f"Saving Excel version to {excel_output}...")
    df.to_excel(excel_output, index=False)
    
    print(f"Processing complete. Results saved successfully.")
    
    return df


if __name__ == "__main__":
    print("=" * 50)
    print("JOB DESCRIPTION EXTRACTION TOOL")
    print("=" * 50)
    start_time = time.time()
    
    result_df = process_job_descriptions()
    
    total_runtime = time.time() - start_time
    print(f"Total runtime: {total_runtime:.2f} seconds")