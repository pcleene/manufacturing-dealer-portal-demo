"""
Embedding generation script for OEMPartner Dealer Portal.

This script generates Voyage AI embeddings (1024 dimensions) for all
products and warranty claims documents. The embeddings enable semantic/vector search.

Manufacturing Group Malaysia - OEMPartner Dealer Portal

Usage:
    python generate_embeddings.py --collection products
    python generate_embeddings.py --collection claims
    python generate_embeddings.py --all
    python generate_embeddings.py --collection products --batch-size 50 --skip 0

Requirements:
    - MongoDB Atlas connection configured
    - VOYAGE_API_KEY environment variable set
    - Voyage AI Python SDK: pip install voyageai
"""

import asyncio
import argparse
import logging
import sys
from datetime import datetime
from typing import List, Dict, Any, Optional

from pymongo import AsyncMongoClient
import voyageai

from app.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Voyage AI client
voyage_client = None


def init_voyage():
    """Initialize Voyage AI client."""
    global voyage_client
    if not settings.voyage_api_key:
        raise ValueError(
            "VOYAGE_API_KEY not set. Please set the environment variable or add to .env file."
        )
    voyage_client = voyageai.Client(api_key=settings.voyage_api_key)
    logger.info(f"Voyage AI client initialized with model: {settings.voyage_model}")


def generate_embedding(text: str) -> List[float]:
    """
    Generate 1024-dimensional embedding using Voyage AI voyage-2.

    Args:
        text: Text to embed (max ~8000 tokens)

    Returns:
        List of 1024 floats representing the embedding vector
    """
    if not voyage_client:
        raise RuntimeError("Voyage AI client not initialized")

    # Truncate text if too long (Voyage has token limits)
    if len(text) > 30000:  # Approximate character limit
        text = text[:30000]
        logger.warning("Text truncated to 30000 characters for embedding")

    result = voyage_client.embed(
        texts=[text],
        model=settings.voyage_model
    )

    embedding = result.embeddings[0]

    if len(embedding) != settings.voyage_dimensions:
        logger.warning(
            f"Expected {settings.voyage_dimensions} dimensions, got {len(embedding)}"
        )

    return embedding


# ============================================================================
# PRODUCT EMBEDDING TEXT GENERATION
# ============================================================================

