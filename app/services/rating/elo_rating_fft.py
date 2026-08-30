import math
from typing import List, Sequence, Tuple
import numpy as np


class EloRatingFft:
    """LeetCode Elo Rating calculation engine using Fast Fourier Transform (FFT).

    Matches the exact algorithm and precision of the LeetCode rating prediction model:
    - O(M log M) expected ranking convolution instead of O(N^2)
    - Dynamic delta coefficient scaling based on attended contest history
    - Geometric mean expected rank interpolation via binary search
    """

    RATING_GRANULARITY: int = 100
    MIN_RATING: float = 0.0
    MAX_RATING: float = 4000.0
    MAX_RATING_SCALED: int = int(MAX_RATING * RATING_GRANULARITY)  # 400,000
    CONVOLUTION_ARRAY_SIZE: int = 2 * MAX_RATING_SCALED + 1        # 800,001
    MAX_SIGMA_INDEX: int = 100

    # Power of two FFT size >= CONVOLUTION_ARRAY_SIZE
    FFT_ARRAY_SIZE: int = 1 << (CONVOLUTION_ARRAY_SIZE - 1).bit_length()  # 1,048,576

    # Precomputed sigma prefix sums for attended contest decay factor
    _sigma_prefix_sums: np.ndarray = None
    _win_prob_fft: np.ndarray = None

    @classmethod
    def _initialize(cls) -> None:
        if cls._sigma_prefix_sums is not None:
            return

        # Precompute sigma prefix sums: sigma_i = (5/7)^i + sigma_{i-1}
        sigmas = np.zeros(cls.MAX_SIGMA_INDEX + 1, dtype=np.float64)
        sigmas[0] = 1.0
        for i in range(1, cls.MAX_SIGMA_INDEX + 1):
            sigmas[i] = math.pow(5.0 / 7.0, i) + sigmas[i - 1]
        cls._sigma_prefix_sums = sigmas

        # Precompute win probability curve: 1 / (1 + 10^(i / (400 * RatingGranularity)))
        indices = np.arange(-cls.MAX_RATING_SCALED, cls.MAX_RATING_SCALED + 1, dtype=np.float64)
        win_prob_curve = 1.0 / (1.0 + np.power(10.0, indices / (400.0 * cls.RATING_GRANULARITY)))

        # Pad with zeros to FFT size
        win_prob_padded = np.zeros(cls.FFT_ARRAY_SIZE, dtype=np.float64)
        win_prob_padded[: len(win_prob_curve)] = win_prob_curve

        cls._win_prob_fft = np.fft.fft(win_prob_padded)

    @classmethod
    def delta_coefficient(cls, attended_contests_count: int) -> float:
        cls._initialize()
        if attended_contests_count > cls.MAX_SIGMA_INDEX:
            return 2.0 / 9.0
        return 1.0 / (1.0 + cls._sigma_prefix_sums[attended_contests_count])

    @classmethod
    def pre_calc_convolution(cls, ratings: np.ndarray) -> np.ndarray:
        cls._initialize()
        rating_histogram = np.zeros(cls.CONVOLUTION_ARRAY_SIZE, dtype=np.float64)

        # Scale ratings into discrete histogram bins
        scaled_indices = np.rint(ratings * cls.RATING_GRANULARITY).astype(int)
        np.add.at(rating_histogram, scaled_indices, 1.0)

        # Pad with zeros to FFT size
        histogram_padded = np.zeros(cls.FFT_ARRAY_SIZE, dtype=np.float64)
        histogram_padded[: cls.CONVOLUTION_ARRAY_SIZE] = rating_histogram

        rating_histogram_fft = np.fft.fft(histogram_padded)
        convolution_freq = cls._win_prob_fft * rating_histogram_fft
        convolution_time = np.fft.ifft(convolution_freq).real

        return convolution_time[: cls.CONVOLUTION_ARRAY_SIZE]

    @classmethod
    def _binary_search_expected_rating(cls, convolution: np.ndarray, mean_rank: float) -> int:
        lo = 0
        hi = cls.MAX_RATING_SCALED
        while lo <= hi:
            mid = (lo + hi) >> 1
            search_value = convolution[mid + cls.MAX_RATING_SCALED] + 1.0
            if search_value < mean_rank:
                hi = mid - 1
            else:
                lo = mid + 1
        return lo

    @classmethod
    def expected_rating(cls, rank: int, rating: float, convolution: np.ndarray) -> float:
        rating_index = int(round(rating * cls.RATING_GRANULARITY))
        expected_rank = convolution[rating_index + cls.MAX_RATING_SCALED] + 0.5
        mean_rank = math.sqrt(expected_rank * rank)
        return cls._binary_search_expected_rating(convolution, mean_rank) / cls.RATING_GRANULARITY

    @classmethod
    def rating_adjustments(
        cls,
        ranks: Sequence[int],
        ratings: Sequence[float],
        attended_contests_counts: Sequence[int],
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Calculates expected ratings and rating deltas for all participants in a contest.

        Args:
            ranks: 1-indexed contest rankings
            ratings: Old ratings before contest (0.0 to 4000.0)
            attended_contests_counts: Historical count of attended contests

        Returns:
            Tuple of (expected_ratings, weighted_deltas)
        """
        cls._initialize()
        n = len(ranks)
        if not (len(ratings) == n and len(attended_contests_counts) == n):
            raise ValueError(f"Array lengths must match: ranks={len(ranks)}, ratings={len(ratings)}, counts={len(attended_contests_counts)}")

        ratings_arr = np.asarray(ratings, dtype=np.float64)
        ranks_arr = np.asarray(ranks, dtype=np.int32)
        counts_arr = np.asarray(attended_contests_counts, dtype=np.int32)

        if np.any(ratings_arr < cls.MIN_RATING) or np.any(ratings_arr > cls.MAX_RATING):
            raise ValueError(f"All ratings must be between {cls.MIN_RATING} and {cls.MAX_RATING}")

        convolution = cls.pre_calc_convolution(ratings_arr)
        coefficients = np.array([cls.delta_coefficient(c) for c in counts_arr], dtype=np.float64)

        expected_ratings = np.empty(n, dtype=np.float64)
        for i in range(n):
            expected_ratings[i] = cls.expected_rating(ranks_arr[i], ratings_arr[i], convolution)

        deltas = expected_ratings - ratings_arr
        weighted_deltas = deltas * coefficients

        return expected_ratings, weighted_deltas

    @classmethod
    def compute_real_time_ratings_matrix(
        cls,
        ratings: Sequence[float],
        attended_contests_counts: Sequence[int],
        real_time_ranks_matrix: Sequence[Sequence[int]],
    ) -> List[List[float]]:
        """Computes real-time rating progressions for each user across all minute marks."""
        cls._initialize()
        ratings_arr = np.asarray(ratings, dtype=np.float64)
        counts_arr = np.asarray(attended_contests_counts, dtype=np.int32)

        convolution = cls.pre_calc_convolution(ratings_arr)
        coefficients = np.array([cls.delta_coefficient(c) for c in counts_arr], dtype=np.float64)

        results: List[List[float]] = []
        for i in range(len(ratings_arr)):
            rating = ratings_arr[i]
            coeff = coefficients[i]
            user_ranks = real_time_ranks_matrix[i]
            user_ratings: List[float] = []
            for rank in user_ranks:
                delta = cls.expected_rating(rank, rating, convolution) - rating
                weighted_delta = delta * coeff
                user_ratings.append(round(rating + weighted_delta, 2))
            results.append(user_ratings)

        return results
