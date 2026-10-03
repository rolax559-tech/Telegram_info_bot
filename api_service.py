import aiohttp
import asyncio
from config import USERS_LOOKUP_API_BASE_URL, USERS_LOOKUP_API_KEY
from datetime import datetime
import uuid

class UsersLookupAPI:
    """Modular API service for Users Lookup API integration."""
    
    def __init__(self):
        self.base_url = USERS_LOOKUP_API_BASE_URL
        self.api_key = USERS_LOOKUP_API_KEY
        self.timeout = aiohttp.ClientTimeout(total=30)
    
    def _get_headers(self):
        """Return auth headers."""
        return {
            "X-API-Key": self.api_key,
            "User-Agent": "TelegramBot/1.0"
        }
    
    async def health_check(self):
        """Check API health. GET /"""
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(
                    f"{self.base_url}/",
                    headers=self._get_headers()
                ) as resp:
                    if resp.status == 200:
                        return True, "OK"
                    return False, f"Status {resp.status}"
        except asyncio.TimeoutError:
            return False, "Timeout"
        except Exception as e:
            return False, str(e)
    
    async def mobile_lookup(self, mobile_number):
        """
        Mobile/Number Lookup. GET /user/{mobile}
        
        Returns:
        {
            "success": bool,
            "error": str or None,
            "search_id": str (unique identifier),
            "data": {
                "mobile": str,
                "name": str,
                "fname": str,
                "address": str,
                "alt": str,
                "circle": str,
                "id": str,
                "count": int,
                "results": [...]
            }
        }
        """
        try:
            # Validate input
            mobile = str(mobile_number).strip()
            if not mobile.isdigit() or len(mobile) < 10:
                return {
                    "success": False,
                    "error": "Invalid mobile number (min 10 digits)",
                    "search_id": None,
                    "data": None
                }
            
            search_id = str(uuid.uuid4())
            
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(
                    f"{self.base_url}/user/{mobile}",
                    headers=self._get_headers()
                ) as resp:
                    
                    if resp.status == 200:
                        data = await resp.json()
                        return {
                            "success": True,
                            "error": None,
                            "search_id": search_id,
                            "data": data
                        }
                    elif resp.status == 400:
                        return {
                            "success": False,
                            "error": "Bad request",
                            "search_id": search_id,
                            "data": None
                        }
                    elif resp.status == 401:
                        return {
                            "success": False,
                            "error": "Unauthorized - invalid API key",
                            "search_id": search_id,
                            "data": None
                        }
                    elif resp.status == 404:
                        return {
                            "success": False,
                            "error": "No records found",
                            "search_id": search_id,
                            "data": None
                        }
                    elif resp.status == 422:
                        return {
                            "success": False,
                            "error": "Validation error",
                            "search_id": search_id,
                            "data": None
                        }
                    elif resp.status == 503:
                        return {
                            "success": False,
                            "error": "Service unavailable",
                            "search_id": search_id,
                            "data": None
                        }
                    else:
                        return {
                            "success": False,
                            "error": f"HTTP {resp.status}",
                            "search_id": search_id,
                            "data": None
                        }
        
        except asyncio.TimeoutError:
            return {
                "success": False,
                "error": "Request timeout",
                "search_id": None,
                "data": None
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Error: {str(e)}",
                "search_id": None,
                "data": None
            }
    
    async def id_search(self, record_id):
        """
        ID Search. GET /id/{record_id}
        
        Returns same structure as mobile_lookup.
        """
        try:
            record_id = str(record_id).strip()
            if not record_id:
                return {
                    "success": False,
                    "error": "Invalid record ID",
                    "search_id": None,
                    "data": None
                }
            
            search_id = str(uuid.uuid4())
            
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(
                    f"{self.base_url}/id/{record_id}",
                    headers=self._get_headers()
                ) as resp:
                    
                    if resp.status == 200:
                        data = await resp.json()
                        return {
                            "success": True,
                            "error": None,
                            "search_id": search_id,
                            "data": data
                        }
                    elif resp.status == 404:
                        return {
                            "success": False,
                            "error": "ID not found",
                            "search_id": search_id,
                            "data": None
                        }
                    elif resp.status == 401:
                        return {
                            "success": False,
                            "error": "Unauthorized",
                            "search_id": search_id,
                            "data": None
                        }
                    elif resp.status == 503:
                        return {
                            "success": False,
                            "error": "Service unavailable",
                            "search_id": search_id,
                            "data": None
                        }
                    else:
                        return {
                            "success": False,
                            "error": f"HTTP {resp.status}",
                            "search_id": search_id,
                            "data": None
                        }
        
        except asyncio.TimeoutError:
            return {
                "success": False,
                "error": "Request timeout",
                "search_id": None,
                "data": None
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Error: {str(e)}",
                "search_id": None,
                "data": None
            }
    
    async def get_stats(self):
        """Get API stats. GET /stats. May be slow."""
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=60)) as session:
                async with session.get(
                    f"{self.base_url}/stats",
                    headers=self._get_headers()
                ) as resp:
                    if resp.status == 200:
                        return True, await resp.json()
                    return False, f"Status {resp.status}"
        except asyncio.TimeoutError:
            return False, "Timeout"
        except Exception as e:
            return False, str(e)
