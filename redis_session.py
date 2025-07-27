"""
Redis-based Session implementation for OpenAI Agents SDK
"""
import json
import os
from typing import List, Dict, Any, Optional, TYPE_CHECKING
import redis.asyncio as redis
from dotenv import load_dotenv

# TResponseInputItemは実行時には単なるdictなので、型エイリアスとして定義
if TYPE_CHECKING:
    from agents.items import TResponseInputItem
else:
    TResponseInputItem = Dict[str, Any]

load_dotenv()


class RedisSession:
    """Redis-backed session storage for OpenAI Agents"""
    
    def __init__(self, session_id: str, redis_url: Optional[str] = None):
        """
        Initialize Redis session
        
        Args:
            session_id: Unique identifier for the session
            redis_url: Redis connection URL (defaults to REDIS_URL env var)
        """
        self.session_id = session_id
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379")
        self._client: Optional[redis.Redis] = None
        self._key = f"openai_agent_session:{session_id}"
        
    async def _get_client(self) -> redis.Redis:
        """Get or create Redis client"""
        if self._client is None:
            self._client = await redis.from_url(
                self.redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
        return self._client
    
    async def get_items(self, limit: Optional[int] = None) -> List[TResponseInputItem]:
        """
        Retrieve conversation items from Redis
        
        Args:
            limit: Maximum number of items to retrieve (None for all)
            
        Returns:
            List of conversation items
        """
        client = await self._get_client()
        
        # Get all items from the list
        if limit is None:
            items = await client.lrange(self._key, 0, -1)
        else:
            # Get the most recent 'limit' items
            items = await client.lrange(self._key, -limit, -1)
        
        # Parse JSON strings back to dictionaries
        return [json.loads(item) for item in items]
    
    async def add_items(self, items: List[TResponseInputItem]) -> None:
        """
        Add conversation items to Redis
        
        Args:
            items: List of conversation items to add
        """
        if not items:
            return
            
        client = await self._get_client()
        
        # Convert items to JSON strings
        json_items = [json.dumps(item, ensure_ascii=False) for item in items]
        
        # Add all items to the end of the list
        await client.rpush(self._key, *json_items)
        
        # Set expiration (7 days by default)
        ttl_seconds = int(os.getenv("REDIS_SESSION_TTL", "604800"))  # 7 days
        await client.expire(self._key, ttl_seconds)
    
    async def pop_item(self) -> Optional[TResponseInputItem]:
        """
        Remove and return the most recent conversation item
        
        Returns:
            The most recent item or None if empty
        """
        client = await self._get_client()
        
        # Pop from the right (most recent)
        item = await client.rpop(self._key)
        
        if item:
            return json.loads(item)
        return None
    
    async def clear_session(self) -> None:
        """Remove all items from the session"""
        client = await self._get_client()
        await client.delete(self._key)
    
    async def close(self) -> None:
        """Close Redis connection"""
        if self._client:
            await self._client.close()
            self._client = None
    
    async def exists(self) -> bool:
        """Check if session exists in Redis"""
        client = await self._get_client()
        return await client.exists(self._key) > 0
    
    async def get_session_info(self) -> Dict[str, Any]:
        """Get session metadata"""
        client = await self._get_client()
        
        # Get session length and TTL
        length = await client.llen(self._key)
        ttl = await client.ttl(self._key)
        
        return {
            "session_id": self.session_id,
            "item_count": length,
            "ttl_seconds": ttl if ttl > 0 else None,
            "exists": length > 0
        }
    
    async def extend_ttl(self, seconds: Optional[int] = None) -> None:
        """Extend session TTL"""
        client = await self._get_client()
        
        if await self.exists():
            ttl_seconds = seconds or int(os.getenv("REDIS_SESSION_TTL", "604800"))
            await client.expire(self._key, ttl_seconds)
    
    # Context manager support
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()


# Helper function for easy session creation
async def create_redis_session(
    session_id: str, 
    redis_url: Optional[str] = None,
    restore_existing: bool = True
) -> RedisSession:
    """
    Create or restore a Redis session
    
    Args:
        session_id: Session identifier
        redis_url: Redis connection URL
        restore_existing: If False, clears any existing session data
        
    Returns:
        RedisSession instance
    """
    session = RedisSession(session_id, redis_url)
    
    if not restore_existing:
        await session.clear_session()
    
    return session