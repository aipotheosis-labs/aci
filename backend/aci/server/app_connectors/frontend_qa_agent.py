import asyncio
import ipaddress
import logging
import socket
import time
from datetime import UTC, datetime, timedelta
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
from aci.common.exceptions import FrontendQaAgentError, UnexpectedError
from aci.common.logging_setup import get_logger
from aci.common.schemas.app_connectors.frontend_qa_agent import WebsiteEvaluationPublic
from aci.common.schemas.security_scheme import NoAuthScheme, NoAuthSchemeCredentials
from aci.common.utils import create_db_session
from aci.server import config
from aci.server.app_connectors.base import AppConnectorBase

logger = get_logger(__name__)


# Completely suppress browser_use logging
browser_use_logger = logging.getLogger("browser_use")
browser_use_logger.setLevel(logging.CRITICAL)  # Suppress internal handler output
browser_use_logger.propagate = False  # Prevent propagation to parent loggers

browser_use_cost_logger = logging.getLogger("cost")
browser_use_cost_logger.setLevel(logging.CRITICAL)  # Suppress internal handler output
browser_use_cost_logger.propagate = False  # Prevent propagation to parent loggers


def _validate_url(url: str) -> None:
    """
    Validate URL format and security to prevent SSRF attacks.
    TODO: the best way to prevent SSRF attacks is actually put this agent execution in a sandboxed
    environment such as E2B.

    Args:
        url: URL to validate

    Raises:
        FrontendQaAgent: If URL format is invalid or poses security risk
    """
    # Basic format validation using urlparse
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        raise FrontendQaAgentError(
            "Invalid URL format. URL must include protocol (http/https) and domain."
        )

    # Ensure protocol is http or https
    if parsed.scheme not in ["http", "https"]:
        raise FrontendQaAgentError("URL must use http or https protocol.")

    # Extract hostname for security validation
    hostname = parsed.hostname
    if not hostname:
        raise FrontendQaAgentError("Invalid URL: hostname cannot be determined.")

    # Block localhost and common internal hostnames
    blocked_hostnames = ["localhost", "127.0.0.1", "::1", "0.0.0.0"]
    if hostname.lower() in blocked_hostnames:
        raise FrontendQaAgentError(
            "Access to localhost/loopback addresses is not allowed for security reasons."
        )

    # Check if hostname is an IP address and block private ranges
    try:
        ip = ipaddress.ip_address(hostname)
        if ip.is_private or ip.is_loopback:
            raise FrontendQaAgentError(
                "Access to private/internal IP addresses is not allowed for security reasons."
            )

        # Block cloud metadata service (AWS/GCP/Azure)
        if str(ip) in ["169.254.169.254", "169.254.169.253", "168.63.129.16"]:
            raise FrontendQaAgentError(
                "Access to cloud metadata endpoints is not allowed for security reasons."
            )

    except ValueError:
        # It's a hostname, not an IP - do basic DNS resolution check
        try:
            resolved_ip = socket.gethostbyname(hostname)
            ip = ipaddress.ip_address(resolved_ip)
            if ip.is_private or ip.is_loopback:
                raise FrontendQaAgentError(
                    "Domain resolves to private/internal IP address, access not allowed for security reasons."
                )
        except (socket.gaierror, ValueError):
            # DNS resolution failed or invalid IP - let browser handle it
            pass


