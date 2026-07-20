from typing import Any

from ai.llm import llm_service
from ai.rag import rag_service


class EmergencyAgent:
    def assess(self, message: str) -> dict[str, Any]:
        chunks = rag_service.retrieve(message)
        context = rag_service.format_context(chunks)
        fallback = self._fallback(message, chunks)
        system_prompt = (
            "Tu es un agent HSE pour detecter l'urgence industrielle. "
            "Utilise le contexte RAG. Retourne uniquement un JSON valide avec: "
            "immediate_danger(boolean), urgency(LOW/MEDIUM/HIGH/CRITICAL), reasons(list), safety_instruction(str)."
        )
        user_prompt = f"Contexte RAG:\n{context}\n\nMessage utilisateur:\n{message}"
        result = llm_service.generate_json(system_prompt, user_prompt, fallback)
        result["rag_sources"] = [chunk["source"] for chunk in chunks]
        return result

    @staticmethod
    def _fallback(message: str, chunks: list[dict[str, str | float]]) -> dict[str, Any]:
        normalized = message.lower()
        critical_words = [
            "incendie", "explosion", "electrocution", "électrocution", "gaz", "chimique",
            "blessure", "sang", "feu", "حريق", "انفجار", "كهرباء"
        ]
        high_words = ["fuite", "huile", "glissade", "chute", "machine", "cable", "كابل", "زيت", "خطر"]

        consignation_words = [
            "consignation", "isolation", "isoler", "cadenas", "permis de consignation",
            "zero energie", "zéro énergie", "loto", "cadenassage", "verrouillage",
        ]

        if any(word in normalized for word in critical_words):
            urgency = "CRITICAL"
            immediate = True
        elif any(word in normalized for word in high_words):
            urgency = "HIGH"
            immediate = True
        elif any(word in normalized for word in consignation_words):
            urgency = "HIGH"
            immediate = True
        else:
            urgency = "MEDIUM"
            immediate = False

        if any(word in normalized for word in consignation_words):
            safety_instruction = (
                "Avant toute intervention, arretez et isolez toutes les energies, validez le permis de consignation, "
                "posez un cadenas personnel par intervenant, dissipez les energies residuelles et verifiez l'absence d'energie. "
                "Un arret d'urgence ou un asservissement ne remplace jamais une consignation."
            )
        else:
            safety_instruction = (
                "Securisez la zone, eloignez les personnes exposees et prevenez le responsable HSE."
                if immediate else
                "Continuez la declaration et precisez la localisation et le risque potentiel."
            )

        return {
            "immediate_danger": immediate,
            "urgency": urgency,
            "reasons": ["Evaluation locale basee sur mots-cles HSE."],
            "safety_instruction": safety_instruction,
            "rag_sources": [chunk["source"] for chunk in chunks],
        }


emergency_agent = EmergencyAgent()
