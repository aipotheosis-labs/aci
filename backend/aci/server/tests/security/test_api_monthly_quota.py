import logging
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from aci.common.db import crud
from aci.common.db.sql_models import Agent, Function, LinkedAccount, Plan, Project
from aci.common.schemas.function import FunctionExecute
from aci.common.schemas.subscription import SubscriptionFiltered
from aci.server import config

logger = logging.getLogger(__name__)


class TestQuotaIncrease:
    """Test that quota increases as expected for search and execute routes."""

    def test_search_apps_increases_quota(
        self,
        test_client: TestClient,
        dummy_api_key_1: str,
        dummy_project_1: Project,
        db_session: Session,
    ) -> None:
        """Test that search apps route increases quota usage."""
        # Get initial quota usage
        initial_usage = dummy_project_1.api_quota_monthly_used

        # Make search request
        response = test_client.get(
            f"{config.ROUTER_PREFIX_APPS}/search",
            params={"limit": 1},
            headers={"x-api-key": dummy_api_key_1},
        )

        assert response.status_code == status.HTTP_200_OK

        # Refresh project and check quota increased
        db_session.refresh(dummy_project_1)
        assert dummy_project_1.api_quota_monthly_used == initial_usage + 1

    def test_search_functions_increases_quota(
        self,
        test_client: TestClient,
        dummy_api_key_1: str,
        dummy_project_1: Project,
        db_session: Session,
    ) -> None:
        """Test that search functions route increases quota usage."""
        # Get initial quota usage
        initial_usage = dummy_project_1.api_quota_monthly_used

        # Make search request
        response = test_client.get(
            f"{config.ROUTER_PREFIX_FUNCTIONS}/search",
            params={"limit": 1},
            headers={"x-api-key": dummy_api_key_1},
        )

        assert response.status_code == status.HTTP_200_OK

        # Refresh project and check quota increased
        db_session.refresh(dummy_project_1)
        assert dummy_project_1.api_quota_monthly_used == initial_usage + 1

    def test_execute_function_increases_quota(
        self,
        test_client: TestClient,
        dummy_agent_1_with_all_apps_allowed: Agent,
        dummy_function_aci_test__hello_world_no_args: Function,
        dummy_linked_account_default_api_key_aci_test_project_1: LinkedAccount,
        db_session: Session,
    ) -> None:
        """Test that execute function route increases quota usage."""
        # Get the project associated with the agent
        project = crud.projects.get_project(
            db_session, dummy_agent_1_with_all_apps_allowed.project_id
        )
        assert project is not None  # Added for type checking
        initial_usage = project.api_quota_monthly_used

        # Mock the function execution to avoid actual HTTP calls
        with patch("aci.server.function_executors.get_executor") as mock_get_executor:
            mock_executor = MagicMock()
            mock_executor.execute.return_value = MagicMock(success=True, data={"test": "result"})
            mock_get_executor.return_value = mock_executor

            function_execute = FunctionExecute(
                linked_account_owner_id=dummy_linked_account_default_api_key_aci_test_project_1.linked_account_owner_id,
            )

            response = test_client.post(
                f"{config.ROUTER_PREFIX_FUNCTIONS}/{dummy_function_aci_test__hello_world_no_args.name}/execute",
                json=function_execute.model_dump(mode="json"),
                headers={"x-api-key": dummy_agent_1_with_all_apps_allowed.api_keys[0].key},
            )

            assert response.status_code == status.HTTP_200_OK

            # Refresh project and check quota increased
            db_session.refresh(project)
            assert project.api_quota_monthly_used == initial_usage + 1


