import os
from google.api_core.client_options import ClientOptions
from google.cloud import discoveryengine

def create_data_store(
    project_id: str,
    location: str,
    data_store_id: str,
    datastore_name: str
) -> str:
    #  For more information, refer to:
    # https://cloud.google.com/generative-ai-app-builder/docs/locations#specify_a_multi-region_for_your_data_store
    client_options = (
        ClientOptions(api_endpoint=f"{location}-discoveryengine.googleapis.com")
        if location != "global"
        else None
    )

    # Create a client
    client = discoveryengine.DataStoreServiceClient(client_options=client_options)

    # The full resource name of the collection
    # e.g. projects/{project}/locations/{location}/collections/default_collection
    parent = client.collection_path(
        project=project_id,
        location=location,
        collection="default_collection",
    )

    data_store = discoveryengine.DataStore(
        display_name= datastore_name,
        # Options: GENERIC, MEDIA, HEALTHCARE_FHIR
        industry_vertical=discoveryengine.IndustryVertical.GENERIC,
        # Options: SOLUTION_TYPE_RECOMMENDATION, SOLUTION_TYPE_SEARCH, SOLUTION_TYPE_CHAT, SOLUTION_TYPE_GENERATIVE_CHAT
        solution_types=[discoveryengine.SolutionType.SOLUTION_TYPE_CHAT],
        # TODO(developer): Update content_config based on data store type.
        # Options: NO_CONTENT, CONTENT_REQUIRED, PUBLIC_WEBSITE
        content_config=discoveryengine.DataStore.ContentConfig.CONTENT_REQUIRED,
    )

    request = discoveryengine.CreateDataStoreRequest(
        parent=parent,
        data_store_id=data_store_id,
        data_store=data_store,
        # Optional: For Advanced Site Search Only
        # create_advanced_site_search=True,
    )

    # Make the request
    operation = client.create_data_store(request=request)

    print(f"Waiting for operation to complete: {operation.operation.name}")
    response = operation.result()

    # After the operation is complete,
    # get information from operation metadata
    metadata = discoveryengine.CreateDataStoreMetadata(operation.metadata)

    # Handle the response
    print(response)
    print(metadata)

    return operation.operation.name

def import_documents_gcs(
    project_id: str, location: str, datastore_id: str, gcs_uri: str
) -> str:
    """Imports documents from Google Cloud Storage (GCS) into a Discovery Engine datastore.

    Args:
        project_id: Your Google Cloud Project ID.
        location: The location of your Discovery Engine datastore (e.g., "global", "us-central1").
        datastore_id: The ID of your Discovery Engine datastore.
        gcs_uri: The Google Cloud Storage URI pointing to your documents.
                   This can be a single file or a wildcard pattern (e.g., "gs://bucket-name/path/to/documents/*.pdf").

    Returns:
        str: The operation name of the import process, which can be used to track its status.
    """
    client_options = (
        ClientOptions(api_endpoint=f"{location}-discoveryengine.googleapis.com")
        if location != "global"
        else None
    )

    # Create a client
    client = discoveryengine.DocumentServiceClient(client_options=client_options)

    # The full resource name of the search engine branch.
    parent = client.branch_path(
        project=project_id,
        location=location,
        data_store=datastore_id,
        branch="default_branch"
    )

    request = discoveryengine.ImportDocumentsRequest(
        parent=parent,
        gcs_source=discoveryengine.GcsSource(
            # Multiple URIs are supported
            input_uris=[gcs_uri],
            # Options:
            # - `content` - Unstructured documents (PDF, HTML, DOC, TXT, PPTX)
            # - `custom` - Unstructured documents with custom JSONL metadata
            # - `document` - Structured documents in the discoveryengine.Document format.
            # - `csv` - Unstructured documents with CSV metadata
            data_schema="content",
        ),
        # Options: `FULL`, `INCREMENTAL`
        reconciliation_mode=discoveryengine.ImportDocumentsRequest.ReconciliationMode.INCREMENTAL,
    )

    # Make the request
    operation = client.import_documents(request=request)

    print(f"Waiting for operation to complete: {operation.operation.name}")
    response = operation.result()

    # After the operation is complete,
    # get information from operation metadata
    metadata = discoveryengine.ImportDocumentsMetadata(operation.metadata)

    # Handle the response
    print(response)
    print(metadata)

    return operation.operation.name