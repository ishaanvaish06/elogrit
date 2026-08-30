import asyncio
import logging
from typing import Dict, List, Optional, Tuple
from app.models.user import User, UserContestHistory
from app.services.sourcing.client import HttpClient

logger = logging.getLogger(__name__)

LEETCODE_US_GRAPHQL = "https://leetcode.com/graphql"
LEETCODE_CN_GRAPHQL = "https://leetcode.cn/graphql"


class UserSourcing:
    @staticmethod
    async def fetch_user_profile_us(user_slug: str) -> Optional[Tuple[str, str]]:
        query = """
        query userPublicProfile($username: String!) {
            matchedUser(username: $username) {
                profile {
                    realName
                    userAvatar
                }
            }
        }
        """
        try:
            res = await HttpClient.post_json(
                LEETCODE_US_GRAPHQL,
                {"query": query, "variables": {"username": user_slug}, "operationName": "userPublicProfile"},
            )
            matched = res.get("data", {}).get("matchedUser")
            if matched and matched.get("profile"):
                prof = matched["profile"]
                return prof.get("realName", "") or "", prof.get("userAvatar", "") or ""
            return None
        except Exception as e:
            logger.error(f"Error fetching US user profile for {user_slug}: {e}")
            return None

    @staticmethod
    async def fetch_user_profile_cn(user_slug: str) -> Optional[Tuple[str, str]]:
        query = """
        query userProfilePublicProfile($userSlug: String!) {
            userProfilePublicProfile(userSlug: $userSlug) {
                profile {
                    realName
                    userAvatar
                }
            }
        }
        """
        try:
            res = await HttpClient.post_json(
                LEETCODE_CN_GRAPHQL,
                {"query": query, "variables": {"userSlug": user_slug}, "operationName": "userProfilePublicProfile"},
            )
            data = res.get("data", {}).get("userProfilePublicProfile")
            if data and data.get("profile"):
                prof = data["profile"]
                return prof.get("realName", "") or "", prof.get("userAvatar", "") or ""
            return None
        except Exception as e:
            logger.error(f"Error fetching CN user profile for {user_slug}: {e}")
            return None

    @staticmethod
    async def fetch_user_contest_ranking(data_region: str, user_slug: str) -> Optional[Dict[str, float]]:
        is_cn = data_region.upper() == "CN"
        url = LEETCODE_CN_GRAPHQL if is_cn else LEETCODE_US_GRAPHQL

        if is_cn:
            query = """
            query userContestRankingInfo($userSlug: String!) {
                userContestRanking(userSlug: $userSlug) {
                    attendedContestsCount
                    rating
                    globalRanking
                }
            }
            """
            variables = {"userSlug": user_slug}
        else:
            query = """
            query getContestRankingData($username: String!) {
                userContestRanking(username: $username) {
                    attendedContestsCount
                    rating
                    globalRanking
                }
            }
            """
            variables = {"username": user_slug}

        try:
            res = await HttpClient.post_json(url, {"query": query, "variables": variables})
            ranking_data = res.get("data", {}).get("userContestRanking")
            if ranking_data:
                return {
                    "attendedContestsCount": int(ranking_data.get("attendedContestsCount", 0)),
                    "rating": float(ranking_data.get("rating", 1500.0)),
                    "globalRanking": int(ranking_data.get("globalRanking", 0)),
                }
            return None
        except Exception as e:
            logger.error(f"Error fetching contest ranking for {data_region}/{user_slug}: {e}")
            return None

    @classmethod
    async def fetch_user(cls, data_region: str, user_slug: str) -> Optional[User]:
        region = data_region.upper()
        slug = user_slug.lower()

        if region == "CN":
            profile = await cls.fetch_user_profile_cn(slug)
        else:
            profile = await cls.fetch_user_profile_us(slug)

        if not profile:
            return None

        real_name, avatar_url = profile
        ranking_info = await cls.fetch_user_contest_ranking(region, slug)

        return User(
            data_region=region,
            user_slug=slug,
            real_name=real_name,
            avatar_url=avatar_url,
            attended_contests_count=ranking_info.get("attendedContestsCount") if ranking_info else None,
            rating=ranking_info.get("rating") if ranking_info else None,
            global_ranking=ranking_info.get("globalRanking") if ranking_info else None,
        )

    @classmethod
    async def fetch_user_contest_history(cls, data_region: str, user_slug: str) -> List[UserContestHistory]:
        region = data_region.upper()
        slug = user_slug.lower()
        is_cn = region == "CN"
        url = LEETCODE_CN_GRAPHQL if is_cn else LEETCODE_US_GRAPHQL

        query = """
        query userContestRankingInfo($username: String!) {
            userContestRankingHistory(username: $username) {
                attended
                rating
                ranking
                trendDirection
                problemsSolved
                totalProblems
                finishTimeInSeconds
                contest {
                    title
                    titleSlug
                    startTime
                }
            }
        }
        """
        try:
            res = await HttpClient.post_json(
                url,
                {"query": query, "variables": {"username": slug}},
            )
            history_data = res.get("data", {}).get("userContestRankingHistory", [])
            if not history_data:
                return []

            histories: List[UserContestHistory] = []
            for h in history_data:
                contest = h.get("contest") or {}
                contest_slug = contest.get("titleSlug", "")
                if not contest_slug:
                    continue

                hist = UserContestHistory(
                    data_region=region,
                    user_slug=slug,
                    contest_title_slug=contest_slug,
                    attended=h.get("attended", True),
                    rating=float(h.get("rating", 1500.0)),
                    ranking=int(h.get("ranking", 0)),
                    trend_direction=h.get("trendDirection", ""),
                    problems_solved=int(h.get("problemsSolved", 0)),
                    total_problems=int(h.get("totalProblems", 4)),
                    finish_time_in_seconds=int(h.get("finishTimeInSeconds", 0)),
                )
                histories.append(hist)
            return histories
        except Exception as e:
            logger.error(f"Error fetching contest history for {region}/{slug}: {e}")
            return []
