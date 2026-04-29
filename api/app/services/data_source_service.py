"""Data source service"""
from typing import Sequence, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.data_source_repo import SourceGroupRepository, DataSourceRepository
from app.schemas.data_source import (
    SourceGroupResponse,
    SourceGroupCreate,
    SourceGroupUpdate,
    SourceGroupListResponse,
    DataSourceResponse,
    DataSourceCreate,
    DataSourceUpdate,
    DataSourceListResponse,
)
from app.core.exceptions import NotFoundException


class DataSourceService:
    """Data source management service"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.group_repo = SourceGroupRepository(session)
        self.source_repo = DataSourceRepository(session)

    async def list_groups(self, page: int = 1, page_size: int = 20) -> SourceGroupListResponse:
        """List all source groups"""
        offset = (page - 1) * page_size
        groups = await self.group_repo.get_all(limit=page_size, offset=offset)
        total = await self.group_repo.count()
        return SourceGroupListResponse(
            total=total,
            items=[
                SourceGroupResponse(
                    id=str(g.id),
                    name=g.name,
                    collect_interval=g.collect_interval,
                    is_active=g.is_active,
                    created_at=g.created_at,
                    updated_at=g.updated_at,
                )
                for g in groups
            ],
        )

    async def create_group(self, request: SourceGroupCreate) -> SourceGroupResponse:
        """Create a new source group"""
        group = await self.group_repo.create(
            name=request.name,
            collect_interval=request.collect_interval,
            is_active=request.is_active,
        )
        await self.session.commit()
        return SourceGroupResponse(
            id=str(group.id),
            name=group.name,
            collect_interval=group.collect_interval,
            is_active=group.is_active,
            created_at=group.created_at,
            updated_at=group.updated_at,
        )

    async def get_group(self, group_id: UUID) -> SourceGroupResponse:
        """Get a source group by ID"""
        group = await self.group_repo.get_by_id(group_id)
        if not group:
            raise NotFoundException("Source group not found")
        return SourceGroupResponse(
            id=str(group.id),
            name=group.name,
            collect_interval=group.collect_interval,
            is_active=group.is_active,
            created_at=group.created_at,
            updated_at=group.updated_at,
        )

    async def update_group(self, group_id: UUID, request: SourceGroupUpdate) -> SourceGroupResponse:
        """Update a source group"""
        update_data = request.model_dump(exclude_none=True)
        if not update_data:
            raise NotFoundException("No update data provided")

        group = await self.group_repo.update(group_id, **update_data)
        if not group:
            raise NotFoundException("Source group not found")
        await self.session.commit()
        return SourceGroupResponse(
            id=str(group.id),
            name=group.name,
            collect_interval=group.collect_interval,
            is_active=group.is_active,
            created_at=group.created_at,
            updated_at=group.updated_at,
        )

    async def delete_group(self, group_id: UUID) -> bool:
        """Delete a source group"""
        # Check if group has sources
        count = await self.source_repo.count_by_group(group_id)
        if count > 0:
            raise NotFoundException(f"Cannot delete group with {count} data sources")

        deleted = await self.group_repo.delete_by_id(group_id)
        if not deleted:
            raise NotFoundException("Source group not found")
        await self.session.commit()
        return True

    async def list_sources(
        self,
        group_id: Optional[UUID] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> DataSourceListResponse:
        """List data sources"""
        offset = (page - 1) * page_size
        if group_id:
            sources = await self.source_repo.get_by_group(group_id)
            total = await self.source_repo.count_by_group(group_id)
        else:
            sources = await self.source_repo.get_all(limit=page_size, offset=offset)
            total = await self.source_repo.count()

        return DataSourceListResponse(
            total=total,
            items=[
                DataSourceResponse(
                    id=str(s.id),
                    group_id=str(s.group_id),
                    name=s.name,
                    type=s.type,
                    collector_type=s.collector_type,
                    config=s.config,
                    priority=s.priority,
                    is_active=s.is_active,
                    status=s.status,
                    last_collected_at=s.last_collected_at,
                    last_error_at=s.last_error_at,
                    last_error_message=s.last_error_message,
                    consecutive_failures=s.consecutive_failures,
                    created_at=s.created_at,
                    updated_at=s.updated_at,
                )
                for s in sources
            ],
        )

    async def create_source(self, request: DataSourceCreate) -> DataSourceResponse:
        """Create a new data source"""
        # Validate group exists
        group = await self.group_repo.get_by_id(UUID(request.group_id))
        if not group:
            raise NotFoundException("Source group not found")

        source = await self.source_repo.create(
            group_id=UUID(request.group_id),
            name=request.name,
            type=request.type,
            collector_type=request.collector_type,
            config=request.config,
            priority=request.priority,
            is_active=request.is_active,
        )
        await self.session.commit()
        return DataSourceResponse(
            id=str(source.id),
            group_id=str(source.group_id),
            name=source.name,
            type=source.type,
            collector_type=source.collector_type,
            config=source.config,
            priority=source.priority,
            is_active=source.is_active,
            status=source.status,
            last_collected_at=source.last_collected_at,
            last_error_at=source.last_error_at,
            last_error_message=source.last_error_message,
            consecutive_failures=source.consecutive_failures,
            created_at=source.created_at,
            updated_at=source.updated_at,
        )

    async def get_source(self, source_id: UUID) -> DataSourceResponse:
        """Get a data source by ID"""
        source = await self.source_repo.get_by_id(source_id)
        if not source:
            raise NotFoundException("Data source not found")
        return DataSourceResponse(
            id=str(source.id),
            group_id=str(source.group_id),
            name=source.name,
            type=source.type,
            collector_type=source.collector_type,
            config=source.config,
            priority=source.priority,
            is_active=source.is_active,
            status=source.status,
            last_collected_at=source.last_collected_at,
            last_error_at=source.last_error_at,
            last_error_message=source.last_error_message,
            consecutive_failures=source.consecutive_failures,
            created_at=source.created_at,
            updated_at=source.updated_at,
        )

    async def update_source(self, source_id: UUID, request: DataSourceUpdate) -> DataSourceResponse:
        """Update a data source"""
        update_data = request.model_dump(exclude_none=True)
        if not update_data:
            raise NotFoundException("No update data provided")

        source = await self.source_repo.update(source_id, **update_data)
        if not source:
            raise NotFoundException("Data source not found")
        await self.session.commit()
        return DataSourceResponse(
            id=str(source.id),
            group_id=str(source.group_id),
            name=source.name,
            type=source.type,
            collector_type=source.collector_type,
            config=source.config,
            priority=source.priority,
            is_active=source.is_active,
            status=source.status,
            last_collected_at=source.last_collected_at,
            last_error_at=source.last_error_at,
            last_error_message=source.last_error_message,
            consecutive_failures=source.consecutive_failures,
            created_at=source.created_at,
            updated_at=source.updated_at,
        )

    async def delete_source(self, source_id: UUID) -> bool:
        """Delete a data source"""
        deleted = await self.source_repo.delete_by_id(source_id)
        if not deleted:
            raise NotFoundException("Data source not found")
        await self.session.commit()
        return True

    async def toggle_source(self, source_id: UUID, is_active: bool) -> DataSourceResponse:
        """Toggle data source active status"""
        source = await self.source_repo.update(source_id, is_active=is_active)
        if not source:
            raise NotFoundException("Data source not found")
        await self.session.commit()
        return DataSourceResponse(
            id=str(source.id),
            group_id=str(source.group_id),
            name=source.name,
            type=source.type,
            collector_type=source.collector_type,
            config=source.config,
            priority=source.priority,
            is_active=source.is_active,
            status=source.status,
            last_collected_at=source.last_collected_at,
            last_error_at=source.last_error_at,
            last_error_message=source.last_error_message,
            consecutive_failures=source.consecutive_failures,
            created_at=source.created_at,
            updated_at=source.updated_at,
        )