import pandas as pd


def prompt_easy(row: pd.Series) -> str:
    """Generate an easy task-oriented intent prompt."""
    return f"""
You are simulating realistic user intents for a software platform with many apps and functions. The user knows they want to use the app called "{row["app_name"]}", which is used for {row["app_description"]}. One of the available functions is:

Function Name: {row["function_name"]}
Function Description: {row["function_description"]}

Simulate a user intent where the user wants to use the {row["app_name"]} app to accomplish something. The intent should be:
- Direct and straightforward
- Mention the app name explicitly
- Express what they want to do clearly
- Use simple, everyday language
- Be concise (1-2 sentences max)

Do not mention the function name, but the goal should clearly align with what the function does.
Format: You should only return the intent, nothing else.
""".strip()


def prompt_medium(row: pd.Series) -> str:
    """Generate a medium difficulty intent prompt."""
    return f"""
You are simulating realistic user intents for a software platform with many apps and functions. The user knows they want to use the app called "{row["app_name"]}". {row["app_description"]}. One of the available functions is:

Function Name: {row["function_name"]}
Function Description: {row["function_description"]}

Simulate a user intent where the user wants to use the {row["app_name"]} app. The intent should be:
- More conversational and natural
- Mention the app name
- Include some context about WHY they need this (e.g., "for my presentation", "to help my team", "for our project")
- Use more descriptive language
- Be slightly indirect but still make the goal clear
- Avoid technical terms from the function description and the function name

The user should explain their goal within a realistic scenario or use case. Return only the intent.
""".strip()


def prompt_hard(row: pd.Series) -> str:
    """Generate a hard difficulty intent prompt."""
    return f"""
You are simulating realistic user intents for a software platform with many apps and functions. The user is familiar with the system and has a task in mind that can be fulfilled by the following function:

Function Name: {row["function_name"]}
Function Description: {row["function_description"]}
App Name: {row["app_name"]}
App Description: {row["app_description"]}

Simulate a user intent where the goal can be achieved using this function. The intent should be:
- Make the goal part of a broader context — such as compliance reporting, workflow automation, or reviewing historical data — where using this function would be a necessary step
- Do not mention the app name explicitly
- Embed the need within a broader organizational or professional context
- Use sophisticated, professional language
- Be longer and more detailed (3-4 sentences)
- Completely avoid direct keywords from both function name and description
- Frame as a high-level business objective that requires this function as a step

The user should sound like they're solving a real enterprise problem where this function is just one part of a larger workflow. Return only the intent.
""".strip()


# Dictionary of all available prompts
PROMPTS = {
    "prompt_easy": prompt_easy,
    "prompt_medium": prompt_medium,
    "prompt_hard": prompt_hard,
}
