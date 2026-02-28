#!/bin/bash
set -euo pipefail

echo "[localstack-init] Creating SQS queue..."
awslocal sqs create-queue \
  --queue-name hairstyle-jobs \
  --attributes VisibilityTimeout=1800,MessageRetentionPeriod=86400

echo "[localstack-init] SQS queue 'hairstyle-jobs' ready."

# Print queue URL for confirmation
awslocal sqs get-queue-url --queue-name hairstyle-jobs
echo "[localstack-init] Done."
