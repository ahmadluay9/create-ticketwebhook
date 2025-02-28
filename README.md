# Cloud Run
gcloud config set project [PROJECT_ID]

gcloud config set run/region us-central1

cd createticket-webhook

gcloud run deploy --source .

curl -X POST http://localhost:8080/webhook \
-H "Content-Type: application/json" \
-d @request-file.json

curl -X POST http://localhost:8080/check_status \
-H "Content-Type: application/json" \
-d @request-file-copy.json
