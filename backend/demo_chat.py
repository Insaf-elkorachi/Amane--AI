import argparse
from uuid import uuid4

import requests


DEFAULT_MESSAGES = [
    "bonjour",
    "non",
    "situation dangereuse",
    (
        "Une flaque d'huile est presente pres de la ligne de production, "
        "avec risque de glissade pour les operateurs."
    ),
    "10/07/2026 a 14:30",
    "Site SONASID Nador, atelier conditionnement, zone convoyeur 2",
    "Aucun nom identifie",
    "Amine El Fassi",
    "Balisage de la zone et demande de nettoyage immediat",
    "Chute de plain-pied, blessure et arret de production",
    "oui",
]


def post_message(base_url: str, session_id: str, message: str) -> dict:
    response = requests.post(
        f"{base_url}/api/chat",
        json={
            "session_id": session_id,
            "message": message,
        },
        timeout=15,
    )
    response.raise_for_status()
    return response.json()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Lance une conversation AMANE complete de demonstration."
    )
    parser.add_argument(
        "--base-url",
        default="http://127.0.0.1:8000",
        help="URL de l'API AMANE.",
    )
    parser.add_argument(
        "--session-id",
        default=f"demo-{uuid4().hex[:8]}",
        help="Identifiant de session a utiliser.",
    )
    args = parser.parse_args()

    print(f"Session: {args.session_id}")
    print()

    for message in DEFAULT_MESSAGES:
        result = post_message(args.base_url, args.session_id, message)
        print(f"> {message}")
        print(result["response"])
        print(
            "step={step} completed={completed} emergency={emergency}".format(
                step=result["step"],
                completed=result["completed"],
                emergency=result["emergency"],
            )
        )
        if result.get("collected_data", {}).get("report_number"):
            print(f"report_number={result['collected_data']['report_number']}")
        print("-" * 72)


if __name__ == "__main__":
    main()

