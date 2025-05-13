import requests
import json
import re
import pandas as pd
from bs4 import BeautifulSoup

def fetch_data(url):
    """
    Fetches JSON data from the specified API endpoint.
    
    Parameters:
        url (str): The API endpoint to fetch data from
        
    Returns:
        dict/list: Parsed JSON response, or None if request failed
    """
    print(f"Fetching data from URL: {url}")
    response = requests.get(url)
    if response.status_code == 200:
        try:
            data = response.json()
            length_info = len(data) if hasattr(data, '__len__') else 'unknown'
            print(f"Successfully fetched {length_info} items from API")
            return data
        except json.JSONDecodeError:
            print(f"Error decoding JSON response: {response.text}")
            return None
    else:
        print(f"Error fetching data from API: Status code {response.status_code}")
        return None

def extract_job_listings(data):
    """
    Extracts and flattens job listings from raw API data.
    
    Parameters:
        data (list): List of raw job listing items from the API
        
    Returns:
        list: Processed list of job listing dictionaries
    """
    print(f"Starting extraction of job listings from {len(data)} raw data items")
    job_listings_data = []
    error_keys = []

    for item in data:
        try:
            job_listing = {
                "id": item["id"],
                "title": item["title"],
                "companyName": item["companyName"] if "companyName" in item else "",
                "url": item["url"],
                "listingDate": item["listingDate"],
                "listingDateDisplay": item["listingDateDisplay"],
                "isFeatured": item["isFeatured"] if "isFeatured" in item else "",
                "displayType": item["displayType"],
                "displayStyle_search": item["displayStyle"]["search"] if "displayStyle" in item else "",
                "teaser": item["teaser"],
                "roleId": item["roleId"] if "roleId" in item else "",
                "salaryLabel": item["salaryLabel"] if "salaryLabel" in item else "",
                "companyProfileStructuredDataId": str(item["companyProfileStructuredDataId"]) if "companyProfileStructuredDataId" in item else "",
                "content": item["content"],
                "advertiser_id": item["advertiser"]["id"] if "id" in item["advertiser"] else "",
                "advertiser_description": item["advertiser"]["description"],
                "branding_serpLogoUrl": item["branding"]["serpLogoUrl"] if "branding" in item else "",
                "locations_0_countryCode": item["locations"][0]["countryCode"],
                "locations_0_label": item["locations"][0]["label"],
                "locations_0_seoHierarchy_0_contextualName": item["locations"][0]["seoHierarchy"][0]["contextualName"],
                "locations_0_seoHierarchy_1_contextualName": item["locations"][0]["seoHierarchy"][1]["contextualName"],
                "classifications_0_classification_id": item["classifications"][0]["classification"]["id"],
                "classifications_0_classification_description": item["classifications"][0]["classification"]["description"],
                "classifications_0_subclassification_id": item["classifications"][0]["subclassification"]["id"],
                "classifications_0_subclassification_description": item["classifications"][0]["subclassification"]["description"],
                "classifications_1_classification_id": item["classifications"][1]["classification"]["id"] if len(item["classifications"]) > 1 else "",
                "classifications_1_classification_description": item["classifications"][1]["classification"]["description"] if len(item["classifications"]) > 1 else "",
                "classifications_1_subclassification": item["classifications"][1]["subclassification"] if len(item["classifications"]) > 1 else "",
                "classifications_1_subclassification_id": item["classifications"][1]["subclassification"]["id"] if len(item["classifications"]) > 1 else "",
                "classifications_1_subclassification_description": item["classifications"][1]["subclassification"]["description"] if len(item["classifications"]) > 1 else "",
                "bulletPoints_0": item["bulletPoints"][0] if ("bulletPoints" in item and len(item["bulletPoints"]) > 0) else "",
                "bulletPoints_1": item["bulletPoints"][1] if ("bulletPoints" in item and len(item["bulletPoints"]) > 1) else "",
                "bulletPoints_2": item["bulletPoints"][2] if ("bulletPoints" in item and len(item["bulletPoints"]) > 2) else "",
                "workArrangements_displayText": item["workArrangements"]["displayText"] if "displayText" in item else "",
                "workArrangements_data_0_id": item["workArrangements"]["data"][0]["id"],
                "workArrangements_data_0_label_text": item["workArrangements"]["data"][0]["label"]["text"],
                "workTypes_0": item["workTypes"][0],
                "tags_0_type": item["tags"][0]["type"] if "tags" in item else "",
                "tags_0_label": item["tags"][0]["label"] if "tags" in item else "",
            }
        except KeyError as e:
            print(f"KeyError when processing job ID {item.get('id', 'unknown')}: {e}")
            error_keys.append(str(e))
            # Print only essential info for debugging
            print(f"Problem item keys: {list(item.keys())}")
            continue

        job_listings_data.append(job_listing)

    unique_errors = list(set(error_keys))
    print(f"Extraction complete: {len(job_listings_data)} valid listings extracted")
    if unique_errors:
        print(f"Encountered {len(unique_errors)} types of KeyErrors: {', '.join(unique_errors)}")
    return job_listings_data

