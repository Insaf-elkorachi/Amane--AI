import base64
import json
import re
from pathlib import Path
from typing import Any

from ai.llm import llm_service
from ai.rag import rag_service


class VisionRiskAgent:
    """Analyze HSE risk photos and classify unsafe acts/conditions."""

    @staticmethod
    def _normalize_language(language: str | None) -> str:
        value = str(language or "ar").lower().strip()
        if value in {"fr", "french", "fr-fr"}:
            return "fr"
        if value in {"en", "english", "en-us", "en-gb"}:
            return "en"
        return "ar"

    @staticmethod
    def _language_instruction(language: str) -> str:
        if language == "fr":
            return "IMPORTANT LANGUE: tous les textes rediges pour l'utilisateur doivent etre en francais professionnel clair. N'utilise pas l'arabe ni l'anglais sauf pour les noms officiels comme SONASID, AMANE, HSE et SAP. "
        if language == "en":
            return "IMPORTANT LANGUAGE: all user-facing text must be in clear professional English. Do not use Arabic or French except official names such as SONASID, AMANE, HSE and SAP. "
        return "IMPORTANT LANGUE: tous les textes rediges pour l'utilisateur doivent etre en arabe classique clair et professionnel. N'utilise pas la darija, n'utilise pas l'anglais, et n'utilise pas le francais dans les champs textuels sauf pour les noms officiels comme SONASID, AMANE, HSE, SAP et les valeurs metier imposees. "

    def classify(self, image_path: Path, content_type: str | None = None, analysis_language: str = "ar") -> dict[str, Any]:
        language = self._normalize_language(analysis_language)
        fallback = self._fallback(image_path)
        if not llm_service.available:
            return fallback

        mime = content_type or "image/jpeg"
        image_bytes = image_path.read_bytes()
        encoded = base64.b64encode(image_bytes).decode("ascii")
        context = rag_service.format_context(
            rag_service.retrieve(
                "analyse photo HSE chantier excavation engins charge suspendue EPI balisage circulation pietons consignation SONASID Nador",
                top_k=8,
            )
        )
        system_prompt = (
            "Tu es AMANE AI, agent vision HSE expert pour SONASID Nador. "
            "Analyse la photo comme un preventeur HSE terrain, avec prudence mais de maniere intelligente. "
            + self._language_instruction(language)
            + "Tu dois identifier tous les risques visibles ou fortement probables, les consequences possibles, "
            "les mesures de prevention, les regles SST SONASID pertinentes et le niveau de risque global. "
            "Tu ne dois jamais affirmer une absence ou une non-conformite qui n'est pas directement visible. Distingue explicitement: visible, probable, non confirmable. Pour les EPI, si casque/gilet sont visibles mais gants/lunettes/chaussures ne sont pas confirmables, ecris que les EPI sont partiellement visibles et que certains EPI ne sont pas confirmables sur la photo. Ne dis pas absence d'EPI sauf si l'absence est clairement visible. Pour une tranchee ou excavation, ne conclus pas a une absence d'etayage/blindage si l'interieur n'est pas visible; ecris que le blindage ou l'etayage n'est pas confirmable sur la photo. Qualifie correctement le risque: chute dans une excavation n'est pas une simple chute de plain-pied. Si un point est incertain, marque-le comme a confirmer. "
            "Retourne uniquement un JSON valide avec exactement ces cles: "
            "classification, confidence, scene_summary, risk_items, main_risks, prevention_measures, "
            "global_risk_level, global_risk_reason, immediate_danger, recommended_action, questions, "
            "location_hints, related_sst_rules. "
            "classification doit etre exactement 'Acte dangereux', 'Situation dangereuse', 'Acte dangereux et situation dangereuse' ou 'A confirmer'. "
            "risk_items doit etre une liste d'objets avec: risk, description, possible_consequences, severity. "
            "severity doit etre LOW, MEDIUM, HIGH ou CRITICAL. "
            "main_risks, prevention_measures, questions, location_hints et related_sst_rules doivent etre des listes de textes dans la langue demandee. "
            "global_risk_level doit etre LOW, MEDIUM, HIGH ou CRITICAL. "
            "Si des personnes sont visibles en comportement dangereux, inclure acte dangereux. "
            "Si l'environnement, l'equipement, la zone, la fouille, le balisage, le rangement ou la machine cree le danger, inclure situation dangereuse."
        )
        user_text = (
            "Contexte RAG SONASID et regles SST disponibles:\n"
            f"{context}\n\n"
            "Analyse cette photo HSE comme dans un rapport professionnel. "
            "Le contenu lisible par l'utilisateur doit respecter la langue demandee: observations, risques, consequences, mesures, justification et question de confirmation. "
            "Reste prudent: formule les elements incertains comme des hypotheses a confirmer sur le terrain."
        )

        try:
            response = llm_service.client.chat.completions.create(
                model=llm_service.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": user_text},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{mime};base64,{encoded}",
                                    "detail": "high",
                                },
                            },
                        ],
                    },
                ],
                temperature=0.1,
                response_format={"type": "json_object"},
            )
            content = response.choices[0].message.content or "{}"
            result = {**fallback, **json.loads(content)}
            result["source_image"] = str(image_path)
            return self._normalize_result(result)
        except Exception as exc:
            return {**fallback, "vision_error": str(exc)}

    @staticmethod
    def _fallback(image_path: Path) -> dict[str, Any]:
        return {
            "classification": "A confirmer",
            "confidence": 0.0,
            "scene_summary": "\u062a\u0645 \u0627\u0633\u062a\u0644\u0627\u0645 \u0635\u0648\u0631\u0629 HSE\u060c \u0644\u0643\u0646 \u0627\u0644\u062a\u062d\u0644\u064a\u0644 \u0627\u0644\u0628\u0635\u0631\u064a \u0627\u0644\u0622\u0644\u064a \u063a\u064a\u0631 \u0645\u062a\u0627\u062d \u062d\u0627\u0644\u064a\u0627. \u064a\u062c\u0628 \u062a\u0623\u0643\u064a\u062f \u0627\u0644\u0648\u0636\u0639 \u0645\u064a\u062f\u0627\u0646\u064a\u0627 \u0645\u0646 \u0637\u0631\u0641 \u0627\u0644\u0645\u0635\u0631\u062d \u0623\u0648 \u0645\u0633\u0624\u0648\u0644 HSE.",
            "risk_items": [
                {
                    "risk": "\u062e\u0637\u0631 \u064a\u062d\u062a\u0627\u062c \u0625\u0644\u0649 \u062a\u0623\u0643\u064a\u062f",
                    "description": "\u0644\u0627 \u064a\u0645\u0643\u0646 \u062a\u0623\u0643\u064a\u062f \u0637\u0628\u064a\u0639\u0629 \u0627\u0644\u062e\u0637\u0631 \u0645\u0646 \u0627\u0644\u0635\u0648\u0631\u0629 \u0622\u0644\u064a\u0627 \u0641\u064a \u0647\u0630\u0647 \u0627\u0644\u0644\u062d\u0638\u0629. \u064a\u062c\u0628 \u0645\u0631\u0627\u062c\u0639\u0629 \u0627\u0644\u0635\u0648\u0631\u0629 \u0645\u064a\u062f\u0627\u0646\u064a\u0627 \u0642\u0628\u0644 \u0627\u062a\u062e\u0627\u0630 \u0642\u0631\u0627\u0631 \u0646\u0647\u0627\u0626\u064a.",
                    "possible_consequences": "\u0642\u062f \u064a\u0642\u0639 \u062d\u0627\u062f\u062b \u0625\u0630\u0627 \u0643\u0627\u0646 \u0627\u0644\u062e\u0637\u0631 \u0645\u0648\u062c\u0648\u062f\u0627 \u0648\u0644\u0645 \u064a\u062a\u0645 \u0639\u0632\u0644\u0647 \u0623\u0648 \u0645\u0639\u0627\u0644\u062c\u062a\u0647 \u0628\u0633\u0631\u0639\u0629.",
                    "severity": "MEDIUM",
                }
            ],
            "main_risks": ["\u062e\u0637\u0631 HSE \u064a\u062d\u062a\u0627\u062c \u0625\u0644\u0649 \u062a\u0623\u0643\u064a\u062f \u0645\u064a\u062f\u0627\u0646\u064a"],
            "prevention_measures": [
                "\u0627\u0644\u062a\u062d\u0642\u0642 \u0645\u0646 \u0627\u0644\u0635\u0648\u0631\u0629 \u0645\u0639 \u0627\u0644\u0645\u0635\u0631\u062d \u0623\u0648 \u0645\u0633\u0624\u0648\u0644 HSE.",
                "\u062a\u0623\u0643\u064a\u062f \u0645\u0627 \u0625\u0630\u0627 \u0643\u0627\u0646 \u0627\u0644\u0623\u0645\u0631 \u064a\u062a\u0639\u0644\u0642 \u0628\u0641\u0639\u0644 \u062e\u0637\u064a\u0631 \u0623\u0648 \u0628\u0648\u0636\u0639\u064a\u0629 \u062e\u0637\u064a\u0631\u0629.",
                "\u062a\u0623\u0645\u064a\u0646 \u0627\u0644\u0645\u0646\u0637\u0642\u0629 \u0648\u0648\u0636\u0639 \u0627\u0644\u062d\u0648\u0627\u062c\u0632 \u0623\u0648 \u0627\u0644\u062a\u0634\u0648\u064a\u0631 \u0625\u0630\u0627 \u0643\u0627\u0646 \u0647\u0646\u0627\u0643 \u062e\u0637\u0631 \u0642\u0627\u0626\u0645.",
            ],
            "global_risk_level": "MEDIUM",
            "global_risk_reason": "\u0627\u0644\u062a\u062d\u0644\u064a\u0644 \u0627\u0644\u0628\u0635\u0631\u064a \u0627\u0644\u0622\u0644\u064a \u063a\u064a\u0631 \u0645\u062a\u0627\u062d\u061b \u0644\u0630\u0644\u0643 \u064a\u062c\u0628 \u062a\u0623\u0643\u064a\u062f \u0645\u0633\u062a\u0648\u0649 \u0627\u0644\u062e\u0637\u0631 \u0641\u064a \u0627\u0644\u0645\u064a\u062f\u0627\u0646.",
            "immediate_danger": False,
            "recommended_action": "\u062a\u0623\u0643\u064a\u062f \u0627\u0644\u062a\u062d\u0644\u064a\u0644 \u0645\u0639 \u0627\u0644\u0645\u0635\u0631\u062d\u060c \u062b\u0645 \u062a\u0637\u0628\u064a\u0642 \u0625\u062c\u0631\u0627\u0621\u0627\u062a \u0627\u0644\u0648\u0642\u0627\u064a\u0629 \u0627\u0644\u0645\u0646\u0627\u0633\u0628\u0629 \u062d\u0633\u0628 \u0642\u0648\u0627\u0639\u062f HSE.",
            "questions": [
                "\u0647\u0644 \u062a\u0624\u0643\u062f \u0623\u0646 \u0627\u0644\u0635\u0648\u0631\u0629 \u062a\u0645\u062b\u0644 \u0641\u0639\u0644\u0627 \u062e\u0637\u064a\u0631\u0627 \u0623\u0645 \u0648\u0636\u0639\u064a\u0629 \u062e\u0637\u064a\u0631\u0629\u061f",
                "\u0645\u0627 \u0647\u064a \u0645\u0646\u0637\u0642\u0629 SONASID Nador \u0627\u0644\u0645\u0639\u0646\u064a\u0629\u061f",
                "\u0647\u0644 \u062a\u0648\u062c\u062f \u0623\u0634\u062e\u0627\u0635 \u0645\u0639\u0631\u0636\u0648\u0646 \u0644\u0644\u062e\u0637\u0631 \u0628\u0634\u0643\u0644 \u0641\u0648\u0631\u064a\u061f",
            ],
            "location_hints": [],
            "related_sst_rules": [],
            "source_image": str(image_path),
        }

    @staticmethod
    def _as_list(value: Any) -> list[Any]:
        if value is None:
            return []
        if isinstance(value, list):
            return value
        return [value]


    @staticmethod
    def _soften_visual_overclaims(text: str) -> str:
        softened = text
        patterns = [
            (r"\b(absence|manque|pas|sans)\s+d['?]?\s*epi\b", "EPI partiellement visibles; certains EPI ne sont pas confirmables sur la photo"),
            (r"\b(absence|manque|pas|sans)\s+des\s+epi\b", "EPI partiellement visibles; certains EPI ne sont pas confirmables sur la photo"),
            (r"\btranch[e?]e\s+d[e?]pourvue\s+d['?]?\s*[e?]tayage\b", "etayage/blindage non confirmable sur la photo"),
            (r"\babsence\s+d['?]?\s*[e?]tayage\b", "etayage/blindage non confirmable sur la photo"),
            (r"\babsence\s+de\s+blindage\b", "blindage non confirmable sur la photo"),
        ]
        for pattern, replacement in patterns:
            softened = re.sub(pattern, replacement, softened, flags=re.IGNORECASE)

        lowered = softened.lower()
        if "excavation" in lowered or "tranchee" in lowered or "tranch?e" in lowered:
            softened = re.sub(r"chute\s+de\s+plain[- ]pied", "chute dans une excavation", softened, flags=re.IGNORECASE)
        softened = softened.replace("chute dans une excavation dans une excavation", "chute dans une excavation")
        softened = softened.replace("Chute dans une excavation dans une excavation", "Chute dans une excavation")
        return softened


    @classmethod
    def _normalize_result(cls, result: dict[str, Any]) -> dict[str, Any]:
        classification = str(result.get("classification") or "A confirmer").strip()
        lowered = classification.lower()
        if lowered in {"acte", "unsafe act", "acte dangereux"}:
            classification = "Acte dangereux"
        elif lowered in {"situation", "unsafe condition", "condition dangereuse", "situation dangereuse"}:
            classification = "Situation dangereuse"
        elif lowered in {
            "acte dangereux et situation dangereuse",
            "acte et situation dangereuse",
            "unsafe act and unsafe condition",
            "both",
        }:
            classification = "Acte dangereux et situation dangereuse"
        elif classification not in {
            "Acte dangereux",
            "Situation dangereuse",
            "Acte dangereux et situation dangereuse",
            "A confirmer",
        }:
            classification = "A confirmer"

        result["classification"] = classification
        result["immediate_danger"] = bool(result.get("immediate_danger"))
        result["risk_items"] = cls._normalize_risk_items(result.get("risk_items"))
        for key in ["main_risks", "prevention_measures", "questions", "location_hints", "related_sst_rules"]:
            result[key] = [cls._soften_visual_overclaims(str(item)) for item in cls._as_list(result.get(key)) if str(item).strip()]
        level = str(result.get("global_risk_level") or "MEDIUM").upper()
        result["global_risk_level"] = level if level in {"LOW", "MEDIUM", "HIGH", "CRITICAL"} else "MEDIUM"
        result["scene_summary"] = cls._soften_visual_overclaims(str(result.get("scene_summary") or result.get("description") or "Analyse photo HSE."))
        result["description"] = result["scene_summary"]
        result["recommended_action"] = cls._soften_visual_overclaims(str(result.get("recommended_action") or "Securiser la zone et confirmer l'analyse avec le responsable HSE."))
        result["global_risk_reason"] = cls._soften_visual_overclaims(str(result.get("global_risk_reason") or "Niveau etabli selon les risques visibles sur la photo."))
        return result

    @classmethod
    def _normalize_risk_items(cls, value: Any) -> list[dict[str, str]]:
        items = cls._as_list(value)
        normalized: list[dict[str, str]] = []
        for item in items:
            if isinstance(item, dict):
                severity = str(item.get("severity") or "MEDIUM").upper()
                normalized.append(
                    {
                        "risk": cls._soften_visual_overclaims(str(item.get("risk") or "Risque observe")),
                        "description": cls._soften_visual_overclaims(str(item.get("description") or "A confirmer sur terrain.")),
                        "possible_consequences": cls._soften_visual_overclaims(str(item.get("possible_consequences") or item.get("consequences") or "Accident potentiel.")),
                        "severity": severity if severity in {"LOW", "MEDIUM", "HIGH", "CRITICAL"} else "MEDIUM",
                    }
                )
            elif str(item).strip():
                normalized.append(
                    {
                        "risk": str(item),
                        "description": "A confirmer sur terrain.",
                        "possible_consequences": "Accident potentiel.",
                        "severity": "MEDIUM",
                    }
                )
        return normalized

    @staticmethod
    def _level_label(level: Any) -> str:
        labels = {
            "LOW": "\u0645\u0646\u062e\u0641\u0636",
            "MEDIUM": "\u0645\u062a\u0648\u0633\u0637",
            "HIGH": "\u0645\u0631\u062a\u0641\u0639",
            "CRITICAL": "\u062d\u0631\u062c",
        }
        return labels.get(str(level or "MEDIUM").upper(), "\u0645\u062a\u0648\u0633\u0637")

    @staticmethod
    def _classification_label_ar(value: Any) -> str:
        labels = {
            "Acte dangereux": "\u0641\u0639\u0644 \u062e\u0637\u064a\u0631",
            "Situation dangereuse": "\u0648\u0636\u0639\u064a\u0629 \u062e\u0637\u064a\u0631\u0629",
            "Acte dangereux et situation dangereuse": "\u0641\u0639\u0644 \u062e\u0637\u064a\u0631 \u0648\u0648\u0636\u0639\u064a\u0629 \u062e\u0637\u064a\u0631\u0629",
            "A confirmer": "\u064a\u062d\u062a\u0627\u062c \u0625\u0644\u0649 \u062a\u0623\u0643\u064a\u062f",
        }
        return labels.get(str(value or "A confirmer"), "\u064a\u062d\u062a\u0627\u062c \u0625\u0644\u0649 \u062a\u0623\u0643\u064a\u062f")

    @staticmethod
    def _has_arabic(text: Any) -> bool:
        return any("\u0600" <= char <= "\u06ff" for char in str(text or ""))

    @classmethod
    def _arabic_or_note(cls, text: Any) -> str:
        value = str(text or "").strip()
        if cls._has_arabic(value):
            return value
        return "\u0647\u0630\u0627 \u0627\u0644\u0639\u0646\u0635\u0631 \u064a\u062d\u062a\u0627\u062c \u0625\u0644\u0649 \u062a\u0623\u0643\u064a\u062f \u0645\u064a\u062f\u0627\u0646\u064a \u0627\u0639\u062a\u0645\u0627\u062f\u0627 \u0639\u0644\u0649 \u0627\u0644\u0635\u0648\u0631\u0629."

    @staticmethod
    def _level_label_latin(level: Any, language: str = "fr") -> str:
        value = str(level or "MEDIUM").upper()
        if language == "en":
            labels = {"LOW": "Low", "MEDIUM": "Medium", "HIGH": "High", "CRITICAL": "Critical"}
        else:
            labels = {"LOW": "Faible", "MEDIUM": "Moyen", "HIGH": "Eleve", "CRITICAL": "Critique"}
        return labels.get(value, labels["MEDIUM"])

    @staticmethod
    def _format_detailed_response_latin(result: dict[str, Any], language: str = "fr") -> str:
        is_en = language == "en"
        labels = {
            "title": "AMANE HSE Photo Analysis" if is_en else "Analyse photo HSE AMANE",
            "classification": "Proposed classification" if is_en else "Classification proposee",
            "level": "Overall risk level" if is_en else "Niveau de risque global",
            "summary": "Scene summary" if is_en else "Resume",
            "observed": "Observed risks" if is_en else "Risques observes",
            "main": "Main risks" if is_en else "Principaux risques",
            "prevention": "Recommended prevention measures" if is_en else "Mesures de prevention recommandees",
            "reason": "Overall risk justification" if is_en else "Justification du niveau global",
            "rules": "Related SONASID SST rules" if is_en else "Regles SST SONASID liees",
            "question": "AMANE question" if is_en else "Question AMANE",
            "consequences": "Possible consequences" if is_en else "Consequences possibles",
            "risk_level": "Level" if is_en else "Niveau",
            "no_precise": "No precise risk was detected automatically; field confirmation is required." if is_en else "Aucun risque precis detecte automatiquement; confirmation terrain necessaire.",
            "default_risk": "HSE risk to confirm" if is_en else "Risque HSE a confirmer",
            "default_action": "Secure the area and confirm the analysis with the HSE supervisor." if is_en else "Securiser la zone et confirmer l'analyse avec le responsable HSE.",
            "default_question": "Do you confirm whether this is an unsafe act or an unsafe condition?" if is_en else "Confirmez-vous s'il s'agit d'un acte dangereux ou d'une situation dangereuse ?",
        }
        risk_lines = []
        for item in result.get("risk_items", [])[:12]:
            risk_lines.append(
                "- "
                f"{item.get('risk', 'Risque')}: {item.get('description', '')} "
                f"{labels['consequences']}: {item.get('possible_consequences', '')} "
                f"{labels['risk_level']}: {VisionRiskAgent._level_label_latin(item.get('severity', 'MEDIUM'), language)}."
            )
        if not risk_lines:
            risk_lines.append("- " + labels["no_precise"])

        main_risks = result.get("main_risks", []) or [labels["default_risk"]]
        prevention = result.get("prevention_measures", []) or [result.get("recommended_action", labels["default_action"])]
        rules = result.get("related_sst_rules", [])
        questions = result.get("questions", []) or [labels["default_question"]]

        sections = [
            labels["title"],
            "",
            f"{labels['classification']}: {result.get('classification', 'A confirmer')}",
            f"{labels['level']}: {VisionRiskAgent._level_label_latin(result.get('global_risk_level', 'MEDIUM'), language)}",
            f"{labels['summary']}: {result.get('scene_summary', '')}",
            "",
            labels["observed"] + ":",
            *risk_lines,
            "",
            labels["main"] + ":",
            *(f"- {risk}" for risk in main_risks[:10]),
            "",
            labels["prevention"] + ":",
            *(f"- {measure}" for measure in prevention[:12]),
            "",
            f"{labels['reason']}: {result.get('global_risk_reason', '')}",
        ]
        if rules:
            sections.extend(["", labels["rules"] + ":", *(f"- {rule}" for rule in rules[:8])])
        sections.extend(["", f"{labels['question']}: {questions[0]}"])
        return "\n".join(sections)

    @staticmethod
    def format_detailed_response(result: dict[str, Any], language: str = "ar") -> str:
        language = VisionRiskAgent._normalize_language(language)
        if language in {"fr", "en"}:
            return VisionRiskAgent._format_detailed_response_latin(result, language)

        risk_lines = []
        for item in result.get("risk_items", [])[:12]:
            risk_lines.append(
                "- "
                f"{VisionRiskAgent._arabic_or_note(item.get('risk', "\u062e\u0637\u0631"))}: {VisionRiskAgent._arabic_or_note(item.get('description', ''))} "
                f"\u0627\u0644\u0639\u0648\u0627\u0642\u0628 \u0627\u0644\u0645\u062d\u062a\u0645\u0644\u0629: {VisionRiskAgent._arabic_or_note(item.get('possible_consequences', ''))} "
                f"\u0627\u0644\u0645\u0633\u062a\u0648\u0649: {VisionRiskAgent._level_label(item.get('severity', 'MEDIUM'))}."
            )
        if not risk_lines:
            risk_lines.append("- " + "\u0644\u0645 \u064a\u062a\u0645 \u062a\u062d\u062f\u064a\u062f \u062e\u0637\u0631 \u062f\u0642\u064a\u0642 \u062a\u0644\u0642\u0627\u0626\u064a\u0627\u061b \u064a\u0644\u0632\u0645 \u062a\u0623\u0643\u064a\u062f \u0645\u064a\u062f\u0627\u0646\u064a.")

        main_risks = result.get("main_risks", []) or ["\u062e\u0637\u0631 HSE \u064a\u062d\u062a\u0627\u062c \u0625\u0644\u0649 \u062a\u0623\u0643\u064a\u062f \u0645\u064a\u062f\u0627\u0646\u064a"]
        prevention = result.get("prevention_measures", []) or [result.get("recommended_action", "\u064a\u062c\u0628 \u062a\u0623\u0645\u064a\u0646 \u0627\u0644\u0645\u0646\u0637\u0642\u0629.")]
        rules = result.get("related_sst_rules", [])
        questions = result.get("questions", []) or ["\u0647\u0644 \u062a\u0624\u0643\u062f \u0647\u0630\u0627 \u0627\u0644\u062a\u062d\u0644\u064a\u0644\u061f"]

        sections = [
            "\u062a\u062d\u0644\u064a\u0644 \u0635\u0648\u0631\u0629 HSE \u0628\u0648\u0627\u0633\u0637\u0629 AMANE",
            "",
            f"\u0627\u0644\u062a\u0635\u0646\u064a\u0641 \u0627\u0644\u0645\u0642\u062a\u0631\u062d: {VisionRiskAgent._classification_label_ar(result.get('classification', 'A confirmer'))}",
            f"\u0645\u0633\u062a\u0648\u0649 \u0627\u0644\u062e\u0637\u0631 \u0627\u0644\u0639\u0627\u0645: {VisionRiskAgent._level_label(result.get('global_risk_level', 'MEDIUM'))}",
            f"\u0645\u0644\u062e\u0635 \u0627\u0644\u0645\u0634\u0647\u062f: {VisionRiskAgent._arabic_or_note(result.get('scene_summary', ''))}",
            "",
            "\u0627\u0644\u0645\u062e\u0627\u0637\u0631 \u0627\u0644\u0645\u0631\u0635\u0648\u062f\u0629" + ":",
            *risk_lines,
            "",
            "\u0627\u0644\u0645\u062e\u0627\u0637\u0631 \u0627\u0644\u0631\u0626\u064a\u0633\u064a\u0629" + ":",
            *(f"- {VisionRiskAgent._arabic_or_note(risk)}" for risk in main_risks[:10]),
            "",
            "\u0625\u062c\u0631\u0627\u0621\u0627\u062a \u0627\u0644\u0648\u0642\u0627\u064a\u0629 \u0627\u0644\u0645\u0648\u0635\u0649 \u0628\u0647\u0627" + ":",
            *(f"- {VisionRiskAgent._arabic_or_note(measure)}" for measure in prevention[:12]),
            "",
            f"\u062a\u0628\u0631\u064a\u0631 \u0645\u0633\u062a\u0648\u0649 \u0627\u0644\u062e\u0637\u0631 \u0627\u0644\u0639\u0627\u0645: {VisionRiskAgent._arabic_or_note(result.get('global_risk_reason', ''))}",
        ]
        if rules:
            sections.extend(["", "\u0642\u0648\u0627\u0639\u062f SST \u0627\u0644\u062e\u0627\u0635\u0629 \u0628\u0640 SONASID \u0627\u0644\u0645\u0631\u062a\u0628\u0637\u0629" + ":", *(f"- {VisionRiskAgent._arabic_or_note(rule)}" for rule in rules[:8])])
        question = questions[0] if VisionRiskAgent._has_arabic(questions[0]) else "\u0647\u0644 \u062a\u0624\u0643\u062f \u0623\u0646 \u0627\u0644\u0635\u0648\u0631\u0629 \u062a\u0645\u062b\u0644 \u0641\u0639\u0644\u0627 \u062e\u0637\u064a\u0631\u0627 \u0623\u0645 \u0648\u0636\u0639\u064a\u0629 \u062e\u0637\u064a\u0631\u0629\u061f"
        sections.extend(["", f"\u0633\u0624\u0627\u0644 AMANE: {question}"])
        return "\n".join(sections)

    @staticmethod
    def to_conversation_message(result: dict[str, Any]) -> str:
        risks = ", ".join(item.get("risk", "") for item in result.get("risk_items", []) if item.get("risk")) or "risque a confirmer"
        prevention = ", ".join(str(item) for item in result.get("prevention_measures", [])[:4]) or result.get("recommended_action", "")
        location_hints = ", ".join(str(item) for item in result.get("location_hints", []) if item) or "localisation a confirmer"
        return (
            "Analyse photo HSE. "
            f"Classification proposee: {result.get('classification', 'A confirmer')}. "
            f"Niveau global: {result.get('global_risk_level', 'MEDIUM')}. "
            f"Description: {result.get('scene_summary', '')}. "
            f"Risques observes: {risks}. "
            f"Localisation probable: {location_hints}. "
            f"Mesures recommandees: {prevention}. "
            "AMANE doit demander confirmation avant enregistrement."
        )


vision_risk_agent = VisionRiskAgent()