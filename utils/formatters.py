"""CLI display helpers built with Rich and tabulate."""

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from tabulate import tabulate

console = Console()


def print_success(message):
    """Print a success message.

    Args:
        message: Text to display.
    """
    console.print(f"[bold green]Success:[/bold green] {message}")


def print_error(message):
    """Print an error message.

    Args:
        message: Text to display.
    """
    console.print(f"[bold red]Error:[/bold red] {message}")


def print_warning(message):
    """Print a warning message.

    Args:
        message: Text to display.
    """
    console.print(f"[bold yellow]Warning:[/bold yellow] {message}")


def print_table(title, headers, rows, empty_message=None):
    """Render a titled table, or a friendly empty-state message.

    Args:
        title: Table heading.
        headers: Column names.
        rows: Sequence of row sequences.
        empty_message: Optional text shown when there are no rows.
    """
    if not rows:
        console.print(Panel(empty_message or "Nothing to show yet.", title=title))
        return
    table = tabulate(rows, headers=headers, tablefmt="simple")
    console.print(Panel(table, title=title, expand=False))


def format_users(users):
    """Display the user list.

    Args:
        users: Collection of User objects.
    """
    rows = [
        [user.id, user.name, user.email, len(user.projects)]
        for user in users
    ]
    print_table(
        "Users",
        ["ID", "Name", "Email", "Projects"],
        rows,
        empty_message="No users yet. Try: python main.py add-user --name Alex --email alex@example.com",
    )


def format_projects(projects, heading="Projects"):
    """Display the project list.

    Args:
        projects: Collection of Project objects.
        heading: Optional table title.
    """
    rows = []
    for project in projects:
        due = project.due_date.isoformat() if project.due_date else "—"
        owner = project.owner.name if project.owner else "—"
        flag = " overdue" if project.is_overdue else ""
        rows.append(
            [
                project.id,
                project.title,
                owner,
                due + flag,
                f"{project.progress}%",
                len(project.tasks),
            ]
        )
    print_table(
        heading,
        ["ID", "Title", "Owner", "Due", "Progress", "Tasks"],
        rows,
        empty_message="No projects found. Add one with add-project.",
    )


def format_tasks(project):
    """Display tasks for a single project.

    Args:
        project: Project whose tasks should be listed.
    """
    rows = []
    for task in project.tasks:
        assignee = task.assigned_to.name if task.assigned_to else "—"
        contributors = ", ".join(user.name for user in task.contributors) or "—"
        rows.append([task.id, task.title, task.status, assignee, contributors])
    print_table(
        f"Tasks · {project.title}",
        ["ID", "Title", "Status", "Assigned To", "Contributors"],
        rows,
        empty_message=f"No tasks on '{project.title}' yet. Add one with add-task.",
    )


def format_project_detail(project):
    """Display a detailed project card.

    Args:
        project: Project to describe.
    """
    owner = project.owner.name if project.owner else "unassigned"
    due = project.due_date.isoformat() if project.due_date else "no due date"
    body = Text()
    body.append(f"{project.description or 'No description provided.'}\n\n")
    body.append(f"Owner: {owner}\n")
    body.append(f"Due: {due}")
    if project.is_overdue:
        body.append(" (overdue)", style="bold red")
    body.append(f"\nProgress: {project.progress}%")
    body.append(f"\nTasks: {len(project.tasks)} total, {len(project.open_tasks)} open")
    console.print(Panel(body, title=project.title, expand=False))
    format_tasks(project)


def format_insight(title, text, source):
    """Display generated insight text.

    Args:
        title: Panel title.
        text: Insight body.
        source: Provider name, such as ollama or local.
    """
    console.print(
        Panel(
            text,
            title=f"{title} · {source}",
            border_style="cyan",
            expand=False,
        )
    )
