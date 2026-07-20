from typing import Any

from ai.llm import llm_service


class IntentAgent:
    def classify(self, message: str) -> dict[str, Any]:
        fallback = self._fallback(message)
        system_prompt = (
            "Tu es un agent de classification d'intention pour AMANE AI. "
            "Retourne uniquement un JSON valide avec: intent, language, confidence. "
            "intent doit etre: greeting, hse_report, answer, confirmation, other. "
            "language doit etre: fr, en, darija, ar, mixed."
        )
        user_prompt = f"Message utilisateur: {message}"
        return llm_service.generate_json(system_prompt, user_prompt, fallback)

    @staticmethod
    def _fallback(message: str) -> dict[str, Any]:
        normalized = message.lower().strip()
        arabic = any("\u0600" <= char <= "\u06ff" for char in message)
        language = "darija" if arabic else "fr"
        english_words = ["hello", "hi", "please", "report", "unsafe", "hazard", "incident", "risk", "yes", "no"]
        darija_words = [
            "salam", "salem", "bghit", "baghi", "wach", "wash", "kayn", "kayna",
            "khatar", "safi", "wakha", "daba", "dyal", "dial", "fin", "chno",
        ]
        french_words = [
            "bonjour", "je", "vous", "nous", "avec", "pour", "dans", "sur", "est",
            "veux", "voudrais", "signaler", "declarer", "d?clarer", "risque", "situation",
        ]
        tokens = set(normalized.split())
        if tokens.intersection(darija_words):
            language = "darija"
        elif sum(1 for word in tokens if word in french_words) >= 2:
            language = "fr"
        elif any(word in normalized for word in english_words):
            language = "en"

        report_words = ["danger", "risque", "anomalie", "incident", "fuite", "glissade", "unsafe", "hazard", "report", "oil", "leak", "slip", "خطر", "مشكل"]
        greeting_words = ["bonjour", "salut", "salam", "hello", "hi", "سلام"]
        yes_no = ["oui", "non", "yes", "no", "لا", "نعم", "wakha", "safi"]

        if any(word in normalized for word in report_words):
            intent = "hse_report"
        elif any(word in normalized for word in greeting_words):
            intent = "greeting"
        elif any(word in normalized for word in yes_no):
            intent = "confirmation"
        else:
            intent = "answer"

        return {"intent": intent, "language": language, "confidence": 0.72}


intent_agent = IntentAgent()

