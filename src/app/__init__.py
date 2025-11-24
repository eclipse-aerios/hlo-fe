'''
Docstring
'''
from fastapi import FastAPI
from app.routers import router

# FastAPI object customization
FASTAPI_TITLE = "hlo-fe-engine"
FASTAPI_DESCRIPTION = "HLO Front End exposure API"
FASTAPI_VERSION = "0.109.0"
FASTAPI_OPEN_API_URL = "/openapi.json"
FASTAPI_DOCS_URL = "/"

app = FastAPI(
    title=FASTAPI_TITLE,
    description=FASTAPI_DESCRIPTION,
    version=FASTAPI_VERSION,
    docs_url=FASTAPI_DOCS_URL,
    openapi_url=FASTAPI_OPEN_API_URL
)

app.include_router(router=router, tags=["hlo-fe-engine"])
