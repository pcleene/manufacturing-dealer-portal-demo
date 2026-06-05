"""
Vector search utilities using Voyage AI embeddings.

Manufacturing Group Manufacturing OEMPartner Dealer Portal.
This module provides semantic search capabilities using 1024-dimensional
embeddings from Voyage AI's voyage-2 model.
"""
from typing import List, Dict, Any, Optional
import logging

import voyageai

from app.config import settings
from app.search.pagination import format_pipeline_as_python

logger = logging.getLogger(__name__)

# Initialize Voyage AI client
voyage_client = None
if settings.voyage_api_key:
    voyage_client = voyageai.Client(api_key=settings.voyage_api_key)
else:
    logger.warning("VOYAGE_API_KEY not set. Vector search will not be available.")


def generate_embedding(text: str) -> List[float]:
    """
    Generate 1024-dimensional embedding using Voyage AI voyage-2.

    Args:
        text: Text to embed

    Returns:
        List of 1024 floats representing the embedding vector

    Raises:
        RuntimeError: If Voyage AI client is not initialized
        Exception: If embedding generation fails
    """
    if not voyage_client:
        raise RuntimeError(
            "Voyage AI client not initialized. Please set VOYAGE_API_KEY environment variable."
        )

    try:
        result = voyage_client.embed(
            texts=[text],
            model=settings.voyage_model
        )

        embedding = result.embeddings[0]

        # Verify dimensions
        if len(embedding) != settings.voyage_dimensions:
            logger.warning(
                f"Expected {settings.voyage_dimensions} dimensions, got {len(embedding)}"
            )

        return embedding

    except Exception as e:
        logger.error(f"Error generating embedding: {e}")
        raise


def generate_product_embedding_text(product_doc: Dict[str, Any]) -> str:
    """
    Create comprehensive text representation for product semantic embedding.

    Uses ALL relevant fields from the document for maximum semantic coverage:
    - Basic info: name, partNumber, sku, brand, category, subcategory
    - Description and search text
    - Compatible models with full details (code, name, years, notes)
    - Pricing (msrp, dealerPrice)
    - Inventory (status, quantity, warehouses)
    - All specifications
    - Supersession chain
    - Related products

    Args:
        product_doc: Product document

    Returns:
        Text representation optimized for semantic search
    """
    text_parts = []

    # Core identification
    text_parts.append(f"Product: {product_doc.get('name', 'Unknown')}")
    text_parts.append(f"Part Number: {product_doc.get('partNumber', 'Unknown')}")
    text_parts.append(f"SKU: {product_doc.get('sku', 'Unknown')}")
    text_parts.append(f"Brand: {product_doc.get('brand', 'OEMPartner')}")

    # Category hierarchy
    text_parts.append(f"Category: {product_doc.get('category', 'Unknown')}")
    text_parts.append(f"Subcategory: {product_doc.get('subcategory', 'Unknown')}")

    product_type = product_doc.get('productType', '')
    if product_type:
        text_parts.append(f"Product Type: {product_type}")

    # Full description
    description = product_doc.get('description', '')
    if description:
        text_parts.append(f"Description: {description}")

    # Compatible models - include ALL details
    compatible_models = product_doc.get('compatibleModels', [])
    if compatible_models:
        model_details = []
        for model in compatible_models:
            model_str = f"{model.get('modelCode', '')} {model.get('modelName', '')}"
            year_start = model.get('yearStart', '')
            year_end = model.get('yearEnd', '')
            if year_start or year_end:
                model_str += f" ({year_start}-{year_end})"
            notes = model.get('notes', '')
            if notes:
                model_str += f" [{notes}]"
            model_details.append(model_str)
        text_parts.append(f"Compatible Models: {'; '.join(model_details)}")

    # Pricing - all price points
    pricing = product_doc.get('pricing', {})
    msrp = pricing.get('msrp', 0)
    dealer_price = pricing.get('dealerPrice', 0)
    if msrp > 0:
        text_parts.append(f"MSRP: RM {msrp:.2f}")
    if dealer_price > 0:
        text_parts.append(f"Dealer Price: RM {dealer_price:.2f}")

    # Inventory - comprehensive status
    inventory = product_doc.get('inventory', {})
    status = inventory.get('status', 'Unknown')
    total_qty = inventory.get('totalQuantity', 0)
    reorder_point = inventory.get('reorderPoint', 0)
    text_parts.append(f"Availability: {status}")
    text_parts.append(f"Total Stock: {total_qty} units")
    text_parts.append(f"Reorder Point: {reorder_point}")

    # Warehouse details
    warehouses = inventory.get('warehouses', [])
    if warehouses:
        wh_details = []
        for wh in warehouses:
            wh_details.append(f"{wh.get('name', wh.get('code', 'Unknown'))}: {wh.get('quantity', 0)} units")
        text_parts.append(f"Warehouse Stock: {'; '.join(wh_details)}")

    # ALL specifications
    specs = product_doc.get('specifications', {})
    if specs:
        spec_parts = [f"{k}: {v}" for k, v in specs.items() if v]
        if spec_parts:
            text_parts.append(f"Specifications: {'; '.join(spec_parts)}")

    # Supersession chain
    supersession = product_doc.get('supersession', {})
    if supersession:
        supersedes = supersession.get('supersedes', '')
        superseded_by = supersession.get('supersededBy', '')
        if supersedes:
            text_parts.append(f"Supersedes Part: {supersedes}")
        if superseded_by:
            text_parts.append(f"Superseded By: {superseded_by}")

    # Related products
    related = product_doc.get('relatedProducts', [])
    if related:
        text_parts.append(f"Related Parts: {', '.join(related)}")

    # Search text (may contain additional keywords)
    search_text = product_doc.get('searchText', '')
    if search_text:
        text_parts.append(f"Keywords: {search_text}")

    # Product status
    product_status = product_doc.get('status', '')
    if product_status:
        text_parts.append(f"Product Status: {product_status}")

    return ". ".join(text_parts)


