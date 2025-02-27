from flask import Flask, request, jsonify
import logging
from google.cloud import bigquery
import os
from datetime import datetime
import uuid

app = Flask(__name__)

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
try:
    bq_client = bigquery.Client(project=BIGQUERY_PROJECT_ID)
    logger.info("BigQuery client initialized successfully.")
except Exception as bq_init_error:
    logger.error("Error initializing BigQuery client: %s", str(bq_init_error), exc_info=True)
    bq_client = None

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        # Log the raw incoming request for debugging
        request_data = request.get_json()
        logger.info("Received request: %s", request_data)

        # Extract parameters from the request
        parameters = request_data.get('sessionInfo', {}).get('parameters', {})
        
        # Generate required fields
        ticket_id = str(uuid.uuid4())  
        created_at = datetime.utcnow().isoformat()

        # Extract user-provided fields
        email = parameters.get('email', 'N/A')
        issue = parameters.get('issue', 'N/A')
        name = parameters.get('name', {}).get('name', 'N/A')

        logger.info("Extracted parameters - Name: %s, Email: %s, Issue: %s", name, email, issue)
        
        # Prepare row matching BigQuery schema
        row_to_insert = {
            "ticket_id": ticket_id,
            "created_at": created_at,
            "issue": issue,
            "status": "Open",  
            "name": name,
            "email_address": email  
        }
        
        # BigQuery insertion
        if bq_client:
            try:
                table_id  = f"{BIGQUERY_PROJECT_ID}.{BIGQUERY_DATASET_ID}.{BIGQUERY_TABLE_ID}"
                errors = bq_client.insert_rows_json(table_id, [row_to_insert])

                if not errors:
                    logger.info("Data inserted successfully")
                else:
                    logger.error("BigQuery errors: %s", errors)
                    return jsonify({"error": "Database insertion failed"}), 500
            except Exception as bq_error:
                logger.error("BigQuery error: %s", str(bq_error), exc_info=True)
                return jsonify({"error": "Database error"}), 500
        else:
            logger.error("BigQuery client not initialized")
            return jsonify({"error": "Server configuration error"}), 500
            
        # Create response
        response = {
            "fulfillmentResponse": {
                "messages": [{
                    "text": {
                        "text": [
                            "Ticket Summary:\n \n"
                            f"Ticket ID: **{ticket_id}** \n"
                            f"Name: **{name}** \n"
                            f"Email address: **{email}** \n"
                            f"Issue: **{issue}** \n \n"
                            "Your ticket has been created. A confirmation email has been sent. \n"
                        ]
                    }
                }]
            },
            "sessionInfo": {
                "parameters": {
                    "ticket_id": ticket_id,
                    "status": "Open",
                    "email_address": email
                }
            }
        }

        logger.info("Sending response: %s", response)
        return jsonify(response)

    except Exception as e:
        logger.error("Error processing webhook: %s", str(e), exc_info=True)
        return jsonify({
            "fulfillmentResponse": {
                "messages": [{
                    "text": {
                        "text": ["An error occurred while processing your request"]
                    }
                }]
            }
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)