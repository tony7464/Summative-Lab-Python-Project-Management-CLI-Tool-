"""Reusable insight clients for project summaries and next-step notes.

The CLI never talks to a model directly. Command handlers send structured
project data into InsightService, which chooses a provider and returns
readable text. New providers can be added by subclassing InsightClient.
"""

from __future__ import annotations

import json
import os
from abc import ABC, abstractmethod

import requests

from utils.errors import ServiceError


class InsightClient(ABC):
    """Shared interface for any summary/risk/next-step provider."""

    name = "insight"

    @abstractmethod
    def generate(self, prompt, context):
        """Create insight text from a prompt and structured context.

        Args:
            prompt: Instruction describing the desired output.
            context: JSON-serializable project/task payload.

        Returns:
            str: Readable insight text.

        Raises:
            ServiceError: If the provider cannot complete the request.
        """


class OllamaInsightClient(InsightClient):
    """HTTP client for a local Ollama server."""

    name = "ollama"

    def __init__(self, base_url=None, model=None, timeout=8):
        """Configure the Ollama endpoint and model.

        Args:
            base_url: Ollama host. Defaults to OLLAMA_HOST or localhost.
            model: Model name. Defaults to OLLAMA_MODEL or llama3.2.
            timeout: Request timeout in seconds.
        """
        self.base_url = (
            base_url or os.getenv("OLLAMA_HOST") or "http://localhost:11434"
        ).rstrip("/")
        self.model = model or os.getenv("OLLAMA_MODEL") or "llama3.2"
        self.timeout = timeout

    def generate(self, prompt, context):
        """Send structured project data to Ollama and return the reply.

        Args:
            prompt: Instruction for the model.
            context: Project/task payload.

        Returns:
            str: Model-generated insight.

        Raises:
            ServiceError: If the HTTP request fails or the response is empty.
        """
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model,
            "prompt": (
                f"{prompt}\n\nProject data (JSON):\n"
                f"{json.dumps(context, indent=2)}\n\n"
                "Respond in 4-8 concise sentences. Do not invent tasks."
            ),
            "stream": False,
        }
        try:
            response = requests.post(url, json=payload, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
        except requests.Timeout as exc:
            raise ServiceError(
                f"Ollama timed out after {self.timeout}s at {self.base_url}."
            ) from exc
        except requests.ConnectionError as exc:
            raise ServiceError(
                f"Could not connect to Ollama at {self.base_url}."
            ) from exc
        except requests.HTTPError as exc:
            status = exc.response.status_code if exc.response is not None else "unknown"
            raise ServiceError(f"Ollama returned HTTP {status}.") from exc
        except requests.RequestException as exc:
            raise ServiceError(f"Ollama request failed: {exc}") from exc
        except ValueError as exc:
            raise ServiceError("Ollama returned a non-JSON response.") from exc

        text = (data.get("response") or "").strip()
        if not text:
            raise ServiceError("Ollama returned an empty response.")
        return text


class LocalInsightClient(InsightClient):
    """Deterministic fallback that still uses structured project data."""

    name = "local"

    def generate(self, prompt, context):
        """Build a readable note from project fields without a remote model.

        Args:
            prompt: Instruction describing the desired output.
            context: Project/task payload.

        Returns:
            str: Locally generated insight.
        """
        mode = _detect_mode(prompt)
        title = context.get("title", "Untitled project")
        owner = context.get("owner") or "an unassigned owner"
        due = context.get("due_date") or "no due date"
        progress = context.get("progress", 0)
        tasks = context.get("tasks") or []
        open_count = context.get("open_task_count", 0)
        overdue = context.get("is_overdue", False)
        unassigned = [task["title"] for task in tasks if not task.get("assigned_to")]
        blocked = [
            task["title"]
            for task in tasks
            if task.get("status") == "todo" and not task.get("assigned_to")
        ]
        in_progress = [
            task["title"] for task in tasks if task.get("status") == "in_progress"
        ]
        completed = [task["title"] for task in tasks if task.get("status") == "complete"]

        if mode == "risk":
            risks = []
            if overdue:
                risks.append(f"{title} is past its due date ({due}) and still open.")
            if open_count and not in_progress:
                risks.append("Open work exists, but nothing is marked in progress.")
            if unassigned:
                risks.append(
                    "Unassigned tasks may stall the schedule: " + ", ".join(unassigned) + "."
                )
            if not tasks:
                risks.append("The project has no tasks, so progress cannot be measured.")
            if not risks:
                risks.append(
                    f"{title} looks healthy: {progress}% complete with owners on active work."
                )
            return " ".join(risks)

        if mode == "next":
            if in_progress:
                return (
                    f"Continue '{in_progress[0]}' before starting new work on {title}. "
                    f"That keeps the current in-progress item moving."
                )
            if blocked:
                return (
                    f"Assign and start '{blocked[0]}' next. "
                    f"It is still todo and has no owner."
                )
            if open_count:
                open_titles = [
                    task["title"] for task in tasks if task.get("status") != "complete"
                ]
                return f"Start '{open_titles[0]}' next to keep {title} moving."
            return f"{title} has no remaining tasks. Review the completed work or add a follow-up."

        summary = [
            f"{title} is owned by {owner} and is {progress}% complete with a due date of {due}.",
            f"There are {len(tasks)} task(s) and {open_count} still open.",
        ]
        if completed:
            summary.append("Completed: " + ", ".join(completed) + ".")
        if in_progress:
            summary.append("In progress: " + ", ".join(in_progress) + ".")
        if unassigned:
            summary.append("Needs an owner: " + ", ".join(unassigned) + ".")
        if overdue:
            summary.append("This project is overdue and needs attention.")
        elif not tasks:
            summary.append("Add a first task so the team can track progress.")
        return " ".join(summary)


class InsightService:
    """Facade used by the CLI to request project insights.

    Configuration:
        TRACKER_INSIGHT_PROVIDER: auto, ollama, or local
        OLLAMA_HOST: Ollama base URL
        OLLAMA_MODEL: Model name
    """

    PROMPTS = {
        "summary": (
            "Write a short project-management summary of status, owners, "
            "and remaining work."
        ),
        "risk": (
            "Write a short risk note. Call out overdue work, unassigned "
            "tasks, and stalled items."
        ),
        "next": (
            "Suggest one concrete next step the team should take. "
            "Name a specific task when possible."
        ),
    }

    def __init__(self, provider=None, client=None):
        """Create the facade with an optional explicit client.

        Args:
            provider: auto, ollama, or local. Defaults to env/auto.
            client: Optional InsightClient used for tests or custom providers.
        """
        self.provider = (
            provider or os.getenv("TRACKER_INSIGHT_PROVIDER") or "auto"
        ).strip().lower()
        self._client = client
        self.last_source = None

    def summarize_project(self, project):
        """Return a project summary.

        Args:
            project: Project instance.

        Returns:
            str: Summary text.
        """
        return self._run("summary", project)

    def assess_risks(self, project):
        """Return a risk note for the project.

        Args:
            project: Project instance.

        Returns:
            str: Risk note.
        """
        return self._run("risk", project)

    def suggest_next_step(self, project):
        """Return a suggested next step.

        Args:
            project: Project instance.

        Returns:
            str: Next-step recommendation.
        """
        return self._run("next", project)

    def _run(self, mode, project):
        """Generate insight text and fall back locally when needed.

        Args:
            mode: summary, risk, or next.
            project: Project instance.

        Returns:
            str: Insight text from the selected provider or fallback.
        """
        prompt = self.PROMPTS[mode]
        context = project.context_payload()
        clients = self._clients()
        errors = []
        for client in clients:
            try:
                text = client.generate(prompt, context)
                self.last_source = client.name
                if errors:
                    return (
                        f"AI service unavailable ({errors[0]}). "
                        f"Using {client.name} fallback:\n{text}"
                    )
                return text
            except ServiceError as exc:
                errors.append(str(exc))
        self.last_source = "local"
        fallback = LocalInsightClient()
        note = fallback.generate(prompt, context)
        if errors:
            return (
                "AI service unavailable "
                f"({errors[0]}). Local fallback:\n{note}"
            )
        return note

    def _clients(self):
        """Return the provider chain for the configured mode.

        Returns:
            list[InsightClient]: Clients to try in order.

        Raises:
            ServiceError: If the provider name is unknown.
        """
        if self._client is not None:
            return [self._client]
        if self.provider == "local":
            return [LocalInsightClient()]
        if self.provider == "ollama":
            return [OllamaInsightClient()]
        if self.provider == "auto":
            return [OllamaInsightClient(), LocalInsightClient()]
        raise ServiceError(
            f"Unknown insight provider '{self.provider}'. Use auto, ollama, or local."
        )


def _detect_mode(prompt):
    """Infer the requested insight type from the prompt text.

    Args:
        prompt: Instruction sent to a client.

    Returns:
        str: summary, risk, or next.
    """
    lowered = prompt.lower()
    if "risk" in lowered:
        return "risk"
    if "next step" in lowered or "next" in lowered:
        return "next"
    return "summary"
