"""
Seed Data for Job Categories, Roles, and Question Templates.

This module provides the initial data for seeding the job_master tables.
Run via: python -m app.domains.job_master.seed_data
"""

import asyncio
import uuid
from typing import List, Dict, Any

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.job_master.models import (
    JobCategory,
    JobRole,
    RoleQuestionTemplate,
    job_category_role_association,
    JobType,
)
from app.shared.database import async_session_factory
from app.shared.logging import get_logger, setup_logging


logger = get_logger(__name__)


# ==================== CATEGORIES ====================

CATEGORIES: List[Dict[str, Any]] = [
    {"name": "Technology & IT", "slug": "technology-it", "icon": "laptop", "display_order": 1, "description": "Software development, IT support, data science, and tech roles"},
    {"name": "Delivery & Logistics", "slug": "delivery-logistics", "icon": "truck", "display_order": 2, "description": "Delivery, courier, warehouse, and logistics roles"},
    {"name": "Customer Support", "slug": "customer-support", "icon": "headset", "display_order": 3, "description": "Telecalling, customer care, and support roles"},
    {"name": "Sales & Marketing", "slug": "sales-marketing", "icon": "megaphone", "display_order": 4, "description": "Sales, marketing, business development roles"},
    {"name": "Healthcare", "slug": "healthcare", "icon": "heart-pulse", "display_order": 5, "description": "Nursing, medical assistance, pharmacy, and healthcare roles"},
    {"name": "Education & Training", "slug": "education-training", "icon": "graduation-cap", "display_order": 6, "description": "Teaching, tutoring, training, and education roles"},
    {"name": "Manufacturing & Production", "slug": "manufacturing-production", "icon": "factory", "display_order": 7, "description": "Factory work, assembly, quality control roles"},
    {"name": "Construction & Trades", "slug": "construction-trades", "icon": "hard-hat", "display_order": 8, "description": "Construction, plumbing, electrical, and skilled trades"},
    {"name": "Food & Hospitality", "slug": "food-hospitality", "icon": "utensils", "display_order": 9, "description": "Restaurant, hotel, catering, and hospitality roles"},
    {"name": "Retail & E-commerce", "slug": "retail-ecommerce", "icon": "shopping-bag", "display_order": 10, "description": "Retail, e-commerce, inventory management roles"},
    {"name": "Finance & Accounting", "slug": "finance-accounting", "icon": "calculator", "display_order": 11, "description": "Accounting, banking, insurance, and finance roles"},
    {"name": "Design & Creative", "slug": "design-creative", "icon": "palette", "display_order": 12, "description": "Graphic design, UI/UX, content creation, and creative roles"},
    {"name": "Security & Facility", "slug": "security-facility", "icon": "shield", "display_order": 13, "description": "Security guard, facility management, housekeeping roles"},
    {"name": "Transportation & Driving", "slug": "transportation-driving", "icon": "car", "display_order": 14, "description": "Driver, cab services, transport, and vehicle-related roles"},
    {"name": "Agriculture & Farming", "slug": "agriculture-farming", "icon": "sprout", "display_order": 15, "description": "Farming, agriculture, and allied roles"},
]

# ==================== ROLES ====================
# Each role has: name, slug, job_type, description, suggested_skills, categories (list of category slugs)

