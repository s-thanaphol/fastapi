import json
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field
import motor.motor_asyncio
from bson.objectid import ObjectId
import os
from dotenv import load_dotenv

app = FastAPI()

# Load environment variables from .env file
load_dotenv()

switch = os.environ.get("MONGODB_AUTH")

if switch in ["True", "true", "yes", "1"]:
    uri = f"mongodb://{os.environ.get('MONGODB_USER')}" \
            + f":{os.environ.get('MONGODB_PASSWORD')}" \
            + f"@{os.environ.get('MONGODB_SERVER')}" \
            + f":{os.environ.get('MONGODB_PORT')}"
elif switch in ["False", "false", "no", "0"]:
    uri = f"mongodb://{os.environ.get('MONGODB_SERVER')}" \
            + f":{os.environ.get('MONGODB_PORT')}"
            
dbname = os.environ.get("MONGODB_NAME")
col_name = os.environ.get("MONGODB_COLLECTION")
            

# Connect to MongoDB using motor
client = motor.motor_asyncio.AsyncIOMotorClient(uri)
db = client[dbname]
collection = db[col_name]

# Model for your data
class CreateItemModel(BaseModel):
    name: str
    description: str
    
class ItemModel(CreateItemModel):
    id: str

class MessageResponse(BaseModel):
    message: str

# API route to create an item
@app.post("/items/",status_code=status.HTTP_201_CREATED,response_model=MessageResponse)
async def create_item(item: CreateItemModel):
    # data = {"name": item.name, "description": item.description}
    await collection.insert_one(item.model_dump())
    return {"message": "Item created successfully"}


@app.get("/items/",status_code=status.HTTP_200_OK,response_model=list[ItemModel])
async def get_all_products():
    products = []
    async for product in collection.find():
        product["id"] = str(product["_id"])
        products.append(ItemModel(**product))
    return products

# Get a specific item by name
@app.get("/items/{id}",status_code=status.HTTP_200_OK,response_model=ItemModel)
async def get_item(id: str):
    item = await collection.find_one({"_id": ObjectId(id)})
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    item["id"] = str(item["_id"]) 
    return ItemModel(**item)
    # a = {"name": item["name"], "description": item["description"], "id": str(item["_id"])}
    # print(type(a))
    # return a

# Update a post by ID
@app.patch("/items/{id}",status_code=status.HTTP_200_OK,response_model=MessageResponse)
async def update_post(id: str,item: CreateItemModel):
    result = await collection.update_one({"_id": ObjectId(item["_id"])}, item)
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="not found")
    return {"message": "Item patched successfully"}

# Delete a post by ID
@app.delete("/items/{id}",status_code=status.HTTP_200_OK,response_model=MessageResponse)
async def delete_post(id: str):
    result = await collection.delete_one({"_id": ObjectId(id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="item not found")
    return {"message": "item deleted successfully"}