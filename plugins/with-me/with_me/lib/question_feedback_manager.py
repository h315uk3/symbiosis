#!/usr/bin/env python3
"""
Question Feedback Manager for with-me plugin

Manages question feedback data including sessions, statistics, and persistence.
Follows as-you plugin patterns for consistency.
"""

import json
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, TypedDict


@dataclass(frozen=True)
class WithMeConfig:
    """Immutable configuration for with-me plugin"""

    project_root: Path
    claude_dir: Path
    with_me_dir: Path
    feedback_file: Path

    @classmethod
    def from_environment(cls):
        """
        Load configuration from environment variables

        Examples:
            >>> config = WithMeConfig.from_environment()
            >>> config.feedback_file.name
            'question_feedback.json'
        """
        # Use PROJECT_ROOT if available, otherwise find git root
        if "PROJECT_ROOT" in os.environ:
            project_root = Path(os.environ["PROJECT_ROOT"])
        else:
            # Try to find git root from current directory
            current = Path.cwd()
            project_root = current
            for parent in [current, *current.parents]:
                if (parent / ".git").exists():
                    project_root = parent
                    break

        claude_dir = Path(
            os.getenv("CLAUDE_DIR", os.path.join(project_root, ".claude"))
        )
        with_me_dir = claude_dir / "with_me"
        feedback_file = with_me_dir / "question_feedback.json"

        return cls(
            project_root=project_root,
            claude_dir=claude_dir,
            with_me_dir=with_me_dir,
            feedback_file=feedback_file,
        )


class QuestionData(TypedDict, total=False):
    """
    Type definition for a single question

    v0.3.0 Extensions:
    - dimension_beliefs_before: Posterior distributions before question
    - dimension_beliefs_after: Posterior distributions after answer
    """

    question: str
    dimension: str
    timestamp: str
    context: dict[str, Any]
    answer: dict[str, Any]
    reward_scores: dict[str, float]
    # v0.3.0: Bayesian belief tracking
    dimension_beliefs_before: dict[str, dict] | None  # Serialized HypothesisSet
    dimension_beliefs_after: dict[str, dict] | None  # Serialized HypothesisSet


class SessionSummary(TypedDict):
    """Type definition for session summary"""

    total_questions: int
    avg_reward_per_question: float
    total_info_gain: float
    final_clarity_score: float
    dimensions_resolved: list[str]
    session_efficiency: float


class SessionData(TypedDict, total=False):
    """
    Type definition for a session

    v0.3.0 Extensions:
    - initial_dimension_beliefs: Starting posterior distributions
    - final_dimension_beliefs: Ending posterior distributions
    """

    session_id: str
    started_at: str
    completed_at: str | None
    duration_seconds: int | None
    questions: list[QuestionData]
    summary: SessionSummary | None
    # v0.3.0: Bayesian belief tracking
    initial_dimension_beliefs: dict[str, dict] | None  # Serialized HypothesisSet
    final_dimension_beliefs: dict[str, dict] | None  # Serialized HypothesisSet


class FeedbackData(TypedDict, total=False):
    """Type definition for feedback file structure"""

    sessions: list[SessionData]
    statistics: dict[str, Any]


def load_feedback(feedback_file: Path) -> FeedbackData:
    """
    Load question feedback data with error handling

    Args:
        feedback_file: Path to question_feedback.json

    Returns:
        Feedback data with guaranteed keys

    Examples:
        >>> from pathlib import Path
        >>> import tempfile
        >>> with tempfile.NamedTemporaryFile(
        ...     mode="w", suffix=".json", delete=False
        ... ) as f:
        ...     _ = f.write('{"sessions": [], "statistics": {}}')
        ...     temp_path = Path(f.name)
        >>> data = load_feedback(temp_path)
        >>> "sessions" in data
        True
        >>> "statistics" in data
        True
        >>> temp_path.unlink()
    """
    default_data: FeedbackData = {
        "sessions": [],
        "statistics": {
            "total_sessions": 0,
            "total_questions": 0,
            "avg_questions_per_session": 0.0,
            "best_questions": [],
            "dimension_stats": {},
        },
    }

    if not feedback_file.exists():
        return default_data

    try:
        with open(feedback_file, encoding="utf-8") as f:
            data = json.load(f)

        # Ensure all required keys exist
        for key, value in default_data.items():
            if key not in data:
                data[key] = value

        return data
    except (json.JSONDecodeError, OSError) as e:
        print(f"Warning: Could not load feedback file: {e}")
        return default_data


