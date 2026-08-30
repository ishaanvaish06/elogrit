# 📊 LeetCode Contest Rating Prediction — Usage Guide

This guide explains how the **LeetCode Contest Analytics & Rating Prediction Engine** works and how users and frontend applications can view predicted ratings, score changes ($\Delta$), and real-time performance curves after a contest.

---

## 🧠 How the Rating Predictor Works

When a LeetCode contest finishes (or during live updates):
1. **Data Ingestion**: The system fetches the participant leaderboard, scores, finish times, penalty times, and submission records from both LeetCode US and CN endpoints.
2. **User History & Rating Enrichment**: Each participant's pre-contest rating ($R_{\text{old}}$) and attended contest count are retrieved.
3. **FFT-Powered Elo Computation**:
   - A naive expectation calculation across 40,000+ contestants requires $O(N^2)$ calculations ($\approx 1.6 \text{ billion operations}$).
   - Instead, this engine computes expected ranks via **discrete convolution in the frequency domain** using Fast Fourier Transform (**FFT**) in $O(M \log M)$ time ($\approx \text{under 1 second}$).
4. **Weighted Delta & Decay Scaling**:
   - Uses LeetCode's historical damping formula: $K = \frac{1}{1 + \sum (5/7)^i}$.
   - Computes expected rating using geometric mean ranking: $\text{MeanRank} = \sqrt{\text{ExpectedRank} \times \text{ActualRank}}$.
   - Calculates $\Delta = (\text{ExpectedRating} - R_{\text{old}}) \times K$.
   - Predicts New Rating: $R_{\text{new}} = R_{\text{old}} + \Delta$.

---

## 🚀 How to View Your Predicted Rating (Step-by-Step)

