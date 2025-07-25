#!/bin/bash
# Wait for MinIO to be ready
sleep 10

# Install MinIO client
curl -o /tmp/mc https://dl.min.io/client/mc/release/linux-amd64/mc
chmod +x /tmp/mc

# Configure MinIO client
/tmp/mc alias set local http://minio:9000 minioadmin minioadmin123

# Create bucket
/tmp/mc mb local/ai-video-chaptering

# Set public policy for development
/tmp/mc anonymous set public local/ai-video-chaptering

echo "MinIO bucket setup complete"
