import logging
from fastapi import APIRouter, HTTPException, Request, Depends
from typing import List, Dict, Any

from app.services.llm_service import LLMService
from app.core.logging import log_exception

logger = logging.getLogger(__name__)
router = APIRouter()

def get_llm_service() -> LLMService:
    return LLMService()

def get_user_email(request: Request) -> str:
    return getattr(request.state, 'user_email', 'unknown')

@router.get("/providers")
async def get_providers(
    request: Request,
    llm_service: LLMService = Depends(get_llm_service),
    user_email: str = Depends(get_user_email)
) -> List[Dict[str, Any]]:
    try:
        providers = await llm_service.get_available_providers(user_email)
        return providers
    except Exception as e:
        log_exception(logger, e, "retrieving LLM providers")
        raise HTTPException(status_code=500, detail="Failed to retrieve LLM providers")

@router.get("/providers/{provider_id}")
async def get_provider_details(
    provider_id: str,
    request: Request,
    llm_service: LLMService = Depends(get_llm_service),
    user_email: str = Depends(get_user_email)
) -> Dict[str, Any]:
    try:
        provider = await llm_service.get_provider_details(provider_id, user_email)
        if not provider:
            raise HTTPException(status_code=404, detail="Provider not found")
        return provider
    except HTTPException:
        raise
    except Exception as e:
        log_exception(logger, e, f"retrieving provider details for {provider_id}")
        raise HTTPException(status_code=500, detail="Failed to retrieve provider details")

@router.post("/providers/{provider_id}/validate")
async def validate_provider_access(
    provider_id: str,
    request: Request,
    llm_service: LLMService = Depends(get_llm_service),
    user_email: str = Depends(get_user_email)
) -> Dict[str, Any]:
    try:
        validation = await llm_service.validate_provider_access(provider_id, user_email)
        return validation
    except Exception as e:
        log_exception(logger, e, f"validating provider access for {provider_id}")
        raise HTTPException(status_code=500, detail="Failed to validate provider access")