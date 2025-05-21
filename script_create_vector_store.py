import os
import pandas as pd
from typing import List, Dict, Any
from langchain_core.documents import Document
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings


def create_job_store(
    records: List[Dict[str, str]], 
    persist_dir: str = "chroma_db"
) -> Chroma:
    """Create a Chroma vector store from job records.
    
    Args:
        records: List of dicts, each with
            - "job_id": a unique ID str
            - "job_details": the text to embed
        persist_dir: where to write the Chroma database
        
    Returns:
        Chroma: A Chroma vectorstore instance
    """
    print(f"Creating vector store with {len(records)} records...")
    embeds = OpenAIEmbeddings()
    docs = [
        Document(
            page_content=rec["job_details"],
            metadata={"job_id": rec["job_id"]}
        )
        for rec in records
    ]
    print("Documents created, generating embeddings...")
    store = Chroma.from_documents(docs, embedding=embeds, persist_directory=persist_dir)
    print("Vector store created successfully!")
    return store



def store_from_parquet(
    parquet_path: str,
    id_col: str,
    text_col: str,
    persist_dir: str
) -> Chroma:
    """Loads a parquet of preprocessed seek jobs and creates a Chroma store.
    
    Args:
        parquet_path: Path to the .parquet file
        id_col: Name of the column with unique job IDs
        text_col: Name of the column with the job description text
        persist_dir: Directory where Chroma will persist its data
        
    Returns:
        Chroma: A Chroma vectorstore instance
    """
    print(f"Reading parquet file from {parquet_path}...")
    # 1) Load the dataframe
    df = pd.read_parquet(parquet_path)
    print(f"Loaded {len(df)} rows from parquet file")

    # 2) Build the minimal records list
    print("Converting data to records format...")
    records = [
        {
            "job_id": str(row[id_col]),
            "job_details": str(row[text_col])
        }
        for _, row in df.iterrows()
    ]
    print("Records created successfully")

    # 3) Call the existing helper
    return create_job_store(records, persist_dir=persist_dir)


def create_vector_store_from_parquet():
    try:
        # Use os.path.join for cross-platform path handling
        parquet_path = os.path.join("data", "preprocessed_seek_jobs_files", "preprocessed_seek_jobs.parquet")
        persist_dir = os.path.join("data", "chroma_db")
        
        print(f"Loading data from {parquet_path}")
        store = store_from_parquet(
            parquet_path=parquet_path,
            id_col="Job Id",
            text_col="Job Details",
            persist_dir=persist_dir
        )
        
        # Get some basic stats about the store
        collection = store._collection
        print(f"Successfully created vector store with {collection.count()} documents")
        print(f"Vector store persisted to {persist_dir}")
        
    except FileNotFoundError as e:
        print(f"Error: Could not find the parquet file: {e}")
    except Exception as e:
        print(f"Error: An error occurred while creating the vector store: {e}")

if __name__ == "__main__":
    create_vector_store_from_parquet()