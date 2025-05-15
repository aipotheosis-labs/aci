import json
import logging
import os
import shutil
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import requests
from datasets import load_dataset
from dotenv import load_dotenv
from huggingface_hub import HfApi
from tqdm import tqdm

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SearchEvaluationPipeline:
    def __init__(self, api_url: str, api_key: str):
        self.api_url = api_url
        self.headers = {"X-API-KEY": api_key}
        self.hf_api = HfApi(token=os.getenv("EVALS_HF_TOKEN"))

    def _search(self, intent: str, limit: int = 5) -> tuple[list[dict[str, Any]], float]:
        try:
            start_time = time.time()
            response = requests.get(
                f"{self.api_url}/v1/functions/search",
                params={"intent": intent, "limit": str(limit), "format": "basic"},
                headers=self.headers,
            )
            response.raise_for_status()
            return response.json(), time.time() - start_time
        except requests.exceptions.RequestException as e:
            logger.error(f"Error searching functions: {e}")
            return [], 0.0

    def _find_rank(self, results: list[dict[str, Any]], expected: str) -> int | None:
        """Find 1-based rank of expected function in results."""
        return next((i + 1 for i, r in enumerate(results) if r["name"] == expected), None)

    def _update_metrics(
        self, metrics: dict[str, Any], rank: int | None, response_time: float
    ) -> None:
        """Update running metrics with results from a single evaluation."""
        metrics["response_time"] += response_time
        if rank:
            metrics["correct"] += 1
            metrics["mrr"] += 1.0 / rank
            for k in metrics["top_k"]:
                if rank <= k:
                    metrics["top_k"][k] += 1

    def _calculate_final_metrics(
        self, metrics: dict[str, Any], num_samples: int, incorrect_results: list
    ) -> dict[str, Any]:
        """Calculate final metrics from running totals."""
        return {
            "accuracy": metrics["correct"] / num_samples,
            "mrr": metrics["mrr"] / num_samples,
            "top_k_accuracy": {k: v / num_samples for k, v in metrics["top_k"].items()},
            "avg_response_time": metrics["response_time"] / num_samples,
            "total_samples": num_samples,
            "correct_predictions": metrics["correct"],
            "incorrect_results": incorrect_results,
        }

    def evaluate_dataset(
        self, dataset_name: str, split: str = "train", num_samples: int | None = None
    ) -> dict[str, Any]:
        dataset = load_dataset(dataset_name, split=split, token=os.getenv("EVALS_HF_TOKEN"))
        if num_samples is None:
            num_samples = len(dataset["synthetic_output"])

        metrics = {"correct": 0, "mrr": 0.0, "response_time": 0.0, "top_k": {1: 0, 3: 0, 5: 0}}
        incorrect_results = []

        for intent, expected in tqdm(
            zip(
                dataset["synthetic_output"][:num_samples],
                dataset["function_name"][:num_samples],
                strict=False,
            ),
            desc="Evaluating intents",
            total=num_samples,
        ):
            results, response_time = self._search(intent)
            rank = self._find_rank(results, expected)

            self._update_metrics(metrics, rank, response_time)

            if not rank:
                incorrect_results.append(
                    {"intent": intent, "expected": expected, "results": results}
                )

        return self._calculate_final_metrics(metrics, num_samples, incorrect_results)

    def _get_commit_hash(self, dataset_name: str) -> str | None:
        """Get latest commit hash from dataset repository."""
        try:
            commits = self.hf_api.list_repo_commits(repo_id=dataset_name, repo_type="dataset")
            commit_hash = commits[0].commit_id if commits else None
            logger.info(f"Got latest commit hash: {commit_hash}")
            return commit_hash
        except Exception as e:
            logger.warning(f"Could not get commit hash: {e}")
            return None

    def _setup_temp_dir(self) -> Path:
        """Create and return path to temporary results directory."""
        temp_dir = Path("results")
        temp_dir.mkdir(exist_ok=True)
        return temp_dir

    def _download_existing_results(self, dataset_name: str, results_file: Path) -> None:
        """Download existing results file if it exists."""
        try:
            self.hf_api.hf_hub_download(
                repo_id=dataset_name,
                filename="results.jsonl",
                local_dir="results",
                repo_type="dataset",
            )
        except Exception as e:
            logger.info(f"Creating new results file: {e}")
            results_file.touch()

    def save_results(self, results: dict[str, Any], dataset_name: str, model_name: str) -> None:
        temp_dir = self._setup_temp_dir()
        try:
            results_file = temp_dir / "results.jsonl"
            self._download_existing_results(dataset_name, results_file)

            commit_hash = self._get_commit_hash(dataset_name)

            with open(results_file, "a") as f:
                f.write(
                    json.dumps(
                        {
                            "timestamp": datetime.now().isoformat(),
                            "model": model_name,
                            "commit_hash": commit_hash,
                            **results,
                        }
                    )
                    + "\n"
                )

            self.hf_api.upload_file(
                path_or_fileobj=str(results_file),
                path_in_repo="results.jsonl",
                repo_id=dataset_name,
                repo_type="dataset",
            )
        finally:
            # Clean up temporary directory
            shutil.rmtree(temp_dir, ignore_errors=True)

    def run(self, dataset_name: str, model_name: str) -> None:
        """Run the complete evaluation pipeline."""
        results = self.evaluate_dataset(dataset_name)
        self.save_results(results, dataset_name, model_name)


def main() -> None:
    if not (api_key := os.getenv("EVALS_API_KEY")):
        raise ValueError("EVALS_API_KEY environment variable is required")

    pipeline = SearchEvaluationPipeline("http://server:8000", api_key)
    dataset_name = "Aipolabs/function_search_synthetic_data"
    model_name = "dual_encoder_text_embedding_3_small_1024"
    pipeline.run(dataset_name, model_name)


if __name__ == "__main__":
    main()
