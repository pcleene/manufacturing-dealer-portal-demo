"""
Sample data generation script for OEMPartner Dealer Portal.

This script generates realistic Malaysian OEMPartner dealer data for testing purposes.
Manufacturing Group Malaysia - Dealer Portal

Usage:
    python generate_sample_data.py --products 100 --claims 200 --dealers 10
    python generate_sample_data.py --clear  # Clear all data

Requirements:
    - MongoDB Atlas connection configured
    - Faker library: pip install faker
"""

import asyncio
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple
import argparse
import sys

from faker import Faker
from pymongo import AsyncMongoClient

from app.config import settings

# Initialize Faker (en_US as fallback, Malaysian names generated manually)
fake = Faker('en_US')
Faker.seed(42)  # For reproducible data

# ============================================================================
# MALAYSIAN-SPECIFIC DATA
# ============================================================================

MALAYSIAN_STATES = [
    "Johor", "Kedah", "Kelantan", "Malacca", "Negeri Sembilan",
    "Pahang", "Penang", "Perak", "Perlis", "Sabah", "Sarawak",
    "Selangor", "Terengganu", "Kuala Lumpur", "Labuan", "Putrajaya"
]

STATE_WEIGHTS = {
    "Selangor": 0.20, "Kuala Lumpur": 0.15, "Johor": 0.12,
    "Penang": 0.08, "Perak": 0.08, "Sabah": 0.07, "Sarawak": 0.07,
    "Kedah": 0.05, "Kelantan": 0.05, "Pahang": 0.04,
    "Negeri Sembilan": 0.03, "Terengganu": 0.03, "Malacca": 0.02,
    "Perlis": 0.01, "Labuan": 0.005, "Putrajaya": 0.005
}

MALAYSIAN_CITIES = {
    "Kuala Lumpur": ["Kuala Lumpur"],
    "Selangor": ["Petaling Jaya", "Shah Alam", "Subang Jaya", "Puchong", "Klang"],
    "Johor": ["Johor Bahru", "Skudai", "Batu Pahat", "Muar"],
    "Penang": ["George Town", "Butterworth", "Bukit Mertajam"],
    "Perak": ["Ipoh", "Taiping"],
    "Sabah": ["Kota Kinabalu", "Sandakan"],
    "Sarawak": ["Kuching", "Miri", "Sibu"],
    "Kedah": ["Alor Setar", "Sungai Petani"],
    "Kelantan": ["Kota Bharu"],
    "Pahang": ["Kuantan", "Temerloh"],
    "Negeri Sembilan": ["Seremban"],
    "Terengganu": ["Kuala Terengganu"],
    "Malacca": ["Malacca City"],
    "Perlis": ["Kangar"],
    "Labuan": ["Victoria"],
    "Putrajaya": ["Putrajaya"]
}

# ============================================================================
# OEMPartner PRODUCT DATA
# ============================================================================

OEMPartner_MODELS = [
    {"code": "Y15ZR", "name": "Y15ZR", "category": "Moped", "cc": 150, "years": [2019, 2024]},
    {"code": "Y16ZR", "name": "Y16ZR", "category": "Moped", "cc": 155, "years": [2021, 2024]},
    {"code": "LC135", "name": "LC135", "category": "Moped", "cc": 135, "years": [2016, 2024]},
    {"code": "NVX155", "name": "NVX 155", "category": "Scooter", "cc": 155, "years": [2017, 2024]},
    {"code": "NMAX155", "name": "NMAX 155", "category": "Scooter", "cc": 155, "years": [2020, 2024]},
    {"code": "XMAX250", "name": "XMAX 250", "category": "Scooter", "cc": 250, "years": [2018, 2024]},
    {"code": "MT15", "name": "MT-15", "category": "Naked", "cc": 155, "years": [2019, 2024]},
    {"code": "MT25", "name": "MT-25", "category": "Naked", "cc": 250, "years": [2019, 2024]},
    {"code": "R15", "name": "YZF-R15", "category": "Sport", "cc": 155, "years": [2017, 2024]},
    {"code": "R25", "name": "YZF-R25", "category": "Sport", "cc": 250, "years": [2019, 2024]},
]

PRODUCT_CATEGORIES = {
    "Engine Parts": [
        "Piston Kit", "Cylinder Block", "Crankshaft", "Connecting Rod",
        "Gasket Set", "Oil Filter", "Air Filter", "Spark Plug", "Camshaft",
        "Valve", "Timing Chain", "Oil Pump", "Engine Mount", "Carburetor"
    ],
    "Electrical": [
        "CDI Unit", "Ignition Coil", "Stator Coil", "Rectifier", "Battery",
        "Headlight Bulb", "Tail Light Assembly", "Turn Signal", "Horn",
        "Starter Motor", "Relay", "Fuse", "Wiring Harness", "Switch Assembly"
    ],
    "Body Parts": [
        "Front Fender", "Rear Fender", "Side Cover", "Fuel Tank",
        "Seat Assembly", "Windscreen", "Fairing", "Tail Cowl",
        "Headlight Cover", "Mirror", "Footrest", "Handle Grip", "Lever"
    ],
    "Brake System": [
        "Brake Pad Front", "Brake Pad Rear", "Brake Disc Front", "Brake Disc Rear",
        "Brake Shoe", "Master Cylinder", "Brake Caliper", "Brake Hose",
        "Brake Lever", "Brake Fluid", "ABS Sensor", "Brake Light Switch"
    ],
    "Suspension": [
        "Front Fork", "Rear Shock Absorber", "Fork Oil", "Fork Seal",
        "Swing Arm", "Linkage Kit", "Steering Bearing", "Handlebar"
    ],
    "Transmission": [
        "Clutch Plate", "Clutch Spring", "Gear Set", "Chain Kit",
        "Sprocket Front", "Sprocket Rear", "Belt Drive", "Gear Shift Lever"
    ],
    "Cooling System": [
        "Radiator", "Coolant Hose", "Thermostat", "Water Pump",
        "Radiator Cap", "Coolant", "Fan Motor", "Temperature Sensor"
    ],
    "Accessories": [
        "Helmet", "Riding Gloves", "Rain Coat", "Tank Bag", "Side Box",
        "Phone Holder", "USB Charger", "Alarm System", "Cover Motorcycle"
    ],
    "Lubricants": [
        "Yamalube 4T", "Yamalube 2T", "Gear Oil", "Fork Oil",
        "Chain Lube", "Brake Cleaner", "Polish", "Coolant"
    ]
}

