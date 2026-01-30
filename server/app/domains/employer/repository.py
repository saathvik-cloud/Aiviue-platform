"""
Employer Repository for Aiviue Platform.

Repository pattern for employer database operations.

Principle: Repository handles ONLY database operations.
- No business logic
- No validation
- No error transformation (let exceptions bubble up)

All business logic belongs in the Service layer.
"""

from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import and_, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.employer.models import Employer
from app.domains.employer.schemas import EmployerFilters
from app.shared.exceptions import ConflictError, NotFoundError
from app.shared.logging import get_logger
from app.shared.utils.pagination import CursorData, decode_cursor


logger = get_logger(__name__)


class EmployerRepository:
    """
    Repository for Employer database operations.
    
    Args:
        session: SQLAlchemy async session
    
    Usage:
        repo = EmployerRepository(session)
        employer = await repo.create({"name": "John", ...})
        employer = await repo.get_by_id(uuid)
    """
    
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
    
    # ==================== CREATE ====================
    
    async def create(self, data: dict[str, Any]) -> Employer:
        """
        Create a new employer.
        
        Args:
            data: Dictionary of employer attributes
        
        Returns:
            Created Employer instance
        
        Note: Does not commit - caller handles transaction.
        """
        employer = Employer(**data)
        self.session.add(employer)
        await self.session.flush()  # Get ID without committing
        await self.session.refresh(employer)
        
        logger.debug(
            f"Employer created: {employer.id}",
            extra={"employer_id": str(employer.id)},
        )
        
        return employer
    
    # ==================== READ ====================
    
    async def get_by_id(
        self,
        employer_id: UUID,
        include_inactive: bool = False,
    ) -> Optional[Employer]:
        """
        Get employer by ID.
        
        Args:
            employer_id: UUID of employer
            include_inactive: Include soft-deleted records
        
        Returns:
            Employer or None if not found
        """
        query = select(Employer).where(Employer.id == employer_id)
        
        if not include_inactive:
            query = query.where(Employer.is_active == True)
        
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_by_email(
        self,
        email: str,
        include_inactive: bool = False,
    ) -> Optional[Employer]:
        """
        Get employer by email.
        
        Args:
            email: Email address (case-insensitive)
            include_inactive: Include soft-deleted records
        
        Returns:
            Employer or None if not found
        """
        query = select(Employer).where(
            func.lower(Employer.email) == email.lower()
        )
        
        if not include_inactive:
            query = query.where(Employer.is_active == True)
        
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_by_mobile(
        self,
        mobile: str,
        include_inactive: bool = False,
    ) -> Optional[Employer]:
        """
        Get employer by mobile number.
        
        Args:
            mobile: Mobile number
            include_inactive: Include soft-deleted records
        
        Returns:
            Employer or None if not found
        """
        query = select(Employer).where(Employer.mobile == mobile)
        
        if not include_inactive:
            query = query.where(Employer.is_active == True)
        
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def exists_by_email(
        self,
        email: str,
        exclude_id: Optional[UUID] = None,
    ) -> bool:
        """
        Check if email already exists.
        
        Args:
            email: Email to check
            exclude_id: Exclude this ID from check (for updates)
        
        Returns:
            True if email exists
        """
        query = select(func.count()).select_from(Employer).where(
            func.lower(Employer.email) == email.lower()
        )
        
        if exclude_id:
            query = query.where(Employer.id != exclude_id)
        
        result = await self.session.execute(query)
        count = result.scalar()
        return count > 0
    
    async def exists_by_mobile(
        self,
        mobile: str,
        exclude_id: Optional[UUID] = None,
    ) -> bool:
        """
        Check if mobile already exists.
        
        Args:
            mobile: Mobile to check
            exclude_id: Exclude this ID from check (for updates)
        
        Returns:
            True if mobile exists
        """
        query = select(func.count()).select_from(Employer).where(
            Employer.mobile == mobile
        )
        
        if exclude_id:
            query = query.where(Employer.id != exclude_id)
        
        result = await self.session.execute(query)
        count = result.scalar()
        return count > 0
    
    # ==================== LIST ====================
    
    async def list(
        self,
        filters: Optional[EmployerFilters] = None,
        cursor: Optional[str] = None,
        limit: int = 20,
    ) -> list[Employer]:
        """
        List employers with filters and pagination.
        
        Args:
            filters: Filter parameters
            cursor: Pagination cursor
            limit: Max items to return (fetch limit + 1 to check has_more)
        
        Returns:
            List of Employer instances
        """
        query = select(Employer)
        
        # Apply filters
        if filters:
            query = self._apply_filters(query, filters)
        else:
            # Default: only active
            query = query.where(Employer.is_active == True)
        
        # Apply cursor pagination
        cursor_data = decode_cursor(cursor)
        if cursor_data:
            query = query.where(
                or_(
                    Employer.created_at < cursor_data.created_at,
                    and_(
                        Employer.created_at == cursor_data.created_at,
                        Employer.id < UUID(cursor_data.id),
                    ),
                )
            )
        
        # Order by created_at DESC, then by id for consistency
        query = query.order_by(
            Employer.created_at.desc(),
            Employer.id.desc(),
        )
        
        # Limit (fetch one extra to check has_more)
        query = query.limit(limit + 1)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def count(
        self,
        filters: Optional[EmployerFilters] = None,
    ) -> int:
        """
        Count employers matching filters.
        
        Args:
            filters: Filter parameters
        
        Returns:
            Count of matching employers
        """
        query = select(func.count()).select_from(Employer)
        
        if filters:
            query = self._apply_filters(query, filters)
        else:
            query = query.where(Employer.is_active == True)
        
        result = await self.session.execute(query)
        return result.scalar() or 0
    
    def _apply_filters(
        self,
        query,
        filters: EmployerFilters,
    ):
        """Apply filter conditions to query."""
        conditions = []
        
        # Active status
        if filters.is_active is not None:
            conditions.append(Employer.is_active == filters.is_active)
        
        # Search (name, email, company_name)
        if filters.search:
            search_term = f"%{filters.search}%"
            conditions.append(
                or_(
                    Employer.name.ilike(search_term),
                    Employer.email.ilike(search_term),
                    Employer.company_name.ilike(search_term),
                )
            )
        
        # Company size
        if filters.company_size:
            conditions.append(Employer.company_size == filters.company_size)
        
        # Industry
        if filters.industry:
            conditions.append(Employer.industry.ilike(f"%{filters.industry}%"))
        
        # Verification status
        if filters.is_verified is not None:
            if filters.is_verified:
                conditions.append(
                    or_(
                        Employer.is_email_verified == True,
                        Employer.is_mobile_verified == True,
                    )
                )
            else:
                conditions.append(
                    and_(
                        Employer.is_email_verified == False,
                        Employer.is_mobile_verified == False,
                    )
                )
        
        if conditions:
            query = query.where(and_(*conditions))
        
        return query
    
    # ==================== UPDATE ====================
    
    async def update(
        self,
        employer_id: UUID,
        data: dict[str, Any],
        expected_version: int,
    ) -> Optional[Employer]:
        """
        Update employer with optimistic locking.
        
        Args:
            employer_id: UUID of employer
            data: Fields to update
            expected_version: Current version (for optimistic locking)
        
        Returns:
            Updated Employer or None if not found/version mismatch
        
        Raises:
            ConflictError: If version mismatch (concurrent modification)
        """
        # Build update statement with version check
        stmt = (
            update(Employer)
            .where(
                and_(
                    Employer.id == employer_id,
                    Employer.is_active == True,
                    Employer.version == expected_version,
                )
            )
            .values(
                **data,
                version=Employer.version + 1,
                updated_at=datetime.now(timezone.utc),
            )
            .returning(Employer)
        )
        
        result = await self.session.execute(stmt)
        employer = result.scalar_one_or_none()
        
        if employer is None:
            # Check if employer exists to distinguish between not found and version mismatch
            existing = await self.get_by_id(employer_id, include_inactive=True)
            if existing is None:
                return None
            elif not existing.is_active:
                return None
            else:
                # Version mismatch - concurrent modification
                raise ConflictError(
                    message="Employer was modified by another request",
                    error_code="VERSION_CONFLICT",
                    context={
                        "employer_id": str(employer_id),
                        "expected_version": expected_version,
                        "actual_version": existing.version,
                    },
                )
        
        logger.debug(
            f"Employer updated: {employer_id}",
            extra={
                "employer_id": str(employer_id),
                "version": employer.version,
            },
        )
        
        return employer
    
    # ==================== DELETE ====================
    
    async def soft_delete(
        self,
        employer_id: UUID,
        expected_version: int,
    ) -> bool:
        """
        Soft delete employer (set is_active = False).
        
        Args:
            employer_id: UUID of employer
            expected_version: Current version
        
        Returns:
            True if deleted, False if not found
        
        Raises:
            ConflictError: If version mismatch
        """
        result = await self.update(
            employer_id,
            {"is_active": False},
            expected_version,
        )
        return result is not None
    
    async def hard_delete(self, employer_id: UUID) -> bool:
        """
        Permanently delete employer.
        
        WARNING: Use with caution. Prefer soft_delete.
        
        Args:
            employer_id: UUID of employer
        
        Returns:
            True if deleted
        """
        employer = await self.get_by_id(employer_id, include_inactive=True)
        if employer:
            await self.session.delete(employer)
            await self.session.flush()
            return True
        return False
