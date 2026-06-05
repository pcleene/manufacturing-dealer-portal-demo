"""
Pydantic models for Warranty Claim entities.
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


class StatusHistoryEntry(BaseModel):
    """Claim status history entry."""
    status: str
    changed_at: datetime = Field(..., alias="changedAt")
    changed_by: str = Field(..., alias="changedBy")
    notes: Optional[str] = None

    model_config = ConfigDict(populate_by_name=True)


class DealerInfo(BaseModel):
    """Dealer information embedded in claim."""
    dealer_id: str = Field(..., alias="dealerId")
    dealer_code: str = Field(..., alias="dealerCode")
    name: str
    region: str

    model_config = ConfigDict(populate_by_name=True)


class VehicleInfo(BaseModel):
    """Vehicle information for warranty claim."""
    model_code: str = Field(..., alias="modelCode")
    model_name: str = Field(..., alias="modelName")
    registration_number: str = Field(..., alias="registrationNumber")
    engine_number: str = Field(..., alias="engineNumber")
    frame_number: str = Field(..., alias="frameNumber")
    purchase_date: datetime = Field(..., alias="purchaseDate")
    mileage_at_claim: int = Field(..., alias="mileageAtClaim")
    warranty_start_date: datetime = Field(..., alias="warrantyStartDate")
    warranty_end_date: datetime = Field(..., alias="warrantyEndDate")

    model_config = ConfigDict(populate_by_name=True)


class CustomerInfo(BaseModel):
    """Customer information for warranty claim."""
    name: str
    phone: str
    email: str
    address: str  # Simplified to single string as per frontend

    model_config = ConfigDict(populate_by_name=True)


class FailureDetails(BaseModel):
    """Failure details for warranty claim."""
    category: str  # Engine, Electrical, Fuel System, Transmission, Suspension, Body
    description: str
    date_reported: datetime = Field(..., alias="dateReported")
    technician_notes: Optional[str] = Field(None, alias="technicianNotes")

    model_config = ConfigDict(populate_by_name=True)


class PartClaimed(BaseModel):
    """Part claimed in warranty claim."""
    part_number: str = Field(..., alias="partNumber")
    part_name: str = Field(..., alias="partName")
    quantity: int
    unit_price: float = Field(..., alias="unitPrice")
    total_price: float = Field(..., alias="totalPrice")
    warranty_approved: bool = Field(False, alias="warrantyApproved")

    model_config = ConfigDict(populate_by_name=True)


class LabourClaimed(BaseModel):
    """Labour claimed in warranty claim."""
    operation_code: str = Field(..., alias="operationCode")
    description: str
    hours: float
    rate: float
    total_price: float = Field(..., alias="totalPrice")
    warranty_approved: bool = Field(False, alias="warrantyApproved")

    model_config = ConfigDict(populate_by_name=True)


class ClaimTotals(BaseModel):
    """Claim total amounts."""
    parts_total: float = Field(..., alias="partsTotal")
    labour_total: float = Field(..., alias="labourTotal")
    claim_total: float = Field(..., alias="claimTotal")
    approved_parts: float = Field(0, alias="approvedParts")
    approved_labour: float = Field(0, alias="approvedLabour")
    approved_total: float = Field(0, alias="approvedTotal")

    model_config = ConfigDict(populate_by_name=True)


class SupportingDocument(BaseModel):
    """Supporting document for warranty claim."""
    document_id: str = Field(..., alias="documentId")
    document_type: str = Field(..., alias="documentType")
    file_name: str = Field(..., alias="fileName")
    uploaded_at: datetime = Field(..., alias="uploadedAt")
    uploaded_by: str = Field(..., alias="uploadedBy")

    model_config = ConfigDict(populate_by_name=True)


class ReviewInfo(BaseModel):
    """Review information for warranty claim."""
    reviewed_by: Optional[str] = Field(None, alias="reviewedBy")
    reviewed_at: Optional[datetime] = Field(None, alias="reviewedAt")
    decision: Optional[str] = None  # Approved, Rejected
    rejection_reason: Optional[str] = Field(None, alias="rejectionReason")
    comments: Optional[str] = None

    model_config = ConfigDict(populate_by_name=True)


class PaymentInfo(BaseModel):
    """Payment information for warranty claim."""
    payment_date: Optional[datetime] = Field(None, alias="paymentDate")
    payment_amount: Optional[float] = Field(None, alias="paymentAmount")
    payment_reference: Optional[str] = Field(None, alias="paymentReference")
    payment_method: Optional[str] = Field(None, alias="paymentMethod")

    model_config = ConfigDict(populate_by_name=True)


class SLAInfo(BaseModel):
    """SLA tracking information."""
    target_days: int = Field(..., alias="targetDays")
    submitted_at: datetime = Field(..., alias="submittedAt")
    due_date: datetime = Field(..., alias="dueDate")
    sla_breached: bool = Field(False, alias="slaBreached")
    days_elapsed: int = Field(0, alias="daysElapsed")

    model_config = ConfigDict(populate_by_name=True)


class WarrantyClaim(BaseModel):
    """Complete warranty claim document model."""
    id: Optional[PyObjectId] = Field(None, alias="_id")
    claim_id: str = Field(..., alias="claimId")

    # Status tracking
    status: str  # Draft, Submitted, Under Review, Approved, Rejected, Paid
    status_history: List[StatusHistoryEntry] = Field(
        default_factory=list, alias="statusHistory"
    )

    # Dealer info (denormalized)
    dealer: DealerInfo

    # Vehicle info
    vehicle: VehicleInfo

    # Customer info
    customer: CustomerInfo

    # Failure details
    failure: FailureDetails

    # Parts claimed
    parts_claimed: List[PartClaimed] = Field(
        default_factory=list, alias="partsClaimed"
    )

    # Labour claimed (list as per frontend)
    labour_claimed: List[LabourClaimed] = Field(
        default_factory=list, alias="labourClaimed"
    )

    # Totals
    totals: ClaimTotals

    # Supporting documents
    supporting_documents: List[SupportingDocument] = Field(
        default_factory=list, alias="supportingDocuments"
    )

    # Review info (optional)
    review: Optional[ReviewInfo] = None

    # Payment info (optional)
    payment: Optional[PaymentInfo] = None

    # SLA tracking
    sla: SLAInfo

    # Timestamps
    submitted_at: datetime = Field(..., alias="submittedAt")
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: datetime = Field(..., alias="updatedAt")

    # Search optimization (internal use)
    search_text: Optional[str] = Field(None, alias="searchText")
    embedding: Optional[List[float]] = None

    # For search results
    search_score: Optional[float] = Field(None, alias="searchScore")
    vector_score: Optional[float] = Field(None, alias="vectorScore")
    pagination_token: Optional[str] = Field(None, alias="paginationToken")

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )


class WarrantyClaimResponse(BaseModel):
    """API response for a single warranty claim."""
    claim: WarrantyClaim
    message: Optional[str] = None


class WarrantyClaimSearchResponse(BaseModel):
    """API response for warranty claim search results."""
    results: List[WarrantyClaim]
    total_count: Optional[int] = Field(None, alias="totalCount")
    pagination: dict
    facets: Optional[List[dict]] = None

    model_config = ConfigDict(populate_by_name=True)


class ClaimSummary(BaseModel):
    """Lightweight claim summary for lists."""
    claim_id: str = Field(..., alias="claimId")
    status: str
    vehicle_model: str = Field(..., alias="vehicleModel")
    registration_number: str = Field(..., alias="registrationNumber")
    customer_name: str = Field(..., alias="customerName")
    failure_category: str = Field(..., alias="failureCategory")
    claim_type: str = Field(..., alias="claimType")  # Parts, Labour, Parts + Labour
    claim_total: float = Field(..., alias="claimTotal")
    submitted_at: Optional[datetime] = Field(None, alias="submittedAt")

    model_config = ConfigDict(populate_by_name=True)


class CreateClaimRequest(BaseModel):
    """Request model for creating a new warranty claim."""
    vehicle: VehicleInfo
    customer: CustomerInfo
    failure: FailureDetails
    parts_claimed: List[PartClaimed] = Field(default_factory=list, alias="partsClaimed")
    labour_claimed: Optional[LabourClaimed] = Field(None, alias="labourClaimed")

    model_config = ConfigDict(populate_by_name=True)


class UpdateClaimRequest(BaseModel):
    """Request model for updating a warranty claim."""
    failure: Optional[FailureDetails] = None
    parts_claimed: Optional[List[PartClaimed]] = Field(None, alias="partsClaimed")
    labour_claimed: Optional[LabourClaimed] = Field(None, alias="labourClaimed")
    documents: Optional[List[SupportingDocument]] = None

    model_config = ConfigDict(populate_by_name=True)
