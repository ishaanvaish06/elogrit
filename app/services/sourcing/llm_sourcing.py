import logging
from typing import List, Tuple
from app.models.llm import Llm, LlmContestRanking
from app.services.sourcing.client import HttpClient

logger = logging.getLogger(__name__)

LEETCODE_US_GRAPHQL = "https://leetcode.com/graphql"


class LlmSourcing:
    @staticmethod
    async def fetch_contest_llm_ranking(contest_slug: str) -> List[Tuple[Llm, float, float]]:
        query = """
        query contestLlmRanking($contestSlug: String!) {
            contestLlmRanking(contestSlug: $contestSlug) {
                aiModel {
                    companyName
                    logoUrl
                    name
                    info
                    id
                }
                avgScore
                maxScore
            }
        }
        """
        try:
            res = await HttpClient.post_json(
                LEETCODE_US_GRAPHQL,
                {
                    "query": query,
                    "variables": {"contestSlug": contest_slug},
                    "operationName": "contestLlmRanking",
                },
            )
            rankings_data = res.get("data", {}).get("contestLlmRanking") or []
            results = []
            for r in rankings_data:
                ai = r.get("aiModel") or {}
                llm = Llm(
                    id=int(ai.get("id", 0)),
                    name=ai.get("name", ""),
                    logo_url=ai.get("logoUrl", ""),
                    company_name=ai.get("companyName", ""),
                    info=ai.get("info", ""),
                )
                avg_score = float(r.get("avgScore", 0.0))
                max_score = float(r.get("maxScore", 0.0))
                results.append((llm, avg_score, max_score))
            return results
        except Exception as e:
            logger.error(f"Error fetching LLM ranking for {contest_slug}: {e}")
            return []

    @staticmethod
    async def fetch_contest_llm_detail(ai_model_id: int, contest_slug: str) -> Tuple[float, float]:
        query = """
        query contestLlmDetail($aiModelId: ID!, $contestSlug: String!) {
            contestLlmDetail(aiModelId: $aiModelId, contestSlug: $contestSlug) {
                acRate
                avgTriedTimes
            }
        }
        """
        try:
            res = await HttpClient.post_json(
                LEETCODE_US_GRAPHQL,
                {
                    "query": query,
                    "variables": {"aiModelId": str(ai_model_id), "contestSlug": contest_slug},
                    "operationName": "contestLlmDetail",
                },
            )
            detail = res.get("data", {}).get("contestLlmDetail") or {}
            ac_rate = float(detail.get("acRate", 0.0))
            avg_tried_times = float(detail.get("avgTriedTimes", 0.0))
            return ac_rate, avg_tried_times
        except Exception as e:
            logger.error(f"Error fetching LLM detail for model {ai_model_id} in {contest_slug}: {e}")
            return 0.0, 0.0

    @classmethod
    async def fetch_and_build_llm_rankings(cls, contest_slug: str) -> Tuple[List[Llm], List[LlmContestRanking]]:
        rankings_data = await cls.fetch_contest_llm_ranking(contest_slug)
        if not rankings_data:
            return [], []

        llms: List[Llm] = []
        contest_rankings: List[LlmContestRanking] = []

        for llm, avg_score, max_score in rankings_data:
            llms.append(llm)
            ac_rate, avg_tried = await cls.fetch_contest_llm_detail(llm.id, contest_slug)
            cr = LlmContestRanking(
                llm_id=llm.id,
                contest_slug=contest_slug,
                avg_score=avg_score,
                max_score=max_score,
                ac_rate=ac_rate,
                avg_tried_times=avg_tried,
            )
            contest_rankings.append(cr)

        return llms, contest_rankings
