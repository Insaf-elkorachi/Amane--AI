import re


class SpeechToTextAdapter:
    """Speech-to-text boundary for the AMANE voice architecture."""

    provider = "browser_web_speech_api"

    def accept_transcript(self, transcript: str) -> str:
        cleaned = transcript.strip()
        if not cleaned:
            raise ValueError("Transcript vocal vide")
        return self.fix_domain_terms(cleaned)

    @staticmethod
    def fix_assistant_name_vocative(text: str) -> str:
        corrected = text or ""
        corrected = re.sub(
            r"\b(bonjour|salut|salam|salem|hello|hey)\s+(?:ahmed|ahmad|amal|amel|amina|amine|amen|amene|aman)\b",
            r"\1 AMANE",
            corrected,
            flags=re.IGNORECASE,
        )
        corrected = re.sub(
            r"\b(ok|allo|hey)\s+(?:ahmed|ahmad|amal|amel|amina|amine|amen|amene|aman)\b",
            r"\1 AMANE",
            corrected,
            flags=re.IGNORECASE,
        )
        return corrected

    @staticmethod
    def fix_domain_terms(text: str) -> str:
        text = SpeechToTextAdapter.fix_assistant_name_vocative(text)
        replacements = [
            (r"\b(?:cite|citÃ©|site)\s+son\s*(?:acid|acide|asid|aside)\s+n(?:['â€™]|\s+)?adore\b", "Site SONASID Nador"),
            (r"\bsonasid\s+nador\b", "SONASID Nador"),
            (r"\bsite\s+sonasid\s+casablanca\b", "Site SONASID Nador"),
            (r"\bsonasid\s+casablanca\b", "SONASID Nador"),
            (r"\bsite\s+casablanca\b", "Site SONASID Nador"),
            (r"\bcasablanca\b", "Nador"),
            (r"\bamen\b", "AMANE"),
            (r"\bamene\b", "AMANE"),
            (r"\bamelle\b", "AMANE"),
            (r"\bamane\b", "AMANE"),
            (r"\baman\b", "AMANE"),
            (r"\bson\s*acid\b", "SONASID"),
            (r"\bson\s*acide\b", "SONASID"),
            (r"\bson\s*asid\b", "SONASID"),
            (r"\bson\s*aside\b", "SONASID"),
            (r"\bsonasid\b", "SONASID"),
            (r"\bsonaside\b", "SONASID"),
            (r"\bsona\s*sid\b", "SONASID"),
            (r"\bn(?:['â€™]|\s+)?adore\b", "Nador"),
            (r"\bnadore\b", "Nador"),
            (r"\bnador\b", "Nador"),
            (r"\bcite\b", "Site"),
            (r"\bcitÃ©\b", "Site"),
            (r"\bh\s*s\s*e\b", "HSE"),
            (r"\bachesse\b", "HSE"),
            (r"\bacierie\b", "aciÃ©rie"),
            (r"\baciÃ©rie\b", "aciÃ©rie"),
            (r"\blaminoire\b", "laminoir"),
            (r"\blaminoir\b", "laminoir"),
            (r"\bpont\s*bascule\b", "pont-bascule"),
            (r"\bloge\s+de\s+garde\b", "loge de garde"),
            (r"\bstation\s+service\b", "station service"),
            (r"\bparachevement\b", "parachevement"),
            (r"\bparach[eÃ©]vement\b", "parachevement"),
            (r"\bstockage\s+couronnes\b", "stockage couronnes"),
            (r"\bcoil\s+storage\b", "stockage couronnes"),
            (r"\bbatiment\s+du\s+laminoir\b", "batiment du laminoir"),
            (r"\bb[aÃ¢]timent\s+du\s+laminoir\b", "batiment du laminoir"),
            (r"\batelier\s+des\s+cylindres\b", "atelier des cylindres"),
            (r"\broll\s+shop\b", "atelier des cylindres"),
            (r"\bsalle\s+de\s+commande\s+electrique\b", "salle de commande electrique"),
            (r"\bsalle\s+de\s+commande\s+[eÃ©]lectrique\b", "salle de commande electrique"),
            (r"\belectrical\s+control\s+room\b", "salle de commande electrique"),
            (r"\btraitement\s+d['â€™]?eau\s+pour\s+laminoir\b", "traitement d'eau pour laminoir"),
            (r"\btraitement\s+d['â€™]?eau\s+brute\b", "traitement d'eau brute"),
            (r"\braw\s+water\s+treatment\b", "traitement d'eau brute"),
            (r"\bfuel\s+lourd\b", "fuel lourd"),
            (r"\boil\s+storage\b", "stockage du fuel lourd"),
            (r"\bparc\s+de\s+stockage\s+a\s+billettes\b", "parc de stockage a billettes"),
            (r"\bparc\s+de\s+stockage\s+[aÃ ]\s+billettes\b", "parc de stockage a billettes"),
            (r"\bbillet\s+stockyard\b", "parc de stockage a billettes"),
            (r"\bsous\s*station\s+principale\b", "sous-station principale"),
            (r"\bsub\s*station\b", "sous-station principale"),
            (r"\bmain\s+sub\s*station\b", "sous-station principale"),
            (r"\btrain\s+a\s+fil\b", "train a fil"),
            (r"\btrain\s+[aÃ ]\s+fil\b", "train a fil"),
            (r"\bfour\s+de\s+rechauffage\b", "four de rechauffage"),
            (r"\bfour\s+de\s+r[eÃ©]chauffage\b", "four de rechauffage"),
            (r"\breheat\s+furnace\b", "four de rechauffage"),
            (r"\bcisaille\s+pour\s+billettes\b", "cisaille pour billettes"),
            (r"\bbillet\s+shear\b", "cisaille pour billettes"),
            (r"\bcages?\s+degrossisseuses?\b", "cages degrossisseuses"),
            (r"\bcages?\s+d[eÃ©]grossisseuses?\b", "cages degrossisseuses"),
            (r"\broughing\s+stands?\b", "cages degrossisseuses"),
            (r"\bcisailles?\s+a\s+ebouter\b", "cisailles a ebouter"),
            (r"\bcisailles?\s+[aÃ ]\s+[eÃ©]bouter\b", "cisailles a ebouter"),
            (r"\bcrop\s+shears?\b", "cisailles a ebouter"),
            (r"\bcages?\s+intermediaires?\b", "cages intermediaires"),
            (r"\bcages?\s+interm[eÃ©]diaires?\b", "cages intermediaires"),
            (r"\bintermediate\s+stands?\b", "cages intermediaires"),
            (r"\bpupitre\b", "pupitre de commande principal du laminoir"),
            (r"\bmain\s+mill\s+control\s+pulpit\b", "pupitre de commande principal du laminoir"),
            (r"\bpresse\s+a\s+loups?\b", "presse a loups"),
            (r"\bpresse\s+[aÃ ]\s+loups?\b", "presse a loups"),
            (r"\bcobble\b", "presse a loups"),
            (r"\bno\s*twist\b", "trains finisseurs No Twist"),
            (r"\btrains?\s+finisseurs?\b", "trains finisseurs No Twist"),
            (r"\bboite\s+a\s+eau\b", "boite a eau"),
            (r"\bbo[iÃ®]te\s+[aÃ ]\s+eau\b", "boite a eau"),
            (r"\bwater\s+box\b", "boite a eau"),
            (r"\baiguille\s+pour\s+bobinoir\b", "aiguille pour bobinoir"),
            (r"\bbobinoirs?\b", "bobinoirs"),
            (r"\bpouring\s+reels?\b", "bobinoirs"),
            (r"\bforme?urs?\s+de\s+spires?\b", "formeurs de spires"),
            (r"\blaying\s+heads?\b", "formeurs de spires"),
            (r"\bstel\s*mor\b", "Stelmor"),
            (r"\bstelmore\b", "Stelmor"),
            (r"\bstelmor\b", "Stelmor"),
            (r"\bconvoyeurs?\s+stel\s*mor\b", "convoyeurs Stelmor"),
            (r"\bconvoyeurs?\s+stelmore\b", "convoyeurs Stelmor"),
            (r"\bforme?urs?\s+de\s+couronnes?\b", "formeurs de couronnes"),
            (r"\breform\s+tubs?\b", "formeurs de couronnes"),
            (r"\bc\s*hook\b", "C hook"),
            (r"\bcrochet\s+c\b", "C hook"),
            (r"\bchariot\s+collecteur\b", "chariot collecteur C hook"),
            (r"\bconvoyeurs?\s+de\s+couronnes?\b", "convoyeur de couronnes"),
            (r"\bcoil\s+handling\b", "convoyeur de couronnes"),
            (r"\bcompacteuses?\b", "compacteuses a couronnes"),
            (r"\bcompacteurs?\b", "compacteuses a couronnes"),
            (r"\bligatureuses?\b", "machines a ligaturer"),
            (r"\bmachines?\s+a\s+ligaturer\b", "machines a ligaturer"),
            (r"\bmachines?\s+[aÃ ]\s+ligaturer\b", "machines a ligaturer"),
            (r"\bcoil\s+compactors?\b", "compacteuses a couronnes"),
            (r"\bfour\s+electrique\b", "four Ã©lectrique"),
            (r"\bfour\s+Ã©lectrique\b", "four Ã©lectrique"),
            (r"\bcoulee\s+continue\b", "coulÃ©e continue"),
            (r"\bcoulÃ©e\s+continue\b", "coulÃ©e continue"),
            (r"\bpont\s+roulant\b", "pont roulant"),
            (r"\bposte\s+de\s+soudure\b", "poste de soudure"),
            (r"\bconvoyeur\b", "convoyeur"),
            (r"\bepi\b", "EPI"),
            (r"Ø£Ù…Ø§Ù†", "AMANE"),
            (r"Ø§Ù…ÙŠÙ†", "AMANE"),
            (r"Ø£Ù…ÙŠÙ†", "AMANE"),
            (r"Ø³ÙˆÙ†Ø§Ø³ÙŠØ¯", "SONASID"),
            (r"Ø³ÙˆÙ†\s*Ø£Ø³ÙŠØ¯", "SONASID"),
            (r"Ø³ÙˆÙ†\s*Ø§Ø³ÙŠØ¯", "SONASID"),
        ]

        corrected = text
        for pattern, value in replacements:
            corrected = re.sub(pattern, value, corrected, flags=re.IGNORECASE)

        return corrected


speech_to_text_adapter = SpeechToTextAdapter()


