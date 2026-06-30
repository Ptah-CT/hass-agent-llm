"""Follow-up / ask-back tool for Home Agent.

Lets the model ask the user a clarifying question and keep the conversation open
(the voice satellite re-opens the mic without requiring the wake word again),
instead of guessing when information is missing.

HA's ``ChatLog.continue_conversation`` is a *derived* property (true only when the
last assistant message ends in "?"), which is an unreliable heuristic. This tool
gives the model explicit, deterministic control: calling it flags the turn so the
agent sets ``ConversationResult.continue_conversation = True`` regardless of
punctuation.
"""

from __future__ import annotations

import logging
from typing import Any, Callable

from homeassistant.core import HomeAssistant

from .registry import BaseTool

_LOGGER = logging.getLogger(__name__)

TOOL_ASK_FOLLOWUP = "nachfragen"


class AskFollowupTool(BaseTool):
    """Tool that keeps the conversation open for a follow-up answer.

    The host agent passes a ``set_continue`` callback that flags the current turn;
    the agent reads that flag when building the ConversationResult.
    """

    def __init__(self, hass: HomeAssistant, set_continue: Callable[[], None]) -> None:
        super().__init__(hass)
        self._set_continue = set_continue

    @property
    def name(self) -> str:
        return TOOL_ASK_FOLLOWUP

    @property
    def description(self) -> str:
        return (
            "Stelle dem Nutzer eine kurze Rückfrage und halte das Gespräch offen, "
            "ohne dass er das Aktivierungswort erneut sagen muss (das Mikrofon bleibt "
            "an). Nutze dies, wann immer dir Information fehlt, um eine Aktion "
            "auszuführen, statt zu raten — z.B. welches Gerät, welcher Raum, welcher "
            "Wert gemeint ist. Übergib die Rückfrage als 'frage'; formuliere danach "
            "deine Antwort an den Nutzer als genau diese Rückfrage."
        )

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "frage": {
                    "type": "string",
                    "description": "Die kurze Rückfrage, die dem Nutzer gestellt wird.",
                }
            },
            "required": ["frage"],
        }

    async def execute(self, **kwargs: Any) -> dict[str, Any]:
        frage = (kwargs.get("frage") or "").strip()
        self._set_continue()
        _LOGGER.debug("ask_followup: keeping conversation open; frage=%r", frage)
        return {
            "success": True,
            "continue_conversation": True,
            "frage": frage,
            "instruction": (
                "Das Gespräch bleibt offen (Mikrofon an). Antworte dem Nutzer jetzt "
                "mit genau dieser Rückfrage und warte auf seine Antwort."
            ),
        }
