from sqlalchemy import create_engine #make connection to MySQL databases
from sqlalchemy.orm import sessionmaker #make session to interact with database
from models import Base #to make table
import os
from dotenv import load_dotenv
load_dotenv()
#url below is postgreSQL database, useing 5432 as port numbers 
DATABASE_URL =  os.getenv("DATABASE_URL") #to show the engine below the address, password, host, etc, so engine could access db

engine = create_engine( #make connection to db
    DATABASE_URL,
    echo=True, #to print all SQL Queries (only helps in learning)
    pool_pre_ping=True #to check if connection is alive before using 
)

#Note: EVERY DATABASE OPERATION NEED session to work/interact with database

SessionLocal = sessionmaker( #Sessionlocal is a factoory that produce a session to interact with db
    autocommit=False, #so system wont autocommit request to db (safer), but do it as ordered manually using ".commit()"
    autoflush=False, #manually sending query to db, not auto (safer)
    bind = engine #to bind the session to engine, so session know where to query. (bind = method from sessionmaker)
)

def create_tables(): #function that read the models.py then create it to sql tables
    #Base.metadata = all the info of all class that inherit from Base(Order, OrderItem)
    Base.metadata.create_all(bind=engine) #create_all = read all info from metadata then generate table. bind=engine: to show the location address that table will be created at
    print("Database tables created successfully!")

def get_db(): #will be called to give session to API endpoints(like get, post, delete, etc) to interact with db
    db = SessionLocal() #db is now a session that inherrit all of its method
    try:
        yield db #PAUSE for a while, give db to endpoint, endpoint use db(session), endpoints done using db, then UNPAUSE 
    finally:
        db.close() #close the db(session)