"""
Pydantic models for Dealer (dealership) entities.
Matches the MongoDB schema for Manufacturing Group Manufacturing OEMPartner Dealer Portal.
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from bson import ObjectId


class PyObjectId(str):
    """Custom type for MongoDB ObjectId."""

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v, _info):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return str(v)


class DealerAddress(BaseModel):
    """Dealer address information."""
    line1: str
    line2: Optional[str] = None
    city: str
    state: str
    postcode: str


class DealerContact(BaseModel):
    """Dealer contact information."""
    address: DealerAddress
    phone: str
    email: str
    website: Optional[str] = None


class DealerPersonnel(BaseModel):
    """Key personnel at dealer."""
    name: str
    role: str  # Dealer Principal, Parts Manager, Service Manager
    phone: str
    email: str
    is_primary: bool = Field(..., alias="isPrimary")

    model_config = ConfigDict(populate_by_name=True)


class DealerMetrics(BaseModel):
    """Performance metrics for dealer."""
    ytd_sales_units: int = Field(..., alias="ytdSalesUnits")
    ytd_sales_value: float = Field(..., alias="ytdSalesValue")
    ytd_parts_sales: float = Field(..., alias="ytdPartsSales")
    ytd_warranty_claims: int = Field(..., alias="ytdWarrantyClaims")
    warranty_approval_rate: float = Field(..., alias="warrantyApprovalRate")
    avg_claim_processing_days: float = Field(..., alias="avgClaimProcessingDays")
    customer_satisfaction_score: float = Field(..., alias="customerSatisfactionScore")
    last_updated: datetime = Field(..., alias="lastUpdated")

    model_config = ConfigDict(populate_by_name=True)


class PortalUser(BaseModel):
    """Portal user reference."""
    username: str
    name: str
    role: str  # Admin, Parts, Service
    last_login: Optional[datetime] = Field(None, alias="lastLogin")

    model_config = ConfigDict(populate_by_name=True)


class Dealer(BaseModel):
    """Complete dealer document model."""
    id: Optional[PyObjectId] = Field(None, alias="_id")
    dealer_id: str = Field(..., alias="dealerId")

    # Basic info
    name: str
    legal_name: str = Field(..., alias="legalName")
    registration_number: str = Field(..., alias="registrationNumber")

    # Classification
    tier: str  # 3S (Sales, Service, Spare Parts), 2S, 1S, Authorized Reseller
    region: str  # Malaysian state
    territory: List[str] = Field(default_factory=list)  # Covered areas

    # Contact
    contact: DealerContact

    # Personnel
    personnel: List[DealerPersonnel] = Field(default_factory=list)

    # Performance metrics
    metrics: DealerMetrics

    # Account status
    status: str = "active"  # active, inactive, suspended
    onboarded_date: datetime = Field(..., alias="onboardedDate")
    contract_renewal_date: datetime = Field(..., alias="contractRenewalDate")

    # Portal users
    portal_users: List[PortalUser] = Field(default_factory=list, alias="portalUsers")

    # Metadata
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: datetime = Field(..., alias="updatedAt")

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )


class DealerResponse(BaseModel):
    """API response for a single dealer."""
    dealer: Dealer
    message: Optional[str] = None


class DealerSummary(BaseModel):
    """Lightweight dealer summary."""
    dealer_id: str = Field(..., alias="dealerId")
    name: str
    tier: str
    region: str
    status: str
    warranty_approval_rate: float = Field(..., alias="warrantyApprovalRate")
    ytd_claims: int = Field(..., alias="ytdClaims")

    model_config = ConfigDict(populate_by_name=True)
