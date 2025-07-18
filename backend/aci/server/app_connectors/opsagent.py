import asyncio
from datetime import datetime, timedelta
from typing import override
from urllib.parse import urlparse
from uuid import UUID

from browser_use import Agent
from browser_use.browser import BrowserProfile
from browser_use.llm.anthropic.chat import ChatAnthropic
from sqlalchemy.exc import OperationalError

from aci.common.db import crud
from aci.common.db.sql_models import LinkedAccount
from aci.common.enums import WebsiteEvaluationStatus
from aci.common.exceptions import OpsAgentError
from aci.common.logging_setup import get_logger
from aci.common.schemas.app_connectors.opsagent import WebsiteEvaluationPublic
from aci.common.schemas.security_scheme import NoAuthScheme, NoAuthSchemeCredentials
from aci.common.utils import create_db_session
from aci.server import config
from aci.server.app_connectors.base import AppConnectorBase

logger = get_logger(__name__)


def _validate_url(url: str) -> None:
    """
    Validate URL format and accessibility.

    Args:
        url: URL to validate

    Raises:
        OpsAgentError: If URL format is invalid
    """
    # Basic format validation using urlparse
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        raise OpsAgentError(
            "Invalid URL format. URL must include protocol (http/https) and domain."
        )

    # Ensure protocol is http or https
    if parsed.scheme not in ["http", "https"]:
        raise OpsAgentError("URL must use http or https protocol.")


class Opsagent(AppConnectorBase):
    """
    OpsAgent Connector that helps you to automate your DevOps tasks, e.g. evaluate and debug your website.
    """

    def __init__(
        self,
        linked_account: LinkedAccount,
        security_scheme: NoAuthScheme,
        security_credentials: NoAuthSchemeCredentials,
    ):
        super().__init__(linked_account, security_scheme, security_credentials)

    @override
    def _before_execute(self) -> None:
        pass

    def evaluate_website(self, url: str) -> dict[str, str]:
        """
        Initiate an asynchronous website evaluation to identify UI/UX issues.

        This function validates the URL, checks for rate limiting, creates or updates
        an evaluation record, and starts the async evaluation process.

        Args:
            url: The URL of the website to evaluate

        Returns:
            dict with status and message indicating evaluation has started

        Raises:
            OpsAgentError: If URL is invalid, rate limited, or evaluation is in progress
        """
        # Validate URL format
        _validate_url(url)

        with create_db_session(config.DB_FULL_URL) as db_session:
            # Check for existing evaluation with rate limiting
            existing_evaluation = crud.opsagent.get_website_evaluation_by_url_and_linked_account(
                db_session, self.linked_account.id, url
            )

            if existing_evaluation:
                # Always enforce 5-minute cooldown regardless of previous status
                five_minutes_ago = datetime.now() - timedelta(minutes=5)

                if existing_evaluation.updated_at > five_minutes_ago:
                    if existing_evaluation.status == WebsiteEvaluationStatus.IN_PROGRESS:
                        raise OpsAgentError(
                            "Website evaluation is currently in progress. Use OPSAGENT__GET_WEBSITE_EVALUATION_RESULT to check the status and retrieve results when completed."
                        )
                    else:  # COMPLETED or FAILED
                        raise OpsAgentError(
                            "Rate limit exceeded. Please wait 5 minutes between evaluation requests for the same URL. Use OPSAGENT__GET_WEBSITE_EVALUATION_RESULT to retrieve the previous evaluation result."
                        )

            # Create or update evaluation record with IN_PROGRESS status
            try:
                evaluation = crud.opsagent.start_website_evaluation(
                    db_session, self.linked_account.id, url
                )
            except OperationalError as e:
                # Lock acquisition failed - another evaluation is in progress
                raise OpsAgentError(
                    "Another evaluation for this URL is currently in progress. Please wait and use OPSAGENT__GET_WEBSITE_EVALUATION_RESULT to check the status."
                ) from e

            # Commit the evaluation record creation before starting async task
            db_session.commit()

            # Start async evaluation task
            asyncio.create_task(_evaluate_and_update_database(url, evaluation.id))  # noqa: RUF006

            logger.info(
                f"Website evaluation initiated for URL: {url}, evaluation_id: {evaluation.id}"
            )

            return {
                "status": "started",
                "message": "Website evaluation initiated successfully. Use OPSAGENT__GET_WEBSITE_EVALUATION_RESULT to retrieve results.",
            }

    def get_website_evaluation_result(self, url: str) -> WebsiteEvaluationPublic:
        """
        Retrieve the result of a website evaluation.

        This function checks the evaluation status and returns results for completed
        evaluations, or provides appropriate error messages for other states.

        Args:
            url: The URL of the website evaluation to retrieve

        Returns:
            WebsiteEvaluationPublic: Structured evaluation data with url, result, and timestamp

        Raises:
            OpsAgentError: If no evaluation exists, evaluation is in progress, or evaluation failed
        """
        with create_db_session(config.DB_FULL_URL) as db_session:
            # Check if evaluation exists for this linked_account + URL
            evaluation = crud.opsagent.get_website_evaluation_by_url_and_linked_account(
                db_session, self.linked_account.id, url
            )

            # No evaluation found
            if not evaluation:
                raise OpsAgentError(
                    "No evaluation found for this URL. Use OPSAGENT__EVALUATE_WEBSITE to start a new website evaluation."
                )

            # Handle different evaluation statuses
            if evaluation.status == WebsiteEvaluationStatus.IN_PROGRESS:
                raise OpsAgentError(
                    "Website evaluation is currently in progress. Please wait and try again in 15-30 seconds. If the evaluation takes longer, wait using exponential backoff: 15s, 30s, 60s, 120s, 240s (up to 5 retries total)."
                )

            elif evaluation.status == WebsiteEvaluationStatus.FAILED:
                raise OpsAgentError(
                    f"Website evaluation failed: {evaluation.result}. Use OPSAGENT__EVALUATE_WEBSITE to start a new evaluation (respecting the 5-minute rate limit)."
                )

            elif evaluation.status == WebsiteEvaluationStatus.COMPLETED:
                logger.info(f"Retrieved completed evaluation for URL: {url}")
                return WebsiteEvaluationPublic(
                    url=evaluation.url, result=evaluation.result, evaluated_at=evaluation.updated_at
                )

            else:
                # Should never happen, but handle unknown status
                raise OpsAgentError(
                    f"Website evaluation has unknown status: {evaluation.status}. Use OPSAGENT__EVALUATE_WEBSITE to start a new evaluation."
                )


