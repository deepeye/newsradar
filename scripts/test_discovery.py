"""Test script: manually run discovery recommendation generation."""
import asyncio
import json
import sys

sys.path.insert(0, "/Users/felixwang/devspace/cc-project/cqh-agent/api")

from app.core.database import db_manager
from app.services.discovery_service import DiscoveryService
from app.repositories.org_config_repo import OrgConfigRepository
from app.repositories.clue_repo import ClueRepository, DataSourceRepository
from app.utils.domain_taxonomy import classify_domains, resolve_domain
from app.utils.heat_value import parse_heat_value
from datetime import datetime, timezone


async def main():
    await db_manager.initialize()

    async with db_manager.session() as session:
        # 1. Check OrgConfig
        org_repo = OrgConfigRepository(session)
        config = await org_repo.get_active()
        if not config:
            print("ERROR: No active OrgConfig found")
            return
        print(f"\n=== OrgConfig ===")
        print(f"  name: {config.name}")
        print(f"  domains: {config.domains}")
        print(f"  style: {config.style}")

        resolved = set(resolve_domain(d) for d in config.domains)
        print(f"  resolved_domains: {resolved}")

        # 2. Check sources
        ds_repo = DataSourceRepository(session)
        sources = await ds_repo.get_all_active()
        print(f"\n=== Active Sources ({len(sources)}) ===")
        hotlist = [s for s in sources if s.type.value in ("hotlist", "video")]
        accounts = [s for s in sources if s.type.value == "account"]
        print(f"  hotlist/video: {len(hotlist)}")
        print(f"  account/KOL: {len(accounts)}")

        # 3. Run full pipeline
        print(f"\n=== Running Discovery Pipeline ===")
        service = DiscoveryService(session)

        # Layer 1+2: select_clues (no AI yet)
        selected = await service._select_clues(config.domains)

        print(f"\n--- After Layer 1 (domain filter) + Layer 2 (topic merge) ---")
        print(f"  Selected clues: {len(selected)}")

        for i, clue in enumerate(selected):
            score = getattr(clue, "_score", 0)
            domains = getattr(clue, "_classified_domains", [])
            merged_count = getattr(clue, "_merged_count", 1)
            platform = getattr(clue, "_platform_label", "")
            source_type = getattr(clue, "_source_type_label", "")
            heat = clue.heat_value or "N/A"
            merged_summary = getattr(clue, "_merged_platforms_summary", "")
            merge_note = f" [{merged_summary}]" if merged_summary else ""

            print(f"  {i+1}. [{platform}·{source_type}] {clue.title[:40]} | score={score:.3f} | domains={domains} | heat={heat} | merged={merged_count}{merge_note}")

        # Layer 3: Per-clue AI (skip if QWEN_API_KEY not set)
        from app.core.config import settings
        if not settings.QWEN_API_KEY:
            print("\n--- Layer 3: SKIPPED (no QWEN_API_KEY) ---")
        else:
            print(f"\n--- Layer 3: Per-clue AI generation (max {len(selected)} calls, concurrent=5) ---")
            raw_results = await service._generate_per_clue(
                selected, config.domains, config.style
            )
            print(f"  Successful recommendations: {len(raw_results)}")

            # Sort by clue score
            scored_recs = []
            for rec, clue in raw_results:
                clue_score = getattr(clue, "_score", 0)
                scored_recs.append((clue_score, rec))
            scored_recs.sort(key=lambda x: x[0], reverse=True)

            for i, (score, rec) in enumerate(scored_recs[:10]):
                print(f"\n  Recommendation #{i+1} (clue_score={score:.3f}):")
                print(f"    title: {rec.get('title', '')}")
                print(f"    reason: {rec.get('reason', '')}")
                print(f"    angles: {rec.get('angles', [])}")
                print(f"    source: {rec.get('source', '')}")
                print(f"    tag: {rec.get('tag', '')}")

    await db_manager.close()


if __name__ == "__main__":
    asyncio.run(main())