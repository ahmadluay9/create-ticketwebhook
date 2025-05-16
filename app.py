# Import Library
from flask import Flask, request,jsonify, Response as FlaskResponse
import logging
from google.cloud import bigquery
import os
from datetime import datetime
import uuid
from dotenv import load_dotenv
from dialogflow import DialogFlowReply
from twilio.rest import Client

load_dotenv()
app = Flask(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# --- Load environment variables ---
account_sid = os.getenv("TWILIO_ACCOUNT_SID")
auth_token = os.getenv("TWILIO_AUTH_TOKEN")

language_code = os.getenv("LANGUAGE_CODE")

# BigQuery Configuration
BIGQUERY_PROJECT_ID = os.getenv("PROJECT_ID")
BIGQUERY_DATASET_ID = os.getenv("BIGQUERY_DATASET_ID") 
BIGQUERY_TABLE_ID = os.getenv("BIGQUERY_TABLE_ID")
BIGQUERY_TABLE_ID_WA = os.getenv("BIGQUERY_TABLE_ID_WA") 

# BigQuery Configuration
BIGQUERY_PROJECT_ID = os.getenv("PROJECT_ID")
BIGQUERY_DATASET_ID = os.getenv("BIGQUERY_DATASET_ID") 
BIGQUERY_TABLE_ID = os.getenv("BIGQUERY_TABLE_ID_WA") 

if not account_sid:
    logger.error("Twilio Account SID (TWILIO_ACCOUNT_SID) not found in environment variables.")
if not auth_token:
    logger.error("Twilio Auth Token (TWILIO_AUTH_TOKEN) not found in environment variables.")
if not language_code:
    logger.warning("Language Code (LANGUAGE_CODE) not found in environment variables. Using default or Dialogflow's default.")
if not BIGQUERY_PROJECT_ID:
    logger.error("PROJECT_ID not found in environment variables.")
if not BIGQUERY_DATASET_ID:
    logger.error("BIGQUERY_DATASET_ID not found in environment variables.")
if not BIGQUERY_TABLE_ID:
    logger.error("TBIGQUERY_TABLE_ID not found in environment variables.")

logger.info(f"Twilio Account SID loaded: {'Yes' if account_sid else 'No'}")
logger.info(f"Twilio Auth Token loaded: {'Yes' if auth_token else 'No'}")

logger.info(f"Language Code loaded: {language_code if language_code else 'Not set, using default'}")

logger.info(f"BigQuery Project ID loaded: {'Yes' if BIGQUERY_PROJECT_ID else 'No'}")
logger.info(f"BigQuery Dataset ID loaded: {'Yes' if BIGQUERY_DATASET_ID else 'No'}")
logger.info(f"BigQuery Table ID loaded: {'Yes' if BIGQUERY_TABLE_ID else 'No'}")

# Set the environment variable to suppress the project ID warning
os.environ["GOOGLE_CLOUD_PROJECT"] = BIGQUERY_PROJECT_ID

# Initialize BigQuery client
try:
    bq_client = bigquery.Client(project=BIGQUERY_PROJECT_ID)
    logger.info("BigQuery client initialized successfully.")
except Exception as bq_init_error:
    logger.error("Error initializing BigQuery client: %s", str(bq_init_error), exc_info=True)
    bq_client = None
    
# --- Flask Route ---
@app.route("/")
def home():
    return "<h1>Twilio Dialogflow Whatsapp Integration"

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        # Log the raw incoming request for debugging
        request_data = request.get_json()
        logger.info("Received request: %s", request_data)

        # Extract parameters from the request
        parameters = request_data.get('sessionInfo', {}).get('parameters', {})
        
        # Generate required fields
        ticket_id = str(uuid.uuid4())[:8]  
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
            "email_address": email,
            "ticket_history_file": ""
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

@app.route('/create', methods=['POST'])
def create_ticket():
    try:
        # Log the raw incoming request for debugging
        request_data = request.get_json()
        logger.info("Received request: %s", request_data)

        # Extract parameters from the request
        parameters = request_data.get('sessionInfo', {}).get('parameters', {})
        
        # Generate required fields
        ticket_id = str(uuid.uuid4())[:8]  
        created_at = datetime.utcnow().isoformat()

        # Extract user-provided fields
        email = parameters.get('Email')
        if not email:
            email = parameters.get('email','N/A')

        issue = parameters.get('Issue')
        if not issue:
            issue = parameters.get('issue','N/A')
            
        name_value = 'N/A'  
        name_parameter = parameters.get('Name') 

        if isinstance(name_parameter, dict):
            name_value = name_parameter.get('name', 'N/A') 
        elif isinstance(name_parameter, str): 
            name_value = name_parameter
        else:            
            name_parameter_lowercase = parameters.get('name')
            if isinstance(name_parameter_lowercase, dict):
                name_value = name_parameter_lowercase.get('name', 'N/A')
            elif isinstance(name_parameter_lowercase, str):
                name_value = name_parameter_lowercase

        name = name_value 

        phone_number = parameters.get('phone', 'N/A')
        if not phone_number:
            phone_number = parameters.get('Phone','N/A')

        logger.info("Extracted parameters - Name: %s, Email: %s, Issue: %s, phone_number: %s", name, email, issue, phone_number)
        
        # Prepare row matching BigQuery schema
        row_to_insert = {
            "ticket_id": ticket_id,
            "created_at": created_at,
            "issue": issue,
            "status": "Open",  
            "name": name,
            "phone_number": phone_number,
            "email_address": email,
            "ticket_history_file": ""
        }
        
        # BigQuery insertion
        if bq_client:
            try:
                table_id  = f"{BIGQUERY_PROJECT_ID}.{BIGQUERY_DATASET_ID}.{BIGQUERY_TABLE_ID_WA}"
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
                            f"Ticket ID: *{ticket_id}* \n"
                            f"Name: *{name}* \n"
                            f"Phone Number: *{phone_number}* \n"
                            f"Email address: *{email}* \n"
                            f"Issue: *{issue}* \n \n"                            
                            "Your ticket has been created. A confirmation email has been sent. \n"
                        ]
                    }
                }]
            },
            "sessionInfo": {
                "parameters": {
                    "ticket_id": ticket_id,
                    "status": "Open",
                    "email_address": email,
                    "phone_number": phone_number
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

@app.route('/check_status', methods=['POST'])
def check_status():
    try:
        # Log the raw incoming request for debugging
        request_data = request.get_json()
        logger.info("Received request: %s", request_data)

        # Extract parameters from the request
        parameters = request_data.get('sessionInfo', {}).get('parameters', {})
        ticket_id = parameters.get('ticket_id', 'N/A')
        logger.info("Extracted parameters - Ticket ID: %s", ticket_id)
        
        if not bq_client:
            logger.error("BigQuery client not initialized")
            return jsonify({"error": "Server configuration error"}), 500               
            
        # Query BigQuery for ticket status
        status_message = "No ticket found with the provided ID."
        status = "Not Found"
        try:
            table_id = f"{BIGQUERY_PROJECT_ID}.{BIGQUERY_DATASET_ID}.{BIGQUERY_TABLE_ID}"
            query = f"""
                SELECT status, created_at, issue 
                FROM `{table_id}` 
                WHERE ticket_id = @ticket_id
            """
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("ticket_id", "STRING", ticket_id)
                ]
            )
            query_job = bq_client.query(query, job_config=job_config)
            results = list(query_job.result())  # Convert to list to check for results

            if results:
                # Assuming ticket_id is unique, take the first result
                ticket = results[0]
                status = ticket.status
                created_at = ticket.created_at
                issue = ticket.issue
                status_message = (
                    "Ticket Status:\n\n"
                    f"Ticket ID: **{ticket_id}**\n"
                    f"Created At: **{created_at}**\n"
                    f"Issue: **{issue}**\n"
                    f"Status: **{status}**\n"
                )
        except Exception as bq_error:
            logger.error("BigQuery error: %s", str(bq_error), exc_info=True)
            return jsonify({"error": "Database error"}), 500

        # Create response
        response = {
            "fulfillmentResponse": {
                "messages": [{
                    "text": {
                        "text": [status_message]
                    }
                }]
            },
            "sessionInfo": {
                "parameters": {
                    "ticketid": ticket_id,
                    "status": status
                }
            }
        }

        logger.info("Sending response: %s", response)
        return jsonify(response)

    except Exception as e:
        logger.error("Error checking ticket status: %s", str(e), exc_info=True)
        return jsonify({
            "fulfillmentResponse": {
                "messages": [{
                    "text": {
                        "text": ["An error occurred while checking your ticket status."]
                    }
                }]
            }
        }), 500

