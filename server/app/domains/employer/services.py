"""
Employer Service for Aiviue Platform.

Service layer containing all business logic for employer operations.

Principle: Service handles:
- Input sanitization
- Business rule validation
- Transaction management
- Cache operations
- Event publishing

Repository handles only database operations.
"""

from typing import Any, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.employer.models import Employer
from app.domains.employer.repository import EmployerRepository
from app.domains.employer.schemas import (
    EmployerCreateRequest,
    EmployerFilters,
    EmployerListResponse,
    EmployerResponse,
    EmployerSummaryResponse,
    EmployerUpdateRequest,
)
from app.shared.cache import CacheService, CacheTTL, RedisClient
from app.shared.events import EventPublisher, EventTypes
from app.shared.exceptions import ConflictError, NotFoundError, ValidationError
from app.shared.logging import get_logger
from app.shared.utils import create_paginated_response, sanitize_text


logger = get_logger(__name__)


class EmployerService:
    """
    Service for employer business logic.
    
    Args:
        session: SQLAlchemy async session
        cache: Optional CacheService for caching
        event_publisher: Optional EventPublisher for events
    
    Usage:
        service = EmployerService(session, cache, publisher)
        employer = await service.create(request)
    """
    
    def __init__(
        self,
        session: AsyncSession,
        cache: Optional[CacheService] = None,
        event_publisher: Optional[EventPublisher] = None,
    ) -> None:
        self.session = session
        self.repo = EmployerRepository(session)
        self.cache = cache
        self.publisher = event_publisher
    
    # ==================== CREATE ====================
    
    async def create(
        self,
        request: EmployerCreateRequest,
    ) -> EmployerResponse:
        """
        Create a new employer.
        
        Steps:
        1. Sanitize input
        2. Check for duplicate email/phone
        3. Create employer
        4. Publish event
        5. Return response
        
        Args:
            request: EmployerCreateRequest with validated data
        
        Returns:
            EmployerResponse
        
        Raises:
            ConflictError: If email or phone already exists
        """
        # 1. Sanitize input
        sanitized_data = self._sanitize_create_data(request)
        
        # 2. Check for duplicates
        await self._check_duplicate_email(sanitized_data["email"])
        if sanitized_data.get("phone"):
            await self._check_duplicate_phone(sanitized_data["phone"])
        
        # 3. Create employer
        employer = await self.repo.create(sanitized_data)
        
        logger.info(
            f"Employer created: {employer.id}",
            extra={
                "event": "employer_created",
                "employer_id": str(employer.id),
                "email": employer.email,
                "company_name": employer.company_name,
            },
        )
        
        # 4. Publish event (only if screening events enabled)
        from app.config import settings
        if settings.enable_screening_events and self.publisher:
            await self.publisher.publish(
                EventTypes.EMPLOYER_CREATED,
                {
                    "employer_id": str(employer.id),
                    "name": employer.name,
                    "email": employer.email,
                    "company_name": employer.company_name,
                },
            )
            logger.info(f"Event sent: employer.created")
        
        # 5. Return response
        return self._to_response(employer)
    
    # ==================== READ ====================
    
    async def get_by_id(
        self,
        employer_id: UUID,
    ) -> EmployerResponse:
        """
        Get employer by ID.
        
        Uses cache if available.
        
        Args:
            employer_id: UUID of employer
        
        Returns:
            EmployerResponse
        
        Raises:
            NotFoundError: If employer not found
        """
        # Try cache first
        if self.cache:
            cached = await self.cache.get(str(employer_id))
            if cached:
                logger.debug(f"Cache hit for employer {employer_id}")
                return EmployerResponse.model_validate(cached)
        
        # Fetch from database
        employer = await self.repo.get_by_id(employer_id)
        
        if employer is None:
            raise NotFoundError(
                message="Employer not found",
                error_code="EMPLOYER_NOT_FOUND",
                context={"employer_id": str(employer_id)},
            )
        
        response = self._to_response(employer)
        
        # Store in cache
        if self.cache:
            await self.cache.set(
                str(employer_id),
                response.model_dump(mode="json"),
                ttl=CacheTTL.MEDIUM,
            )
        
        return response
    
    async def get_by_email(
        self,
        email: str,
    ) -> EmployerResponse:
        """
        Get employer by email.
        
        Args:
            email: Email address
        
        Returns:
            EmployerResponse
        
        Raises:
            NotFoundError: If employer not found
        """
        employer = await self.repo.get_by_email(email.lower().strip())
        
        if employer is None:
            raise NotFoundError(
                message="Employer not found",
                error_code="EMPLOYER_NOT_FOUND",
                context={"email": email},
            )
        
        return self._to_response(employer)
    
    # ==================== LIST ====================
    
    async def list(
        self,
        filters: Optional[EmployerFilters] = None,
        cursor: Optional[str] = None,
        limit: int = 20,
        include_total: bool = False,
    ) -> EmployerListResponse:
        """
        List employers with filters and pagination.
        
        Args:
            filters: Filter parameters
            cursor: Pagination cursor
            limit: Max items per page
            include_total: Include total count (expensive)
        
        Returns:
            EmployerListResponse with items and pagination
        """
        # Fetch items (limit + 1 to check has_more)
        employers = await self.repo.list(
            filters=filters,
            cursor=cursor,
            limit=limit,
        )
        
        # Build paginated response
        paginated = create_paginated_response(
            items=employers,
            limit=limit,
            cursor_field="id",
            timestamp_field="created_at",
        )
        
        # Convert to summary responses
        items = [
            self._to_summary_response(emp)
            for emp in paginated["items"]
        ]
        
        # Get total count if requested
        total_count = None
        if include_total:
            total_count = await self.repo.count(filters)
        
        return EmployerListResponse(
            items=items,
            next_cursor=paginated["next_cursor"],
            has_more=paginated["has_more"],
            total_count=total_count,
        )
    
    # ==================== UPDATE ====================
    
    async def update(
        self,
        employer_id: UUID,
        request: EmployerUpdateRequest,
    ) -> EmployerResponse:
        """
        Update employer.
        
        Steps:
        1. Sanitize input
        2. Check if employer exists
        3. Check for duplicate phone (if changed)
        4. Update with optimistic locking
        5. Invalidate cache
        6. Publish event
        
        Args:
            employer_id: UUID of employer
            request: EmployerUpdateRequest with fields to update
        
        Returns:
            Updated EmployerResponse
        
        Raises:
            NotFoundError: If employer not found
            ConflictError: If version mismatch or phone duplicate
        """
        # 1. Sanitize and get changed fields
        update_data = self._sanitize_update_data(request)
        
        if not update_data:
            # No fields to update, just return current
            return await self.get_by_id(employer_id)
        
        # 2. Check for duplicate phone if changing
        if "phone" in update_data and update_data["phone"]:
            existing = await self.repo.get_by_phone(update_data["phone"])
            if existing and existing.id != employer_id:
                raise ConflictError(
                    message="Phone number already in use",
                    error_code="PHONE_ALREADY_EXISTS",
                    context={"phone": update_data["phone"]},
                )
        
        # 3. Update with optimistic locking
        employer = await self.repo.update(
            employer_id=employer_id,
            data=update_data,
            expected_version=request.version,
        )
        
        if employer is None:
            raise NotFoundError(
                message="Employer not found",
                error_code="EMPLOYER_NOT_FOUND",
                context={"employer_id": str(employer_id)},
            )
        
        logger.info(
            f"Employer updated: {employer_id}",
            extra={
                "event": "employer_updated",
                "employer_id": str(employer_id),
                "updated_fields": list(update_data.keys()),
                "new_version": employer.version,
            },
        )
        
        # 4. Invalidate cache
        if self.cache:
            await self.cache.delete(str(employer_id))
        
        # 5. Publish event (only if screening events enabled)
        from app.config import settings
        if settings.enable_screening_events and self.publisher:
            await self.publisher.publish(
                EventTypes.EMPLOYER_UPDATED,
                {
                    "employer_id": str(employer_id),
                    "changes": update_data,
                },
            )
            logger.info(f"Event sent: employer.updated")
        
        return self._to_response(employer)
    
    # ==================== DELETE ====================
    
    async def delete(
        self,
        employer_id: UUID,
        version: int,
    ) -> bool:
        """
        Soft delete employer.
        
        Args:
            employer_id: UUID of employer
            version: Current version for optimistic locking
        
        Returns:
            True if deleted
        
        Raises:
            NotFoundError: If employer not found
            ConflictError: If version mismatch
        """
        deleted = await self.repo.soft_delete(employer_id, version)
        
        if not deleted:
            raise NotFoundError(
                message="Employer not found",
                error_code="EMPLOYER_NOT_FOUND",
                context={"employer_id": str(employer_id)},
            )
        
        logger.info(
            f"Employer deleted: {employer_id}",
            extra={
                "event": "employer_deleted",
                "employer_id": str(employer_id),
            },
        )
        
        # Invalidate cache
        if self.cache:
            await self.cache.delete(str(employer_id))
        
        return True
    
    # ==================== HELPERS ====================
    
    def _sanitize_create_data(
        self,
        request: EmployerCreateRequest,
    ) -> dict[str, Any]:
        """Sanitize and prepare data for creation."""
        return {
            "name": sanitize_text(request.name),
            "email": request.email.lower().strip(),
            "phone": request.phone.strip() if request.phone else None,
            "company_name": sanitize_text(request.company_name),
            "company_description": sanitize_text(request.company_description) if request.company_description else None,
            "company_website": request.company_website.strip() if request.company_website else None,
            "company_size": request.company_size,
            "industry": sanitize_text(request.industry) if request.industry else None,
            "headquarters_location": sanitize_text(request.headquarters_location) if request.headquarters_location else None,
            "city": sanitize_text(request.city) if request.city else None,
            "state": sanitize_text(request.state) if request.state else None,
            "country": sanitize_text(request.country) if request.country else None,
            "logo_url": request.logo_url.strip() if request.logo_url else None,
            "gst_number": sanitize_text(request.gst_number) if request.gst_number else None,
        }
    
    def _sanitize_update_data(
        self,
        request: EmployerUpdateRequest,
    ) -> dict[str, Any]:
        """Sanitize and prepare data for update (only changed fields)."""
        data = {}
        
        if request.name is not None:
            data["name"] = sanitize_text(request.name)
        if request.phone is not None:
            data["phone"] = request.phone.strip() if request.phone else None
        if request.company_name is not None:
            data["company_name"] = sanitize_text(request.company_name)
        if request.company_description is not None:
            data["company_description"] = sanitize_text(request.company_description) if request.company_description else None
        if request.company_website is not None:
            data["company_website"] = request.company_website.strip() if request.company_website else None
        if request.company_size is not None:
            data["company_size"] = request.company_size
        if request.industry is not None:
            data["industry"] = sanitize_text(request.industry) if request.industry else None
        if request.headquarters_location is not None:
            data["headquarters_location"] = sanitize_text(request.headquarters_location) if request.headquarters_location else None
        if request.city is not None:
            data["city"] = sanitize_text(request.city) if request.city else None
        if request.state is not None:
            data["state"] = sanitize_text(request.state) if request.state else None
        if request.country is not None:
            data["country"] = sanitize_text(request.country) if request.country else None
        if request.logo_url is not None:
            data["logo_url"] = request.logo_url.strip() if request.logo_url else None
        if request.gst_number is not None:
            data["gst_number"] = sanitize_text(request.gst_number) if request.gst_number else None
        
        return data
    
    async def _check_duplicate_email(self, email: str) -> None:
        """Check if email already exists."""
        if await self.repo.exists_by_email(email):
            raise ConflictError(
                message="Email already exists",
                error_code="EMAIL_ALREADY_EXISTS",
                context={"email": email},
            )
    
    async def _check_duplicate_phone(self, phone: str) -> None:
        """Check if phone already exists."""
        if await self.repo.exists_by_phone(phone):
            raise ConflictError(
                message="Phone number already exists",
                error_code="PHONE_ALREADY_EXISTS",
                context={"phone": phone},
            )
    
    def _to_response(self, employer: Employer) -> EmployerResponse:
        """Convert Employer model to EmployerResponse."""
        return EmployerResponse(
            id=employer.id,
            name=employer.name,
            email=employer.email,
            phone=employer.phone,
            company_name=employer.company_name,
            company_description=employer.company_description,
            company_website=employer.company_website,
            company_size=employer.company_size,
            industry=employer.industry,
            headquarters_location=employer.headquarters_location,
            city=employer.city,
            state=employer.state,
            country=employer.country,
            logo_url=employer.logo_url,
            gst_number=employer.gst_number,
            is_verified=employer.is_verified,
            verified_at=employer.verified_at,
            is_active=employer.is_active,
            version=employer.version,
            created_at=employer.created_at,
            updated_at=employer.updated_at,
        )
    
    def _to_summary_response(self, employer: Employer) -> EmployerSummaryResponse:
        """Convert Employer model to EmployerSummaryResponse."""
        return EmployerSummaryResponse(
            id=employer.id,
            name=employer.name,
            email=employer.email,
            company_name=employer.company_name,
            is_verified=employer.is_verified,
            created_at=employer.created_at,
        )


# ==================== DEPENDENCY FACTORY ====================

def get_employer_service(
    session: AsyncSession,
    redis_client: Optional[RedisClient] = None,
    event_publisher: Optional[EventPublisher] = None,
) -> EmployerService:
    """
    Factory function to create EmployerService with dependencies.
    
    Usage in routes:
        @router.post("/")
        async def create_employer(
            request: EmployerCreateRequest,
            session: AsyncSession = Depends(get_db),
            redis: RedisClient = Depends(get_redis_client),
        ):
            cache = CacheService(redis, namespace="employer")
            publisher = EventPublisher(redis)
            service = get_employer_service(session, redis, publisher)
            return await service.create(request)
    """
    cache = None
    if redis_client:
        cache = CacheService(redis_client, namespace="employer")
    
    return EmployerService(
        session=session,
        cache=cache,
        event_publisher=event_publisher,
    )
