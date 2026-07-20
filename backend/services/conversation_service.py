from datetime import datetime
from enum import Enum
import json
from pathlib import Path
import re
import unicodedata
from typing import Any

from sqlalchemy.orm import Session

from ai.llm import llm_service
from ai.rag import rag_service
from schemas.report import ReportCreate
from services.report_service import ReportService, normalize_classification
from services.employee_directory import employee_directory


USER_CORRECTIONS_PATH = Path(__file__).resolve().parent.parent / "knowledge" / "user_corrections.json"


class ConversationStep(str, Enum):
    START = "start"
    EMERGENCY_CHECK = "emergency_check"
    CLASSIFICATION = "classification"
    DESCRIPTION = "description"
    EVENT_DATETIME = "event_datetime"
    LOCATION = "location"
    OBSERVED_PERSON = "observed_person"
    DECLARANT = "declarant"
    IMMEDIATE_ACTION = "immediate_action"
    RISK_ANALYSIS = "risk_analysis"
    SUMMARY = "summary"
    CONFIRMATION = "confirmation"
    COMPLETED = "completed"


QUESTIONS_FR = {
    ConversationStep.EMERGENCY_CHECK: (
        "Cette situation prÃ©sente-t-elle un danger immÃ©diat pour vous "
        "ou pour les personnes autour de vous ?"
    ),
    ConversationStep.CLASSIFICATION: (
        "S'agit-il d'un acte dangereux ou d'une situation dangereuse ?"
    ),
    ConversationStep.DESCRIPTION: (
        "Pouvez-vous dÃ©crire prÃ©cisÃ©ment ce qui s'est passÃ© ?"
    ),
    ConversationStep.EVENT_DATETIME: (
        "Quelle est la date et l'heure de l'Ã©vÃ©nement ?"
    ),
    ConversationStep.LOCATION: (
        "Sur quel site cela s'est-il produit ? "
        "PrÃ©cisez l'atelier, la zone et l'emplacement exact."
    ),
    ConversationStep.OBSERVED_PERSON: (
        "Une personne a-t-elle Ã©tÃ© observÃ©e en situation dangereuse ?"
    ),
    ConversationStep.DECLARANT: "Quel est votre nom ou votre matricule ?",
    ConversationStep.IMMEDIATE_ACTION: (
        "Quelle action immÃ©diate a Ã©tÃ© rÃ©alisÃ©e ou doit Ãªtre rÃ©alisÃ©e "
        "pour sÃ©curiser la situation ?"
    ),
    ConversationStep.RISK_ANALYSIS: (
        "Quel risque cette situation pourrait-elle provoquer dans le futur ?"
    ),
}


QUESTIONS_DARIJA = {
    ConversationStep.EMERGENCY_CHECK: (
        "Wach kayne chi khatar daba aalik oula aala nass li maak?"
    ),
    ConversationStep.CLASSIFICATION: (
        "Wach hadchi acte dangereux oula situation dangereuse?"
    ),
    ConversationStep.DESCRIPTION: (
        "Afak chraah lia b tafsil chnou oukaa."
    ),
    ConversationStep.EVENT_DATETIME: (
        "Fach oukaa had lhadath? Aatini tarikh ou l waqt."
    ),
    ConversationStep.LOCATION: (
        "Fin oukaa hadchi? Aatini site, atelier, ou zone b dabt."
    ),
    ConversationStep.OBSERVED_PERSON: (
        "Wach kayne chi wahed oula chi wahda kan f wadiya khatira?"
    ),
    ConversationStep.DECLARANT: "Chnou smitak oula matricule dyalek?",
    ConversationStep.IMMEDIATE_ACTION: (
        "Chnou l action li derto daba bach tseddo l khatar?"
    ),
    ConversationStep.RISK_ANALYSIS: (
        "Chnou l khatar li momkin youkaa mn baad ila bqat had l wadiya?"
    ),
}
QUESTIONS_EN = {
    ConversationStep.EMERGENCY_CHECK: (
        "Does this situation present an immediate danger to you or to people around you?"
    ),
    ConversationStep.CLASSIFICATION: (
        "Is this an unsafe act or an unsafe condition?"
    ),
    ConversationStep.DESCRIPTION: (
        "Please describe precisely what happened."
    ),
    ConversationStep.EVENT_DATETIME: (
        "What is the date and time of the event?"
    ),
    ConversationStep.LOCATION: (
        "Where did it happen? Please specify the site, workshop, area, and exact location."
    ),
    ConversationStep.OBSERVED_PERSON: (
        "Was anyone observed in an unsafe situation?"
    ),
    ConversationStep.DECLARANT: "What is your name or employee ID?",
    ConversationStep.IMMEDIATE_ACTION: (
        "What immediate action was taken or should be taken to secure the situation?"
    ),
    ConversationStep.RISK_ANALYSIS: (
        "What risk could this situation cause in the future?"
    ),
}

NEXT_STEP = {
    ConversationStep.START: ConversationStep.EMERGENCY_CHECK,
    ConversationStep.EMERGENCY_CHECK: ConversationStep.CLASSIFICATION,
    ConversationStep.CLASSIFICATION: ConversationStep.DESCRIPTION,
    ConversationStep.DESCRIPTION: ConversationStep.EVENT_DATETIME,
    ConversationStep.EVENT_DATETIME: ConversationStep.LOCATION,
    ConversationStep.LOCATION: ConversationStep.OBSERVED_PERSON,
    ConversationStep.OBSERVED_PERSON: ConversationStep.DECLARANT,
    ConversationStep.DECLARANT: ConversationStep.IMMEDIATE_ACTION,
    ConversationStep.IMMEDIATE_ACTION: ConversationStep.RISK_ANALYSIS,
    ConversationStep.RISK_ANALYSIS: ConversationStep.SUMMARY,
    ConversationStep.SUMMARY: ConversationStep.CONFIRMATION,
    ConversationStep.CONFIRMATION: ConversationStep.COMPLETED,
}


