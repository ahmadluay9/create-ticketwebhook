# Cloud Run
gcloud config set project [PROJECT_ID]
cd createticket-webhook
gcloud run deploy --source .

curl -X POST http://localhost:8080/webhook \
-H "Content-Type: application/json" \
-d @request-file.json