class FrontendQaAgent(AppConnectorBase):
    """
    Frontend QA Agent Connector that helps you evaluate and debug your website.
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
            FrontendQaAgent: If URL is invalid, rate limited, or evaluation is in progress
        """
        # Validate URL format
        _validate_url(url)

        with create_db_session(config.DB_FULL_URL) as db_session:
            # Check for existing evaluation with rate limiting
            existing_evaluation = (
                crud.frontend_qa_agent.get_website_evaluation_by_url_and_linked_account(
                    db_session, self.linked_account.id, url
                )
            )

            if existing_evaluation:
                match existing_evaluation.status:
                    case WebsiteEvaluationStatus.IN_PROGRESS:
                        # Block IN_PROGRESS evaluations regardless of time
                        raise FrontendQaAgentError(
                            "Website evaluation is currently in progress. Use FRONTEND_QA_AGENT__GET_WEBSITE_EVALUATION_RESULT to check the status and retrieve results when completed."
                        )
                    case WebsiteEvaluationStatus.COMPLETED:
                        # Apply 5-minute rate limit for completed evaluations
                        five_minutes_ago = datetime.now(UTC) - timedelta(minutes=5)
                        if existing_evaluation.updated_at.replace(tzinfo=UTC) > five_minutes_ago:
                            raise FrontendQaAgentError(
                                "Rate limit exceeded. Please wait 5 minutes between evaluation requests for the same URL. Use FRONTEND_QA_AGENT__GET_WEBSITE_EVALUATION_RESULT to retrieve the previous evaluation result."
                            )
                    case WebsiteEvaluationStatus.FAILED:
                        # Apply 5-minute rate limit for failed evaluations
                        five_minutes_ago = datetime.now(UTC) - timedelta(minutes=5)
                        if existing_evaluation.updated_at.replace(tzinfo=UTC) > five_minutes_ago:
                            raise FrontendQaAgentError(
                                "Rate limit exceeded. Please wait 5 minutes between evaluation requests for the same URL. The previous evaluation failed, you can retry after the cooldown period."
                            )
                # If we reach here, existing evaluation is COMPLETED or FAILED and older than 5 minutes, so proceed

            # Create or update evaluation record with IN_PROGRESS status
            try:
                evaluation = crud.frontend_qa_agent.mark_website_evaluation_as_in_progress(
                    db_session, self.linked_account.id, url
                )
            except OperationalError as e:
                # Lock acquisition failed - another evaluation is in progress
                raise FrontendQaAgentError(
                    "Another evaluation for this URL is currently in progress. Please wait and use FRONTEND_QA_AGENT__GET_WEBSITE_EVALUATION_RESULT to check the status."
                ) from e

            # Commit the evaluation record creation before starting async task
            db_session.commit()

            # Start async evaluation task
            try:
                asyncio.create_task(_evaluate_and_update_database(url, evaluation.id))  # noqa: RUF006
            except Exception as e:
                # Task creation failed - immediately mark as failed
                with create_db_session(config.DB_FULL_URL) as cleanup_session:
                    crud.frontend_qa_agent.update_website_evaluation_status_and_result(
                        cleanup_session,
                        evaluation.id,
                        WebsiteEvaluationStatus.FAILED,
                        f"Failed to start evaluation task: {e}",
                    )
                    cleanup_session.commit()
                raise UnexpectedError(
                    "Failed to start website evaluation. Please try again later."
                ) from e

            logger.info(
                f"Website evaluation initiated for URL: {url}, evaluation_id: {evaluation.id}"
            )

            return {
                "status": WebsiteEvaluationStatus.IN_PROGRESS.value,
                "message": "Website evaluation initiated successfully. Use FRONTEND_QA_AGENT__GET_WEBSITE_EVALUATION_RESULT to retrieve results.",
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
            FrontendQaAgent: If no evaluation exists, evaluation is in progress, or evaluation failed
        """
        with create_db_session(config.DB_FULL_URL) as db_session:
            # Check if evaluation exists for this linked_account + URL
            evaluation = crud.frontend_qa_agent.get_website_evaluation_by_url_and_linked_account(
                db_session, self.linked_account.id, url
            )

            # No evaluation found
            if not evaluation:
                raise FrontendQaAgentError(
                    "No evaluation found for this URL. Use FRONTEND_QA_AGENT__EVALUATE_WEBSITE to start a new website evaluation."
                )

            # Handle different evaluation statuses
            if evaluation.status == WebsiteEvaluationStatus.IN_PROGRESS:
                raise FrontendQaAgentError(
                    "Website evaluation is currently in progress. Please wait and try again in 15-30 seconds. If the evaluation takes longer, wait using exponential backoff: 15s, 30s, 60s, 120s, 240s (up to 5 retries total)."
                )

            elif evaluation.status == WebsiteEvaluationStatus.FAILED:
                raise FrontendQaAgentError(
                    f"Website evaluation failed: {evaluation.result}. Use FRONTEND_QA_AGENT__EVALUATE_WEBSITE to start a new evaluation (respecting the 5-minute rate limit)."
                )

            elif evaluation.status == WebsiteEvaluationStatus.COMPLETED:
                logger.info(f"Retrieved completed evaluation for URL: {url}")
                return WebsiteEvaluationPublic(
                    url=evaluation.url, result=evaluation.result, evaluated_at=evaluation.updated_at
                )

            else:
                # Should never happen, but handle unknown status
                raise FrontendQaAgentError(
                    f"Website evaluation has unknown status: {evaluation.status}. Use FRONTEND_QA_AGENT__EVALUATE_WEBSITE to start a new evaluation."
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
    start_time = time.time()
    logger.info(
        f"Starting _evaluate_and_update_database for URL: {url}, evaluation_id: {evaluation_id}"
    )

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
                crud.frontend_qa_agent.update_website_evaluation_status_and_result(
                    db_session, evaluation_id, WebsiteEvaluationStatus.FAILED, error_msg
                )
                logger.warning(f"Website evaluation returned empty result for URL: {url}")
                return

            # Update database with successful result
            crud.frontend_qa_agent.update_website_evaluation_status_and_result(
                db_session, evaluation_id, WebsiteEvaluationStatus.COMPLETED, result
            )
            logger.info(f"Website evaluation completed successfully for URL: {url}")

        except TimeoutError:
            error_msg = "Website evaluation timed out after 5 minutes. The website may be slow to respond or the evaluation process encountered issues."
            crud.frontend_qa_agent.update_website_evaluation_status_and_result(
                db_session, evaluation_id, WebsiteEvaluationStatus.FAILED, error_msg
            )
            logger.warning(f"Website evaluation timed out for URL: {url}")

        except Exception as e:
            # TODO: Add specific browser_use exception handling once we determine the exact exception types
            error_msg = f"Website evaluation failed: {e!s}. Please try again or contact support if the issue persists."

            crud.frontend_qa_agent.update_website_evaluation_status_and_result(
                db_session, evaluation_id, WebsiteEvaluationStatus.FAILED, error_msg
            )
            logger.error(f"Website evaluation failed for URL {url}: {e}")

        finally:
            # Always commit to ensure database state is updated
            db_session.commit()

            # Log total function duration
            end_time = time.time()
            total_duration = end_time - start_time
            logger.info(
                f"_evaluate_and_update_database completed for URL: {url}, evaluation_id: {evaluation_id}, total duration: {total_duration:.2f} seconds"
            )


async def _evaluate_website_with_browser_use(url: str) -> str | None:
    llm = ChatAnthropic(
        model=config.ANTHROPIC_MODEL_FOR_FRONTEND_QA_AGENT, api_key=config.ANTHROPIC_API_KEY
    )

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
    logger.info(
        f"Browser-use agent execution total duration: {history.total_duration_seconds()} seconds"
    )
    return history.final_result()  # type: ignore
