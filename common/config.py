
import os

POSTGRES_DSN = os.getenv("POSTGRES_DSN", "postgresql+psycopg2://rfms:rfms@postgres:5432/rfms")
S3_ENDPOINT   = os.getenv("S3_ENDPOINT", "http://minio:9000")
S3_ACCESS_KEY = os.getenv("S3_ACCESS_KEY", "minioadmin")
S3_SECRET_KEY = os.getenv("S3_SECRET_KEY", "minioadmin")
S3_BUCKET     = os.getenv("S3_BUCKET", "rfms")
REDIS_URL     = os.getenv("REDIS_URL", "redis://redis:6379/0")
REGION        = os.getenv("REGION", "region-a")