async def _evaluate_and_update_database(url: str, evaluation_id: UUID) -> None:
    """
    Async wrapper function that evaluates a website and updates the database with results.

    This function handles the complete evaluation lifecycle:
    1. Calls the browser_use evaluation with timeout
    2. Updates database with COMPLETED status on success
    3. Updates database with FAILED status on any error
    4. Handles specific exception types with appropriate error messages

    Args:
        url: URL to evaluate
        evaluation_id: ID of the evaluation record to update

    Note:
        Creates its own database session to avoid transaction conflicts.
        Always commits the transaction to ensure status updates are persisted.
        TODO: Implement cleanup process for old evaluation records if audit trail approach is adopted.
    """
    with create_db_session(config.DB_FULL_URL) as db_session:
        try:
            # Evaluate website with 5-minute timeout
            logger.info(f"Starting website evaluation for URL: {url}")
            result = await asyncio.wait_for(
                _evaluate_website_with_browser_use(url),
                timeout=300,  # 5 minutes
            )

            # Handle empty or None result as a failure case
            if result is None or result.strip() == "":
                error_msg = "Website evaluation completed but returned no results. The website may have blocked automated access or encountered technical issues."
                crud.opsagent.update_website_evaluation_status_and_result(
                    db_session, evaluation_id, WebsiteEvaluationStatus.FAILED, error_msg
                )
                logger.warning(f"Website evaluation returned empty result for URL: {url}")
                return

            # Update database with successful result
            crud.opsagent.update_website_evaluation_status_and_result(
                db_session, evaluation_id, WebsiteEvaluationStatus.COMPLETED, result
            )
            logger.info(f"Website evaluation completed successfully for URL: {url}")

        except TimeoutError:
            error_msg = "Website evaluation timed out after 5 minutes. The website may be slow to respond or the evaluation process encountered issues."
            crud.opsagent.update_website_evaluation_status_and_result(
                db_session, evaluation_id, WebsiteEvaluationStatus.FAILED, error_msg
            )
            logger.warning(f"Website evaluation timed out for URL: {url}")

        except Exception as e:
            # TODO: Add specific browser_use exception handling once we determine the exact exception types
            error_msg = f"Website evaluation failed: {e!s}. Please try again or contact support if the issue persists."

            crud.opsagent.update_website_evaluation_status_and_result(
                db_session, evaluation_id, WebsiteEvaluationStatus.FAILED, error_msg
            )
            logger.error(f"Website evaluation failed for URL {url}: {e}")

        finally:
            # Always commit to ensure database state is updated
            db_session.commit()


