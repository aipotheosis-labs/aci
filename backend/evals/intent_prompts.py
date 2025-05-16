import pandas as pd


def task_prompt(row: pd.Series) -> str:
    """Generate a task-oriented intent prompt."""
    return f"""
You are simulating realistic user intents for a software platform with many apps and functions. The user knows they want to use the app called "{row["app_name"]}", which is used for {row["app_description"]}. One of the available functions is:

Function Name: {row["function_name"]}
Function Description: {row["function_description"]}

Simulate a user intent where the user only knows they want to use the {row["app_name"]} app, and they have a goal that can be fulfilled by the function above. Do not mention the function name but mention the app name. The intent should be phrased as a task the user wants to accomplish, not a question. Be natural and goal-oriented.
Format: You should only return the intent, nothing else.
""".strip()


# Dictionary of all available prompts
PROMPTS = {
    "task": task_prompt,
}
