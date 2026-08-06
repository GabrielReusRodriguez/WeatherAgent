"""weather_agent — GAIA agent for text weather forecasts.

Installs the ``weather_agent`` agent into the GAIA registry via the ``gaia.agent``
entry-point group (see ``pyproject.toml``).
"""

__all__ = ["build_registration"]

__version__ = "0.1.0"


def __getattr__(name):
    if name == "WeatherAgent":
        from weather_agent.agent import WeatherAgent

        return WeatherAgent
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def build_registration():
    """Return the :class:`AgentRegistration` for the weather_agent agent."""
    from gaia.agents.registry import AgentRegistration, class_factory

    def factory(**kwargs):
        from weather_agent.agent import WeatherAgent

        return class_factory(WeatherAgent)(**kwargs)

    return AgentRegistration(
        id="weather_agent",
        name="weather_agent",
        description="Generates text weather forecast reports for a place and time",
        source="installed",
        conversation_starters=[
            "What is the weather tomorrow in Valencia?",
            "Weather in Berlin this weekend in English",
            "¿Qué tiempo hace ahora en Madrid?",
        ],
        factory=factory,
        agent_dir=None,
        models=["Gemma-4-E4B-it-GGUF"],
        namespaced_agent_id="installed:weather_agent",
        category="general",
        tags=["weather", "meteo", "forecast"],
        icon="sparkles",
        tools_count=6,
    )
