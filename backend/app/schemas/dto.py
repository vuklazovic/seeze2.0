from pydantic import BaseModel
from typing import Optional, List, Dict, Any


class CarDealDTO(BaseModel):
    """DTO for car deal information sent to frontend"""
    make: str
    model: str
    trim: Optional[str] = None
    price: Optional[float] = None
    potential_profit: Optional[float] = None
    mileage: Optional[int] = None
    image: Optional[str] = None
    link: Optional[str] = None


class CarDealsResponseDTO(BaseModel):
    """DTO for car deals search results"""
    success: bool
    total_cars: int
    cars: List[CarDealDTO]
    error: Optional[str] = None 