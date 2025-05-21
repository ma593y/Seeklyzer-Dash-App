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
    print(f"Processing job description ({len(job_details)} characters)...")
    
    # Initialize ChatXAI
    chat_xai = ChatXAI(api_key=api_key, model="grok-3-mini-beta", temperature=0, max_tokens=4096)
    print("ChatXAI initialized with grok-3-mini-beta model")
    
    system_prompt = "You are an assistant that formats job descriptions in a structured way."
    human_prompt = f"""

    You are an expert in analyzing job descriptions (JDs) for IT roles to support recruitment. Your task is to extract and summarize three critical sections from a provided IT job description: **Key Responsibilities / Duties**, **Essential Qualifications & Experience**, and **Skills & Competencies**. These sections will be used to evaluate and shortlist candidates based on their resumes in a separate process. For each extracted bullet point, provide instructions for how it can be assessed using resume content, without assigning scores. Follow the instructions below to ensure accurate, concise, and practical extraction, focusing on IT-specific context as commonly seen in real-world JDs:

    1. **Key Responsibilities / Duties**

    - Extract primary day-to-day IT tasks (e.g., developing software, managing networks, ensuring system security).
        - Provide assessment instructions to review resume content for relevant experience.
    - Include responsibilities with clear outcomes or deliverables (e.g., "deploy applications to production" or "reduce downtime by 10%").
        - Provide assessment instructions to identify related achievements in the resume.
    - Summarize as a list of tuples, each formatted as ((Bullet Point: [text]), (Assessment Instructions: [text])).

    2. **Essential Qualifications & Experience**

    - Identify all listed qualifications and experience, including:
        - Required and preferred degrees or certifications (e.g., "Bachelor's in Computer Science" or "AWS Certified Solutions Architect preferred").
        - Provide assessment instructions to verify qualifications in the resume.
        - Minimum years of relevant IT experience, including any preferred experience levels (e.g., "2+ years in cloud administration, 5+ years preferred").
        - Provide assessment instructions to check relevant experience duration.
        - Specific industry or technical expertise, required or preferred (e.g., "experience with HIPAA-compliant systems" or "familiarity with DevOps practices preferred").
        - Provide assessment instructions to identify relevant expertise in the resume.
    - Clearly distinguish between essential and preferred qualifications in the bullet points.
    - Summarize as a list of tuples, each formatted as ((Bullet Point: [text]), (Assessment Instructions: [text])).

    3. **Skills & Competencies**

    - Extract key IT-relevant skills, including:
        - **Hard Skills**: Proficiency in specific tools, languages, or platforms (e.g., Java, Azure, Linux).
        - Provide assessment instructions to check for listed skills in the resume.
        - **Soft Skills**: Problem-solving, clear communication with technical/non-technical stakeholders, and teamwork (e.g., in Agile environments).
        - Provide assessment instructions to identify implied skills in resume content.
    - Summarize as a list of tuples, each formatted as ((Bullet Point: [text]), (Assessment Instructions: [text])), separating hard and soft skills for clarity.

    **Output Format**:
    Provide the extracted information in JSON format with three keys: `key_responsibilities_duties`, `essential_qualifications_experience`, and `skills_competencies`. Each key maps to a list of objects, where each object represents a tuple with two fields: `bullet_point` (the extracted text) and `assessment_instructions` (the resume-based assessment instructions). If a section is not explicitly stated in the JD, include a single tuple with `bullet_point` as "Not explicitly stated" and appropriate `assessment_instructions` for inferred IT-specific details if feasible. Ensure the tone is professional and the content is concise, reflecting standard IT JD language. Do not add information beyond the JD.

    **Example Output**:

    ```json
    {{
    "key_responsibilities_duties": [
        {{
        "bullet_point": "Develop and maintain web applications using Node.js",
        "assessment_instructions": "Review the resume's work experience for roles or projects involving Node.js or similar web development technologies."
        }},
        {{
        "bullet_point": "Ensure network security through regular audits and updates",
        "assessment_instructions": "Look for achievements in the resume's work experience related to network security or audits, such as implementing security protocols."
        }}
    ],
    "essential_qualifications_experience": [
        {{
        "bullet_point": "Essential: Bachelor's degree in Information Technology or related field",
        "assessment_instructions": "Check the resume's education section for a Bachelor's degree in IT or a related field."
        }},
        {{
        "bullet_point": "Essential: 3+ years in software development or network administration",
        "assessment_instructions": "Review the resume's work history to confirm at least 3 years in relevant software development or network administration roles."
        }},
        {{
        "bullet_point": "Preferred: Master's degree in Computer Science",
        "assessment_instructions": "Check the resume's education section for a Master's degree in Computer Science."
        }},
        {{
        "bullet_point": "Preferred: Experience with cloud-based environments like AWS or Azure",
        "assessment_instructions": "Look for cloud-related experience (e.g., AWS, Azure) in the resume's work history or projects."
        }}
    ],
    "skills_competencies": [
        {{
        "bullet_point": "Hard Skills: Node.js, AWS, firewall management",
        "assessment_instructions": "Check the resume's skills section or job descriptions for proficiency in Node.js, AWS, and firewall management."
        }},
        {{
        "bullet_point": "Soft Skills: Problem-solving, technical communication, Agile teamwork",
        "assessment_instructions": "Look for evidence in the resume's job duties or achievements, such as resolving technical issues, communicating with stakeholders, or working in Agile teams."
        }}
    ]
    }}
    ```

    **Input**:
    ============JOB DESCRIPTION============
    {job_details}
    ============JOB DESCRIPTION============

    **Task**:
    Analyze the provided IT job description and extract the three sections as described, presenting the output in JSON format with each section as a list of objects containing `bullet_point` and `assessment_instructions` fields. If no job description is provided, respond with a JSON object containing a single key `error` with the value "An IT job description is required to proceed with the extraction."

    **Example Error Output**:

    ```json
    {{
    "error": "An IT job description is required to proceed with the extraction"
    }}
    ```

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
    max_workers = 10  # Adjust based on your system capabilities
    
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
    print("JOB DETAILS EXTRACTION TOOL")
    print("=" * 50)
    start_time = time.time()
    
    result_df = process_job_descriptions()
    
    total_runtime = time.time() - start_time
    print(f"Total runtime: {total_runtime:.2f} seconds")