from fastapi import APIRouter, HTTPException, Query
from sqlalchemy.orm import Session
from api.dependents import db_dependency
from plaid.model.institutions_get_by_id_request import InstitutionsGetByIdRequest
from plaid.model.country_code import CountryCode
from ...plaid_client import client
from api.models import PlaidInstitution
from .utils import run_blocking

router = APIRouter(prefix="/institution")

@router.get("/info")
async def get_institution_info(
    institution_id: str,
    db: db_dependency):
    try:
        # Check if the institution_id is in the database
        institution = db.query(PlaidInstitution).filter(PlaidInstitution.institution_id == institution_id).first()
        if institution:
            return {
                "institution_id": institution.institution_id,
                "name": institution.name,
                "url": institution.url,
                "primary_color": institution.primary_color,
                "logo": institution.logo,
                "oauth": institution.oauth,
                "products": institution.products,
                "country_codes": institution.country_codes,
                "status": institution.status,
            }
            
        # If not found, fetch it from Plaid
        request = InstitutionsGetByIdRequest(
            institution_id=institution_id,
            country_codes=[CountryCode("US")], #Country Code is an enum 
        )
        response = await run_blocking(client.institutions_get_by_id, request)

        inst = response.institution
        # Save to DB
        institution = PlaidInstitution(
            institution_id=inst.institution_id,
            name=inst.name,
            url=getattr(inst, "url", None),
            primary_color=getattr(inst, "primary_color", None),
            logo=getattr(inst, "logo", None),
            oauth=getattr(inst, "oauth", False),
            products=[p.value for p in getattr(inst, "products", [])],  # Convert enums to strings
            country_codes=[c.value for c in getattr(inst, "country_codes", [])],  # Convert enums to strings
            status=getattr(inst, "status", None)
        )

        db.add(institution)
        db.commit()
        db.refresh(institution)

        return inst.to_dict()

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get institution info: {e}")