@app.route('/check', methods=['POST'])
def check():
    try:
        # Log the raw incoming request for debugging
        request_data = request.get_json()
        logger.info("Received request: %s", request_data)

        # Extract parameters from the request
        parameters = request_data.get('sessionInfo', {}).get('parameters', {})
        
        # Generate required fields
        ticket_id = parameters.get('ticketid')
        if not ticket_id:
            ticket_id = parameters.get('ticket_id')
        if not ticket_id:
            ticket_id = parameters.get('TicketID','N/A')

        logger.info("Extracted parameters - Ticket ID: %s", ticket_id)
        
        if not bq_client:
            logger.error("BigQuery client not initialized")
            return jsonify({"error": "Server configuration error"}), 500               
            
        # Query BigQuery for ticket status
        status_message = "No ticket found with the provided ID."
        status = "Not Found"
        try:
            table_id = f"{BIGQUERY_PROJECT_ID}.{BIGQUERY_DATASET_ID}.{BIGQUERY_TABLE_ID_WA}"
            query = f"""
                SELECT status, created_at, issue 
                FROM `{table_id}` 
                WHERE ticket_id = @ticket_id
            """
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("ticket_id", "STRING", ticket_id)
                ]
            )
            query_job = bq_client.query(query, job_config=job_config)
            results = list(query_job.result())  # Convert to list to check for results

            if results:
                # Assuming ticket_id is unique, take the first result
                ticket = results[0]
                status = ticket.status
                created_at = ticket.created_at
                issue = ticket.issue
                status_message = (
                    f"Ticket ID: *{ticket_id}*\n"
                    f"Created At: *{created_at}*\n"
                    f"Issue: *{issue}*\n"
                    f"Status: *{status}*\n"
                )
        except Exception as bq_error:
            logger.error("BigQuery error: %s", str(bq_error), exc_info=True)
            return jsonify({"error": "Database error"}), 500

        # Create response
        response = {
            "fulfillmentResponse": {
                "messages": [{
                    "text": {
                        "text": [status_message]
                    }
                }]
            },
            "sessionInfo": {
                "parameters": {
                    "ticketid": ticket_id,
                    "status": status
                }
            }
        }

        logger.info("Sending response: %s", response)
        return jsonify(response)

    except Exception as e:
        logger.error("Error checking ticket status: %s", str(e), exc_info=True)
        return jsonify({
            "fulfillmentResponse": {
                "messages": [{
                    "text": {
                        "text": ["An error occurred while checking your ticket status."]
                    }
                }]
            }
        }), 500

