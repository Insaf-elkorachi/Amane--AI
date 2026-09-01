import json
from typing import Any

import httpx

from core.config import settings

try:
    from openai import OpenAI
except ModuleNotFoundError:  # Allows local demo without installing OpenAI globally.
    OpenAI = None


class LLMService:
    def __init__(self) -> None:
        self.provider = (settings.LLM_PROVIDER or "openai").lower().strip()
        self.client = (
            OpenAI(api_key=settings.OPENAI_API_KEY, http_client=httpx.Client(trust_env=False))
            if OpenAI is not None and settings.OPENAI_API_KEY
            else None
        )
        self.model = settings.OLLAMA_MODEL if self.provider == "ollama" else settings.OPENAI_MODEL
        self.vision_model = settings.OLLAMA_VISION_MODEL if self.provider == "ollama" else settings.OPENAI_VISION_MODEL
        self.embedding_model = settings.OPENAI_EMBEDDING_MODEL
        self.ollama_base_url = settings.OLLAMA_BASE_URL.rstrip("/")
        self.timeout = settings.OLLAMA_TIMEOUT_SECONDS

    @property
    def available(self) -> bool:
        if not settings.LLM_ENABLED:
            return False
        if self.provider == "ollama":
            return True
        return bool(self.client)

    @property
    def openai_available(self) -> bool:
        return bool(settings.LLM_ENABLED and self.client)

    def _ollama_chat(
        self,
        model: str,
        messages: list[dict[str, Any]],
        *,
        temperature: float = 0.2,
        json_mode: bool = True,
        num_ctx: int | None = None,
        num_predict: int | None = None,
    ) -> str:
        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "stream": False,
            "keep_alive": settings.OLLAMA_KEEP_ALIVE,
            "options": {
                "temperature": temperature,
                "num_ctx": num_ctx or settings.OLLAMA_NUM_CTX,
                "num_predict": num_predict or settings.OLLAMA_NUM_PREDICT,
            },
        }
        if json_mode:
            payload["format"] = "json"
        with httpx.Client(timeout=self.timeout, trust_env=False) as client:
            response = client.post(f"{self.ollama_base_url}/api/chat", json=payload)
            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                raise RuntimeError(f"Ollama chat {response.status_code}: {response.text[:1000]}") from exc
            data = response.json()
        return str((data.get("message") or {}).get("content") or "")

    @staticmethod
    def _loads_json(content: str, fallback: dict[str, Any]) -> dict[str, Any]:
        try:
            return json.loads(content or "{}")
        except Exception:
            start = (content or "").find("{")
            end = (content or "").rfind("}")
            if start >= 0 and end > start:
                try:
                    return json.loads(content[start : end + 1])
                except Exception:
                    pass
        return fallback

    def generate_json(
        self,
        system_prompt: str,
        user_prompt: str,
        fallback: dict[str, Any],
        temperature: float = 0.2,
    ) -> dict[str, Any]:
        if not self.available:
            return fallback

        try:
            if self.provider == "ollama":
                content = self._ollama_chat(
                    self.model,
                    [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=temperature,
                    json_mode=True,
                )
                return self._loads_json(content, fallback)

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=temperature,
                response_format={"type": "json_object"},
            )
            content = response.choices[0].message.content or "{}"
            return json.loads(content)
        except Exception as exc:
            return {**fallback, "llm_error": str(exc)}


    @staticmethod
    def _caption_to_hse_json(caption: str) -> dict[str, Any]:
        text = (caption or "").strip()
        lower = text.lower()
        secondary_terms = ["door", "handle", "wall", "window", "ceiling", "plafond", "mur", "porte", "poignee", "fenetre"]
        important_terms = [
            "person", "worker", "operator", "load", "machine", "cable", "cord", "wire", "chemical", "spill", "liquid",
            "storage", "obstacle", "vehicle", "truck", "forklift", "crane", "hook", "coil", "cabinet", "electrical", "warning sign",
            "personne", "operateur", "charge", "engin", "machine", "flaque", "stockage", "obstacle", "coffret", "electrique",
        ]
        has_important_fact = any(term in lower for term in important_terms)
        observations = [text] if text and has_important_fact else []
        risk_items: list[dict[str, Any]] = []

        def add_risk(risk: str, severity: str, rule: str, prevention: str, consequences: str, observation: str | None = None, cause: str | None = None) -> None:
            if len(risk_items) >= 2:
                return
            risk_items.append(
                {
                    "risk": risk,
                    "observation": observation or text,
                    "cause": cause or (observation or text),
                    "description": observation or text,
                    "possible_consequences": consequences,
                    "severity": severity,
                    "prevention_measure": prevention,
                    "sst_rule": rule,
                }
            )

        if any(word in lower for word in ["suspended load", "hanging load", "charge suspendue", "crane hook", "hook"]):
            add_risk(
                "Risque d ecrasement par charge suspendue",
                "CRITICAL",
                "N3 Charge suspendue / N11 Elinguage",
                "Interdire la presence sous la charge et baliser le rayon de levage.",
                "Ecrasement ou blessure grave en cas de chute ou de mouvement de la charge.",
            )
        if any(word in lower for word in ["ladder", "scaffold", "height", "edge", "opening", "echelle", "echafaudage", "hauteur"]):
            add_risk(
                "Risque de chute de hauteur",
                "HIGH",
                "N8 Travaux en hauteur",
                "Verifier les protections collectives et les moyens d'acces avant intervention.",
                "Chute de hauteur pouvant provoquer des blessures graves.",
            )
        if any(word in lower for word in ["vehicle", "truck", "forklift", "loader", "excavator", "engin", "camion", "chariot"]):
            add_risk(
                "Risque de heurt lie a la circulation d engin",
                "HIGH",
                "N7 Conduite et engins / N19 Circulation des engins",
                "Separarer les flux pietons et engins et confirmer le balisage de circulation.",
                "Collision ou heurt avec un engin en mouvement.",
            )
        if any(word in lower for word in ["cord", "cable", "wire", "electrical cord", "fil", "rallonge"]):
            cable_exposure = ["floor", "ground", "sol", "passage", "walkway", "across", "loop", "coiled", "hanging", "boucle", "traverse", "suspendu"]
            if any(exposure in lower for exposure in cable_exposure):
                add_risk(
                    "Risque de trebuchement lie a un cable",
                    "MEDIUM",
                    "N23 5S Site propre",
                    "Ranger ou fixer le cable et maintenir le passage degage.",
                    "Trebuchage possible ou deterioration du cable si celui-ci est expose au passage.",
                    observation="Une partie du cable est visible au sol.",
                    cause="Une partie du cable touche le sol dans la partie visible de la photo.",
                )
        if any(word in lower for word in ["coil", "coils", "spool", "bobine", "couronne", "roll", "storage"]):
            if any(place in lower for place in ["floor", "ground", "sol", "stocked", "stored", "posee", "posee", "storage"]):
                add_risk(
                    "Risque potentiel de deplacement ou de roulement lors de la manutention",
                    "MEDIUM",
                    "N13 Manutention manuelle / N23 5S Site propre",
                    "Verifier le maintien de la bobine avant toute manutention et garder la zone degagee.",
                    "La bobine pourrait se deplacer ou rouler lors des operations de manutention.",
                    observation="Une bobine ou couronne est visible au sol.",
                    cause="La bobine ou couronne est posee au sol dans la partie visible de la photo.",
                )
        if any(word in lower for word in ["liquid", "spill", "oil", "water", "flaque", "huile", "eau"]):
            add_risk(
                "Risque de glissade lie a un deversement visible",
                "MEDIUM",
                "N23 5S Site propre",
                "Baliser la zone et nettoyer le deversement avec le moyen adapte.",
                "Glissade ou chute de plain-pied.",
            )
        if any(word in lower for word in ["flame", "fire", "smoke", "spark", "flamme", "fumee", "etincelle"]):
            add_risk(
                "Risque d incendie ou de fumee visible",
                "CRITICAL",
                "Regle incendie / POI Nador",
                "Alerter immediatement, evacuer si necessaire et appliquer la procedure d'urgence.",
                "Brulure, intoxication ou propagation d'incendie.",
            )

        if risk_items:
            level_order = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}
            global_level = max((item["severity"] for item in risk_items), key=lambda level: level_order.get(level, 1))
            return {
                "classification": "Situation dangereuse",
                "confidence": 0.85 if len(observations) <= 2 else 0.70,
                "observations": observations,
                "scene_summary": "Elements visibles: " + "; ".join(observations[:3]) + ". L'analyse se limite aux dangers pouvant etre deduits de ces elements visibles.",
                "risk_items": risk_items,
                "main_risks": [item["risk"] for item in risk_items],
                "prevention_measures": [item["prevention_measure"] for item in risk_items],
                "global_risk_level": global_level,
                "global_risk_reason": "Niveau etabli a partir des elements visibles extraits automatiquement; confirmation terrain recommandee.",
                "immediate_danger": global_level == "CRITICAL",
                "recommended_action": risk_items[0]["prevention_measure"],
                "questions": ["La zone visible est-elle une zone de passage ou de travail frequente ?"],
                "location_hints": [],
                "related_sst_rules": list(dict.fromkeys(item["sst_rule"] for item in risk_items if item.get("sst_rule")))[:3],
            }

        return {
            "classification": "A confirmer",
            "confidence": 0.50,
            "observations": observations,
            "scene_summary": ("Elements visibles: " + "; ".join(observations[:3]) + ". Aucun danger significatif ne ressort automatiquement de ces elements visibles.") if has_important_fact else "Les elements extraits automatiquement sont insuffisants pour decrire precisement la scene.",
            "risk_items": [],
            "main_risks": [],
            "prevention_measures": ["Conserver la vigilance et confirmer la situation avec le responsable HSE si besoin."],
            "global_risk_level": "LOW",
            "global_risk_reason": "Aucun danger direct n'a ete extrait automatiquement depuis la photo.",
            "immediate_danger": False,
            "recommended_action": "Confirmer la scene sur le terrain si un doute subsiste.",
            "questions": ["Pouvez-vous confirmer ce qui doit etre controle sur cette photo ?"],
            "location_hints": [],
            "related_sst_rules": [],
        }

    def generate_vision_json(
        self,
        system_prompt: str,
        user_prompt: str,
        image_base64: str,
        fallback: dict[str, Any],
        temperature: float = 0.05,
    ) -> dict[str, Any]:
        if not self.available:
            return fallback

        try:
            if self.provider == "ollama":
                combined_prompt = system_prompt.strip() + "\n\n" + user_prompt.strip() + "\n\nReturn only valid JSON. No markdown. No explanation outside JSON."

                errors: list[str] = []
                if self.vision_model and self.vision_model.lower() != "moondream":
                    try:
                        content = self._ollama_chat(
                            self.vision_model,
                            [{"role": "user", "content": combined_prompt, "images": [image_base64]}],
                            temperature=temperature,
                            json_mode=True,
                            num_predict=settings.OLLAMA_NUM_PREDICT,
                            num_ctx=settings.OLLAMA_NUM_CTX,
                        )
                        result = self._loads_json(content, {})
                        if result:
                            return {**result, "vision_model": self.vision_model, "llm_provider": "ollama"}
                        errors.append(f"{self.vision_model}: invalid JSON: {content[:300]}")
                    except Exception as exc:
                        errors.append(f"{self.vision_model}: {exc}")

                caption_models: list[str] = []
                for model in [self.vision_model, "moondream"]:
                    if model and model not in caption_models:
                        caption_models.append(model)

                for caption_model in caption_models:
                    caption = ""
                    try:
                        caption = self._ollama_chat(
                            caption_model,
                            [
                                {
                                    "role": "user",
                                    "content": (
                                        "Describe only useful visible facts in this industrial HSE image. "
                                        "Ignore walls, doors, windows, handles, and ceiling unless they directly create a risk. "
                                        "Prioritize in this order: people, loads, vehicles, machines, cables, products, storage, obstacles, floor, warning signs. "
                                        "Do not invent. Do not mention absence unless clearly visible. Keep it factual and concise."
                                    ),
                                    "images": [image_base64],
                                }
                            ],
                            temperature=0.0,
                            json_mode=False,
                            num_predict=260,
                            num_ctx=2048,
                        ).strip()
                        if caption:
                            heuristic = self._caption_to_hse_json(caption)
                            return {
                                **heuristic,
                                "vision_model": f"{caption_model}+rules",
                                "llm_provider": "ollama",
                                "vision_caption": caption,
                                "ollama_errors": errors,
                            }
                            analysis_prompt = combined_prompt + "\n\nVisible facts extracted by the vision model:\n" + caption + "\n\nBuild the requested JSON from these visible facts only. If a risk is not directly supported by these facts, do not include it."
                            content = self._ollama_chat(
                                self.model,
                                [{"role": "user", "content": analysis_prompt}],
                                temperature=temperature,
                                json_mode=True,
                                num_predict=settings.OLLAMA_NUM_PREDICT,
                                num_ctx=settings.OLLAMA_NUM_CTX,
                            )
                            result = self._loads_json(content, {})
                            if result:
                                return {
                                    **result,
                                    "vision_model": f"{caption_model}+{self.model}",
                                    "llm_provider": "ollama",
                                    "vision_caption": caption,
                                }
                            errors.append(f"{caption_model}+{self.model}: invalid JSON: {content[:300]}")
                    except Exception as exc:
                        errors.append(f"{caption_model}: {exc}")
                        if caption:
                            heuristic = self._caption_to_hse_json(caption)
                            if heuristic.get("observations") or heuristic.get("risk_items"):
                                return {
                                    **heuristic,
                                    "vision_model": f"{caption_model}+rules",
                                    "llm_provider": "ollama",
                                    "vision_caption": caption,
                                    "ollama_errors": errors,
                                }

                for model in ["llava"]:
                    try:
                        content = self._ollama_chat(
                            model,
                            [{"role": "user", "content": combined_prompt, "images": [image_base64]}],
                            temperature=temperature,
                            json_mode=True,
                            num_predict=settings.OLLAMA_NUM_PREDICT,
                            num_ctx=settings.OLLAMA_NUM_CTX,
                        )
                        result = self._loads_json(content, {})
                        if result:
                            return {**result, "vision_model": model, "llm_provider": "ollama"}
                        errors.append(f"{model}: invalid JSON: {content[:300]}")
                    except Exception as exc:
                        errors.append(f"{model}: {exc}")

                return {**fallback, "vision_error": " | ".join(errors)}

            response = self.client.chat.completions.create(
                model=self.vision_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": user_prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_base64}",
                                    "detail": settings.OPENAI_VISION_IMAGE_DETAIL,
                                },
                            },
                        ],
                    },
                ],
                temperature=temperature,
                max_tokens=settings.OPENAI_VISION_MAX_TOKENS,
                response_format={"type": "json_object"},
            )
            content = response.choices[0].message.content or "{}"
            result = json.loads(content)
            return {**result, "vision_model": self.vision_model, "llm_provider": "openai"}
        except Exception as exc:
            return {**fallback, "vision_error": str(exc)}

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not self.openai_available or not texts:
            return []

        response = self.client.embeddings.create(
            model=self.embedding_model,
            input=texts,
        )
        return [item.embedding for item in response.data]


llm_service = LLMService()