ROLES: List[Dict[str, Any]] = [
    # Technology & IT
    {
        "name": "Software Developer",
        "slug": "software-developer",
        "job_type": JobType.WHITE_COLLAR,
        "description": "Develops software applications and systems",
        "suggested_skills": ["JavaScript", "Python", "React", "Node.js", "Java", "SQL", "Git", "Docker", "AWS", "TypeScript"],
        "categories": ["technology-it"],
    },
    {
        "name": "Frontend Developer",
        "slug": "frontend-developer",
        "job_type": JobType.WHITE_COLLAR,
        "description": "Builds user interfaces and web applications",
        "suggested_skills": ["React", "JavaScript", "TypeScript", "HTML", "CSS", "Next.js", "Tailwind CSS", "Vue.js", "Angular"],
        "categories": ["technology-it"],
    },
    {
        "name": "Backend Developer",
        "slug": "backend-developer",
        "job_type": JobType.WHITE_COLLAR,
        "description": "Builds server-side logic and APIs",
        "suggested_skills": ["Python", "Node.js", "Java", "PostgreSQL", "MongoDB", "FastAPI", "Django", "Express.js", "Redis"],
        "categories": ["technology-it"],
    },
    {
        "name": "Data Analyst",
        "slug": "data-analyst",
        "job_type": JobType.WHITE_COLLAR,
        "description": "Analyzes data to provide business insights",
        "suggested_skills": ["Python", "SQL", "Excel", "Tableau", "Power BI", "R", "Statistics", "Data Visualization"],
        "categories": ["technology-it"],
    },
    {
        "name": "IT Support Technician",
        "slug": "it-support-technician",
        "job_type": JobType.WHITE_COLLAR,
        "description": "Provides technical support and troubleshooting",
        "suggested_skills": ["Windows", "Linux", "Networking", "Hardware", "Troubleshooting", "Active Directory"],
        "categories": ["technology-it"],
    },
    # Delivery & Logistics
    {
        "name": "Delivery Boy",
        "slug": "delivery-boy",
        "job_type": JobType.BLUE_COLLAR,
        "description": "Delivers packages and food items to customers",
        "suggested_skills": ["Driving", "Navigation", "Customer Service", "Time Management"],
        "categories": ["delivery-logistics", "transportation-driving"],
    },
    {
        "name": "Warehouse Associate",
        "slug": "warehouse-associate",
        "job_type": JobType.BLUE_COLLAR,
        "description": "Handles warehouse operations including loading, unloading, and sorting",
        "suggested_skills": ["Inventory Management", "Physical Fitness", "Forklift Operation", "Organization"],
        "categories": ["delivery-logistics", "manufacturing-production"],
    },
    {
        "name": "Courier Executive",
        "slug": "courier-executive",
        "job_type": JobType.BLUE_COLLAR,
        "description": "Picks up and delivers documents and parcels",
        "suggested_skills": ["Driving", "Navigation", "Time Management", "Communication"],
        "categories": ["delivery-logistics"],
    },
    # Customer Support
    {
        "name": "Telecaller",
        "slug": "telecaller",
        "job_type": JobType.BLUE_COLLAR,
        "description": "Makes and receives calls for sales, support, or verification",
        "suggested_skills": ["Communication", "Multilingual", "Sales", "Customer Service", "Computer Basics"],
        "categories": ["customer-support", "sales-marketing"],
    },
    {
        "name": "Customer Care Executive",
        "slug": "customer-care-executive",
        "job_type": JobType.BLUE_COLLAR,
        "description": "Handles customer queries and complaints",
        "suggested_skills": ["Communication", "Problem Solving", "Empathy", "Computer Basics", "Multilingual"],
        "categories": ["customer-support"],
    },
    # Sales & Marketing
    {
        "name": "Sales Executive",
        "slug": "sales-executive",
        "job_type": JobType.WHITE_COLLAR,
        "description": "Drives sales and manages client relationships",
        "suggested_skills": ["Sales", "Negotiation", "CRM", "Communication", "Target Achievement"],
        "categories": ["sales-marketing"],
    },
    {
        "name": "Digital Marketing Executive",
        "slug": "digital-marketing-executive",
        "job_type": JobType.WHITE_COLLAR,
        "description": "Manages digital marketing campaigns",
        "suggested_skills": ["SEO", "Google Ads", "Social Media", "Content Marketing", "Analytics", "Email Marketing"],
        "categories": ["sales-marketing", "design-creative"],
    },
    {
        "name": "Field Sales Representative",
        "slug": "field-sales-representative",
        "job_type": JobType.BLUE_COLLAR,
        "description": "Conducts in-person sales visits and demos",
        "suggested_skills": ["Sales", "Communication", "Travelling", "Negotiation", "Local Language"],
        "categories": ["sales-marketing"],
    },
    # Healthcare
    {
        "name": "Nurse",
        "slug": "nurse",
        "job_type": JobType.WHITE_COLLAR,
        "description": "Provides patient care in hospitals and clinics",
        "suggested_skills": ["Patient Care", "Medical Knowledge", "First Aid", "Communication", "Empathy"],
        "categories": ["healthcare"],
    },
    {
        "name": "Medical Lab Technician",
        "slug": "medical-lab-technician",
        "job_type": JobType.WHITE_COLLAR,
        "description": "Performs laboratory tests and diagnostics",
        "suggested_skills": ["Lab Equipment", "Sample Analysis", "Medical Knowledge", "Attention to Detail"],
        "categories": ["healthcare"],
    },
    # Food & Hospitality
    {
        "name": "Cook / Chef",
        "slug": "cook-chef",
        "job_type": JobType.BLUE_COLLAR,
        "description": "Prepares food in restaurants, hotels, or catering",
        "suggested_skills": ["Cooking", "Food Safety", "Menu Planning", "Kitchen Management"],
        "categories": ["food-hospitality"],
    },
    {
        "name": "Waiter / Server",
        "slug": "waiter-server",
        "job_type": JobType.BLUE_COLLAR,
        "description": "Serves food and beverages to customers",
        "suggested_skills": ["Customer Service", "Communication", "Multitasking", "Teamwork"],
        "categories": ["food-hospitality"],
    },
    # Security & Facility
    {
        "name": "Security Guard",
        "slug": "security-guard",
        "job_type": JobType.BLUE_COLLAR,
        "description": "Provides security at premises",
        "suggested_skills": ["Vigilance", "Physical Fitness", "Communication", "Emergency Response"],
        "categories": ["security-facility"],
    },
    {
        "name": "Housekeeping Staff",
        "slug": "housekeeping-staff",
        "job_type": JobType.BLUE_COLLAR,
        "description": "Maintains cleanliness of hotels, offices, or homes",
        "suggested_skills": ["Cleaning", "Time Management", "Attention to Detail", "Physical Fitness"],
        "categories": ["security-facility", "food-hospitality"],
    },
    # Transportation & Driving
    {
        "name": "Cab / Taxi Driver",
        "slug": "cab-taxi-driver",
        "job_type": JobType.BLUE_COLLAR,
        "description": "Drives passengers in taxis or cab services",
        "suggested_skills": ["Driving", "Navigation", "Customer Service", "Vehicle Maintenance"],
        "categories": ["transportation-driving"],
    },
    {
        "name": "Truck Driver",
        "slug": "truck-driver",
        "job_type": JobType.BLUE_COLLAR,
        "description": "Operates heavy vehicles for goods transport",
        "suggested_skills": ["Heavy Vehicle Driving", "Navigation", "Vehicle Maintenance", "Logistics"],
        "categories": ["transportation-driving", "delivery-logistics"],
    },
    # Finance & Accounting
    {
        "name": "Accountant",
        "slug": "accountant",
        "job_type": JobType.WHITE_COLLAR,
        "description": "Manages financial records and reporting",
        "suggested_skills": ["Tally", "Excel", "GST", "Accounting", "Taxation", "Financial Reporting"],
        "categories": ["finance-accounting"],
    },
    # Design & Creative
    {
        "name": "Graphic Designer",
        "slug": "graphic-designer",
        "job_type": JobType.WHITE_COLLAR,
        "description": "Creates visual content for branding and marketing",
        "suggested_skills": ["Photoshop", "Illustrator", "Figma", "Canva", "Branding", "Typography"],
        "categories": ["design-creative"],
    },
    # Retail
    {
        "name": "Store Associate",
        "slug": "store-associate",
        "job_type": JobType.BLUE_COLLAR,
        "description": "Assists customers and manages store operations",
        "suggested_skills": ["Customer Service", "Sales", "Inventory", "Cash Handling", "Communication"],
        "categories": ["retail-ecommerce"],
    },
    # Education
    {
        "name": "Tutor / Teacher",
        "slug": "tutor-teacher",
        "job_type": JobType.WHITE_COLLAR,
        "description": "Teaches students in schools or coaching centers",
        "suggested_skills": ["Teaching", "Subject Expertise", "Communication", "Patience", "Classroom Management"],
        "categories": ["education-training"],
    },
]


