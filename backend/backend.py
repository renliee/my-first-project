from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from db import get_db, create_tables
from models import Order, OrderItem
from schemas import OrderCreate, OrderResponse, OrderDetailResponse, OrderStatusUpdate

app = FastAPI(title = "Restaurant API") #app now inherit all the method of FastAPI

#why use decorator? decorator means : Function below (def startup) is registered to FastAPI as handler event startup
@app.on_event("startup") #on_event is a method from app -> on_event("nameofevent"), on this one is startup method(what to do before running the server), there is also shutdown(what to do after the server shutdown)
def startup():
    create_tables() #before running the server, create the database tables first
    print("Server started!")

@app.get("/") #get is a method from app to retrive info, others are: delete, post, put, etc. "/" is the url. so this means: "GET http://localhost:8000/docs""
def root():
    return {"message": "Restaurant API is running"} #if he open the the url links, will return message to user and show it at the browser

#.post method to add more data to database. (usually input schemas at the function, then response format at the @)
@app.post("/orders", response_model = OrderDetailResponse) # "/orders" means "POST /orders". response_model is from fastapi. after function below ends, wil return response of schemas "OrderResponse" to client
def create_order(order_data: OrderCreate, db: Session = Depends(get_db)): #order_data contains the inputted data from client, if there is missing info/different format with the schemas, wont interact with db. NEXT, db: get the ability of session to connect database. ": Session" is just a info of the type to the system (Depends used everytime wanna call session)
    total = sum(item.price * item.quantity for item in order_data.items) #for every items at OrderCreate (List of OrderItemCreate) from schemas.py, count total of all them by their qty

    new_order = Order(  #new order now access Order in models.py and update the name,total, and status
        customer_name = order_data.customer_name, #order_data.costumer_name is to access the inputted name from the user and update the customer_name in Order from models.py
        table_number = order_data.table_number,
        total = total,
        status = "pending"
    )
    #at this point, id and created_at at new_order still empty bcs the data isnt updated yet to db, db will define it automatically later

    for item_data in order_data.items: #for every items at OrderCreate 
        order_item = OrderItem(
            item_key = item_data.item_key,
            name = item_data.name,
            quantity = item_data.quantity,
            price = item_data.price
        )
        new_order.items.append(order_item) #add every detailed items after the order summary. new_order.items is from OrderCreate from schemas
    
    db.add(new_order) #add new_order to session
    db.commit() #officially added to db
    db.refresh(new_order) #this refresh will update the id (usually increment by 1 from the last id) and define the created_at using "datetime.utcnow" method

    return new_order #function return object new_order and fastapi convert it to response_model schemas before showing it to the client

#to get all orders
@app.get("/orders", response_model = List[OrderDetailResponse]) #response is a list of Order (each data must be the same as schemas)
def get_orders(db: Session = Depends(get_db)): 
    orders = db.query(Order).all() #db.query(Order) similar to "SELECT * FROM Order(orders)" then .all() to take each line
    return orders #return the list of Order, check with schemas, convert to json, show to client

#to get an order and its detailed items (by input order_id)
@app.get("/orders/{order_id}", response_model = OrderDetailResponse) #format is: "/orders/21". {order_id} is like: "hey system, there will be value here, input that value to otder_id later". /orders is just for readability, almost no impact on system if changed
def get_order(order_id: int, db: Session = Depends(get_db)): #order_id will recieve input as int 
    order = db.query(Order).filter(Order.id == order_id).first() #.filter similar to WHERE in sql, to filter data. then .first, to take the first data thats found at the filter

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    return order

@app.delete("/orders/{order_id}") #to delete order(by input order_id)
def delete_order(order_id: int, db: Session = Depends(get_db)):
    #will delete order founded and all it items due to cascade
    order = db.query(Order).filter(Order.id == order_id).first() #select all orders, filter it all by searching for the same id, pick the first matched id

    if not order:
        raise HTTPException(status_code=404, detail="Order not found") 
    
    db.delete(order) #delete data at db that has same info as data founded in order 
    db.commit()

    return {"message" : f"Order {order_id} deleted successfully!"} #will return json message to client (no need schemas bcs not complex and could directly return it)

#endpoints for cashiers so they can update the status of order
@app.patch("/orders/{order_id}/status", response_model = OrderResponse) #technically, could only use /{order_id} bcs order_id is not from schemas(if status_update below isnt from schemas, then will need to add /{status_update} also), if order_id from schemas then not a must to use /{order_id}
def update_order_status(order_id: int, status_update: OrderStatusUpdate, db: Session = Depends(get_db)): #needed to input order id that wanna be changed and the new status
    order = db.query(Order).filter(Order.id == order_id).first()

    if not order:
        raise HTTPException(status_code = 404, detail="Order not found")
    order.status = status_update.status
    db.commit()
    db.refresh(order)

    return order