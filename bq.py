from google.cloud import bigquery
import logging
import os
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# BigQuery Configuration
BIGQUERY_PROJECT_ID = "eikon-dev-ai-team"  
BIGQUERY_DATASET_ID = "ticketing_dataset"  
BIGQUERY_TABLE_ID = "ticket_table"  

# Set the environment variable to suppress the project ID warning
os.environ["GOOGLE_CLOUD_PROJECT"] = BIGQUERY_PROJECT_ID

# Initialize BigQuery client
bq_client = None
try:
    bq_client = bigquery.Client(project=BIGQUERY_PROJECT_ID)
    logger.info("BigQuery client initialized successfully.")
except Exception as bq_init_error:
    logger.error("Error initializing BigQuery client: %s", str(bq_init_error), exc_info=True)

# Prepare row matching BigQuery schema
row_to_insert = {
    "ticket_id": 12345,
    "created_at": datetime.now().isoformat(),
    "issue": "Login Issue",
    "status": "Open",  
    "name": "Jane Doe",
    "email_address": "John.doe@example.com"  
    }
    
# BigQuery insertion
if bq_client:
    try:
        # Use fully qualified table ID
        table_id = f"{BIGQUERY_PROJECT_ID}.{BIGQUERY_DATASET_ID}.{BIGQUERY_TABLE_ID}"
        errors = bq_client.insert_rows_json(table_id, [row_to_insert])

        if not errors:
            logger.info("Data inserted successfully")
        else:
            logger.error("BigQuery errors during insertion: %s", errors)
            
    except Exception as bq_error:
        logger.error("BigQuery error: %s", str(bq_error), exc_info=True)
        
else:
    logger.error("BigQuery client not initialized")
        
