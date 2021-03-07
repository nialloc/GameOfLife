gcloud functions deploy gameoflife \
--runtime python38 \
--trigger-http \
--allow-unauthenticated \
--env-vars-file env.yaml