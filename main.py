#!/usr/bin/env python3
"""Interactive CLI for weather_agent."""

from weather_agent.agent import WeatherAgent

EXIT_COMMANDS = {"salir", "exit", "quit"}


def main() -> None:
    agent = WeatherAgent()
    print("weather_agent listo. Escribe tu consulta (salir / exit / quit para terminar).")

    while True:
        try:
            query = input("\n¿Qué tiempo quieres consultar? ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n¡Adiós!")
            break

        if not query:
            continue
        if query.lower() in EXIT_COMMANDS:
            print("¡Adiós!")
            break

        agent.process_query(query)


if __name__ == "__main__":
    main()
