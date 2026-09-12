"""Command handlers. CLI parsing stays in parser.py; I/O stays in services."""

from services.ai_client import InsightService
from utils.errors import TrackerError
from utils.formatters import (
    format_insight,
    format_project_detail,
    format_projects,
    format_tasks,
    format_users,
    print_error,
    print_success,
)


def dispatch(args, storage):
    """Route a parsed argparse namespace to the matching handler.

    Args:
        args: Parsed CLI arguments.
        storage: Loaded StorageService.

    Returns:
        int: Process exit code.
    """
    if not getattr(args, "command", None):
        return 0

    handlers = {
        "add-user": add_user,
        "list-users": list_users,
        "add-project": add_project,
        "list-projects": list_projects,
        "show-project": show_project,
        "edit-project": edit_project,
        "add-task": add_task,
        "list-tasks": list_tasks,
        "complete-task": complete_task,
        "edit-task": edit_task,
        "add-contributor": add_contributor,
        "summarize-project": summarize_project,
        "suggest-next": suggest_next,
        "assess-risks": assess_risks,
    }
    handler = handlers.get(args.command)
    if handler is None:
        print_error(f"Unknown command: {args.command}")
        return 1
    try:
        handler(args, storage)
    except (TrackerError, ValueError) as exc:
        print_error(str(exc))
        return 1
    return 0


def add_user(args, storage):
    """Create a user and persist the change.

    Args:
        args: Parsed arguments with name and email.
        storage: Loaded StorageService.
    """
    user = storage.add_user(name=args.name, email=args.email)
    print_success(f"Added user {user.name} <{user.email}> (id {user.id}).")


def list_users(args, storage):
    """List all users.

    Args:
        args: Parsed arguments.
        storage: Loaded StorageService.
    """
    format_users(storage.users)


def add_project(args, storage):
    """Create a project for an existing user.

    Args:
        args: Parsed arguments with user, title, and optional details.
        storage: Loaded StorageService.
    """
    user = storage.require_user(args.user)
    project = storage.add_project(
        user=user,
        title=args.title,
        description=args.description,
        due_date=args.due_date,
    )
    print_success(f"Added project '{project.title}' for {user.name}.")


def list_projects(args, storage):
    """List all projects or only those owned by one user.

    Args:
        args: Parsed arguments with optional user filter.
        storage: Loaded StorageService.
    """
    if args.user:
        user = storage.require_user(args.user)
        format_projects(user.projects, heading=f"Projects · {user.name}")
        return
    format_projects(storage.projects)


def show_project(args, storage):
    """Show one project and its tasks.

    Args:
        args: Parsed arguments with project title.
        storage: Loaded StorageService.
    """
    project = storage.require_project(args.project)
    format_project_detail(project)


def edit_project(args, storage):
    """Update persisted project fields.

    Args:
        args: Parsed arguments with the current title and optional new values.
        storage: Loaded StorageService.
    """
    project = storage.require_project(args.title)
    if args.new_title is None and args.description is None and args.due_date is None:
        raise ValueError("Provide --new-title, --description, or --due-date to edit a project.")
    if args.new_title:
        clash = next(
            (
                item
                for item in storage.projects
                if item is not project
                and item.title.lower() == args.new_title.strip().lower()
            ),
            None,
        )
        if clash:
            raise ValueError(f"A project titled '{args.new_title}' already exists.")
        project.title = args.new_title
    if args.description is not None:
        project.description = args.description
    if args.due_date is not None:
        project.due_date = args.due_date
    storage.save()
    print_success(f"Updated project '{project.title}'.")


def add_task(args, storage):
    """Create a task on a project.

    Args:
        args: Parsed arguments with project, title, and optional assignment.
        storage: Loaded StorageService.
    """
    project = storage.require_project(args.project)
    assignee = storage.require_user(args.assigned_to) if args.assigned_to else None
    task = storage.add_task(
        project=project,
        title=args.title,
        assigned_to=assignee,
        status=args.status,
    )
    print_success(f"Added task '{task.title}' to '{project.title}'.")


def list_tasks(args, storage):
    """List tasks on a project.

    Args:
        args: Parsed arguments with project title.
        storage: Loaded StorageService.
    """
    project = storage.require_project(args.project)
    format_tasks(project)


def complete_task(args, storage):
    """Mark a task complete and save.

    Args:
        args: Parsed arguments with project and task titles.
        storage: Loaded StorageService.
    """
    project = storage.require_project(args.project)
    task = storage.require_task(project, args.task)
    task.mark_complete()
    storage.save()
    print_success(f"Completed '{task.title}' on '{project.title}'.")


def edit_task(args, storage):
    """Update persisted task fields.

    Args:
        args: Parsed arguments with project, task, and optional new values.
        storage: Loaded StorageService.
    """
    project = storage.require_project(args.project)
    task = storage.require_task(project, args.task)
    if args.new_title is None and args.status is None and args.assigned_to is None:
        raise ValueError("Provide --new-title, --status, or --assigned-to to edit a task.")
    if args.new_title:
        clash = project.find_task(args.new_title)
        if clash is not None and clash is not task:
            raise ValueError(
                f"Project '{project.title}' already has a task titled '{args.new_title}'."
            )
        task.title = args.new_title
    if args.status:
        task.status = args.status
    if args.assigned_to:
        task.assigned_to = storage.require_user(args.assigned_to)
    storage.save()
    print_success(f"Updated task '{task.title}'.")


def add_contributor(args, storage):
    """Attach another user to a task.

    Args:
        args: Parsed arguments with project, task, and user names.
        storage: Loaded StorageService.
    """
    project = storage.require_project(args.project)
    task = storage.require_task(project, args.task)
    user = storage.require_user(args.user)
    task.add_contributor(user)
    storage.save()
    print_success(f"Added {user.name} as a contributor on '{task.title}'.")


def summarize_project(args, storage):
    """Generate a project summary through the insight service.

    Args:
        args: Parsed arguments with project title.
        storage: Loaded StorageService.
    """
    _run_insight(args, storage, "summary")


def suggest_next(args, storage):
    """Generate a next-step suggestion through the insight service.

    Args:
        args: Parsed arguments with project title.
        storage: Loaded StorageService.
    """
    _run_insight(args, storage, "next")


def assess_risks(args, storage):
    """Generate a risk note through the insight service.

    Args:
        args: Parsed arguments with project title.
        storage: Loaded StorageService.
    """
    _run_insight(args, storage, "risk")


def _run_insight(args, storage, mode):
    """Shared helper for insight commands.

    Args:
        args: Parsed arguments with project title.
        storage: Loaded StorageService.
        mode: summary, next, or risk.
    """
    project = storage.require_project(args.project)
    service = InsightService()
    if mode == "summary":
        text = service.summarize_project(project)
        heading = "Project summary"
    elif mode == "next":
        text = service.suggest_next_step(project)
        heading = "Suggested next step"
    else:
        text = service.assess_risks(project)
        heading = "Risk note"
    format_insight(heading, text, service.last_source or "insight")
