import os
from typing import MutableSequence
from google.cloud import dialogflowcx_v3beta1 as dialogflow
from google.cloud.dialogflowcx_v3beta1.types.response_message import ResponseMessage
import logging
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Set the GOOGLE_APPLICATION_CREDENTIALS environment variable
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.getenv("SERVICE_ACCOUNT_PATH")

class DialogFlowReply:
    """
    Encapsulates interactions with a Dialogflow CX agent.
    """

    def __init__(
        self,
        session_id: str,
        project_id: str = None,
        agent_id: str = None,
        location: str = None,
    ):
        """
        Initializes the DialogFlowReply class.

        Args:
            session_id: ID of the Dialogflow CX session to use.
            project_id: ID of the GCP project containing the Dialogflow agent.
                If not provided, attempts to retrieve from the 'projectId' environment variable.
            agent_id: ID of the Dialogflow CX agent.
                If not provided, attempts to retrieve from the 'agentId' environment variable.
            location: Location of the Dialogflow agent.
                If not provided, attempts to retrieve from the 'location' environment variable.
        """
        self.session_id = session_id
        logger.info(f"Initializing DialogFlowReply for session ID: {session_id}")

        self.project_id = project_id if project_id else os.environ.get("PROJECT_ID")
        self.agent_id = agent_id if agent_id else os.environ.get("AGENT_ID")
        self.location = location if location else os.environ.get("LOCATION")

        if not self.project_id:
            logger.error("Project ID is not set. Please provide it or set the 'PROJECT_ID' environment variable.")
            raise ValueError("Project ID is required.")
        if not self.agent_id:
            logger.error("Agent ID is not set. Please provide it or set the 'AGENT_ID' environment variable.")
            raise ValueError("Agent ID is required.")
        if not self.location:
            logger.error("Location is not set. Please provide it or set the 'LOCATION' environment variable.")
            raise ValueError("Location is required.")

        logger.info(f"Project ID: {self.project_id}")
        logger.info(f"Agent ID: {self.agent_id}")
        logger.info(f"Location: {self.location}")

        self.dialogflow_client = self.set_dialogflow_client()
        self.session_path = self.set_session_path()
        logger.info("DialogFlowReply initialized successfully.")

    def set_dialogflow_client(self):
        """
        Creates and returns a Dialogflow CX SessionsClient.
        """
        try:
            api_endpoint = f"{self.location}-dialogflow.googleapis.com"
            logger.info(f"Setting Dialogflow client with API endpoint: {api_endpoint}")
            client = dialogflow.SessionsClient(
                client_options={
                    "api_endpoint": api_endpoint
                }
            )
            logger.info("Dialogflow CX SessionsClient created successfully.")
            return client
        except Exception as e:
            logger.error(f"Error creating Dialogflow CX SessionsClient: {e}", exc_info=True)
            raise

    def set_session_path(self):
        """
        Constructs and returns the session path for the Dialogflow CX session.
        """
        try:
            session_path = self.dialogflow_client.session_path(
                project=self.project_id,
                session=self.session_id,
                location=self.location,
                agent=self.agent_id,
            )
            logger.info(f"Dialogflow session path set: {session_path}")
            return session_path
        except Exception as e:
            logger.error(f"Error setting Dialogflow session path: {e}", exc_info=True)
            raise

    # Create Dialogflow CX request
    def send_request(
        self, message: str, language_code: str
    ) -> MutableSequence[ResponseMessage]:
        """Sends a message to the DialogFlow CX agent and returns the reply.

        Args:
            message: str. The message to send to the agent.
            language_code: str. The language code of the message (e.g., 'en').

        Returns:
            A list of ResponseMessage objects representing the agent's responses.
        """
        logger.info(f"Sending message to Dialogflow: '{message}' with language code: '{language_code}'")
        request = {
            "session": self.session_path,
            "query_input": {
                "text": {
                    "text": message,
                },
                "language_code": language_code,
            },
        }
        logger.debug(f"Dialogflow request payload: {request}")

        # Get Dialogflow CX response
        try:
            response = self.dialogflow_client.detect_intent(request=request)
            query_result = response.query_result
            logger.info(f"Dialogflow Response Messages: {query_result.response_messages}")
            if query_result.match and query_result.match.intent:
                logger.info(f"Matched Intent: {query_result.match.intent.display_name}")
            logger.info(f"Current Page: {query_result.current_page.display_name}")
            return query_result.response_messages
        except Exception as error:
            logger.error(f"Error during Dialogflow detect_intent request: {error}", exc_info=True)
            return []