def generate_product_embedding_text(doc: Dict[str, Any]) -> str:
    """
    Create comprehensive text representation for product semantic embedding.

    Uses ALL relevant fields from the product document to create a rich
    semantic representation for vector search.

    Args:
        doc: Product document from MongoDB

    Returns:
        Text representation optimized for semantic search
    """
    sections = []

    # Basic product info
    sections.append(f"Product Name: {doc.get('name', 'Unknown')}")
    sections.append(f"Part Number: {doc.get('partNumber', 'Unknown')}")
    sections.append(f"SKU: {doc.get('sku', 'Unknown')}")
    sections.append(f"Brand: {doc.get('brand', 'OEMPartner')}")

    # Category information
    sections.append(f"Category: {doc.get('category', 'Unknown')}")
    sections.append(f"Subcategory: {doc.get('subcategory', 'Unknown')}")

    # Description
    description = doc.get('description', '')
    if description:
        sections.append(f"Description: {description}")

    # Compatible models - comprehensive list
    compatible_models = doc.get('compatibleModels', [])
    if compatible_models:
        model_details = []
        for model in compatible_models:
            model_code = model.get('modelCode', '')
            model_name = model.get('modelName', '')
            year_start = model.get('yearStart', '')
            year_end = model.get('yearEnd', '')
            notes = model.get('notes', '')

            model_str = f"{model_name} ({model_code})"
            if year_start and year_end:
                model_str += f" {year_start}-{year_end}"
            if notes:
                model_str += f" - {notes}"
            model_details.append(model_str)

        sections.append(f"Compatible Motorcycle Models: {'; '.join(model_details)}")

        # Also add just the model codes for exact matching
        model_codes = [m.get('modelCode', '') for m in compatible_models if m.get('modelCode')]
        sections.append(f"Model Codes: {', '.join(model_codes)}")

    # Pricing information
    pricing = doc.get('pricing', {})
    if pricing:
        msrp = pricing.get('msrp', 0)
        dealer_price = pricing.get('dealerPrice', 0)
        currency = pricing.get('currency', 'MYR')
        if msrp > 0:
            sections.append(f"Retail Price: {currency} {msrp:.2f}")
        if dealer_price > 0:
            sections.append(f"Dealer Price: {currency} {dealer_price:.2f}")

    # Inventory information
    inventory = doc.get('inventory', {})
    if inventory:
        status = inventory.get('status', 'Unknown')
        total_qty = inventory.get('totalQuantity', 0)
        reorder_point = inventory.get('reorderPoint', 0)

        sections.append(f"Availability Status: {status}")
        sections.append(f"Stock Quantity: {total_qty} units")

        if total_qty <= reorder_point:
            sections.append("Stock Alert: Low stock, needs reorder")

        # Warehouse locations
        warehouses = inventory.get('warehouses', [])
        if warehouses:
            wh_names = [f"{wh.get('name', '')} ({wh.get('quantity', 0)} units)" for wh in warehouses]
            sections.append(f"Available at Warehouses: {'; '.join(wh_names)}")

    # Specifications
    specifications = doc.get('specifications', {})
    if specifications:
        spec_items = []
        for key, value in specifications.items():
            if value:
                # Convert camelCase to readable format
                readable_key = ''.join([' ' + c if c.isupper() else c for c in key]).strip().title()
                spec_items.append(f"{readable_key}: {value}")
        if spec_items:
            sections.append(f"Specifications: {'; '.join(spec_items)}")

    # Supersession information
    supersession = doc.get('supersession', {})
    if supersession:
        superseded_by = supersession.get('supersededBy')
        supersedes = supersession.get('supersedes')
        if superseded_by:
            sections.append(f"Superseded by newer part: {superseded_by}")
        if supersedes:
            sections.append(f"Replaces older part: {supersedes}")

    # Related products
    related = doc.get('relatedProducts', [])
    if related:
        sections.append(f"Related Parts: {', '.join(related[:10])}")

    # Manufacturing information (NEW)
    manufacturing = doc.get('manufacturing', {})
    if manufacturing:
        country = manufacturing.get('countryOfOrigin', '')
        manufacturer = manufacturing.get('manufacturerName', '')
        certifications = manufacturing.get('qualityCertifications', [])
        lead_time = manufacturing.get('leadTimeDays', 0)
        
        if country:
            sections.append(f"Made in: {country}")
        if manufacturer:
            sections.append(f"Manufacturer: {manufacturer}")
        if certifications:
            sections.append(f"Quality Certifications: {', '.join(certifications)}")
        if lead_time:
            sections.append(f"Lead Time: {lead_time} days")

    # Fitment notes (NEW)
    fitment = doc.get('fitmentNotes', {})
    if fitment:
        difficulty = fitment.get('difficultyLevel', '')
        install_time = fitment.get('estimatedInstallTime', '')
        tools = fitment.get('toolsRequired', [])
        instructions = fitment.get('specialInstructions', '')
        
        if difficulty:
            sections.append(f"Installation Difficulty: {difficulty}")
        if install_time:
            sections.append(f"Estimated Install Time: {install_time}")
        if tools:
            sections.append(f"Tools Required: {', '.join(tools[:5])}")
        if instructions:
            sections.append(f"Special Instructions: {instructions}")

    # Technical documentation (NEW)
    tech_docs = doc.get('technicalDocs', [])
    if tech_docs:
        doc_types = [d.get('docType', '') for d in tech_docs if d.get('docType')]
        doc_titles = [d.get('title', '') for d in tech_docs if d.get('title')]
        if doc_types:
            sections.append(f"Available Documentation: {', '.join(set(doc_types))}")
        if doc_titles:
            sections.append(f"Documents: {'; '.join(doc_titles[:3])}")

    # Sales data (NEW) - brief summary
    sales_data = doc.get('salesData', {})
    if sales_data:
        units_sold = sales_data.get('totalUnitsSold', 0)
        rating = sales_data.get('avgRating')
        top_regions = sales_data.get('topSellingRegions', [])
        
        if units_sold > 0:
            sections.append(f"Units Sold: {units_sold}")
        if rating:
            sections.append(f"Customer Rating: {rating}/5")
        if top_regions:
            sections.append(f"Popular in: {', '.join(top_regions[:3])}")

    # Packaging info (NEW)
    packaging = doc.get('packaging', {})
    if packaging:
        hazmat = packaging.get('hazmatClass')
        if hazmat:
            sections.append(f"Hazmat Classification: {hazmat}")

    # Search text field (if exists, may contain additional keywords)
    search_text = doc.get('searchText', '')
    if search_text:
        sections.append(f"Keywords: {search_text}")

    # Join all sections
    full_text = ". ".join(sections)

    return full_text


