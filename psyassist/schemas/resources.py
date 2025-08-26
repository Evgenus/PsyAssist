"""
Resource schemas for PsyAssist AI support system.
"""

from enum import Enum
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field, validator


class ResourceType(str, Enum):
    """Types of support resources."""
    HOTLINE = "HOTLINE"
    CRISIS_LINE = "CRISIS_LINE"
    EMERGENCY = "EMERGENCY"
    INFORMATION = "INFORMATION"
    REFERRAL = "REFERRAL"
    SELF_HELP = "SELF_HELP"
    COMMUNITY = "COMMUNITY"


class ResourceCategory(str, Enum):
    """Categories of resources."""
    SUICIDE_PREVENTION = "SUICIDE_PREVENTION"
    MENTAL_HEALTH = "MENTAL_HEALTH"
    DOMESTIC_VIOLENCE = "DOMESTIC_VIOLENCE"
    SUBSTANCE_ABUSE = "SUBSTANCE_ABUSE"
    CRISIS_INTERVENTION = "CRISIS_INTERVENTION"
    GENERAL_SUPPORT = "GENERAL_SUPPORT"


class Availability(str, Enum):
    """Resource availability status."""
    AVAILABLE = "AVAILABLE"
    BUSY = "BUSY"
    UNAVAILABLE = "UNAVAILABLE"
    UNKNOWN = "UNKNOWN"


class ContactMethod(str, Enum):
    """Methods of contacting a resource."""
    PHONE = "PHONE"
    TEXT = "TEXT"
    CHAT = "CHAT"
    EMAIL = "EMAIL"
    WEBSITE = "WEBSITE"
    IN_PERSON = "IN_PERSON"


class Resource(BaseModel):
    """Support resource information."""
    resource_id: str = Field(..., description="Unique resource identifier")
    name: str = Field(..., description="Resource name")
    type: ResourceType = Field(..., description="Type of resource")
    category: ResourceCategory = Field(..., description="Resource category")
    
    # Contact information
    contact_methods: List[ContactMethod] = Field(..., description="Available contact methods")
    phone_number: Optional[str] = Field(None, description="Phone number if available")
    text_number: Optional[str] = Field(None, description="Text/SMS number if available")
    website: Optional[str] = Field(None, description="Website URL if available")
    email: Optional[str] = Field(None, description="Email address if available")
    
    # Service details
    description: str = Field(..., description="Resource description")
    hours: Optional[str] = Field(None, description="Operating hours")
    languages: List[str] = Field(default_factory=lambda: ["English"], description="Supported languages")
    cost: Optional[str] = Field(None, description="Cost information (e.g., 'Free', '$20/session')")
    
    # Geographic and demographic targeting
    regions: List[str] = Field(default_factory=list, description="Served regions")
    age_groups: List[str] = Field(default_factory=list, description="Target age groups")
    specializations: List[str] = Field(default_factory=list, description="Specialized services")
    
    # Status and availability
    availability: Availability = Field(Availability.UNKNOWN, description="Current availability")
    response_time: Optional[str] = Field(None, description="Typical response time")
    verified: bool = Field(False, description="Whether resource has been verified")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow, description="When resource was added")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update time")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    @validator('phone_number', 'text_number')
    def validate_phone_format(cls, v):
        if v is not None:
            # Basic phone number validation
            import re
            phone_pattern = r'^\+?[\d\s\-\(\)]+$'
            if not re.match(phone_pattern, v):
                raise ValueError("Invalid phone number format")
        return v


class ResourceBundle(BaseModel):
    """Collection of resources for a specific situation."""
    bundle_id: str = Field(..., description="Unique bundle identifier")
    name: str = Field(..., description="Bundle name")
    description: str = Field(..., description="Bundle description")
    
    # Resources in this bundle
    resources: List[Resource] = Field(..., description="Resources in the bundle")
    priority_order: List[str] = Field(default_factory=list, description="Resource priority order by ID")
    
    # Bundle targeting
    risk_levels: List[str] = Field(default_factory=list, description="Target risk levels")
    categories: List[ResourceCategory] = Field(default_factory=list, description="Target categories")
    regions: List[str] = Field(default_factory=list, description="Target regions")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Bundle creation time")
    active: bool = Field(True, description="Whether bundle is active")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    @validator('resources')
    def validate_resources(cls, v):
        if not v:
            raise ValueError("Resource bundle must contain at least one resource")
        return v


class EscalationPlan(BaseModel):
    """Plan for escalating a user to human support."""
    plan_id: str = Field(..., description="Unique plan identifier")
    session_id: str = Field(..., description="Associated session ID")
    
    # Escalation details
    escalation_type: str = Field(..., description="Type of escalation")
    urgency_level: str = Field(..., description="Urgency level")
    reason: str = Field(..., description="Reason for escalation")
    
    # Target resources
    primary_resource: Resource = Field(..., description="Primary resource for escalation")
    backup_resources: List[Resource] = Field(default_factory=list, description="Backup resources")
    
    # Contact information
    user_contact_info: Optional[str] = Field(None, description="User contact information if available")
    emergency_contact: Optional[str] = Field(None, description="Emergency contact information")
    
    # Plan status
    status: str = Field("PENDING", description="Escalation status")
    initiated_at: datetime = Field(default_factory=datetime.utcnow, description="When escalation was initiated")
    completed_at: Optional[datetime] = Field(None, description="When escalation was completed")
    
    # Instructions
    instructions: List[str] = Field(default_factory=list, description="Instructions for escalation")
    safety_notes: Optional[str] = Field(None, description="Safety-related notes")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ResourceDirectory(BaseModel):
    """Directory of available resources."""
    directory_id: str = Field(..., description="Unique directory identifier")
    name: str = Field(..., description="Directory name")
    version: str = Field(..., description="Directory version")
    
    # Resources
    resources: List[Resource] = Field(..., description="All available resources")
    bundles: List[ResourceBundle] = Field(default_factory=list, description="Resource bundles")
    
    # Directory metadata
    last_updated: datetime = Field(default_factory=datetime.utcnow, description="Last update time")
    source: str = Field(..., description="Data source")
    coverage_regions: List[str] = Field(default_factory=list, description="Covered regions")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
