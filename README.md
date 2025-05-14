# Cloud Run
gcloud config set project [PROJECT_ID]

gcloud config set run/region us-central1

cd createticket-webhook

gcloud run deploy --source .

gcloud run deploy ticket-hook \
  --source . \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars="PROJECT_ID=your-actual-project-id" \
  --set-env-vars="BIGQUERY_DATASET_ID=your-dataset-id" \
  --set-env-vars="BIGQUERY_TABLE_ID=your-table-id" \
  --set-env-vars="BIGQUERY_TABLE_ID_WA=your-other-table-id"
  # Add any other flags you normally use, like --service-account

curl -X POST http://localhost:8080/webhook \
-H "Content-Type: application/json" \
-d @request-file.json

curl -X POST http://localhost:8080/check_status \
-H "Content-Type: application/json" \
-d @request-file-copy.json