# ============================================================================
# WARRANTY CLAIM EMBEDDING TEXT GENERATION
# ============================================================================

def generate_claim_embedding_text(doc: Dict[str, Any]) -> str:
    """
    Create comprehensive text representation for warranty claim semantic embedding.

    Uses ALL relevant fields from the claim document to create a rich
    semantic representation for vector search.

    Args:
        doc: Warranty claim document from MongoDB

    Returns:
        Text representation optimized for semantic search
    """
    sections = []

    # Basic claim info
    sections.append(f"Claim ID: {doc.get('claimId', 'Unknown')}")
    sections.append(f"Claim Status: {doc.get('status', 'Unknown')}")

    # Vehicle information - comprehensive
    vehicle = doc.get('vehicle', {})
    if vehicle:
        sections.append(f"Vehicle Model: {vehicle.get('modelName', 'Unknown')}")
        sections.append(f"Model Code: {vehicle.get('modelCode', 'Unknown')}")
        sections.append(f"Registration Number: {vehicle.get('registrationNumber', 'Unknown')}")
        sections.append(f"Engine Number: {vehicle.get('engineNumber', 'Unknown')}")
        sections.append(f"Frame Number: {vehicle.get('frameNumber', 'Unknown')}")

        mileage = vehicle.get('mileageAtClaim', 0)
        if mileage:
            sections.append(f"Mileage at Claim: {mileage} km")

        purchase_date = vehicle.get('purchaseDate')
        if purchase_date:
            if isinstance(purchase_date, datetime):
                sections.append(f"Vehicle Purchase Date: {purchase_date.strftime('%d/%m/%Y')}")
            else:
                sections.append(f"Vehicle Purchase Date: {purchase_date}")

        warranty_start = vehicle.get('warrantyStartDate')
        warranty_end = vehicle.get('warrantyEndDate')
        if warranty_start and warranty_end:
            sections.append(f"Warranty Period: {warranty_start} to {warranty_end}")

    # Dealer information
    dealer = doc.get('dealer', {})
    if dealer:
        sections.append(f"Dealer Name: {dealer.get('name', 'Unknown')}")
        sections.append(f"Dealer Code: {dealer.get('dealerCode', 'Unknown')}")
        sections.append(f"Dealer Region: {dealer.get('region', 'Unknown')}")

    # Customer information
    customer = doc.get('customer', {})
    if customer:
        sections.append(f"Customer Name: {customer.get('name', 'Unknown')}")
        sections.append(f"Customer Phone: {customer.get('phone', 'Unknown')}")

        address = customer.get('address', '')
        if address:
            sections.append(f"Customer Location: {address}")

    # Failure details - comprehensive
    failure = doc.get('failure', {})
    if failure:
        sections.append(f"Failure Category: {failure.get('category', 'Unknown')}")

        description = failure.get('description', '')
        if description:
            sections.append(f"Failure Description: {description}")

        date_reported = failure.get('dateReported')
        if date_reported:
            sections.append(f"Date Reported: {date_reported}")

        technician_notes = failure.get('technicianNotes', '')
        if technician_notes:
            sections.append(f"Technician Notes: {technician_notes}")

    # Parts claimed - comprehensive
    parts_claimed = doc.get('partsClaimed', [])
    if parts_claimed:
        parts_details = []
        for part in parts_claimed:
            part_number = part.get('partNumber', '')
            part_name = part.get('partName', '')
            qty = part.get('quantity', 1)
            total_price = part.get('totalPrice', 0)
            approved = "Approved" if part.get('warrantyApproved') else "Pending"

            parts_details.append(
                f"{part_name} ({part_number}) x{qty} - RM {total_price:.2f} [{approved}]"
            )
        sections.append(f"Parts Claimed: {'; '.join(parts_details)}")

        # Also list just part numbers for exact matching
        part_numbers = [p.get('partNumber', '') for p in parts_claimed if p.get('partNumber')]
        sections.append(f"Part Numbers: {', '.join(part_numbers)}")

    # Labour claimed - comprehensive
    labour_claimed = doc.get('labourClaimed', [])
    if labour_claimed:
        labour_details = []
        for labour in labour_claimed:
            op_code = labour.get('operationCode', '')
            description = labour.get('description', '')
            hours = labour.get('hours', 0)
            total_price = labour.get('totalPrice', 0)
            approved = "Approved" if labour.get('warrantyApproved') else "Pending"

            labour_details.append(
                f"{description} ({op_code}) {hours}hrs - RM {total_price:.2f} [{approved}]"
            )
        sections.append(f"Labour Claimed: {'; '.join(labour_details)}")

    # Totals
    totals = doc.get('totals', {})
    if totals:
        claim_total = totals.get('claimTotal', 0)
        approved_total = totals.get('approvedTotal', 0)
        sections.append(f"Total Claim Amount: RM {claim_total:.2f}")
        if approved_total > 0:
            sections.append(f"Approved Amount: RM {approved_total:.2f}")

    # Review information
    review = doc.get('review', {})
    if review:
        decision = review.get('decision', '')
        if decision:
            sections.append(f"Review Decision: {decision}")

        rejection_reason = review.get('rejectionReason', '')
        if rejection_reason:
            sections.append(f"Rejection Reason: {rejection_reason}")

        comments = review.get('comments', '')
        if comments:
            sections.append(f"Review Comments: {comments}")

    # Payment information
    payment = doc.get('payment', {})
    if payment:
        payment_amount = payment.get('paymentAmount', 0)
        payment_ref = payment.get('paymentReference', '')
        payment_method = payment.get('paymentMethod', '')
        if payment_amount > 0:
            sections.append(f"Payment: RM {payment_amount:.2f} via {payment_method} (Ref: {payment_ref})")

    # SLA information
    sla = doc.get('sla', {})
    if sla:
        target_days = sla.get('targetDays', 10)
        days_elapsed = sla.get('daysElapsed', 0)
        sla_breached = sla.get('slaBreached', False)

        sections.append(f"SLA Target: {target_days} days")
        sections.append(f"Days Elapsed: {days_elapsed} days")
        if sla_breached:
            sections.append("SLA Status: BREACHED - Overdue")

    # Status history - brief summary
    status_history = doc.get('statusHistory', [])
    if status_history:
        statuses = [h.get('status', '') for h in status_history]
        sections.append(f"Status History: {' -> '.join(statuses)}")

    # Submission date
    submitted_at = doc.get('submittedAt')
    if submitted_at:
        if isinstance(submitted_at, datetime):
            sections.append(f"Submitted: {submitted_at.strftime('%d/%m/%Y')}")
        else:
            sections.append(f"Submitted: {submitted_at}")

    # Search text field (if exists)
    search_text = doc.get('searchText', '')
    if search_text:
        sections.append(f"Keywords: {search_text}")

    # Join all sections
    full_text = ". ".join(sections)

    return full_text


