# src/api/routers/queries.py
import os, sys
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

# go 2 lvls up
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))

from rag.query_vector_storage import query_rag
from api.models.query_model import QueryModel


class SubmitQueryRequest(BaseModel):
    query_text: str


router = APIRouter()


@router.get("/get-queries/{query_id}")
async def get_query_endpoint(query_id: str) -> Optional[QueryModel]:
    query = QueryModel.get_item_by_query_id(query_id)
    if not query:
        raise HTTPException(status_code=404, detail="Query not found")
    return query


@router.post("/post-query")
async def post_query_endpoint(request: SubmitQueryRequest) -> Optional[QueryModel]:
    query_response = query_rag(request.query_text)

    new_query = QueryModel(
        query_text=request.query_text,
        response_text=query_response.response_text,
        sources=query_response.sources,
    )

    new_query.create_or_replace_item()

    if not new_query:
        raise HTTPException(status_code=404, detail="Couldn't find relevant data")
    return new_query