class TestQuotaExceeded:
    """Test that errors are raised when quota limits are exceeded."""

    def test_search_apps_quota_exceeded(
        self,
        test_client: TestClient,
        dummy_api_key_1: str,
        dummy_project_1: Project,
        db_session: Session,
        free_plan: Plan,
    ) -> None:
        """Test that search apps route raises error when quota is exceeded."""
        # Set quota usage to the free plan limit (1000)
        fake_time = datetime(2024, 1, 15, tzinfo=UTC)
        dummy_project_1.api_quota_monthly_used = free_plan.features["api_calls_monthly"]
        dummy_project_1.api_quota_last_reset = fake_time
        db_session.commit()
        db_session.refresh(dummy_project_1)

        # Create subscription with free plan
        mock_subscription = SubscriptionFiltered(
            plan=free_plan,
            current_period_start=fake_time,
            status="active",  # type: ignore
        )

        with patch("aci.server.billing.get_subscription_by_org_id", return_value=mock_subscription):
            response = test_client.get(
                f"{config.ROUTER_PREFIX_APPS}/search",
                params={"limit": 1},
                headers={"x-api-key": dummy_api_key_1},
            )

            assert response.status_code == status.HTTP_402_PAYMENT_REQUIRED

    def test_search_functions_quota_exceeded(
        self,
        test_client: TestClient,
        dummy_api_key_1: str,
        dummy_project_1: Project,
        db_session: Session,
        free_plan: Plan,
    ) -> None:
        """Test that search functions route raises error when quota is exceeded."""
        # Set quota usage to the free plan limit (1000)
        fake_time = datetime(2024, 1, 15, tzinfo=UTC)
        dummy_project_1.api_quota_monthly_used = free_plan.features["api_calls_monthly"]
        dummy_project_1.api_quota_last_reset = fake_time
        db_session.commit()
        db_session.refresh(dummy_project_1)

        # Create subscription with free plan
        mock_subscription = SubscriptionFiltered(
            plan=free_plan,
            current_period_start=fake_time,
            status="active",  # type: ignore
        )

        with patch("aci.server.billing.get_subscription_by_org_id", return_value=mock_subscription):
            response = test_client.get(
                f"{config.ROUTER_PREFIX_FUNCTIONS}/search",
                params={"limit": 1},
                headers={"x-api-key": dummy_api_key_1},
            )

            assert response.status_code == status.HTTP_402_PAYMENT_REQUIRED

    def test_execute_function_quota_exceeded(
        self,
        test_client: TestClient,
        dummy_agent_1_with_all_apps_allowed: Agent,
        dummy_function_aci_test__hello_world_no_args: Function,
        dummy_linked_account_default_api_key_aci_test_project_1: LinkedAccount,
        db_session: Session,
        free_plan: Plan,
    ) -> None:
        """Test that execute function route raises error when quota is exceeded."""
        # Get the project associated with the agent
        project = crud.projects.get_project(
            db_session, dummy_agent_1_with_all_apps_allowed.project_id
        )
        assert project is not None  # Added for type checking

        # Set quota usage to the free plan limit (1000)
        fake_time = datetime(2024, 1, 15, tzinfo=UTC)
        project.api_quota_monthly_used = free_plan.features["api_calls_monthly"]
        project.api_quota_last_reset = fake_time
        db_session.commit()
        db_session.refresh(project)

        # Create subscription with free plan
        mock_subscription = SubscriptionFiltered(
            plan=free_plan,
            current_period_start=fake_time,
            status="active",  # type: ignore
        )

        with patch("aci.server.billing.get_subscription_by_org_id", return_value=mock_subscription):
            # Mock the function execution to avoid actual HTTP calls
            with patch("aci.server.function_executors.get_executor") as mock_get_executor:
                mock_executor = MagicMock()
                mock_executor.execute.return_value = MagicMock(
                    success=True, data={"test": "result"}
                )
                mock_get_executor.return_value = mock_executor

                function_execute = FunctionExecute(
                    linked_account_owner_id=dummy_linked_account_default_api_key_aci_test_project_1.linked_account_owner_id,
                )

                response = test_client.post(
                    f"{config.ROUTER_PREFIX_FUNCTIONS}/{dummy_function_aci_test__hello_world_no_args.name}/execute",
                    json=function_execute.model_dump(mode="json"),
                    headers={"x-api-key": dummy_agent_1_with_all_apps_allowed.api_keys[0].key},
                )

                assert response.status_code == status.HTTP_402_PAYMENT_REQUIRED


class TestQuotaReset:
    """Test that quota reset works as expected."""

    def test_quota_reset_on_billing_period_change(
        self,
        test_client: TestClient,
        dummy_api_key_1: str,
        dummy_project_1: Project,
        db_session: Session,
        free_plan: Plan,
    ) -> None:
        """Test that quota resets when billing period changes."""
        # Set some initial quota usage
        fake_time = datetime(2024, 1, 15, tzinfo=UTC)
        dummy_project_1.api_quota_last_reset = fake_time - timedelta(days=32)
        dummy_project_1.api_quota_monthly_used = 2
        db_session.commit()
        db_session.refresh(dummy_project_1)
        assert dummy_project_1.api_quota_monthly_used == 2

        # Create a subscription with a new billing period (past date)
        mock_subscription = SubscriptionFiltered(
            plan=free_plan,
            current_period_start=fake_time,
            status="active",  # type: ignore
        )

        with patch("aci.server.billing.get_subscription_by_org_id", return_value=mock_subscription):
            # Make a request which should trigger quota reset
            response = test_client.get(
                f"{config.ROUTER_PREFIX_APPS}/search",
                params={"limit": 1},
                headers={"x-api-key": dummy_api_key_1},
            )

            assert response.status_code == status.HTTP_200_OK

            # Quota should be reset and then incremented by 1 for this request
            db_session.refresh(dummy_project_1)
            assert dummy_project_1.api_quota_monthly_used == 1
            assert dummy_project_1.api_quota_last_reset.replace(tzinfo=UTC) >= fake_time.replace(
                microsecond=0
            )

    def test_quota_aggregation_across_org_projects(
        self,
        test_client: TestClient,
        dummy_api_key_1: str,
        dummy_project_1: Project,
        dummy_project_2: Project,
        db_session: Session,
        free_plan: Plan,
    ) -> None:
        """Test that quota is properly aggregated across all projects in an organization."""
        # Set both projects to half the free plan limit (500 each)
        fake_time = datetime(2024, 1, 15, tzinfo=UTC)
        half_limit = free_plan.features["api_calls_monthly"] // 2

        dummy_project_1.api_quota_monthly_used = half_limit
        dummy_project_2.api_quota_monthly_used = half_limit
        db_session.commit()
        db_session.refresh(dummy_project_1)
        db_session.refresh(dummy_project_2)

        assert dummy_project_1.api_quota_monthly_used == half_limit
        assert dummy_project_2.api_quota_monthly_used == half_limit

        # Create subscription with free plan
        mock_subscription = SubscriptionFiltered(
            plan=free_plan,
            current_period_start=fake_time,
            status="active",  # type: ignore
        )

        with patch("aci.server.billing.get_subscription_by_org_id", return_value=mock_subscription):
            # This should trigger quota exceeded since total usage across org (500 + 500 + 1) will exceed 1000
            response = test_client.get(
                f"{config.ROUTER_PREFIX_APPS}/search",
                params={"limit": 1},
                headers={"x-api-key": dummy_api_key_1},
            )

            # Should fail due to aggregated quota limit
            assert response.status_code == status.HTTP_402_PAYMENT_REQUIRED