def generate_claim_embedding_text(claim_doc: Dict[str, Any]) -> str:
    """
    Create comprehensive text representation for warranty claim semantic embedding.

    Uses ALL relevant fields from the document for maximum semantic coverage:
    - Claim identification: claimId, status
    - Vehicle: model, registration, engine/frame numbers, mileage, warranty dates
    - Dealer: name, code, region, contact info
    - Customer: name, contact, address (full)
    - Failure: category, subcategory, description, symptoms, diagnostic codes, technician notes
    - Parts claimed: all parts with numbers, names, quantities, costs
    - Labour claimed: all operations with codes, descriptions, times, costs
    - Totals: all amounts (parts, labour, claim, approved)
    - Review: reviewer info, comments, adjustments
    - Payment: reference, amount, date
    - SLA: target date, breached status
    - Status history: all transitions

    Args:
        claim_doc: Warranty claim document

    Returns:
        Text representation optimized for semantic search
    """
    text_parts = []

    # Claim identification
    text_parts.append(f"Claim ID: {claim_doc.get('claimId', 'Unknown')}")
    text_parts.append(f"Status: {claim_doc.get('status', 'Unknown')}")

    # Vehicle - comprehensive details
    vehicle = claim_doc.get('vehicle', {})
    text_parts.append(f"Vehicle Model: {vehicle.get('modelName', 'Unknown')} ({vehicle.get('modelCode', '')})")
    text_parts.append(f"Model Year: {vehicle.get('modelYear', 'Unknown')}")
    text_parts.append(f"Registration Number: {vehicle.get('registrationNumber', 'Unknown')}")

    engine_number = vehicle.get('engineNumber', '')
    if engine_number:
        text_parts.append(f"Engine Number: {engine_number}")

    frame_number = vehicle.get('frameNumber', '')
    if frame_number:
        text_parts.append(f"Frame Number: {frame_number}")

    text_parts.append(f"Current Mileage: {vehicle.get('currentMileage', 0)} km")

    # Warranty dates
    warranty_start = vehicle.get('warrantyStartDate', '')
    warranty_end = vehicle.get('warrantyEndDate', '')
    if warranty_start:
        text_parts.append(f"Warranty Start: {warranty_start}")
    if warranty_end:
        text_parts.append(f"Warranty End: {warranty_end}")

    purchase_date = vehicle.get('purchaseDate', '')
    if purchase_date:
        text_parts.append(f"Purchase Date: {purchase_date}")

    # Dealer - all info
    dealer = claim_doc.get('dealer', {})
    text_parts.append(f"Dealer: {dealer.get('dealerName', 'Unknown')}")
    text_parts.append(f"Dealer Code: {dealer.get('dealerCode', 'Unknown')}")
    text_parts.append(f"Dealer Region: {dealer.get('region', 'Unknown')}")

    technician = dealer.get('serviceTechnician', '')
    if technician:
        text_parts.append(f"Service Technician: {technician}")

    service_advisor = dealer.get('serviceAdvisor', '')
    if service_advisor:
        text_parts.append(f"Service Advisor: {service_advisor}")

    # Customer - comprehensive
    customer = claim_doc.get('customer', {})
    text_parts.append(f"Customer: {customer.get('name', 'Unknown')}")

    customer_phone = customer.get('phone', '')
    if customer_phone:
        text_parts.append(f"Customer Phone: {customer_phone}")

    customer_email = customer.get('email', '')
    if customer_email:
        text_parts.append(f"Customer Email: {customer_email}")

    address = customer.get('address', {})
    if address:
        addr_parts = []
        if address.get('line1'):
            addr_parts.append(address['line1'])
        if address.get('line2'):
            addr_parts.append(address['line2'])
        if address.get('city'):
            addr_parts.append(address['city'])
        if address.get('state'):
            addr_parts.append(address['state'])
        if address.get('postcode'):
            addr_parts.append(address['postcode'])
        if addr_parts:
            text_parts.append(f"Customer Address: {', '.join(addr_parts)}")

    # Failure - comprehensive
    failure = claim_doc.get('failure', {})
    text_parts.append(f"Failure Category: {failure.get('category', 'Unknown')}")
    text_parts.append(f"Failure Subcategory: {failure.get('subcategory', 'Unknown')}")

    description = failure.get('description', '')
    if description:
        text_parts.append(f"Failure Description: {description}")

    symptoms = failure.get('reportedSymptoms', [])
    if symptoms:
        text_parts.append(f"Reported Symptoms: {', '.join(symptoms)}")

    diagnostic_codes = failure.get('diagnosticCodes', [])
    if diagnostic_codes:
        text_parts.append(f"Diagnostic Codes: {', '.join(diagnostic_codes)}")

    technician_notes = failure.get('technicianNotes', '')
    if technician_notes:
        text_parts.append(f"Technician Notes: {technician_notes}")

    # Parts claimed - ALL parts with full details
    parts = claim_doc.get('partsClaimed', [])
    if parts:
        part_details = []
        for part in parts:
            part_str = f"{part.get('partNumber', 'Unknown')} {part.get('partName', '')}"
            qty = part.get('quantity', 1)
            unit_cost = part.get('unitCost', 0)
            total = part.get('totalCost', 0)
            part_str += f" (Qty: {qty}, Unit: RM{unit_cost:.2f}, Total: RM{total:.2f})"
            part_details.append(part_str)
        text_parts.append(f"Parts Claimed: {'; '.join(part_details)}")

    # Labour claimed - ALL operations
    labour = claim_doc.get('labourClaimed', [])
    if labour:
        labour_details = []
        for op in labour:
            op_str = f"{op.get('operationCode', '')} {op.get('description', '')}"
            hours = op.get('hours', 0)
            rate = op.get('hourlyRate', 0)
            total = op.get('totalCost', 0)
            op_str += f" ({hours}h @ RM{rate:.2f}/h = RM{total:.2f})"
            labour_details.append(op_str)
        text_parts.append(f"Labour Operations: {'; '.join(labour_details)}")

    # Totals - all amounts
    totals = claim_doc.get('totals', {})
    parts_total = totals.get('partsTotal', 0)
    labour_total = totals.get('labourTotal', 0)
    claim_total = totals.get('claimTotal', 0)
    approved_total = totals.get('approvedTotal', 0)
    text_parts.append(f"Parts Total: RM {parts_total:.2f}")
    text_parts.append(f"Labour Total: RM {labour_total:.2f}")
    text_parts.append(f"Claim Total: RM {claim_total:.2f}")
    if approved_total > 0:
        text_parts.append(f"Approved Total: RM {approved_total:.2f}")

    # Review information
    review = claim_doc.get('review', {})
    if review:
        reviewer = review.get('reviewedBy', '')
        if reviewer:
            text_parts.append(f"Reviewed By: {reviewer}")

        review_comments = review.get('comments', '')
        if review_comments:
            text_parts.append(f"Review Comments: {review_comments}")

        adjustments = review.get('adjustments', [])
        if adjustments:
            adj_details = []
            for adj in adjustments:
                adj_details.append(f"{adj.get('field', '')}: {adj.get('reason', '')}")
            text_parts.append(f"Adjustments: {'; '.join(adj_details)}")

    # Payment information
    payment = claim_doc.get('payment', {})
    if payment:
        payment_ref = payment.get('paymentReference', '')
        if payment_ref:
            text_parts.append(f"Payment Reference: {payment_ref}")

        payment_amount = payment.get('amount', 0)
        if payment_amount > 0:
            text_parts.append(f"Payment Amount: RM {payment_amount:.2f}")

        payment_date = payment.get('paidAt', '')
        if payment_date:
            text_parts.append(f"Paid At: {payment_date}")

    # SLA information
    sla = claim_doc.get('sla', {})
    if sla:
        target_date = sla.get('targetCompletionDate', '')
        if target_date:
            text_parts.append(f"SLA Target: {target_date}")

        breached = sla.get('slaBreached', False)
        text_parts.append(f"SLA Breached: {'Yes' if breached else 'No'}")

    # Status history - all transitions
    status_history = claim_doc.get('statusHistory', [])
    if status_history:
        history_details = []
        for entry in status_history:
            status = entry.get('status', '')
            changed_by = entry.get('changedBy', '')
            timestamp = entry.get('timestamp', '')
            history_details.append(f"{status} by {changed_by} at {timestamp}")
        text_parts.append(f"Status History: {'; '.join(history_details)}")

    # Timestamps
    submitted_at = claim_doc.get('submittedAt', '')
    if submitted_at:
        text_parts.append(f"Submitted At: {submitted_at}")

    return ". ".join(text_parts)