# ==================== QUESTION TEMPLATES ====================
# Templates per role slug. Questions drive the resume builder bot flow.

QUESTION_TEMPLATES: Dict[str, List[Dict[str, Any]]] = {
    # Blue-collar: Delivery Boy
    "delivery-boy": [
        {
            "question_key": "full_name",
            "question_text": "What is your full name?",
            "question_type": "text",
            "is_required": True,
            "display_order": 1,
            "validation_rules": {"min_length": 2, "max_length": 100},
        },
        {
            "question_key": "date_of_birth",
            "question_text": "What is your date of birth?",
            "question_type": "date",
            "is_required": True,
            "display_order": 2,
            "validation_rules": {"min_age": 18},
        },
        {
            "question_key": "has_driving_license",
            "question_text": "Do you have a valid driving license?",
            "question_type": "boolean",
            "is_required": True,
            "display_order": 3,
        },
        {
            "question_key": "driving_license_document",
            "question_text": "Please upload your driving license document for verification.",
            "question_type": "file",
            "is_required": False,
            "display_order": 4,
            "condition": {"depends_on": "has_driving_license", "value": True},
        },
        {
            "question_key": "owns_vehicle",
            "question_text": "Do you own a vehicle?",
            "question_type": "boolean",
            "is_required": True,
            "display_order": 5,
        },
        {
            "question_key": "vehicle_type",
            "question_text": "What type of vehicle do you own?",
            "question_type": "select",
            "options": ["Bicycle", "Scooter/Moped", "Motorcycle", "Car", "Auto-rickshaw"],
            "is_required": True,
            "display_order": 6,
            "condition": {"depends_on": "owns_vehicle", "value": True},
        },
        {
            "question_key": "preferred_location",
            "question_text": "Which area/city do you prefer to work in?",
            "question_type": "text",
            "is_required": True,
            "display_order": 7,
        },
        {
            "question_key": "languages_known",
            "question_text": "Which languages do you speak?",
            "question_type": "multi_select",
            "options": ["Hindi", "English", "Tamil", "Telugu", "Kannada", "Malayalam", "Bengali", "Marathi", "Gujarati", "Punjabi", "Other"],
            "is_required": True,
            "display_order": 8,
        },
        {
            "question_key": "experience_years",
            "question_text": "How many years of delivery experience do you have?",
            "question_type": "number",
            "is_required": True,
            "display_order": 9,
            "validation_rules": {"min": 0, "max": 40},
        },
        {
            "question_key": "salary_expectation",
            "question_text": "What is your expected monthly salary (in INR)?",
            "question_type": "number",
            "is_required": True,
            "display_order": 10,
            "validation_rules": {"min": 5000, "max": 100000},
        },
        {
            "question_key": "about",
            "question_text": "Tell us a little about yourself.",
            "question_type": "text",
            "is_required": False,
            "display_order": 11,
        },
    ],
    # Blue-collar: Telecaller
    "telecaller": [
        {
            "question_key": "full_name",
            "question_text": "What is your full name?",
            "question_type": "text",
            "is_required": True,
            "display_order": 1,
        },
        {
            "question_key": "date_of_birth",
            "question_text": "What is your date of birth?",
            "question_type": "date",
            "is_required": True,
            "display_order": 2,
            "validation_rules": {"min_age": 18},
        },
        {
            "question_key": "languages_known",
            "question_text": "Which languages can you speak fluently? (Multilingual candidates preferred)",
            "question_type": "multi_select",
            "options": ["Hindi", "English", "Tamil", "Telugu", "Kannada", "Malayalam", "Bengali", "Marathi", "Gujarati", "Punjabi", "Other"],
            "is_required": True,
            "display_order": 3,
        },
        {
            "question_key": "computer_skills",
            "question_text": "Do you have basic computer skills?",
            "question_type": "boolean",
            "is_required": True,
            "display_order": 4,
        },
        {
            "question_key": "experience_years",
            "question_text": "How many years of telecalling or customer support experience do you have?",
            "question_type": "number",
            "is_required": True,
            "display_order": 5,
            "validation_rules": {"min": 0, "max": 30},
        },
        {
            "question_key": "preferred_shift",
            "question_text": "Which shift do you prefer?",
            "question_type": "select",
            "options": ["Day Shift", "Night Shift", "Rotational", "Flexible"],
            "is_required": True,
            "display_order": 6,
        },
        {
            "question_key": "salary_expectation",
            "question_text": "What is your expected monthly salary (in INR)?",
            "question_type": "number",
            "is_required": True,
            "display_order": 7,
            "validation_rules": {"min": 5000, "max": 100000},
        },
        {
            "question_key": "about",
            "question_text": "Tell us a little about yourself.",
            "question_type": "text",
            "is_required": False,
            "display_order": 8,
        },
    ],
    # White-collar: Software Developer
    "software-developer": [
        {
            "question_key": "full_name",
            "question_text": "What is your full name?",
            "question_type": "text",
            "is_required": True,
            "display_order": 1,
        },
        {
            "question_key": "date_of_birth",
            "question_text": "What is your date of birth?",
            "question_type": "date",
            "is_required": True,
            "display_order": 2,
        },
        {
            "question_key": "education",
            "question_text": "What is your highest education qualification?",
            "question_type": "select",
            "options": ["High School", "Diploma", "Bachelor's Degree", "Master's Degree", "PhD", "Other"],
            "is_required": True,
            "display_order": 3,
        },
        {
            "question_key": "skills",
            "question_text": "What are your technical skills? (Select or type custom)",
            "question_type": "multi_select",
            "options": ["JavaScript", "Python", "React", "Node.js", "Java", "SQL", "Git", "Docker", "AWS", "TypeScript"],
            "is_required": True,
            "display_order": 4,
        },
        {
            "question_key": "experience_years",
            "question_text": "What is your total years of experience in software development?",
            "question_type": "number",
            "is_required": True,
            "display_order": 5,
            "validation_rules": {"min": 0, "max": 40},
        },
        {
            "question_key": "experience_details",
            "question_text": "Briefly describe your most recent role and responsibilities.",
            "question_type": "text",
            "is_required": False,
            "display_order": 6,
        },
        {
            "question_key": "preferred_work_type",
            "question_text": "What is your preferred work arrangement?",
            "question_type": "select",
            "options": ["Remote", "Onsite", "Hybrid", "Flexible"],
            "is_required": True,
            "display_order": 7,
        },
        {
            "question_key": "preferred_location",
            "question_text": "What is your preferred job location?",
            "question_type": "text",
            "is_required": True,
            "display_order": 8,
        },
        {
            "question_key": "salary_expectation",
            "question_text": "What is your expected monthly salary (in INR)?",
            "question_type": "number",
            "is_required": True,
            "display_order": 9,
            "validation_rules": {"min": 10000, "max": 500000},
        },
        {
            "question_key": "portfolio_url",
            "question_text": "Do you have a portfolio or GitHub profile? (Optional)",
            "question_type": "text",
            "is_required": False,
            "display_order": 10,
        },
        {
            "question_key": "about",
            "question_text": "Tell us a little about yourself.",
            "question_type": "text",
            "is_required": False,
            "display_order": 11,
        },
    ],
    # White-collar: Backend Developer
    "backend-developer": [
        {
            "question_key": "full_name",
            "question_text": "What is your full name?",
            "question_type": "text",
            "is_required": True,
            "display_order": 1,
        },
        {
            "question_key": "date_of_birth",
            "question_text": "What is your date of birth?",
            "question_type": "date",
            "is_required": True,
            "display_order": 2,
        },
        {
            "question_key": "education",
            "question_text": "What is your highest education qualification?",
            "question_type": "select",
            "options": ["High School", "Diploma", "Bachelor's Degree", "Master's Degree", "PhD", "Other"],
            "is_required": True,
            "display_order": 3,
        },
        {
            "question_key": "technical_skills",
            "question_text": "What backend technologies and languages do you use?",
            "question_type": "multi_select",
            "options": ["Python", "Node.js", "Java", "Go", "C#", "Ruby", "PHP", "PostgreSQL", "MongoDB", "Redis", "SQL", "REST APIs", "GraphQL", "Docker", "AWS", "FastAPI", "Django", "Express.js", "Spring Boot"],
            "is_required": True,
            "display_order": 4,
        },
        {
            "question_key": "experience_years",
            "question_text": "How many years of backend development experience do you have?",
            "question_type": "number",
            "is_required": True,
            "display_order": 5,
            "validation_rules": {"min": 0, "max": 40},
        },
        {
            "question_key": "experience_details",
            "question_text": "Do you have experience building REST or GraphQL APIs? Briefly describe your backend experience.",
            "question_type": "text",
            "is_required": False,
            "display_order": 6,
        },
        {
            "question_key": "preferred_work_type",
            "question_text": "What is your preferred work arrangement?",
            "question_type": "select",
            "options": ["Remote", "Onsite", "Hybrid", "Flexible"],
            "is_required": True,
            "display_order": 7,
        },
        {
            "question_key": "preferred_location",
            "question_text": "What is your preferred job location?",
            "question_type": "text",
            "is_required": True,
            "display_order": 8,
        },
        {
            "question_key": "languages_known",
            "question_text": "Which languages do you speak?",
            "question_type": "multi_select",
            "options": ["Hindi", "English", "Tamil", "Telugu", "Kannada", "Bengali", "Marathi", "Gujarati", "Other"],
            "is_required": False,
            "display_order": 9,
        },
        {
            "question_key": "salary_expectation",
            "question_text": "What is your expected monthly salary (in INR)?",
            "question_type": "number",
            "is_required": True,
            "display_order": 10,
            "validation_rules": {"min": 15000, "max": 500000},
        },
        {
            "question_key": "portfolio_url",
            "question_text": "Do you have a GitHub profile or portfolio link? (Optional)",
            "question_type": "text",
            "is_required": False,
            "display_order": 11,
        },
        {
            "question_key": "about",
            "question_text": "Tell us a little about yourself and your backend development goals.",
            "question_type": "text",
            "is_required": False,
            "display_order": 12,
        },
    ],
    # White-collar: Graphic Designer
    "graphic-designer": [
        {
            "question_key": "full_name",
            "question_text": "What is your full name?",
            "question_type": "text",
            "is_required": True,
            "display_order": 1,
        },
        {
            "question_key": "skills",
            "question_text": "What design tools/skills do you know?",
            "question_type": "multi_select",
            "options": ["Photoshop", "Illustrator", "Figma", "Canva", "After Effects", "InDesign", "Sketch"],
            "is_required": True,
            "display_order": 2,
        },
        {
            "question_key": "experience_years",
            "question_text": "How many years of design experience do you have?",
            "question_type": "number",
            "is_required": True,
            "display_order": 3,
            "validation_rules": {"min": 0, "max": 40},
        },
        {
            "question_key": "portfolio_url",
            "question_text": "Share your portfolio link (Behance, Dribbble, or personal website).",
            "question_type": "text",
            "is_required": False,
            "display_order": 4,
        },
        {
            "question_key": "salary_expectation",
            "question_text": "What is your expected monthly salary (in INR)?",
            "question_type": "number",
            "is_required": True,
            "display_order": 5,
            "validation_rules": {"min": 10000, "max": 300000},
        },
        {
            "question_key": "about",
            "question_text": "Tell us a little about yourself.",
            "question_type": "text",
            "is_required": False,
            "display_order": 6,
        },
    ],
    # Blue-collar: Security Guard
    "security-guard": [
        {
            "question_key": "full_name",
            "question_text": "What is your full name?",
            "question_type": "text",
            "is_required": True,
            "display_order": 1,
        },
        {
            "question_key": "date_of_birth",
            "question_text": "What is your date of birth?",
            "question_type": "date",
            "is_required": True,
            "display_order": 2,
            "validation_rules": {"min_age": 18, "max_age": 55},
        },
        {
            "question_key": "physical_fitness",
            "question_text": "Are you physically fit for security duties?",
            "question_type": "boolean",
            "is_required": True,
            "display_order": 3,
        },
        {
            "question_key": "experience_years",
            "question_text": "How many years of security experience do you have?",
            "question_type": "number",
            "is_required": True,
            "display_order": 4,
            "validation_rules": {"min": 0, "max": 40},
        },
        {
            "question_key": "preferred_shift",
            "question_text": "Which shift do you prefer?",
            "question_type": "select",
            "options": ["Day Shift", "Night Shift", "Rotational"],
            "is_required": True,
            "display_order": 5,
        },
        {
            "question_key": "salary_expectation",
            "question_text": "What is your expected monthly salary (in INR)?",
            "question_type": "number",
            "is_required": True,
            "display_order": 6,
            "validation_rules": {"min": 5000, "max": 50000},
        },
    ],
    # Blue-collar: Cab/Taxi Driver
    "cab-taxi-driver": [
        {
            "question_key": "full_name",
            "question_text": "What is your full name?",
            "question_type": "text",
            "is_required": True,
            "display_order": 1,
        },
        {
            "question_key": "date_of_birth",
            "question_text": "What is your date of birth?",
            "question_type": "date",
            "is_required": True,
            "display_order": 2,
            "validation_rules": {"min_age": 18},
        },
        {
            "question_key": "has_driving_license",
            "question_text": "Do you have a valid driving license?",
            "question_type": "boolean",
            "is_required": True,
            "display_order": 3,
        },
        {
            "question_key": "license_type",
            "question_text": "What type of license do you have?",
            "question_type": "select",
            "options": ["LMV (Light Motor Vehicle)", "HMV (Heavy Motor Vehicle)", "Both"],
            "is_required": True,
            "display_order": 4,
            "condition": {"depends_on": "has_driving_license", "value": True},
        },
        {
            "question_key": "owns_vehicle",
            "question_text": "Do you own a vehicle for cab service?",
            "question_type": "boolean",
            "is_required": True,
            "display_order": 5,
        },
        {
            "question_key": "experience_years",
            "question_text": "How many years of driving experience do you have?",
            "question_type": "number",
            "is_required": True,
            "display_order": 6,
            "validation_rules": {"min": 0, "max": 40},
        },
        {
            "question_key": "languages_known",
            "question_text": "Which languages do you speak?",
            "question_type": "multi_select",
            "options": ["Hindi", "English", "Tamil", "Telugu", "Kannada", "Bengali", "Marathi", "Other"],
            "is_required": True,
            "display_order": 7,
        },
        {
            "question_key": "salary_expectation",
            "question_text": "What is your expected monthly salary (in INR)?",
            "question_type": "number",
            "is_required": True,
            "display_order": 8,
            "validation_rules": {"min": 10000, "max": 80000},
        },
    ],
}


