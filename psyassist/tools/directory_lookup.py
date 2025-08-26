"""
Directory lookup tool for PsyAssist AI.
"""

import asyncio
import aiohttp
from typing import List, Dict, Any, Optional
from datetime import datetime
from abc import ABC, abstractmethod

from ..schemas.resources import Resource, ResourceDirectory, ResourceBundle, ResourceCategory
from ..config.settings import settings


class BaseDirectoryLookup(ABC):
    """Abstract base class for directory lookups."""
    
    @abstractmethod
    async def get_resources(self, location: str, categories: List[str] = None) -> List[Resource]:
        """Get resources for a specific location and categories."""
        pass
    
    @abstractmethod
    async def get_resource_bundles(self, location: str, risk_level: str = None) -> List[ResourceBundle]:
        """Get resource bundles for a location and risk level."""
        pass
    
    @abstractmethod
    async def search_resources(self, query: str, location: str = None) -> List[Resource]:
        """Search resources by query."""
        pass


class MockDirectoryLookup(BaseDirectoryLookup):
    """Mock directory lookup for testing and development."""
    
    def __init__(self):
        self.directories = self._create_mock_directories()
    
    def _create_mock_directories(self) -> Dict[str, ResourceDirectory]:
        """Create mock directory data."""
        from ..schemas.resources import ContactMethod, ResourceType
        
        # Create mock resources
        resources = {
            'US': [
                Resource(
                    resource_id="crisis_text_line",
                    name="Crisis Text Line",
                    type=ResourceType.CRISIS_LINE,
                    category=ResourceCategory.SUICIDE_PREVENTION,
                    contact_methods=[ContactMethod.TEXT],
                    text_number="988",
                    description="24/7 crisis support via text message",
                    hours="24/7",
                    languages=["English", "Spanish"],
                    cost="Free",
                    regions=["US"],
                    verified=True
                ),
                Resource(
                    resource_id="national_suicide_prevention",
                    name="National Suicide Prevention Lifeline",
                    type=ResourceType.HOTLINE,
                    category=ResourceCategory.SUICIDE_PREVENTION,
                    contact_methods=[ContactMethod.PHONE],
                    phone_number="988",
                    description="24/7 suicide prevention and crisis support",
                    hours="24/7",
                    languages=["English", "Spanish"],
                    cost="Free",
                    regions=["US"],
                    verified=True
                ),
                Resource(
                    resource_id="domestic_violence_hotline",
                    name="National Domestic Violence Hotline",
                    type=ResourceType.HOTLINE,
                    category=ResourceCategory.DOMESTIC_VIOLENCE,
                    contact_methods=[ContactMethod.PHONE, ContactMethod.CHAT],
                    phone_number="1-800-799-7233",
                    website="https://www.thehotline.org",
                    description="24/7 support for domestic violence survivors",
                    hours="24/7",
                    languages=["English", "Spanish"],
                    cost="Free",
                    regions=["US"],
                    verified=True
                ),
                Resource(
                    resource_id="substance_abuse_hotline",
                    name="SAMHSA National Helpline",
                    type=ResourceType.HOTLINE,
                    category=ResourceCategory.SUBSTANCE_ABUSE,
                    contact_methods=[ContactMethod.PHONE],
                    phone_number="1-800-662-4357",
                    description="Treatment referral and information service",
                    hours="24/7",
                    languages=["English", "Spanish"],
                    cost="Free",
                    regions=["US"],
                    verified=True
                ),
                Resource(
                    resource_id="mental_health_info",
                    name="MentalHealth.gov",
                    type=ResourceType.INFORMATION,
                    category=ResourceCategory.MENTAL_HEALTH,
                    contact_methods=[ContactMethod.WEBSITE],
                    website="https://www.mentalhealth.gov",
                    description="Government information and resources on mental health",
                    hours="24/7",
                    languages=["English"],
                    cost="Free",
                    regions=["US"],
                    verified=True
                )
            ],
            'CA': [
                Resource(
                    resource_id="crisis_services_canada",
                    name="Crisis Services Canada",
                    type=ResourceType.CRISIS_LINE,
                    category=ResourceCategory.SUICIDE_PREVENTION,
                    contact_methods=[ContactMethod.PHONE],
                    phone_number="1-833-456-4566",
                    description="24/7 crisis support for Canadians",
                    hours="24/7",
                    languages=["English", "French"],
                    cost="Free",
                    regions=["CA"],
                    verified=True
                ),
                Resource(
                    resource_id="kids_help_phone",
                    name="Kids Help Phone",
                    type=ResourceType.HOTLINE,
                    category=ResourceCategory.MENTAL_HEALTH,
                    contact_methods=[ContactMethod.PHONE, ContactMethod.TEXT],
                    phone_number="1-800-668-6868",
                    text_number="686868",
                    description="24/7 support for young people",
                    hours="24/7",
                    languages=["English", "French"],
                    cost="Free",
                    regions=["CA"],
                    verified=True
                )
            ]
        }
        
        # Create resource bundles
        bundles = {
            'US': [
                ResourceBundle(
                    bundle_id="crisis_support_us",
                    name="Crisis Support Bundle",
                    description="Immediate crisis support resources",
                    resources=[resources['US'][0], resources['US'][1]],  # Crisis Text Line and Suicide Prevention
                    priority_order=["crisis_text_line", "national_suicide_prevention"],
                    risk_levels=["HIGH", "CRITICAL"],
                    categories=[ResourceCategory.SUICIDE_PREVENTION, ResourceCategory.CRISIS_INTERVENTION],
                    regions=["US"]
                ),
                ResourceBundle(
                    bundle_id="domestic_violence_support_us",
                    name="Domestic Violence Support",
                    description="Resources for domestic violence survivors",
                    resources=[resources['US'][2]],  # Domestic Violence Hotline
                    priority_order=["domestic_violence_hotline"],
                    risk_levels=["MEDIUM", "HIGH"],
                    categories=[ResourceCategory.DOMESTIC_VIOLENCE],
                    regions=["US"]
                )
            ],
            'CA': [
                ResourceBundle(
                    bundle_id="crisis_support_ca",
                    name="Canadian Crisis Support",
                    description="Crisis support for Canadians",
                    resources=[resources['CA'][0]],  # Crisis Services Canada
                    priority_order=["crisis_services_canada"],
                    risk_levels=["HIGH", "CRITICAL"],
                    categories=[ResourceCategory.SUICIDE_PREVENTION, ResourceCategory.CRISIS_INTERVENTION],
                    regions=["CA"]
                )
            ]
        }
        
        # Create directories
        directories = {}
        for location in ['US', 'CA']:
            directories[location] = ResourceDirectory(
                directory_id=f"directory_{location.lower()}",
                name=f"Resource Directory - {location}",
                version="1.0",
                resources=resources.get(location, []),
                bundles=bundles.get(location, []),
                source="Mock Directory",
                coverage_regions=[location]
            )
        
        return directories
    
    async def get_resources(self, location: str, categories: List[str] = None) -> List[Resource]:
        """Get resources for a specific location and categories."""
        location = location.upper()
        if location not in self.directories:
            location = 'US'  # Default to US
        
        resources = self.directories[location].resources
        
        # Filter by categories if specified
        if categories:
            filtered_resources = []
            for resource in resources:
                if resource.category.value in categories:
                    filtered_resources.append(resource)
            return filtered_resources
        
        return resources
    
    async def get_resource_bundles(self, location: str, risk_level: str = None) -> List[ResourceBundle]:
        """Get resource bundles for a location and risk level."""
        location = location.upper()
        if location not in self.directories:
            location = 'US'  # Default to US
        
        bundles = self.directories[location].bundles
        
        # Filter by risk level if specified
        if risk_level:
            filtered_bundles = []
            for bundle in bundles:
                if risk_level in bundle.risk_levels:
                    filtered_bundles.append(bundle)
            return filtered_bundles
        
        return bundles
    
    async def search_resources(self, query: str, location: str = None) -> List[Resource]:
        """Search resources by query."""
        query_lower = query.lower()
        results = []
        
        # Search in specified location or all locations
        locations = [location.upper()] if location else ['US', 'CA']
        
        for loc in locations:
            if loc in self.directories:
                for resource in self.directories[loc].resources:
                    # Search in name, description, and specializations
                    searchable_text = f"{resource.name} {resource.description} {' '.join(resource.specializations)}".lower()
                    if query_lower in searchable_text:
                        results.append(resource)
        
        return results


