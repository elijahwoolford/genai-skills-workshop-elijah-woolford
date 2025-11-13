"""
Load Alaska Department of Snow FAQ data from GCS to BigQuery with embeddings.

This script:
1. Loads CSV files from gs://labs.roitraining.com/alaska-dept-of-snow
2. Creates BigQuery dataset and tables
3. Creates BigQuery ML embedding model
4. Generates embeddings for all FAQ entries
"""

import pandas as pd
from google.cloud import bigquery
from google.cloud import bigquery_connection_v1
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.config import (
    PROJECT_ID, LOCATION, DATASET_ID, TABLE_ID, 
    EMBEDDED_TABLE_ID, EMBEDDING_MODEL_ID, BQ_CONNECTION_ID
)

GCS_BUCKET = "labs.roitraining.com"
GCS_PREFIX = "alaska-dept-of-snow/"
GCS_CSV_FILE = "gs://labs.roitraining.com/alaska-dept-of-snow/alaska-dept-of-snow-faqs.csv"


def create_bq_connection():
    """Create BigQuery connection for Vertex AI if it doesn't exist."""
    try:
        connection_client = bigquery_connection_v1.ConnectionServiceClient()
        parent = f"projects/{PROJECT_ID}/locations/{LOCATION}"
        connection_name = f"{parent}/connections/{BQ_CONNECTION_ID}"
        
        try:
            connection_client.get_connection(name=connection_name)
            print(f"✓ Connection already exists: {BQ_CONNECTION_ID}")
            return BQ_CONNECTION_ID
        except:
            pass
        
        connection = bigquery_connection_v1.Connection()
        connection.cloud_resource = bigquery_connection_v1.CloudResourceProperties()
        
        request = bigquery_connection_v1.CreateConnectionRequest(
            parent=parent,
            connection_id=BQ_CONNECTION_ID,
            connection=connection,
        )
        
        created = connection_client.create_connection(request=request)
        print(f"✓ Created connection: {BQ_CONNECTION_ID}")
        return BQ_CONNECTION_ID
    except Exception as e:
        print(f"Connection creation: {e}")
        return BQ_CONNECTION_ID


