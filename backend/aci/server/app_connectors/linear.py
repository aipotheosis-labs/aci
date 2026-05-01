import json
from typing import Any, Dict, List, Optional, override

import requests

from aci.common.db.sql_models import LinkedAccount
from aci.common.exceptions import ACIException
from aci.common.logging_setup import get_logger
from aci.common.schemas.security_scheme import (
    OAuth2Scheme,
    OAuth2SchemeCredentials,
)
from aci.server.app_connectors.base import AppConnectorBase

logger = get_logger(__name__)


class Linear(AppConnectorBase):
    """
    Linear Connector using GraphQL API.
    
    Linear only provides GraphQL API, no REST API.
    This connector implements the most commonly used Linear operations.
    """

    def __init__(
        self,
        linked_account: LinkedAccount,
        security_scheme: OAuth2Scheme,
        security_credentials: OAuth2SchemeCredentials,
    ):
        super().__init__(linked_account, security_scheme, security_credentials)
        self.access_token = security_credentials.access_token
        self.api_url = "https://api.linear.app/graphql"

    @override
    def _before_execute(self) -> None:
        """Initialize Linear GraphQL client with OAuth2 credentials."""
        if not self.access_token:
            raise ACIException("No access token available for Linear API")

    def _make_graphql_request(self, query: str, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make a GraphQL request to Linear API."""
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }
        
        payload = {"query": query}
        if variables:
            payload["variables"] = variables

        try:
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            
            if "errors" in result:
                error_messages = [error.get("message", "Unknown error") for error in result["errors"]]
                raise ACIException(f"GraphQL errors: {'; '.join(error_messages)}")
            
            return result.get("data", {})
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Linear API request failed: {e}")
            raise ACIException(f"Failed to connect to Linear API: {str(e)}")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Linear API response: {e}")
            raise ACIException("Invalid response from Linear API")

    def create_issue(
        self,
        title: str,
        team_id: str,
        description: Optional[str] = None,
        assignee_id: Optional[str] = None,
        priority: Optional[int] = None,
        label_ids: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Create a new issue in Linear.
        
        Function name: LINEAR__CREATE_ISSUE
        """
        query = """
        mutation IssueCreate($input: IssueCreateInput!) {
          issueCreate(input: $input) {
            success
            issue {
              id
              title
              description
              url
              identifier
              priority
              state {
                id
                name
                type
              }
              team {
                id
                name
                key
              }
              assignee {
                id
                name
                email
              }
              labels {
                nodes {
                  id
                  name
                  color
                }
              }
              createdAt
              updatedAt
            }
          }
        }
        """
        
        # Build input object
        input_data = {
            "title": title,
            "teamId": team_id,
        }
        
        if description:
            input_data["description"] = description
        if assignee_id:
            input_data["assigneeId"] = assignee_id
        if priority is not None:
            input_data["priority"] = priority
        if label_ids:
            input_data["labelIds"] = label_ids

        variables = {"input": input_data}
        
        try:
            result = self._make_graphql_request(query, variables)
            issue_create = result.get("issueCreate", {})
            
            if not issue_create.get("success"):
                raise ACIException("Failed to create issue")
            
            return {
                "success": True,
                "issue": issue_create.get("issue", {})
            }
        except Exception as e:
            logger.error(f"Failed to create Linear issue: {e}")
            raise ACIException(f"Failed to create issue: {str(e)}")

    def get_issues(
        self,
        team_id: Optional[str] = None,
        assignee_id: Optional[str] = None,
        state: Optional[str] = None,
        limit: int = 50,
    ) -> Dict[str, Any]:
        """
        Get issues from Linear with optional filtering.
        
        Function name: LINEAR__GET_ISSUES
        """
        # Build filter object
        filter_conditions = []
        
        if team_id:
            filter_conditions.append(f'team: {{ id: {{ eq: "{team_id}" }} }}')
        if assignee_id:
            filter_conditions.append(f'assignee: {{ id: {{ eq: "{assignee_id}" }} }}')
        if state:
            filter_conditions.append(f'state: {{ name: {{ eq: "{state}" }} }}')
        
        filter_str = ""
        if filter_conditions:
            filter_str = f'filter: {{ {", ".join(filter_conditions)} }}'

        query = f"""
        query Issues {{
          issues({filter_str}, first: {limit}) {{
            nodes {{
              id
              title
              description
              url
              identifier
              priority
              state {{
                id
                name
                type
              }}
              team {{
                id
                name
                key
              }}
              assignee {{
                id
                name
                email
              }}
              labels {{
                nodes {{
                  id
                  name
                  color
                }}
              }}
              createdAt
              updatedAt
            }}
            pageInfo {{
              hasNextPage
              hasPreviousPage
              startCursor
              endCursor
            }}
          }}
        }}
        """
        
        try:
            result = self._make_graphql_request(query)
            issues_data = result.get("issues", {})
            
            return {
                "success": True,
                "issues": issues_data.get("nodes", []),
                "page_info": issues_data.get("pageInfo", {})
            }
        except Exception as e:
            logger.error(f"Failed to get Linear issues: {e}")
            raise ACIException(f"Failed to get issues: {str(e)}")

    def update_issue(
        self,
        issue_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        assignee_id: Optional[str] = None,
        priority: Optional[int] = None,
        state_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Update an existing issue in Linear.
        
        Function name: LINEAR__UPDATE_ISSUE
        """
        query = """
        mutation IssueUpdate($id: String!, $input: IssueUpdateInput!) {
          issueUpdate(id: $id, input: $input) {
            success
            issue {
              id
              title
              description
              url
              identifier
              priority
              state {
                id
                name
                type
              }
              team {
                id
                name
                key
              }
              assignee {
                id
                name
                email
              }
              labels {
                nodes {
                  id
                  name
                  color
                }
              }
              updatedAt
            }
          }
        }
        """
        
        # Build input object with only provided fields
        input_data = {}
        
        if title is not None:
            input_data["title"] = title
        if description is not None:
            input_data["description"] = description
        if assignee_id is not None:
            input_data["assigneeId"] = assignee_id
        if priority is not None:
            input_data["priority"] = priority
        if state_id is not None:
            input_data["stateId"] = state_id

        if not input_data:
            raise ACIException("At least one field must be provided to update")

        variables = {
            "id": issue_id,
            "input": input_data
        }
        
        try:
            result = self._make_graphql_request(query, variables)
            issue_update = result.get("issueUpdate", {})
            
            if not issue_update.get("success"):
                raise ACIException("Failed to update issue")
            
            return {
                "success": True,
                "issue": issue_update.get("issue", {})
            }
        except Exception as e:
            logger.error(f"Failed to update Linear issue: {e}")
            raise ACIException(f"Failed to update issue: {str(e)}")

    def get_teams(self) -> Dict[str, Any]:
        """
        Get all teams in the Linear workspace.
        
        Function name: LINEAR__GET_TEAMS
        """
        query = """
        query Teams {
          teams {
            nodes {
              id
              name
              key
              description
              icon
              color
              private
              issueCount
              states {
                nodes {
                  id
                  name
                  type
                  color
                }
              }
              labels {
                nodes {
                  id
                  name
                  color
                  description
                }
              }
            }
          }
        }
        """
        
        try:
            result = self._make_graphql_request(query)
            teams_data = result.get("teams", {})
            
            return {
                "success": True,
                "teams": teams_data.get("nodes", [])
            }
        except Exception as e:
            logger.error(f"Failed to get Linear teams: {e}")
            raise ACIException(f"Failed to get teams: {str(e)}")

    def get_users(self, active_only: bool = True) -> Dict[str, Any]:
        """
        Get users in the Linear workspace.
        
        Function name: LINEAR__GET_USERS
        """
        filter_str = 'filter: { active: { eq: true } }' if active_only else ''
        
        query = f"""
        query Users {{
          users({filter_str}) {{
            nodes {{
              id
              name
              email
              displayName
              avatarUrl
              active
              admin
              guest
            }}
          }}
        }}
        """
        
        try:
            result = self._make_graphql_request(query)
            users_data = result.get("users", {})
            
            return {
                "success": True,
                "users": users_data.get("nodes", [])
            }
        except Exception as e:
            logger.error(f"Failed to get Linear users: {e}")
            raise ACIException(f"Failed to get users: {str(e)}")

    def get_issue(self, issue_id: str) -> Dict[str, Any]:
        """
        Get a specific issue by ID with full details.
        
        Function name: LINEAR__GET_ISSUE
        """
        query = """
        query Issue($id: String!) {
          issue(id: $id) {
            id
            title
            description
            url
            identifier
            priority
            estimate
            state {
              id
              name
              type
              color
            }
            team {
              id
              name
              key
            }
            assignee {
              id
              name
              email
              displayName
            }
            creator {
              id
              name
              email
            }
            labels {
              nodes {
                id
                name
                color
                description
              }
            }
            comments {
              nodes {
                id
                body
                user {
                  id
                  name
                  email
                }
                createdAt
              }
            }
            attachments {
              nodes {
                id
                title
                url
                subtitle
                metadata
              }
            }
            createdAt
            updatedAt
            completedAt
            canceledAt
            startedAt
          }
        }
        """
        
        variables = {"id": issue_id}
        
        try:
            result = self._make_graphql_request(query, variables)
            issue = result.get("issue")
            
            if not issue:
                raise ACIException(f"Issue with ID {issue_id} not found")
            
            return {
                "success": True,
                "issue": issue
            }
        except Exception as e:
            logger.error(f"Failed to get Linear issue: {e}")
            raise ACIException(f"Failed to get issue: {str(e)}")

    def get_projects(
        self,
        include_archived: bool = False,
        limit: int = 50,
    ) -> Dict[str, Any]:
        """
        Get all projects in the Linear workspace.
        
        Function name: LINEAR__GET_PROJECTS
        """
        query = f"""
        query Projects {{
          projects(includeArchived: {str(include_archived).lower()}, first: {limit}) {{
            nodes {{
              id
              name
              description
              icon
              color
              url
              priority
              priorityLabel
              progress
              health
              status {{
                id
                name
                type
                color
              }}
              creator {{
                id
                name
                email
              }}
              lead {{
                id
                name
                email
              }}
              teams {{
                nodes {{
                  id
                  name
                  key
                }}
              }}
              members {{
                nodes {{
                  id
                  name
                  email
                }}
              }}
              targetDate
              startedAt
              completedAt
              canceledAt
              createdAt
              updatedAt
              archivedAt
            }}
            pageInfo {{
              hasNextPage
              hasPreviousPage
              startCursor
              endCursor
            }}
          }}
        }}
        """
        
        try:
            result = self._make_graphql_request(query)
            projects_data = result.get("projects", {})
            
            return {
                "success": True,
                "projects": projects_data.get("nodes", []),
                "page_info": projects_data.get("pageInfo", {})
            }
        except Exception as e:
            logger.error(f"Failed to get Linear projects: {e}")
            raise ACIException(f"Failed to get projects: {str(e)}")

    def get_project(self, project_id: str) -> Dict[str, Any]:
        """
        Get a specific project by ID with full details.
        
        Function name: LINEAR__GET_PROJECT
        """
        query = """
        query Project($id: String!) {
          project(id: $id) {
            id
            name
            description
            content
            icon
            color
            url
            priority
            priorityLabel
            progress
            health
            healthUpdatedAt
            status {
              id
              name
              type
              color
            }
            creator {
              id
              name
              email
              displayName
            }
            lead {
              id
              name
              email
              displayName
            }
            teams {
              nodes {
                id
                name
                key
                description
              }
            }
            members {
              nodes {
                id
                name
                email
                displayName
                avatarUrl
              }
            }
            issues(first: 10) {
              nodes {
                id
                title
                identifier
                priority
                state {
                  name
                  type
                }
                assignee {
                  id
                  name
                }
              }
            }
            projectMilestones {
              nodes {
                id
                name
                description
                targetDate
              }
            }
            targetDate
            startedAt
            completedAt
            canceledAt
            createdAt
            updatedAt
            archivedAt
          }
        }
        """
        
        variables = {"id": project_id}
        
        try:
            result = self._make_graphql_request(query, variables)
            project = result.get("project")
            
            if not project:
                raise ACIException(f"Project with ID {project_id} not found")
            
            return {
                "success": True,
                "project": project
            }
        except Exception as e:
            logger.error(f"Failed to get Linear project: {e}")
            raise ACIException(f"Failed to get project: {str(e)}") 