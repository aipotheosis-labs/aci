# Create the API key
# python -m aipolabs.cli.aipolabs create-random-api-key --visibility-access public


# Make apps
## Brave
python -m aipolabs.cli.aipolabs create-app --app-file ./apps/brave_search/app.json --secrets-file ./apps/brave_search/.app.secrets.json --skip-dry-run

## Google Calendar
python -m aipolabs.cli.aipolabs create-app --app-file ./apps/google_calendar/app.json --secrets-file ./apps/google_calendar/.app.secrets.json --skip-dry-run

## Exa AI
python -m aipolabs.cli.aipolabs create-app --app-file ./apps/exa_ai/app.json --secrets-file ./apps/exa_ai/.app.secrets.json --skip-dry-run

## Tavily
python -m aipolabs.cli.aipolabs create-app --app-file ./apps/tavily/app.json --secrets-file ./apps/tavily/.app.secrets.json --skip-dry-run


# Make functions
## Brave
python -m aipolabs.cli.aipolabs create-functions --functions-file ./apps/brave_search/functions.json --skip-dry-run

## Google Calendar
python -m aipolabs.cli.aipolabs create-functions --functions-file ./apps/google_calendar/functions.json --skip-dry-run

## Exa AI
python -m aipolabs.cli.aipolabs create-functions --functions-file ./apps/exa_ai/functions.json --skip-dry-run

## Tavily
python -m aipolabs.cli.aipolabs create-functions --functions-file ./apps/tavily/functions.json --skip-dry-run

