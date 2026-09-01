import base64
import json
import re
import unicodedata
from io import BytesIO
from pathlib import Path
from typing import Any

from ai.llm import llm_service
from ai.rag import rag_service
from core.config import settings


class VisionRiskAgent:
    """Analyze HSE risk photos and classify unsafe acts/conditions."""


    @staticmethod
    def _encode_image_for_llm(image_path: Path) -> str:
        try:
            from PIL import Image

            with Image.open(image_path) as image:
                image = image.convert("RGB")
                image.thumbnail((768, 768))
                buffer = BytesIO()
                image.save(buffer, format="JPEG", quality=82, optimize=True)
                return base64.b64encode(buffer.getvalue()).decode("ascii")
        except Exception:
            return base64.b64encode(image_path.read_bytes()).decode("ascii")

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
        fallback = self._fallback(image_path, language)
        if not llm_service.available:
            return self._normalize_result(fallback)

        mime = "image/jpeg"
        encoded = self._encode_image_for_llm(image_path)
        context = rag_service.format_context(
            rag_service.retrieve(
                "analyse photo HSE chantier excavation engins charge suspendue EPI balisage circulation pietons consignation SONASID Nador",
                top_k=4,
            )
        )
        system_prompt = (
            "Tu es AMANE, un assistant HSE industriel specialise dans l analyse de photographies provenant d une usine siderurgique SONASID. "
            "Ton role est celui d un inspecteur HSE experimente. "
            + self._language_instruction(language)
            + "Analyse UNIQUEMENT les elements visibles sur la photographie. Ne jamais inventer un risque. Applique toujours la logique inspection HSE en cinq etapes: Observer les faits visibles, Deduire les risques uniquement depuis ces faits, Qualifier le niveau de gravite, Prevenir avec des mesures operationnelles, Verifier avec une question ciblee. "
            "Distingue systematiquement quatre statuts: Danger confirme si l anomalie est clairement visible; Danger potentiel si le danger depend du contexte; Point a verifier si la conformite ne peut pas etre determinee par l image seule; Situation conforme apparente si l element visible ne presente pas d anomalie evidente. Ne transforme jamais une hypothese en fait. Si une information n est pas visible, ecris: Impossible a confirmer a partir de l image seule. "
            "Ne jamais supposer qu un EPI est absent. Ne jamais supposer qu un harnais, un blindage, une consignation ou un dispositif de securite est absent s il n est pas clairement visible. "
            "Rigueur redactionnelle supplementaire: separe toujours observation, interpretation et incertitude. Les observations decrivent uniquement ce qui est visible, sans consequence ni jugement. Les risques sont formules comme des consequences possibles. Les causes et mesures tiennent compte des incertitudes lorsque la photo ne permet pas de conclure avec certitude. Ne commente pas les EPI lorsqu aucun operateur, intervenant ou partie du corps n est visible. Ne conclus pas qu un element saillant, une piece depassante ou une arete constitue un defaut sans contexte d exposition, de circulation, de contact possible ou de non-conformite visible. Lorsque la photo ne permet pas de conclure avec certitude, privilegie des formulations conditionnelles comme pourrait, semble, parait, a confirmer, lorsque cela est necessaire. "
            "Lorsque l image ne permet pas de conclure, ecris clairement: Non confirmable sur cette photographie, ou Aucun element visible ne permet de confirmer. Ajoute une liste observations contenant uniquement des constats factuels visibles, sans interpretation de risque. Chaque risque dans risk_items doit pouvoir etre relie a au moins une observation visible. Pour chaque observation, fais mentalement le tri OUI/NON/INCERTAIN: OUI si un accident plausible est visible ou decoule directement du fait visible; NON si l element visible est neutre ou semble maitrise; INCERTAIN si la photo ne permet pas de conclure. Si la reponse est INCERTAIN mais qu un accident plausible est directement lie a un fait visible, cree un risque potentiel avec pourrait, peut ou susceptible de. Si la reponse est NON, ne cree pas de risque. Il vaut mieux un seul risque potentiel bien justifie que plusieurs risques inventes. "
            "Regle absolue objet versus risque: un objet visible n est pas automatiquement un risque. Le danger doit etre cree par une condition visible: boucle au sol, traversee de passage, proximite dangereuse, personne exposee, mouvement, fuite, charge suspendue, encombrement ou autre exposition claire. Le nom du risque doit commencer par Risque, Risk ou le mot arabe خطر selon la langue. Ne jamais utiliser seulement le nom de l objet comme nom de risque. Toujours privilegier les faits observables. Ne transforme jamais une hypothese en fait. Distinction critique: la presence visible d une machine protegee, d une voie de circulation, d un equipement ou d une zone de travail ne constitue pas un risque si aucun accident plausible n est lie a un fait visible. Les risques potentiels justifies par un fait visible doivent rester dans risk_items avec une formulation prudente. Les risques purement theoriques, hors champ ou non confirmables doivent aller dans scene_summary, global_risk_reason ou questions, mais pas comme risques observes. "
            "Controle mentalement ces categories, mais ne cree un risque que si un danger est directement visible: "
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
            "Indice de confiance: 0.95 a 1.0 si tous les elements sont clairement visibles, 0.80 a 0.94 si quelques elements ne sont pas visibles, 0.60 a 0.79 si la photo est partiellement exploitable, moins de 0.60 si la photo est insuffisante. Ne retourne jamais 0 sauf si l image est inutilisable. Exemples de regles SST SONASID a associer seulement aux risques observes: N1 EPI, N2 Balisage, N3 Charge suspendue, N7 Conduite et engins, N8 Travaux en hauteur, N11 Elingage, N13 Manutention manuelle, N19 Circulation des engins, N20 Chargement/dechargement, N23 5S Site propre. Ne jamais utiliser N3 Charge suspendue si aucune charge suspendue, crochet, elingue, pont roulant en levage ou personne sous charge n est visible. Pour les couronnes ou bobines posees au sol, ne pas ecrire chute de couronnes ni stabilite insuffisante comme certitude; preferer Stockage des couronnes au sol, Risque de deplacement ou de roulement lors de la manutention, et Aucun dispositif de calage ou de maintien n est clairement visible sur la partie photographiee. Associer plutot N23 5S et/ou N13 Manutention si ces risques sont visibles. A la fin, les listes main_risks et prevention_measures doivent prioriser au maximum les 2 risques visibles les plus critiques et les mesures associees; si un seul risque est visible, retourne un seul risque. Pose UNE seule question pertinente permettant de lever une incertitude importante. Ne jamais poser une question dont la reponse est deja visible sur l image. Les mesures de prevention doivent etre specifiques, actionnables sur terrain, et adaptees au danger visible. Les regles related_sst_rules doivent etre choisies uniquement si elles correspondent directement a un risque observe; ne pas citer de regle SST pour une categorie seulement theorique. "
            "Objectivite et priorisation: privilegie la precision plutot que l exhaustivite. Ne cherche jamais un nombre minimum de risques. Il vaut mieux un seul risque potentiel bien justifie que plusieurs risques hypothetiques. Avant d ajouter un risque, verifier: fait visible, accident plausible, observation et non supposition, autre interpretation possible. Si une reponse est non, ne pas ajouter ce risque. Si une reponse est incertaine mais plausible a partir d un fait visible, ajouter un risque potentiel prudent. Limiter strictement les risques: 1 risque si un seul est clairement identifie; 2 risques seulement si les deux sont totalement independants et visibles. Ne cree jamais un troisieme risque sans preuve visuelle exceptionnelle; en pratique, privilegie 1 ou 2 risques. Ne cree jamais un risque supplementaire pour un marquage au sol, une machine ou un objet seul. "
            "Bloc obligatoire anti faux negatifs: avant de conclure 0 danger potentiel, pour chaque objet ou situation visible, demande silencieusement: dans quel scenario raisonnable cet element pourrait-il provoquer un accident ou gener une mesure de securite? Un cable ou une bobine au sol peut creer un risque de trebuchement, obstacle ou encombrement potentiel. Un objet pres d une porte peut gener un passage. Un objet devant un equipement electrique peut gener l acces ou l intervention. Un liquide au sol peut provoquer une glissade. Un materiau saillant peut provoquer coupure ou accrochage. Il est interdit de passer directement de contexte incomplet a aucun danger. Si une condition est necessaire, classe le risque comme Potentiel et explique: ce risque devient pertinent si... "
            "Regle pour les objets au sol: tout objet inhabituel pose au sol doit etre analyse. Si l objet est clairement dans une voie, c est un danger confirme d encombrement ou trebuchement. Si l objet est pres d une porte, d un acces ou d une zone pouvant servir au passage, c est un danger potentiel. Si l utilisation de la zone n est pas connue, produire danger potentiel plus une question contextuelle sur le passage des travailleurs. Evite les contradictions: ne jamais ecrire sol libre de tout obstacle si une bobine, un cable ou un objet est visible au sol. Ecris plutot: la zone semble globalement propre, mais un objet est present au sol. "
            "Qualite de l analyse: le resume doit decrire precisement la scene avec les principaux elements visibles; ne jamais utiliser une phrase generique comme la photo montre une partie d une zone industrielle. Les consequences doivent etre directement liees au danger observe et deduites de l image. Pour une boucle de cable au sol, consequence autorisee: trebuchement possible ou deterioration du cable si expose au passage; consequence interdite: choc electrique ou contact electrique sauf si conducteur endommage, fil nu, coffret ouvert ou element sous tension visible. Les regles SST doivent correspondre exactement au danger identifie, jamais au simple contexte industriel. L indice de confiance doit etre coherent: 0.95 danger clairement visible, 0.85 danger visible avec quelques incertitudes, 0.70 photo partielle, 0.50 preuves insuffisantes. Ne jamais choisir une valeur aleatoire. "
            "Mentionne aussi les elements positifs clairement visibles dans observations ou scene_summary, par exemple zone propre, cable protege, signalisation presente ou passage degage; leur presence ne prouve jamais une conformite reglementaire complete. "
            "Avant de repondre, effectue une double verification: 1 verifier que chaque risque est reellement visible; 2 verifier qu aucun risque majeur visible n a ete oublie; 3 verifier que le resume decrit la scene concrete; 4 verifier que chaque consequence et chaque regle SST sont directement justifiees. "
            "Retourne uniquement un JSON valide avec exactement ces cles: classification, confidence, observations, scene_summary, risk_items, main_risks, prevention_measures, global_risk_level, global_risk_reason, immediate_danger, recommended_action, questions, location_hints, related_sst_rules. "
            "observations doit etre une liste de constats visibles neutres, sans mots comme absence, manque, risque, danger, accident, chute, blessure, non-conformite ou mesure. risk_items doit etre une liste d objets avec: risk, status, observation, location, condition, hazardous_event, cause, description, possible_consequences, exposed_persons, severity, probability, risk_level, confidence, immediate_measure, prevention_measure, sst_rule. status doit etre exactement Confirme, Potentiel ou A verifier. probability doit etre LOW, MEDIUM ou HIGH; si l exposition n est pas connue, ecris MEDIUM et explique dans condition que la probabilite est a confirmer selon l exposition. risk_level doit etre LOW, MEDIUM, HIGH ou CRITICAL. Dans risk_items, observation doit rester factuelle et visible; risk, hazardous_event et possible_consequences doivent porter l interpretation et les consequences possibles; cause doit rester prudente; prevention_measure doit utiliser si necessaire, verifier, confirmer ou mettre en place lorsque cela est applicable si l image est incertaine. risk_items doit contenir seulement les dangers directement observes ou les risques potentiels plausibles justifies par un fait visible, jamais des risques purement theoriques ni des elements conformes/proteges. observation et description doivent citer le fait visible qui soutient l analyse. severity doit etre LOW, MEDIUM, HIGH ou CRITICAL. sst_rule doit citer uniquement la regle SST SONASID directement liee au risque observe; si aucune regle precise n est disponible, ecris Regle SONASID a confirmer selon le referentiel HSE interne. "
            "main_risks, prevention_measures, questions, location_hints et related_sst_rules doivent etre des listes de textes dans la langue demandee. questions doit contenir une seule question. "
            "Interdiction de remplir les listes avec des phrases vagues ou repetees. Chaque risque doit etre specifique et base sur un indice visuel."
        )
        user_text = (
            "Contexte RAG SONASID et regles SST disponibles:\n"
            f"{context}\n\n"
            "Analyse cette photo HSE selon la methode AMANE stricte: uniquement les faits visibles, aucune hypothese transformee en fait, chaque risque doit etre observable. Commence par identifier la scene concrete: personnes visibles ou non, type de lieu, objets principaux, activite visible, texte/affiche/document si la photo montre surtout un document. Si la photo montre une affiche, une politique, un document, un ecran ou un panneau sans situation de travail exposee, dis-le clairement et ne fabrique pas un risque terrain. Ne confonds pas un risque theorique avec un risque observe: une machine visible, une voie de circulation visible ou un equipement protege ne suffit pas. Il faut un danger direct clairement perceptible pour remplir Risques observes. Commence par produire observations: une liste de faits visibles neutres, puis deduis les risques observes a partir de ces observations. "
            "Balaye toutes les categories: EPI, hauteur, levage, circulation, machines, electricite, incendie, manutention, sol/environnement, produits. "
            "Si une categorie ne peut pas etre conclue, utilise une formule non confirmable. Le contenu lisible par l utilisateur doit respecter la langue demandee. "
            "Ne parle des EPI que si une personne est visible. Pour les elements saillants, reste factuel et conditionnel sauf danger direct visible. Separe strictement: observation visible, risque possible, cause prudente, mesure conditionnelle. "
            "Retourne une analyse courte, precise, non repetitive, avec une seule question finale utile. Ne retiens que les risques significatifs et parfaitement justifies. "
        )

        if getattr(llm_service, "provider", "openai") == "ollama":
            if language == "fr":
                language_rule = "Write all user text in French."
            elif language == "en":
                language_rule = "Write all user text in English."
            else:
                language_rule = "Write all user text only in clear Modern Standard Arabic. Do not output English or French sentences. Use Arabic words for AMANE and HSE in user-facing text: أمان and السلامة."
            system_prompt = (
                "You are AMANE, an industrial HSE photo inspector for SONASID. "
                + language_rule
                + " Use only what is directly visible in the image. Do not invent risks. "
                "If no real workplace danger is visible, say no significant visible risk. "
                "Do not claim missing PPE or missing safety devices unless clearly visible. "
                "Return JSON only with: classification, confidence, observations, scene_summary, risk_items, main_risks, prevention_measures, global_risk_level, global_risk_reason, immediate_danger, recommended_action, questions, location_hints, related_sst_rules. "
                "classification must be Acte dangereux, Situation dangereuse, Acte dangereux et situation dangereuse, or A confirmer. "
                "global_risk_level must be LOW, MEDIUM, HIGH, or CRITICAL. confidence must be 0 to 1. "
                "risk_items must be a list of objects with risk, status, observation, location, condition, hazardous_event, cause, description, possible_consequences, exposed_persons, severity, probability, risk_level, confidence, immediate_measure, prevention_measure, sst_rule. "
                "Never confuse object and risk: an object alone is not a risk. A risk requires a visible dangerous condition or exposure. The risk name must start with Risk in English, Risque in French, or خطر in Arabic. Limit to maximum 2 visible risks. If only one risk is visible, return only one. Never create a third risk. Ask one question."
                " Anti false negatives rule: before returning zero potential risks, check every visible object for a reasonable accident scenario. A cable, coil, spool, or unusual object on the floor near a door, access, walkway, machine, or electrical equipment must be at least a potential risk. If context is missing, classify it as Potentiel and ask whether the area is used by workers."
            )
            if language == "ar":
                user_text = (
                    "حلل صورة السلامة هذه باللغة العربية الفصحى فقط. ابدأ بوصف الوقائع المرئية، ثم استخرج فقط المخاطر المرئية فعلا. "
                    "لا تخلط الإنجليزية أو الفرنسية في النص الموجه للمستخدم. "
                    "استعمل قواعد السلامة الخاصة بسوناسيد فقط عندما تكون مرتبطة مباشرة بخطر مرئي: N1 معدات الوقاية، N2 العزل والحواجز، N3 الحمل المعلق، N7 السياقة والآليات، N8 العمل في الارتفاع، N9 العزل الطاقي، N13 المناولة اليدوية، N19 حركة الآليات، N23 النظام والنظافة. "
                    "لا تستعمل N3 إذا لم يظهر حمل معلق في الصورة."
                )
            else:
                user_text = (
                    "Analyze this HSE image. First describe visible facts. Then identify only real visible risks. "
                    "Use SONASID SST rules only when relevant: N1 PPE, N2 Balisage, N3 Suspended load, N7 Engines, N8 Height work, N9 Isolation, N13 Manual handling, N19 Traffic, N23 5S. "
                    "Never use N3 if no suspended load is visible."
                )

        result = llm_service.generate_vision_json(
            system_prompt=system_prompt,
            user_prompt=user_text,
            image_base64=encoded,
            fallback=fallback,
            temperature=0.05,
        )
        if result.get("vision_error"):
            vision_error = str(result.get("vision_error") or "")
            is_openai_provider = (settings.LLM_PROVIDER or "").lower().strip() == "openai"
            if is_openai_provider and ("insufficient_quota" in vision_error or "exceeded your current quota" in vision_error.lower()):
                quota_messages = {
                    "fr": {
                        "summary": "La photo a ete recue, mais l'analyse visuelle ne peut pas demarrer car le quota OpenAI est insuffisant.",
                        "reason": "Quota API insuffisant; aucune analyse HSE automatique ne peut etre confirmee depuis cette photo.",
                        "action": "Rechargez le compte API ou activez la facturation, puis renvoyez la photo.",
                        "question": "Le quota API est-il recharge pour relancer l'analyse photo ?",
                    },
                    "en": {
                        "summary": "The photo was received, but visual analysis cannot start because the OpenAI quota is insufficient.",
                        "reason": "Insufficient API quota; no automatic HSE analysis can be confirmed from this photo.",
                        "action": "Add API credit or enable billing, then upload the photo again.",
                        "question": "Is the API quota available so the photo analysis can be retried?",
                    },
                    "ar": {
                        "summary": "\u062a\u0645 \u0627\u0633\u062a\u0644\u0627\u0645 \u0627\u0644\u0635\u0648\u0631\u0629\u060c \u0644\u0643\u0646 \u062a\u062d\u0644\u064a\u0644\u0647\u0627 \u063a\u064a\u0631 \u0645\u0645\u0643\u0646 \u062d\u0627\u0644\u064a\u0627 \u0644\u0623\u0646 \u0631\u0635\u064a\u062f \u062e\u062f\u0645\u0629 \u0627\u0644\u0630\u0643\u0627\u0621 \u0627\u0644\u0627\u0635\u0637\u0646\u0627\u0639\u064a \u063a\u064a\u0631 \u0643\u0627\u0641.",
                        "reason": "\u0627\u0644\u0631\u0635\u064a\u062f \u063a\u064a\u0631 \u0643\u0627\u0641\u061b \u0644\u0630\u0644\u0643 \u0644\u0627 \u064a\u0645\u0643\u0646 \u062a\u0623\u0643\u064a\u062f \u0623\u064a \u062a\u062d\u0644\u064a\u0644 \u0633\u0644\u0627\u0645\u0629 \u062a\u0644\u0642\u0627\u0626\u064a \u0645\u0646 \u0647\u0630\u0647 \u0627\u0644\u0635\u0648\u0631\u0629.",
                        "action": "\u0623\u0636\u0641 \u0631\u0635\u064a\u062f\u0627 \u0623\u0648 \u0641\u0639\u0651\u0644 \u0627\u0644\u0641\u0648\u062a\u0631\u0629\u060c \u062b\u0645 \u0623\u0639\u062f \u0625\u0631\u0633\u0627\u0644 \u0627\u0644\u0635\u0648\u0631\u0629.",
                        "question": "\u0647\u0644 \u062a\u0645 \u062a\u0648\u0641\u064a\u0631 \u0627\u0644\u0631\u0635\u064a\u062f \u0627\u0644\u0644\u0627\u0632\u0645 \u0644\u0625\u0639\u0627\u062f\u0629 \u062a\u062d\u0644\u064a\u0644 \u0627\u0644\u0635\u0648\u0631\u0629\u061f",
                    },
                }
                labels = quota_messages.get(language, quota_messages["ar"])
                fallback.update(
                    scene_summary=labels["summary"],
                    global_risk_reason=labels["reason"],
                    recommended_action=labels["action"],
                    prevention_measures=[labels["action"]],
                    questions=[labels["question"]],
                )
                result = {**fallback, "vision_error": vision_error}
            return self._normalize_result(result)

        result = {**fallback, **result}
        result["analysis_available"] = True
        result["source_image"] = str(image_path)
        return self._ensure_result_language(self._normalize_result(result), language)

    @staticmethod
    def _fallback(image_path: Path, language: str = "ar") -> dict[str, Any]:
        texts = {
            "fr": {
                "summary": "La photo a ete recue, mais l'analyse visuelle automatique n'est pas disponible pour le moment. Aucune conclusion HSE ne doit etre tiree de cette image sans nouvelle analyse.",
                "reason": "Le modele vision n'a pas retourne d'analyse exploitable; aucun risque ne peut etre confirme a partir de ce fallback.",
                "action": "Verifiez la cle OpenAI, le modele vision et la connexion, puis renvoyez la photo.",
                "question": "Pouvez-vous renvoyer la photo ou verifier que le modele vision est disponible ?",
            },
            "en": {
                "summary": "The photo was received, but automatic visual analysis is currently unavailable. No HSE conclusion should be drawn from this image without a new analysis.",
                "reason": "The vision model did not return usable analysis; no risk can be confirmed from this fallback.",
                "action": "Check the OpenAI key, vision model, and connection, then upload the photo again.",
                "question": "Can you upload the photo again or check that the vision model is available?",
            },
            "ar": {
                "summary": "تم استلام الصورة، لكن التحليل البصري الآلي غير متاح حاليا. لا يجب استخلاص أي قرار متعلق بالسلامة من هذه الصورة بدون تحليل جديد.",
                "reason": "نموذج الرؤية لم يرجع تحليلا قابلا للاستعمال؛ لذلك لا يمكن تأكيد أي خطر من هذا الرد الاحتياطي.",
                "action": "تحقق من مفتاح خدمة الذكاء الاصطناعي ونموذج الرؤية والاتصال، ثم أعد إرسال الصورة.",
                "question": "هل يمكنك إعادة إرسال الصورة أو التأكد من توفر نموذج الرؤية؟",
            },
        }
        if (settings.LLM_PROVIDER or "").lower().strip() == "ollama":
            ollama_messages = {
                "fr": {
                    "summary": "La photo a ete recue, mais l'analyse locale Llama/Ollama n'est pas disponible pour le moment.",
                    "reason": "Ollama ou le modele vision local ne repond pas; aucun risque ne peut etre confirme depuis ce fallback.",
                    "action": "Lancez Ollama et installez le modele local configure, puis renvoyez la photo.",
                    "question": "Ollama est-il lance avec le modele local configure ?",
                },
                "en": {
                    "summary": "The photo was received, but local Llama/Ollama analysis is currently unavailable.",
                    "reason": "Ollama or the local vision model is not responding; no risk can be confirmed from this fallback.",
                    "action": "Start Ollama and install the configured local vision model, then upload the photo again.",
                    "question": "Is Ollama running with the configured local vision model?",
                },
                "ar": {
                    "summary": "\u062a\u0645 \u0627\u0633\u062a\u0644\u0627\u0645 \u0627\u0644\u0635\u0648\u0631\u0629\u060c \u0644\u0643\u0646 \u062a\u062d\u0644\u064a\u0644\u0647\u0627 \u0627\u0644\u0645\u062d\u0644\u064a \u0628\u0648\u0627\u0633\u0637\u0629 \u0644\u0627\u0645\u0627 \u063a\u064a\u0631 \u0645\u062a\u0627\u062d \u062d\u0627\u0644\u064a\u0627.",
                    "reason": "\u062e\u062f\u0645\u0629 \u0623\u0648\u0644\u0627\u0645\u0627 \u0623\u0648 \u0646\u0645\u0648\u0630\u062c \u0627\u0644\u0631\u0624\u064a\u0629 \u0627\u0644\u0645\u062d\u0644\u064a \u0644\u0627 \u064a\u062c\u064a\u0628\u061b \u0644\u0630\u0644\u0643 \u0644\u0627 \u064a\u0645\u0643\u0646 \u062a\u0623\u0643\u064a\u062f \u0623\u064a \u062e\u0637\u0631 \u0645\u0646 \u0647\u0630\u0627 \u0627\u0644\u0631\u062f \u0627\u0644\u0627\u062d\u062a\u064a\u0627\u0637\u064a.",
                    "action": "\u0634\u063a\u0651\u0644 \u0623\u0648\u0644\u0627\u0645\u0627 \u0648\u062b\u0628\u0651\u062a \u0646\u0645\u0648\u0630\u062c \u0627\u0644\u0631\u0624\u064a\u0629\u060c \u062b\u0645 \u0623\u0639\u062f \u0625\u0631\u0633\u0627\u0644 \u0627\u0644\u0635\u0648\u0631\u0629.",
                    "question": "\u0647\u0644 \u062e\u062f\u0645\u0629 \u0623\u0648\u0644\u0627\u0645\u0627 \u062a\u0639\u0645\u0644 \u0645\u0639 \u0646\u0645\u0648\u0630\u062c \u0627\u0644\u0631\u0624\u064a\u0629\u061f",
                },
            }
            texts = ollama_messages
        labels = texts.get(language, texts["ar"])
        return {
            "analysis_available": False,
            "classification": "A confirmer",
            "confidence": 0.0,
            "observations": [],
            "scene_summary": labels["summary"],
            "risk_items": [],
            "main_risks": [],
            "prevention_measures": [labels["action"]],
            "global_risk_level": "LOW",
            "global_risk_reason": labels["reason"],
            "immediate_danger": False,
            "recommended_action": labels["action"],
            "questions": [labels["question"]],
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
    def _normalize_observation_text(cls, text: str) -> str:
        value = cls._apply_editorial_rigor(cls._normalize_coil_handling_claims(str(text or "")))
        value = re.sub(r"\b(risque|danger)\s+(de|d[' ]?)\s+", "", value, flags=re.IGNORECASE)
        value = re.sub(r"\b(peut|pourrait|risque de|susceptible de)\s+[^.;,]+", "", value, flags=re.IGNORECASE)
        value = re.sub(r"\b(non[- ]?conformite|defaut|accident|blessure|consequence|mesure|prevention)\b.*", "", value, flags=re.IGNORECASE)
        value = re.sub(r"\b(chute|collision|ecrasement|brulure|glissade|coupure)\b", "element a verifier", value, flags=re.IGNORECASE)
        value = re.sub(r"\s+(et|ou|avec|pour)\s*$", "", value, flags=re.IGNORECASE)
        value = re.sub(r"\s+[,.;:]\s*$", "", value).strip()
        return " ".join(value.split()) or "Observation visible a confirmer."

    @classmethod
    def _apply_editorial_rigor(cls, text: str) -> str:
        value = str(text or "")
        lower_value = value.lower()
        if "trebuchement" in lower_value and "cable" in lower_value:
            return "خطر محتمل للتعثر بسبب كابل."
        if "partie du cable" in lower_value and "visible au sol" in lower_value:
            return "يوجد جزء من الكابل مرئيا على الأرض."
        if "partie du cable" in lower_value and "touche le sol" in lower_value:
            return "جزء من الكابل يلامس الأرض في الجزء المرئي من الصورة."
        if "deplacement" in lower_value and "roulement" in lower_value:
            return "خطر محتمل للتحرك أو التدحرج أثناء المناولة."
        if "bobine" in lower_value and "visible au sol" in lower_value:
            return "توجد بكرة أو كورونة مرئية على الأرض."
        if "bobine" in lower_value and "rouler" in lower_value:
            return "قد تتحرك البكرة أو تتدحرج أثناء عمليات المناولة."
        replacements = [
            (r"\b(element|objet|piece|arete)\s+saillant(e)?\s+(constitue|represente|est)\s+(un\s+)?(defaut|non-conformite)\b", r"\1 saillant\2 pourrait constituer un point a verifier selon le contexte"),
            (r"\belement\s+saillant\s+dangereux\b", "element saillant potentiellement dangereux si une exposition au contact est confirmee"),
            (r"\barete\s+saillante\s+dangereuse\b", "arete saillante potentiellement dangereuse si une exposition au contact est confirmee"),
            (r"\b(absence|manque|sans)\s+(de\s+)?(casque|gants|lunettes|chaussures|harnais|gilet|epi)\b", "EPI non confirmable sur cette photographie"),
            (r"\bdoit\s+etre\s+(retire|corrige|remplace|supprime)\b", "devrait etre verifie puis traite si necessaire"),
        ]
        for pattern, replacement in replacements:
            value = re.sub(pattern, replacement, value, flags=re.IGNORECASE)
        uncertainty_markers = [
            "non confirmable", "a confirmer", "ne peut pas etre confirme", "semble", "pourrait", "peut constituer",
        ]
        normalized = cls._strip_accents(value.lower())
        if any(marker in normalized for marker in uncertainty_markers):
            value = re.sub(r"\best\s+(un\s+)?danger\b", "pourrait constituer un danger", value, flags=re.IGNORECASE)
            value = re.sub(r"\bconstitue\s+(un\s+)?danger\b", "pourrait constituer un danger", value, flags=re.IGNORECASE)
            value = re.sub(r"\bnecessite\s+une\s+action\s+immediate\b", "peut necessiter une action apres confirmation terrain", value, flags=re.IGNORECASE)
        return " ".join(value.split())

    @classmethod
    def _has_visible_person_context(cls, result: dict[str, Any]) -> bool:
        texts: list[str] = []
        for key in ["scene_summary", "global_risk_reason", "recommended_action"]:
            texts.append(str(result.get(key) or ""))
        texts.extend(str(item) for item in cls._as_list(result.get("observations")))
        for item in cls._as_list(result.get("risk_items")):
            if isinstance(item, dict):
                texts.extend(str(item.get(key) or "") for key in ["risk", "observation", "description", "cause"])
        combined = cls._strip_accents(" ".join(texts).lower())
        person_markers = {
            "personne", "personnes", "operateur", "operateurs", "intervenant", "intervenants", "ouvrier", "ouvriers",
            "salarie", "travailleur", "travailleurs", "agent", "agents", "pieton", "pietons", "worker", "workers",
            "main visible", "bras visible", "visage", "corps", "silhouette", "personnel visible",
        }
        return any(marker in combined for marker in person_markers)

    @classmethod
    def _is_epi_comment(cls, text: str) -> bool:
        combined = cls._strip_accents(str(text or "").lower())
        return any(term in combined for term in ["epi", "casque", "lunettes", "gants", "chaussures", "harnais", "gilet", "protection auditive", "protection respiratoire"])

    @classmethod
    def _normalize_coil_handling_claims(cls, text: str) -> str:
        value = cls._soften_visual_overclaims(str(text or ""))
        lowered = cls._strip_accents(value.lower())
        has_coil_context = any(word in lowered for word in ["couronne", "couronnes", "bobine", "bobines", "coil", "coils"])

        if has_coil_context:
            replacements = [
                (r"chute\s+de\s+(couronnes?|bobines?|coils?)", "risque de deplacement ou de roulement des couronnes lors de la manutention"),
                (r"chute\s+des\s+(couronnes?|bobines?|coils?)", "risque de deplacement ou de roulement des couronnes lors de la manutention"),
                (r"(couronnes?|bobines?|coils?)\s+(peuvent|pourraient|risquent de)\s+chuter", "les couronnes pourraient se deplacer ou rouler lors des operations de manutention"),
                (r"stabilit\S*\s+potentiellement\s+insuffisante", "aucun dispositif de calage ou de maintien n est clairement visible sur la partie photographiee"),
                (r"stabilit\S*\s+insuffisante", "aucun dispositif de calage ou de maintien n est clairement visible sur la partie photographiee"),
                (r"instabilit\S*\s+des\s+(couronnes?|bobines?|coils?)", "dispositif de calage ou de maintien non clairement visible sur la partie photographiee"),
            ]
            for pattern, replacement in replacements:
                value = re.sub(pattern, replacement, value, flags=re.IGNORECASE)
        else:
            value = re.sub(r"stabilit\S*\s+potentiellement\s+insuffisante", "non confirmable sur cette photographie", value, flags=re.IGNORECASE)
            value = re.sub(r"stabilit\S*\s+insuffisante", "non confirmable sur cette photographie", value, flags=re.IGNORECASE)

        value = value.replace("la risque de deplacement", "le risque de deplacement")
        value = value.replace("Les les couronnes", "Les couronnes")
        value = value.replace("les les couronnes", "les couronnes")
        return value

    @classmethod
    def _filter_sst_rule(cls, rule: str, item: dict[str, str]) -> str:
        cleaned = cls._normalize_coil_handling_claims(rule).strip()
        if not cleaned:
            return ""
        context = cls._strip_accents(
            " ".join(
                str(item.get(key) or "")
                for key in ["risk", "observation", "description", "cause", "possible_consequences", "prevention_measure"]
            ).lower()
        )
        mentions_n3 = bool(re.search(r"\bn\s*0?3\b|charge suspendue", cls._strip_accents(cleaned.lower())))
        has_lifting_evidence = any(
            token in context
            for token in [
                "charge suspendue",
                "suspendue",
                "crochet",
                "elingue",
                "elingage",
                "pont roulant",
                "grue",
                "personne sous charge",
            ]
        )
        if mentions_n3 and not has_lifting_evidence:
            if any(token in context for token in ["couronne", "couronnes", "bobine", "bobines", "coil", "coils", "manutention"]):
                return "N13 Manutention manuelle / N23 5S Site propre"
            return ""
        return cleaned


    @classmethod
    def _risk_sort_key(cls, item: dict[str, str]) -> tuple[int, int]:
        severity_rank = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}
        severity = severity_rank.get(str(item.get("severity") or "MEDIUM").upper(), 2)
        evidence = len(str(item.get("observation") or "")) + len(str(item.get("description") or ""))
        return (severity, evidence)

    @classmethod
    def _has_clear_visual_evidence(cls, item: dict[str, str]) -> bool:
        observation = cls._strip_accents(str(item.get("observation") or item.get("description") or "").lower())
        risk = cls._strip_accents(str(item.get("risk") or "").lower())
        if len(observation) < 18:
            return False
        weak_observations = {
            "observation visible a confirmer", "a confirmer sur terrain", "aucun fait visible detaille n a ete fourni",
            "localisation a confirmer", "zone visible", "equipement visible", "machine visible", "objet visible",
        }
        if observation in weak_observations:
            return False
        unsupported_risk_markers = [
            "frequent", "typique", "possible sans preuve", "theorique", "hypothese", "a confirmer", "non confirmable",
        ]
        if any(marker in risk for marker in unsupported_risk_markers):
            return False
        object_only_markers = [
            "marquage au sol visible", "machine visible", "objet visible", "equipement visible", "voie visible", "zone visible",
        ]
        if observation in object_only_markers:
            return False
        if any(marker in observation for marker in ["marquage au sol", "machine visible", "objet visible", "equipement visible"]):
            exposure_terms = ["obstacle", "fuite", "cable", "personne", "operateur", "pieton", "proximite", "contact", "bloque", "encombre", "passage reduit"]
            if not any(term in observation for term in exposure_terms):
                return False
        evidence_terms = [
            "au sol", "flaque", "obstacle", "encombre", "cable", "personne", "operateur", "pieton", "charge suspendue",
            "crochet", "elingue", "ouverture", "bord", "hauteur", "fuite", "flamme", "fumee", "organe", "mobile",
            "couronne", "bobine", "stockage", "passage", "voie", "zone", "proximite", "contact", "saillant",
            "\u0639\u0644\u0649 \u0627\u0644\u0623\u0631\u0636", "\u0627\u0644\u0623\u0631\u0636", "\u0643\u0627\u0628\u0644", "\u0633\u0644\u0643", "\u0639\u0627\u0626\u0642",
            "\u0628\u0643\u0631\u0629", "\u0643\u0648\u0631\u0648\u0646\u0629", "\u062a\u062e\u0632\u064a\u0646", "\u0645\u0645\u0631", "\u062a\u0633\u0631\u0628", "\u0632\u064a\u062a", "\u0645\u0627\u0621",
            "\u0634\u062e\u0635", "\u0639\u0627\u0645\u0644", "\u0631\u0627\u062c\u0644", "\u0634\u0627\u062d\u0646\u0629", "\u0631\u0627\u0641\u0639\u0629", "\u0645\u0639\u062f\u0629",
            "\u062d\u0645\u0648\u0644\u0629", "\u0645\u0639\u0644\u0642\u0629", "\u0641\u062a\u062d\u0629", "\u062d\u0627\u0641\u0629", "\u0627\u0631\u062a\u0641\u0627\u0639", "\u0646\u0627\u0631", "\u062f\u062e\u0627\u0646",
        ]
        return any(term in observation for term in evidence_terms)

    @classmethod
    def _limit_significant_risks(cls, items: list[dict[str, str]]) -> list[dict[str, str]]:
        filtered = [item for item in items if cls._has_clear_visual_evidence(item)]
        unique: list[dict[str, str]] = []
        seen: set[str] = set()
        for item in sorted(filtered, key=cls._risk_sort_key, reverse=True):
            key = cls._strip_accents(str(item.get("risk") or "").lower())
            key = re.sub(r"\b(possible|potentiel|potentiellement|risque de|risque d)\b", "", key).strip()
            if not key or key in seen:
                continue
            seen.add(key)
            unique.append(item)
        return unique[:2]

    @classmethod
    def _potential_ground_object_risk(cls, result: dict[str, Any]) -> dict[str, Any] | None:
        texts = [str(result.get("scene_summary") or ""), str(result.get("description") or "")]
        texts.extend(str(item) for item in cls._as_list(result.get("observations")))
        combined = " ".join(texts)
        normalized = cls._strip_accents(combined.lower())
        has_arabic = cls._has_arabic(combined)

        ground_terms = [
            "au sol", "sur le sol", "par terre", "ground", "floor",
            "\u0639\u0644\u0649 \u0627\u0644\u0623\u0631\u0636", "\u0641\u0648\u0642 \u0627\u0644\u0623\u0631\u0636", "\u0628\u0627\u0644\u0623\u0631\u0636",
        ]
        object_terms = [
            "bobine", "bøk", "bøbine", "couronne", "coil", "spool", "cable", "câble", "flexible", "objet",
            "\u0628\u0643\u0631\u0629", "\u0643\u0627\u0628\u0644", "\u0633\u0644\u0643", "\u063a\u0631\u0636", "\u0639\u0627\u0626\u0642",
        ]
        access_terms = [
            "porte", "acces", "accès", "passage", "mمر", "couloir", "voie", "entree", "entrée", "sortie",
            "equipement electrique", "équipement électrique", "coffret", "tableau", "armoire",
            "\u0628\u0627\u0628", "\u0645\u062f\u062e\u0644", "\u0645\u0645\u0631", "\u0645\u0633\u0627\u0631", "\u0644\u0648\u062d\u0629", "\u0643\u0647\u0631\u0628",
        ]
        has_ground = any(term in normalized or term in combined for term in ground_terms)
        has_object = any(term in normalized or term in combined for term in object_terms)
        has_access = any(term in normalized or term in combined for term in access_terms)
        if not (has_ground and has_object):
            return None

        observation = next((text for text in texts if text.strip() and (any(term in cls._strip_accents(text.lower()) for term in object_terms) or any(term in text for term in object_terms))), combined[:180])
        if has_arabic:
            return {
                "risk": "خطر التعثر أو الإعاقة بسبب جسم موضوع على الأرض",
                "status": "Potentiel" if has_access else "A verifier",
                "observation": observation,
                "location": "قرب العنصر المرئي في الصورة، ويجب تأكيد الموقع الدقيق ميدانيا.",
                "condition": "يصبح هذا الخطر مهما إذا كانت المنطقة تستعمل لمرور الأشخاص أو للوصول إلى تجهيزات السلامة.",
                "hazardous_event": "تعثر شخص أو إعاقة المرور.",
                "cause": "وجود جسم أو كابل على الأرض في منطقة قد تستعمل للمرور.",
                "description": observation,
                "possible_consequences": "قد يحدث سقوط أو إصابة، وقد يسبب ذلك إعاقة الوصول عند الحاجة.",
                "exposed_persons": "الأشخاص المارون في المنطقة إذا كان المرور مسموحا.",
                "severity": "MEDIUM",
                "probability": "MEDIUM",
                "risk_level": "MEDIUM",
                "confidence": min(float(result.get("confidence") or 0.85), 0.85),
                "immediate_measure": "إبعاد الجسم عن مسار المرور أو تأمينه مؤقتا.",
                "prevention_measure": "تخصيص مكان واضح وآمن لتخزين الكابلات أو البكرات، والحفاظ على الممرات خالية.",
                "sst_rule": "N23 5S Site propre",
            }
        return {
            "risk": "Risque potentiel de trébuchement ou d’encombrement lié à un objet au sol",
            "status": "Potentiel" if has_access else "A verifier",
            "observation": observation,
            "location": "Près de l’élément visible sur la photo; localisation exacte à confirmer sur site.",
            "condition": "Ce risque devient pertinent si la zone est utilisée pour le passage des travailleurs ou l’accès à un équipement.",
            "hazardous_event": "Trébuchement ou gêne du passage.",
            "cause": "Présence d’un objet ou câble au sol dans une zone pouvant servir au passage.",
            "description": observation,
            "possible_consequences": "Chute, blessure légère à moyenne ou gêne d’accès en cas de besoin.",
            "exposed_persons": "Personnes circulant dans la zone si le passage est autorisé.",
            "severity": "MEDIUM",
            "probability": "MEDIUM",
            "risk_level": "MEDIUM",
            "confidence": min(float(result.get("confidence") or 0.85), 0.85),
            "immediate_measure": "Retirer l’objet du passage ou le sécuriser provisoirement.",
            "prevention_measure": "Prévoir un rangement dédié pour les câbles ou bobines et maintenir les passages dégagés.",
            "sst_rule": "N23 5S Site propre",
        }

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
        result["observations"] = [cls._normalize_observation_text(str(item)) for item in cls._as_list(result.get("observations")) if str(item).strip()]
        result["immediate_danger"] = bool(result.get("immediate_danger"))
        result["risk_items"] = cls._limit_significant_risks(cls._normalize_risk_items(result.get("risk_items")))
        if not result["risk_items"]:
            candidate = cls._potential_ground_object_risk(result)
            if candidate:
                result["risk_items"] = cls._limit_significant_risks(cls._normalize_risk_items([candidate]))
        for key in ["main_risks", "prevention_measures", "questions", "location_hints", "related_sst_rules"]:
            result[key] = [cls._apply_editorial_rigor(cls._normalize_coil_handling_claims(str(item))) for item in cls._as_list(result.get(key)) if str(item).strip()]
        if not result["observations"] and result["risk_items"]:
            result["observations"] = [item["observation"] for item in result["risk_items"] if item.get("observation")]
        observed_rules: list[str] = []
        for item in result["risk_items"]:
            rule = cls._filter_sst_rule(str(item.get("sst_rule") or "").strip(), item)
            item["sst_rule"] = rule
            if rule and rule not in observed_rules:
                observed_rules.append(rule)
        combined_item = {
            "risk": " ".join(item.get("risk", "") for item in result["risk_items"]),
            "observation": " ".join(item.get("observation", "") for item in result["risk_items"]),
            "description": " ".join(item.get("description", "") for item in result["risk_items"]),
            "cause": " ".join(item.get("cause", "") for item in result["risk_items"]),
            "possible_consequences": " ".join(item.get("possible_consequences", "") for item in result["risk_items"]),
            "prevention_measure": " ".join(item.get("prevention_measure", "") for item in result["risk_items"]),
        }
        filtered_related_rules: list[str] = []
        for related_rule in result["related_sst_rules"]:
            filtered_rule = cls._filter_sst_rule(related_rule, combined_item)
            if filtered_rule and filtered_rule not in filtered_related_rules:
                filtered_related_rules.append(filtered_rule)
        if observed_rules:
            result["related_sst_rules"] = observed_rules
        elif result["risk_items"]:
            result["related_sst_rules"] = filtered_related_rules
        if not cls._has_visible_person_context(result):
            result["risk_items"] = [
                item for item in result["risk_items"]
                if not cls._is_epi_comment(" ".join(str(item.get(key) or "") for key in ["risk", "observation", "description", "cause", "prevention_measure"]))
            ]
            result["observations"] = [item for item in result["observations"] if not cls._is_epi_comment(item)]
            for key in ["main_risks", "prevention_measures", "related_sst_rules"]:
                result[key] = [item for item in result.get(key, []) if not cls._is_epi_comment(item)]
        result["risk_items"] = cls._limit_significant_risks(result["risk_items"])
        result["related_sst_rules"] = result.get("related_sst_rules", [])[:3]
        observed_risk_names = {cls._strip_accents(str(item.get("risk") or "").lower()) for item in result["risk_items"]}
        if observed_risk_names:
            result["main_risks"] = [item.get("risk") for item in result["risk_items"] if item.get("risk")]
            result["prevention_measures"] = [item.get("prevention_measure") for item in result["risk_items"] if item.get("prevention_measure")]
            result["main_risks"] = result["main_risks"][:2]
            result["prevention_measures"] = result["prevention_measures"][:2]
            result["related_sst_rules"] = result.get("related_sst_rules", [])[:3]
        if result["risk_items"] and not result["main_risks"]:
            result["main_risks"] = [item["risk"] for item in result["risk_items"] if item.get("risk")][:2]
        if result["risk_items"] and not result["prevention_measures"]:
            result["prevention_measures"] = [
                item["prevention_measure"] for item in result["risk_items"] if item.get("prevention_measure")
            ][:2]
        if not result["risk_items"]:
            result["main_risks"] = []
            result["related_sst_rules"] = []
            result["global_risk_level"] = "LOW"
        else:
            if result["classification"] == "A confirmer":
                result["classification"] = "Situation dangereuse"
            severity_order = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}
            max_observed_severity = max(
                (
                    max(
                        severity_order.get(str(item.get("severity") or "MEDIUM").upper(), 2),
                        severity_order.get(str(item.get("risk_level") or "MEDIUM").upper(), 2),
                    )
                    for item in result["risk_items"]
                ),
                default=2,
            )
            current_level = str(result.get("global_risk_level") or "MEDIUM").upper()
            current_rank = severity_order.get(current_level, 2)
            if current_rank > max_observed_severity:
                result["global_risk_level"] = next(level for level, rank in severity_order.items() if rank == max_observed_severity)
            elif current_rank < max_observed_severity:
                result["global_risk_level"] = next(level for level, rank in severity_order.items() if rank == max_observed_severity)
        level = str(result.get("global_risk_level") or "MEDIUM").upper()
        result["global_risk_level"] = level if level in {"LOW", "MEDIUM", "HIGH", "CRITICAL"} else "MEDIUM"
        result["scene_summary"] = cls._apply_editorial_rigor(cls._normalize_coil_handling_claims(str(result.get("scene_summary") or result.get("description") or "Analyse photo HSE.")))
        if result.get("analysis_available") is False:
            result["confidence"] = 0.0
        elif result["confidence"] <= 0.0 and (result["observations"] or result["risk_items"] or result["scene_summary"]):
            result["confidence"] = 0.35
        result["description"] = result["scene_summary"]
        result["recommended_action"] = cls._apply_editorial_rigor(cls._normalize_coil_handling_claims(str(result.get("recommended_action") or "Securiser la zone et confirmer l'analyse avec le responsable HSE.")))
        result["global_risk_reason"] = cls._apply_editorial_rigor(cls._normalize_coil_handling_claims(str(result.get("global_risk_reason") or "Niveau etabli selon les risques visibles sur la photo.")))
        return result

    @classmethod
    def _ensure_result_language(cls, result: dict[str, Any], language: str) -> dict[str, Any]:
        if language == "ar":
            cls._sanitize_arabic_result(result)
            if getattr(llm_service, "provider", "openai") == "ollama":
                return result
            if not llm_service.available or not cls._needs_arabic_translation(result):
                return result
            translated = cls._translate_result_text(result, language)
            cls._sanitize_arabic_result(translated)
            return translated
        if language in {"fr", "en"} and llm_service.available and cls._needs_latin_translation(result):
            return cls._translate_result_text(result, language)
        return result

    @classmethod
    def _sanitize_arabic_result(cls, result: dict[str, Any]) -> dict[str, Any]:
        for key in ["scene_summary", "recommended_action", "global_risk_reason", "description"]:
            if key in result:
                result[key] = cls._force_arabic_display_text(result.get(key))
        for key in ["observations", "main_risks", "prevention_measures", "questions", "location_hints", "related_sst_rules"]:
            result[key] = [cls._force_arabic_display_text(item) for item in cls._as_list(result.get(key)) if str(item or "").strip()]
        sanitized_items = []
        for item in cls._as_list(result.get("risk_items")):
            if isinstance(item, dict):
                clean = dict(item)
                for key in [
                    "risk", "observation", "location", "condition", "hazardous_event", "cause",
                    "description", "possible_consequences", "exposed_persons",
                    "immediate_measure", "prevention_measure", "sst_rule",
                ]:
                    clean[key] = cls._force_arabic_display_text(clean.get(key))
                clean["status"] = cls._normalize_risk_status(clean.get("status"), clean)
                sanitized_items.append(clean)
        result["risk_items"] = sanitized_items
        return result

    @classmethod
    def _has_meaningful_latin_text(cls, text: Any) -> bool:
        value = str(text or "")
        value = re.sub(r"\b(AMANE|SONASID|HSE|SST|SAP|LOW|MEDIUM|HIGH|CRITICAL|N[0-9]+)\b", " ", value, flags=re.IGNORECASE)
        value = re.sub(r"[0-9%.,:;()/\-]+", " ", value)
        return bool(re.search(r"[A-Za-z]{3,}", value))

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
                    for key in [
                        "risk", "observation", "location", "condition", "hazardous_event", "cause",
                        "description", "possible_consequences", "exposed_persons",
                        "immediate_measure", "prevention_measure", "sst_rule",
                    ]
                    if str(item.get(key) or "").strip()
                )
        return any(cls._has_meaningful_latin_text(value) for value in texts)

    @classmethod
    def _needs_latin_translation(cls, result: dict[str, Any]) -> bool:
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
                    for key in [
                        "risk", "observation", "location", "condition", "hazardous_event", "cause",
                        "description", "possible_consequences", "exposed_persons",
                        "immediate_measure", "prevention_measure", "sst_rule",
                    ]
                    if str(item.get(key) or "").strip()
                )
        return any(cls._has_arabic(value) for value in texts)

    @classmethod
    def _translate_result_text(cls, result: dict[str, Any], language: str) -> dict[str, Any]:
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
        system_prompt = (
            f"Translate all user-facing textual values in this JSON to {('clear professional Modern Standard Arabic' if language == 'ar' else 'clear professional French' if language == 'fr' else 'clear professional English')}. "
            "Keep the same JSON keys and list structure. Do not add risks. Do not change classification, status, severity, booleans, model names, or source data. "
            "Preserve official names such as SONASID. For Arabic, use \u0623\u0645\u0627\u0646 instead of AMANE and \u0627\u0644\u0633\u0644\u0627\u0645\u0629 instead of HSE in user-facing text. Return only valid JSON."
        )
        translated = llm_service.generate_json(
            system_prompt=system_prompt,
            user_prompt=json.dumps(payload, ensure_ascii=False),
            fallback={},
            temperature=0.0,
        )
        if not translated:
            return result
        merged = dict(result)
        for key in ["observations", "scene_summary", "main_risks", "prevention_measures", "global_risk_reason", "recommended_action", "questions", "location_hints", "related_sst_rules"]:
            if translated.get(key):
                merged[key] = translated[key]
        if isinstance(translated.get("risk_items"), list):
            merged["risk_items"] = translated["risk_items"]
        merged["description"] = merged.get("scene_summary", result.get("description"))
        return merged

    @staticmethod
    def _strip_accents(text: str) -> str:
        return "".join(char for char in unicodedata.normalize("NFKD", text) if not unicodedata.combining(char))

    @classmethod
    def _is_observed_risk_item(cls, item: dict[str, str]) -> bool:
        risk = str(item.get("risk") or "").strip()
        description = str(item.get("description") or "").strip()
        observation = str(item.get("observation") or description).strip()
        combined = cls._strip_accents(f"{risk} {observation} {description}".lower())
        non_observed_markers = {
            "non confirmable", "aucun element visible", "a confirmer", "ne peut pas etre confirme", "ne sont pas confirmables", "risque theorique", "hypothese",
            "\u063a\u064a\u0631 \u0642\u0627\u0628\u0644 \u0644\u0644\u062a\u0623\u0643\u064a\u062f", "\u0644\u0627 \u064a\u0645\u0643\u0646 \u062a\u0623\u0643\u064a\u062f", "\u064a\u062d\u062a\u0627\u062c \u0625\u0644\u0649 \u062a\u0623\u0643\u064a\u062f", "\u063a\u064a\u0631 \u0645\u0624\u0643\u062f", "\u0644\u0627 \u064a\u0648\u062c\u062f \u0639\u0646\u0635\u0631 \u0645\u0631\u0626\u064a", "\u0644\u0627 \u062a\u0648\u062c\u062f \u0639\u0646\u0627\u0635\u0631 \u0645\u0631\u0626\u064a\u0629",
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
                status = cls._normalize_risk_status(item.get("status"), item)
                observation = cls._normalize_coil_handling_claims(str(item.get("observation") or item.get("description") or "Aucun fait visible detaille n a ete fourni."))
                cause = cls._normalize_coil_handling_claims(str(item.get("cause") or "Cause non confirmable sur cette photographie."))
                prevention_measure = cls._normalize_coil_handling_claims(str(item.get("prevention_measure") or item.get("measure") or item.get("recommended_action") or "Securiser la zone et confirmer l action avec le responsable HSE."))
                immediate_measure = cls._normalize_coil_handling_claims(str(item.get("immediate_measure") or item.get("immediate_action") or prevention_measure))
                probability = str(item.get("probability") or "MEDIUM").upper()
                risk_level = str(item.get("risk_level") or severity).upper()
                item_confidence = item.get("confidence")
                sst_rule = cls._filter_sst_rule(str(item.get("sst_rule") or item.get("rule") or item.get("regle_sst") or ""), item)
                normalized.append({
                    "risk": cls._apply_editorial_rigor(cls._normalize_coil_handling_claims(str(item.get("risk") or "Risque observe"))),
                    "status": status,
                    "observation": cls._normalize_observation_text(observation),
                    "description": cls._normalize_observation_text(observation),
                    "location": cls._apply_editorial_rigor(cls._normalize_coil_handling_claims(str(item.get("location") or item.get("localisation") or "Localisation precise a confirmer sur la photographie."))),
                    "condition": cls._apply_editorial_rigor(cls._normalize_coil_handling_claims(str(item.get("condition") or "Condition d exposition a confirmer selon l utilisation de la zone."))),
                    "hazardous_event": cls._apply_editorial_rigor(cls._normalize_coil_handling_claims(str(item.get("hazardous_event") or item.get("event") or item.get("dangerous_event") or "Evenement dangereux potentiel a confirmer."))),
                    "cause": cls._apply_editorial_rigor(cause),
                    "possible_consequences": cls._apply_editorial_rigor(cls._normalize_coil_handling_claims(str(item.get("possible_consequences") or item.get("consequences") or "Accident potentiel."))),
                    "exposed_persons": cls._apply_editorial_rigor(cls._normalize_coil_handling_claims(str(item.get("exposed_persons") or "Personnes exposees a confirmer selon l utilisation de la zone."))),
                    "severity": severity if severity in {"LOW", "MEDIUM", "HIGH", "CRITICAL"} else "MEDIUM",
                    "probability": probability if probability in {"LOW", "MEDIUM", "HIGH"} else "MEDIUM",
                    "risk_level": risk_level if risk_level in {"LOW", "MEDIUM", "HIGH", "CRITICAL"} else (severity if severity in {"LOW", "MEDIUM", "HIGH", "CRITICAL"} else "MEDIUM"),
                    "confidence": item_confidence,
                    "immediate_measure": cls._apply_editorial_rigor(immediate_measure),
                    "prevention_measure": cls._apply_editorial_rigor(prevention_measure),
                    "sst_rule": sst_rule,
                })
            elif str(item).strip():
                normalized.append({
                    "risk": str(item),
                    "status": "A verifier",
                    "observation": "A confirmer sur terrain.",
                    "description": "A confirmer sur terrain.",
                    "location": "Localisation precise a confirmer sur la photographie.",
                    "condition": "Condition d exposition a confirmer selon l utilisation de la zone.",
                    "hazardous_event": "Evenement dangereux potentiel a confirmer.",
                    "cause": "Cause non confirmable sur cette photographie.",
                    "possible_consequences": "Accident potentiel.",
                    "exposed_persons": "Personnes exposees a confirmer selon l utilisation de la zone.",
                    "severity": "MEDIUM",
                    "probability": "MEDIUM",
                    "risk_level": "MEDIUM",
                    "confidence": None,
                    "immediate_measure": "Securiser la zone et confirmer l action avec le responsable HSE.",
                    "prevention_measure": "Securiser la zone et confirmer l action avec le responsable HSE.",
                    "sst_rule": "",
                })
        return [item for item in normalized if cls._is_observed_risk_item(item)]

    @classmethod
    def _normalize_risk_status(cls, value: Any, item: dict[str, Any] | None = None) -> str:
        raw = cls._strip_accents(str(value or "").lower()).strip()
        if raw in {"confirme", "confirmed", "danger confirme"}:
            return "Confirme"
        if raw in {"potentiel", "potential", "danger potentiel"}:
            return "Potentiel"
        if raw in {"a verifier", "à verifier", "to verify", "point a verifier"}:
            return "A verifier"
        combined = cls._strip_accents(" ".join(str((item or {}).get(key) or "") for key in ["risk", "observation", "cause", "description"]).lower())
        if any(marker in combined for marker in ["a confirmer", "non confirmable", "si cette zone", "si l exposition", "pourrait", "potentiel"]):
            return "Potentiel"
        return "Confirme"

    @staticmethod
    def _status_label_ar(value: Any) -> str:
        labels = {
            "Confirme": "مؤكد",
            "Potentiel": "محتمل",
            "A verifier": "يحتاج إلى تحقق",
        }
        return labels.get(str(value or "A verifier"), "يحتاج إلى تحقق")

    @staticmethod
    def _level_label(level: Any) -> str:
        labels = {
            "LOW": "منخفض",
            "MEDIUM": "متوسط",
            "HIGH": "مرتفع",
            "CRITICAL": "حرج",
        }
        return labels.get(str(level or "MEDIUM").upper(), "متوسط")

    @staticmethod
    def _probability_label_ar(value: Any) -> str:
        labels = {
            "LOW": "منخفضة",
            "MEDIUM": "متوسطة",
            "HIGH": "مرتفعة",
        }
        return labels.get(str(value or "MEDIUM").upper(), "متوسطة")

    @staticmethod
    def _classification_label_ar(value: Any) -> str:
        labels = {
            "Acte dangereux": "فعل خطير",
            "Situation dangereuse": "وضعية خطيرة",
            "Acte dangereux et situation dangereuse": "فعل خطير ووضعية خطيرة",
            "A confirmer": "يحتاج إلى تأكيد",
        }
        return labels.get(str(value or "A confirmer"), "يحتاج إلى تأكيد")

    @staticmethod
    def _has_arabic(text: Any) -> bool:
        return any("\u0600" <= char <= "\u06ff" for char in str(text or ""))

    @classmethod
    def _force_arabic_display_text(cls, text: Any) -> str:
        value = str(text or "").strip()
        if not value:
            return ""

        lower_value = value.lower()
        if "elements visibles" in lower_value and "orange cable" in lower_value and "ground" in lower_value:
            return "\u062a\u0638\u0647\u0631 \u0627\u0644\u0635\u0648\u0631\u0629 \u0628\u0643\u0631\u0629 \u0643\u0627\u0628\u0644 \u0628\u0631\u062a\u0642\u0627\u0644\u064a\u0629 \u0645\u0648\u0636\u0648\u0639\u0629 \u0639\u0644\u0649 \u0627\u0644\u0623\u0631\u0636. \u0644\u0627 \u064a\u0638\u0647\u0631 \u0623\u064a \u0639\u0627\u0645\u0644 \u0623\u0648 \u0645\u0639\u062f\u0627\u062a \u0645\u062a\u062d\u0631\u0643\u0629 \u0641\u064a \u0627\u0644\u062c\u0632\u0621 \u0627\u0644\u0645\u0631\u0626\u064a \u0645\u0646 \u0627\u0644\u0635\u0648\u0631\u0629."
        if "trebuchage possible" in lower_value and "deterioration du cable" in lower_value:
            return "\u0642\u062f \u064a\u062d\u062f\u062b \u062a\u0639\u062b\u0631 \u0623\u0648 \u062a\u0644\u0641 \u0644\u0644\u0643\u0627\u0628\u0644 \u0625\u0630\u0627 \u0643\u0627\u0646 \u0627\u0644\u0643\u0627\u0628\u0644 \u0645\u0639\u0631\u0636\u0627 \u0644\u0644\u0645\u0631\u0648\u0631."
        if lower_value.strip() == "n23 5s site propre":
            return "\u0642\u0627\u0639\u062f\u0629 \u0633\u0648\u0646\u0627\u0633\u064a\u062f \u0631\u0642\u0645 \u062b\u0644\u0627\u062b\u0629 \u0648\u0639\u0634\u0631\u064a\u0646 \u062d\u0648\u0644 \u0627\u0644\u0646\u0638\u0627\u0641\u0629 \u0648\u0627\u0644\u062a\u0631\u062a\u064a\u0628."
        if "trebuchement" in lower_value and "cable" in lower_value:
            return "خطر محتمل للتعثر بسبب كابل."
        if "partie du cable" in lower_value and "visible au sol" in lower_value:
            return "يوجد جزء من الكابل مرئيا على الأرض."
        if "partie du cable" in lower_value and "touche le sol" in lower_value:
            return "جزء من الكابل يلامس الأرض في الجزء المرئي من الصورة."
        if "deplacement" in lower_value and "roulement" in lower_value:
            return "خطر محتمل للتحرك أو التدحرج أثناء المناولة."
        if "bobine" in lower_value and "visible au sol" in lower_value:
            return "توجد بكرة أو كورونة مرئية على الأرض."
        if "bobine" in lower_value and "rouler" in lower_value:
            return "قد تتحرك البكرة أو تتدحرج أثناء عمليات المناولة."
        replacements = [
            ("The image has been received, but local analysis by Llama is currently unavailable.", "تم استلام الصورة، لكن التحليل المحلي غير متاح حاليا."),
            ("The photo was received, but local Llama/Ollama analysis is currently unavailable.", "تم استلام الصورة، لكن التحليل المحلي غير متاح حاليا."),
            ("Secure the area and confirm the analysis with the HSE responsible.", "أمّن المنطقة وتحقق من التحليل مع مسؤول السلامة."),
            ("No direct risk observed", "لم يتم رصد خطر مباشر."),
            ("Do you confirm this analysis?", "هل تؤكد هذا التحليل؟"),
            ("Cable ou rallonge visible dans la zone de travail.", "يوجد كابل أو سلك تمديد مرئي في منطقة العمل."),
            ("Cable ou rallonge visible dans la zone", "كابل أو سلك تمديد مرئي في المنطقة."),
            ("Le cable forme une boucle, traverse ou occupe une partie visible de la zone.", "الكابل يشكل حلقة أو يشغل جزءا مرئيا من المنطقة."),
            ("Trebuchage, deterioration du cable ou contact electrique si l'exposition est confirmee.", "قد يحدث تعثر، أو تلف للكابل، أو تماس كهربائي إذا تم تأكيد التعرض."),
            ("Ranger ou fixer le cable et maintenir le passage degage.", "يجب ترتيب الكابل أو تثبيته، مع الحفاظ على الممر مفتوحا."),
            ("N23 5S Site propre / N21 Outillage a main", "قاعدة سوناسيد رقم ثلاثة وعشرين حول النظافة والترتيب، وقاعدة رقم واحد وعشرين حول أدوات العمل اليدوية."),
            ("Niveau etabli a partir des elements visibles extraits automatiquement; confirmation terrain recommandee.", "تم تحديد المستوى بناء على العناصر المرئية المستخرجة، ويوصى بتأكيد الوضع ميدانيا."),
            ("La zone visible est-elle une zone de passage ou de travail frequente ?", "هل المنطقة المرئية ممر أو منطقة عمل مستعملة بشكل متكرر؟"),
            ("1. Orange cable on the ground.", "توجد بكرة كابل برتقالية موضوعة على الأرض."),
            ("Orange cable on the ground.", "توجد بكرة كابل برتقالية موضوعة على الأرض."),
            ("Photo montrant un ou plusieurs elements visibles au sol dans une zone industrielle; l'analyse se limite aux dangers directement perceptibles.", "تظهر الصورة جزءا من منطقة صناعية فيها عنصر موضوع على الأرض، وينحصر التحليل في ما هو مرئي بشكل واضح."),
            ("A white door with a gold handle is partially open in the background of an industrial setting.", ""),
        ]
        for source, target in replacements:
            value = value.replace(source, target)

        regex_replacements = [
            (r"\bAMANE\s+AI\b|\bAMANE\b", "أمان"),
            (r"\bSONASID\b", "سوناسيد"),
            (r"\bHSE\b", "السلامة"),
            (r"\bSST\b", "السلامة"),
            (r"\bSAP\b", "نظام ساب"),
            (r"\bOpenAI\b", "خدمة الذكاء الاصطناعي"),
            (r"\bAPI\b", "واجهة برمجة التطبيقات"),
            (r"\bLOW\b", "منخفض"),
            (r"\bMEDIUM\b", "متوسط"),
            (r"\bHIGH\b", "مرتفع"),
            (r"\bCRITICAL\b", "حرج"),
            (r"\bLlama/Ollama\b|\bOllama\b|\bLlama\b", "النموذج المحلي"),
        ]
        for pattern, target in regex_replacements:
            value = re.sub(pattern, target, value, flags=re.IGNORECASE)

        value = re.sub(r"\bN\s*(\d+)\b", lambda match: "قاعدة رقم " + match.group(1), value, flags=re.IGNORECASE)
        value = re.sub(r"[A-Za-z]+", "", value)
        value = re.sub(r"\s+", " ", value).strip(" -?:?.")
        if not value:
            return "غير قابل للتأكيد من خلال هذه الصورة."
        if cls._has_meaningful_latin_text(value):
            return "غير قابل للتأكيد من خلال هذه الصورة."
        if value and value[-1] not in ".؟!":
            value += "."
        return value

    @classmethod
    def _arabic_or_note(cls, text: Any) -> str:
        value = cls._force_arabic_display_text(text)
        if value:
            return value
        return "غير محدد، يجب تأكيده ميدانيا."

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
    def _arabic_confidence_percent(value: Any) -> str:
        return VisionRiskAgent._confidence_percent(value).replace("%", " في المائة")

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
        if result.get("analysis_available") is False:
            title = "Photo analysis unavailable" if is_en else "Analyse photo indisponible"
            return "\n".join([
                title,
                "",
                str(result.get("scene_summary") or ""),
                "",
                ("Recommended action: " if is_en else "Action recommandee : ") + str(result.get("recommended_action") or ""),
                ("AMANE question: " if is_en else "Question AMANE : ") + str((result.get("questions") or [""])[0]),
            ]).strip()
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
            risk_lines.extend([
                f"- {item.get('risk', 'Risque')}",
                f"  {labels['observation']}: {item.get('observation') or item.get('description') or labels['non_confirmable']}",
                f"  {labels['cause']}: {item.get('cause') or labels['non_confirmable']}",
                f"  {labels['consequences']}: {item.get('possible_consequences') or labels['non_confirmable']}",
                f"  {labels['risk_level']}: {VisionRiskAgent._level_label_latin(item.get('severity', 'MEDIUM'), language)}",
                f"  {labels['prevention_measure']}: {item.get('prevention_measure') or result.get('recommended_action') or labels['default_action']}",
                f"  {labels['sst_rule']}: {item.get('sst_rule') or labels['non_confirmable']}",
            ])
        if not risk_lines:
            risk_lines.append("" + labels["no_precise"])
        observations = result.get("observations", []) or [labels["no_observation"]]
        main_risks = result.get("main_risks", []) or [labels["default_risk"]]
        prevention = result.get("prevention_measures", []) or [result.get("recommended_action", labels["default_action"])]
        rules = result.get("related_sst_rules", [])
        questions = result.get("questions", []) or [labels["default_question"]]
        scene_summary_text = VisionRiskAgent._arabic_or_note(result.get('scene_summary', ''))
        global_reason_text = VisionRiskAgent._arabic_or_note(result.get('global_risk_reason', ''))
        if not result.get("risk_items"):
            scene_summary_text = 'تظهر الصورة عنصرا مرئيا داخل منطقة صناعية، لكن لا يظهر خطر مباشر بشكل واضح من خلال الصورة.'
            global_reason_text = 'لم يتم رصد وضعية خطيرة مباشرة، لذلك يبقى مستوى الخطر منخفضا إلى حين التأكيد الميداني.'
            prevention = ['يجب الحفاظ على اليقظة وتأكيد الوضع ميدانيا عند الحاجة.']
            questions = ['ما هو العنصر الذي تريد تأكيده في هذه الصورة؟']
        sections = [
            labels["title"], "",
            f"{labels['classification']}: {'Les deux' if result.get('classification') == 'Acte dangereux et situation dangereuse' and language == 'fr' else result.get('classification', 'A confirmer')}",
            f"{labels['level']}: {VisionRiskAgent._level_label_latin(result.get('global_risk_level', 'MEDIUM'), language)}",
            f"{labels['confidence']}: {VisionRiskAgent._confidence_percent(result.get('confidence'))}", "",
            labels["observations"] + ":", *(f"- {observation}" for observation in observations[:8]), "",
            f"{labels['summary']}: {result.get('scene_summary', '')}", "",
            labels["observed"] + ":", *risk_lines, "",
            labels["main"] + ":", *(f"- {risk}" for risk in main_risks[:10]), "",
            labels["prevention"] + ":", *(f"- {measure}" for measure in prevention[:12]), "",
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
        if result.get("analysis_available") is False:
            question = VisionRiskAgent._arabic_or_note((result.get("questions") or [""])[0])
            return "\n".join([
                "تحليل الصورة غير متاح", "",
                VisionRiskAgent._arabic_or_note(result.get("scene_summary") or ""), "",
                "الإجراء الموصى به: " + VisionRiskAgent._arabic_or_note(result.get("recommended_action") or ""),
                "سؤال أمان: " + question,
            ]).strip()
        observations = result.get("observations", []) or ["لم يتم استخراج ملاحظة مرئية واضحة تلقائيا."]
        risk_items = result.get("risk_items", [])[:2]
        confirmed_items = [item for item in risk_items if item.get("status") == "Confirme"]
        potential_items = [item for item in risk_items if item.get("status") != "Confirme"]
        main_risks = result.get("main_risks", []) or ["لم يتم رصد خطر مباشر على الصورة"]
        prevention = result.get("prevention_measures", []) or [result.get("recommended_action", "يجب تأمين المنطقة.")]
        rules = result.get("related_sst_rules", [])
        questions = result.get("questions", []) or ["هل تؤكد هذا التحليل؟"]
        scene_summary_text = VisionRiskAgent._arabic_or_note(result.get('scene_summary', ''))
        global_reason_text = VisionRiskAgent._arabic_or_note(result.get('global_risk_reason', ''))
        if not result.get("risk_items"):
            scene_summary_text = 'تظهر الصورة عنصرا مرئيا داخل منطقة صناعية، لكن لا يظهر خطر مباشر بشكل واضح من خلال الصورة.'
            global_reason_text = 'لم يتم رصد وضعية خطيرة مباشرة، لذلك يبقى مستوى الخطر منخفضا إلى حين التأكيد الميداني.'
            prevention = ['يجب الحفاظ على اليقظة وتأكيد الوضع ميدانيا عند الحاجة.']
            questions = ['ما هو العنصر الذي تريد تأكيده في هذه الصورة؟']
        primary_risk = VisionRiskAgent._arabic_or_note(main_risks[0]) if result.get("risk_items") else "لم يتم تأكيد خطر مباشر."
        priority_action = VisionRiskAgent._arabic_or_note(prevention[0]) if prevention else VisionRiskAgent._arabic_or_note(result.get("recommended_action"))

        def render_risk_item(item: dict[str, Any]) -> list[str]:
            item_confidence = item.get("confidence")
            if item_confidence in {None, ""}:
                item_confidence = result.get("confidence")
            return [
                f"اسم الخطر: {VisionRiskAgent._arabic_or_note(item.get('risk', 'خطر'))}",
                f"الحالة: {VisionRiskAgent._status_label_ar(item.get('status'))}",
                f"الملاحظة: {VisionRiskAgent._arabic_or_note(item.get('observation') or item.get('description'))}",
                f"الموقع في الصورة: {VisionRiskAgent._arabic_or_note(item.get('location'))}",
                f"شرط تحقق الخطر: {VisionRiskAgent._arabic_or_note(item.get('condition'))}",
                f"الحدث الخطير المحتمل: {VisionRiskAgent._arabic_or_note(item.get('hazardous_event'))}",
                f"السبب: {VisionRiskAgent._arabic_or_note(item.get('cause'))}",
                f"الأشخاص المحتمل تعرضهم: {VisionRiskAgent._arabic_or_note(item.get('exposed_persons'))}",
                f"العواقب: {VisionRiskAgent._arabic_or_note(item.get('possible_consequences'))}",
                f"درجة الخطورة: {VisionRiskAgent._level_label(item.get('severity', 'MEDIUM'))}",
                f"احتمالية الحدوث: {VisionRiskAgent._probability_label_ar(item.get('probability', 'MEDIUM'))}",
                f"مستوى الخطر: {VisionRiskAgent._level_label(item.get('risk_level') or item.get('severity', 'MEDIUM'))}",
                f"مؤشر الثقة: {VisionRiskAgent._arabic_confidence_percent(item_confidence)}",
                f"الإجراء الفوري: {VisionRiskAgent._arabic_or_note(item.get('immediate_measure') or item.get('prevention_measure') or result.get('recommended_action'))}",
                f"الإجراء الوقائي: {VisionRiskAgent._arabic_or_note(item.get('prevention_measure') or result.get('recommended_action'))}",
                f"قاعدة سوناسيد: {VisionRiskAgent._arabic_or_note(item.get('sst_rule') or 'قاعدة سوناسيد يجب تأكيدها حسب المرجع الداخلي للسلامة.')}",
                "",
            ]

        confirmed_lines = []
        for item in confirmed_items:
            confirmed_lines.extend(render_risk_item(item))
        if not confirmed_lines:
            confirmed_lines.append("لا يوجد خطر مؤكد بشكل قاطع من خلال هذه الصورة.")

        potential_lines = []
        for item in potential_items:
            potential_lines.extend(render_risk_item(item))
        if not potential_lines:
            potential_lines.append("لا يوجد خطر محتمل إضافي واضح من خلال هذه الصورة.")

        positive_observations = [
            observation for observation in observations
            if any(word in str(observation) for word in ["نظيف", "مرتبة", "محمي", "محمية", "إشارة", "علامة", "خالية"])
        ][:4]
        if not positive_observations:
            positive_observations = ["توجد بعض العناصر المرئية مرتبة ظاهريا، لكن المطابقة الكاملة يجب تأكيدها ميدانيا."]

        confirmed_count = len(confirmed_items)
        potential_count = len(potential_items)
        combined_arabic_text = " ".join(
            str(value or "")
            for value in [
                *observations,
                scene_summary_text,
                *(item.get("observation", "") for item in risk_items),
                *(item.get("risk", "") for item in risk_items),
            ]
        )
        verification_points: list[str] = []
        if any(word in combined_arabic_text for word in ["بكرة", "كابل", "الأرض", "ممر", "باب", "مدخل", "عائق"]):
            verification_points.append("تكرار مرور الأشخاص في هذه المنطقة غير قابل للتأكيد من خلال الصورة وحدها.")
        if any(word in combined_arabic_text for word in ["كهرب", "لوحة", "كابل", "أسلاك", "صندوق"]):
            verification_points.append("المطابقة التقنية للتجهيزات الكهربائية غير قابلة للتأكيد من خلال الصورة وحدها.")
        if not verification_points:
            verification_points.append("لا توجد نقطة تحقق إضافية مؤثرة واضحة من خلال الصورة.")
        intro = (
            "تحليل أمان انتهى.\n\n"
            f"تم رصد {confirmed_count} خطر مؤكد و{potential_count} خطر محتمل.\n\n"
            f"الخطر الرئيسي:\n{primary_risk}\n\n"
            f"مستوى الخطر العام:\n{VisionRiskAgent._level_label(result.get('global_risk_level', 'MEDIUM'))}\n\n"
            f"مؤشر الثقة العام:\n{VisionRiskAgent._arabic_confidence_percent(result.get('confidence'))}\n\n"
            f"الإجراء الأولوي:\n{priority_action}"
        )
        sections = [
            intro, "",
            "تحليل صورة السلامة بواسطة أمان", "",
            "التصنيف المقترح:",
            VisionRiskAgent._classification_label_ar(result.get('classification', 'A confirmer')),
            "",
            "مستوى الخطر العام:",
            VisionRiskAgent._level_label(result.get('global_risk_level', 'MEDIUM')),
            "",
            "مؤشر الثقة:",
            VisionRiskAgent._arabic_confidence_percent(result.get('confidence')),
            "",
            "### الملاحظات", *(VisionRiskAgent._arabic_or_note(observation) for observation in observations[:8]), "",
            "### وصف المشهد", scene_summary_text, "",
            "### المخاطر المؤكدة", *confirmed_lines, "",
            "### المخاطر المحتملة", *potential_lines, "",
            "### نقاط يجب التحقق منها", *verification_points, "",
            "### العناصر الإيجابية المرصودة", *(VisionRiskAgent._arabic_or_note(item) for item in positive_observations), "",
            "### المخاطر الرئيسية", *(VisionRiskAgent._arabic_or_note(risk) for risk in main_risks[:2]), "",
            "### الإجراءات الوقائية الموصى بها", *(VisionRiskAgent._arabic_or_note(measure) for measure in prevention[:2]), "",
            "### الإجراء الأولوي", priority_action, "",
            "### تبرير مستوى الخطر العام", global_reason_text,
        ]
        if rules:
            sections.extend(["", "### قواعد السلامة الخاصة بسوناسيد المرتبطة", *(VisionRiskAgent._arabic_or_note(rule) for rule in rules[:8])])
        question = VisionRiskAgent._arabic_or_note(questions[0])
        if not VisionRiskAgent._has_arabic(question):
            question = "هل هذه المنطقة تستعمل بانتظام كممر للعمال؟"
        sections.extend(["", "### الخلاصة", global_reason_text, "", f"### سؤال أمان\n{question}"])
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


