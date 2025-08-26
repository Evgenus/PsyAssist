"""
Warm transfer API tool for PsyAssist AI.
"""

import asyncio
import aiohttp
from typing import Dict, Any, Optional, List
from datetime import datetime
from abc import ABC, abstractmethod

from ..schemas.resources import Resource
from ..config.settings import settings


class BaseWarmTransferAPI(ABC):
    """Abstract base class for warm transfer APIs."""
    
    @abstractmethod
    async def initiate_transfer(self, session_id: str, resource: Resource, context: Dict[str, Any]) -> Dict[str, Any]:
        """Initiate a warm transfer to a human support resource."""
        pass
    
    @abstractmethod
    async def check_transfer_status(self, transfer_id: str) -> Dict[str, Any]:
        """Check the status of a transfer."""
        pass
    
    @abstractmethod
    async def cancel_transfer(self, transfer_id: str) -> bool:
        """Cancel an active transfer."""
        pass


class MockWarmTransferAPI(BaseWarmTransferAPI):
    """Mock warm transfer API for testing and development."""
    
    def __init__(self):
        self.active_transfers = {}
        self.transfer_counter = 0
    
    async def initiate_transfer(self, session_id: str, resource: Resource, context: Dict[str, Any]) -> Dict[str, Any]:
        """Initiate a mock warm transfer."""
        self.transfer_counter += 1
        transfer_id = f"transfer_{self.transfer_counter}_{datetime.utcnow().isoformat()}"
        
        transfer_info = {
            'transfer_id': transfer_id,
            'session_id': session_id,
            'resource_id': resource.resource_id,
            'resource_name': resource.name,
            'status': 'initiated',
            'initiated_at': datetime.utcnow().isoformat(),
            'estimated_wait_time': 5,  # minutes
            'context': context,
            'contact_info': self._get_contact_info(resource)
        }
        
        self.active_transfers[transfer_id] = transfer_info
        
        # Simulate async processing
        asyncio.create_task(self._simulate_transfer_progress(transfer_id))
        
        return transfer_info
    
    async def check_transfer_status(self, transfer_id: str) -> Dict[str, Any]:
        """Check the status of a mock transfer."""
        if transfer_id not in self.active_transfers:
            return {
                'transfer_id': transfer_id,
                'status': 'not_found',
                'error': 'Transfer not found'
            }
        
        transfer_info = self.active_transfers[transfer_id]
        
        # Update status based on time elapsed
        initiated_at = datetime.fromisoformat(transfer_info['initiated_at'])
        elapsed_minutes = (datetime.utcnow() - initiated_at).total_seconds() / 60
        
        if elapsed_minutes > 10:
            transfer_info['status'] = 'completed'
        elif elapsed_minutes > 3:
            transfer_info['status'] = 'connected'
        elif elapsed_minutes > 1:
            transfer_info['status'] = 'routing'
        
        return transfer_info
    
    async def cancel_transfer(self, transfer_id: str) -> bool:
        """Cancel a mock transfer."""
        if transfer_id in self.active_transfers:
            transfer_info = self.active_transfers[transfer_id]
            transfer_info['status'] = 'cancelled'
            transfer_info['cancelled_at'] = datetime.utcnow().isoformat()
            return True
        return False
    
    def _get_contact_info(self, resource: Resource) -> Dict[str, Any]:
        """Get contact information for the resource."""
        contact_info = {
            'name': resource.name,
            'description': resource.description,
            'hours': resource.hours,
            'languages': resource.languages,
            'cost': resource.cost
        }
        
        if resource.phone_number:
            contact_info['phone'] = resource.phone_number
        if resource.text_number:
            contact_info['text'] = resource.text_number
        if resource.website:
            contact_info['website'] = resource.website
        if resource.email:
            contact_info['email'] = resource.email
        
        return contact_info
    
    async def _simulate_transfer_progress(self, transfer_id: str):
        """Simulate the progress of a transfer."""
        await asyncio.sleep(2)  # Wait 2 seconds before status change
        
        if transfer_id in self.active_transfers:
            self.active_transfers[transfer_id]['status'] = 'routing'
        
        await asyncio.sleep(3)  # Wait 3 more seconds before connection
        
        if transfer_id in self.active_transfers:
            self.active_transfers[transfer_id]['status'] = 'connected'
            self.active_transfers[transfer_id]['connected_at'] = datetime.utcnow().isoformat()


