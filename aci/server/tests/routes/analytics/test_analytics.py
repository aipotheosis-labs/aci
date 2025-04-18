from unittest.mock import MagicMock, patch

from fastapi import status
from fastapi.testclient import TestClient

from aci.server import config


@patch("aci.server.routes.analytics.AsyncLogfireQueryClient")
def test_get_app_usage_distribution(
    mock_logfire_client: MagicMock,
    test_client: TestClient,
    dummy_api_key_1: str,
) -> None:
    mock_client_instance = mock_logfire_client.return_value.__aenter__.return_value
    mock_client_instance.query_json_rows.return_value = {
        "columns": [
            {"name": "name", "datatype": "Utf8", "nullable": True},
            {"name": "value", "datatype": "Int64", "nullable": False},
        ],
        "rows": [
            {"name": "BRAVE_SEARCH", "value": 78},
            {"name": "GITHUB", "value": 31},
            {"name": "GMAIL", "value": 23},
            {"name": "GOOGLE_CALENDAR", "value": 13},
            {"name": "NOTION", "value": 6},
        ],
    }

    response = test_client.get(
        f"{config.ROUTER_PREFIX_ANALYTICS}/app-usage-distribution",
        headers={"x-api-key": dummy_api_key_1},
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == [
        {"name": "BRAVE_SEARCH", "value": 78},
        {"name": "GITHUB", "value": 31},
        {"name": "GMAIL", "value": 23},
        {"name": "GOOGLE_CALENDAR", "value": 13},
        {"name": "NOTION", "value": 6},
    ]


@patch("aci.server.routes.analytics.AsyncLogfireQueryClient")
def test_get_function_usage_distribution(
    mock_logfire_client: MagicMock,
    test_client: TestClient,
    dummy_api_key_1: str,
) -> None:
    mock_client_instance = mock_logfire_client.return_value.__aenter__.return_value
    mock_client_instance.query_json_rows.return_value = {
        "columns": [
            {"name": "name", "datatype": "Utf8", "nullable": True},
            {"name": "value", "datatype": "Int64", "nullable": False},
        ],
        "rows": [
            {"name": "BRAVE_SEARCH__WEB_SEARCH", "value": 72},
            {"name": "TAVILY__SEARCH", "value": 5},
            {"name": "GITHUB__GET_USER", "value": 5},
            {"name": "NOTION__SEARCH_PAGES", "value": 2},
            {"name": "ACI_SEARCH_FUNCTIONS_OVERFLOW", "value": 1},
            {"name": "GOOGLE_CALENDAR__EVENTS_INSERT", "value": 1},
        ],
    }

    response = test_client.get(
        f"{config.ROUTER_PREFIX_ANALYTICS}/function-usage-distribution",
        headers={"x-api-key": dummy_api_key_1},
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == [
        {"name": "BRAVE_SEARCH__WEB_SEARCH", "value": 72},
        {"name": "TAVILY__SEARCH", "value": 5},
        {"name": "GITHUB__GET_USER", "value": 5},
        {"name": "NOTION__SEARCH_PAGES", "value": 2},
        {"name": "ACI_SEARCH_FUNCTIONS_OVERFLOW", "value": 1},
        {"name": "GOOGLE_CALENDAR__EVENTS_INSERT", "value": 1},
    ]


@patch("aci.server.routes.analytics.AsyncLogfireQueryClient")
def test_get_app_usage_timeseries(
    mock_logfire_client: MagicMock,
    test_client: TestClient,
    dummy_api_key_1: str,
) -> None:
    mock_client_instance = mock_logfire_client.return_value.__aenter__.return_value
    mock_client_instance.query_json_rows.return_value = {
        "columns": [
            {"name": "x", "datatype": "Date32", "nullable": True},
            {"name": "app_name", "datatype": "Utf8", "nullable": True},
            {"name": "amount", "datatype": "Int64", "nullable": False},
        ],
        "rows": [
            {"x": "2025-04-03", "app_name": "GMAIL", "amount": 1},
            {"x": "2025-04-03", "app_name": "BRAVE_SEARCH", "amount": 22},
            {"x": "2025-04-02", "app_name": "GOOGLE_CALENDAR", "amount": 2},
            {"x": "2025-04-02", "app_name": "SCRAPYBARA", "amount": 6},
            {"x": "2025-04-02", "app_name": "BRAVE_SEARCH", "amount": 4},
            {"x": "2025-04-02", "app_name": "GMAIL", "amount": 1},
            {"x": "2025-04-01", "app_name": "GOOGLE_CALENDAR", "amount": 2},
            {"x": "2025-04-01", "app_name": "ACI_SEARCH_FUNCTIONS_OVERFLOW", "amount": 1},
            {"x": "2025-04-01", "app_name": "NOTION", "amount": 6},
            {"x": "2025-04-01", "app_name": "TAVILY", "amount": 2},
            {"x": "2025-04-01", "app_name": "BRAVE_SEARCH", "amount": 21},
            {"x": "2025-04-01", "app_name": "GMAIL", "amount": 21},
            {"x": "2025-03-31", "app_name": "TAVILY", "amount": 1},
            {"x": "2025-03-31", "app_name": "BRAVE_SEARCH", "amount": 8},
            {"x": "2025-03-30", "app_name": "TAVILY", "amount": 2},
            {"x": "2025-03-30", "app_name": "BRAVE_SEARCH", "amount": 3},
            {"x": "2025-03-30", "app_name": "GOOGLE_CALENDAR", "amount": 1},
            {"x": "2025-03-29", "app_name": "GOOGLE_CALENDAR", "amount": 8},
            {"x": "2025-03-29", "app_name": "GITHUB", "amount": 7},
            {"x": "2025-03-29", "app_name": "BRAVE_SEARCH", "amount": 20},
            {"x": "2025-03-28", "app_name": "GITHUB", "amount": 5},
            {"x": "2025-03-27", "app_name": "GITHUB", "amount": 19},
        ],
    }

    response = test_client.get(
        f"{config.ROUTER_PREFIX_ANALYTICS}/app-usage-timeseries",
        headers={"x-api-key": dummy_api_key_1},
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == [
        {"date": "2025-04-03", "GMAIL": 1, "BRAVE_SEARCH": 22},
        {
            "date": "2025-04-02",
            "GOOGLE_CALENDAR": 2,
            "SCRAPYBARA": 6,
            "BRAVE_SEARCH": 4,
            "GMAIL": 1,
        },
        {
            "date": "2025-04-01",
            "GOOGLE_CALENDAR": 2,
            "ACI_SEARCH_FUNCTIONS_OVERFLOW": 1,
            "NOTION": 6,
            "TAVILY": 2,
            "BRAVE_SEARCH": 21,
            "GMAIL": 21,
        },
        {"date": "2025-03-31", "TAVILY": 1, "BRAVE_SEARCH": 8},
        {"date": "2025-03-30", "TAVILY": 2, "BRAVE_SEARCH": 3, "GOOGLE_CALENDAR": 1},
        {"date": "2025-03-29", "GOOGLE_CALENDAR": 8, "GITHUB": 7, "BRAVE_SEARCH": 20},
        {"date": "2025-03-28", "GITHUB": 5},
        {"date": "2025-03-27", "GITHUB": 19},
    ]


@patch("aci.server.routes.analytics.AsyncLogfireQueryClient")
def test_get_function_usage_timeseries(
    mock_logfire_client: MagicMock,
    test_client: TestClient,
    dummy_api_key_1: str,
) -> None:
    mock_client_instance = mock_logfire_client.return_value.__aenter__.return_value
    mock_client_instance.query_json_rows.return_value = {
        "columns": [
            {"name": "x", "datatype": "Date32", "nullable": True},
            {"name": "function_name", "datatype": "Utf8", "nullable": True},
            {"name": "amount", "datatype": "Int64", "nullable": False},
        ],
        "rows": [
            {"x": "2025-04-03", "function_name": "GMAIL__MESSAGES_LIST", "amount": 1},
            {"x": "2025-04-03", "function_name": "BRAVE_SEARCH__WEB_SEARCH", "amount": 22},
            {"x": "2025-04-02", "function_name": "SCRAPYBARA__START_INSTANCE", "amount": 6},
            {"x": "2025-04-02", "function_name": "BRAVE_SEARCH__WEB_SEARCH", "amount": 4},
            {"x": "2025-04-02", "function_name": "GMAIL__MESSAGES_LIST", "amount": 1},
            {"x": "2025-04-02", "function_name": "GOOGLE_CALENDAR__CALENDARLIST_LIST", "amount": 2},
            {"x": "2025-04-01", "function_name": "NOTION__GET_PAGE", "amount": 4},
            {"x": "2025-04-01", "function_name": "ACI_SEARCH_FUNCTIONS_OVERFLOW", "amount": 1},
            {"x": "2025-04-01", "function_name": "NOTION__SEARCH_PAGES", "amount": 2},
            {"x": "2025-04-01", "function_name": "GMAIL__MESSAGES_LIST", "amount": 18},
            {"x": "2025-04-01", "function_name": "GMAIL__MESSAGES_GET", "amount": 3},
            {"x": "2025-04-01", "function_name": "BRAVE_SEARCH__WEB_SEARCH", "amount": 19},
            {"x": "2025-04-01", "function_name": "GOOGLE_CALENDAR__EVENTS_LIST", "amount": 2},
            {"x": "2025-04-01", "function_name": "BRAVE_SEARCH__NEWS_SEARCH", "amount": 2},
            {"x": "2025-04-01", "function_name": "TAVILY__SEARCH", "amount": 2},
            {"x": "2025-03-31", "function_name": "BRAVE_SEARCH__WEB_SEARCH", "amount": 4},
            {"x": "2025-03-31", "function_name": "BRAVE_SEARCH__NEWS_SEARCH", "amount": 4},
            {"x": "2025-03-31", "function_name": "TAVILY__SEARCH", "amount": 1},
            {"x": "2025-03-30", "function_name": "BRAVE_SEARCH__WEB_SEARCH", "amount": 3},
            {"x": "2025-03-30", "function_name": "TAVILY__SEARCH", "amount": 2},
            {"x": "2025-03-30", "function_name": "GOOGLE_CALENDAR__EVENTS_LIST", "amount": 1},
            {"x": "2025-03-29", "function_name": "BRAVE_SEARCH__WEB_SEARCH", "amount": 20},
            {"x": "2025-03-29", "function_name": "GOOGLE_CALENDAR__EVENTS_LIST", "amount": 7},
            {"x": "2025-03-29", "function_name": "GITHUB__STAR_REPOSITORY", "amount": 3},
            {"x": "2025-03-29", "function_name": "GOOGLE_CALENDAR__EVENTS_INSERT", "amount": 1},
            {"x": "2025-03-29", "function_name": "GITHUB__GET_USER", "amount": 4},
            {"x": "2025-03-28", "function_name": "GITHUB__STAR_REPOSITORY", "amount": 5},
            {"x": "2025-03-27", "function_name": "GITHUB__STAR_REPOSITORY", "amount": 14},
            {"x": "2025-03-27", "function_name": "GITHUB__GET_USER", "amount": 1},
            {"x": "2025-03-27", "function_name": "GITHUB__STAR_REPO", "amount": 4},
        ],
    }

    response = test_client.get(
        f"{config.ROUTER_PREFIX_ANALYTICS}/function-usage-timeseries",
        headers={"x-api-key": dummy_api_key_1},
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == [
        {"date": "2025-04-03", "GMAIL__MESSAGES_LIST": 1, "BRAVE_SEARCH__WEB_SEARCH": 22},
        {
            "date": "2025-04-02",
            "SCRAPYBARA__START_INSTANCE": 6,
            "BRAVE_SEARCH__WEB_SEARCH": 4,
            "GMAIL__MESSAGES_LIST": 1,
            "GOOGLE_CALENDAR__CALENDARLIST_LIST": 2,
        },
        {
            "date": "2025-04-01",
            "NOTION__GET_PAGE": 4,
            "ACI_SEARCH_FUNCTIONS_OVERFLOW": 1,
            "NOTION__SEARCH_PAGES": 2,
            "GMAIL__MESSAGES_LIST": 18,
            "GMAIL__MESSAGES_GET": 3,
            "BRAVE_SEARCH__WEB_SEARCH": 19,
            "GOOGLE_CALENDAR__EVENTS_LIST": 2,
            "BRAVE_SEARCH__NEWS_SEARCH": 2,
            "TAVILY__SEARCH": 2,
        },
        {
            "date": "2025-03-31",
            "BRAVE_SEARCH__WEB_SEARCH": 4,
            "BRAVE_SEARCH__NEWS_SEARCH": 4,
            "TAVILY__SEARCH": 1,
        },
        {
            "date": "2025-03-30",
            "BRAVE_SEARCH__WEB_SEARCH": 3,
            "TAVILY__SEARCH": 2,
            "GOOGLE_CALENDAR__EVENTS_LIST": 1,
        },
        {
            "date": "2025-03-29",
            "BRAVE_SEARCH__WEB_SEARCH": 20,
            "GOOGLE_CALENDAR__EVENTS_LIST": 7,
            "GITHUB__STAR_REPOSITORY": 3,
            "GOOGLE_CALENDAR__EVENTS_INSERT": 1,
            "GITHUB__GET_USER": 4,
        },
        {"date": "2025-03-28", "GITHUB__STAR_REPOSITORY": 5},
        {
            "date": "2025-03-27",
            "GITHUB__STAR_REPOSITORY": 14,
            "GITHUB__GET_USER": 1,
            "GITHUB__STAR_REPO": 4,
        },
    ]