# Define a function to format each row's details
def create_job_details(row):
    job_details = ""

    if row['Job Id']:
        job_details += f"Job Id: {row['Job Id']}\n"
    if row['Role Id']:
        job_details += f"Role Id: {row['Role Id']}\n"
    if row['Job Title']:
        job_details += f"Job Title: {row['Job Title']}\n"
    if row['Work Arrangement']:
        job_details += f"Work Arrangement: {row['Work Arrangement']}\n"
    if row['Work Type']:
        job_details += f"Work Type: {row['Work Type']}\n"
    if row['Posting Date']:
        job_details += f"Posting Date: {row['Posting Date']}\n"
    if row['Salary Range']:
        job_details += f"Salary Range: {row['Salary Range']}\n"
    if row['Company Name']:
        job_details += f"Company Name: {row['Company Name']}\n"
    if row['Advertiser Name']:
        job_details += f"Advertiser Name: {row['Advertiser Name']}\n"
    if row['Location']:
        job_details += f"Location: {row['Location']}\n"
    if row['Job Teaser']:
        job_details += f"Job Teaser: {row['Job Teaser']}\n"
    if row['Highlight Point 1']:
        job_details += f"Highlight Point 1: {row['Highlight Point 1']}\n"
    if row['Highlight Point 2']:
        job_details += f"Highlight Point 2: {row['Highlight Point 2']}\n"
    if row['Highlight Point 3']:
        job_details += f"Highlight Point 3: {row['Highlight Point 3']}\n"
    if row['Job Description Cleaned']:
        job_details += f"Job Description: {row['Job Description Cleaned']}"

    return job_details

