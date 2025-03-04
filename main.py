from fastapi import FastAPI, HTTPException
from pymongo import MongoClient
from pydantic import BaseModel
import logging
import uvicorn

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('/logs_zain')]  # Send logs to the console
)

# Create a logger
logger = logging.getLogger(__name__)
app = FastAPI()

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")  # Replace with your MongoDB connection string
db = client['user_database']
users = db['users']

# Pydantic model for request validation
class User(BaseModel):
    fullName: str
    email: str
    password: str
    cnic: str
    city: str
    contact: str

@app.post("/create-account")
async def create_account(user: User):
    logger.info(f"Received user data: {user.dict()}")  # Log incoming data

    # Check if email already exists
    existing_user = users.find_one({"email": user.email})
    if existing_user:
        logger.warning(f"Email already registered: {user.email}")  # Log duplicate email
        raise HTTPException(status_code=400, detail="Email already registered")

    # Insert user data into MongoDB
    try:
        result = users.insert_one(user.dict())
        if result.inserted_id:
            logger.info(f"Inserted user ID: {str(result.inserted_id)}")  # Log inserted ID
            return {"message": "Account created successfully", "user_id": str(result.inserted_id)}
        else:
            logger.error("Failed to insert user data into MongoDB")  # Log failure
            raise HTTPException(status_code=500, detail="Failed to insert user data into MongoDB")
    except Exception as e:
        logger.error(f"Error inserting user data: {e}")  # Log any exceptions
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
    
# Pydantic model for request validation
class UserLogin(BaseModel):
    username: str
    password: str

@app.post("/login")
async def login(user: UserLogin):
    logger.info(f"Received login data: {user.dict()}")  # Log incoming data

    # Check if user exists
    existing_user = users.find_one({"fullName": user.username})
    if not existing_user:
        logger.warning(f"User not found: {user.username}")  # Log user not found
        raise HTTPException(status_code=400, detail="User not found. Please check your username.")

    # Check if password matches
    if existing_user["password"] != user.password:
        logger.warning(f"Incorrect password for user: {user.username}")  # Log incorrect password
        raise HTTPException(status_code=400, detail="Incorrect password. Please try again.")

    logger.info(f"User logged in successfully: {user.username}")  # Log successful login
    return {"message": "Logged in successfully", "user_id": str(existing_user["_id"]), "fullName": existing_user["fullName"]}

if __name__ == "__main__":
    PORT = int(os.getenv("PORT", 8000))  # Default to 8000 if PORT is not set
    uvicorn.run(app, host="0.0.0.0", port=PORT)