@app.route("/twilio-dialogflowcx", methods=["POST"])
def twilio_dialogflowcx_handler(): # Renamed handler function for clarity
    """
    Handles incoming WhatsApp messages via Twilio, sends them to Dialogflow CX,
    and replies to the user with the agent's response.
    """
    logger.info("Received POST request on /twilio-dialogflowcx")

    # --- Form Data Handling ---
    try:
        received_msg = request.form.get("Body")
        user_number = request.form.get("From") # This will be like 'whatsapp:+1234567890'
        twilio_number = request.form.get("To") # This will be your Twilio WhatsApp number

        if not all([received_msg, user_number, twilio_number]):
            missing_fields = []
            if not received_msg: missing_fields.append("Body")
            if not user_number: missing_fields.append("From")
            if not twilio_number: missing_fields.append("To")
            logger.warning(f"Missing form fields: {', '.join(missing_fields)}")
            return FlaskResponse(f"Missing required form fields: {', '.join(missing_fields)}", status=400)

        logger.info(f"Received message: '{received_msg}' from: {user_number} to: {twilio_number}")

    except Exception as e:
        logger.error(f"Error accessing form data: {e}", exc_info=True)
        return FlaskResponse("Error processing request data.", status=400)

    # --- Create Twilio Client ---
    if not account_sid or not auth_token:
        logger.error("Twilio credentials (accountSID or authToken) are not configured. Cannot send reply.")
        # Return 500 because it's a server-side configuration issue.
        return FlaskResponse("Twilio service not configured.", status=500)
    try:
        twilio_client = Client(account_sid, auth_token)
        logger.info("Twilio client initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize Twilio client: {e}", exc_info=True)
        return FlaskResponse("Failed to initialize Twilio service.", status=500)

    # --- Call Dialogflow CX Agent ---
    try:
        # Use user_number for session ID to maintain context
        dialogflow_cx_session = DialogFlowReply(session_id=user_number)
        logger.info(f"DialogFlowReply instance created for session_id: {user_number}")

        # Ensure language_code is passed; DialogFlowReply might have its own default or error handling
        if not language_code:
            logger.warning("Language code is not set; Dialogflow will use its default.")
            # Consider setting a default 'en' or other common language if not provided
            # effective_language_code = language_code or "en" # Example
            effective_language_code = language_code # Pass None if that's intended
        else:
            effective_language_code = language_code

        dialogflow_responses = dialogflow_cx_session.send_request(
            message=received_msg, language_code=effective_language_code
        )
        logger.info(f"Received {len(dialogflow_responses)} response(s) from Dialogflow.")

    except Exception as e:
        logger.error(f"Error during Dialogflow CX request: {e}", exc_info=True)
        # Send generic error to user
        try:
            error_reply = "Sorry, I encountered an error. Please try again later."
            twilio_client.messages.create(
                to=user_number,
                from_=twilio_number,
                body=error_reply,
            )
            logger.info(f"Sent generic error message to {user_number}")
        except Exception as twilio_error:
            logger.error(f"Failed to send generic error message via Twilio: {twilio_error}", exc_info=True)
        return FlaskResponse("Error communicating with Dialogflow.", status=500)


    # --- Process Dialogflow Response and Send via Twilio ---
    if not dialogflow_responses:
        logger.warning("No message returned from Dialogflow CX.")
        try:
            no_response_reply = "I'm not sure how to respond to that. Can you try rephrasing?"
            twilio_client.messages.create(
                to=user_number,
                from_=twilio_number,
                body=no_response_reply
            )
            logger.info(f"Sent 'no Dialogflow response' message to {user_number}")
        except Exception as e:
            logger.error(f"Error sending 'no Dialogflow response' message via Twilio: {e}", exc_info=True)
        # Even if sending this fails, we still inform the Twilio platform that we received the webhook.
        return FlaskResponse("No message content from Dialogflow.", status=200) # Or 400 if it's considered a bad request

    sent_messages_count = 0
    for df_message in dialogflow_responses:
        if df_message.text and df_message.text.text:
            # Dialogflow CX often returns a list of text strings.
            # We'll join them or take the first one. Taking the first is common.
            agent_response_text = df_message.text.text[0]
            if not agent_response_text.strip():
                logger.info("Dialogflow message text is empty, skipping.")
                continue

            logger.info(f"Preparing to send Dialogflow response to {user_number}: '{agent_response_text}'")
            try:
                twilio_client.messages.create(
                    to=user_number,       # e.g., 'whatsapp:+1234567890'
                    from_=twilio_number,  # e.g., 'whatsapp:+0987654321'
                    body=agent_response_text,
                )
                logger.info(f"Message sent successfully to {user_number} via Twilio.")
                sent_messages_count += 1
            except Exception as error:
                logger.error(f"Error sending message via Twilio: {error}", exc_info=True)
                # If one message fails, should we stop or continue?
                # For now, we'll log and continue if there are multiple response messages.
                # If it's critical that all messages are sent, you might return an error earlier.
        else:
            logger.info(f"Dialogflow response message does not contain text: {df_message}")

    if sent_messages_count > 0:
        logger.info(f"Successfully sent {sent_messages_count} message(s) via Twilio.")
        # Twilio expects a 200 OK if the webhook was processed, even if no message is sent back.
        # Or a 204 No Content if you specifically don't want Twilio to send anything else.
        # For an empty response body to Twilio, use FlaskResponse(status=204) or just return an empty string.
        # Twilio's own examples often just return an empty XML <Response/> or an empty string for a 200.
        return FlaskResponse("", status=200) # Empty body, 200 OK
    else:
        logger.warning("No actionable text messages found in Dialogflow responses to send via Twilio.")
        return FlaskResponse("No messages were sent.", status=200)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)