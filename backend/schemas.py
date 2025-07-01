from pydantic import BaseModel
from typing import Optional

class DocumentBase(BaseModel):
    id: int
    filename: str
    storage_path: str
    upload_timestamp: Optional[str]
    status: str
    owner_id: int

    class Config:
        orm_mode = True

class DocumentChunkBase(BaseModel):
    id: int
    document_id: int
    chunk_text: str
    chunk_metadata: str

    class Config:
        orm_mode = True 