# ============================================================================
# BATCH EMBEDDING GENERATION
# ============================================================================

async def generate_embeddings_for_collection(
    db,
    collection_name: str,
    embedding_text_generator,
    embedding_field: str = "embedding",
    batch_size: int = 50,
    skip: int = 0,
    limit: Optional[int] = None,
    force: bool = False
):
    """
    Generate embeddings for all documents in a collection.

    Args:
        db: MongoDB database instance
        collection_name: Name of the collection
        embedding_text_generator: Function to generate embedding text from document
        embedding_field: Field name to store embedding
        batch_size: Number of documents to process per batch
        skip: Number of documents to skip (for resuming)
        limit: Maximum number of documents to process (None for all)
        force: If True, regenerate embeddings even if they exist
    """
    collection = db[collection_name]

    # Build query - skip documents that already have embeddings (unless force)
    query = {}
    if not force:
        query[embedding_field] = {"$exists": False}

    # Count total documents to process
    total_count = await collection.count_documents(query)
    logger.info(f"Found {total_count} documents to process in '{collection_name}'")

    if total_count == 0:
        logger.info("No documents need embedding generation")
        return

    # Apply limit if specified
    if limit:
        total_count = min(total_count, limit)

    processed = 0
    errors = 0
    cursor = collection.find(query).skip(skip)

    if limit:
        cursor = cursor.limit(limit)

    batch = []
    batch_docs = []

    async for doc in cursor:
        try:
            # Generate embedding text
            embedding_text = embedding_text_generator(doc)

            # Generate embedding
            embedding = generate_embedding(embedding_text)

            batch.append({
                "filter": {"_id": doc["_id"]},
                "update": {
                    "$set": {
                        embedding_field: embedding,
                        "embeddingGeneratedAt": datetime.utcnow()
                    }
                }
            })
            batch_docs.append(doc.get("_id"))

            # Process batch when full
            if len(batch) >= batch_size:
                # Bulk update
                for op in batch:
                    await collection.update_one(op["filter"], op["update"])

                processed += len(batch)
                logger.info(
                    f"Progress: {processed}/{total_count} ({processed * 100 / total_count:.1f}%) - "
                    f"Last batch IDs: {batch_docs[:3]}..."
                )

                batch = []
                batch_docs = []

        except Exception as e:
            errors += 1
            logger.error(f"Error processing document {doc.get('_id')}: {e}")
            continue

    # Process remaining batch
    if batch:
        for op in batch:
            await collection.update_one(op["filter"], op["update"])

        processed += len(batch)
        logger.info(f"Final batch processed. Total: {processed}/{total_count}")

    logger.info(f"Embedding generation complete for '{collection_name}'")
    logger.info(f"  Processed: {processed}")
    logger.info(f"  Errors: {errors}")


