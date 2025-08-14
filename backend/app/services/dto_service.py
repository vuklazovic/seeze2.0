from typing import List, Dict, Any, Optional
from app.schemas.dto import CarDealDTO, CarDealsResponseDTO
import logging

logger = logging.getLogger(__name__)


class DTOService:
    """Service for converting MongoDB car data to frontend DTOs"""
    
    @staticmethod
    def convert_car_to_dto(raw_car: Dict[str, Any]) -> CarDealDTO:
        """Convert raw MongoDB car data to CarDealDTO"""
        try:
            # Extract make and model
            make = raw_car.get('make', 'Unknown')
            model = raw_car.get('model', 'Unknown')
            trim = raw_car.get('trim')
            
            # Extract and convert price
            price = None
            price_raw = raw_car.get('price')
            if price_raw is not None:
                try:
                    price_str = str(price_raw).replace('$', '').replace(',', '').strip()
                    price = float(price_str) if price_str else None
                except (ValueError, TypeError):
                    price = None

            # Extract and convert price
            potential_profit = None
            potential_profit_raw = raw_car.get('potential_profit')
            if potential_profit_raw is not None:
                try:
                    potential_profit_str = str(potential_profit_raw).replace('$', '').replace(',', '').strip()
                    potential_profit = float(potential_profit_str) if potential_profit_str else None
                except (ValueError, TypeError):
                    potential_profit = None
            
            # Extract and convert mileage
            mileage = None
            mileage_raw = raw_car.get('mileage')
            if mileage_raw is not None:
                try:
                    mileage_str = str(mileage_raw).replace(',', '').replace('miles', '').replace('mi', '').strip()
                    mileage = int(float(mileage_str)) if mileage_str else None
                except (ValueError, TypeError):
                    mileage = None
            
            # Extract image (first image from list)
            image = None
            images = raw_car.get('images', [])
            if images and isinstance(images, list) and len(images) > 0:
                image = images[0]
            
            # Extract link
            link = raw_car.get('link')
            
            return CarDealDTO(
                make=make,
                model=model,
                trim=trim,
                price=price,
                potential_profit=potential_profit,
                mileage=mileage,
                image=image,
                link=link
            )
            
        except Exception as e:
            logger.error(f"Error converting car to DTO: {e}")
            return CarDealDTO(
                make=raw_car.get('make', 'Unknown'),
                model=raw_car.get('model', 'Unknown')
            )
    
    @staticmethod
    def convert_cars_to_dto_response(raw_cars: List[Dict[str, Any]],
                                   error: Optional[str] = None) -> CarDealsResponseDTO:
        """Convert raw cars list to CarDealsResponseDTO"""
        try:
            # Convert each car to DTO
            car_dtos = [DTOService.convert_car_to_dto(car) for car in raw_cars]
            
            return CarDealsResponseDTO(
                success=error is None,
                total_cars=len(car_dtos),
                cars=car_dtos,
                error=error
            )
            
        except Exception as e:
            logger.error(f"Error converting cars to DTO response: {e}")
            return CarDealsResponseDTO(
                success=False,
                total_cars=0,
                cars=[],
                error=str(e)
            ) 