Easy template:
You are simulating realistic user intents for a software platform with many apps and functions. The user knows they want to use the app called "{row["app_name"]}", which is used for {row["app_description"]}. One of the available functions is:

Function Name: {row["function_name"]}
Function Description: {row["function_description"]}

Simulate a user intent where the user only knows they want to use the {row["app_name"]} app, and they have a goal that can be fulfilled by the function above. Do not mention the function name but mention the app name. The intent should be phrased as a task the user wants to accomplish, not a question. Be natural and goal-oriented.
Format: You should only return the intent, nothing else.

Medium Template: You are simulating realistic user intents for a software platform with many apps and functions. The user knows they want to use the app called "{row['app_name']}". {row['app_description']}. One of the available functions is:

Function Name: {row['function_name']}
Function Description: {row['function_description']}

Simulate a user intent where the user only knows they want to use the {row['app_name']} app. They express a goal that can be fulfilled by the function above, but do **not** mention the function name or use explicit terms from the function description (e.g., avoid words like “search,” “generate,” “download,” etc.).

Instead, embed the goal within a business task or situational need that **implies** the function’s purpose. The intent should be phrased as a natural task the user wants to accomplish, possibly within a broader context. Be slightly indirect but still make the goal clear. Return only the intent.


Hard Template: You are simulating realistic user intents for a software platform with many apps and functions. The user is familiar with the system and has a task in mind that can be fulfilled by the following function:

Function Name: {row['function_name']}
Function Description: {row['function_description']}

Simulate a user intent where the goal can be achieved using this function, but the user does **not** mention the function name and **may or may not** mention the app name (“{row['app_name']}”). App Definition: {row['app_description']}

Avoid direct keywords from the function description. Instead, make the goal part of a broader context — such as compliance reporting, workflow automation, or reviewing historical data — where using this function would be a necessary step. The intent should sound like something a real user might say while trying to complete a high-level task. Return only the intent.