def preprocess_dataframe(job_listings_data):
    """
    Processes job listings data into a clean, structured DataFrame.
    
    Performs cleaning, enrichment, column renaming, and removes unwanted data.
    
    Parameters:
        job_listings_data (list): List of job listing dictionaries
        
    Returns:
        DataFrame: Processed and cleaned pandas DataFrame
    """
    print(f"Preprocessing dataframe from {len(job_listings_data)} job listings")
    df = pd.DataFrame(job_listings_data)
    print(f"Created DataFrame with {df.shape[0]} rows and {df.shape[1]} columns")

    df = df[df['isFeatured'] != True]
    print(f"Removed featured listings: {df.shape[0]} rows remaining")
    df = df.drop_duplicates(subset=['id'])
    print(f"Removed duplicates: {df.shape[0]} rows remaining")

    column_mapping = {
        "id": "job_id",
        "title": "job_title",
        "companyName": "company_name",
        "url": "job_url",
        "listingDate": "posting_date",
        "teaser": "job_teaser",
        "roleId": "role_id",
        "salaryLabel": "salary_range",
        "content": "job_description",
        "advertiser_id": "advertiser_id",
        "advertiser_description": "advertiser_name",
        "branding_serpLogoUrl": "advertiser_logo_url",
        "locations_0_countryCode": "location_country_code",
        "locations_0_label": "location_label",
        "bulletPoints_0": "highlight_point_1",
        "bulletPoints_1": "highlight_point_2",
        "bulletPoints_2": "highlight_point_3",
        "workArrangements_data_0_label_text": "work_arrangement",
        "workTypes_0": "work_type"
    }

    print("Renaming columns for clarity...")
    df = df.rename(columns=column_mapping)
    print("Columns renamed according to mapping")

    df['role_id'] = df['role_id'].apply(lambda x: x.replace('-', ' ').title())

    df['job_title'] = df.apply(lambda row: row['job_title'] + ' | ' + row['role_id'] if row['role_id'] not in str(row['job_title']).title() else row['job_title'], axis=1)
    
    print("Job titles adjusted with role IDs where necessary")

    df['highlights'] = (df[['highlight_point_1', 'highlight_point_2', 'highlight_point_3']].fillna('').apply(lambda x: '; '.join([val for val in x if val != '']), axis=1))
    
    print("Highlights consolidated")

    df['job_description_cleaned'] = df['job_description'].apply(lambda x: BeautifulSoup(x, 'html.parser').get_text(separator='   ') if x else '')

    print("Job descriptions cleaned and merged")

    df['location'] = (df['location_label'].fillna('') + ' - ' + df['location_country_code'].fillna(''))

    print("Location column created")

    df.replace(regex={r'[\ud800-\udfff]': ''}, inplace=True)

    df.columns = [col.title().replace('_', ' ') for col in df.columns]

    print("Column names formatted to title case and underscores replaced with spaces")
    print(json.dumps(list(df.columns), indent=4))

    columns_to_drop = [
        "Listingdatedisplay",
        "Isfeatured",
        "Displaytype",
        "Displaystyle Search",
        "Companyprofilestructureddataid",
        "Classifications 1 Classification Id",
        "Classifications 1 Classification Description",
        "Classifications 1 Subclassification",
        "Classifications 1 Subclassification Id",
        "Classifications 1 Subclassification Description",
        "Workarrangements Displaytext",
        "Workarrangements Data 0 Id",
    ]
    
    df.drop(columns=columns_to_drop, errors='ignore', inplace=True)
    print("Dropped unnecessary columns")
    
    # Add a comment explaining Job Details column creation
    print("Creating formatted Job Details column...")

    # Apply the formatting function to each row
    df['Job Details'] = df.apply(create_job_details, axis=1)

    print("Job Details column created with formatted content for each listing")

    new_column_order = [
        "Job Id",
        "Role Id",
        "Job Title",
        "Work Arrangement",
        "Work Type",
        "Posting Date",
        "Salary Range",
        "Company Name",
        "Advertiser Id",
        "Advertiser Name",
        "Advertiser Logo Url",
        "Location",
        "Location Country Code",
        "Location Label",
        "Locations 0 Seohierarchy 0 Contextualname",
        "Locations 0 Seohierarchy 1 Contextualname",
        "Classifications 0 Classification Id",
        "Classifications 0 Classification Description",
        "Classifications 0 Subclassification Id",
        "Classifications 0 Subclassification Description",
        "Job Teaser",
        "Highlights",
        "Highlight Point 1",
        "Highlight Point 2",
        "Highlight Point 3",
        "Job Description",
        "Job Description Cleaned",
        "Job Details",
        "Tags 0 Type",
        "Tags 0 Label",
        "Job Url",
    ]

    print(f"Creating final DataFrame with {len(new_column_order)} columns")
    final_df = df[new_column_order]
    print(f"Final DataFrame ready: {final_df.shape[0]} jobs with {final_df.shape[1]} attributes")

    print("Reordering columns to final format...")
    print("Final DataFrame columns:")
    print(json.dumps(list(final_df.columns), indent=4))

    return final_df

def save_outputs(df):
    """
    Exports the final DataFrame to multiple file formats.
    
    Saves the data as Excel (.xlsx), Feather (.feather),
    Parquet (.parquet), and JSON (.json) files.
    
    Parameters:
        df (DataFrame): The processed DataFrame to save
    """
    print("Saving outputs to multiple formats...")

    file_name = 'preprocessed_job_listings'
    print(f"Saving {df.shape[0]} job listings to files with base name: {file_name}")

    df.to_excel(f'{file_name}.xlsx', index=False)
    print(f"✓ Excel file saved: {file_name}.xlsx")
    df.to_feather(f'{file_name}.feather')
    print(f"✓ Feather file saved: {file_name}.feather")
    df.to_parquet(f'{file_name}.parquet', index=False)
    print(f"✓ Parquet file saved: {file_name}.parquet") 
    df.to_json(f'{file_name}.json', orient='records', lines=True)
    print(f"✓ JSON file saved: {file_name}.json")
    print("All output files saved successfully")

def main():
    print("=" * 60)
    print("STARTING JOB LISTINGS DATA PIPELINE")
    print("=" * 60)
    url = "https://api.apify.com/v2/datasets/JjAzvUEH4pSeV294Q/items?clean=true&format=json"
    data = fetch_data(url)
    if not data:
        print("ERROR: No data retrieved; exiting pipeline.")
        return

    print("-" * 60)
    job_listings = extract_job_listings(data)
    print("-" * 60)
    df = preprocess_dataframe(job_listings)
    print("-" * 60)
    save_outputs(df)
    print("=" * 60)
    print(f"PIPELINE COMPLETED: Processed {df.shape[0]} job listings successfully")
    print("=" * 60)


if __name__ == "__main__":
    main()