async def vector_search_products(
    collection,
    query: str,
    filters: Optional[Dict[str, Any]] = None,
    limit: int = 20,
    num_candidates: int = 100,
    include_query: bool = False
) -> Dict[str, Any]:
    """
    Perform semantic vector search on products collection.

    Args:
        collection: Products MongoDB collection
        query: Natural language query (e.g., "motorcycle good for city commuting with good fuel economy")
        filters: Optional metadata filters to apply post-search
        limit: Number of results to return
        num_candidates: Number of candidates for vector search (should be > limit)
        include_query: Include the MongoDB pipeline in response (for debugging/demos)

    Returns:
        Dict with results and pagination info
    """
    # Generate query embedding
    try:
        query_embedding = generate_embedding(query)
    except Exception as e:
        logger.error(f"Failed to generate query embedding: {e}")
        raise

    # Build vector search pipeline
    # Note: 'embedding' field is populated by generate_embeddings.py script
    pipeline = [
        {
            "$vectorSearch": {
                "index": settings.products_vector_index,
                "path": "embedding",
                "queryVector": query_embedding,
                "numCandidates": num_candidates,
                "limit": limit
            }
        },
        {
            "$addFields": {
                "vectorScore": {"$meta": "vectorSearchScore"}
            }
        }
    ]

    # Add optional filters (post-vector search)
    if filters:
        match_filters = {}

        # Convert filter format to MongoDB query format
        if filters.get("category"):
            match_filters["category"] = {"$in": filters["category"]}
        if filters.get("subcategory"):
            match_filters["subcategory"] = {"$in": filters["subcategory"]}
        if filters.get("availability_status"):
            match_filters["inventory.status"] = {"$in": filters["availability_status"]}
        if filters.get("model_series"):
            match_filters["compatibleModels.modelCode"] = {"$in": filters["model_series"]}
        if filters.get("min_price") is not None or filters.get("max_price") is not None:
            price_filter = {}
            if filters.get("min_price") is not None:
                price_filter["$gte"] = filters["min_price"]
            if filters.get("max_price") is not None:
                price_filter["$lte"] = filters["max_price"]
            match_filters["pricing.msrp"] = price_filter

        if match_filters:
            pipeline.append({"$match": match_filters})

    # Project fields
    pipeline.append({
        "$project": {
            "_id": 1,
            "partNumber": 1,
            "sku": 1,
            "name": 1,
            "description": 1,
            "category": 1,
            "subcategory": 1,
            "productType": 1,
            "compatibleModels": 1,
            "pricing": 1,
            "inventory": 1,
            "specifications": 1,
            "images": 1,
            "status": 1,
            "createdAt": 1,
            "updatedAt": 1,
            "vectorScore": 1
        }
    })

    # Execute pipeline
    cursor = await collection.aggregate(pipeline)
    results = await cursor.to_list(length=limit)

    response = {
        "results": results,
        "pagination": {
            "limit": limit,
            "hasMore": len(results) >= limit,
            "totalCount": len(results),
            "currentPageSize": len(results)
        },
        "query": query
    }
    
    # Include debug query if requested
    if include_query:
        # Create a display version with placeholder for the embedding vector
        display_pipeline = []
        for stage in pipeline:
            if "$vectorSearch" in stage:
                # Replace the actual embedding with a placeholder for readability
                display_stage = {
                    "$vectorSearch": {
                        **stage["$vectorSearch"],
                        "queryVector": f"<{len(query_embedding)}-dimensional embedding from Voyage AI for: '{query}'>"
                    }
                }
                display_pipeline.append(display_stage)
            else:
                display_pipeline.append(stage)
        
        collection_name = collection.name if hasattr(collection, 'name') else 'products'
        response["debugQuery"] = format_pipeline_as_python(display_pipeline, collection_name)
    
    return response


