import base64
import json
import re
import unicodedata
from pathlib import Path
from typing import Any

from ai.llm import llm_service
from ai.rag import rag_service
from core.config import settings


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
        return "IMPORTANT LANGUE: tous les textes rediges pour l'utilisateur doivent etre en arabe classique clair et professionnel. N'utilise pas la darija, n'utilise pas l'anglais, et n'utilise pas le francais dans les champs textuels sauf pour les noms officiels comme SONASID, AMANE, HSE, SAP et les valeurs metier imposees. Les champs scene_summary, risk_items.risk, risk_items.observation, risk_items.cause, risk_items.description, risk_items.possible_consequences, risk_items.prevention_measure, risk_items.sst_rule, main_risks, prevention_measures, global_risk_reason, recommended_action, questions, location_hints et related_sst_rules doivent etre en arabe classique."

    def classify(self, image_path: Path, content_type: str | None = None, analysis_language: str = "ar") -> dict[str, Any]:
        language = self._normalize_language(analysis_language)
        fallback = self._fallback(image_path)
        if not llm_service.available:
            return self._normalize_result(fallback)

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
            "Tu es AMANE, un assistant HSE industriel specialise dans l analyse de photographies provenant d une usine siderurgique SONASID. "
            "Ton role est celui d un inspecteur HSE experimente. "
            + self._language_instruction(language)
            + "Analyse UNIQUEMENT les elements visibles sur la photographie. Ne jamais inventer un risque. Applique toujours la logique inspection HSE en cinq etapes: Observer les faits visibles, Deduire les risques uniquement depuis ces faits, Qualifier le niveau de gravite, Prevenir avec des mesures operationnelles, Verifier avec une question ciblee. "
            "Ne jamais supposer qu un EPI est absent. Ne jamais supposer qu un harnais, un blindage, une consignation ou un dispositif de securite est absent s il n est pas clairement visible. "
            "Lorsque l image ne permet pas de conclure, ecris clairement: Non confirmable sur cette photographie, ou Aucun element visible ne permet de confirmer. Ajoute une liste observations contenant uniquement des constats factuels visibles, sans interpretation de risque. Chaque risque dans risk_items doit pouvoir etre relie a au moins une observation visible. "
            "Toujours privilegier les faits observables. Ne transforme jamais une hypothese en fait. Distinction critique: la presence visible d une machine protegee, d une voie de circulation, d un equipement, d un stockage ou d une zone de travail ne constitue pas un risque observe si aucun danger direct n est visible. La liste risk_items/Risques observes est reservee uniquement aux dangers directement perceptibles sur la photo. Les risques theoriques, potentiels ou non confirmables doivent etre mentionnes prudemment dans scene_summary, global_risk_reason ou questions, mais pas comme risques observes. "
            "Analyse systematiquement ces categories meme si certains elements sont non confirmables: "
            "1 EPI: casque, lunettes, gants, chaussures, harnais, gilet, protection auditive, protection respiratoire. "
            "2 Travail en hauteur: garde-corps, harnais, ligne de vie, ouverture, echelle, echafaudage. "
            "3 Levage: charge suspendue, elingage, pont roulant, rayon de deplacement, personne sous charge. "
            "4 Circulation: engins, pietons, separation, angle mort, vitesse, voies de circulation. "
            "5 Machines: protecteurs, organes en mouvement, consignation visible, acces dangereux. "
            "6 Electricite: cable, coffret, armoire, fil apparent. "
            "7 Incendie: flamme, etincelles, produits inflammables, extincteur visible. "
            "8 Manutention: posture, charge lourde, stockage, stabilite. "
            "9 Sol et environnement: obstacle, huile, eau, poussiere, encombrement, 5S. "
            "10 Produits: fuite, emballage, element saillant, stockage. "
            "Pour chaque risque detecte, fournir un risk_item avec nom du risque, observation factuelle visible, cause, consequences possibles, gravite LOW/MEDIUM/HIGH/CRITICAL, mesure de prevention et regle SST SONASID concernee. Avant d ajouter un risk_item, verifier qu il existe un indice visuel concret de danger: obstacle, proximite dangereuse, charge suspendue, personne exposee, fuite, cable apparent, organe en mouvement accessible, chute possible visible, encombrement, posture dangereuse, ou autre danger directement visible. Ne pas creer de risk_item pour un risque purement theorique. "
            "classification doit etre exactement Acte dangereux, Situation dangereuse, ou Acte dangereux et situation dangereuse. Utilise Acte dangereux et situation dangereuse lorsque la photo montre les deux. "
            "Determiner le niveau global selon cette regle: CRITICAL si presence visible d un risque pouvant provoquer immediatement un accident mortel: charge suspendue, travail en hauteur non protege, metal en fusion, pont roulant, intervention electrique, espace confine, machine dangereuse, incendie important. HIGH si plusieurs risques importants combines. MEDIUM si risques maitrisables. LOW si aucun risque significatif visible. Toujours justifier le niveau. "
            "Ne jamais ecrire absence de casque, absence de harnais, absence de lunettes, absence de gants, absence de chaussures, absence de blindage, absence d extincteur ou absence de consignation si ce n est pas clairement visible. Preferer: Le port du casque ne peut pas etre confirme, ou Non confirmable sur cette photographie. "
            "Indice de confiance: 0.95 a 1.0 si tous les elements sont clairement visibles, 0.80 a 0.94 si quelques elements ne sont pas visibles, 0.60 a 0.79 si la photo est partiellement exploitable, moins de 0.60 si la photo est insuffisante. Ne retourne jamais 0 sauf si l image est inutilisable. Exemples de regles SST SONASID a associer seulement aux risques observes: N1 EPI, N2 Balisage, N3 Charge suspendue, N7 Conduite et engins, N8 Travaux en hauteur, N11 Elingage, N13 Manutention manuelle, N19 Circulation des engins, N20 Chargement/dechargement, N23 5S Site propre. A la fin, les listes main_risks et prevention_measures doivent prioriser les 3 risques les plus critiques et les mesures associees. Pose UNE seule question pertinente permettant de lever une incertitude importante. Ne jamais poser une question dont la reponse est deja visible sur l image. Les mesures de prevention doivent etre specifiques, actionnables sur terrain, et adaptees au danger visible. Les regles related_sst_rules doivent etre choisies uniquement si elles correspondent directement a un risque observe; ne pas citer de regle SST pour une categorie seulement theorique. "
            "Avant de repondre, effectue une double verification: 1 verifier que chaque risque est reellement visible; 2 verifier qu aucun risque majeur visible n a ete oublie. "
            "Retourne uniquement un JSON valide avec exactement ces cles: classification, confidence, observations, scene_summary, risk_items, main_risks, prevention_measures, global_risk_level, global_risk_reason, immediate_danger, recommended_action, questions, location_hints, related_sst_rules. "
            "observations doit etre une liste de constats visibles neutres. risk_items doit etre une liste d objets avec: risk, observation, cause, description, possible_consequences, severity, prevention_measure, sst_rule. risk_items doit contenir seulement les dangers directement observes, jamais des risques theoriques ni des elements conformes/proteges. observation et description doivent citer le fait visible qui prouve le danger. cause doit rester prudente et basee sur l observation. possible_consequences doit decrire les consequences possibles. severity doit etre LOW, MEDIUM, HIGH ou CRITICAL. prevention_measure doit etre une action terrain specifique. sst_rule doit citer uniquement la regle SST SONASID directement liee au risque observe, sinon chaine vide. "
            "main_risks, prevention_measures, questions, location_hints et related_sst_rules doivent etre des listes de textes dans la langue demandee. questions doit contenir une seule question. "
            "Interdiction de remplir les listes avec des phrases vagues ou repetees. Chaque risque doit etre specifique et base sur un indice visuel."
        )
        user_text = (
            "Contexte RAG SONASID et regles SST disponibles:\n"
            f"{context}\n\n"
            "Analyse cette photo HSE selon la methode AMANE stricte: uniquement les faits visibles, aucune hypothese transformee en fait, chaque risque doit etre observable. Ne confonds pas un risque theorique avec un risque observe: une machine visible, une voie de circulation visible ou un equipement protege ne suffit pas. Il faut un danger direct clairement perceptible pour remplir Risques observes. Commence par produire observations: une liste de faits visibles neutres, puis deduis les risques observes a partir de ces observations. "
            "Balaye toutes les categories: EPI, hauteur, levage, circulation, machines, electricite, incendie, manutention, sol/environnement, produits. "
            "Si une categorie ne peut pas etre conclue, utilise une formule non confirmable. Le contenu lisible par l utilisateur doit respecter la langue demandee. "
            "Retourne une analyse precise, non repetitive, avec une seule question finale utile."
        )

        errors: list[str] = []
        model_candidates = []
        for model in [settings.OPENAI_VISION_MODEL, llm_service.model]:
            if model and model not in model_candidates:
                model_candidates.append(model)

        for model in model_candidates:
            try:
                response = llm_service.client.chat.completions.create(
                    model=model,
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
                    temperature=0.05,
                    response_format={"type": "json_object"},
                )
                content = response.choices[0].message.content or "{}"
                result = {**fallback, **json.loads(content)}
                result["source_image"] = str(image_path)
                result["vision_model"] = model
                return self._ensure_result_language(self._normalize_result(result), language)
            except Exception as exc:
                errors.append(f"{model}: {exc}")

        return self._normalize_result({**fallback, "vision_error": " | ".join(errors)})

    @staticmethod
    def _fallback(image_path: Path) -> dict[str, Any]:
        return {
            "classification": "A confirmer",
            "confidence": 0.35,
            "observations": [],
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
        try:
            result["confidence"] = max(0.0, min(1.0, float(result.get("confidence") or 0.0)))
        except (TypeError, ValueError):
            result["confidence"] = 0.35
        result["observations"] = [cls._soften_visual_overclaims(str(item)) for item in cls._as_list(result.get("observations")) if str(item).strip()]
        result["immediate_danger"] = bool(result.get("immediate_danger"))
        result["risk_items"] = cls._normalize_risk_items(result.get("risk_items"))
        for key in ["main_risks", "prevention_measures", "questions", "location_hints", "related_sst_rules"]:
            result[key] = [cls._soften_visual_overclaims(str(item)) for item in cls._as_list(result.get(key)) if str(item).strip()]
        if not result["observations"] and result["risk_items"]:
            result["observations"] = [item["observation"] for item in result["risk_items"] if item.get("observation")]
        observed_rules: list[str] = []
        for item in result["risk_items"]:
            rule = str(item.get("sst_rule") or "").strip()
            if rule and rule not in observed_rules:
                observed_rules.append(cls._soften_visual_overclaims(rule))
        if observed_rules:
            result["related_sst_rules"] = observed_rules
        if result["risk_items"] and not result["main_risks"]:
            result["main_risks"] = [item["risk"] for item in result["risk_items"] if item.get("risk")][:5]
        if result["risk_items"] and not result["prevention_measures"]:
            result["prevention_measures"] = [
                item["prevention_measure"] for item in result["risk_items"] if item.get("prevention_measure")
            ][:8]
        if not result["risk_items"]:
            result["main_risks"] = []
            result["related_sst_rules"] = []
            result["global_risk_level"] = "LOW"
        else:
            severity_order = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}
            max_observed_severity = max(
                (severity_order.get(str(item.get("severity") or "MEDIUM").upper(), 2) for item in result["risk_items"]),
                default=2,
            )
            current_level = str(result.get("global_risk_level") or "MEDIUM").upper()
            current_rank = severity_order.get(current_level, 2)
            if current_rank > max_observed_severity:
                result["global_risk_level"] = next(level for level, rank in severity_order.items() if rank == max_observed_severity)
        level = str(result.get("global_risk_level") or "MEDIUM").upper()
        result["global_risk_level"] = level if level in {"LOW", "MEDIUM", "HIGH", "CRITICAL"} else "MEDIUM"
        result["scene_summary"] = cls._soften_visual_overclaims(str(result.get("scene_summary") or result.get("description") or "Analyse photo HSE."))
        if result["confidence"] <= 0.0 and (result["observations"] or result["risk_items"] or result["scene_summary"]):
            result["confidence"] = 0.35
        result["description"] = result["scene_summary"]
        result["recommended_action"] = cls._soften_visual_overclaims(str(result.get("recommended_action") or "Securiser la zone et confirmer l'analyse avec le responsable HSE."))
        result["global_risk_reason"] = cls._soften_visual_overclaims(str(result.get("global_risk_reason") or "Niveau etabli selon les risques visibles sur la photo."))
        return result

    @classmethod
    def _ensure_result_language(cls, result: dict[str, Any], language: str) -> dict[str, Any]:
        if language != "ar" or not llm_service.available:
            return result
        if not cls._needs_arabic_translation(result):
            return result
        return cls._translate_result_to_arabic(result)

    @classmethod
    def _needs_arabic_translation(cls, result: dict[str, Any]) -> bool:
        texts: list[str] = []
        for key in ["scene_summary", "recommended_action", "global_risk_reason", "observations"]:
            value = str(result.get(key) or "").strip()
            if value:
                texts.append(value)
        for key in ["main_risks", "prevention_measures", "questions", "location_hints", "related_sst_rules"]:
            texts.extend(str(item).strip() for item in cls._as_list(result.get(key)) if str(item).strip())
        for item in cls._as_list(result.get("risk_items")):
            if isinstance(item, dict):
                texts.extend(
                    str(item.get(key) or "").strip()
                    for key in ["risk", "observation", "cause", "description", "possible_consequences", "prevention_measure", "sst_rule"]
                    if str(item.get(key) or "").strip()
                )
        if not texts:
            return False
        non_arabic = [value for value in texts if not cls._has_arabic(value)]
        return len(non_arabic) >= max(1, len(texts) // 3)

    @classmethod
    def _translate_result_to_arabic(cls, result: dict[str, Any]) -> dict[str, Any]:
        payload = {
            "observations": result.get("observations", []),
            "scene_summary": result.get("scene_summary"),
            "risk_items": result.get("risk_items", []),
            "main_risks": result.get("main_risks", []),
            "prevention_measures": result.get("prevention_measures", []),
            "global_risk_reason": result.get("global_risk_reason"),
            "recommended_action": result.get("recommended_action"),
            "questions": result.get("questions", []),
            "location_hints": result.get("location_hints", []),
            "related_sst_rules": result.get("related_sst_rules", []),
        }
        try:
            response = llm_service.client.chat.completions.create(
                model=llm_service.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Translate all user-facing textual values in this JSON to clear professional Modern Standard Arabic. "
                            "Keep the same JSON keys and list structure. Do not add risks. Do not change classification, severity, booleans, model names, or source data. "
                            "Preserve official names such as SONASID, AMANE, HSE, SAP and technical acronyms. Return only valid JSON."
                        ),
                    },
                    {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
                ],
                temperature=0.0,
                response_format={"type": "json_object"},
            )
            translated = json.loads(response.choices[0].message.content or "{}")
        except Exception:
            return result

        merged = dict(result)
        for key in [
            "observations",
            "scene_summary",
            "main_risks",
            "prevention_measures",
            "global_risk_reason",
            "recommended_action",
            "questions",
            "location_hints",
            "related_sst_rules",
        ]:
            if translated.get(key):
                merged[key] = translated[key]
        if isinstance(translated.get("risk_items"), list):
            merged["risk_items"] = translated["risk_items"]
        merged["description"] = merged.get("scene_summary", result.get("description"))
        return merged

    @staticmethod
    def _strip_accents(text: str) -> str:
        return "".join(
            char for char in unicodedata.normalize("NFKD", text)
            if not unicodedata.combining(char)
        )

    @classmethod
    def _is_observed_risk_item(cls, item: dict[str, str]) -> bool:
        risk = str(item.get("risk") or "").strip()
        description = str(item.get("description") or "").strip()
        observation = str(item.get("observation") or description).strip()
        combined = cls._strip_accents(f"{risk} {observation} {description}".lower())
        non_observed_markers = {
            "non confirmable",
            "aucun element visible",
            "a confirmer",
            "ne peut pas etre confirme",
            "ne sont pas confirmables",
            "risque theorique",
            "risque potentiel",
            "hypothese",
            "غير قابل للتأكيد",
            "لا يمكن تأكيد",
            "يحتاج إلى تأكيد",
            "غير مؤكد",
            "لا يوجد عنصر مرئي",
            "لا توجد عناصر مرئية",
        }
        if any(marker in combined for marker in non_observed_markers):
            return False
        if len(observation) < 18:
            return False
        return True

    @classmethod
    def _normalize_risk_items(cls, value: Any) -> list[dict[str, str]]:
        items = cls._as_list(value)
        normalized: list[dict[str, str]] = []
        for item in items:
            if isinstance(item, dict):
                severity = str(item.get("severity") or "MEDIUM").upper()
                observation = cls._soften_visual_overclaims(
                    str(item.get("observation") or item.get("description") or "Aucun fait visible detaille n a ete fourni.")
                )
                cause = cls._soften_visual_overclaims(
                    str(item.get("cause") or "Cause non confirmable sur cette photographie.")
                )
                prevention_measure = cls._soften_visual_overclaims(
                    str(
                        item.get("prevention_measure")
                        or item.get("measure")
                        or item.get("recommended_action")
                        or "Securiser la zone et confirmer l action avec le responsable HSE."
                    )
                )
                sst_rule = cls._soften_visual_overclaims(
                    str(item.get("sst_rule") or item.get("rule") or item.get("regle_sst") or "")
                )
                normalized.append(
                    {
                        "risk": cls._soften_visual_overclaims(str(item.get("risk") or "Risque observe")),
                        "observation": observation,
                        "description": observation,
                        "cause": cause,
                        "possible_consequences": cls._soften_visual_overclaims(
                            str(item.get("possible_consequences") or item.get("consequences") or "Accident potentiel.")
                        ),
                        "severity": severity if severity in {"LOW", "MEDIUM", "HIGH", "CRITICAL"} else "MEDIUM",
                        "prevention_measure": prevention_measure,
                        "sst_rule": sst_rule,
                    }
                )
            elif str(item).strip():
                normalized.append(
                    {
                        "risk": str(item),
                        "observation": "A confirmer sur terrain.",
                        "description": "A confirmer sur terrain.",
                        "cause": "Cause non confirmable sur cette photographie.",
                        "possible_consequences": "Accident potentiel.",
                        "severity": "MEDIUM",
                        "prevention_measure": "Securiser la zone et confirmer l action avec le responsable HSE.",
                        "sst_rule": "",
                    }
                )
        return [item for item in normalized if cls._is_observed_risk_item(item)]

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
        if value:
            return value
        return "\u063a\u064a\u0631 \u0645\u062d\u062f\u062f\u060c \u064a\u062c\u0628 \u062a\u0623\u0643\u064a\u062f\u0647 \u0645\u064a\u062f\u0627\u0646\u064a\u0627."

    @staticmethod
    def _confidence_percent(value: Any) -> str:
        try:
            number = float(value or 0.0)
        except (TypeError, ValueError):
            number = 0.0
        if number > 1:
            number = number / 100
        number = max(0.0, min(1.0, number))
        return f"{round(number * 100)}%"

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
            "confidence": "Confidence index" if is_en else "Indice de confiance",
            "observations": "Observations" if is_en else "Observations",
            "summary": "Scene summary" if is_en else "Resume",
            "observed": "Observed risks" if is_en else "Risques observes",
            "main": "Main risks" if is_en else "Principaux risques",
            "prevention": "Recommended prevention measures" if is_en else "Mesures de prevention recommandees",
            "reason": "Overall risk justification" if is_en else "Justification du niveau global",
            "rules": "Related SONASID SST rules" if is_en else "Regles SST SONASID liees",
            "question": "AMANE question" if is_en else "Question AMANE",
            "observation": "Observation" if is_en else "Observation",
            "cause": "Cause" if is_en else "Cause",
            "consequences": "Possible consequences" if is_en else "Consequences possibles",
            "risk_level": "Level" if is_en else "Gravite",
            "prevention_measure": "Prevention measure" if is_en else "Mesure de prevention",
            "sst_rule": "SONASID SST rule" if is_en else "Regle SST SONASID",
            "non_confirmable": "Not confirmable from this photograph" if is_en else "Non confirmable sur cette photographie",
            "no_precise": "No directly observable danger was detected in the photo; keep standard vigilance and confirm on site if needed." if is_en else "Aucun danger directement observable n a ete detecte sur la photo; maintenir la vigilance standard et confirmer sur terrain si besoin.",
            "default_risk": "No direct danger observed" if is_en else "Aucun danger direct observe",
            "default_action": "Secure the area and confirm the analysis with the HSE supervisor." if is_en else "Securiser la zone et confirmer l'analyse avec le responsable HSE.",
            "default_question": "Do you confirm whether this is an unsafe act or an unsafe condition?" if is_en else "Confirmez-vous s'il s'agit d'un acte dangereux ou d'une situation dangereuse ?",
            "no_observation": "No clear factual observation could be extracted automatically." if is_en else "Aucune observation factuelle claire n a pu etre extraite automatiquement.",
        }
        risk_lines = []
        for item in result.get("risk_items", [])[:12]:
            risk_lines.extend(
                [
                    f"- {item.get('risk', 'Risque')}",
                    f"  {labels['observation']}: {item.get('observation') or item.get('description') or labels['non_confirmable']}",
                    f"  {labels['cause']}: {item.get('cause') or labels['non_confirmable']}",
                    f"  {labels['consequences']}: {item.get('possible_consequences') or labels['non_confirmable']}",
                    f"  {labels['risk_level']}: {VisionRiskAgent._level_label_latin(item.get('severity', 'MEDIUM'), language)}",
                    f"  {labels['prevention_measure']}: {item.get('prevention_measure') or result.get('recommended_action') or labels['default_action']}",
                    f"  {labels['sst_rule']}: {item.get('sst_rule') or labels['non_confirmable']}",
                ]
            )
        if not risk_lines:
            risk_lines.append("- " + labels["no_precise"])

        observations = result.get("observations", []) or [labels["no_observation"]]
        main_risks = result.get("main_risks", []) or [labels["default_risk"]]
        prevention = result.get("prevention_measures", []) or [result.get("recommended_action", labels["default_action"])]
        rules = result.get("related_sst_rules", [])
        questions = result.get("questions", []) or [labels["default_question"]]

        sections = [
            labels["title"],
            "",
            f"{labels['classification']}: {'Les deux' if result.get('classification') == 'Acte dangereux et situation dangereuse' and language == 'fr' else result.get('classification', 'A confirmer')}",
            f"{labels['level']}: {VisionRiskAgent._level_label_latin(result.get('global_risk_level', 'MEDIUM'), language)}",
            f"{labels['confidence']}: {VisionRiskAgent._confidence_percent(result.get('confidence'))}",
            "",
            labels["observations"] + ":",
            *(f"- {observation}" for observation in observations[:8]),
            "",
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
            risk_lines.extend(
                [
                    f"- {VisionRiskAgent._arabic_or_note(item.get('risk', '\u062e\u0637\u0631'))}",
                    f"  \u0627\u0644\u0645\u0644\u0627\u062d\u0638\u0629: {VisionRiskAgent._arabic_or_note(item.get('observation') or item.get('description'))}",
                    f"  \u0627\u0644\u0633\u0628\u0628: {VisionRiskAgent._arabic_or_note(item.get('cause'))}",
                    f"  \u0627\u0644\u0639\u0648\u0627\u0642\u0628 \u0627\u0644\u0645\u062d\u062a\u0645\u0644\u0629: {VisionRiskAgent._arabic_or_note(item.get('possible_consequences'))}",
                    f"  \u0627\u0644\u062e\u0637\u0648\u0631\u0629: {VisionRiskAgent._level_label(item.get('severity', 'MEDIUM'))}",
                    f"  \u0625\u062c\u0631\u0627\u0621 \u0627\u0644\u0648\u0642\u0627\u064a\u0629: {VisionRiskAgent._arabic_or_note(item.get('prevention_measure') or result.get('recommended_action'))}",
                    f"  \u0642\u0627\u0639\u062f\u0629 SST SONASID: {VisionRiskAgent._arabic_or_note(item.get('sst_rule'))}",
                ]
            )
        if not risk_lines:
            risk_lines.append("- " + "\u0644\u0645 \u064a\u062a\u0645 \u0631\u0635\u062f \u062e\u0637\u0631 \u0645\u0628\u0627\u0634\u0631 \u0628\u0634\u0643\u0644 \u0648\u0627\u0636\u062d \u0639\u0644\u0649 \u0627\u0644\u0635\u0648\u0631\u0629\u061b \u064a\u062c\u0628 \u0627\u0644\u062d\u0641\u0627\u0638 \u0639\u0644\u0649 \u0627\u0644\u064a\u0642\u0638\u0629 \u0648\u0627\u0644\u062a\u0623\u0643\u064a\u062f \u0645\u064a\u062f\u0627\u0646\u064a\u0627 \u0639\u0646\u062f \u0627\u0644\u062d\u0627\u062c\u0629.")

        observations = result.get("observations", []) or ["\u0644\u0645 \u064a\u062a\u0645 \u0627\u0633\u062a\u062e\u0631\u0627\u062c \u0645\u0644\u0627\u062d\u0638\u0629 \u0645\u0631\u0626\u064a\u0629 \u0648\u0627\u0636\u062d\u0629 \u062a\u0644\u0642\u0627\u0626\u064a\u0627."]
        main_risks = result.get("main_risks", []) or ["\u0644\u0645 \u064a\u062a\u0645 \u0631\u0635\u062f \u062e\u0637\u0631 \u0645\u0628\u0627\u0634\u0631 \u0639\u0644\u0649 \u0627\u0644\u0635\u0648\u0631\u0629"]
        prevention = result.get("prevention_measures", []) or [result.get("recommended_action", "\u064a\u062c\u0628 \u062a\u0623\u0645\u064a\u0646 \u0627\u0644\u0645\u0646\u0637\u0642\u0629.")]
        rules = result.get("related_sst_rules", [])
        questions = result.get("questions", []) or ["\u0647\u0644 \u062a\u0624\u0643\u062f \u0647\u0630\u0627 \u0627\u0644\u062a\u062d\u0644\u064a\u0644\u061f"]

        sections = [
            "\u062a\u062d\u0644\u064a\u0644 \u0635\u0648\u0631\u0629 HSE \u0628\u0648\u0627\u0633\u0637\u0629 AMANE",
            "",
            f"\u0627\u0644\u062a\u0635\u0646\u064a\u0641 \u0627\u0644\u0645\u0642\u062a\u0631\u062d: {VisionRiskAgent._classification_label_ar(result.get('classification', 'A confirmer'))}",
            f"\u0645\u0633\u062a\u0648\u0649 \u0627\u0644\u062e\u0637\u0631 \u0627\u0644\u0639\u0627\u0645: {VisionRiskAgent._level_label(result.get('global_risk_level', 'MEDIUM'))}",
            f"\u0645\u0624\u0634\u0631 \u0627\u0644\u062b\u0642\u0629: {VisionRiskAgent._confidence_percent(result.get('confidence'))}",
            "",
            "\u0627\u0644\u0645\u0644\u0627\u062d\u0638\u0627\u062a" + ":",
            *(f"- {VisionRiskAgent._arabic_or_note(observation)}" for observation in observations[:8]),
            "",
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
        risks = ", ".join(item.get("risk", "") for item in result.get("risk_items", []) if item.get("risk")) or "aucun danger direct observe"
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
