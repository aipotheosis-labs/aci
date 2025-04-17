"""
Meta functions are used by LLM to search for, retrieve, and execute functions.
These functions provide a structured way for the LLM to discover and use available functionality.

The schemas follow OpenAI Responses API function calling schema, ensuring compatibility
with OpenAI's function calling capabilities. This allows the LLM to dynamically find
and use functions based on user requests without needing to know all available functions in advance.
"""

ACI_SEARCH_FUNCTIONS_SCHEMA = {
    "type": "function",
    "name": "ACI_SEARCH_FUNCTIONS",
    "description": "Search for relevant executable functions based on a specific intent or task description. This function helps discover available functionality that can assist with completing a given task or retrieving specific information.",
    "parameters": {
        "type": "object",
        "properties": {
            "intent": {
                "type": "string",
                "description": "A natural language description of what you're trying to accomplish. This helps find relevant functions that match your needs. Examples include 'what's the top news in the stock market today', 'i want to automate outbound marketing emails', or 'find information about a specific company'.",
            },
            "limit": {
                "type": "integer",
                "default": 20,
                "description": "The maximum number of functions to return from the search per response. Controls the size of the result set.",
                "minimum": 1,
                "maximum": 1000,
            },
            "offset": {
                "type": "integer",
                "default": 0,
                "minimum": 0,
                "description": "Pagination offset for retrieving additional results beyond the initial set. Useful when there are more results than the specified limit.",
            },
        },
        "required": [],
        "additionalProperties": False,
    },
}

ACI_GET_FUNCTION_DEFINITION_SCHEMA = {
    "type": "function",
    "name": "ACI_GET_FUNCTION_DEFINITION",
    "description": "Retrieve the complete definition of a specific function, including its parameters, types, and requirements. This provides all the information needed to properly call the function.",
    "parameters": {
        "type": "object",
        "properties": {
            "function_name": {
                "type": "string",
                "description": "The exact name of the function you want to get the definition for. This name should be obtained from the results of the ACI_SEARCH_FUNCTIONS function.",
            }
        },
        "required": ["function_name"],
        "additionalProperties": False,
    },
}

ACI_EXECUTE_FUNCTION_SCHEMA = {
    "type": "function",
    "name": "ACI_EXECUTE_FUNCTION",
    "description": "Execute a specific function with the provided parameters. This allows the LLM to perform actions or retrieve data by calling the appropriate function with the correct arguments.",
    "parameters": {
        "type": "object",
        "properties": {
            "function_name": {
                "type": "string",
                "description": "The name of the function to execute, which should be obtained from the ACI_GET_FUNCTION_DEFINITION function. This must be an exact match to the function name.",
            },
            "function_arguments": {
                "type": "object",
                "description": "A dictionary containing the input parameters required by the specified function. The parameter names and types must exactly match those defined in the function definition. If the function requires no parameters, provide an empty object {}.",
                "additionalProperties": True,
            },
        },
        "required": ["function_name", "function_arguments"],
        "additionalProperties": False,
    },
}

ACI_META_FUNCTIONS_SCHEMA_LIST = [
    ACI_SEARCH_FUNCTIONS_SCHEMA,
    ACI_GET_FUNCTION_DEFINITION_SCHEMA,
    ACI_EXECUTE_FUNCTION_SCHEMA,
]
