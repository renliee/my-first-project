from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship, DeclarativeBase
from datetime import datetime

#tablecontext: there will be 2 tables, table 1 as "orders" is a table with unique id that represent order summary by each customer. table 2 "order_items" also have unique id for each item detailed that belongs to some order's id

class Base(DeclarativeBase): #DeclarativeBase so SQLAlchemy know, class below is a table class
    pass

class Order(Base): #this table represent the order summary
    __tablename__ = "orders" #the real table's name at the database

    id = Column(Integer, primary_key=True, index=True) #primary_key means each order need to have an unique id, so now id = unique char for every order
    customer_name = Column(String(100), default="Guest")
    table_number = Column(Integer, nullable = False) #must be filled by user
    total = Column(Integer)
    status = Column(String(25), default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)

    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan") #to connect with order_items table using relationship. cascade: if order deleted, delete all its item

#table below represent each item detail that belongs to an order
class OrderItem(Base): #only name of class to be imported in different file with "Base" as parent
    __tablename__ = "order_items" #the table's name at the database

    id = Column(Integer, primary_key=True, index=True) #id unique each item
    order_id = Column(Integer, ForeignKey("orders.id")) #foreignkey shows that this item belongs to primarykey of some "orders.id"
    item_key = Column(String(50)) #name for database (nasi goreng)
    name = Column(String(100)) #a display name to user (Nasi Goreng)
    quantity = Column(Integer)
    price = Column(Integer)

    order = relationship("Order", back_populates="items") #to connect with Order uding relationship