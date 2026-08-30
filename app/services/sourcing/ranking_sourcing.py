import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import List, Optional, Tuple

from app.models.ranking import Ranking
from app.models.submission import Submission
from app.services.sourcing.client import HttpClient

logger = logging.getLogger(__name__)

PAGE_SIZE = 25


class RankingSubmissionSourcing:
    @staticmethod
    def ranking_api_url(
        title_slug: str,
        region: str = "global_v2",
        page: int = 1,
        is_cn: bool = False,
    ) -> str:
        base = "https://leetcode.cn" if is_cn else "https://leetcode.com"
        return f"{base}/contest/api/ranking/{title_slug}/?region={region}&pagination={page}"

    @classmethod
    async def fetch_user_count(
        cls,
        title_slug: str,
        region: str = "global_v2",
        is_cn: bool = False,
    ) -> Optional[int]:
        url = cls.ranking_api_url(title_slug, region=region, page=1, is_cn=is_cn)
        try:
            text = await HttpClient.get(url)
            data = json.loads(text)
            return data.get("user_num")
        except Exception as e:
            logger.error(f"Error fetching user count for {title_slug}: {e}")
            return None

    @classmethod
    async def fetch_page(
        cls,
        title_slug: str,
        region: str = "global_v2",
        page: int = 1,
        is_cn: bool = False,
    ) -> Tuple[List[Ranking], List[Submission]]:
        url = cls.ranking_api_url(title_slug, region=region, page=page, is_cn=is_cn)
        try:
            text = await HttpClient.get(url)
            data = json.loads(text)
        except Exception as e:
            logger.error(f"Error fetching ranking page {page} for {title_slug}: {e}")
            return [], []

        rankings: List[Ranking] = []
        submissions: List[Submission] = []
        rank_offset = 1 if region == "global_v2" else 0

        for r_json in data.get("total_rank", []):
            data_region = r_json.get("data_region", "US")
            user_slug = r_json.get("user_slug", "").lower()
            if not user_slug:
                continue

            finish_time_epoch = r_json.get("finish_time", 0)
            finish_time = datetime.fromtimestamp(finish_time_epoch, tz=timezone.utc)
            rank = int(r_json.get("rank", 0)) + rank_offset
            score = int(r_json.get("score", 0))

            ranking = Ranking(
                contest_title_slug=title_slug,
                data_region=data_region.upper(),
                user_slug=user_slug,
                rank=rank,
                score=score,
                finish_time=finish_time,
            )
            rankings.append(ranking)

            subs_dict = r_json.get("submissions", {})
            if isinstance(subs_dict, dict):
                for q_id_str, s_info in subs_dict.items():
                    sub_id = int(s_info.get("submission_id", 0))
                    if sub_id == 0:
                        continue
                    date_epoch = s_info.get("date", 0)
                    timepoint = datetime.fromtimestamp(date_epoch, tz=timezone.utc)
                    sub = Submission(
                        id=sub_id,
                        question_id=int(q_id_str),
                        data_region=data_region.upper(),
                        user_slug=user_slug,
                        timepoint=timepoint,
                        fail_count=int(s_info.get("fail_count", 0)),
                        lang=s_info.get("lang", ""),
                    )
                    submissions.append(sub)

        return rankings, submissions

    @classmethod
    async def fetch_all_rankings_and_submissions(
        cls,
        title_slug: str,
        region: str = "global_v2",
        is_cn: bool = False,
        concurrency: int = 10,
    ) -> Tuple[List[Ranking], List[Submission]]:
        user_num = await cls.fetch_user_count(title_slug, region=region, is_cn=is_cn)
        if not user_num:
            logger.warning(f"Could not determine user count for {title_slug}")
            return [], []

        max_page = (user_num + PAGE_SIZE - 1) // PAGE_SIZE
        logger.info(f"Fetching {max_page} ranking pages for {title_slug} (total users: {user_num})")

        all_rankings: List[Ranking] = []
        all_submissions: List[Submission] = []

        semaphore = asyncio.Semaphore(concurrency)

        async def fetch_with_sem(page: int):
            async with semaphore:
                return await cls.fetch_page(title_slug, region=region, page=page, is_cn=is_cn)

        tasks = [fetch_with_sem(p) for p in range(1, max_page + 1)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for res in results:
            if isinstance(res, tuple):
                r_page, s_page = res
                all_rankings.extend(r_page)
                all_submissions.extend(s_page)
            else:
                logger.error(f"Page fetch encountered error: {res}")

        logger.info(f"Fetched {len(all_rankings)} rankings and {len(all_submissions)} submissions for {title_slug}")
        return all_rankings, all_submissions
