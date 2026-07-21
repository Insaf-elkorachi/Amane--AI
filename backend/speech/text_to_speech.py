import re


class TextToSpeechAdapter:
    """Text-to-speech boundary for the AMANE voice architecture."""

    provider = "openai_tts_with_browser_fallback"

    @staticmethod
    def contains_arabic(text: str) -> bool:
        return bool(re.search(r"[\u0600-\u06ff]", text or ""))

    @staticmethod
    def is_darija(text: str) -> bool:
        return TextToSpeechAdapter.contains_arabic(text) or bool(
            re.search(
                r"\b(salam|salem|wach|wash|kayn|kayna|bghit|baghi|khatar|daba|dyal|dial|chno|chnou|fin|fayn|hadchi|afak|safi|wakha)\b",
                text or "",
                re.IGNORECASE,
            )
        )

    @staticmethod
    def arabic_to_french_phonetics(text: str) -> str:
        """Approximate Arabic text with French-readable phonetics for TTS engines."""
        if not text:
            return text

        phrase_replacements = {
            "\u0647\u0644 \u062a\u0624\u0643\u062f \u0623\u0646 \u0627\u0644\u0635\u0648\u0631\u0629 \u062a\u0645\u062b\u0644 \u0641\u0639\u0644\u0627 \u062e\u0637\u064a\u0631\u0627 \u0623\u0645 \u0648\u0636\u0639\u064a\u0629 \u062e\u0637\u064a\u0631\u0629\u061f": "Hal tou-ak-kid anna ssoura tou-mat-til fi-lan khatiran am wad-iya khatira ?",
            "\u062a\u062d\u0644\u064a\u0644 \u0635\u0648\u0631\u0629 HSE \u0628\u0648\u0627\u0633\u0637\u0629 AMANE": "Tahlil ssoura H S E bi wassitat Amane",
            "\u0627\u0644\u062a\u0635\u0646\u064a\u0641 \u0627\u0644\u0645\u0642\u062a\u0631\u062d": "Attasnif al mouk-tarah",
            "\u0645\u0633\u062a\u0648\u0649 \u0627\u0644\u062e\u0637\u0631 \u0627\u0644\u0639\u0627\u0645": "Moustawa al khatar al aam",
            "\u0645\u0644\u062e\u0635 \u0627\u0644\u0645\u0634\u0647\u062f": "Moulakhas al mach-had",
            "\u0627\u0644\u0645\u062e\u0627\u0637\u0631 \u0627\u0644\u0645\u0631\u0635\u0648\u062f\u0629": "Al makhatir al marsouda",
            "\u0627\u0644\u0645\u062e\u0627\u0637\u0631 \u0627\u0644\u0631\u0626\u064a\u0633\u064a\u0629": "Al makhatir ar-ra-issiya",
            "\u0625\u062c\u0631\u0627\u0621\u0627\u062a \u0627\u0644\u0648\u0642\u0627\u064a\u0629 \u0627\u0644\u0645\u0648\u0635\u0649 \u0628\u0647\u0627": "Ijra-at al wikaya al moussa biha",
            "\u062a\u0628\u0631\u064a\u0631 \u0645\u0633\u062a\u0648\u0649 \u0627\u0644\u062e\u0637\u0631 \u0627\u0644\u0639\u0627\u0645": "Tabrir moustawa al khatar al aam",
            "\u0633\u0624\u0627\u0644 AMANE": "Soual Amane",
            "\u064a\u062d\u062a\u0627\u062c \u0625\u0644\u0649 \u062a\u0623\u0643\u064a\u062f": "yahtaj ila ta-akid",
            "\u0645\u062a\u0648\u0633\u0637": "moutawassit",
            "\u0645\u0646\u062e\u0641\u0636": "mounkhafid",
            "\u0645\u0631\u062a\u0641\u0639": "mourtafaa",
            "\u062d\u0631\u062c": "haraj",
            "\u0641\u0639\u0644 \u062e\u0637\u064a\u0631": "fiil khatir",
            "\u0648\u0636\u0639\u064a\u0629 \u062e\u0637\u064a\u0631\u0629": "wad-iya khatira",
            "\u0627\u0644\u0639\u0648\u0627\u0642\u0628 \u0627\u0644\u0645\u062d\u062a\u0645\u0644\u0629": "al awakib al mouhtamala",
            "\u0627\u0644\u0645\u0633\u062a\u0648\u0649": "al moustawa",
        }
        cleaned = text
        for source, target in phrase_replacements.items():
            cleaned = cleaned.replace(source, target)

        cleaned = re.sub(r"[\u064b-\u065f\u0670]", "", cleaned)
        cleaned = cleaned.replace("\u0644\u0627", "la")
        table = {
            "\u0627": "a", "\u0623": "a", "\u0625": "i", "\u0622": "aa", "\u0621": "", "\u0624": "ou", "\u0626": "i",
            "\u0628": "b", "\u062a": "t", "\u062b": "s", "\u062c": "j", "\u062d": "h", "\u062e": "kh",
            "\u062f": "d", "\u0630": "z", "\u0631": "r", "\u0632": "z", "\u0633": "s", "\u0634": "ch",
            "\u0635": "s", "\u0636": "d", "\u0637": "t", "\u0638": "z", "\u0639": "aa", "\u063a": "gh",
            "\u0641": "f", "\u0642": "k", "\u0643": "k", "\u0644": "l", "\u0645": "m", "\u0646": "n",
            "\u0647": "h", "\u0629": "a", "\u0648": "ou", "\u064a": "i", "\u0649": "a",
            "\u060c": ",", "\u061b": ";", "\u061f": "?",
        }
        phonetic = "".join(table.get(char, char) for char in cleaned)
        phonetic = phonetic.replace("AMANE AI", "Amane")
        phonetic = phonetic.replace("AMANE", "Amane")
        phonetic = phonetic.replace("HSE", "H S E")
        phonetic = phonetic.replace("SONASID", "Sonasid")
        phonetic = phonetic.replace("3", "aa").replace("9", "k").replace("7", "h")
        return " ".join(phonetic.split())

    def prepare_speech_text(self, text: str) -> str:
        cleaned = (text or "").strip()
        if not cleaned:
            return cleaned

        if self.contains_arabic(cleaned):
            return self.arabic_to_french_phonetics(cleaned)

        replacements = {
            "AMANE AI": "Amane",
            "AMANE": "Amane",
            "HSE": "H S E",
            "SONASID": "Sonasid",
        }
        for source, target in replacements.items():
            cleaned = cleaned.replace(source, target)

        cleaned = re.sub(r"\b3lik\b", "aalik", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\b3la\b", "aala", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\bm3ak\b", "maak", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\b3afak\b", "afak", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\b3tini\b", "aatini", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\bw9a\b", "oukaa", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"9", "k", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"7", "h", cleaned, flags=re.IGNORECASE)
        return " ".join(cleaned.split())


text_to_speech_adapter = TextToSpeechAdapter()

