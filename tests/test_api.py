from datetime import datetime, timezone
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.contest import Contest
from app.models.question import Question
from app.models.ranking import Ranking
from app.models.user import User


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


@pytest.mark.asyncio
async def test_root(client: AsyncClient):
    response = await client.get("/")
    assert response.status_code == 200
    assert "running" in response.json()["message"]


@pytest.mark.asyncio
async def test_contests_crud_and_endpoints(client: AsyncClient, db_session: AsyncSession):
    # 1. Insert sample contest
    contest = Contest(
        title_slug="weekly-contest-400",
        start_time=datetime(2024, 6, 2, 2, 30, tzinfo=timezone.utc),
        duration_seconds=5400,
        title_us="Weekly Contest 400",
        title_cn="第 400 场周赛",
        unrated_us=False,
        unrated_cn=False,
    )
    db_session.add(contest)

    # 2. Insert sample questions
    q1 = Question(
        id=1001,
        contest_title_slug="weekly-contest-400",
        id_us=1001,
        id_cn=1001,
        title_slug="minimum-chairs",
        title_us="Minimum Chairs",
        title_cn="最少椅子数",
        difficulty=1,
        credit=3,
    )
    db_session.add(q1)

    # 3. Insert sample ranking
    r1 = Ranking(
        contest_title_slug="weekly-contest-400",
        data_region="US",
        user_slug="tourist",
        rank=1,
        score=18,
        finish_time=datetime(2024, 6, 2, 2, 45, tzinfo=timezone.utc),
        attended_contests_count=50,
        old_rating=3500.0,
        expected_rating=3520.0,
        delta_rating=20.0,
    )
    db_session.add(r1)

    # 4. Insert sample user
    user = User(
        data_region="US",
        user_slug="tourist",
        real_name="Gennady",
        avatar_url="https://avatar.url/tourist.png",
        attended_contests_count=50,
        rating=3520.0,
        global_ranking=1,
    )
    db_session.add(user)

    await db_session.commit()

    # Test list contests
    res = await client.get("/api/v1/leetcode/contests")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 1
    assert data["items"][0]["title_slug"] == "weekly-contest-400"
    assert data["items"][0]["contest_type"] == "Weekly"

    # Test get single contest
    res = await client.get("/api/v1/leetcode/contests/weekly-contest-400")
    assert res.status_code == 200
    assert res.json()["title_us"] == "Weekly Contest 400"

    # Test get contest questions
    res = await client.get("/api/v1/leetcode/contests/weekly-contest-400/questions")
    assert res.status_code == 200
    questions = res.json()
    assert len(questions) == 1
    assert questions[0]["title_slug"] == "minimum-chairs"

    # Test get contest rankings
    res = await client.get("/api/v1/leetcode/contests/weekly-contest-400/rankings")
    assert res.status_code == 200
    rankings = res.json()
    assert rankings["total"] == 1
    assert rankings["items"][0]["user_slug"] == "tourist"
    assert rankings["items"][0]["delta_rating"] == 20.0

    # Test get user profile
    res = await client.get("/api/v1/leetcode/users/US/tourist")
    assert res.status_code == 200
    assert res.json()["real_name"] == "Gennady"
    assert res.json()["rating"] == 3520.0
