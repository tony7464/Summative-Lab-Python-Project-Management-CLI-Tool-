"""Argparse setup for the project-management CLI."""

import argparse


def build_parser():
    """Build the top-level parser and all subcommands.

    Returns:
        argparse.ArgumentParser: Configured CLI parser.
    """
    parser = argparse.ArgumentParser(
        prog="python main.py",
        description="Command-line project tracker for users, projects, and tasks.",
        epilog=(
            "Examples:\n"
            "  python main.py add-user --name Alex --email alex@example.com\n"
            "  python main.py add-project --user Alex --title \"CLI Tool\" "
            "--description \"Build project tracker\" --due-date 2026-10-01\n"
            "  python main.py add-task --project \"CLI Tool\" "
            "--title \"Implement add-task command\" --assigned-to Alex\n"
            "  python main.py summarize-project --project \"CLI Tool\"\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", metavar="COMMAND")

    add_user = subparsers.add_parser("add-user", help="Create a new user.")
    add_user.add_argument("--name", required=True, help="User display name.")
    add_user.add_argument("--email", required=True, help="Unique email address.")

    subparsers.add_parser("list-users", help="Show every user in the tracker.")

    add_project = subparsers.add_parser(
        "add-project", help="Add a project owned by an existing user."
    )
    add_project.add_argument("--user", required=True, help="Owner's name.")
    add_project.add_argument("--title", required=True, help="Unique project title.")
    add_project.add_argument(
        "--description", default="", help="Optional project description."
    )
    add_project.add_argument(
        "--due-date",
        dest="due_date",
        help="Optional due date, such as 2026-10-01 or October 1, 2026.",
    )

    list_projects = subparsers.add_parser(
        "list-projects", help="List all projects or only one user's projects."
    )
    list_projects.add_argument("--user", help="Optional owner name to filter by.")
    list_projects.add_argument(
        "--overdue",
        action="store_true",
        help="Show only projects that are past due with open work.",
    )

    show_project = subparsers.add_parser(
        "show-project", help="Show project details and its tasks."
    )
    show_project.add_argument("--project", required=True, help="Project title.")

    edit_project = subparsers.add_parser(
        "edit-project", help="Update a project's title, description, or due date."
    )
    edit_project.add_argument("--title", required=True, help="Current project title.")
    edit_project.add_argument("--new-title", dest="new_title", help="Replacement title.")
    edit_project.add_argument("--description", help="Replacement description.")
    edit_project.add_argument(
        "--due-date", dest="due_date", help="Replacement due date."
    )

    add_task = subparsers.add_parser("add-task", help="Add a task to a project.")
    add_task.add_argument("--project", required=True, help="Project title.")
    add_task.add_argument("--title", required=True, help="Task title.")
    add_task.add_argument(
        "--assigned-to", dest="assigned_to", help="Optional assignee name."
    )
    add_task.add_argument(
        "--status", default="todo", help="todo, in_progress, or complete."
    )

    list_tasks = subparsers.add_parser("list-tasks", help="List tasks on a project.")
    list_tasks.add_argument("--project", required=True, help="Project title.")
    list_tasks.add_argument(
        "--status", help="Optional status filter: todo, in_progress, or complete."
    )

    start_task = subparsers.add_parser(
        "start-task", help="Mark a task in progress and save the change."
    )
    start_task.add_argument("--project", required=True, help="Project title.")
    start_task.add_argument("--task", required=True, help="Task title.")

    complete_task = subparsers.add_parser(
        "complete-task", help="Mark a task complete and save the change."
    )
    complete_task.add_argument("--project", required=True, help="Project title.")
    complete_task.add_argument("--task", required=True, help="Task title.")

    edit_task = subparsers.add_parser(
        "edit-task", help="Update a task's title, status, or assignee."
    )
    edit_task.add_argument("--project", required=True, help="Project title.")
    edit_task.add_argument("--task", required=True, help="Current task title.")
    edit_task.add_argument("--new-title", dest="new_title", help="Replacement title.")
    edit_task.add_argument("--status", help="todo, in_progress, or complete.")
    edit_task.add_argument(
        "--assigned-to", dest="assigned_to", help="Replacement assignee name."
    )

    add_contributor = subparsers.add_parser(
        "add-contributor",
        help="Link another user to a task (many-to-many contributors).",
    )
    add_contributor.add_argument("--project", required=True, help="Project title.")
    add_contributor.add_argument("--task", required=True, help="Task title.")
    add_contributor.add_argument("--user", required=True, help="Contributor name.")

    summarize = subparsers.add_parser(
        "summarize-project",
        help="Generate a project summary through the insight client.",
    )
    summarize.add_argument("--project", required=True, help="Project title.")

    suggest = subparsers.add_parser(
        "suggest-next",
        help="Ask the insight client for a next-step suggestion.",
    )
    suggest.add_argument("--project", required=True, help="Project title.")

    risks = subparsers.add_parser(
        "assess-risks",
        help="Ask the insight client for a short risk note.",
    )
    risks.add_argument("--project", required=True, help="Project title.")

    return parser
