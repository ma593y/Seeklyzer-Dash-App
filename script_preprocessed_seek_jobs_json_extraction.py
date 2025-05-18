
import json
import os
from dotenv import load_dotenv
from langchain_xai import ChatXAI
import pandas as pd
from tqdm import tqdm

load_dotenv()

api_key = os.environ.get("XAI_API_KEY")


def extract_job_description(job_details: str) -> dict:
    """
    Extract structured data from a job description using ChatXAI.
    
    Args:
        job_details (str): The job description text.
        
    Returns:
        dict: Extracted structured data in JSON format.
    """
    # Initialize ChatXAI
    chat_xai = ChatXAI(api_key=api_key, model="grok-3-mini-beta", temperature=0, max_tokens=4096)

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
        - Categorize skills as 'required' or 'preferred' based on the job description’s explicit sections.

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
    response = chat_xai.invoke(messages)

    return response.content



def process_job_descriptions():
    """
    Process job descriptions from a parquet file, extract structured data,
    and save to a new parquet file.
    """

    input_file="data/preprocessed_seek_jobs_files/preprocessed_seek_jobs.parquet"
    output_file="data/preprocessed_seek_jobs_files/preprocessed_seek_jobs_plus_json.parquet"
    
    # Load the parquet file
    df = pd.read_parquet(input_file)
    
    # Create a new column for the extracted data
    df['Extracted Details'] = None
    
    # Process each job description
    print(f"Processing {len(df)} job descriptions...")
    for i in tqdm(range(len(df))):
        try:
            job_details = df.loc[i, 'Job Details']
            if isinstance(job_details, str) and job_details.strip():
                extracted_json = extract_job_description(job_details)
                df.loc[i, 'Extracted Details'] = extracted_json
        except Exception as e:
            print(f"Error processing row {i}: {str(e)}")

        break
    
    # Save the updated dataframe to a new parquet file
    df.to_parquet(output_file, index=False)
    df.to_excel(output_file.replace('.parquet', '.xlsx'), index=False)
    print(f"Processing complete. Results saved to {output_file}")
    
    return df




if __name__ == "__main__":
    process_job_descriptions()
