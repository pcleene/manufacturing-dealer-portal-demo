"""
Pydantic models for Product (motorcycle, parts, accessories) entities.
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


class CompatibleModel(BaseModel):
    """Model compatibility information."""
    model_code: str = Field(..., alias="modelCode")
    model_name: str = Field(..., alias="modelName")
    year_start: int = Field(..., alias="yearStart")
    year_end: Optional[int] = Field(None, alias="yearEnd")
    variant: List[str] = Field(default_factory=list)
    notes: Optional[str] = None

    model_config = ConfigDict(populate_by_name=True)


class Pricing(BaseModel):
    """Product pricing information."""
    dealer_price: float = Field(..., alias="dealerPrice")
    msrp: float
    currency: str = "MYR"
    margin_percent: Optional[float] = Field(None, alias="marginPercent")
    last_price_update: Optional[datetime] = Field(None, alias="lastPriceUpdate")
    promo_price: Optional[float] = Field(None, alias="promoPrice")
    promo_valid_until: Optional[datetime] = Field(None, alias="promoValidUntil")

    model_config = ConfigDict(populate_by_name=True)


class Warehouse(BaseModel):
    """Warehouse stock information."""
    code: str
    name: str
    quantity: int
    last_restocked: Optional[datetime] = Field(None, alias="lastRestocked")

    model_config = ConfigDict(populate_by_name=True)


class Inventory(BaseModel):
    """Product inventory information."""
    total_quantity: int = Field(..., alias="totalQuantity")
    reorder_point: int = Field(..., alias="reorderPoint")
    reorder_qty: int = Field(..., alias="reorderQty")
    status: str  # In Stock, Low Stock, Out of Stock, Discontinued
    warehouses: List[Warehouse] = Field(default_factory=list)
    last_stock_update: Optional[datetime] = Field(None, alias="lastStockUpdate")

    model_config = ConfigDict(populate_by_name=True)


class Supersession(BaseModel):
    """Part supersession tracking."""
    supersedes: Optional[str] = None  # Part number this supersedes
    superseded_by: Optional[str] = Field(None, alias="supersededBy")  # Part number that supersedes this
    supersession_date: Optional[datetime] = Field(None, alias="supersessionDate")

    model_config = ConfigDict(populate_by_name=True)


class RelatedProduct(BaseModel):
    """Related product reference."""
    part_number: str = Field(..., alias="partNumber")
    relationship: str  # Description of relationship
    type: str  # companion, consumable, upsell

    model_config = ConfigDict(populate_by_name=True)


class ProductImage(BaseModel):
    """Product image reference."""
    url: str
    is_primary: bool = Field(..., alias="isPrimary")
    alt_text: str = Field(..., alias="altText")

    model_config = ConfigDict(populate_by_name=True)


class Product(BaseModel):
    """Complete product document model."""
    id: Optional[PyObjectId] = Field(None, alias="_id")
    part_number: str = Field(..., alias="partNumber")
    sku: str

    # Basic Info
    name: str
    description: str
    category: str  # Motorcycle, Scooter, Parts, Accessories, Apparel, Lubricants
    subcategory: str
    product_type: str = Field(..., alias="productType")  # Replacement Part, OEM, Accessory

    # Model Compatibility
    compatible_models: List[CompatibleModel] = Field(
        default_factory=list, alias="compatibleModels"
    )

    # Pricing
    pricing: Pricing

    # Inventory
    inventory: Inventory

    # Specifications (flexible schema)
    specifications: dict = Field(default_factory=dict)

    # Supersession tracking
    supersession: Optional[Supersession] = None

    # Related products
    related_products: List[RelatedProduct] = Field(
        default_factory=list, alias="relatedProducts"
    )

    # Media
    images: List[ProductImage] = Field(default_factory=list)

    # Search optimization
    search_text: str = Field(..., alias="searchText")
    semantic_embedding: Optional[List[float]] = Field(None, alias="semanticEmbedding")

    # Metadata
    status: str = "active"  # active, inactive, discontinued
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: datetime = Field(..., alias="updatedAt")
    updated_by: str = Field(..., alias="updatedBy")

    # For search results
    search_score: Optional[float] = Field(None, alias="searchScore")
    vector_score: Optional[float] = Field(None, alias="vectorScore")
    pagination_token: Optional[str] = Field(None, alias="paginationToken")

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )


class ProductResponse(BaseModel):
    """API response for a single product."""
    product: Product
    message: Optional[str] = None


class ProductSearchResponse(BaseModel):
    """API response for product search results."""
    results: List[Product]
    total_count: Optional[int] = Field(None, alias="totalCount")
    pagination: dict
    facets: Optional[List[dict]] = None

    model_config = ConfigDict(populate_by_name=True)


class ProductSummary(BaseModel):
    """Lightweight product summary for lists."""
    part_number: str = Field(..., alias="partNumber")
    sku: str
    name: str
    category: str
    subcategory: str
    dealer_price: float = Field(..., alias="dealerPrice")
    msrp: float
    stock_status: str = Field(..., alias="stockStatus")
    total_quantity: int = Field(..., alias="totalQuantity")
    compatible_models_summary: str = Field(..., alias="compatibleModelsSummary")
    updated_at: datetime = Field(..., alias="updatedAt")

    model_config = ConfigDict(populate_by_name=True)


class AutocompleteResult(BaseModel):
    """Autocomplete search result."""
    text: str
    part_number: Optional[str] = Field(None, alias="partNumber")
    category: Optional[str] = None
    type: str  # product_name, part_number, model
