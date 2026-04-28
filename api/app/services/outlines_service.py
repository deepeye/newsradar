"""Outlines service"""
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.outline_repo import OutlineRepository
from app.repositories.clue_repo import ClueRepository
from app.repositories.org_config_repo import OrgConfigRepository
from app.services.ai_service import AIService
from app.models.outline import TopicOutline
import structlog

logger = structlog.get_logger("outlines_service")


class OutlinesService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.outline_repo = OutlineRepository(db)
        self.clue_repo = ClueRepository(db)
        self.org_config_repo = OrgConfigRepository(db)
        self.ai_service = AIService()

    async def list_outlines(self, page: int = 1, page_size: int = 20) -> dict:
        offset = (page - 1) * page_size
        items = await self.outline_repo.get_all(limit=page_size, offset=offset)
        total = await self.outline_repo.count()
        return {
            "total": total,
            "items": [self._format_outline(o) for o in items],
        }

    async def get_outline(self, outline_id: UUID) -> Optional[dict]:
        outline = await self.outline_repo.get_by_id(outline_id)
        if not outline:
            return None
        return self._format_outline(outline)

    async def create_outline(self, title: str, summary: Optional[str], urgency: str, user_id: UUID) -> dict:
        outline = await self.outline_repo.create(
            title=title,
            summary=summary,
            urgency=urgency,
            created_by=user_id,
        )
        return self._format_outline(outline)

    async def update_outline(self, outline_id: UUID, **kwargs) -> Optional[dict]:
        outline = await self.outline_repo.update(outline_id, **kwargs)
        if not outline:
            return None
        return self._format_outline(outline)

    async def delete_outline(self, outline_id: UUID) -> bool:
        return await self.outline_repo.delete_by_id(outline_id)

    async def generate_from_clues(
        self,
        clue_ids: list[str],
        additional_context: Optional[str],
        user_id: UUID,
    ) -> dict:
        # Fetch clues
        uuid_ids = [UUID(cid) for cid in clue_ids]
        clues = await self.clue_repo.get_by_ids(uuid_ids)
        clues_text = "\n".join(
            f"- [{c.author or '未知'}] {c.title} (热度: {c.heat_value or 'N/A'}, 链接: {c.url or '无'})"
            for c in clues
        )

        # Get org config
        org_config = await self.org_config_repo.get_active()
        domains = org_config.domains if org_config else []
        style = org_config.style if org_config else []

        # Generate via AI
        ai_result = await self.ai_service.generate_outline(
            domains=domains,
            style=style,
            clues_text=clues_text,
            additional_context=additional_context,
        )

        # Create outline record
        outline = await self.outline_repo.create(
            title=ai_result.get("title", "未命名选题"),
            summary=ai_result.get("summary"),
            urgency=ai_result.get("urgency", "中"),
            info_density=ai_result.get("info_density", 0),
            headlines=ai_result.get("headlines"),
            lead_paragraph=ai_result.get("lead_paragraph"),
            outline_sections=ai_result.get("outline_sections"),
            interview_directions=ai_result.get("interview_directions"),
            references=ai_result.get("references"),
            source_clue_ids=clue_ids,
            ai_model=self.ai_service.model,
            created_by=user_id,
        )
        return self._format_outline(outline)

    async def regenerate_section(
        self,
        outline_id: UUID,
        section: str,
    ) -> Optional[dict]:
        outline = await self.outline_repo.get_by_id(outline_id)
        if not outline:
            return None

        outline_text = f"标题: {outline.title}\n概要: {outline.summary or ''}"

        if section == "headlines":
            headlines = await self.ai_service.generate_headlines(outline_text)
            await self.outline_repo.update(outline_id, headlines=headlines)
        elif section == "outline":
            # Re-generate outline sections
            org_config = await self.org_config_repo.get_active()
            domains = org_config.domains if org_config else []
            style = org_config.style if org_config else []
            clues_text = outline.summary or outline.title
            ai_result = await self.ai_service.generate_outline(domains, style, clues_text)
            await self.outline_repo.update(
                outline_id,
                outline_sections=ai_result.get("outline_sections"),
            )
        elif section == "interview":
            interview = await self.ai_service.generate_headlines(
                f"采访方向生成\n{outline_text}\n概要: {outline.summary}",
                styles=["政策观察家", "一线从业者", "学术研究者"],
            )
            directions = [
                {"id": f"i{i+1}", "role": h.get("style", ""), "description": h.get("text", "")}
                for i, h in enumerate(interview)
            ]
            await self.outline_repo.update(outline_id, interview_directions=directions)

        updated = await self.outline_repo.get_by_id(outline_id)
        return self._format_outline(updated)

    def _format_outline(self, outline: TopicOutline) -> dict:
        return {
            "id": str(outline.id),
            "title": outline.title,
            "summary": outline.summary,
            "urgency": outline.urgency,
            "info_density": outline.info_density,
            "headlines": outline.headlines,
            "lead_paragraph": outline.lead_paragraph,
            "outline_sections": outline.outline_sections,
            "interview_directions": outline.interview_directions,
            "references": outline.references,
            "source_clue_ids": outline.source_clue_ids,
            "ai_model": outline.ai_model,
            "status": outline.status,
            "created_at": outline.created_at,
            "updated_at": outline.updated_at,
        }