# ==================== SEED FUNCTION ====================

async def seed_job_master_data() -> None:
    """
    Seed job categories, roles, and question templates.

    This function is idempotent - it checks for existing data before inserting.
    """
    async with async_session_factory() as session:
        try:
            # Check if data already exists
            existing_count = await session.execute(
                select(func.count()).select_from(JobCategory)
            )
            count = existing_count.scalar() or 0

            if count > 0:
                logger.info(f"Job master data already seeded ({count} categories found). Skipping.")
                return

            logger.info("Seeding job master data...")

            # 1. Create categories
            category_map = {}  # slug -> JobCategory instance
            for cat_data in CATEGORIES:
                category = JobCategory(**cat_data)
                session.add(category)
                await session.flush()
                category_map[cat_data["slug"]] = category
                logger.info(f"  Created category: {cat_data['name']}")

            # 2. Create roles and link to categories
            role_map = {}  # slug -> JobRole instance
            for role_data in ROLES:
                category_slugs = role_data.pop("categories")

                # Convert suggested_skills list to JSON-compatible format
                if "suggested_skills" in role_data and isinstance(role_data["suggested_skills"], list):
                    role_data["suggested_skills"] = role_data["suggested_skills"]

                role = JobRole(**role_data)
                session.add(role)
                await session.flush()

                # Link to categories
                for cat_slug in category_slugs:
                    if cat_slug in category_map:
                        await session.execute(
                            job_category_role_association.insert().values(
                                category_id=category_map[cat_slug].id,
                                role_id=role.id,
                            )
                        )

                role_map[role_data["slug"]] = role
                logger.info(f"  Created role: {role_data['name']} ({role_data['job_type']})")

            # 3. Create question templates
            for role_slug, templates in QUESTION_TEMPLATES.items():
                if role_slug not in role_map:
                    logger.warning(f"  Role '{role_slug}' not found in role_map. Skipping templates.")
                    continue

                role = role_map[role_slug]
                for tmpl_data in templates:
                    template = RoleQuestionTemplate(
                        role_id=role.id,
                        **tmpl_data,
                    )
                    session.add(template)

                logger.info(f"  Created {len(templates)} question templates for: {role_slug}")

            await session.commit()
            logger.info("Job master data seeded successfully!")

        except Exception as e:
            await session.rollback()
            logger.error(f"Failed to seed job master data: {e}")
            raise


