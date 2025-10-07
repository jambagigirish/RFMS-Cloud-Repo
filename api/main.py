
from fastapi import FastAPI, Depends
from pydantic import BaseModel
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker, Session
from minio import Minio
import redis, hashlib, io, json
from datetime import timedelta
from common.config import POSTGRES_DSN, S3_ENDPOINT, S3_ACCESS_KEY, S3_SECRET_KEY, S3_BUCKET, REDIS_URL, REGION
from .models import Base, Replica

engine = create_engine(POSTGRES_DSN, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, future=True)
Base.metadata.create_all(engine)
s3 = Minio(S3_ENDPOINT.replace("http://", "").replace("https://", ""), access_key=S3_ACCESS_KEY, secret_key=S3_SECRET_KEY, secure=False)
r = redis.Redis.from_url(REDIS_URL, decode_responses=True)
app = FastAPI(title="RFMS Cloud API")

class RegisterReplica(BaseModel):
    group_id: str
    object_key: str
    size_bytes: int
    checksum: str | None = None
    metadata: dict = {}

@app.post("/replicas/register")
def register_replica(req: RegisterReplica, db: Session = Depends(lambda: SessionLocal())):
    rc = db.execute(select(Replica).where(Replica.group_id==req.group_id, Replica.object_key==req.object_key)).scalar_one_or_none()
    if rc:
        rc.size_bytes = req.size_bytes
        rc.checksum = req.checksum or rc.checksum
        db.commit()
        return {"status":"updated","id":rc.id}
    rr = Replica(group_id=req.group_id, object_key=req.object_key, size_bytes=req.size_bytes, checksum=req.checksum or "", metadata=req.metadata, vector_clock={REGION:1})
    db.add(rr); db.commit(); db.refresh(rr)
    r.xadd("rfms:events", {"type":"replica.created","group_id":req.group_id,"object_key":req.object_key})
    return {"status":"created","id":rr.id}

@app.get("/replicas/{group_id}")
def list_replicas(group_id: str, db: Session = Depends(lambda: SessionLocal())):
    rows = db.execute(select(Replica).where(Replica.group_id==group_id)).scalars().all()
    return [{"object_key":r.object_key,"checksum":r.checksum,"updated_at":r.updated_at.isoformat()} for r in rows]

@app.post("/objects/put")
def put_object(req: RegisterReplica, db: Session = Depends(lambda: SessionLocal())):
    data = json.dumps(req.metadata).encode("utf-8")
    checksum = hashlib.sha256(data).hexdigest()
    s3.put_object(S3_BUCKET, f"{REGION}/{req.group_id}/{req.object_key}", io.BytesIO(data), len(data))
    return register_replica(RegisterReplica(group_id=req.group_id, object_key=req.object_key, size_bytes=len(data), checksum=checksum, metadata=req.metadata), db)
