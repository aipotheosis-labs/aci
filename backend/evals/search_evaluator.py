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

# Suppress verbose httpx logging
logging.getLogger("httpx").setLevel(logging.WARNING)


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
            # Set a longer timeout for search requests (120 seconds)
            timeout = httpx.Timeout(120.0)
            with httpx.Client(timeout=timeout) as client:
                response = client.get(
                    f"{self.api_url}/v1/functions/search",
                    params={"intent": intent, "limit": limit},
                    headers=self.headers,
                )
            response.raise_for_status()
            return response.json(), time.time() - start_time
        except httpx.HTTPStatusError as e:
            logger.error(
                f"HTTP error searching functions: {e.response.status_code} - {e.response.text}"
            )
            return [], 0.0
        except httpx.RequestError as e:
            logger.error(f"Request error searching functions: {e}")
            return [], 0.0
        except Exception as e:
            logger.error(f"Unexpected error searching functions: {e}")
            return [], 0.0

    def _find_rank(self, results: list[dict[str, Any]], expected: str) -> int | None:
        """
        Find the rank (1-based) of the expected function in the search results.

        Args:
            results: List of search results (BasicFunctionDefinition format)
            expected: Name of the expected function

        Returns:
            Rank of the expected function (1-based) or None if not found
        """
        expected_lc = expected.lower()
        for i, result in enumerate(results):
            # BasicFunctionDefinition only has 'name' and 'description' fields
            function_name = result.get("name", "")

            if function_name and function_name.lower() == expected_lc:
                return i + 1  # Return 1-based rank
        return None

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
            if rank == 1:
                metrics["correct"] += 1
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
            "correct": metrics["correct"],
            "mrr": metrics["mrr"] / num_samples,
            "response_time": metrics["response_time"],
            "top_k": metrics["top_k"],
            "avg_response_time": metrics["response_time"] / num_samples,
            "total_samples": num_samples,
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

        # Initialize metrics with original naming structure
        eval_metrics = {
            "correct": 0,
            "mrr": 0.0,
            "response_time": 0.0,
            "top_k": {1: 0, 3: 0, 5: 0},
        }
        incorrect_results = []
        detailed_results = []

        # Get the subset of data to evaluate
        data_to_evaluate = dataset.head(num_samples)

        with tqdm(total=len(data_to_evaluate), desc="Evaluating intents") as pbar:
            for _, row in data_to_evaluate.iterrows():
                # Get search results
                results, response_time = self._search(row["synthetic_output"])

                # Find rank of expected function
                rank = self._find_rank(results, row["function_name"])

                # Process results for tracking (BasicFunctionDefinition format)
                processed_results = []
                for idx, result in enumerate(results):
                    function_name = result.get("name", "Unknown")
                    description = result.get("description", "")

                    processed_results.append(
                        {
                            "rank": idx + 1,
                            "name": function_name,
                            "score": 0,  # BasicFunctionDefinition doesn't include score
                            "found": function_name.lower() == row["function_name"].lower(),
                            "description": description,
                        }
                    )

                # Update metrics using helper method
                self._update_metrics(eval_metrics, rank, response_time)

                # Track incorrect results
                if rank is None or rank > 1:
                    incorrect_results.append(
                        {
                            "intent": row["synthetic_output"],
                            "expected": row["function_name"],
                            "expected_app": row.get("app_name", "Unknown"),
                            "actual_rank": rank,
                            "results": processed_results[:5],  # Only keep top 5 for analysis
                        }
                    )

                # Store detailed results
                detailed_results.append(
                    {
                        "synthetic_output": row["synthetic_output"],
                        "expected_function": row["function_name"],
                        "rank": rank,
                        "response_time": response_time,
                        "results": processed_results,
                    }
                )

                pbar.update(1)

        # Calculate final metrics using helper method
        final_metrics = self._calculate_final_metrics(eval_metrics, num_samples, incorrect_results)

        # Add detailed results
        final_metrics["detailed_results"] = detailed_results

        return final_metrics

    def test_connection(self) -> bool:
        """
        Test if the API connection is working.

        Returns:
            True if connection is successful, False otherwise
        """
        try:
            timeout = httpx.Timeout(10.0)
            with httpx.Client(timeout=timeout) as client:
                # Test with a simple health check or apps endpoint
                response = client.get(f"{self.api_url}/health")
                if response.status_code == 200:
                    logger.info("✅ API connection test successful")
                    return True
                else:
                    logger.error(f"❌ API health check failed: {response.status_code}")
                    return False
        except Exception as e:
            logger.error(f"❌ API connection test failed: {e}")
            return False

    def _search_functions(self, intent: str, limit: int = 5) -> list[dict[str, Any]]:
        """
        Public method to search functions (used for testing in evaluation pipeline).

        Args:
            intent: The search query/intent
            limit: Maximum number of results to return

        Returns:
            List of search results
        """
        results, _ = self._search(intent, limit)
        return results
