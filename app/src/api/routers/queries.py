# src/api/routers/queries.py
import os, sys
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

# go 2 lvls up
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))

from rag.query_vector_storage import query_rag, QueryResponse


class SubmitQueryRequest(BaseModel):
    query_text: str


router = APIRouter()


@router.post("/post-query")
async def post_query_endpoint(request: SubmitQueryRequest) -> Optional[QueryResponse]:
    query_response = query_rag(request.query_text)
    if not query_response:
        raise HTTPException(status_code=404, detail="Couldn't find relevant data")
    return query_response
