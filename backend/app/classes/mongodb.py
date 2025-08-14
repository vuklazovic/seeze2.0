from typing import Dict, List, Any, Optional
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
import logging, sys
from app.core import settings
from app.services.extraction_service import ExtractionService
from urllib.parse import quote_plus

logger = logging.getLogger(__name__)


class MongoDB:
    """MongoDB connection and query executor - Singleton pattern"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MongoDB, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize MongoDB connection using environment variables"""
        if not self._initialized:
            print(f"=== Connecting to MongoDb Seeze server   ====")
            self.connection_string = self._build_connection_string()
            self.database_name = settings.MONGODB_DATABASE_NAME
            self.collection_name = settings.MONGODB_COLLECTION_NAME
            self.client: Optional[MongoClient] = None
            self.database = None
            self.collection = None
            self._connect()
            self._initialized = True
            self.extraction_service = ExtractionService()
    
    def _build_connection_string(self) -> str:
        """Build MongoDB connection string from individual environment variables"""
        username = settings.MONGODB_USERNAME
        password = settings.MONGODB_PASSWORD
        host = settings.MONGODB_HOST
        port = settings.MONGODB_PORT
        auth_source = settings.MONGODB_AUTH_SOURCE
        
        # If username and password are provided, use authentication
        if username and password:
            return f"mongodb://{username}:{quote_plus(password)}@{host}:{port}/?authSource={auth_source}"
        else:
            # No authentication
            return f"mongodb://{host}:{port}"
    
    def _connect(self) -> None:
        """Establish connection to MongoDB"""
        try:
            self.client = MongoClient(
                self.connection_string,
                # serverSelectionTimeoutMS=5000,
                # connectTimeoutMS=5000,
                # socketTimeoutMS=5000
            )
            # Test the connection
            self.client.admin.command('ping')
            self.database = self.client[self.database_name]
            self.collection = self.database[self.collection_name]
            logger.info(f"Connected to MongoDB: {self.database_name}.{self.collection_name}")
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise ConnectionError(f"Could not connect to MongoDB: {e}")
    
    def execute_query(self, filter_dict: Dict[str, Any], limit: int = 50, skip: int = 0) -> List[Dict[str, Any]]:
        """
        Execute a query on the specified collection
        
        Args:
            filter_dict: MongoDB filter dictionary
            limit: Maximum number of results
            skip: Number of results to skip
            
        Returns:
            List of documents matching the filter
        """
        try:
            results = []
            cursor = self.collection.find(filter_dict).sort('potential_profit_percentage', -1).limit(limit)
            for doc in cursor:
                del doc['_id']
                results.append(doc)
            return results
        except Exception as e:
            logger.error(f"Error executing query: {e}")
            raise
    
    def convert_filter_to_mongo(self, llm_filter: List[Dict[str, Any]], use_seeze_syntax_fields: bool = True) -> Dict[str, Any]:
        """
        Convert LLM filter format to MongoDB filter format with improved logic
        
        Args:
            llm_filter: Filter from LLM in format:
                [
                    {
                        "make": {"value": "BMW", "operator": "eq"},
                        "model": {"value": "M3", "operator": "eq"},
                        "year": {"value": 2023, "operator": "gte"},
                        "price": {"min": 50000, "max": 100000, "operator": "between"}
                    }
                ]
            use_seeze_syntax_fields: Whether to use Seeze-specific field syntax
            
        Returns:
            MongoDB filter dictionary with $and conditions for multiple car groups
        """
        mongo_filter = []

        def handle_operator(field, rule):
            """Handle different operators and convert to MongoDB format"""
            op = rule.get("operator")
            val = rule.get("value") if "value" in rule else rule.get("values") 
            min_val = rule.get("min")
            max_val = rule.get("max")

            # Apply Seeze field mapping if enabled
            if use_seeze_syntax_fields:
                if field == 'make':
                    field = 'extracted_make'
                elif field == 'model':
                    field = 'extracted_model'
                elif field == 'trim':
                    field = 'extracted_trim'
                elif field == 'location':
                    field = 'zip_num'

            if op == "eq":
                return {field: val}
            elif op == "not":
                return {field: {"$ne": val}}
            elif op == "lt":
                return {field: {"$lt": val}}
            elif op == "lte":
                return {field: {"$lte": val}}
            elif op == "gt":
                return {field: {"$gt": val}}
            elif op == "gte":
                return {field: {"$gte": val}}
            elif op == "between":
                return {field: {"$gte": min_val, "$lte": max_val}}
            elif op == "in":
                return {field: {"$in": val if isinstance(val, list) else [val]}}
            elif op == "nin":
                return {field: {"$nin": val if isinstance(val, list) else [val]}}
            elif op == "regex":
                return {field: {"$regex": val, "$options": "i"}}
            else:
                raise ValueError(f"Unsupported operator: {op}")

        # Process each car group (each item in the list represents a car group)
        for car_group in llm_filter:
            and_conditions = []
            
            for key, rule in car_group.items():
                if not isinstance(rule, dict) or "operator" not in rule:
                    # Skip invalid rules
                    continue
                
                try:
                    and_conditions.append(handle_operator(key, rule))
                except Exception as e:
                    logger.warning(f"Skipping field '{key}' due to error: {e}")
                    continue
            
            # Add $and condition for this car group if we have valid conditions
            if and_conditions:
                mongo_filter.append({"$and": and_conditions})

        # Return empty filter if no valid conditions found
        if not mongo_filter:
            return {}

        # If we have multiple car groups, wrap them in $or
        if len(mongo_filter) > 1:
            if use_seeze_syntax_fields:
                self._walk_through_filter_and_setting_up_fields(mongo_filter)
            return {"$or": mongo_filter}
        else:
            # For single car group, optimize the filter structure
            single_filter = mongo_filter[0]
            if use_seeze_syntax_fields:
                self._walk_through_filter_and_setting_up_fields([single_filter])
            
            # If there's only one condition in the $and, return it directly
            if "$and" in single_filter and len(single_filter["$and"]) == 1:
                return single_filter["$and"][0]
            else:
                return single_filter
    
    def _walk_through_filter_and_setting_up_fields(self, mongo_filter):
        """
        Process MongoDB filter to extract and enhance make/model/trim fields
        This method should be called only once per filter conversion
        """
        if isinstance(mongo_filter, dict):
            # Handle $and conditions (single car group)
            if "$and" in mongo_filter:
                self._process_car_group_conditions(mongo_filter["$and"])
            # Handle $or conditions (multiple car groups)
            elif "$or" in mongo_filter:
                for car_group in mongo_filter["$or"]:
                    if "$and" in car_group:
                        self._process_car_group_conditions(car_group["$and"])
        elif isinstance(mongo_filter, list):
            # Handle list of car groups
            for car_group in mongo_filter:
                if isinstance(car_group, dict) and "$and" in car_group:
                    self._process_car_group_conditions(car_group["$and"])

    def _process_car_group_conditions(self, conditions):
        """
        Process conditions for a single car group
        """
        # Collect make, model, trim values for extraction
        make_model_trim_values = {}
        mileage_conditions = []
        
        # First pass: collect all make/model/trim values and identify mileage conditions
        for condition in conditions:
            if isinstance(condition, dict):
                for field, value in condition.items():
                    if field in ['extracted_make', 'extracted_model', 'extracted_trim']:
                        if field not in make_model_trim_values:
                            make_model_trim_values[field] = []
                        if isinstance(value, str):
                            make_model_trim_values[field].append(value)
                    elif field == 'mileage':
                        # Collect all mileage conditions (both dict and simple values)
                        mileage_conditions.append((condition, field, value))
                    elif field == 'zip_num':
                        zip_value = value
                        # Convert values to integers based on the structure
                        if isinstance(zip_value, dict):
                            # Handle operators like 'in', 'not_in'
                            for operator, values in zip_value.items():
                                if isinstance(values, list):
                                    # Convert each ZIP code string to integer
                                    zip_value[operator] = [int(zip_str) for zip_str in values if zip_str.isdigit()]
                                elif isinstance(values, str) and values.isdigit():
                                    # Single string value
                                    zip_value[operator] = int(values)
                        elif isinstance(zip_value, list):
                            # Direct list of ZIP codes
                            condition['zip_num'] = [int(zip_str) for zip_str in zip_value if zip_str.isdigit()]
                        elif isinstance(zip_value, str) and zip_value.isdigit():
                            # Single ZIP code string
                            condition['zip_num'] = int(zip_value)
        
        # Build make_model_name for extraction if we have make/model/trim data
        if make_model_trim_values:
            make_model_name = ""
            if 'extracted_make' in make_model_trim_values:
                make_model_name += " ".join(make_model_trim_values['extracted_make']) + " "
            if 'extracted_model' in make_model_trim_values:
                make_model_name += " ".join(make_model_trim_values['extracted_model']) + " "
            if 'extracted_trim' in make_model_trim_values:
                make_model_name += " ".join(make_model_trim_values['extracted_trim'])
            
            # Perform extraction once per car group
            if make_model_name.strip():
                extracted_data = self.extraction_service.extract_car_info(make_model_name.strip())
                if extracted_data.get('success') and 'extracted_info' in extracted_data:
                    extracted_info = extracted_data['extracted_info']
                    
                    # Update conditions with extracted data
                    for condition in conditions:
                        if isinstance(condition, dict):
                            for field in ['extracted_make', 'extracted_model', 'extracted_trim']:
                                if field in condition and field in extracted_info and extracted_info[field] != ' ':
                                    condition[field] = extracted_info[field]
        
        # Process mileage conditions (10% tolerance)
        for condition, field, value in mileage_conditions:
            if isinstance(value, dict):
                if '$gte' in value and '$lte' in value:
                    # Already processed with tolerance
                    continue
                elif '$eq' in value:
                    # Convert $eq to tolerance range
                    eq_value = value['$eq']
                    if isinstance(eq_value, (int, float)):
                        tolerance = eq_value * 0.1
                        condition[field] = {
                            "$gte": int(eq_value - tolerance),
                            "$lte": int(eq_value + tolerance)
                        }
            elif isinstance(value, (int, float)):
                # Apply 10% tolerance to simple numeric values
                tolerance = value * 0.1
                condition[field] = {
                    "$gte": int(value - tolerance),
                    "$lte": int(value + tolerance)
                }

    def close(self) -> None:
        """Close the MongoDB connection"""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()

    def __del__(self):
        """Destructor to ensure connection is closed"""
        if not sys.is_finalizing():
            self.close()
