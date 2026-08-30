import gzip
import os
import numpy as np
import pytest
from app.services.rating.elo_rating_fft import EloRatingFft


def load_contest_prediction_data(file_path: str):
    with gzip.open(file_path, "rt", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]

    parsed = [list(map(float, line.split(","))) for line in lines]
    attended_counts = [int(row[0]) for row in parsed]
    ranks = [int(row[1]) for row in parsed]
    old_ratings = [row[2] for row in parsed]
    expected_new_ratings = [row[3] for row in parsed]

    return attended_counts, ranks, old_ratings, expected_new_ratings


def test_elo_rating_fft_accuracy():
    test_data_path = os.path.join(os.path.dirname(__file__), "data", "contest_prediction_1.txt.gz")
    assert os.path.exists(test_data_path), f"Test fixture not found: {test_data_path}"

    attended_counts, ranks, old_ratings, expected_new_ratings = load_contest_prediction_data(test_data_path)

    expected_ratings, deltas = EloRatingFft.rating_adjustments(
        ranks=ranks,
        ratings=old_ratings,
        attended_contests_counts=attended_counts,
    )

    predicted_new_ratings = np.array(old_ratings) + deltas
    errors = np.abs(predicted_new_ratings - np.array(expected_new_ratings))

    rating_delta_precision = 0.05
    max_error = float(np.max(errors))
    assert np.all(errors < rating_delta_precision), (
        f"Elo delta test failed. Max error: {max_error:.4f}, threshold: {rating_delta_precision:.4f}"
    )