FAILURE_CATEGORIES = [
    "Engine Failure", "Electrical Fault", "Brake System Failure",
    "Transmission Issue", "Suspension Damage", "Cooling System Failure",
    "Body/Frame Damage", "Fuel System Issue", "Exhaust System",
    "Manufacturing Defect", "Premature Wear"
]

CLAIM_STATUSES = [
    "Draft", "Pending Review", "Under Review", "Awaiting Parts",
    "Approved", "Rejected", "Paid", "Closed"
]

CLAIM_STATUS_WEIGHTS = [0.05, 0.15, 0.15, 0.05, 0.25, 0.10, 0.15, 0.10]

WAREHOUSES = [
    {"code": "WH-KL", "name": "Kuala Lumpur Central", "region": "Central"},
    {"code": "WH-PJ", "name": "Petaling Jaya Hub", "region": "Central"},
    {"code": "WH-JB", "name": "Johor Bahru", "region": "South"},
    {"code": "WH-PNG", "name": "Penang Distribution", "region": "North"},
    {"code": "WH-IPH", "name": "Ipoh Warehouse", "region": "North"},
    {"code": "WH-KCH", "name": "Kuching Depot", "region": "East Malaysia"},
    {"code": "WH-KK", "name": "Kota Kinabalu", "region": "East Malaysia"},
]

LABOUR_OPERATIONS = [
    {"code": "LBR-001", "desc": "Engine Overhaul", "hours": 8.0, "rate": 80.0},
    {"code": "LBR-002", "desc": "Clutch Replacement", "hours": 2.5, "rate": 80.0},
    {"code": "LBR-003", "desc": "Brake Service", "hours": 1.5, "rate": 80.0},
    {"code": "LBR-004", "desc": "Fork Seal Replacement", "hours": 2.0, "rate": 80.0},
    {"code": "LBR-005", "desc": "Electrical Diagnosis", "hours": 1.0, "rate": 100.0},
    {"code": "LBR-006", "desc": "Chain & Sprocket Replace", "hours": 1.5, "rate": 80.0},
    {"code": "LBR-007", "desc": "Carburetor Tuning", "hours": 1.0, "rate": 80.0},
    {"code": "LBR-008", "desc": "Full Service", "hours": 2.0, "rate": 80.0},
    {"code": "LBR-009", "desc": "Tire Change", "hours": 0.5, "rate": 60.0},
    {"code": "LBR-010", "desc": "Body Panel Replace", "hours": 1.0, "rate": 60.0},
]

REJECTION_REASONS = [
    "Outside warranty period", "Customer misuse evident",
    "Non-genuine parts installed", "Maintenance neglect",
    "Accident damage - not covered", "Documentation incomplete",
    "Mileage exceeds warranty limit", "Previous unauthorized modification"
]

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def weighted_choice(choices: List[str], weights: List[float]) -> str:
    """Select item based on weights."""
    return random.choices(choices, weights=weights, k=1)[0]


def get_weighted_state() -> str:
    """Get random state based on population weights."""
    states = list(STATE_WEIGHTS.keys())
    weights = list(STATE_WEIGHTS.values())
    return random.choices(states, weights=weights, k=1)[0]


def generate_phone_number() -> str:
    """Generate Malaysian phone number."""
    mobile_prefixes = ["010", "011", "012", "013", "014", "016", "017", "018", "019"]
    return f"+60{random.choice(mobile_prefixes)}-{random.randint(1000000, 9999999)}"


def generate_postcode(state: str) -> str:
    """Generate realistic postcode for state."""
    postcode_ranges = {
        "Kuala Lumpur": (50000, 60000), "Selangor": (40000, 48999),
        "Johor": (79000, 86000), "Penang": (10000, 14400),
        "Perak": (30000, 36800), "Sabah": (87000, 91309),
        "Sarawak": (93000, 98859), "Kedah": (5000, 9810),
        "Kelantan": (15000, 19800), "Pahang": (25000, 28800),
        "Negeri Sembilan": (70000, 73509), "Terengganu": (20000, 24300),
        "Malacca": (75000, 78309), "Perlis": (1000, 2800),
        "Labuan": (87000, 87033), "Putrajaya": (62000, 62988)
    }
    min_code, max_code = postcode_ranges.get(state, (50000, 60000))
    return str(random.randint(min_code, max_code))


def generate_malaysian_name() -> str:
    """Generate realistic Malaysian name."""
    ethnicity = random.choices(["Malay", "Chinese", "Indian"], weights=[0.60, 0.25, 0.15], k=1)[0]

    if ethnicity == "Malay":
        first_names = ["Ahmad", "Ali", "Hassan", "Ibrahim", "Aziz", "Siti", "Fatimah", "Nur", "Aisyah", "Mohamed"]
        last_names = ["Abdullah", "Rahman", "Ali", "Ismail", "Omar", "Ahmad", "Hassan", "Ibrahim", "bin Yusof"]
        return f"{random.choice(first_names)} {random.choice(last_names)}"
    elif ethnicity == "Chinese":
        surnames = ["Tan", "Lee", "Lim", "Wong", "Ng", "Ong", "Chan", "Chong", "Teo", "Liew"]
        first_names = ["Wei", "Ming", "Hui", "Li", "Jia", "Xin", "Ying", "Chen", "Jun", "Kai"]
        return f"{random.choice(surnames)} {random.choice(first_names)}"
    else:
        first_names = ["Kumar", "Raj", "Ravi", "Siva", "Muthu", "Devi", "Lakshmi", "Priya", "Suresh", "Arjun"]
        last_names = ["Kumar", "Raj", "Murugan", "Devi", "Krishnan", "Samy", "Maniam"]
        return f"{random.choice(first_names)} {random.choice(last_names)}"


# ============================================================================
# DEALER DOCUMENT GENERATION
# ============================================================================