def save_feedback(feedback_file: Path, data: FeedbackData) -> None:
    """
    Save feedback data with atomic write

    Uses temp file + rename for atomicity (prevents corruption)

    Args:
        feedback_file: Path to question_feedback.json
        data: Feedback data to save

    Examples:
        >>> from pathlib import Path
        >>> import tempfile
        >>> import os
        >>> temp_dir = Path(tempfile.mkdtemp())
        >>> feedback_file = temp_dir / "feedback.json"
        >>> data = {"sessions": [], "statistics": {}}
        >>> save_feedback(feedback_file, data)
        >>> feedback_file.exists()
        True
        >>> import shutil
        >>> shutil.rmtree(temp_dir)
    """
    # Ensure parent directory exists
    feedback_file.parent.mkdir(parents=True, exist_ok=True)

    # Atomic write: temp file → rename
    temp_file = feedback_file.with_suffix(".tmp")
    try:
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        temp_file.replace(feedback_file)
    except Exception as e:
        if temp_file.exists():
            temp_file.unlink()
        raise OSError(f"Failed to save feedback: {e}") from e


class QuestionFeedbackManager:
    """Manage question feedback sessions and statistics"""

    def __init__(self, feedback_file: Path | None = None):
        """
        Initialize manager with feedback file path

        Args:
            feedback_file: Path to feedback JSON (defaults to config location)
        """
        if feedback_file is None:
            config = WithMeConfig.from_environment()
            feedback_file = config.feedback_file

        self.feedback_file = feedback_file
        self.data = load_feedback(feedback_file)

    def start_session(
        self, initial_dimension_beliefs: dict[str, dict] | None = None
    ) -> str:
        """
        Start a new session

        Args:
            initial_dimension_beliefs: Optional initial Bayesian beliefs (v0.3.0)

        Returns:
            Session ID (ISO timestamp)

        Examples:
            >>> manager = QuestionFeedbackManager(Path("/tmp/test_feedback.json"))
            >>> session_id = manager.start_session()
            >>> len(session_id) > 0
            True
        """
        session_id = datetime.now().isoformat()
        session: SessionData = {
            "session_id": session_id,
            "started_at": session_id,
            "completed_at": None,
            "duration_seconds": None,
            "questions": [],
            "summary": None,
            "initial_dimension_beliefs": initial_dimension_beliefs,
            "final_dimension_beliefs": None,
        }

        self.data["sessions"].append(session)
        save_feedback(self.feedback_file, self.data)

        return session_id

    def record_question(
        self,
        session_id: str,
        question: str,
        dimension: str,
        context: dict[str, Any],
        answer: dict[str, Any],
        reward_scores: dict[str, float],
        dimension_beliefs_before: dict[str, dict] | None = None,
        dimension_beliefs_after: dict[str, dict] | None = None,
    ) -> None:
        """
        Record a question-answer pair in a session

        Args:
            session_id: Session identifier
            question: Question text
            dimension: Target dimension
            context: Context with uncertainties before/after
            answer: Answer data (word_count, has_examples)
            reward_scores: Reward components and total
            dimension_beliefs_before: Optional Bayesian beliefs before question (v0.3.0)
            dimension_beliefs_after: Optional Bayesian beliefs after answer (v0.3.0)
        """
        session = self._find_session(session_id)
        if session is None:
            raise ValueError(f"Session {session_id} not found")

        question_data: QuestionData = {
            "question": question,
            "dimension": dimension,
            "timestamp": datetime.now().isoformat(),
            "context": context,
            "answer": answer,
            "reward_scores": reward_scores,
            "dimension_beliefs_before": dimension_beliefs_before,
            "dimension_beliefs_after": dimension_beliefs_after,
        }

        session["questions"].append(question_data)
        save_feedback(self.feedback_file, self.data)

    def complete_session(
        self,
        session_id: str,
        final_uncertainties: dict[str, float],
        final_dimension_beliefs: dict[str, dict] | None = None,
    ) -> SessionSummary:
        """
        Complete a session and generate summary

        Args:
            session_id: Session identifier
            final_uncertainties: Final uncertainty scores
            final_dimension_beliefs: Optional final Bayesian beliefs (v0.3.0)

        Returns:
            Session summary

        Examples:
            >>> manager = QuestionFeedbackManager(Path("/tmp/test_feedback.json"))
            >>> session_id = manager.start_session()
            >>> manager.record_question(
            ...     session_id,
            ...     "What?",
            ...     "purpose",
            ...     {
            ...         "uncertainties_before": {"purpose": 1.0},
            ...         "uncertainties_after": {"purpose": 0.3},
            ...     },
            ...     {"word_count": 50, "has_examples": True},
            ...     {"info_gain": 0.7, "total_reward": 0.85},
            ... )
            >>> summary = manager.complete_session(session_id, {"purpose": 0.3})
            >>> summary["total_questions"]
            1
        """
        session = self._find_session(session_id)
        if session is None:
            raise ValueError(f"Session {session_id} not found")

        # Calculate summary
        questions = session["questions"]
        total_questions = len(questions)
        total_reward = sum(q["reward_scores"].get("total_reward", 0) for q in questions)
        total_info_gain = sum(
            q["reward_scores"].get("components", {}).get("info_gain", 0)
            for q in questions
        )
        final_clarity = 1.0 - (
            sum(final_uncertainties.values()) / len(final_uncertainties)
            if final_uncertainties
            else 0
        )

        dimensions_resolved = [
            dim for dim, unc in final_uncertainties.items() if unc < 0.3
        ]

        summary: SessionSummary = {
            "total_questions": total_questions,
            "avg_reward_per_question": total_reward / total_questions
            if total_questions > 0
            else 0,
            "total_info_gain": total_info_gain,
            "final_clarity_score": final_clarity,
            "dimensions_resolved": dimensions_resolved,
            "session_efficiency": total_info_gain / total_questions
            if total_questions > 0
            else 0,
        }

        # Update session
        session["completed_at"] = datetime.now().isoformat()
        start_time = datetime.fromisoformat(session["started_at"])
        end_time = datetime.fromisoformat(session["completed_at"])
        session["duration_seconds"] = int((end_time - start_time).total_seconds())
        session["summary"] = summary
        session["final_dimension_beliefs"] = final_dimension_beliefs  # v0.3.0

        # Update statistics
        self._update_statistics()

        save_feedback(self.feedback_file, self.data)

        return summary

    def get_statistics(self) -> dict[str, Any]:
        """
        Get current statistics

        Returns:
            Statistics dictionary
        """
        return self.data.get("statistics", {})

    def get_recent_sessions(self, limit: int = 5) -> list[SessionData]:
        """
        Get most recent sessions

        Args:
            limit: Maximum number of sessions to return

        Returns:
            List of recent sessions
        """
        sessions = self.data.get("sessions", [])
        return sessions[-limit:]

    def _find_session(self, session_id: str) -> SessionData | None:
        """Find session by ID"""
        for session in self.data["sessions"]:
            if session["session_id"] == session_id:
                return session
        return None

    def _update_statistics(self) -> None:
        """Update global statistics"""
        sessions = self.data.get("sessions", [])
        completed_sessions = [s for s in sessions if s.get("completed_at")]

        if not completed_sessions:
            return

        total_sessions = len(completed_sessions)
        total_questions = sum(len(s["questions"]) for s in completed_sessions)

        # Best questions (highest avg reward)
        question_rewards = {}
        for session in completed_sessions:
            for q in session["questions"]:
                question_text = q["question"]
                reward = q["reward_scores"].get("total_reward", 0)

                if question_text not in question_rewards:
                    question_rewards[question_text] = {
                        "question": question_text,
                        "dimension": q["dimension"],
                        "total_reward": 0,
                        "count": 0,
                    }

                question_rewards[question_text]["total_reward"] += reward
                question_rewards[question_text]["count"] += 1

        # Calculate averages and sort
        best_questions = []
        for data in question_rewards.values():
            avg_reward = data["total_reward"] / data["count"]
            best_questions.append(
                {
                    "question": data["question"],
                    "avg_reward": avg_reward,
                    "times_used": data["count"],
                    "dimension": data["dimension"],
                }
            )

        best_questions.sort(key=lambda x: x["avg_reward"], reverse=True)

        # Dimension stats
        dimension_stats = {}
        for dim in ["purpose", "data", "behavior", "constraints", "quality"]:
            dim_questions = []
            for session in completed_sessions:
                dim_questions.extend(
                    [q for q in session["questions"] if q["dimension"] == dim]
                )

            if dim_questions:
                avg_info_gain = sum(
                    q["reward_scores"].get("components", {}).get("info_gain", 0)
                    for q in dim_questions
                ) / len(dim_questions)

                # Average questions to resolve (sessions where this dimension was resolved)
                resolved_sessions = [
                    s
                    for s in completed_sessions
                    if s.get("summary")
                    and dim in s["summary"].get("dimensions_resolved", [])
                ]
                avg_questions_to_resolve = (
                    sum(
                        len([q for q in s["questions"] if q["dimension"] == dim])
                        for s in resolved_sessions
                    )
                    / len(resolved_sessions)
                    if resolved_sessions
                    else 0
                )

                dimension_stats[dim] = {
                    "avg_info_gain": avg_info_gain,
                    "avg_questions_to_resolve": avg_questions_to_resolve,
                }

        self.data["statistics"] = {
            "total_sessions": total_sessions,
            "total_questions": total_questions,
            "avg_questions_per_session": total_questions / total_sessions
            if total_sessions > 0
            else 0,
            "best_questions": best_questions[:10],  # Top 10
            "dimension_stats": dimension_stats,
        }


