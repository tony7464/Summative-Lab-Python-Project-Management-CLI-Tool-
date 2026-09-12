# Project Management CLI

A Python command-line project tracker for a small development team. Administrators can create users, attach projects to those users, assign tasks, persist everything locally as JSON, and ask a reusable insight client for a summary, risk note, or next-step suggestion.

The app is organized around object relationships:

- **One-to-many:** a `User` owns many `Project` records
- **One-to-many:** a `Project` contains many `Task` records
- **Many-to-many:** a `Task` can have many contributing users, and a user can contribute to many tasks

## Features

- Create and list users from the command line
- Add projects to a specific user and list that user's projects
- Assign tasks, add extra contributors, and mark work complete
- Edit project and task fields; every change is saved to `data/project_data.json`
- Validate names, emails, statuses, and due dates through properties and setters
- Inherit shared behavior (`Person` → `User`, `WorkItem` → `Task`)
- Format tables with **Rich** and **tabulate**
- Parse flexible due dates with **python-dateutil**
- Generate project insights through a reusable client that talks to **Ollama** when available and falls back locally when it is not

## Requirements

- Python 3.10+
- pip, or [Pipenv](https://pipenv.pypa.io/) if you prefer a Pipfile workflow

## Setup

Clone the repository and move into the project folder:

```bash
git clone git@github.com:tony7464/Summative-Lab-Python-Project-Management-CLI-Tool-.git
cd Summative-Lab-Python-Project-Management-CLI-Tool-
```

### Option 1: pip and a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Option 2: Pipenv

```bash
pip install pipenv
pipenv install
pipenv shell
```

## How to run the CLI

From the project root:

```bash
python main.py --help
python main.py add-user --help
```

If no command is given, the tool prints the full help text.

The repository includes sample data in `data/project_data.json` so `list-users` and `list-projects` work immediately after setup.

## Example commands

```bash
python main.py add-user --name "Alex" --email "alex@example.com"
python main.py add-user --name "Jordan" --email "jordan@example.com"

python main.py add-project --user "Alex" --title "CLI Tool" \
  --description "Build project tracker" --due-date 2026-10-01

python main.py add-task --project "CLI Tool" \
  --title "Implement add-task command" --assigned-to "Alex"

python main.py add-task --project "CLI Tool" \
  --title "Write README" --assigned-to "Jordan"

python main.py add-contributor --project "CLI Tool" \
  --task "Implement add-task command" --user "Jordan"

python main.py complete-task --project "CLI Tool" \
  --task "Implement add-task command"

python main.py list-users
python main.py list-projects --user "Alex"
python main.py list-projects --overdue
python main.py list-tasks --project "CLI Tool"
python main.py list-tasks --project "CLI Tool" --status in_progress
python main.py start-task --project "Docs Site" --task "Outline setup guide"
python main.py show-project --project "CLI Tool"

python main.py edit-project --title "CLI Tool" --due-date "October 15, 2026"
python main.py edit-task --project "CLI Tool" --task "Write README" --status in_progress

python main.py summarize-project --project "CLI Tool"
python main.py suggest-next --project "CLI Tool"
python main.py assess-risks --project "CLI Tool"
```

Due dates accept ISO values such as `2026-10-01` and written dates such as `October 15, 2026`.

## File structure

```text
.
├── main.py                 # CLI entry point
├── cli/
│   ├── parser.py           # argparse subcommands
│   └── handlers.py         # command handlers
├── models/
│   ├── person.py           # Person base class
│   ├── user.py             # User accounts
│   ├── work_item.py        # Shared title/status behavior
│   ├── project.py          # Projects and progress
│   └── task.py             # Tasks and contributors
├── services/
│   ├── storage_service.py  # JSON load/save and object graph
│   └── ai_client.py        # Insight client + Ollama/local providers
├── utils/
│   ├── formatters.py       # Rich / tabulate output
│   ├── validators.py       # Dates, status, required text
│   └── errors.py           # User-facing exceptions
├── data/
│   └── project_data.json   # Persisted users, projects, and tasks
├── requirements.txt
├── Pipfile
└── README.md
```

The CLI layer only parses input and prints results. Models own relationships and validation. `StorageService` owns file I/O. `InsightService` owns any external or fallback insight call.

## External packages

All runtime dependencies are listed in both `requirements.txt` and `Pipfile`:

| Package | How it is used |
| --- | --- |
| `rich` | Colored status messages and framed panels |
| `tabulate` | User, project, and task tables |
| `python-dateutil` | Flexible due-date parsing |
| `requests` | HTTP client for the optional Ollama insight service |

## External service / AI client

`summarize-project`, `suggest-next`, and `assess-risks` all go through `InsightService` in `services/ai_client.py`. That facade sends structured project and task data to a reusable `InsightClient`.

Provider chain:

1. **Ollama** (`OllamaInsightClient`) posts to `http://localhost:11434/api/generate` using `requests`
2. If Ollama is not running, the request times out, or the model is missing, the service prints a clear failure note and uses `LocalInsightClient`
3. The local client still reads the same structured payload and returns a summary, risk note, or next-step suggestion

The CLI never imports `requests` or talks to Ollama itself. To add another provider later, subclass `InsightClient` and register it in `InsightService`.

### Optional Ollama setup

Ollama is optional. The insight commands work without it.

1. Install Ollama from [https://ollama.com](https://ollama.com)
2. Pull a model, for example `ollama pull llama3.2`
3. Leave the Ollama app/server running

Environment variables:

| Variable | Meaning | Default |
| --- | --- | --- |
| `TRACKER_INSIGHT_PROVIDER` | `auto`, `ollama`, or `local` | `auto` |
| `OLLAMA_HOST` | Ollama base URL | `http://localhost:11434` |
| `OLLAMA_MODEL` | Model name | `llama3.2` |

Examples:

```bash
TRACKER_INSIGHT_PROVIDER=local python main.py summarize-project --project "CLI Tool"
OLLAMA_MODEL=llama3.2 python main.py assess-risks --project "CLI Tool"
```

## Persistence

Users, projects, tasks, and ID counters are stored in `data/project_data.json`.

- A missing file is created automatically
- Empty files start as a blank store
- Malformed JSON raises a clear error and, when possible, writes a `.json.corrupt` backup
- Saves write to a temporary file first, then replace the real file

## Known issues and limitations

- Project titles must be unique across the whole tracker so commands can look them up by title
- Task titles must be unique inside a single project
- User names must be unique because most commands find people by name
- Ollama is not bundled with this project; without it, insight commands use the local fallback
- Generated summaries are brief status notes, not a replacement for a full project report
- There is no login or permission system; any local user can run admin commands