def generate_dealer_document(dealer_num: int) -> Dict[str, Any]:
    """Generate a realistic dealer document."""
    state = get_weighted_state()
    city = random.choice(MALAYSIAN_CITIES[state])

    dealer_id = f"DLR-{state[:3].upper()}-{dealer_num:03d}"
    dealer_code = f"YD{random.randint(1000, 9999)}"

    company_types = ["Sdn Bhd", "Enterprise", "(M) Sdn Bhd"]
    dealer_names = [
        f"{city} OEMPartner {random.choice(company_types)}",
        f"OEMPartner {city} Motor {random.choice(company_types)}",
        f"{fake.last_name()} Motor {random.choice(company_types)}",
        f"Motoworld {city} {random.choice(company_types)}"
    ]

    dealer = {
        "dealerId": dealer_id,
        "dealerCode": dealer_code,
        "name": random.choice(dealer_names),
        "status": weighted_choice(["Active", "Inactive", "Suspended"], [0.85, 0.10, 0.05]),
        "dealerType": weighted_choice(["Authorized", "Service Center", "Parts Dealer"], [0.60, 0.30, 0.10]),
        "address": {
            "street": fake.street_address(),
            "city": city,
            "state": state,
            "postcode": generate_postcode(state),
            "country": "Malaysia"
        },
        "contact": {
            "phone": generate_phone_number(),
            "email": f"info@OEMPartner{city.lower().replace(' ', '')}.com.my",
            "website": f"www.OEMPartner{city.lower().replace(' ', '')}.com.my" if random.random() > 0.5 else None
        },
        "personnel": {
            "ownerName": generate_malaysian_name(),
            "managerName": generate_malaysian_name(),
            "serviceTechnicians": random.randint(2, 8),
            "salesStaff": random.randint(1, 5)
        },
        "metrics": {
            "totalClaimsSubmitted": random.randint(50, 500),
            "totalClaimsApproved": random.randint(40, 400),
            "totalClaimValue": round(random.uniform(50000, 500000), 2),
            "averageProcessingDays": round(random.uniform(3, 10), 1),
            "approvalRate": round(random.uniform(0.75, 0.95), 2),
            "lastClaimDate": datetime.now() - timedelta(days=random.randint(1, 30))
        },
        "certifications": ["OEMPartner Authorized", "3S Center"] if random.random() > 0.3 else ["OEMPartner Authorized"],
        "portalUsers": [
            {
                "userId": f"user_{dealer_id.lower().replace('-', '_')}_1",
                "username": f"admin_{dealer_code.lower()}",
                "role": "Dealer Admin",
                "lastLogin": datetime.now() - timedelta(days=random.randint(0, 7))
            }
        ],
        "region": state,
        "createdAt": datetime.now() - timedelta(days=random.randint(365, 3650)),
        "updatedAt": datetime.now()
    }

    return dealer


# ============================================================================
# PRODUCT ENRICHMENT DATA
# ============================================================================

TECHNICAL_DOC_TYPES = ["Installation", "Repair", "Maintenance", "Safety", "Technical Bulletin"]
COUNTRIES_OF_ORIGIN = ["Japan", "Indonesia", "Thailand", "Malaysia", "Taiwan"]
MANUFACTURERS = [
    {"code": "OEM-JP", "name": "OEMPartner Motor Co., Ltd.", "plant": "IWA-01"},
    {"code": "OEM-ID", "name": "PT OEMPartner Indonesia Motor Manufacturing", "plant": "JKT-01"},
    {"code": "OEM-TH", "name": "Thai OEMPartner Motor Co., Ltd.", "plant": "BKK-01"},
    {"code": "OEM-MY", "name": "Manufacturing Group OEMPartner Motor Sdn Bhd", "plant": "KL-01"},
]
QUALITY_CERTIFICATIONS = ["ISO 9001:2015", "ISO 14001:2015", "ISO 45001:2018", "IATF 16949"]
DIFFICULTY_LEVELS = ["Easy", "Intermediate", "Advanced", "Professional"]
TOOLS_LIST = [
    "10mm socket", "12mm socket", "14mm socket", "17mm socket",
    "Allen key set (2-10mm)", "Torque wrench", "Phillips screwdriver",
    "Flathead screwdriver", "Pliers", "Wire cutters", "Multimeter",
    "Chain breaker tool", "Bearing puller", "Oil filter wrench"
]
MATERIALS = [
    "Aluminum Alloy 6061-T6", "Stainless Steel 304", "Carbon Steel",
    "ABS Plastic", "Reinforced Nylon", "Natural Rubber", "Silicone Rubber",
    "Copper", "Brass", "Chrome-plated Steel", "Cast Iron", "Titanium Alloy"
]
FINISHES = ["Powder Coated", "Anodized", "Chrome Plated", "Painted", "Raw", "Polished", "Matte Black"]
COLORS = ["Black", "Matte Black", "Silver", "Chrome", "Red", "Blue", "White", "Gray", "Gold"]
REGIONS = ["Central", "Northern", "Southern", "East Coast", "East Malaysia"]


def generate_technical_docs(category: str, compatible_models: List[Dict]) -> List[Dict]:
    """Generate technical documentation metadata for a product."""
    docs = []
    num_docs = random.randint(1, 4)
    
    model_codes = [m["modelCode"] for m in compatible_models]
    
    doc_titles = {
        "Installation": [
            "Installation Guide", "Mounting Instructions", "Fitment Guide",
            "Step-by-Step Installation", "Quick Install Guide"
        ],
        "Repair": [
            "Repair Manual", "Service Guide", "Troubleshooting Guide",
            "Diagnostic Procedures", "Overhaul Instructions"
        ],
        "Maintenance": [
            "Maintenance Schedule", "Periodic Service Guide", "Care Instructions",
            "Lubrication Guide", "Inspection Checklist"
        ],
        "Safety": [
            "Safety Bulletin", "Recall Notice", "Safety Guidelines",
            "Warning Instructions", "Hazard Information"
        ],
        "Technical Bulletin": [
            "Technical Service Bulletin", "Engineering Update",
            "Product Advisory", "Field Service Notice"
        ]
    }
    
    used_types = set()
    for i in range(num_docs):
        doc_type = random.choice([t for t in TECHNICAL_DOC_TYPES if t not in used_types])
        used_types.add(doc_type)
        
        titles = doc_titles.get(doc_type, ["Technical Document"])
        
        docs.append({
            "docId": f"TD-{random.randint(10000, 99999)}",
            "title": random.choice(titles),
            "docType": doc_type,
            "language": "en",
            "version": f"{random.randint(1, 5)}.{random.randint(0, 9)}",
            "pageCount": random.randint(4, 48),
            "lastUpdated": (datetime.now() - timedelta(days=random.randint(30, 365))).strftime("%Y-%m-%d"),
            "fileSize": f"{random.uniform(0.5, 15):.1f} MB",
            "applicableModels": random.sample(model_codes, min(random.randint(1, len(model_codes)), len(model_codes))),
            "summary": fake.sentence(),
            "downloadUrl": f"https://docs.OEMPartner-motor.com.my/technical/{doc_type.lower().replace(' ', '-')}-{random.randint(1000, 9999)}.pdf"
        })
    
    return docs