FIELD_BY_STEP = {
    ConversationStep.EMERGENCY_CHECK: "immediate_danger",
    ConversationStep.CLASSIFICATION: "classification",
    ConversationStep.DESCRIPTION: "description",
    ConversationStep.EVENT_DATETIME: "event_datetime",
    ConversationStep.LOCATION: "location",
    ConversationStep.OBSERVED_PERSON: "observed_person",
    ConversationStep.DECLARANT: "declarant",
    ConversationStep.IMMEDIATE_ACTION: "immediate_action",
    ConversationStep.RISK_ANALYSIS: "risk_analysis",
}


GENERAL_SITE_ZONES = {
    1: "Bureau de pont-bascule / loge de garde",
    2: "Station service et garage",
    3: "Parachevement",
    4: "Stockage couronnes",
    5: "Batiment du laminoir",
    6: "Atelier cylindres et magasins",
    7: "Salle de commande electrique",
    8: "Traitement d'eau pour laminoir",
    9: "Traitement d'eau brute",
    10: "Reservoir",
    11: "Stockage du fuel lourd",
    12: "Parc de stockage a billettes",
    13: "Bureaux",
    14: "Centre de formation",
    15: "Batiment des services",
    16: "Sous-station principale",
}

LAMINOIR_ZONES = {
    1: "Stockage et manutention de billettes",
    2: "Four de rechauffage",
    3: "Cisaille pour billettes",
    4: "Cages degrossisseuses",
    5: "Cisailles a ebouter",
    6: "Cages intermediaires",
    7: "Pupitre de commande principal du laminoir",
    8: "Presse a loups / cobble bundle",
    9: "Trains finisseurs No Twist",
    10: "Boite a eau",
    11: "Aiguille pour bobinoir",
    12: "Bobinoirs",
    13: "Formeurs de spires / laying heads",
    14: "Convoyeurs Stelmor",
    15: "Formeurs de couronnes / reform tubs",
    16: "Chariot collecteur C hook carrier",
    17: "Convoyeur de couronnes / coil handling system",
    18: "Compacteuses a couronnes et machines a ligaturer",
}


