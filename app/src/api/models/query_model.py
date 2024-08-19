from uuid import uuid4  # random unique uuid
from time import time
from os import environ
from typing import List, Optional, Dict, Any
from logging import basicConfig, getLogger, INFO
import boto3
from botocore.exceptions import ClientError
from pydantic import BaseModel, Field

# from dotenv import load_dotenv

# load_dotenv()  # local testing outside container

DYNAMODB_TABLE_NAME = environ.get("DYNAMODB_TABLE_NAME")
GLOBAL_SECONDARY_INDEX = "queries_by_user_id"  # to speed up queries on non-key attribute "user_id"
TTL_EXPIRE_WEEKS = 1
# The timestamp must be stored in Unix epoch time format at the seconds granularity
# https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/TTL.html
TTL_EXPIRE_TIMESTAMP = 60 * 60 * 24 * 7 * TTL_EXPIRE_WEEKS

# set up logger
basicConfig(level=INFO)
logger = getLogger()


class QueryModel(BaseModel):
    query_id: str = Field(default_factory=lambda: uuid4().hex)
    user_id: str = "nobody"
    created_at_unix_timestamp: int = Field(default_factory=lambda: int(time()))  # unix timestamp
    time_to_live_unix_timestamp: int = Field(default_factory=lambda: int(time() + TTL_EXPIRE_TIMESTAMP))
    query_text: str = "what are the available services that stellar web solutions offer?"
    response_text: Optional[str] = None
    sources: List[str] = Field(default_factory=list)

    @classmethod
    def get_table(cls):
        dynamodb = boto3.resource("dynamodb")
        return dynamodb.Table(DYNAMODB_TABLE_NAME)

    def as_dynamodb_item(self) -> Dict[str, Any]:
        item = {}
        for key, value in self.model_dump().items():
            if value:
                item[key] = value
        return item

    def create_or_replace_item(self) -> None:
        item = self.as_dynamodb_item()
        try:
            response = self.get_table().put_item(Item=item)
            print(response)
        except ClientError as e:  # most common exception, provided by an AWS service to a Boto3 client
            logger.error(e)
            raise e

    @classmethod
    def get_item_by_query_id(cls, query_id: str) -> Optional["QueryModel"]:
        try:
            response = cls.get_table().get_item(Key={"query_id": query_id})
        except ClientError as e:
            logger.error(e)
            return None

        if "Item" not in response:
            return None
        else:
            item = response["Item"]
            return cls(**item)  # unpack item data and use it to create new QueryModel instance

    @classmethod
    def get_items_by_user_id(cls, user_id: str, count: int) -> List["QueryModel"]:
        try:
            response = cls.get_table().query(
                IndexName=GLOBAL_SECONDARY_INDEX,
                KeyConditionExpression="user_id = :user_id",
                ExpressionAttributeValues={":user_id": user_id},
                Limit=count,
                ScanIndexForward=False,  # sort by descending order
            )
        except ClientError as e:
            logger.error(e)
            return []

        items = response.get("Items", [])
        result = []
        for item in items:
            result.append(cls(**item))
        return result
