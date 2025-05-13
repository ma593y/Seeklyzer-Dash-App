import requests
import json
import re
import pandas as pd
from bs4 import BeautifulSoup

def fetch_data(url):
    """
    Block 1: Fetch JSON data from the API.
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
    Block 2: Turn raw items into a list of flattened job_listing dicts.
    Prints any KeyErrors and the final lists of errors & listings.
    """
    print(f"Starting extraction of job listings from data with {len(data)} items")
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
                "companyProfileStructuredDataId": item["companyProfileStructuredDataId"] if "companyProfileStructuredDataId" in item else "",
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
            print(f"KeyError: {e}")
            error_keys.append(str(e))
            print(json.dumps(item, indent=4))
            continue

        job_listings_data.append(job_listing)

    unique_errors = list(set(error_keys))
    print(f"Extraction complete: {len(job_listings_data)} listings extracted with {len(unique_errors)} unique KeyErrors")
    print(json.dumps(unique_errors, indent=4))
    return job_listings_data

def preprocess_dataframe(job_listings_data):
    """
    Block 3: Load into pandas, clean, enrich, reorder, and drop unwanted columns.
    Returns the final DataFrame.
    """
    print(f"Preprocessing dataframe from {len(job_listings_data)} job listings")
    df = pd.DataFrame(job_listings_data)
    print(f"Initial DataFrame shape: {df.shape}")

    df = df[df['isFeatured'] != True]
    print(f"After filtering featured listings: {df.shape}")
    df = df.drop_duplicates(subset=['id'])
    print(f"After dropping duplicates: {df.shape}")

    column_mapping = {
        "id": "job_id",
        "title": "job_title",
        "companyName": "companyName",
        "url": "job_url",
        "listingDate": "posting_date",
        "teaser": "job_teaser",
        "roleId": "role_id",
        "salaryLabel": "salary_range",
        "content": "job_description",
        "advertiser_id": "advertiser_id",
        "advertiser_description": "company_name",
        "branding_serpLogoUrl": "advertiser_logo_url",
        "locations_0_countryCode": "location_country_code",
        "locations_0_label": "location_label",
        "bulletPoints_0": "highlight_point_1",
        "bulletPoints_1": "highlight_point_2",
        "bulletPoints_2": "highlight_point_3",
        "workArrangements_data_0_label_text": "work_arrangement",
        "workTypes_0": "work_type"
    }

    df = df.rename(columns=column_mapping)
    print("Columns renamed according to mapping")

    df['role_id'] = df['role_id'].apply(lambda x: x.replace('-', ' ').title())

    df['job_title'] = df.apply(lambda row: row['job_title'] + ' | ' + row['role_id'] if row['role_id'] not in str(row['job_title']).title() else row['job_title'], axis=1)
    
    print("Job titles adjusted with role IDs where necessary")

    df['highlights'] = (df[['highlight_point_1', 'highlight_point_2', 'highlight_point_3']].fillna('').apply(lambda x: '; '.join([val for val in x if val != '']), axis=1))
    
    print("Highlights consolidated")

    df['job_description'] = df['job_description'].apply(lambda x: BeautifulSoup(x, 'html.parser').get_text(separator='   ') if x else '')

    df['job_description'] = (df['job_teaser'].fillna('') + ' | ' + df['highlights'].fillna('') + ' | ' + df['job_description']).apply(lambda x: re.sub(r'\s+', ' ', x).strip())

    print("Job descriptions cleaned and combined")

    df['location'] = (df['location_label'].fillna('') + ' - ' + df['location_country_code'].fillna(''))

    print("Location column created")

    df.replace(regex={r'[\ud800-\udfff]': ''}, inplace=True)

    columns_to_drop = [
        'listingDateDisplay', 'isFeatured', 'displayType', 'displayStyle_search',
        'companyProfileStructuredDataId', 'locations_0_seoHierarchy_0_contextualName',
        'locations_0_seoHierarchy_1_contextualName', 'classifications_0_classification_id',
        'classifications_0_classification_description', 'classifications_0_subclassification_id',
        'classifications_0_subclassification_description', 'classifications_1_classification_id',
        'classifications_1_subclassification_id', 'classifications_1_subclassification_description',
        'workArrangements_displayText', 'workArrangements_data_0_id', 'tags_0_type', 'tags_0_label',
        'classifications_1_classification_description', 'classifications_1_subclassification', 'companyName',
        'highlight_point_1', 'highlight_point_2', 'highlight_point_3', 'location_country_code',
        'location_label', 'role_id', 'job_teaser', 'advertiser_id', 'highlights', 'advertiser_logo_url'
    ]
    
    df.drop(columns=columns_to_drop, errors='ignore', inplace=True)
    print("Dropped unnecessary columns")

    df.columns = [col.title().replace('_', ' ') for col in df.columns]
    new_column_order = [
        "Job Id",
        "Job Title",
        "Company Name",
        "Work Type",
        "Work Arrangement",
        "Location",
        "Posting Date",
        "Job Url",
        "Job Description",
    ]
    final_df = df[new_column_order]
    print(f"Final DataFrame ready with shape: {final_df.shape}")
    return final_df

def save_outputs(df):
    """
    Block 4: Export the final DataFrame to Excel and JSON.
    """
    print(f"Saving outputs: Excel, JSON, plus feather and parquet formats")

    file_name ='preprocessed_job_listings'

    df.to_excel(f'{file_name}.xlsx', index=False)
    df.to_feather(f'{file_name}.feather')
    df.to_parquet(f'{file_name}.parquet', index=False)
    df.to_json(f'{file_name}.json', orient='records', lines=True)
    print("All files saved successfully")

def main():
    print("Starting job listings data pipeline...")
    url = "https://api.apify.com/v2/datasets/JjAzvUEH4pSeV294Q/items?clean=true&format=json"
    data = fetch_data(url)
    if not data:
        print("No data retrieved; exiting pipeline.")
        return

    job_listings = extract_job_listings(data)
    df = preprocess_dataframe(job_listings)
    save_outputs(df)
    print("Pipeline completed successfully")

if __name__ == "__main__":
    main()