def generate_manufacturing_info() -> Dict[str, Any]:
    """Generate manufacturing and quality information."""
    manufacturer = random.choice(MANUFACTURERS)
    country = random.choice(COUNTRIES_OF_ORIGIN)
    
    return {
        "countryOfOrigin": country,
        "manufacturerCode": manufacturer["code"],
        "manufacturerName": manufacturer["name"],
        "plantCode": manufacturer["plant"],
        "qualityCertifications": random.sample(QUALITY_CERTIFICATIONS, random.randint(1, 3)),
        "leadTimeDays": random.choice([7, 14, 21, 28, 35]),
        "minOrderQuantity": random.choice([1, 2, 5, 10, 20])
    }


def generate_specifications(category: str) -> Dict[str, Any]:
    """Generate detailed specifications based on category."""
    weight = round(random.uniform(0.05, 25), 2)
    length = random.randint(20, 1000)
    width = random.randint(10, 500)
    height = random.randint(10, 300)
    
    specs = {
        "weight": f"{weight} kg",
        "material": random.choice(MATERIALS),
        "dimensions": {
            "length": f"{length} mm",
            "width": f"{width} mm",
            "height": f"{height} mm"
        },
        "color": random.choice(COLORS),
        "finishType": random.choice(FINISHES),
        "warrantyMonths": random.choice([6, 12, 18, 24, 36])
    }
    
    # Add category-specific specs
    if category in ["Engine Parts", "Cooling System"]:
        specs["operatingTemp"] = f"-20°C to {random.choice([80, 100, 120, 150])}°C"
    
    if category == "Electrical":
        specs["voltage"] = f"{random.choice([6, 12, 14])}V"
        specs["waterproofRating"] = random.choice(["IP54", "IP65", "IP67", None])
    
    if category == "Brake System":
        specs["brakeType"] = random.choice(["Disc", "Drum", "ABS Compatible"])
    
    if category == "Lubricants":
        specs["viscosity"] = random.choice(["10W-40", "20W-50", "15W-40", "SAE 90"])
        specs["volume"] = f"{random.choice([0.5, 1, 2, 4])} L"
    
    return specs


def generate_fitment_notes(category: str) -> Dict[str, Any]:
    """Generate fitment and installation information."""
    difficulty = random.choice(DIFFICULTY_LEVELS)
    
    # Time based on difficulty
    time_ranges = {
        "Easy": (10, 30),
        "Intermediate": (30, 90),
        "Advanced": (60, 180),
        "Professional": (120, 480)
    }
    min_time, max_time = time_ranges[difficulty]
    install_time = random.randint(min_time, max_time)
    
    # Format time
    if install_time < 60:
        time_str = f"{install_time} minutes"
    else:
        hours = install_time // 60
        mins = install_time % 60
        if mins > 0:
            time_str = f"{hours} hour{'s' if hours > 1 else ''} {mins} minutes"
        else:
            time_str = f"{hours} hour{'s' if hours > 1 else ''}"
    
    # Tools based on difficulty
    num_tools = {"Easy": 2, "Intermediate": 4, "Advanced": 6, "Professional": 8}
    tools = random.sample(TOOLS_LIST, min(num_tools[difficulty], len(TOOLS_LIST)))
    
    instructions = [
        "Ensure engine is cool before starting work.",
        "Disconnect battery before electrical work.",
        "Torque all bolts to specification.",
        "Apply thread locker to critical fasteners.",
        "Use genuine OEMPartner parts for best fitment.",
        "Refer to service manual for torque specifications.",
        "Clean mating surfaces before installation.",
        "Check alignment after installation."
    ]
    
    return {
        "difficultyLevel": difficulty,
        "estimatedInstallTime": time_str,
        "toolsRequired": tools,
        "specialInstructions": random.choice(instructions),
        "professionalInstallRecommended": difficulty in ["Advanced", "Professional"]
    }


def generate_cross_sell(part_number: str, category: str) -> Dict[str, Any]:
    """Generate cross-sell and related product references."""
    category_codes = {
        "Engine Parts": "ENG", "Electrical": "ELC", "Body Parts": "BDY",
        "Brake System": "BRK", "Suspension": "SUS", "Transmission": "TRN",
        "Cooling System": "COL", "Accessories": "ACC", "Lubricants": "LUB"
    }
    
    # Generate fake related part numbers
    def gen_part(cat_code=None):
        if cat_code is None:
            cat_code = random.choice(list(category_codes.values()))
        return f"{cat_code}-{random.randint(10000, 99999)}"
    
    return {
        "frequentlyBoughtTogether": [gen_part() for _ in range(random.randint(0, 3))],
        "accessories": [gen_part("ACC") for _ in range(random.randint(0, 2))],
        "alternativeProducts": [gen_part(category_codes.get(category)) for _ in range(random.randint(0, 2))]
    }


