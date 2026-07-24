import re


class TextToSpeechAdapter:
    """Text-to-speech boundary for the AMANE voice architecture."""

    provider = "openai_tts_with_browser_fallback"

    @staticmethod
    def contains_arabic(text: str) -> bool:
        return bool(re.search(r"[\u0600-\u06ff]", text or ""))

    @staticmethod
    def is_darija(text: str) -> bool:
        if TextToSpeechAdapter.contains_arabic(text):
            return False
        return bool(
            re.search(
                r"\b(salam|salem|wach|wash|kayn|kayna|bghit|baghi|khatar|daba|dyal|dial|chno|chnou|fin|fayn|hadchi|afak|safi|wakha)\b",
                text or "",
                re.IGNORECASE,
            )
        )

    @staticmethod
    def is_arabic_text(text: str) -> bool:
        return TextToSpeechAdapter.contains_arabic(text)

    @staticmethod
    def apply_brand_pronunciation(text: str, lang: str | None = None) -> str:
        value = text or ""
        requested_lang = (lang or "").lower()
        if requested_lang.startswith("ar") or (not requested_lang.startswith(("fr", "en")) and TextToSpeechAdapter.contains_arabic(value)):
            value = value.replace("AMANE AI", "\u0623\u0645\u0627\u0646")
            value = value.replace("AMANE", "\u0623\u0645\u0627\u0646")
            value = value.replace("HSE", "\u0625\u062a\u0634 \u0625\u0633 \u0625\u064a")
            value = value.replace("SONASID", "\u0633\u0648\u0646\u0627\u0633\u064a\u062f")
            return value
        value = value.replace("AMANE AI", "A-mane")
        value = value.replace("AMANE", "A-mane")
        value = re.sub(r"\bAmane\b", "A-mane", value)
        value = value.replace("HSE", "H S E")
        value = value.replace("SONASID", "Sonasid")
        return value

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


    @staticmethod
    def latin_darija_to_arabic_script(text: str) -> str:
        """Render common Latin Darija as Arabic script so TTS uses a Moroccan Arabic voice."""
        value = f" {text or ''} "
        value = re.sub(r"\b3", "a", value, flags=re.IGNORECASE)
        value = re.sub(r"\b9", "k", value, flags=re.IGNORECASE)
        value = re.sub(r"\b7", "h", value, flags=re.IGNORECASE)

        phrases = [
            ("Salam, ana AMANE", "\u0633\u0644\u0627\u0645\u060c \u0623\u0646\u0627 AMANE"),
            ("Ana AMANE", "\u0623\u0646\u0627 AMANE"),
            ("l assistant vocal dyal HSE", "\u0627\u0644\u0645\u0633\u0627\u0639\u062f \u0627\u0644\u0635\u0648\u062a\u064a \u062f\u064a\u0627\u0644 HSE"),
            ("Ila bghiti tsajli chi khatar oula anomalie", "\u0625\u0644\u0627 \u0628\u063a\u064a\u062a\u064a \u062a\u0633\u062c\u0644\u064a \u0634\u064a \u062e\u0637\u0631 \u0648\u0644\u0627 \u0623\u0646\u0648\u0645\u0627\u0644\u064a"),
            ("goul lia chnou oukaa", "\u0642\u0648\u0644 \u0644\u064a\u0627 \u0634\u0646\u0648 \u0648\u0642\u0639"),
            ("Afak chraah lia b tafsil chnou oukaa", "\u0639\u0627\u0641\u0627\u0643 \u0634\u0631\u062d \u0644\u064a\u0627 \u0628\u0627\u0644\u062a\u0641\u0635\u064a\u0644 \u0634\u0646\u0648 \u0648\u0642\u0639"),
            ("Wach kayne chi khatar daba", "\u0648\u0627\u0634 \u0643\u0627\u064a\u0646 \u0634\u064a \u062e\u0637\u0631 \u062f\u0627\u0628\u0627"),
            ("aalik oula aala nass li maak", "\u0639\u0644\u064a\u0643 \u0648\u0644\u0627 \u0639\u0644\u0649 \u0627\u0644\u0646\u0627\u0633 \u0644\u064a \u0645\u0639\u0627\u0643"),
            ("Wach hadchi fiil khatir oula wadiya khatira", "\u0648\u0627\u0634 \u0647\u0627\u062f\u0634\u064a \u0641\u0639\u0644 \u062e\u0637\u064a\u0631 \u0648\u0644\u0627 \u0648\u0636\u0639\u064a\u0629 \u062e\u0637\u064a\u0631\u0629"),
            ("Fach oukaa had lhadath", "\u0641\u0627\u0634 \u0648\u0642\u0639 \u0647\u0627\u062f \u0627\u0644\u062d\u0627\u062f\u062b"),
            ("Aatini tarikh ou l waqt", "\u0639\u0637\u064a\u0646\u064a \u0627\u0644\u062a\u0627\u0631\u064a\u062e \u0648\u0627\u0644\u0648\u0642\u062a"),
            ("Fin oukaa hadchi", "\u0641\u064a\u0646 \u0648\u0642\u0639 \u0647\u0627\u062f\u0634\u064a"),
            ("Aatini site, atelier, ou zone b dabt", "\u0639\u0637\u064a\u0646\u064a \u0627\u0644\u0645\u0648\u0642\u0639\u060c \u0627\u0644\u0623\u062a\u0644\u064a\u064a\u060c \u0623\u0648 \u0627\u0644\u0632\u0648\u0646 \u0628\u0627\u0644\u0636\u0628\u0637"),
            ("Chnou smitak", "\u0634\u0646\u0648 \u0633\u0645\u064a\u062a\u0643"),
            ("Chnou smitak oula matricule dyalek", "\u0634\u0646\u0648 \u0633\u0645\u064a\u062a\u0643 \u0648\u0644\u0627 \u0627\u0644\u0645\u0627\u062a\u0631\u064a\u0643\u0648\u0644 \u062f\u064a\u0627\u0644\u0643"),
            ("Chnou l action li derto daba bach tseddo l khatar", "\u0634\u0646\u0648 \u0627\u0644\u0625\u062c\u0631\u0627\u0621 \u0644\u064a \u062f\u0631\u062a\u0648 \u062f\u0627\u0628\u0627 \u0628\u0627\u0634 \u062a\u0633\u062f\u0648 \u0627\u0644\u062e\u0637\u0631"),
            ("Chnou l khatar li momkin youkaa mn baad ila bqat had l wadiya", "\u0634\u0646\u0648 \u0627\u0644\u062e\u0637\u0631 \u0644\u064a \u0645\u0645\u0643\u0646 \u064a\u0648\u0642\u0639 \u0645\u0646 \u0628\u0639\u062f \u0625\u0644\u0627 \u0628\u0642\u0627\u062a \u0647\u0627\u062f \u0627\u0644\u0648\u0636\u0639\u064a\u0629"),
            ("Jawbni b ah oula la", "\u062c\u0627\u0648\u0628\u0646\u064a \u0628 \u0622\u0647 \u0648\u0644\u0627 \u0644\u0627"),
            ("Ma kayn mochkil", "\u0645\u0627 \u0643\u0627\u064a\u0646 \u0645\u0634\u0643\u0644"),
            ("Hadchi kayban fih khatar", "\u0647\u0627\u062f\u0634\u064a \u0643\u0627\u064a\u0628\u0627\u0646 \u0641\u064a\u0647 \u062e\u0637\u0631"),
            ("Afak ammen zone daba", "\u0639\u0627\u0641\u0627\u0643 \u0623\u0645\u0646 \u0627\u0644\u0632\u0648\u0646 \u062f\u0627\u0628\u0627"),
            ("ayet l responsable ou service HSE", "\u0639\u064a\u0637 \u0644\u0644\u0645\u0633\u0624\u0648\u0644 \u0623\u0648 \u0633\u064a\u0631\u0641\u064a\u0633 HSE"),
            ("Mnin tkon situation securisee, nkemlo", "\u0645\u0646\u064a\u0646 \u062a\u0643\u0648\u0646 \u0627\u0644\u0648\u0636\u0639\u064a\u0629 \u0645\u0624\u0645\u0646\u0629\u060c \u0646\u0643\u0645\u0644\u0648"),
        ]
        for source, target in phrases:
            value = re.sub(re.escape(source), target, value, flags=re.IGNORECASE)

        words = {
            "salam": "\u0633\u0644\u0627\u0645", "ana": "\u0623\u0646\u0627", "afak": "\u0639\u0627\u0641\u0627\u0643", "aafak": "\u0639\u0627\u0641\u0627\u0643",
            "wach": "\u0648\u0627\u0634", "wash": "\u0648\u0627\u0634", "kayne": "\u0643\u0627\u064a\u0646", "kayn": "\u0643\u0627\u064a\u0646", "kayna": "\u0643\u0627\u064a\u0646\u0629",
            "chi": "\u0634\u064a", "khatar": "\u062e\u0637\u0631", "daba": "\u062f\u0627\u0628\u0627", "dyal": "\u062f\u064a\u0627\u0644", "dial": "\u062f\u064a\u0627\u0644",
            "chnou": "\u0634\u0646\u0648", "chno": "\u0634\u0646\u0648", "fin": "\u0641\u064a\u0646", "fayn": "\u0641\u064a\u0646", "oukaa": "\u0648\u0642\u0639", "youkaa": "\u064a\u0648\u0642\u0639",
            "hadchi": "\u0647\u0627\u062f\u0634\u064a", "had": "\u0647\u0627\u062f", "lhadath": "\u0627\u0644\u062d\u0627\u062f\u062b", "site": "\u0627\u0644\u0645\u0648\u0642\u0639",
            "atelier": "\u0627\u0644\u0623\u062a\u0644\u064a\u064a", "zone": "\u0627\u0644\u0632\u0648\u0646", "smitak": "\u0633\u0645\u064a\u062a\u0643", "matricule": "\u0627\u0644\u0645\u0627\u062a\u0631\u064a\u0643\u0648\u0644",
            "dyalek": "\u062f\u064a\u0627\u0644\u0643", "action": "\u0627\u0644\u0625\u062c\u0631\u0627\u0621", "derto": "\u062f\u0631\u062a\u0648", "bach": "\u0628\u0627\u0634", "tseddo": "\u062a\u0633\u062f\u0648",
            "momkin": "\u0645\u0645\u0643\u0646", "baad": "\u0628\u0639\u062f", "ila": "\u0625\u0644\u0627", "bqat": "\u0628\u0642\u0627\u062a", "wadiya": "\u0648\u0636\u0639\u064a\u0629",
            "khatira": "\u062e\u0637\u064a\u0631\u0629", "fiil": "\u0641\u0639\u0644", "ah": "\u0622\u0647", "la": "\u0644\u0627", "oula": "\u0648\u0644\u0627", "nass": "\u0627\u0644\u0646\u0627\u0633",
            "maak": "\u0645\u0639\u0627\u0643", "hse": "HSE", "sonasid": "SONASID", "nador": "Nador", "amane": "AMANE",
        }
        for source, target in sorted(words.items(), key=lambda item: len(item[0]), reverse=True):
            value = re.sub(rf"\b{re.escape(source)}\b", target, value, flags=re.IGNORECASE)
        value = re.sub(r"\s+", " ", value).strip()
        return TextToSpeechAdapter.apply_brand_pronunciation(value, "ar-MA")

    def prepare_speech_text(self, text: str, lang: str | None = None) -> str:
        cleaned = (text or "").strip()
        if not cleaned:
            return cleaned

        if self.is_darija(cleaned):
            return self.latin_darija_to_arabic_script(cleaned)

        cleaned = self.apply_brand_pronunciation(cleaned, lang)

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