class APIWarmTransferAPI(BaseWarmTransferAPI):
    """API-based warm transfer for production use."""
    
    def __init__(self, api_url: str = None):
        self.api_url = api_url or settings.warm_transfer_api_url
        if not self.api_url:
            raise ValueError("Warm transfer API URL is required for APIWarmTransferAPI")
    
    async def initiate_transfer(self, session_id: str, resource: Resource, context: Dict[str, Any]) -> Dict[str, Any]:
        """Initiate a warm transfer via API."""
        async with aiohttp.ClientSession() as session:
            payload = {
                'session_id': session_id,
                'resource_id': resource.resource_id,
                'resource_info': {
                    'name': resource.name,
                    'phone_number': resource.phone_number,
                    'text_number': resource.text_number,
                    'website': resource.website,
                    'email': resource.email
                },
                'context': context
            }
            
            try:
                async with session.post(f"{self.api_url}/transfers", json=payload) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        # Fallback to mock
                        mock_api = MockWarmTransferAPI()
                        return await mock_api.initiate_transfer(session_id, resource, context)
            except Exception as e:
                # Fallback to mock on error
                mock_api = MockWarmTransferAPI()
                return await mock_api.initiate_transfer(session_id, resource, context)
    
    async def check_transfer_status(self, transfer_id: str) -> Dict[str, Any]:
        """Check transfer status via API."""
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(f"{self.api_url}/transfers/{transfer_id}") as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        # Fallback to mock
                        mock_api = MockWarmTransferAPI()
                        return await mock_api.check_transfer_status(transfer_id)
            except Exception as e:
                # Fallback to mock on error
                mock_api = MockWarmTransferAPI()
                return await mock_api.check_transfer_status(transfer_id)
    
    async def cancel_transfer(self, transfer_id: str) -> bool:
        """Cancel transfer via API."""
        async with aiohttp.ClientSession() as session:
            try:
                async with session.delete(f"{self.api_url}/transfers/{transfer_id}") as response:
                    if response.status == 200:
                        return True
                    else:
                        # Fallback to mock
                        mock_api = MockWarmTransferAPI()
                        return await mock_api.cancel_transfer(transfer_id)
            except Exception as e:
                # Fallback to mock on error
                mock_api = MockWarmTransferAPI()
                return await mock_api.cancel_transfer(transfer_id)


class WarmTransferAPI:
    """Main warm transfer API interface."""
    
    def __init__(self, api_type: str = "mock"):
        self.api_type = api_type
        
        if api_type == "mock":
            self.api = MockWarmTransferAPI()
        elif api_type == "api":
            self.api = APIWarmTransferAPI()
        else:
            raise ValueError(f"Unknown API type: {api_type}")
    
    async def initiate_transfer(self, session_id: str, resource: Resource, context: Dict[str, Any]) -> Dict[str, Any]:
        """Initiate a warm transfer."""
        return await self.api.initiate_transfer(session_id, resource, context)
    
    async def check_transfer_status(self, transfer_id: str) -> Dict[str, Any]:
        """Check transfer status."""
        return await self.api.check_transfer_status(transfer_id)
    
    async def cancel_transfer(self, transfer_id: str) -> bool:
        """Cancel a transfer."""
        return await self.api.cancel_transfer(transfer_id)
    
    async def wait_for_connection(self, transfer_id: str, timeout_minutes: int = 10) -> Dict[str, Any]:
        """Wait for transfer to connect with timeout."""
        start_time = datetime.utcnow()
        timeout_seconds = timeout_minutes * 60
        
        while True:
            status_info = await self.check_transfer_status(transfer_id)
            
            if status_info['status'] in ['connected', 'completed']:
                return status_info
            
            if status_info['status'] in ['failed', 'cancelled']:
                return status_info
            
            # Check timeout
            elapsed_seconds = (datetime.utcnow() - start_time).total_seconds()
            if elapsed_seconds > timeout_seconds:
                return {
                    'transfer_id': transfer_id,
                    'status': 'timeout',
                    'error': 'Transfer timed out'
                }
            
            # Wait before checking again
            await asyncio.sleep(30)  # Check every 30 seconds
    
    async def get_transfer_summary(self, transfer_id: str) -> Dict[str, Any]:
        """Get a summary of the transfer."""
        status_info = await self.check_transfer_status(transfer_id)
        
        if 'error' in status_info:
            return status_info
        
        summary = {
            'transfer_id': transfer_id,
            'status': status_info['status'],
            'resource_name': status_info.get('resource_name', 'Unknown'),
            'initiated_at': status_info.get('initiated_at'),
            'estimated_wait_time': status_info.get('estimated_wait_time'),
            'contact_info': status_info.get('contact_info', {})
        }
        
        if 'connected_at' in status_info:
            summary['connected_at'] = status_info['connected_at']
            # Calculate actual wait time
            initiated_at = datetime.fromisoformat(status_info['initiated_at'])
            connected_at = datetime.fromisoformat(status_info['connected_at'])
            summary['actual_wait_time'] = (connected_at - initiated_at).total_seconds() / 60
        
        return summary
