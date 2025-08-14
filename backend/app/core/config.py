from typing import List, Union
from pydantic import AnyHttpUrl, validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "Seeze Backend API"
    
    # MongoDB - Credentials 
    MONGODB_USERNAME: str = "MONGODB_USERNAME"
    MONGODB_PASSWORD: str = "MONGODB_PASSWORD"
    MONGODB_HOST: str = "MONGODB_HOST"
    MONGODB_PORT: str = "MONGODB_PORT"
    MONGODB_AUTH_SOURCE: str = "MONGODB_AUTH_SOURCE"

    # MongoDB - Databases/Collections
    MONGODB_DATABASE_NAME: str = "MONGODB_DATABASE_NAME"
    MONGODB_COLLECTION_NAME: str = "MONGODB_COLLECTION_NAME"

    # LLM Configuration
    LLM_TYPE: str = ""
    
    # large language Model - LOCAL
    LOCAL_LLM_URL: str = "LOCAL_LLM_URL"
    LOCAL_LLM_API_KEY: str = "LOCAL_LLM_API_KEY"
    LOCAL_LLM_MODEL_NAME: str = "LOCAL_LLM_MODEL_NAME"

    # large language Model - OpenAI
    OPENAI_API_KEY: str = "OPENAI_API_KEY"
    OPENAI_MODEL_NAME: str = "OPENAI_MODEL_NAME"
    

    # CORS Configuration
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []
    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    class Config:
        case_sensitive = True
        env_file = ".env"


settings = Settings() 