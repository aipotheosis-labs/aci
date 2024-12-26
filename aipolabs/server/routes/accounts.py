import json
from typing import Annotated
from uuid import UUID

import requests
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from aipolabs.common.db import crud
from aipolabs.common.enums import SecurityScheme
from aipolabs.common.logging import get_logger
from aipolabs.common.schemas.accounts import AccountCreate
from aipolabs.server import dependencies as deps

router = APIRouter()
logger = get_logger(__name__)


# TODO:
# Note:
# - Use authlib to handle OAuth2 account linking by creating a new OAuth2 client for every request (avoid caching and concurrency issues)
# - For token refresh (when executing functions), either use authlib's oauth2 client/session or build the request manually.
#   If doing mannually, might need to handle dynamic url dicovery via discovery doc (e.g., google)
# - encrypt the state payload data to avoid tampering, parsing it in callback to get integration_id & account_name etc.
@router.post("/accounts")
async def link_account(
    account_create: AccountCreate,
    api_key_id: Annotated[UUID, Depends(deps.validate_api_key)],
    db_session: Annotated[Session, Depends(deps.yield_db_session)],
) -> RedirectResponse | dict:
    # validations
    # TODO: only allow linking accounts for enabled integrations?
    db_project = crud.get_project_by_api_key_id(db_session, api_key_id)
    db_integration = crud.get_integration(db_session, account_create.integration_id)
    if not db_integration:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Integration not found")
    if db_integration.project_id != db_project.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The integration does not belong to the project",
        )

    db_app = crud.get_app_by_id(db_session, db_integration.app_id)
    security_scheme = db_integration.security_scheme

    # for OAuth2 account, we need to redirect to the OAuth2 provider's authorization endpoint
    if security_scheme == SecurityScheme.OAUTH2:
        oauth_config = db_app.security_schemes.get("OAUTH2", {})
        if not oauth_config:
            raise HTTPException(500, "No OAUTH2 config present")

        # Attempt to fetch discovery document if available
        discovery_url = oauth_config.get("discovery_document_url")
        authorize_url = oauth_config.get("authorize_url")
        token_url = oauth_config.get("token_url")

        # If there's a discovery doc
        if discovery_url:
            try:
                resp = requests.get(discovery_url, timeout=5)
                resp.raise_for_status()
                disc_data = resp.json()
                # Override the static ones if discovered
                authorize_url = disc_data.get("authorization_endpoint", authorize_url)
                token_url = disc_data.get("token_endpoint", token_url)
            except Exception as e:
                logger.warning(f"Discovery doc fetch error for {discovery_url}: {e}")
                # fallback to static if present
                if not (authorize_url and token_url):
                    raise HTTPException(500, "Could not fetch discovery doc or fallback endpoints")

        # We must still have authorize_url, token_url now
        if not authorize_url:
            raise HTTPException(500, "No 'authorize_url' found from config or discovery")

        # Build up the redirect
        state_dict = {
            "integration_id": str(account_create.integration_id),
            "account_name": account_create.account_name,
        }
        state_str = json.dumps(state_dict)
        redirect_uri = oauth_config["redirect_uri"]
        client_id = oauth_config["client_id"]
        scope = oauth_config["scope"]

        # Example for building final authorize URL:
        final_auth_url = (
            f"{authorize_url}?"
            f"client_id={client_id}&"
            f"redirect_uri={redirect_uri}&"
            f"response_type=code&"
            f"scope={scope}&"
            f"state={state_str}"
        )
        return RedirectResponse(url=final_auth_url, status_code=status.HTTP_303_SEE_OTHER)

    elif security_scheme == SecurityScheme.API_KEY:
        # ... handle API key ...
        return {"status": "success"}

    else:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, f"Unsupported security scheme: {security_scheme}"
        )
