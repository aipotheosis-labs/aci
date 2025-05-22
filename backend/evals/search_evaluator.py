import logging
import time
from typing import Any

import httpx
import pandas as pd
from dotenv import load_dotenv
from tqdm import tqdm

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SearchEvaluator:
    """
    Evaluates the performance of function search using synthetic intents.

    This evaluator:
    1. Takes a dataset of synthetic intents and their expected function matches
    2. Sends each intent to the search API
    3. Calculates various metrics including accuracy, MRR, and response time
    4. Tracks incorrect results for analysis
    """

    def __init__(self, api_url: str, api_key: str):
        """
        Initialize the evaluator with API configuration.

        Args:
            api_url: Base URL of the search API
            api_key: API key for authentication
        """
        self.api_url = api_url
        self.headers = {"X-API-KEY": api_key}

    def _search(self, intent: str, limit: int = 5) -> tuple[list[dict[str, Any]], float]:
        """
        Send a search request to the API and measure response time.

        Args:
            intent: The search query/intent
            limit: Maximum number of results to return

        Returns:
            Tuple of (search results, response time in seconds)
        """
        try:
            start_time = time.time()
            with httpx.Client() as client:
                response = client.get(
                    f"{self.api_url}/v1/functions/search",
                    params={"intent": intent, "limit": str(limit), "format": "basic"},
                    headers=self.headers,
                )
            response.raise_for_status()
            return response.json(), time.time() - start_time
        except httpx.HTTPError as e:
            logger.error(f"Error searching functions: {e}")
            return [], 0.0

    def _find_rank(self, results: list[dict[str, Any]], expected: str) -> int | None:
        """
        Find the rank (1-based) of the expected function in the search results.

        Args:
            results: List of search results
            expected: Name of the expected function

        Returns:
            Rank of the expected function (1-based) or None if not found
        """
        expected_lc = expected.lower()
        return next(
            (i + 1 for i, r in enumerate(results) if r["name"].lower() == expected_lc),
            None,
        )

    def _update_metrics(
        self, metrics: dict[str, Any], rank: int | None, response_time: float
    ) -> None:
        """
        Update running metrics with results from a single evaluation.

        Args:
            metrics: Dictionary of running metrics to update
            rank: Rank of the expected function (1-based) or None
            response_time: Response time in seconds
        """
        metrics["response_time"] += response_time
        if rank:
            metrics["mrr"] += 1.0 / rank
            for k in metrics["top_k"]:
                if rank <= k:
                    metrics["top_k"][k] += 1

    def _calculate_final_metrics(
        self, metrics: dict[str, Any], num_samples: int, incorrect_results: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """
        Calculate final metrics from running totals.

        Args:
            metrics: Dictionary of running metrics
            num_samples: Total number of samples evaluated
            incorrect_results: List of incorrect predictions for analysis

        Returns:
            Dictionary of final metrics
        """
        return {
            "accuracy": metrics["top_k"][1] / num_samples,
            "mrr": metrics["mrr"] / num_samples,
            "top_k_accuracy": {k: v / num_samples for k, v in metrics["top_k"].items()},
            "avg_response_time": metrics["response_time"] / num_samples,
            "total_samples": num_samples,
            "correct_predictions": metrics["top_k"][1],
            "incorrect_results": incorrect_results,
        }

    def evaluate_dataset(
        self, dataset: pd.DataFrame, num_samples: int | None = None
    ) -> dict[str, Any]:
        """
        Evaluate search performance on a dataset of synthetic intents.

        Args:
            dataset: DataFrame containing synthetic intents and expected functions
            num_samples: Number of samples to evaluate (default: all)

        Returns:
            Dictionary containing evaluation metrics
        """
        if num_samples is None:
            num_samples = len(dataset)

        # Initialize metrics
        metrics = {"correct": 0, "mrr": 0.0, "response_time": 0.0, "top_k": {1: 0, 3: 0, 5: 0}}
        incorrect_results = []

        # Evaluate each sample
        for _, row in tqdm(
            dataset.head(num_samples).iterrows(),
            desc="Evaluating intents",
            total=num_samples,
        ):
            # Get search results
            results, response_time = self._search(row["synthetic_output"])

            # Process results
            found = False
            results = [
                {
                    "rank": idx + 1,
                    **r,
                    "found": found or (found := r["name"].lower() == row["function_name"].lower()),
                }
                for idx, r in enumerate(results)
            ]
            rank = self._find_rank(results, row["function_name"])

            # Update metrics
            self._update_metrics(metrics, rank, response_time)

            # Track incorrect results
            if rank is None or rank > 1:
                incorrect_results.append(
                    {
                        "intent": row["synthetic_output"],
                        "expected": row["function_name"],
                        "results": results,
                    }
                )

        return self._calculate_final_metrics(metrics, num_samples, incorrect_results)