async def vector_search_claims(
    collection,
    query: str,
    filters: Optional[Dict[str, Any]] = None,
    limit: int = 20,
    num_candidates: int = 100,
    include_query: bool = False
) -> Dict[str, Any]:
    """
    Perform semantic vector search on warranty claims collection.

    Args:
        collection: Warranty claims MongoDB collection
        query: Natural language query (e.g., "Y15ZR engine claims last 3 months")
        filters: Optional metadata filters to apply post-search
        limit: Number of results to return
        num_candidates: Number of candidates for vector search (should be > limit)
        include_query: Include the MongoDB pipeline in response (for debugging/demos)

    Returns:
        Dict with results and pagination info
    """
    # Generate query embedding
    try:
        query_embedding = generate_embedding(query)
    except Exception as e:
        logger.error(f"Failed to generate query embedding: {e}")
        raise

    # Build vector search pipeline
    # Note: 'embedding' field is populated by generate_embeddings.py script
    pipeline = [
        {
            "$vectorSearch": {
                "index": settings.claims_vector_index,
                "path": "embedding",
                "queryVector": query_embedding,
                "numCandidates": num_candidates,
                "limit": limit
            }
        },
        {
            "$addFields": {
                "vectorScore": {"$meta": "vectorSearchScore"}
            }
        }
    ]

    # Add optional filters (post-vector search)
    if filters:
        match_filters = {}

        # Convert filter format to MongoDB query format
        if filters.get("status"):
            match_filters["status"] = {"$in": filters["status"]}
        if filters.get("vehicle_model"):
            match_filters["vehicle.modelCode"] = {"$in": filters["vehicle_model"]}
        if filters.get("failure_category"):
            match_filters["failure.category"] = {"$in": filters["failure_category"]}
        if filters.get("dealer_id"):
            match_filters["dealer.dealerId"] = filters["dealer_id"]
        if filters.get("min_amount") is not None or filters.get("max_amount") is not None:
            amount_filter = {}
            if filters.get("min_amount") is not None:
                amount_filter["$gte"] = filters["min_amount"]
            if filters.get("max_amount") is not None:
                amount_filter["$lte"] = filters["max_amount"]
            match_filters["totals.claimTotal"] = amount_filter

        if match_filters:
            pipeline.append({"$match": match_filters})

    # Project fields
    pipeline.append({
        "$project": {
            "_id": 1,
            "claimId": 1,
            "status": 1,
            "statusHistory": 1,
            "dealer": 1,
            "vehicle": 1,
            "customer": 1,
            "failure": 1,
            "partsClaimed": 1,
            "labourClaimed": 1,
            "totals": 1,
            "documents": 1,
            "review": 1,
            "createdAt": 1,
            "submittedAt": 1,
            "updatedAt": 1,
            "sla": 1,
            "vectorScore": 1
        }
    })

    # Execute pipeline
    cursor = await collection.aggregate(pipeline)
    results = await cursor.to_list(length=limit)

    response = {
        "results": results,
        "pagination": {
            "limit": limit,
            "hasMore": len(results) >= limit,
            "totalCount": len(results),
            "currentPageSize": len(results)
        },
        "query": query
    }
    
    # Include debug query if requested
    if include_query:
        # Create a display version with placeholder for the embedding vector
        display_pipeline = []
        for stage in pipeline:
            if "$vectorSearch" in stage:
                # Replace the actual embedding with a placeholder for readability
                display_stage = {
                    "$vectorSearch": {
                        **stage["$vectorSearch"],
                        "queryVector": f"<{len(query_embedding)}-dimensional embedding from Voyage AI for: '{query}'>"
                    }
                }
                display_pipeline.append(display_stage)
            else:
                display_pipeline.append(stage)
        
        collection_name = collection.name if hasattr(collection, 'name') else 'warrantyClaims'
        response["debugQuery"] = format_pipeline_as_python(display_pipeline, collection_name)
    
    return response
