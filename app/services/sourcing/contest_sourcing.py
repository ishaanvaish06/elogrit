import asyncio
import json
import logging
import re
from datetime import datetime, timezone
from typing import List, Optional, Tuple

from app.models.contest import Contest
from app.models.question import Question
from app.services.sourcing.client import HttpClient

logger = logging.getLogger(__name__)

LEETCODE_US_BASE = "https://leetcode.com"
LEETCODE_CN_BASE = "https://leetcode.cn"
LEETCODE_US_GRAPHQL = f"{LEETCODE_US_BASE}/graphql"
LEETCODE_CN_GRAPHQL = f"{LEETCODE_CN_BASE}/graphql"


class ContestQuestionSourcing:
    @staticmethod
    async def fetch_upcoming_contest_slugs() -> List[str]:
        try:
            html = await HttpClient.get(f"{LEETCODE_US_BASE}/contest/")
            build_id_match = re.search(r'"buildId":\s*"(.*?)"', html)
            if not build_id_match:
                logger.warning("Could not find buildId on contest homepage")
                return []

            build_id = build_id_match.group(1)
            json_text = await HttpClient.get(f"{LEETCODE_US_BASE}/_next/data/{build_id}/contest.json")
            data = json.loads(json_text)

            top_two = data.get("pageProps", {}).get("topTwoContests", [])
            return [c["titleSlug"] for c in top_two if "titleSlug" in c]
        except Exception as e:
            logger.error(f"Error fetching upcoming contest slugs: {e}")
            return []

    @staticmethod
    async def fetch_past_contest_slugs(page: int = 1) -> List[str]:
        query = """
        query pastContests($pageNo: Int) {
            pastContests(pageNo: $pageNo) {
                data { title titleSlug startTime duration }
            }
        }
        """
        try:
            res = await HttpClient.post_json(
                LEETCODE_US_GRAPHQL,
                {"query": query, "variables": {"pageNo": page}},
            )
            contests_data = res.get("data", {}).get("pastContests", {}).get("data", [])
            return [c["titleSlug"] for c in contests_data if "titleSlug" in c]
        except Exception as e:
            logger.error(f"Error fetching past contest slugs for page {page}: {e}")
            return []

    @staticmethod
    async def fetch_contest_detail_graphql(title_slug: str, is_cn: bool = False) -> dict:
        url = LEETCODE_CN_GRAPHQL if is_cn else LEETCODE_US_GRAPHQL
        query = """
        query contestDetailPage($contestSlug: String!) {
            contestDetailPage(contestSlug: $contestSlug) {
                startTime
                duration
                titleSlug
                title
                discussUrl
                registerUserNum
            }
        }
        """
        try:
            res = await HttpClient.post_json(
                url,
                {
                    "query": query,
                    "variables": {"contestSlug": title_slug},
                    "operationName": "contestDetailPage",
                },
            )
            return res.get("data", {}).get("contestDetailPage", {}) or {}
        except Exception as e:
            logger.error(f"Error fetching GraphQL contest detail for {title_slug} (is_cn={is_cn}): {e}")
            return {}

    @staticmethod
    async def fetch_contest_info_rest(title_slug: str, is_cn: bool = False) -> dict:
        base = LEETCODE_CN_BASE if is_cn else LEETCODE_US_BASE
        url = f"{base}/contest/api/info/{title_slug}/"
        try:
            text = await HttpClient.get(url)
            return json.loads(text)
        except Exception as e:
            logger.error(f"Error fetching REST contest info for {title_slug} (is_cn={is_cn}): {e}")
            return {}

    @classmethod
    async def fetch_contest_and_questions(cls, title_slug: str) -> Tuple[Optional[Contest], List[Question]]:
        us_detail_f = cls.fetch_contest_detail_graphql(title_slug, is_cn=False)
        cn_detail_f = cls.fetch_contest_detail_graphql(title_slug, is_cn=True)
        us_info_f = cls.fetch_contest_info_rest(title_slug, is_cn=False)
        cn_info_f = cls.fetch_contest_info_rest(title_slug, is_cn=True)

        us_detail, cn_detail, us_info, cn_info = await asyncio.gather(
            us_detail_f, cn_detail_f, us_info_f, cn_info_f
        )

        if not us_detail and not us_info:
            logger.warning(f"No contest data received for {title_slug}")
            return None, []

        start_time_epoch = us_detail.get("startTime") or us_info.get("contest", {}).get("start_time", 0)
        start_time = datetime.fromtimestamp(start_time_epoch, tz=timezone.utc)
        duration = us_detail.get("duration") or us_info.get("contest", {}).get("duration", 5400)

        contest = Contest(
            title_slug=title_slug,
            start_time=start_time,
            duration_seconds=duration,
            title_us=us_detail.get("title") or us_info.get("contest", {}).get("title", title_slug),
            title_cn=cn_detail.get("title") or cn_info.get("contest", {}).get("title", title_slug),
            unrated_us=us_info.get("unrated", False),
            unrated_cn=cn_info.get("unrated", False),
            ranking_updated_us=us_info.get("ranking_updated", False),
            ranking_updated_cn=cn_info.get("ranking_updated", False),
            register_user_num_us=us_detail.get("registerUserNum", 0),
            register_user_num_cn=cn_detail.get("registerUserNum", 0),
            user_num_us=us_info.get("user_num"),
            user_num_cn=cn_info.get("user_num"),
            discuss_url_us=us_detail.get("discussUrl"),
            discuss_url_cn=cn_detail.get("discussUrl"),
        )

        us_questions = us_info.get("questions", [])
        cn_questions = cn_info.get("questions", [])

        questions: List[Question] = []
        for i, uq in enumerate(us_questions):
            cq = cn_questions[i] if i < len(cn_questions) else {}
            q = Question(
                id=int(uq.get("question_id", uq.get("id", 0))),
                contest_title_slug=title_slug,
                id_us=int(uq.get("id", 0)),
                id_cn=int(cq.get("id", 0)),
                title_slug=uq.get("title_slug", ""),
                title_us=uq.get("title", ""),
                title_cn=cq.get("title", uq.get("title", "")),
                difficulty=int(uq.get("difficulty", 1)),
                credit=int(uq.get("credit", 0)),
            )
            questions.append(q)

        return contest, questions
