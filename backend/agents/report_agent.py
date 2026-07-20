from typing import Any

from ai.llm import llm_service
from ai.rag import rag_service


class ReportAgent:
    def quick_enrich(self, collected_data: dict[str, Any], latest_message: str = "") -> dict[str, Any]:
        query = " ".join(str(value) for value in collected_data.values() if value) + " " + latest_message
        chunks = rag_service.retrieve(query)
        result = self._fallback(collected_data, chunks)
        result["rag_sources"] = [chunk["source"] for chunk in chunks]
        result["mode"] = "quick_rag_fallback"
        return result

    def enrich(self, collected_data: dict[str, Any], latest_message: str) -> dict[str, Any]:
        query = " ".join(str(value) for value in collected_data.values() if value) + " " + latest_message
        chunks = rag_service.retrieve(query)
        context = rag_service.format_context(chunks)
        fallback = self._fallback(collected_data, chunks)
        system_prompt = (
            "Tu es un agent de generation de reclamation HSE compatible SAP. "
            "A partir des donnees collectees et du contexte RAG, retourne uniquement un JSON valide avec: "
            "title, urgency, danger_type, recommended_action, missing_fields, sap_ready(boolean). "
            "urgency doit etre exactement LOW, MEDIUM, HIGH ou CRITICAL, jamais en francais."
        )
        user_prompt = (
            f"Contexte RAG:\n{context}\n\n"
            f"Donnees collectees:\n{collected_data}\n"
            f"Dernier message:\n{latest_message}"
        )
        result = llm_service.generate_json(system_prompt, user_prompt, fallback)
        result["rag_sources"] = [chunk["source"] for chunk in chunks]
        return result

    @staticmethod
    def _fallback(collected_data: dict[str, Any], chunks: list[dict[str, str | float]]) -> dict[str, Any]:
        description = str(collected_data.get("description", "")).lower()
        classification = collected_data.get("classification") or "Non classifie"
        missing_fields = [
            field for field in [
                "classification", "description", "event_datetime", "location",
                "declarant", "immediate_action", "risk_analysis"
            ]
            if not collected_data.get(field)
        ]

        consignation_words = [
            "consignation", "isolation", "isoler", "cadenas", "permis de consignation",
            "zero energie", "zéro énergie", "loto", "cadenassage", "verrouillage",
        ]

        if any(word in description for word in consignation_words):
            recommended_action = (
                "Appliquer la consignation avant intervention: identifier toutes les energies, arreter l'equipement, "
                "isoler chaque source, poser un cadenas personnel par intervenant, dissiper les energies residuelles, "
                "verifier l'absence d'energie et travailler seulement avec permis valide."
            )
            danger_type = "consignation_isolation_energies"
            urgency = "HIGH"
        elif "huile" in description or "gliss" in description:
            recommended_action = "Baliser la zone, nettoyer immediatement et identifier la source de la fuite."
            danger_type = "sol_glissant"
            urgency = "HIGH"
        elif "cable" in description or "elect" in description:
            recommended_action = "Interdire l'acces, couper l'alimentation si possible et prevenir la maintenance electrique."
            danger_type = "risque_electrique"
            urgency = "CRITICAL"
        else:
            recommended_action = "Securiser la zone, informer le responsable HSE et traiter l'anomalie."
            danger_type = str(classification)
            urgency = "MEDIUM"

        return {
            "title": f"Signalement HSE - {classification}",
            "urgency": urgency,
            "danger_type": danger_type,
            "recommended_action": recommended_action,
            "missing_fields": missing_fields,
            "sap_ready": not missing_fields,
            "rag_sources": [chunk["source"] for chunk in chunks],
        }


report_agent = ReportAgent()
