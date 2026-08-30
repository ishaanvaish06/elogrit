import asyncio
import logging
import math
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_maker
from app.models.contest import Contest
from app.models.question_count import QuestionRealTimeCount
from app.models.ranking import Ranking
from app.repositories.contest_repo import ContestRepository
from app.repositories.llm_repo import LlmRepository
from app.repositories.question_count_repo import QuestionRealTimeCountRepository
from app.repositories.question_repo import QuestionRepository
from app.repositories.ranking_repo import RankingRepository
from app.repositories.submission_repo import SubmissionRepository
from app.repositories.user_repo import UserRepository
from app.services.rating.elo_rating_fft import EloRatingFft
from app.services.sourcing.contest_sourcing import ContestQuestionSourcing
from app.services.sourcing.llm_sourcing import LlmSourcing
from app.services.sourcing.ranking_sourcing import RankingSubmissionSourcing
from app.services.sourcing.user_sourcing import UserSourcing

logger = logging.getLogger(__name__)


class ContestService:
    @staticmethod
    async def sync_contest_metadata(title_slug: str) -> Optional[Contest]:
        async with async_session_maker() as session:
            contest_repo = ContestRepository(session)
            question_repo = QuestionRepository(session)

            contest, questions = await ContestQuestionSourcing.fetch_contest_and_questions(title_slug)
            if contest:
                await contest_repo.upsert(contest)
                if questions:
                    await question_repo.upsert_many(questions)
                logger.info(f"Synced metadata for {title_slug} with {len(questions)} questions")
            return contest

    @classmethod
    async def run_contest_prediction(cls, title_slug: str) -> bool:
        """Full contest data ingestion and Elo rating prediction pipeline."""
        logger.info(f"Starting rating prediction pipeline for {title_slug}")

        # 1. Fetch metadata
        contest = await cls.sync_contest_metadata(title_slug)
        if not contest:
            logger.error(f"Could not load contest {title_slug}")
            return False

        # 2. Fetch all rankings & submissions
        rankings, submissions = await RankingSubmissionSourcing.fetch_all_rankings_and_submissions(
            title_slug, region="global_v2", concurrency=8
        )
        if not rankings:
            logger.warning(f"No rankings found for {title_slug}")
            return False

        async with async_session_maker() as session:
            ranking_repo = RankingRepository(session)
            submission_repo = SubmissionRepository(session)
            user_repo = UserRepository(session)
            count_repo = QuestionRealTimeCountRepository(session)

            # Store raw rankings and submissions
            await ranking_repo.bulk_sync_by_contest(title_slug, rankings)
            await submission_repo.bulk_sync_submissions(submissions)

            # 3. Synchronize user ratings & contest history
            user_ids = await ranking_repo.get_user_ids_by_contest(title_slug, positive_score_only=True)
            logger.info(f"Syncing {len(user_ids)} users for {title_slug}")

            # Batch sync users concurrently
            sem = asyncio.Semaphore(10)

            async def sync_single_user(region: str, slug: str):
                async with sem:
                    user = await UserSourcing.fetch_user(region, slug)
                    if user:
                        async with async_session_maker() as user_session:
                            u_repo = UserRepository(user_session)
                            await u_repo.upsert_user(user)

            await asyncio.gather(*[sync_single_user(r, s) for r, s in user_ids[:500]], return_exceptions=True)

            # Fill previous ratings and attended counts
            await ranking_repo.fill_user_old_rating_info(title_slug)

            # 4. Fetch enriched rankings for Elo prediction
            enriched_rankings = await ranking_repo.get_all_by_contest(title_slug)
            if not enriched_rankings:
                logger.warning(f"No enriched rankings available for {title_slug}")
                return False

            ranks = [r.rank for r in enriched_rankings]
            ratings = [r.old_rating if r.old_rating is not None else 1500.0 for r in enriched_rankings]
            attended_counts = [r.attended_contests_count if r.attended_contests_count is not None else 0 for r in enriched_rankings]

            # Run FFT Elo Rating calculation
            expected_ratings, deltas = EloRatingFft.rating_adjustments(
                ranks=ranks,
                ratings=ratings,
                attended_contests_counts=attended_counts,
            )

            # Update predictions on rankings
            for i, r in enumerate(enriched_rankings):
                r.expected_rating = round(float(expected_ratings[i]), 2)
                r.delta_rating = round(float(deltas[i]), 2)

            await session.commit()
            logger.info(f"Calculated Elo ratings for {len(enriched_rankings)} participants in {title_slug}")

            # 5. Calculate Real-Time question solve counts over 90 minutes
            if submissions:
                duration_mins = max(1, contest.duration_seconds // 60)
                start_time = contest.start_time
                q_ids = list({s.question_id for s in submissions})

                question_counts: List[QuestionRealTimeCount] = []
                for q_id in q_ids:
                    q_subs = [s for s in submissions if s.question_id == q_id]
                    for minute in range(1, duration_mins + 1):
                        solve_count = sum(
                            1 for s in q_subs
                            if (s.timepoint - start_time).total_seconds() <= minute * 60
                        )
                        question_counts.append(
                            QuestionRealTimeCount(
                                contest_title_slug=title_slug,
                                question_id=q_id,
                                time_index=minute,
                                count=solve_count,
                            )
                        )
                await count_repo.upsert_counts(question_counts)
                logger.info(f"Calculated {len(question_counts)} minute-by-minute question solve milestones")

        # 6. Sourcing LLM ratings
        try:
            llms, llm_rankings = await LlmSourcing.fetch_and_build_llm_rankings(title_slug)
            if llms:
                async with async_session_maker() as session:
                    llm_repo = LlmRepository(session)
                    await llm_repo.upsert_llms(llms)
                    await llm_repo.upsert_contest_rankings(llm_rankings)
                logger.info(f"Synced {len(llms)} LLM models and rankings for {title_slug}")
        except Exception as e:
            logger.warning(f"LLM data sync skipped or failed for {title_slug}: {e}")

        logger.info(f"Rating prediction completed successfully for {title_slug}")
        return True
