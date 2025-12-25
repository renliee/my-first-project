#Pydantic models is to validate user input/request to database and to decide the format of output to frontend 
from pydantic import BaseModel #BaseModel = pydantic class for validation
from typing import List, Optional 
from datetime import datetime

class OrderItemCreate(BaseModel): #validate the user input/request
    item_key: str
    name: str
    quantity: int
    price: int

class OrderCreate(BaseModel): #validate that the information from user is complete 
    customer_name: Optional[str] = "Guest" #if user didnt input any name, default will be "Guest"
    table_number: int
    items: List[OrderItemCreate] #item is a list of OrderItemCreate. (List = library from typing)

class OrderResponse(BaseModel): #to create the format of summary data order to frontend
    id: int
    customer_name: str
    table_number: int
    total: int
    status: str
    created_at: datetime

    class Config: #so pydantic could understand the data, bcs sqlaclhemy return python object while pydantic could only read dictionary
        from_attributes = True #convert database object to Json/dictionary

class OrderItemResponse(BaseModel): #to create the format of each food to front end
    id: int
    #dont need order_id bcs we dont need to show the user each item is related to what order, bcs there is already id at the order summary
    item_key: str
    name: str
    quantity: int
    price: int

    class Config:
        from_attributes = True

class OrderDetailResponse(OrderResponse): #inherit all fields from OrderResponse
    items: List[OrderItemResponse] #add list of OrderItemResponse

    class Config:
        from_attributes = True

class OrderStatusUpdate(BaseModel): #to validate the string in patch method
    status: str