def generate_sales_data() -> Dict[str, Any]:
    """Generate sales and performance data."""
    units_sold = random.randint(10, 5000)
    review_count = random.randint(0, min(units_sold // 10, 200))
    
    return {
        "totalUnitsSold": units_sold,
        "avgRating": round(random.uniform(3.5, 5.0), 1) if review_count > 0 else None,
        "reviewCount": review_count,
        "returnRate": round(random.uniform(0.1, 5.0), 1),
        "topSellingRegions": random.sample(REGIONS, random.randint(1, 3))
    }


def generate_packaging_info(weight_kg: float) -> Dict[str, Any]:
    """Generate packaging information."""
    # Package is slightly larger/heavier than product
    pkg_weight = round(weight_kg * random.uniform(1.1, 1.5), 1)
    
    # Dimensions in cm
    length = random.randint(10, 100)
    width = random.randint(8, 60)
    height = random.randint(5, 40)
    
    hazmat_categories = {
        "Lubricants": random.choice(["Class 3 - Flammable Liquid", None]),
        "Electrical": random.choice(["Class 9 - Lithium Battery", None]) if random.random() > 0.8 else None,
    }
    
    return {
        "packageWeight": f"{pkg_weight} kg",
        "packageDimensions": f"{length} x {width} x {height} cm",
        "unitsPerCarton": random.choice([1, 2, 4, 6, 10, 12, 24]),
        "cartonBarcode": f"489{random.randint(10000000000, 99999999999)}",
        "hazmatClass": hazmat_categories.get(random.choice(list(hazmat_categories.keys())))
    }


# ============================================================================
# PRODUCT DOCUMENT GENERATION
# ============================================================================

def generate_product_document(product_num: int) -> Dict[str, Any]:
    """Generate a realistic enriched product document."""
    category = random.choice(list(PRODUCT_CATEGORIES.keys()))
    subcategory = random.choice(PRODUCT_CATEGORIES[category])

    # Generate part number
    category_codes = {
        "Engine Parts": "ENG", "Electrical": "ELC", "Body Parts": "BDY",
        "Brake System": "BRK", "Suspension": "SUS", "Transmission": "TRN",
        "Cooling System": "COL", "Accessories": "ACC", "Lubricants": "LUB"
    }
    part_number = f"{category_codes[category]}-{random.randint(10000, 99999)}"
    sku = f"OEM-{part_number}-{random.randint(100, 999)}"

    # Compatible models
    num_models = random.randint(1, 5)
    compatible_models = []
    for model in random.sample(OEMPartner_MODELS, min(num_models, len(OEMPartner_MODELS))):
        compatible_models.append({
            "modelCode": model["code"],
            "modelName": model["name"],
            "yearStart": model["years"][0],
            "yearEnd": model["years"][1],
            "notes": f"For {model['cc']}cc variant" if random.random() > 0.7 else None
        })

    # Pricing
    base_price = random.uniform(10, 5000)
    msrp = round(base_price * random.uniform(1.3, 2.0), 2)
    dealer_price = round(base_price * random.uniform(1.1, 1.4), 2)
    cost = round(base_price, 2)

    # Inventory
    total_qty = random.randint(0, 500)
    reorder_point = random.randint(10, 50)

    if total_qty == 0:
        status = "Out of Stock"
    elif total_qty <= reorder_point:
        status = "Low Stock"
    else:
        status = "In Stock"

    # Warehouse distribution
    warehouses = []
    remaining_qty = total_qty
    for wh in random.sample(WAREHOUSES, random.randint(1, min(4, len(WAREHOUSES)))):
        if remaining_qty <= 0:
            break
        wh_qty = random.randint(0, remaining_qty)
        remaining_qty -= wh_qty
        warehouses.append({
            "code": wh["code"],
            "name": wh["name"],
            "quantity": wh_qty,
            "lastRestocked": datetime.now() - timedelta(days=random.randint(1, 60))
        })

    # Generate enriched specifications
    specifications = generate_specifications(category)
    
    # Extract weight for packaging calculation
    weight_str = specifications.get("weight", "1 kg")
    weight_kg = float(weight_str.replace(" kg", ""))

    product = {
        "partNumber": part_number,
        "sku": sku,
        "name": f"{subcategory} - {random.choice(['OEM', 'Genuine', 'Standard'])}",
        "description": f"High quality {subcategory.lower()} for OEMPartner motorcycles. {fake.sentence()}",
        "category": category,
        "subcategory": subcategory,
        "brand": "OEMPartner",
        "compatibleModels": compatible_models,
        "pricing": {
            "msrp": msrp,
            "dealerPrice": dealer_price,
            "cost": cost,
            "currency": "MYR",
            "lastPriceUpdate": datetime.now() - timedelta(days=random.randint(1, 180))
        },
        "inventory": {
            "totalQuantity": total_qty,
            "reorderPoint": reorder_point,
            "status": status,
            "warehouses": warehouses,
            "lastStockCheck": datetime.now() - timedelta(days=random.randint(0, 7))
        },
        # NEW: Enriched specifications with nested dimensions
        "specifications": specifications,
        # NEW: Technical documentation
        "technicalDocs": generate_technical_docs(category, compatible_models),
        # NEW: Manufacturing information
        "manufacturing": generate_manufacturing_info(),
        # NEW: Fitment notes
        "fitmentNotes": generate_fitment_notes(category),
        # NEW: Cross-sell references
        "crossSell": generate_cross_sell(part_number, category),
        # NEW: Sales data
        "salesData": generate_sales_data(),
        # NEW: Packaging info
        "packaging": generate_packaging_info(weight_kg),
        "supersession": {
            "supersededBy": None,
            "supersedes": f"OLD-{random.randint(10000, 99999)}" if random.random() > 0.9 else None
        },
        "relatedProducts": [],
        "images": [
            {
                "url": f"https://parts.OEMPartner.com/images/{part_number.lower()}.jpg",
                "altText": f"{subcategory} image",
                "isPrimary": True
            }
        ],
        "searchText": f"{subcategory} {category} {' '.join([m['modelCode'] for m in compatible_models])}",
        "embedding": None,  # Would be generated via API
        "createdAt": datetime.now() - timedelta(days=random.randint(30, 1000)),
        "updatedAt": datetime.now() - timedelta(days=random.randint(0, 30))
    }

    return product


# ============================================================================
# WARRANTY CLAIM DOCUMENT GENERATION
# ============================================================================

def generate_claim_document(claim_num: int, dealers: List[Dict], products: List[Dict]) -> Dict[str, Any]:
    """Generate a realistic warranty claim document."""
    dealer = random.choice(dealers)
    model = random.choice(OEMPartner_MODELS)

    claim_id = f"WC-{datetime.now().year}-{claim_num:06d}"

    # Dates
    submitted_at = datetime.now() - timedelta(days=random.randint(1, 365))
    purchase_date = submitted_at - timedelta(days=random.randint(30, 730))
    mileage = random.randint(1000, 50000)

    # Status
    status = weighted_choice(CLAIM_STATUSES, CLAIM_STATUS_WEIGHTS)

    # Status history
    status_history = [
        {
            "status": "Draft",
            "changedAt": submitted_at - timedelta(hours=random.randint(1, 24)),
            "changedBy": f"user_{dealer['dealerId'].lower().replace('-', '_')}_1",
            "notes": "Claim created"
        }
    ]

    if status != "Draft":
        status_history.append({
            "status": "Pending Review",
            "changedAt": submitted_at,
            "changedBy": f"user_{dealer['dealerId'].lower().replace('-', '_')}_1",
            "notes": "Submitted for review"
        })

    if status in ["Under Review", "Awaiting Parts", "Approved", "Rejected", "Paid", "Closed"]:
        status_history.append({
            "status": "Under Review",
            "changedAt": submitted_at + timedelta(days=random.randint(1, 3)),
            "changedBy": "mfg_officer_001",
            "notes": "Assigned to reviewer"
        })

    # Vehicle info
    reg_letters = ["W", "B", "J", "P", "K", "D", "N", "A", "T", "C"]
    registration = f"{random.choice(reg_letters)}{random.choice(reg_letters)}{random.randint(1, 9999)} {random.choice('ABCDEFGHJKLMNPQRSTUVWXY')}"

    # Customer info
    customer_name = generate_malaysian_name()

    # Failure details
    failure_category = random.choice(FAILURE_CATEGORIES)

    # Parts claimed
    parts_claimed = []
    parts_total = 0
    num_parts = random.randint(1, 4)

    for _ in range(num_parts):
        if products:
            part = random.choice(products)
            qty = random.randint(1, 2)
            unit_price = part["pricing"]["dealerPrice"]
            total = unit_price * qty
            parts_total += total

            parts_claimed.append({
                "partNumber": part["partNumber"],
                "partName": part["name"],
                "quantity": qty,
                "unitPrice": unit_price,
                "totalPrice": round(total, 2),
                "warrantyApproved": status in ["Approved", "Paid", "Closed"]
            })

    # Labour claimed
    labour_claimed = []
    labour_total = 0
    num_labour = random.randint(1, 3)

    for labour in random.sample(LABOUR_OPERATIONS, min(num_labour, len(LABOUR_OPERATIONS))):
        total = labour["hours"] * labour["rate"]
        labour_total += total

        labour_claimed.append({
            "operationCode": labour["code"],
            "description": labour["desc"],
            "hours": labour["hours"],
            "rate": labour["rate"],
            "totalPrice": round(total, 2),
            "warrantyApproved": status in ["Approved", "Paid", "Closed"]
        })

    claim_total = parts_total + labour_total

    # Approved amounts (if approved)
    if status in ["Approved", "Paid", "Closed"]:
        approved_parts = parts_total * random.uniform(0.8, 1.0)
        approved_labour = labour_total * random.uniform(0.8, 1.0)
        approved_total = approved_parts + approved_labour
    else:
        approved_parts = 0
        approved_labour = 0
        approved_total = 0

    # Review info
    review_info = None
    if status in ["Approved", "Rejected", "Paid", "Closed"]:
        review_info = {
            "reviewedBy": f"mfg_officer_{random.randint(1, 10):03d}",
            "reviewedAt": submitted_at + timedelta(days=random.randint(3, 10)),
            "decision": "Approved" if status != "Rejected" else "Rejected",
            "rejectionReason": random.choice(REJECTION_REASONS) if status == "Rejected" else None,
            "comments": f"Reviewed and {'approved' if status != 'Rejected' else 'rejected'} as per warranty policy."
        }

        status_history.append({
            "status": status if status in ["Approved", "Rejected"] else "Approved",
            "changedAt": review_info["reviewedAt"],
            "changedBy": review_info["reviewedBy"],
            "notes": review_info["comments"]
        })

    # Payment info
    payment_info = None
    if status in ["Paid", "Closed"]:
        payment_info = {
            "paymentDate": submitted_at + timedelta(days=random.randint(10, 30)),
            "paymentAmount": round(approved_total, 2),
            "paymentReference": f"PAY-{datetime.now().year}-{random.randint(100000, 999999)}",
            "paymentMethod": "Bank Transfer"
        }

        status_history.append({
            "status": "Paid",
            "changedAt": payment_info["paymentDate"],
            "changedBy": "finance_system",
            "notes": f"Payment processed: {payment_info['paymentReference']}"
        })

    # SLA tracking
    sla_days = 10  # 10 business days SLA
    days_since_submission = (datetime.now() - submitted_at).days
    sla_breached = days_since_submission > sla_days and status in ["Pending Review", "Under Review", "Awaiting Parts"]

    claim = {
        "claimId": claim_id,
        "status": status,
        "statusHistory": status_history,
        "dealer": {
            "dealerId": dealer["dealerId"],
            "dealerCode": dealer["dealerCode"],
            "name": dealer["name"],
            "region": dealer["region"]
        },
        "vehicle": {
            "modelCode": model["code"],
            "modelName": model["name"],
            "registrationNumber": registration,
            "engineNumber": f"E{model['code']}{random.randint(100000, 999999)}",
            "frameNumber": f"MH3{model['code'][:3]}{random.randint(1000000, 9999999)}",
            "purchaseDate": purchase_date,
            "mileageAtClaim": mileage,
            "warrantyStartDate": purchase_date,
            "warrantyEndDate": purchase_date + timedelta(days=730)  # 2 year warranty
        },
        "customer": {
            "name": customer_name,
            "phone": generate_phone_number(),
            "email": f"{customer_name.lower().replace(' ', '.')}@{random.choice(['gmail.com', 'yahoo.com', 'hotmail.com'])}",
            "address": f"{fake.street_address()}, {dealer['address']['city']}, {dealer['address']['state']}"
        },
        "failure": {
            "category": failure_category,
            "description": f"{failure_category} detected during service. {fake.sentence()}",
            "dateReported": submitted_at - timedelta(days=random.randint(0, 7)),
            "technicianNotes": f"Inspection confirmed {failure_category.lower()}. Replacement required."
        },
        "partsClaimed": parts_claimed,
        "labourClaimed": labour_claimed,
        "totals": {
            "partsTotal": round(parts_total, 2),
            "labourTotal": round(labour_total, 2),
            "claimTotal": round(claim_total, 2),
            "approvedParts": round(approved_parts, 2),
            "approvedLabour": round(approved_labour, 2),
            "approvedTotal": round(approved_total, 2)
        },
        "supportingDocuments": [
            {
                "documentId": f"DOC-{claim_id}-001",
                "documentType": "Service Report",
                "fileName": f"service_report_{claim_id}.pdf",
                "uploadedAt": submitted_at,
                "uploadedBy": f"user_{dealer['dealerId'].lower().replace('-', '_')}_1"
            }
        ],
        "review": review_info,
        "payment": payment_info,
        "sla": {
            "targetDays": sla_days,
            "submittedAt": submitted_at,
            "dueDate": submitted_at + timedelta(days=sla_days),
            "slaBreached": sla_breached,
            "daysElapsed": days_since_submission
        },
        "searchText": f"{claim_id} {customer_name} {registration} {model['code']} {failure_category}",
        "embedding": None,  # Would be generated via API
        "submittedAt": submitted_at,
        "createdAt": submitted_at - timedelta(hours=random.randint(1, 24)),
        "updatedAt": datetime.now() - timedelta(days=random.randint(0, days_since_submission))
    }

    return claim


# ============================================================================
# BATCH INSERTION
# ============================================================================

async def batch_insert(collection, documents: List[Dict], batch_size: int = 100, entity_type: str = "documents"):
    """Insert documents in batches with progress tracking."""
    total = len(documents)
    inserted = 0

    for i in range(0, total, batch_size):
        batch = documents[i:i + batch_size]
        await collection.insert_many(batch, ordered=False)
        inserted += len(batch)
        percentage = (inserted / total) * 100
        print(f"   Progress: {inserted:,}/{total:,} {entity_type} ({percentage:.1f}%) inserted", end='\r')

    print()
    return inserted


async def stream_insert(collection, generator, total_count: int, batch_size: int = 1000, entity_type: str = "documents"):
    """
    Stream insert documents with memory-efficient batching.
    
    This approach generates and inserts documents in batches to avoid
    memory issues with large datasets.
    
    Args:
        collection: MongoDB collection
        generator: Generator function that yields documents
        total_count: Total number of documents to generate
        batch_size: Number of documents per batch (default: 1000)
        entity_type: Description of document type for logging
    
    Returns:
        Number of documents inserted
    """
    import time
    
    inserted = 0
    batch = []
    start_time = time.time()
    last_log_time = start_time
    
    for doc in generator:
        batch.append(doc)
        
        if len(batch) >= batch_size:
            # Insert batch
            await collection.insert_many(batch, ordered=False)
            inserted += len(batch)
            batch = []
            
            # Progress update with time estimate
            current_time = time.time()
            elapsed = current_time - start_time
            
            if current_time - last_log_time >= 1.0:  # Update every second
                rate = inserted / elapsed if elapsed > 0 else 0
                remaining = total_count - inserted
                eta = remaining / rate if rate > 0 else 0
                
                eta_str = f"{int(eta // 60)}m {int(eta % 60)}s" if eta > 60 else f"{int(eta)}s"
                
                percentage = (inserted / total_count) * 100
                print(f"   Progress: {inserted:,}/{total_count:,} ({percentage:.1f}%) | "
                      f"{rate:.0f}/s | ETA: {eta_str}     ", end='\r')
                last_log_time = current_time
    
    # Insert remaining documents
    if batch:
        await collection.insert_many(batch, ordered=False)
        inserted += len(batch)
    
    # Final summary
    elapsed = time.time() - start_time
    rate = inserted / elapsed if elapsed > 0 else 0
    print(f"   ✅ Inserted {inserted:,} {entity_type} in {elapsed:.1f}s ({rate:.0f}/s)      ")
    
    return inserted


def products_generator(count: int, start_num: int = 1):
    """Generator that yields product documents one at a time."""
    for i in range(count):
        yield generate_product_document(start_num + i)


def claims_generator(count: int, dealers: List[Dict], products: List[Dict], start_num: int = 1):
    """Generator that yields claim documents one at a time."""
    for i in range(count):
        yield generate_claim_document(start_num + i, dealers, products)


# ============================================================================
# MAIN DATA GENERATION FUNCTION
# ============================================================================

async def generate_sample_data(
    num_products: int, 
    num_claims: int, 
    num_dealers: int,
    batch_size: int = 1000,
    use_streaming: bool = True
):
    """
    Generate sample data and insert into MongoDB.

    Args:
        num_products: Number of product documents to generate
        num_claims: Number of warranty claim documents to generate
        num_dealers: Number of dealer documents to generate
        batch_size: Batch size for bulk inserts (default: 1000 for large datasets)
        use_streaming: Use streaming insert for large datasets (default: True)
    """
    import time
    overall_start = time.time()
    
    print(f"🏍️  Starting OEMPartner Dealer Portal sample data generation...")
    print(f"   Products: {num_products:,}")
    print(f"   Warranty Claims: {num_claims:,}")
    print(f"   Dealers: {num_dealers:,}")
    
    # Determine optimal batch size based on data volume
    if num_products > 10000 or num_claims > 10000:
        batch_size = max(batch_size, 2000)
        print(f"   Batch size: {batch_size:,} (optimized for large dataset)")
    else:
        print(f"   Batch size: {batch_size:,}")
    print()

    # Connect to MongoDB
    client = AsyncMongoClient(settings.mongodb_url)
    db = client[settings.mongodb_db_name]

    try:
        # ========================================
        # PHASE 1: Generate and Insert Dealers
        # ========================================
        print(f"🏪 Phase 1: Generating {num_dealers:,} dealers...")
        dealers = []

        for i in range(num_dealers):
            dealer = generate_dealer_document(i + 1)
            dealers.append(dealer)

        print(f"   ✅ Generated {len(dealers):,} dealers")

        if dealers:
            print(f"   Inserting dealers into database...")
            await batch_insert(db.dealers, dealers, batch_size=min(batch_size, 500), entity_type="dealers")

        # ========================================
        # PHASE 2: Generate and Insert Products
        # ========================================
        print(f"\n📦 Phase 2: Generating and inserting {num_products:,} products...")
        
        if use_streaming and num_products > 10000:
            # Use streaming insert for large datasets (memory efficient)
            await stream_insert(
                db.products,
                products_generator(num_products),
                num_products,
                batch_size=batch_size,
                entity_type="products"
            )
            # Need to fetch some products for claims
            print(f"   Fetching product sample for claims generation...")
            products_cursor = db.products.find({}, {"partNumber": 1, "name": 1, "pricing.dealerPrice": 1})
            products = await products_cursor.to_list(length=min(5000, num_products))
            print(f"   ✅ Fetched {len(products):,} products for reference")
        else:
            # Traditional approach for smaller datasets
            products = []
            for i in range(num_products):
                product = generate_product_document(i + 1)
                products.append(product)
                if (i + 1) % 1000 == 0:
                    print(f"   Generated {i + 1:,}/{num_products:,} products", end='\r')
            print()
            if products:
                print(f"   Inserting products into database...")
                await batch_insert(db.products, products, batch_size=batch_size, entity_type="products")

        # ========================================
        # PHASE 3: Generate and Insert Claims
        # ========================================
        print(f"\n📋 Phase 3: Generating and inserting {num_claims:,} warranty claims...")
        
        if use_streaming and num_claims > 10000:
            # Use streaming insert for large datasets
            await stream_insert(
                db.warrantyClaims,
                claims_generator(num_claims, dealers, products),
                num_claims,
                batch_size=batch_size,
                entity_type="claims"
            )
        else:
            # Traditional approach for smaller datasets
            claims = []
            for i in range(num_claims):
                claim = generate_claim_document(i + 1, dealers, products)
                claims.append(claim)
                if (i + 1) % 1000 == 0:
                    print(f"   Generated {i + 1:,}/{num_claims:,} claims", end='\r')
            print()
            if claims:
                print(f"   Inserting claims into database...")
                await batch_insert(db.warrantyClaims, claims, batch_size=batch_size, entity_type="claims")

        # ========================================
        # PHASE 4: Update Dealer Metrics (Aggregation)
        # ========================================
        print(f"\n📊 Phase 4: Updating dealer metrics via aggregation...")
        
        # Use aggregation pipeline for efficient metric calculation
        pipeline = [
            {"$group": {
                "_id": "$dealer.dealerId",
                "totalClaims": {"$sum": 1},
                "approvedClaims": {
                    "$sum": {"$cond": [{"$in": ["$status", ["Approved", "Paid", "Closed"]]}, 1, 0]}
                },
                "totalValue": {"$sum": "$totals.claimTotal"}
            }}
        ]
        
        cursor = await db.warrantyClaims.aggregate(pipeline).to_list(length=None)
        metrics = cursor
        
        for m in metrics:
            approval_rate = m["approvedClaims"] / m["totalClaims"] if m["totalClaims"] > 0 else 0
            await db.dealers.update_one(
                {"dealerId": m["_id"]},
                {"$set": {
                    "metrics.totalClaimsSubmitted": m["totalClaims"],
                    "metrics.totalClaimsApproved": m["approvedClaims"],
                    "metrics.totalClaimValue": m["totalValue"],
                    "metrics.approvalRate": round(approval_rate, 2)
                }}
            )
        
        print(f"   ✅ Updated metrics for {len(metrics):,} dealers")

        # ========================================
        # SUMMARY
        # ========================================
        elapsed = time.time() - overall_start
        elapsed_str = f"{int(elapsed // 60)}m {int(elapsed % 60)}s" if elapsed > 60 else f"{elapsed:.1f}s"
        
        dealers_count = await db.dealers.count_documents({})
        products_count = await db.products.count_documents({})
        claims_count = await db.warrantyClaims.count_documents({})
        
        print(f"\n✅ Sample data generation complete in {elapsed_str}!")
        print(f"\n📈 Summary:")
        print(f"   Total dealers: {dealers_count:,}")
        print(f"   Total products: {products_count:,}")
        print(f"   Total warranty claims: {claims_count:,}")
        
        # Provide scaling tips if dataset is large
        if products_count > 100000:
            print(f"\n💡 Large dataset tips:")
            print(f"   - Atlas Search indexes may take 5-15 minutes to build")
            print(f"   - Run embeddings separately: python generate_embeddings.py")
            print(f"   - Consider running during low-traffic periods")
        else:
            print(f"\n💡 Next steps:")
            print(f"   1. Create Atlas Search indexes")
            print(f"   2. Run: python generate_embeddings.py (if using vector search)")
            print(f"   3. Start backend: python -m app.main")
            print(f"   4. Start frontend: cd ../frontend && npm run dev")

    except Exception as e:
        print(f"\n❌ Error generating sample data: {e}")
        import traceback
        traceback.print_exc()
        raise

    finally:
        await client.close()


async def clear_sample_data():
    """Clear all sample data from the database."""
    client = AsyncMongoClient(settings.mongodb_url)
    db = client[settings.mongodb_db_name]

    try:
        print("🗑️  Clearing sample data...")

        dealers_count = await db.dealers.count_documents({})
        products_count = await db.products.count_documents({})
        claims_count = await db.warrantyClaims.count_documents({})

        if dealers_count > 0 or products_count > 0 or claims_count > 0:
            print(f"\n⚠️  WARNING: This will delete:")
            print(f"   - {dealers_count:,} dealers")
            print(f"   - {products_count:,} products")
            print(f"   - {claims_count:,} warranty claims")

            confirm = input("\nType 'DELETE' to confirm: ")

            if confirm == "DELETE":
                print("\n   Deleting dealers...")
                await db.dealers.delete_many({})
                print(f"   ✅ Deleted {dealers_count:,} dealers")

                print("   Deleting products...")
                await db.products.delete_many({})
                print(f"   ✅ Deleted {products_count:,} products")

                print("   Deleting warranty claims...")
                await db.warrantyClaims.delete_many({})
                print(f"   ✅ Deleted {claims_count:,} warranty claims")

                # Also clear materialized views
                print("   Clearing materialized views...")
                await db.mv_product_stats.delete_many({})
                await db.mv_claim_stats.delete_many({})
                await db.mv_dealer_claim_stats.delete_many({})
                await db.mv_claims_trend.delete_many({})
                print("   ✅ Cleared materialized views")

                print("\n✅ Sample data cleared")
            else:
                print("❌ Operation cancelled")
        else:
            print("ℹ️  No data to clear")

    finally:
        await client.close()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate sample data for OEMPartner Dealer Portal",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate small dataset for development
  python generate_sample_data.py --products 100 --claims 200 --dealers 10

  # Generate medium dataset for testing
  python generate_sample_data.py --products 1000 --claims 2000 --dealers 50

  # Generate large dataset (1M products, 100K claims) - PRODUCTION SCALE
  python generate_sample_data.py --products 1000000 --claims 100000 --dealers 500

  # Generate 100K products at a time with custom batch size
  python generate_sample_data.py --products 100000 --claims 0 --dealers 0 --batch-size 5000

  # Clear all existing data
  python generate_sample_data.py --clear
        """
    )
    parser.add_argument("--products", type=int, default=100, help="Number of product records (default: 100)")
    parser.add_argument("--claims", type=int, default=200, help="Number of warranty claim records (default: 200)")
    parser.add_argument("--dealers", type=int, default=10, help="Number of dealer records (default: 10)")
    parser.add_argument("--batch-size", type=int, default=1000, help="Batch size for bulk inserts (default: 1000)")
    parser.add_argument("--no-streaming", action="store_true", help="Disable streaming insert (uses more memory)")
    parser.add_argument("--clear", action="store_true", help="Clear existing sample data")

    args = parser.parse_args()

    if args.clear:
        asyncio.run(clear_sample_data())
    else:
        asyncio.run(generate_sample_data(
            num_products=args.products, 
            num_claims=args.claims, 
            num_dealers=args.dealers,
            batch_size=args.batch_size,
            use_streaming=not args.no_streaming
        ))


if __name__ == "__main__":
    main()
