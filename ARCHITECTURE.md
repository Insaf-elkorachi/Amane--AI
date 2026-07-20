# Architecture AMANE AI - Assistant vocal HSE

Cette implementation suit l'architecture en 7 blocs du prototype AMANE.

## 1. Utilisateur

L'utilisateur est un employe, visiteur ou technicien qui constate une anomalie HSE.

Dans la demo :

- interface web : `frontend/index.html`
- bouton micro : `frontend/app.js`
- fallback clavier si le micro n'est pas disponible

## 2. Acces rapide

L'acces se fait par QR code affiche sur site industriel. Le QR code ouvre l'application AMANE.

Dans la demo locale :

```text
http://127.0.0.1:8000/app/
```

Dans le projet :

- service statique FastAPI : `backend/main.py`
- interface : `frontend/index.html`

## 3. Interface vocale AMANE

L'interface vocale permet de parler, transcrire, afficher le dialogue et suivre le rapport.

Dans le projet :

- reconnaissance vocale navigateur : `frontend/app.js`
- synthese vocale navigateur : `frontend/app.js`
- affichage mobile/telephone : `frontend/index.html` et `frontend/styles.css`

## 4. Traitement vocal

Le bloc vocal est separe en deux frontieres techniques.

### 4.1 Speech-to-text

La voix est transformee en texte. Dans cette version, le navigateur utilise la Web Speech API, puis le backend recoit le transcript.

Dans le projet :

- adaptateur STT : `backend/speech/speech_to_text.py`
- entree API : `POST /api/voice/message`

### 4.2 Text-to-speech

La reponse de l'assistant est renvoyee comme texte pret a etre lu. Dans cette version, la lecture vocale est faite par le navigateur.

Dans le projet :

- adaptateur TTS : `backend/speech/text_to_speech.py`
- lecture vocale : `frontend/app.js`

## 5. Agent IA AMAN

L'agent applique les regles HSE, guide la conversation, detecte l'urgence et collecte les champs utiles.

Dans le projet :

- orchestration conversationnelle : `backend/services/conversation_service.py`
- pipeline vocal : `backend/services/voice_pipeline_service.py`
- route vocale : `backend/routers/voice.py`

Pour la demo, l'agent fonctionne avec une logique deterministe afin d'etre stable pendant la presentation. Les fichiers `backend/ai/` peuvent ensuite brancher un LLM reel.

## 6. Formulaire intelligent

Les reponses vocales remplissent progressivement un formulaire de reclamation HSE.

Champs collectes :

- danger immediat
- classification
- description
- date et heure
- localisation
- personne observee
- declarant
- action immediate
- analyse du risque

Dans le projet :

- schemas rapport : `backend/schemas/report.py`
- formulaire visible : `frontend/index.html`
- rendu des donnees : `frontend/app.js`

## 7. Stockage et donnees

Quand l'utilisateur confirme, le rapport est sauvegarde dans PostgreSQL.

Dans le projet :

- modele SQLAlchemy : `backend/models/report.py`
- service stockage : `backend/services/report_service.py`
- routes consultation : `backend/routers/reports.py`
- base locale : `backend/docker-compose.yml`

## Flux technique reel

```text
Utilisateur
  -> QR code / URL
  -> Interface vocale AMANE
  -> Speech-to-text navigateur
  -> POST /api/voice/message
  -> VoicePipelineService
  -> ConversationService / Agent HSE
  -> Formulaire intelligent
  -> Confirmation vocale
  -> PostgreSQL
  -> Text-to-speech navigateur
```

## Endpoints principaux

```text
GET  /app/                 Interface de demonstration
POST /api/voice/message    Pipeline vocal principal
GET  /reports/             Rapports sauvegardes
GET  /health               Verification API
```

## Pourquoi cette architecture est respectee

Chaque bloc du schema possede une responsabilite separee :

- le frontend gere l'experience vocale et mobile ;
- `speech/` represente les frontieres STT/TTS ;
- `voice_pipeline_service` orchestre le parcours vocal ;
- `conversation_service` joue le role d'agent HSE ;
- `schemas/report.py` et le frontend representent le formulaire intelligent ;
- `report_service.py` et PostgreSQL gerent la persistance.