async def add_backend_developer_templates_if_missing() -> None:
    """
    Add question templates for Backend Developer role if the role exists but has no templates.
    Use this when the DB was already seeded before backend-developer templates were added.
    """
    async with async_session_factory() as session:
        try:
            # Find Backend Developer role by slug
            result = await session.execute(
                select(JobRole).where(JobRole.slug == "backend-developer")
            )
            role = result.scalar_one_or_none()
            if not role:
                logger.info("Backend Developer role not found. Run full seed first.")
                return

            # Check if it already has templates
            count_result = await session.execute(
                select(func.count()).select_from(RoleQuestionTemplate).where(
                    RoleQuestionTemplate.role_id == role.id
                )
            )
            if (count_result.scalar() or 0) > 0:
                logger.info("Backend Developer already has question templates. Skipping.")
                return

            templates = QUESTION_TEMPLATES.get("backend-developer", [])
            if not templates:
                logger.warning("No backend-developer templates defined in QUESTION_TEMPLATES.")
                return

            for tmpl_data in templates:
                template = RoleQuestionTemplate(role_id=role.id, **tmpl_data)
                session.add(template)
            await session.commit()
            logger.info(f"Added {len(templates)} question templates for Backend Developer.")
        except Exception as e:
            await session.rollback()
            logger.error(f"Failed to add Backend Developer templates: {e}")
            raise


# Allow running directly
if __name__ == "__main__":
    async def main() -> None:
        await seed_job_master_data()
        # Add backend-developer templates if DB was already seeded without them (single event loop)
        await add_backend_developer_templates_if_missing()

    setup_logging()
    asyncio.run(main())