def main():
    """Load ADS FAQ data and generate embeddings."""
    client = bigquery.Client(project=PROJECT_ID)
    
    # Step 1: Create dataset
    print("Step 1: Creating BigQuery dataset...")
    dataset_id = f"{PROJECT_ID}.{DATASET_ID}"
    dataset = bigquery.Dataset(dataset_id)
    dataset.location = LOCATION
    dataset = client.create_dataset(dataset, exists_ok=True)
    print(f"✓ Dataset ready: {DATASET_ID}")
    
    # Step 2: Load data from GCS (CSV + TXT files)
    print("\nStep 2: Loading FAQ data from GCS...")
    from google.cloud import storage
    
    storage_client = storage.Client(project=PROJECT_ID)
    bucket = storage_client.bucket(GCS_BUCKET)
    
    # First, try to load the CSV file
    try:
        df_csv = pd.read_csv(GCS_CSV_FILE)
        print(f"✓ Loaded {len(df_csv)} entries from CSV")
    except Exception as e:
        print(f"Note: Could not load CSV: {e}")
        df_csv = pd.DataFrame()
    
    # Load all TXT files
    txt_faqs = []
    blobs = storage_client.list_blobs(GCS_BUCKET, prefix=GCS_PREFIX)
    txt_files = [blob for blob in blobs if blob.name.endswith('.txt')]
    
    print(f"Found {len(txt_files)} TXT files")
    
    for blob in txt_files:
        content = blob.download_as_text()
        # TXT format: Line 1 = Question, Line 2 = blank, Line 3+ = Answer
        lines = content.strip().split('\n')
        if len(lines) >= 3:
            question = lines[0].strip()
            # Skip blank line (line 1), answer starts at line 2
            answer = '\n'.join(lines[2:]).strip()
            txt_faqs.append({"question": question, "answer": answer})
    
    df_txt = pd.DataFrame(txt_faqs)
    print(f"✓ Parsed {len(df_txt)} entries from TXT files")
    
    # Combine CSV and TXT data
    if not df_csv.empty and not df_txt.empty:
        df = pd.concat([df_csv, df_txt], ignore_index=True)
    elif not df_csv.empty:
        df = df_csv
    else:
        df = df_txt
    
    print(f"✓ Total: {len(df)} FAQ entries")
    print(f"  Columns: {list(df.columns)}")
    
    # Step 3: Create base table
    print("\nStep 3: Creating BigQuery table...")
    table_ref = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"
    
    schema = [
        bigquery.SchemaField("question", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("answer", "STRING", mode="REQUIRED"),
    ]
    
    job_config = bigquery.LoadJobConfig(
        schema=schema,
        write_disposition="WRITE_TRUNCATE",
    )
    
    job = client.load_table_from_dataframe(df, table_ref, job_config=job_config)
    job.result()
    print(f"✓ Loaded {job.output_rows} rows into {TABLE_ID}")
    
    # Step 4: Create BigQuery connection
    print("\nStep 4: Creating BigQuery connection...")
    create_bq_connection()
    
    # Step 5: Grant permissions (print instructions)
    print("\nStep 5: Grant permissions to connection service account")
    connection_client = bigquery_connection_v1.ConnectionServiceClient()
    connection_name = f"projects/{PROJECT_ID}/locations/{LOCATION}/connections/{BQ_CONNECTION_ID}"
    connection = connection_client.get_connection(name=connection_name)
    service_account = connection.cloud_resource.service_account_id
    
    print(f"  Service Account: {service_account}")
    print(f"  Run: gcloud projects add-iam-policy-binding {PROJECT_ID} \\")
    print(f"         --member=serviceAccount:{service_account} \\")
    print(f"         --role=roles/aiplatform.user")
    
    # Step 6: Create embedding model
    print("\nStep 6: Creating BigQuery ML embedding model...")
    create_model_sql = f"""
    CREATE OR REPLACE MODEL `{EMBEDDING_MODEL_ID}`
    REMOTE WITH CONNECTION `{LOCATION}.{BQ_CONNECTION_ID}`
    OPTIONS (
      ENDPOINT = 'text-embedding-005'
    )
    """
    
    try:
        client.query(create_model_sql).result()
        print(f"✓ Created embedding model: {EMBEDDING_MODEL_ID}")
    except Exception as e:
        print(f"Model creation: {e}")
        print("  Make sure permissions are granted (see Step 5)")
        return
    
    # Step 7: Generate embeddings
    print("\nStep 7: Generating embeddings for all FAQs...")
    embedded_table_ref = f"{PROJECT_ID}.{DATASET_ID}.{EMBEDDED_TABLE_ID}"
    
    generate_embeddings_sql = f"""
    CREATE OR REPLACE TABLE `{embedded_table_ref}` AS
    SELECT
      question,
      answer,
      CONCAT(question, ' ', answer) AS content,
      ml_generate_embedding_result
    FROM
      ML.GENERATE_EMBEDDING(
        MODEL `{EMBEDDING_MODEL_ID}`,
        (SELECT question, answer, CONCAT(question, ' ', answer) AS content
         FROM `{table_ref}`)
      )
    """
    
    job = client.query(generate_embeddings_sql)
    job.result()
    print(f"✓ Created table with embeddings: {EMBEDDED_TABLE_ID}")
    
    # Verify
    verify_query = f"""
    SELECT question, ARRAY_LENGTH(ml_generate_embedding_result) as embedding_dim
    FROM `{embedded_table_ref}`
    LIMIT 3
    """
    print("\nVerifying embeddings:")
    for row in client.query(verify_query).result():
        print(f"  Q: {row.question[:60]}...")
        print(f"  Embedding dim: {row.embedding_dim}")
    
    print("\n" + "="*70)
    print("✓ DATA PIPELINE COMPLETE!")
    print("="*70)
    print(f"  Dataset: {DATASET_ID}")
    print(f"  Base Table: {TABLE_ID}")
    print(f"  Embedded Table: {EMBEDDED_TABLE_ID}")
    print(f"  Embedding Model: {EMBEDDING_MODEL_ID}")


if __name__ == "__main__":
    main()

