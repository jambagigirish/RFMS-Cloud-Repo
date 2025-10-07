
import redis, io
from minio import Minio
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from common.config import POSTGRES_DSN, S3_ENDPOINT, S3_ACCESS_KEY, S3_SECRET_KEY, S3_BUCKET, REDIS_URL
from api.models import Base, Replica

engine = create_engine(POSTGRES_DSN, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, future=True)
r = redis.Redis.from_url(REDIS_URL, decode_responses=True)
s3 = Minio(S3_ENDPOINT.replace("http://", "").replace("https://", ""), access_key=S3_ACCESS_KEY, secret_key=S3_SECRET_KEY, secure=False)

def worker():
    while True:
        msgs = r.xread({"rfms:events": "0"}, count=1, block=5000)
        if not msgs: continue
        for _, items in msgs:
            for msg_id, data in items:
                print("Replicating:", data)
                r.xack("rfms:events", "workers", msg_id)

if __name__ == "__main__":
    print("Worker started")
    worker()
