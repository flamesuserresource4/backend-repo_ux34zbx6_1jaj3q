"""
Database Schemas

Define your MongoDB collection schemas here using Pydantic models.
These schemas are used for data validation in your application.

Each Pydantic model represents a collection in your database.
Model name is converted to lowercase for the collection name:
- User -> "user" collection
- Product -> "product" collection
- BlogPost -> "blogs" collection
"""

from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List
from datetime import date

# Example schemas (replace with your own):

class User(BaseModel):
    """
    Users collection schema
    Collection name: "user" (lowercase of class name)
    """
    name: str = Field(..., description="Full name")
    email: str = Field(..., description="Email address")
    address: str = Field(..., description="Address")
    age: Optional[int] = Field(None, ge=0, le=120, description="Age in years")
    is_active: bool = Field(True, description="Whether user is active")

class Product(BaseModel):
    """
    Products collection schema
    Collection name: "product" (lowercase of class name)
    """
    title: str = Field(..., description="Product title")
    description: Optional[str] = Field(None, description="Product description")
    price: float = Field(..., ge=0, description="Price in dollars")
    category: str = Field(..., description="Product category")
    in_stock: bool = Field(True, description="Whether product is in stock")

# Car rental app schemas

class Car(BaseModel):
    """
    Cars available for rental
    Collection name: "car"
    """
    make: str = Field(..., description="Manufacturer, e.g., Toyota")
    model: str = Field(..., description="Model, e.g., Corolla")
    year: int = Field(..., ge=1990, le=2100, description="Year of manufacture")
    transmission: str = Field(..., description="Transmission type, e.g., Automatic/Manual")
    seats: int = Field(..., ge=2, le=9, description="Number of seats")
    fuel: str = Field(..., description="Fuel type, e.g., Petrol/Diesel/Hybrid/EV")
    price_per_day: float = Field(..., ge=0, description="Price per day in EUR")
    image: Optional[HttpUrl] = Field(None, description="Image URL of the car")
    features: Optional[List[str]] = Field(default=None, description="Key features list")

class Booking(BaseModel):
    """
    Bookings for cars
    Collection name: "booking"
    """
    car_id: str = Field(..., description="ID of the car being booked")
    customer_name: str = Field(..., description="Customer full name")
    customer_email: str = Field(..., description="Customer email")
    customer_phone: Optional[str] = Field(None, description="Customer phone number")
    start_date: date = Field(..., description="Rental start date (YYYY-MM-DD)")
    end_date: date = Field(..., description="Rental end date (YYYY-MM-DD)")