async def generate_product_embeddings(
    db,
    batch_size: int = 50,
    skip: int = 0,
    limit: Optional[int] = None,
    force: bool = False
):
    """Generate embeddings for all products."""
    logger.info("Starting product embedding generation...")
    await generate_embeddings_for_collection(
        db=db,
        collection_name="products",
        embedding_text_generator=generate_product_embedding_text,
        embedding_field="embedding",
        batch_size=batch_size,
        skip=skip,
        limit=limit,
        force=force
    )


async def generate_claim_embeddings(
    db,
    batch_size: int = 50,
    skip: int = 0,
    limit: Optional[int] = None,
    force: bool = False
):
    """Generate embeddings for all warranty claims."""
    logger.info("Starting warranty claim embedding generation...")
    await generate_embeddings_for_collection(
        db=db,
        collection_name="warrantyClaims",
        embedding_text_generator=generate_claim_embedding_text,
        embedding_field="embedding",
        batch_size=batch_size,
        skip=skip,
        limit=limit,
        force=force
    )


# ============================================================================
# MAIN FUNCTION
# ============================================================================

async def main(args):
    """Main entry point."""
    logger.info("=" * 60)
    logger.info("OEMPartner Dealer Portal - Embedding Generation Script")
    logger.info("Using Voyage AI voyage-2 model (1024 dimensions)")
    logger.info("=" * 60)

    # Initialize Voyage AI client
    try:
        init_voyage()
    except ValueError as e:
        logger.error(str(e))
        sys.exit(1)

    # Connect to MongoDB
    logger.info(f"Connecting to MongoDB: {settings.mongodb_db_name}")
    client = AsyncMongoClient(settings.mongodb_url)
    db = client[settings.mongodb_db_name]

    try:
        # Test connection
        await db.command('ping')
        logger.info("MongoDB connection successful")

        if args.all or args.collection == 'products':
            await generate_product_embeddings(
                db=db,
                batch_size=args.batch_size,
                skip=args.skip,
                limit=args.limit,
                force=args.force
            )

        if args.all or args.collection == 'claims':
            await generate_claim_embeddings(
                db=db,
                batch_size=args.batch_size,
                skip=args.skip,
                limit=args.limit,
                force=args.force
            )

        logger.info("=" * 60)
        logger.info("Embedding generation completed successfully!")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"Error during embedding generation: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    finally:
        await client.close()


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Generate Voyage AI embeddings for OEMPartner Dealer Portal",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate embeddings for all products
  python generate_embeddings.py --collection products

  # Generate embeddings for all warranty claims
  python generate_embeddings.py --collection claims

  # Generate embeddings for both collections
  python generate_embeddings.py --all

  # Resume from a specific point (skip first 100)
  python generate_embeddings.py --collection products --skip 100

  # Process only 50 documents
  python generate_embeddings.py --collection products --limit 50

  # Force regenerate all embeddings
  python generate_embeddings.py --all --force

  # Use smaller batch size (for rate limiting)
  python generate_embeddings.py --all --batch-size 20

Environment Variables Required:
  VOYAGE_API_KEY - Your Voyage AI API key for embeddings
  MONGODB_URL - MongoDB connection string (optional, defaults to localhost)
        """
    )

    parser.add_argument(
        "--collection",
        choices=["products", "claims"],
        help="Collection to generate embeddings for"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Generate embeddings for all collections"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=50,
        help="Number of documents to process per batch (default: 50)"
    )
    parser.add_argument(
        "--skip",
        type=int,
        default=0,
        help="Number of documents to skip (for resuming)"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum number of documents to process"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Regenerate embeddings even if they already exist"
    )

    args = parser.parse_args()

    if not args.all and not args.collection:
        parser.error("Either --collection or --all must be specified")

    return args


if __name__ == "__main__":
    args = parse_args()
    asyncio.run(main(args))