async def _evaluate_website_with_browser_use(url: str) -> str | None:
    llm = ChatAnthropic(model="claude-3-5-sonnet-latest", api_key=config.ANTHROPIC_API_KEY)

    task = f"""VISIT: {url}

    GOAL: Perform a comprehensive web page analysis to identify UI/UX issues that can be automatically fixed by a coding agent.

    ANALYSIS APPROACH:
    1. First, take a screenshot and analyze the visual layout
    2. Inspect the DOM structure for technical issues
    3. Test key interactive elements (links, buttons, forms)
    4. Check for accessibility and responsive design problems

    OUTPUT FORMAT: Provide a clear, structured report with your findings. If no issues are found, state that clearly.

    ISSUE CLASSIFICATION:
    - **Priority 1**: Critical functionality breaks (broken links, non-functional buttons, missing required elements)
    - **Priority 2**: Visual defects that impact user experience (broken images, layout issues, styling problems)
    - **Priority 3**: Accessibility and UX improvements (missing alt text, poor contrast, unclear labeling)

    For each issue found, include:
    - **Priority level** (1, 2, or 3)
    - **Issue type** (functionality, visual, or accessibility)
    - **Title**: Brief issue summary
    - **Description**: Detailed description of the problem and its impact
    - **Location**: Best available CSS selector and description of where it appears
    - **Evidence**: What you observed vs what should happen
    - **Action items for coding agent**:
    - **Specific changes needed**: Exact code modifications, file updates, or content changes required
    - **Files to examine**: Likely file paths or component names that need modification
    - **Implementation steps**: Step-by-step instructions for making the fix
    - **Testing verification**: How to confirm the fix worked (specific elements to check, user flows to test)
    - **Confidence level**: High/medium/low confidence in the proposed solution

    DETECTION PRIORITIES:
    1. **Broken Functionality**: Links returning 404s, buttons that don't respond, forms that don't submit
    2. **Missing/Broken Images**: img tags with src returning 404, images showing broken icon placeholders
    3. **Layout Issues**: Overlapping content, elements extending beyond containers, misaligned components
    4. **Styling Problems**: Inconsistent fonts/colors, poor contrast, missing hover states
    5. **Accessibility Issues**: Missing alt text, poor color contrast, unlabeled form inputs
    6. **Content Issues**: Lorem ipsum text, placeholder content, broken/empty sections

    CONSTRAINTS:
    - Focus on issues that can be fixed by modifying HTML, CSS, or simple JavaScript
    - Avoid subjective design opinions - focus on objective problems
    - Don't report issues that would require backend changes or complex application logic
    - For complex selectors, provide context about surrounding elements
    - If unsure about the exact fix, set confidence to "low" and provide general guidance

    ACTIONABLE GUIDANCE FOR CODING AGENT:
    - Provide specific code snippets or changes when possible
    - Suggest likely file types (.html, .css, .js) and common locations (components/, assets/, styles/)
    - Include before/after examples for clarity
    - Mention specific HTML attributes, CSS properties, or JavaScript functions that need attention
    - Give concrete success criteria (e.g., "image should display without broken icon", "button should navigate to X page")
    - Consider common web development patterns and frameworks when suggesting fixes

    ANALYSIS WORKFLOW:
    1. Take an initial screenshot to understand the overall layout
    2. Scroll through the page to see all content
    3. Test interactive elements by hovering/clicking
    4. Inspect the DOM for technical issues
    5. Check for responsive behavior if possible
    6. Compile findings into a structured report

    Remember: The goal is to identify specific, actionable issues that an automated coding agent can fix, not to redesign the entire page.
    """

    agent: Agent = Agent(
        task=task,
        llm=llm,
        browser_profile=BrowserProfile(headless=True),
    )

    history = await agent.run(max_steps=10)
    return history.final_result()  # type: ignore