class ConversationService:
    def __init__(self) -> None:
        self.sessions: dict[str, dict[str, Any]] = {}
        self.user_corrections: dict[str, str] = self._load_user_corrections()

    def _get_or_create_session(self, session_id: str) -> dict[str, Any]:
        if session_id not in self.sessions:
            self.sessions[session_id] = {
                "step": ConversationStep.START,
                "language": "fr",
                "data": {},
                "corrections": dict(self.user_corrections),
            }

        return self.sessions[session_id]

    def reset_session(self, session_id: str) -> bool:
        return self.sessions.pop(session_id, None) is not None

    @staticmethod
    def _load_user_corrections() -> dict[str, str]:
        try:
            if USER_CORRECTIONS_PATH.exists():
                data = json.loads(USER_CORRECTIONS_PATH.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    return {str(k): str(v) for k, v in data.items() if str(k).strip() and str(v).strip()}
        except Exception:
            return {}
        return {}

    def _save_user_correction(self, wrong: str, right: str) -> None:
        wrong = wrong.strip(" .,:;!?\"'â€œâ€â€˜â€™")
        right = right.strip(" .,:;!?\"'â€œâ€â€˜â€™")
        if not wrong or not right:
            return
        self.user_corrections[wrong] = right
        USER_CORRECTIONS_PATH.parent.mkdir(parents=True, exist_ok=True)
        USER_CORRECTIONS_PATH.write_text(
            json.dumps(self.user_corrections, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    @staticmethod
    def _clean_correction_part(value: str) -> str:
        return re.sub(r"^(que|quand|si|je dis|tu comprends|comprends|ecris|Ã©cris)\s+", "", value.strip(), flags=re.IGNORECASE).strip(" .,:;!?\"'â€œâ€â€˜â€™")

    @classmethod
    def _extract_user_correction(cls, message: str) -> tuple[str, str] | None:
        text = (message or "").strip()
        patterns = [
            r"(?:corrige|correction)\s+(.+?)\s+(?:par|en|avec)\s+(.+)$",
            r"(?:quand|si)\s+je\s+dis\s+(.+?)\s*(?:,|;)?\s*(?:tu\s+comprends|comprends|ca\s+veut\s+dire|Ã§a\s+veut\s+dire|ecris|Ã©cris)\s+(.+)$",
            r"(?:ce\s+n['â€™]?est\s+pas|c['â€™]?est\s+pas)\s+(.+?)\s*(?:,|;)?\s*(?:c['â€™]?est|mais|corrige\s+par)\s+(.+)$",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, flags=re.IGNORECASE)
            if match:
                wrong = cls._clean_correction_part(match.group(1))
                right = cls._clean_correction_part(match.group(2))
                if wrong and right and wrong.lower() != right.lower():
                    return wrong, right
        normalized = cls._normalize(text)
        if any(expr in normalized for expr in {"smitk amane", "smitk amane", "ton nom amane", "tu t appelles amane", "tu t'appelle amane"}):
            return "AMANE AI", "AMANE"
        return None

    @staticmethod
    def _apply_corrections(message: str, corrections: dict[str, str]) -> str:
        corrected = message or ""
        for wrong, right in sorted(corrections.items(), key=lambda item: len(item[0]), reverse=True):
            if not wrong.strip():
                continue
            corrected = re.sub(re.escape(wrong), right, corrected, flags=re.IGNORECASE)
        return corrected

    @staticmethod
    def _correction_response(wrong: str, right: str, language: str) -> str:
        if language == "darija":
            return f"Wakha, fhemt. Ila t9al '{wrong}', ghadi nktebha '{right}'."
        if language == "en":
            return f"Understood. When I hear '{wrong}', I will correct it to '{right}'."
        return f"D'accord, correction enregistrÃ©e : '{wrong}' sera compris comme '{right}'."

    @classmethod
    def _prefill_opening_statement(cls, session: dict[str, Any], message: str) -> None:
        cleaned = message.strip()
        if not cleaned:
            return

        normalized = cls._normalize(cleaned)
        report_markers = {
            "danger", "risque", "incident", "reclamation", "rÃ©clamation", "signaler",
            "anomalie", "fuite", "huile", "glissade", "cable", "cÃ¢ble", "convoyeur",
            "maintenance", "soudure", "bghit", "mouchkil", "mochkil", "khatar",
        }
        is_report_detail = len(cleaned) >= 25 or any(marker in normalized for marker in report_markers)
        if is_report_detail:
            session["data"].setdefault("description", cleaned)

        if "classification" not in session["data"]:
            unsafe_act_markers = {
                "acte", "comportement", "sans casque", "sans epi",
                "unsafe act", "fØ¹Ù„", "ØªØµØ±Ù",
            }
            unsafe_condition_markers = {
                "situation", "condition", "fuite", "huile", "cable", "cÃ¢ble",
                "flaque", "convoyeur", "zone", "unsafe condition", "ÙˆØ¶Ø¹ÙŠØ©",
            }
            if any(marker in normalized for marker in unsafe_act_markers):
                session["data"]["classification"] = "Acte dangereux"
            elif any(marker in normalized for marker in unsafe_condition_markers):
                session["data"]["classification"] = "Situation dangereuse"


    @staticmethod
    def _next_unfilled_step(step: ConversationStep, data: dict[str, Any]) -> ConversationStep:
        next_step = step
        terminal_steps = {ConversationStep.SUMMARY, ConversationStep.CONFIRMATION, ConversationStep.COMPLETED}
        while next_step not in terminal_steps:
            field_name = FIELD_BY_STEP.get(next_step)
            if not field_name:
                break
            if field_name not in data or data[field_name] in (None, ""):
                break
            next_step = NEXT_STEP[next_step]
        return next_step
    @staticmethod
    def _normalize(message: str) -> str:
        normalized = unicodedata.normalize("NFKD", message.strip().lower())
        without_accents = "".join(
            char for char in normalized if not unicodedata.combining(char)
        )
        return re.sub(r"[^a-z0-9' ]+", " ", without_accents)

    @classmethod
    def _tokens(cls, message: str) -> list[str]:
        return cls._normalize(message).split()

    @staticmethod
    def _contains_arabic(message: str) -> bool:
        return any("\u0600" <= char <= "\u06ff" for char in message)

    @classmethod
    def _looks_like_french_sentence(cls, message: str) -> bool:
        normalized = cls._normalize(message)
        tokens = normalized.split()
        if not tokens:
            return False

        french_markers = {
            "bonjour", "bonsoir", "salut", "je", "j", "tu", "il", "elle", "nous",
            "vous", "ils", "elles", "mon", "ma", "mes", "notre", "votre", "le", "la",
            "les", "un", "une", "des", "du", "de", "dans", "sur", "avec", "pour",
            "pres", "pr?s", "au", "aux", "est", "suis", "sommes", "etes", "?tes",
            "sont", "veux", "voudrais", "peux", "peut", "pouvez", "signaler",
            "declarer", "d?clarer", "remonter", "confirmer", "merci", "risque",
            "danger", "situation", "acte", "atelier", "zone", "photo", "analyse",
        }
        darija_strong_markers = {
            "salam", "salem", "salaam", "slm", "labas", "bghit", "baghi", "bgha",
            "wash", "wach", "kayn", "kayna", "ghadi", "bzzaf", "khatar", "mouchkil",
            "mochkil", "afak", "3afak", "safi", "wakha", "iyah", "iyeh", "wah",
            "chno", "chnu", "fayn", "fin", "daba", "hna", "tma", "dyal", "dial",
            "machi", "makaynch", "makaynach", "walo",
        }
        french_score = sum(1 for token in tokens if token in french_markers)
        darija_score = sum(1 for token in tokens if token in darija_strong_markers)

        if darija_score:
            return False
        return french_score >= 2 or (len(tokens) >= 6 and french_score >= 1)

    @classmethod
    def _detect_language(cls, message: str) -> str:
        normalized = cls._normalize(message)
        darija_markers = {
            "salam", "salem", "salaam", "slm", "labas", "bghit", "baghi", "bgha",
            "wash", "wach", "kayn", "kayna", "kano", "kan", "kat", "ghadi", "bzzaf",
            "khatar", "mouchkil", "mochkil", "afak", "3afak", "safi", "wakha",
            "iyah", "iyeh", "wah", "chno", "chnu", "fayn", "fin", "daba", "hna",
            "tma", "dyal", "dial", "machi", "lli", "chi", "wahed", "nass",
            "makaynch", "makaynach", "walo",
        }
        english_markers = {
            "hello", "hi", "please", "help", "report", "unsafe", "hazard",
            "dangerous", "condition", "incident", "risk", "yes", "no", "oil",
            "leak", "slip", "location", "workshop", "what", "where", "when", "who", "how",
        }

        if cls._contains_arabic(message):
            return "darija"

        if cls._looks_like_french_sentence(message):
            return "fr"

        tokens = set(normalized.split())
        if tokens.intersection(darija_markers):
            return "darija"
        return "en" if tokens.intersection(english_markers) else "fr"

    @classmethod
    def _should_keep_darija(cls, current_language: str, detected_language: str, message: str) -> bool:
        if current_language != "darija" or detected_language != "fr":
            return False

        if cls._looks_like_french_sentence(message):
            return False

        normalized = cls._normalize(message)
        tokens = set(normalized.split())
        hse_short_answers = {
            "situation", "dangereuse", "acte", "danger", "risque", "zone", "maintenance",
            "convoyeur", "nador", "sonasid", "casque", "epi", "fuite", "huile", "glissade",
            "responsable", "service", "hse", "atelier", "laminoir", "acierie", "aci?rie",
        }

        if len(tokens) <= 4 and tokens.intersection(hse_short_answers):
            return True
        return False

    @classmethod
    def _is_greeting_only(cls, message: str) -> bool:
        normalized = cls._normalize(message)
        raw = message.strip()
        raw_lower = raw.lower()
        greeting_words = {
            "bonjour",
            "bonsoir",
            "salut",
            "salam",
            "salem",
            "salaam",
            "slm",
            "Ø§Ù„Ø³Ù„Ø§Ù…",
            "Ø³Ù„Ø§Ù…",
            "ahlan",
            "hello",
            "amane",
            "aman",
            "amen",
        }
        intent_words = {
            "declarer",
            "declare",
            "report",
            "unsafe",
            "hazard",
            "incident",
            "dÃ©claration",
            "signaler",
            "signale",
            "anomalie",
            "danger",
            "risque",
            "reclamation",
            "bghit",
            "mouchkil",
            "mochkil",
            "khatar",
            "Ø¨ØºÙŠØª",
            "Ù…Ø´ÙƒÙ„",
            "Ø®Ø·Ø±",
        }

        if any(word in normalized or word in raw for word in intent_words):
            return False

        if cls._contains_arabic(raw) and any(word in raw for word in {"Ø³Ù„Ø§Ù…", "Ø§Ù„Ø³Ù„Ø§Ù…"}):
            return True

        tokens = [
            token for token in normalized.split()
            if token not in {"amane", "aman", "amen", "amel"}
        ]
        if raw_lower in greeting_words:
            return True
        return bool(tokens) and all(token in greeting_words for token in tokens)
    @classmethod
    def _is_yes(cls, message: str) -> bool:
        normalized = cls._normalize(message)
        tokens = cls._tokens(message)
        raw = message.strip().lower()

        yes_words = {
            "oui",
            "yes",
            "ok",
            "okay",
            "correct",
            "confirmer",
            "confirme",
            "valide",
            "ah",
            "ahh",
            "iyah",
            "iyeh",
            "ih",
            "wah",
            "wakha",
            "safi",
            "naam",
            "n3am",
        }
        yes_phrases = {
            "bien sur",
            "of course",
            "i confirm",
            "that is correct",
            "it is correct",
            "c'est correct",
            "je confirme",
            "c est bon",
            "c'est bon",
            "tout est correct",
            "Ø§ÙŠÙ‡",
            "Ù†Ø¹Ù…",
            "ÙˆØ§Ø®Ø§",
            "ØµØ§ÙÙŠ",
            "Ø§Ù‡",
        }

        return (
            bool(tokens) and tokens[0] in yes_words
        ) or any(phrase in normalized or phrase in raw for phrase in yes_phrases)

    @classmethod
    def _is_no(cls, message: str) -> bool:
        normalized = cls._normalize(message)
        tokens = cls._tokens(message)
        raw = message.strip().lower()

        no_words = {
            "non",
            "no",
            "nan",
            "aucun",
            "none",
            "not",
            "aucune",
            "la",
            "lla",
            "laa",
            "makaynch",
            "makaynach",
            "walo",
        }
        no_phrases = {
            "pas du tout",
            "not at all",
            "no danger",
            "no immediate danger",
            "there is no",
            "aucun danger",
            "aucune urgence",
            "pas de danger",
            "il n y a pas",
            "ma kaynch",
            "ma kaynach",
            "Ù„Ø§",
            "Ù…Ø§ÙƒØ§ÙŠÙ†Ø´",
            "Ù…Ø§ ÙƒØ§ÙŠÙ†Ø´",
            "ÙˆØ§Ù„Ùˆ",
        }

        return (
            bool(tokens) and tokens[0] in no_words
        ) or any(phrase in normalized or phrase in raw for phrase in no_phrases)

    @classmethod
    def _normalize_location_zone(cls, location: str) -> str:
        value = location.strip()
        if not value:
            return value

        normalized = cls._normalize(value)
        zone_match = re.search(r"\b(?:zone|zonne|zon|numero|num|n)\s*(\d{1,2})\b", normalized)

        laminoir_context = {
            "laminoir", "train", "fil", "veines", "billette", "billettes",
            "four", "rechauffage", "cage", "cages", "cisaille", "cisailles",
            "pupitre", "bobinoir", "bobinoirs", "stelmor", "couronne",
            "couronnes", "spires", "c", "hook", "compacteuse", "compacteuses",
            "ligaturer", "ligature", "no", "twist",
        }
        general_context = {
            "bureau", "bureaux", "garage", "parachevement", "formation",
            "services", "station", "poste", "garde", "pont", "bascule",
            "reservoir", "fuel", "sous", "station", "principale",
        }
        tokens = set(normalized.split())

        if zone_match:
            zone_number = int(zone_match.group(1))
            wants_general = bool(tokens & general_context) and not bool(tokens & laminoir_context)
            zone_name = None
            prefix = None

            if wants_general and zone_number in GENERAL_SITE_ZONES:
                zone_name = GENERAL_SITE_ZONES[zone_number]
                prefix = f"Site SONASID Nador, zone generale {zone_number}"
            elif zone_number in LAMINOIR_ZONES:
                zone_name = LAMINOIR_ZONES[zone_number]
                prefix = f"Site SONASID Nador, laminoir, zone {zone_number}"
            elif zone_number in GENERAL_SITE_ZONES:
                zone_name = GENERAL_SITE_ZONES[zone_number]
                prefix = f"Site SONASID Nador, zone generale {zone_number}"

            if zone_name:
                exact_value = f"{prefix} - {zone_name}"
                if cls._normalize(exact_value) != normalized:
                    return exact_value
            return value

        for zone_number, zone_name in LAMINOIR_ZONES.items():
            normalized_name = cls._normalize(zone_name.split("/")[0])
            if normalized_name and normalized_name in normalized:
                return f"Site SONASID Nador, laminoir, zone {zone_number} - {zone_name}"

        for zone_number, zone_name in GENERAL_SITE_ZONES.items():
            normalized_name = cls._normalize(zone_name.split("/")[0])
            if normalized_name and normalized_name in normalized:
                return f"Site SONASID Nador, zone generale {zone_number} - {zone_name}"

        return value

    @classmethod
    def _normalize_declarant_name(cls, value: str) -> str:
        cleaned = " ".join(value.strip().split())
        normalized = cls._normalize(cleaned)
        known_names = {
            "amine el fassi": "Amine El Fassi",
            "amin el fassi": "Amine El Fassi",
            "amen el fassi": "Amine El Fassi",
            "amane el fassi": "Amine El Fassi",
            "aman el fassi": "Amine El Fassi",
            "amel el fassi": "Amine El Fassi",
            "insaf el korachi": "Insaf El Korachi",
            "insaf el corachi": "Insaf El Korachi",
            "insaf el qorachi": "Insaf El Korachi",
            "insaf korachi": "Insaf El Korachi",
        }
        if normalized in known_names:
            return known_names[normalized]

        cleaned = re.sub(r"\b(?:amane|aman|amen|amel)\s+(el|al)\b", r"Amine El", cleaned, flags=re.IGNORECASE)
        words = []
        for word in cleaned.split():
            low = word.lower()
            if low in {"el", "al", "ben", "ibn"}:
                words.append(low.capitalize())
            elif word.isupper() and len(word) <= 4:
                words.append(word)
            else:
                words.append(word[:1].upper() + word[1:].lower())
        return " ".join(words)

    @classmethod
    def _normalize_event_datetime(cls, value: str) -> str:
        cleaned = " ".join(value.strip().split())
        normalized = cls._normalize(cleaned)
        if normalized in {"aujourdhui", "aujourd hui", "today", "lyoum", "l youm"}:
            return datetime.now().strftime("%d/%m/%Y")

        cleaned = re.sub(r"\b(\d{1,2})\s*h\s*(\d{2})\b", r"\1h\2", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\b(?:a|\u00e0)\s+(\d{1,2}h(?:\d{2})?)\b", "\u00e0 " + r"\1", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\b(\d{1,2}/\d{1,2}/\d{4})\s+(\d{1,2}h(?:\d{2})?)\b", r"\1 " + "\u00e0" + r" \2", cleaned)
        cleaned = re.sub(r"\b(\d{1,2}\s+[a-zA-Z]+\s+\d{4})\s+(\d{1,2}h(?:\d{2})?)\b", r"\1 " + "\u00e0" + r" \2", cleaned)
        return cleaned

    @classmethod
    def _normalize_immediate_action(cls, value: str) -> str:
        normalized = cls._normalize(value)
        if any(marker in normalized for marker in {"faire attention", "lui faire attention", "les lui faire attention", "dire attention"}):
            return "Alerter la personne concernee, lui demander de s'eloigner du danger et informer le responsable HSE."
        if any(marker in normalized for marker in {"rien", "aucune", "pas encore", "walo"}):
            return "Aucune action realisee pour le moment; securiser et baliser la zone immediatement."
        return value.strip()

    @classmethod
    def _is_uncertain_answer(cls, value: str) -> bool:
        normalized = cls._normalize(value)
        uncertain_markers = {
            "je sais pas", "j sais pas", "je ne sais pas", "bah je sais pas",
            "aucune idee", "pas d idee", "maareft", "ma 3raft", "ma arft",
            "mabanch lia", "i do not know", "dont know", "no idea",
        }
        return any(marker in normalized for marker in uncertain_markers)

    @classmethod
    def _normalize_risk_analysis(cls, value: str) -> str:
        normalized = cls._normalize(value)
        if "gliss" in normalized or "huile" in normalized:
            return "Risque de glissade, chute de plain-pied, blessure et arret de production."
        if "elect" in normalized or "cable" in normalized:
            return "Risque d'electrocution, brulure, depart de feu ou arret de production."
        if "chute" in normalized or "hauteur" in normalized:
            return "Risque de chute, blessure grave ou accident mortel."
        return value.strip()

    @classmethod
    def _normalize_field_value(cls, field_name: str, value: str) -> str:
        if field_name == "declarant":
            employee = employee_directory.find_by_matricule(value) or employee_directory.find_by_name(value)
            if employee:
                return employee.get("display_name") or cls._normalize_declarant_name(value)
            return cls._normalize_declarant_name(value)
        if field_name == "event_datetime":
            return cls._normalize_event_datetime(value)
        if field_name == "location":
            return cls._normalize_location_zone(value)
        if field_name == "immediate_action":
            return cls._normalize_immediate_action(value)
        if field_name == "risk_analysis":
            return cls._normalize_risk_analysis(value)
        return value.strip()

    @staticmethod
    def _question(session: dict[str, Any], step: ConversationStep) -> str:
        language = session.get("language")
        if language == "darija":
            questions = QUESTIONS_DARIJA
        elif language == "en":
            questions = QUESTIONS_EN
        else:
            questions = QUESTIONS_FR
        return questions[step]

    @staticmethod
    def _intro(language: str) -> str:
        if language == "darija":
            return (
                "Salam, ana AMANE, l assistant vocal dyal HSE. "
                "Ila bghiti tsajli chi khatar oula anomalie, goul lia chnou oukaa."
            )

        if language == "en":
            return (
                "Hello, I am AMANE, your HSE voice assistant. "
                "Tell me what you want to report, and I will guide you."
            )

        return (
            "Bonjour, je suis AMANE, votre assistant vocal HSE. "
            "Dites-moi ce que vous voulez signaler, et je vous guiderai."
        )

    @staticmethod
    def _build_summary(data: dict[str, Any], language: str = "fr") -> str:
        newline = chr(10)
        if language == "darija":
            lines = [
                "Ù‡Ø§Ø¯Ø§ Ù‡Ùˆ Ù…Ù„Ø®Øµ Ø§Ù„ØªØµØ±ÙŠØ­:",
                "",
                f"- Classification : {data.get('classification', 'Ma t3amratch')}",
                f"- Description : {data.get('description', 'Ma t3amratch')}",
                f"- Date w l'heure : {data.get('event_datetime', 'Ma t3amratch')}",
                f"- Localisation : {data.get('location', 'Ma t3amratch')}",
                f"- Personne observee : {data.get('observed_person', 'Ma t3amratch')}",
                f"- DÃ©clarant : {data.get('declarant', 'Ma t3amratch')}",
                f"- Action immÃ©diate : {data.get('immediate_action', 'Ma t3amratch')}",
                f"- Analyse du risque : {data.get('risk_analysis', 'Ma t3amratch')}",
                "",
                "ÙˆØ§Ø´ Ù‡Ø§Ø¯ Ø§Ù„Ù…Ø¹Ù„ÙˆÙ…Ø§Øª ØµØ­ÙŠØ­Ø©ØŸ",
            ]
            return newline.join(lines)

        if language == "en":
            lines = [
                "Here is the summary of your HSE report:",
                "",
                f"- Classification: {data.get('classification', 'Not provided')}",
                f"- Description: {data.get('description', 'Not provided')}",
                f"- Date and time: {data.get('event_datetime', 'Not provided')}",
                f"- Location: {data.get('location', 'Not provided')}",
                f"- Observed person: {data.get('observed_person', 'Not provided')}",
                f"- Declarant: {data.get('declarant', 'Not provided')}",
                f"- Immediate action: {data.get('immediate_action', 'Not provided')}",
                f"- Risk analysis: {data.get('risk_analysis', 'Not provided')}",
                "",
                "Do you confirm that this information is correct?",
            ]
            return newline.join(lines)

        lines = [
            "Voici le rÃ©sumÃ© de votre remontÃ©e :",
            "",
            f"- Classification : {data.get('classification', 'Non renseignÃ©e')}",
            f"- Description : {data.get('description', 'Non renseignÃ©e')}",
            f"- Date et heure : {data.get('event_datetime', 'Non renseignÃ©es')}",
            f"- Localisation : {data.get('location', 'Non renseignÃ©e')}",
            f"- Personne observee : {data.get('observed_person', 'Non renseignÃ©e')}",
            f"- DÃ©clarant : {data.get('declarant', 'Non renseignÃ©')}",
            f"- Action immÃ©diate : {data.get('immediate_action', 'Non renseignÃ©e')}",
            f"- Analyse du risque : {data.get('risk_analysis', 'Non renseignÃ©e')}",
            "",
            "Ces informations sont-elles correctes ?",
        ]
        return newline.join(lines)
    @staticmethod
    def _response(
        step: ConversationStep,
        response: str,
        data: dict[str, Any],
        completed: bool = False,
        emergency: bool = False,
    ) -> dict[str, Any]:
        return {
            "step": step,
            "response": response,
            "completed": completed,
            "emergency": emergency,
            "data": data,
        }

    @staticmethod
    def _save_draft_report(session_id: str, session: dict[str, Any], db: Session) -> None:
        if db is None or session["data"].get("report_id"):
            return

        report_number = ReportService.generate_report_number(db)
        report_data = ReportCreate(
            report_number=report_number,
            classification=session["data"]["classification"],
            description=session["data"]["description"],
            event_datetime=session["data"]["event_datetime"],
            location=session["data"]["location"],
            observed_person=session["data"].get("observed_person"),
            declarant=session["data"]["declarant"],
            reclamant_name=session["data"].get("declarant"),
            immediate_action=session["data"]["immediate_action"],
            risk_analysis=session["data"]["risk_analysis"],
            immediate_danger=session["data"].get("immediate_danger", False),
            status="en_attente_confirmation",
            session_id=session_id,
            language=session.get("language"),
            source="voice_assistant_draft",
            raw_collected_data=dict(session["data"]),
        )
        report = ReportService.create(db=db, report_data=report_data)
        session["data"]["report_id"] = report.id
        session["data"]["report_number"] = report.report_number

    @staticmethod
    def _confirm_draft_report(session: dict[str, Any], db: Session):
        report_id = session["data"].get("report_id")
        if not report_id:
            return None

        report = ReportService.get_by_id(db, report_id)
        if report is None:
            return None

        report.status = "nouveau"
        report.source = "voice_assistant_confirmed"
        report.raw_collected_data = dict(session["data"])
        db.commit()
        db.refresh(report)
        return report
    @staticmethod
    def _norm_text(text: str) -> str:
        value = unicodedata.normalize("NFD", text or "")
        value = "".join(char for char in value if unicodedata.category(char) != "Mn")
        return value.lower().strip()

    @classmethod
    def _wants_hse_report(cls, message: str) -> bool:
        text = cls._norm_text(message)
        report_markers = {
            "declarer", "declaration", "signaler", "signalement", "remonter", "remontee",
            "reclamation", "rapport", "incident", "accident", "situation dangereuse",
            "acte dangereux", "danger immediat", "photo risque", "enregistrer",
            "bghit nsajel", "tsajel", "remontee hse",
        }
        return any(marker in text for marker in report_markers)

    @classmethod
    def _is_general_chat(cls, message: str) -> bool:
        text = cls._norm_text(message)
        if cls._wants_hse_report(message):
            return False
        general_markers = {
            "question", "explique", "expliquer", "c est quoi", "c'est quoi", "comment", "pourquoi",
            "formation", "entrainement", "entrainer", "test", "demo", "parle moi", "discuter",
            "aide moi", "aide", "regle", "consignation", "isolation", "epi", "balisage",
            "pont roulant", "laminoir", "zone", "sonasid", "hse", "salam", "bonjour", "hello",
            "chno", "wach", "3lach", "kifach", "bghit nfhem",
        }
        return any(marker in text for marker in general_markers)

    @classmethod
    def _looks_like_hse_report_detail(cls, message: str) -> bool:
        text = cls._norm_text(message)
        hazard_markers = {
            "danger", "risque", "incident", "accident", "anomalie", "fuite", "huile",
            "glissade", "cable", "cable denude", "convoyeur", "machine", "blessure",
            "chute", "feu", "incendie", "brulure", "electrique", "soudure", "maintenance",
            "sans casque", "sans epi", "charge suspendue", "pont roulant", "consignation",
            "khatar", "mouchkil", "mochkil", "wa9a3", "oukaa",
        }
        return any(marker in text for marker in hazard_markers)
    @staticmethod
    def _general_fallback(message: str, language: str) -> str:
        if language == "darija":
            return (
                "Ana AMANE. Nqder ndwi m3ak b tariqa 3adiya, njawb 3la ay soual, "
                "w n3awnek f HSE, règles SONASID, consignation, EPI, zones Nador, "
                "ou simulation. Ila bghiti tsajel remontee HSE, goul: je veux declarer une situation."
            )
        if language == "en":
            return (
                "I am AMANE. You can speak with me normally about general topics, training, "
                "HSE rules, SONASID, isolation/lockout, PPE, Nador zones, or simulations. "
                "To create a real report, say: I want to report an HSE situation."
            )
        return (
            "Je suis AMANE. Vous pouvez me parler normalement de sujets generaux, "
            "ou me poser des questions sur la formation, les regles SONASID, la consignation, "
            "les EPI, le balisage et les zones de Nador. Pour creer une vraie remontee, "
            "dites : je veux declarer une situation."
        )
    @classmethod
    def _general_chat_response(cls, message: str, language: str) -> str:
        fallback = cls._general_fallback(message, language)
        if not llm_service.available:
            return fallback

        try:
            context = rag_service.format_context(rag_service.retrieve(message, top_k=5))
            if language == "darija":
                lang_rule = "Reponds en darija marocaine simple, avec les termes techniques HSE en francais si necessaire."
            elif language == "en":
                lang_rule = "Answer in clear professional English."
            else:
                lang_rule = "Reponds en francais professionnel clair."

            response = llm_service.client.chat.completions.create(
                model=llm_service.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Tu es AMANE, assistant conversationnel general et formateur HSE pour SONASID Nador. "
                            "Tu peux discuter normalement, expliquer, entrainer, simuler et repondre aux questions generales ou HSE. "
                            "Ne cree pas de rapport tant que l'utilisateur ne demande pas explicitement de declarer/signaler une situation. "
                            "Pose au maximum une question courte si tu as besoin de precision. "
                            + lang_rule
                        ),
                    },
                    {
                        "role": "user",
                        "content": f"Contexte SONASID/RAG:\n{context}\n\nQuestion utilisateur:\n{message}",
                    },
                ],
                temperature=0.35,
            )
            text = (response.choices[0].message.content or "").strip()
            return text or fallback
        except Exception:
            return fallback

    def process_message(self, session_id: str, message: str, db: Session) -> dict[str, Any]:
        session = self._get_or_create_session(session_id)
        current_step = ConversationStep(session["step"])
        detected_language = self._detect_language(message)
        if self._should_keep_darija(session.get("language", "fr"), detected_language, message):
            detected_language = "darija"
        if detected_language in {"fr", "darija", "en"}:
            session["language"] = detected_language

        correction = self._extract_user_correction(message)
        if correction:
            wrong, right = correction
            self._save_user_correction(wrong, right)
            session.setdefault("corrections", {})[wrong] = right
            return self._response(
                step=current_step,
                response=self._correction_response(wrong, right, session["language"]),
                data=session["data"],
            )

        message = self._apply_corrections(message, session.get("corrections", self.user_corrections))

        if current_step == ConversationStep.START:
            if self._wants_hse_report(message) or self._looks_like_hse_report_detail(message):
                self._prefill_opening_statement(session, message)
                session["step"] = ConversationStep.EMERGENCY_CHECK
                return self._response(
                    step=ConversationStep.EMERGENCY_CHECK,
                    response=self._question(session, ConversationStep.EMERGENCY_CHECK),
                    data=session["data"],
                )

            session["step"] = ConversationStep.START
            return self._response(
                step=ConversationStep.START,
                response=self._general_chat_response(message, session["language"]),
                data=session["data"],
            )

        if current_step == ConversationStep.EMERGENCY_CHECK:
            if self._is_yes(message):
                session["data"]["immediate_danger"] = True
                next_step = self._next_unfilled_step(ConversationStep.CLASSIFICATION, session["data"])
                session["step"] = next_step
                if session["language"] == "darija":
                    response = (
                        "Hadchi kayban fih khatar. Afak ammen zone daba, "
                        "baad nass aala l khatar, ou ayet l responsable ou service HSE. "
                        "Mnin tkon situation sÃ©curisÃ©e, nkemlo. "
                        + self._question(session, next_step)
                    )
                elif session["language"] == "en":
                    response = (
                        "This situation appears to present a significant risk. "
                        "Secure the area immediately, protect exposed people, "
                        "and notify your supervisor and the HSE department. "
                        "Once the situation is secured, let us continue the report. "
                        + self._question(session, next_step)
                    )
                else:
                    response = (
                        "Cette situation semble prÃ©senter un risque important. "
                        "SÃ©curisez immÃ©diatement la zone, protÃ©gez les personnes exposÃ©es "
                        "et prÃ©venez votre responsable ainsi que le service HSE. "
                        "AprÃ¨s sÃ©curisation, continuons la dÃ©claration. "
                        + self._question(session, next_step)
                    )

                return self._response(
                    step=next_step,
                    response=response,
                    data=session["data"],
                    emergency=True,
                )

            if not self._is_no(message):
                if session["language"] == "darija":
                    response = "Ø¬Ø§ÙˆØ¨Ù†ÙŠ Ø¨ Ø¢Ù‡ ÙˆÙ„Ø§ Ù„Ø§. ÙˆØ§Ø´ ÙƒØ§ÙŠÙ† Ø®Ø·Ø± Ø¯Ø§Ø¨Ø§ØŸ"
                elif session["language"] == "en":
                    response = "Please answer yes or no. Is there an immediate danger?"
                else:
                    response = "Veuillez rÃ©pondre par oui ou non. La situation prÃ©sente-t-elle un danger immÃ©diat ?"
                return self._response(
                    step=ConversationStep.EMERGENCY_CHECK,
                    response=response,
                    data=session["data"],
                )

            session["data"]["immediate_danger"] = False
            next_step = self._next_unfilled_step(ConversationStep.CLASSIFICATION, session["data"])
            session["step"] = next_step
            return self._response(
                step=next_step,
                response=self._question(session, next_step),
                data=session["data"],
            )

        if current_step == ConversationStep.CONFIRMATION:
            if self._is_yes(message):
                try:
                    report = self._confirm_draft_report(session, db)
                    if report is None:
                        report_number = ReportService.generate_report_number(db)
                        report_data = ReportCreate(
                            report_number=report_number,
                            classification=session["data"]["classification"],
                            description=session["data"]["description"],
                            event_datetime=session["data"]["event_datetime"],
                            location=session["data"]["location"],
                            observed_person=session["data"].get("observed_person"),
                            declarant=session["data"]["declarant"],
                            reclamant_name=session["data"].get("declarant"),
                            immediate_action=session["data"]["immediate_action"],
                            risk_analysis=session["data"]["risk_analysis"],
                            immediate_danger=session["data"].get("immediate_danger", False),
                            status="nouveau",
                            session_id=session_id,
                            language=session.get("language"),
                            source="voice_assistant_confirmed",
                            raw_collected_data=dict(session["data"]),
                        )
                        report = ReportService.create(db=db, report_data=report_data)
                except Exception:
                    db.rollback()
                    raise

                session["step"] = ConversationStep.COMPLETED
                session["data"]["report_id"] = report.id
                session["data"]["report_number"] = report.report_number
                if session["language"] == "darija":
                    response = f"Safy, signalement tsajel b succÃ¨s sous numÃ©ro {report.report_number}."
                elif session["language"] == "en":
                    response = f"Your HSE report has been successfully saved under number {report.report_number}."
                else:
                    response = f"Votre remontÃ©e a Ã©tÃ© enregistrÃ©e avec succÃ¨s sous le numÃ©ro {report.report_number}."
                return self._response(
                    step=ConversationStep.COMPLETED,
                    response=response,
                    data=session["data"],
                    completed=True,
                )

            if self._is_no(message):
                next_step = ConversationStep.CLASSIFICATION
                session["step"] = next_step
                session["data"] = {}
                if session["language"] == "darija":
                    response = (
                        "Ma confirmitinach signalement. Ghadi n3awdo mn classification. "
                        + self._question(session, next_step)
                    )
                elif session["language"] == "en":
                    response = (
                        "The report was not confirmed. Let us restart from the classification. "
                        + self._question(session, next_step)
                    )
                else:
                    response = (
                        "La remontÃ©e n'a pas ete confirmÃ©e. Reprenons les informations. "
                        + self._question(session, next_step)
                    )
                return self._response(
                    step=next_step,
                    response=response,
                    data=session["data"],
                )

            if session["language"] == "darija":
                response = "Ø¬Ø§ÙˆØ¨Ù†ÙŠ Ø¨ Ø¢Ù‡ ÙˆÙ„Ø§ Ù„Ø§. ÙˆØ§Ø´ ÙƒØªØ£ÙƒØ¯ÙŠ Ù‡Ø§Ø¯ Ø§Ù„Ù…Ø¹Ù„ÙˆÙ…Ø§ØªØŸ"
            elif session["language"] == "en":
                response = "Please answer yes or no. Do you confirm the report information?"
            else:
                response = "Veuillez rÃ©pondre par oui ou non. Confirmez-vous les informations de la remontÃ©e ?"
            return self._response(
                step=ConversationStep.CONFIRMATION,
                response=response,
                data=session["data"],
            )

        if current_step == ConversationStep.COMPLETED:
            if session["language"] == "darija":
                response = "Ù‡Ø§Ø¯ Ø§Ù„ØªØµØ±ÙŠØ­ Ø³Ø§Ù„Ø§ Ù…Ù† Ù‚Ø¨Ù„."
            elif session["language"] == "en":
                response = "This HSE report is already completed."
            else:
                response = "Cette remontÃ©e est deja terminÃ©e."
            return self._response(
                step=ConversationStep.COMPLETED,
                response=response,
                data=session["data"],
                completed=True,
            )

        field_name = FIELD_BY_STEP.get(current_step)
        if field_name:
            value = message.strip()
            if field_name == "risk_analysis" and self._is_uncertain_answer(value):
                if session["language"] == "darija":
                    response = "Ma kayn mochkil. Goul lia chnou momkin youkaa: glissade, blessure, electrocution, chute, ou arret production?"
                elif session["language"] == "en":
                    response = "No problem. What could happen if the situation remains: slip, injury, electric shock, fall, or production stop?"
                else:
                    response = "Pas de souci. Quel risque possible voyez-vous : glissade, blessure, electrocution, chute ou arret de production ?"
                return self._response(
                    step=ConversationStep.RISK_ANALYSIS,
                    response=response,
                    data=session["data"],
                )

            if field_name == "classification":
                value = normalize_classification(value)
            else:
                if field_name == "declarant":
                    employee = employee_directory.find_by_matricule(value) or employee_directory.find_by_name(value)
                    if employee:
                        session["data"]["declarant_matricule"] = employee.get("matricule")
                value = self._normalize_field_value(field_name, value)
            session["data"][field_name] = value

        next_step = self._next_unfilled_step(NEXT_STEP[current_step], session["data"])
        session["step"] = next_step

        if next_step == ConversationStep.SUMMARY:
            self._save_draft_report(session_id, session, db)
            session["step"] = ConversationStep.CONFIRMATION
            return self._response(
                step=ConversationStep.CONFIRMATION,
                response=self._build_summary(session["data"], session["language"]),
                data=session["data"],
            )

        return self._response(
            step=next_step,
            response=self._question(session, next_step),
            data=session["data"],
        )


conversation_service = ConversationService()














































