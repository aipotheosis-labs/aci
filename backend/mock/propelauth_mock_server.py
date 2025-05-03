from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/v1/refresh_token")
async def refresh_token() -> dict:
    return {
        "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsImtpZCI6IjA2YzZmZjc1LWVkODMtNDkzOC1iZWEzLTAzNDExYjc0MDc2ZSJ9.eyJzdWIiOiJlNTA4NzBkMi05ZGNkLTQ0ZmUtYTI3My0xYjljYzFlOTgyZGUiLCJpYXQiOjE3NDYyNzI5NDAsImV4cCI6MTc0NjI3NDc0MCwidXNlcl9pZCI6ImU1MDg3MGQyLTlkY2QtNDRmZS1hMjczLTFiOWNjMWU5ODJkZSIsImlzcyI6Imh0dHBzOi8vODM2Nzg3OC5wcm9wZWxhdXRodGVzdC5jb20iLCJlbWFpbCI6InppeHVhbnpoYW5nLnhAZ21haWwuY29tIiwib3JnX2lkX3RvX29yZ19tZW1iZXJfaW5mbyI6eyIxMDdlMDZkYS1lODU3LTQ4NjQtYmMxZC00YWRjYmEwMmFiNzYiOnsib3JnX2lkIjoiMTA3ZTA2ZGEtZTg1Ny00ODY0LWJjMWQtNGFkY2JhMDJhYjc2Iiwib3JnX25hbWUiOiJQZXJzb25hbCBmYTBIMW0iLCJ1cmxfc2FmZV9vcmdfbmFtZSI6InBlcnNvbmFsLWZhMGgxbSIsIm9yZ19tZXRhZGF0YSI6eyJwZXJzb25hbCI6dHJ1ZX0sInVzZXJfcm9sZSI6Ik93bmVyIiwiaW5oZXJpdGVkX3VzZXJfcm9sZXNfcGx1c19jdXJyZW50X3JvbGUiOlsiT3duZXIiLCJBZG1pbiIsIk1lbWJlciJdLCJvcmdfcm9sZV9zdHJ1Y3R1cmUiOiJzaW5nbGVfcm9sZV9pbl9oaWVyYXJjaHkiLCJhZGRpdGlvbmFsX3JvbGVzIjpbXSwidXNlcl9wZXJtaXNzaW9ucyI6WyJwcm9wZWxhdXRoOjpjYW5faW52aXRlIiwicHJvcGVsYXV0aDo6Y2FuX2NoYW5nZV9yb2xlcyIsInByb3BlbGF1dGg6OmNhbl9yZW1vdmVfdXNlcnMiLCJwcm9wZWxhdXRoOjpjYW5fc2V0dXBfc2FtbCIsInByb3BlbGF1dGg6OmNhbl9tYW5hZ2VfYXBpX2tleXMiLCJwcm9wZWxhdXRoOjpjYW5fZWRpdF9vcmdfYWNjZXNzIiwicHJvcGVsYXV0aDo6Y2FuX3VwZGF0ZV9vcmdfbWV0YWRhdGEiLCJwcm9wZWxhdXRoOjpjYW5fdmlld19vdGhlcl9tZW1iZXJzIiwicHJvcGVsYXV0aDo6Y2FuX2RlbGV0ZV9vcmciXX19LCJsb2dpbl9tZXRob2QiOnsibG9naW5fbWV0aG9kIjoic29jaWFsX3NzbyIsInByb3ZpZGVyIjoiR29vZ2xlIn19.eElE7YM62NOx29rHKtbDE8Z9Wd71QSCjZ5WAA4Xxd1vYru4PFrj2gDWqZSBGEAWZ7Un1O35CcYkaDou3fNulcuf43-xIeLXv_pZnw1Z7P1ZDb--e7FqgT_K_J_Ew5Nb4qwBo4csXQIw-tyK-kNbkFIqmK50WVaHUww5geUXmNx6NoiAilWCARQ5NH95fvAvC1uwBfuZw-2WoJxJQpZn5aPy3RbsYauoOG_uxFNg32mH3Oqdy1UJmj6-ZJPezi0OlO1fDIafNRiUBKk4Uidxom8oWcOSlwawARNiNxFIEhieMiv0M-HMUz8wTgxqBJJUNRVQislyTNAjuCpiapTwNhw",
        "expires_at_seconds": 174274740,
        "org_id_to_org_member_info": {
            "107e06da-e857-4864-bc1d-4adcba02ab76": {
                "org_id": "107e06da-e857-4864-bc1d-4adcba02ab76",
                "org_name": "Personal fa0H1m",
                "url_safe_org_name": "personal-fa0h1m",
                "org_metadata": {"personal": True},
                "user_role": "Owner",
                "inherited_user_roles_plus_current_role": ["Owner", "Admin", "Member"],
                "org_role_structure": "single_role_in_hierarchy",
                "additional_roles": [],
                "user_permissions": [
                    "propelauth::can_invite",
                    "propelauth::can_change_roles",
                    "propelauth::can_remove_users",
                    "propelauth::can_setup_saml",
                    "propelauth::can_manage_api_keys",
                    "propelauth::can_edit_org_access",
                    "propelauth::can_update_org_metadata",
                    "propelauth::can_view_other_members",
                    "propelauth::can_delete_org",
                ],
            }
        },
        "user": {
            "user_id": "e50870d2-9dcd-44fe-a273-1b9cc1e982de",
            "email": "testuser@aipolabs.xyz",
            "email_confirmed": True,
            "has_password": False,
            "first_name": "Test",
            "last_name": "User",
            "picture_url": "",
            "properties": {},
            "metadata": None,
            "locked": False,
            "enabled": True,
            "mfa_enabled": False,
            "can_create_orgs": False,
            "created_at": 1746268241,
            "last_active_at": 1746272886,
            "update_password_required": False,
        },
    }