### Step 1: Start the Backend Server
Make sure the backend is running:
```bash
cd LC
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

---

### Step 2: Trigger Contest Prediction (If not already triggered by Scheduler)
*Note: The built-in background scheduler automatically triggers predictions after every Weekly (Sunday 04:00 UTC) and Biweekly (Saturday 16:00 UTC) contest.*

To trigger or refresh rating predictions manually for a contest (e.g. `weekly-contest-400`):

#### Request:
```bash
curl -X POST "http://localhost:8000/api/v1/leetcode/contests/weekly-contest-400/predict"
```

#### Response:
```json
{
  "message": "Contest weekly-contest-400 rating prediction pipeline triggered in background"
}
```

---

### Step 3: View Predicted Ratings & Leaderboard

#### 🔹 Method A: View the Contest Leaderboard with Predictions
Retrieve paginated rankings for the contest. Each participant record includes `old_rating`, `expected_rating`, `delta_rating`, and `new_rating`.

##### Request:
```bash
curl -X GET "http://localhost:8000/api/v1/leetcode/contests/weekly-contest-400/rankings?limit=25&offset=0"
```

##### Response:
```json
{
  "total": 34210,
  "limit": 25,
  "offset": 0,
  "items": [
    {
      "contest_title_slug": "weekly-contest-400",
      "data_region": "US",
      "user_slug": "tourist",
      "rank": 1,
      "score": 18,
      "finish_time": "2024-06-02T02:45:12Z",
      "attended_contests_count": 52,
      "old_rating": 3480.5,
      "expected_rating": 3570.2,
      "delta_rating": 19.93,
      "new_rating": 3500.43,
      "updated_at": "2024-06-02T04:10:00Z"
    },
    {
      "contest_title_slug": "weekly-contest-400",
      "data_region": "CN",
      "user_slug": "lingling",
      "rank": 2,
      "score": 18,
      "finish_time": "2024-06-02T02:47:30Z",
      "attended_contests_count": 14,
      "old_rating": 2850.0,
      "expected_rating": 3420.0,
      "delta_rating": 42.15,
      "new_rating": 2892.15,
      "updated_at": "2024-06-02T04:10:00Z"
    }
  ]
}
```

---

#### 🔹 Method B: View a User's Real-Time Rank & Rating Progression
View how a user's projected rank and rating evolved minute-by-minute (1 to 90 mins) during the contest:

##### Request:
```bash
curl -X GET "http://localhost:8000/api/v1/leetcode/contests/weekly-contest-400/users/US/tourist/realtime"
```

##### Response:
```json
{
  "contest_title_slug": "weekly-contest-400",
  "data_region": "US",
  "user_slug": "tourist",
  "real_time_ranks": [
    1200, 450, 45, 12, 4, 1, 1, 1, 1
  ],
  "real_time_ratings": [
    3460.1, 3472.5, 3488.2, 3495.0, 3499.1, 3500.43, 3500.43, 3500.43
  ]
}
```

---

#### 🔹 Method C: View User Profile & Contest History

##### 1. User Profile:
```bash
curl -X GET "http://localhost:8000/api/v1/leetcode/users/US/tourist"
```
```json
{
  "data_region": "US",
  "user_slug": "tourist",
  "real_name": "Gennady",
  "avatar_url": "https://assets.leetcode.com/users/tourist/avatar_123.png",
  "attended_contests_count": 52,
  "rating": 3500.43,
  "global_ranking": 1,
  "updated_at": "2024-06-02T04:10:00Z"
}
```

##### 2. User Contest Performance History:
```bash
curl -X GET "http://localhost:8000/api/v1/leetcode/users/US/tourist/history"
```
```json
[
  {
    "data_region": "US",
    "user_slug": "tourist",
    "contest_title_slug": "weekly-contest-400",
    "attended": true,
    "rating": 3500.43,
    "ranking": 1,
    "trend_direction": "UP",
    "problems_solved": 4,
    "total_problems": 4,
    "finish_time_in_seconds": 912,
    "updated_at": "2024-06-02T04:10:00Z"
  }
]
```

---

## 🏷️ Explanation of Rating Fields

| Field | Meaning |
|---|---|
| `rank` | Final placement on the global contest leaderboard (1-indexed). |
| `old_rating` | The user's rating before the contest started. |
| `expected_rating` | The performance rating corresponding to the rank achieved given the participant strength distribution. |
| `delta_rating` | The calculated change ($\Delta$) in rating points (+ for increase, - for decrease). |
| `new_rating` | The predicted new rating: `old_rating + delta_rating`. |
| `attended_contests_count` | Number of previous contests attended (used for weighting rating volatility). |
| `real_time_ranks` | Array of ranks for each minute of the contest window (1..90 mins). |
| `real_time_ratings` | Array of projected ratings at each minute timestamp. |

---

## 💻 Frontend Integration Example (JavaScript / React)

Here is a simple example of how a frontend or web app can fetch and display the user's predicted rating:

```javascript
async function fetchUserPrediction(contestSlug, dataRegion, userSlug) {
  // 1. Fetch contest rankings or realtime progression
  const response = await fetch(
    `http://localhost:8000/api/v1/leetcode/contests/${contestSlug}/rankings?limit=100`
  );
  const data = await response.json();

  // 2. Find the user
  const userRanking = data.items.find(
    (item) =>
      item.user_slug.toLowerCase() === userSlug.toLowerCase() &&
      item.data_region.toUpperCase() === dataRegion.toUpperCase()
  );

  if (userRanking) {
    const isGain = userRanking.delta_rating >= 0;
    console.log(`User: ${userRanking.user_slug}`);
    console.log(`Rank: #${userRanking.rank}`);
    console.log(`Old Rating: ${userRanking.old_rating.toFixed(1)}`);
    console.log(`Delta: ${isGain ? "+" : ""}${userRanking.delta_rating.toFixed(2)}`);
    console.log(`Predicted New Rating: ${userRanking.new_rating.toFixed(2)}`);
  } else {
    console.log("User rating prediction not found.");
  }
}

// Example call:
fetchUserPrediction("weekly-contest-400", "US", "tourist");
```

---

## 🔄 Automated Schedulers

You do not need to manually trigger calculations for upcoming contests. The built-in **APScheduler** ([`app/services/scheduler_service.py`](file:///D:/PROJECT%20T/EntrantHub/LC/app/services/scheduler_service.py)) runs automated tasks:

1. **Every 30 Minutes**: Ingests new upcoming contests and recent problem sets.
2. **Every Sunday at 04:00 UTC**: Fetches Weekly Contest rankings and runs the FFT prediction pipeline.
3. **Every Saturday at 16:00 UTC**: Fetches Biweekly Contest rankings and runs the FFT prediction pipeline.
