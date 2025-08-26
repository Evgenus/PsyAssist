"""
Hotline router tool for PsyAssist AI.
"""

import asyncio
import aiohttp
from typing import List, Dict, Any, Optional
from datetime import datetime
from abc import ABC, abstractmethod

from ..schemas.resources import Resource, ResourceType, ResourceCategory, Availability
from ..config.settings import settings


class BaseHotlineRouter(ABC):
    """Abstract base class for hotline routers."""
    
    @abstractmethod
    async def find_hotlines(self, location: str, categories: List[str] = None) -> List[Resource]:
        """Find available hotlines for given location and categories."""
        pass
    
    @abstractmethod
    async def get_emergency_number(self, location: str) -> str:
        """Get emergency number for given location."""
        pass
    
    @abstractmethod
    async def check_availability(self, resource: Resource) -> Availability:
        """Check availability of a specific resource."""
        pass


class MockHotlineRouter(BaseHotlineRouter):
    """Mock hotline router for testing and development."""
    
    def __init__(self):
        self.mock_hotlines = self._create_mock_hotlines()
        self.emergency_numbers = {
            'US': '911',
            'CA': '911',
            'UK': '999',
            'AU': '000',
            'default': '911'
        }
    
    def _create_mock_hotlines(self) -> Dict[str, List[Resource]]:
        """Create mock hotline data."""
        from ..schemas.resources import ContactMethod
        
        return {
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
                    availability=Availability.AVAILABLE,
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
                    availability=Availability.AVAILABLE,
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
                    availability=Availability.AVAILABLE,
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
                    availability=Availability.AVAILABLE,
                    verified=True
                )
            ]
        }
    
    async def find_hotlines(self, location: str, categories: List[str] = None) -> List[Resource]:
        """Find available hotlines for given location and categories."""
        # Normalize location
        location = location.upper()
        if location not in self.mock_hotlines:
            location = 'US'  # Default to US
        
        hotlines = self.mock_hotlines[location]
        
        # Filter by categories if specified
        if categories:
            filtered_hotlines = []
            for hotline in hotlines:
                if hotline.category.value in categories:
                    filtered_hotlines.append(hotline)
            return filtered_hotlines
        
        return hotlines
    
    async def get_emergency_number(self, location: str) -> str:
        """Get emergency number for given location."""
        location = location.upper()
        return self.emergency_numbers.get(location, self.emergency_numbers['default'])
    
    async def check_availability(self, resource: Resource) -> Availability:
        """Check availability of a specific resource."""
        # Mock availability check - in real implementation, this would call the service
        if resource.resource_id in ["crisis_text_line", "national_suicide_prevention"]:
            return Availability.AVAILABLE
        elif resource.resource_id == "domestic_violence_hotline":
            # Simulate occasional busy status
            import random
            return Availability.BUSY if random.random() < 0.1 else Availability.AVAILABLE
        else:
            return Availability.UNKNOWN


class APIHotlineRouter(BaseHotlineRouter):
    """API-based hotline router for production use."""
    
    def __init__(self, api_url: str = None):
        self.api_url = api_url or settings.hotline_api_url
        if not self.api_url:
            raise ValueError("Hotline API URL is required for APIHotlineRouter")
    
    async def find_hotlines(self, location: str, categories: List[str] = None) -> List[Resource]:
        """Find available hotlines via API."""
        async with aiohttp.ClientSession() as session:
            params = {'location': location}
            if categories:
                params['categories'] = ','.join(categories)
            
            try:
                async with session.get(f"{self.api_url}/hotlines", params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return [Resource(**hotline_data) for hotline_data in data]
                    else:
                        # Fallback to mock data if API fails
                        mock_router = MockHotlineRouter()
                        return await mock_router.find_hotlines(location, categories)
            except Exception as e:
                # Fallback to mock data on error
                mock_router = MockHotlineRouter()
                return await mock_router.find_hotlines(location, categories)
    
    async def get_emergency_number(self, location: str) -> str:
        """Get emergency number via API."""
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(f"{self.api_url}/emergency", params={'location': location}) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('number', '911')
                    else:
                        # Fallback
                        mock_router = MockHotlineRouter()
                        return await mock_router.get_emergency_number(location)
            except Exception as e:
                # Fallback
                mock_router = MockHotlineRouter()
                return await mock_router.get_emergency_number(location)
    
    async def check_availability(self, resource: Resource) -> Availability:
        """Check availability via API."""
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(f"{self.api_url}/availability/{resource.resource_id}") as response:
                    if response.status == 200:
                        data = await response.json()
                        return Availability(data.get('status', 'UNKNOWN'))
                    else:
                        return Availability.UNKNOWN
            except Exception as e:
                return Availability.UNKNOWN


class HotlineRouter:
    """Main hotline router interface."""
    
    def __init__(self, router_type: str = "mock"):
        self.router_type = router_type
        
        if router_type == "mock":
            self.router = MockHotlineRouter()
        elif router_type == "api":
            self.router = APIHotlineRouter()
        else:
            raise ValueError(f"Unknown router type: {router_type}")
    
    async def find_hotlines(self, location: str, categories: List[str] = None) -> List[Resource]:
        """Find available hotlines."""
        return await self.router.find_hotlines(location, categories)
    
    async def get_emergency_number(self, location: str) -> str:
        """Get emergency number."""
        return await self.router.get_emergency_number(location)
    
    async def check_availability(self, resource: Resource) -> Availability:
        """Check resource availability."""
        return await self.router.check_availability(resource)
    
    async def get_crisis_resources(self, location: str) -> List[Resource]:
        """Get crisis-specific resources."""
        crisis_categories = [
            ResourceCategory.SUICIDE_PREVENTION.value,
            ResourceCategory.CRISIS_INTERVENTION.value
        ]
        return await self.find_hotlines(location, crisis_categories)
    
    async def get_specialized_resources(self, location: str, category: str) -> List[Resource]:
        """Get resources for a specific category."""
        return await self.find_hotlines(location, [category])
    
    async def get_all_resources(self, location: str) -> List[Resource]:
        """Get all available resources for a location."""
        return await self.find_hotlines(location)