class APIDirectoryLookup(BaseDirectoryLookup):
    """API-based directory lookup for production use."""
    
    def __init__(self, api_url: str = None):
        self.api_url = api_url or settings.directory_api_url
        if not self.api_url:
            raise ValueError("Directory API URL is required for APIDirectoryLookup")
    
    async def get_resources(self, location: str, categories: List[str] = None) -> List[Resource]:
        """Get resources via API."""
        async with aiohttp.ClientSession() as session:
            params = {'location': location}
            if categories:
                params['categories'] = ','.join(categories)
            
            try:
                async with session.get(f"{self.api_url}/resources", params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return [Resource(**resource_data) for resource_data in data]
                    else:
                        # Fallback to mock
                        mock_lookup = MockDirectoryLookup()
                        return await mock_lookup.get_resources(location, categories)
            except Exception as e:
                # Fallback to mock on error
                mock_lookup = MockDirectoryLookup()
                return await mock_lookup.get_resources(location, categories)
    
    async def get_resource_bundles(self, location: str, risk_level: str = None) -> List[ResourceBundle]:
        """Get resource bundles via API."""
        async with aiohttp.ClientSession() as session:
            params = {'location': location}
            if risk_level:
                params['risk_level'] = risk_level
            
            try:
                async with session.get(f"{self.api_url}/bundles", params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return [ResourceBundle(**bundle_data) for bundle_data in data]
                    else:
                        # Fallback to mock
                        mock_lookup = MockDirectoryLookup()
                        return await mock_lookup.get_resource_bundles(location, risk_level)
            except Exception as e:
                # Fallback to mock on error
                mock_lookup = MockDirectoryLookup()
                return await mock_lookup.get_resource_bundles(location, risk_level)
    
    async def search_resources(self, query: str, location: str = None) -> List[Resource]:
        """Search resources via API."""
        async with aiohttp.ClientSession() as session:
            params = {'query': query}
            if location:
                params['location'] = location
            
            try:
                async with session.get(f"{self.api_url}/search", params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return [Resource(**resource_data) for resource_data in data]
                    else:
                        # Fallback to mock
                        mock_lookup = MockDirectoryLookup()
                        return await mock_lookup.search_resources(query, location)
            except Exception as e:
                # Fallback to mock on error
                mock_lookup = MockDirectoryLookup()
                return await mock_lookup.search_resources(query, location)


class DirectoryLookup:
    """Main directory lookup interface."""
    
    def __init__(self, lookup_type: str = "mock"):
        self.lookup_type = lookup_type
        
        if lookup_type == "mock":
            self.lookup = MockDirectoryLookup()
        elif lookup_type == "api":
            self.lookup = APIDirectoryLookup()
        else:
            raise ValueError(f"Unknown lookup type: {lookup_type}")
    
    async def get_resources(self, location: str, categories: List[str] = None) -> List[Resource]:
        """Get resources for a location."""
        return await self.lookup.get_resources(location, categories)
    
    async def get_resource_bundles(self, location: str, risk_level: str = None) -> List[ResourceBundle]:
        """Get resource bundles for a location."""
        return await self.lookup.get_resource_bundles(location, risk_level)
    
    async def search_resources(self, query: str, location: str = None) -> List[Resource]:
        """Search resources by query."""
        return await self.lookup.search_resources(query, location)
    
    async def get_crisis_resources(self, location: str) -> List[Resource]:
        """Get crisis-specific resources."""
        crisis_categories = [
            ResourceCategory.SUICIDE_PREVENTION.value,
            ResourceCategory.CRISIS_INTERVENTION.value
        ]
        return await self.get_resources(location, crisis_categories)
    
    async def get_mental_health_resources(self, location: str) -> List[Resource]:
        """Get mental health resources."""
        return await self.get_resources(location, [ResourceCategory.MENTAL_HEALTH.value])
    
    async def get_specialized_resources(self, location: str, category: str) -> List[Resource]:
        """Get resources for a specific category."""
        return await self.get_resources(location, [category])
    
    async def get_emergency_bundle(self, location: str) -> Optional[ResourceBundle]:
        """Get emergency resource bundle for a location."""
        bundles = await self.get_resource_bundles(location, "CRITICAL")
        if bundles:
            return bundles[0]  # Return first emergency bundle
        return None
