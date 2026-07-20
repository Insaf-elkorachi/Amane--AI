# AMANE AI - Demo conversation HSE

Ce projet expose une API FastAPI qui guide un declarant dans une remontee HSE :

- verification du danger immediat ;
- collecte des informations de l'evenement ;
- generation d'un resume ;
- confirmation ;
- creation d'un rapport avec un numero du type `SON-HSE-2026-00001`.

## 1. Lancer PostgreSQL

Depuis le dossier `backend` :

```powershell
docker compose up -d
```

La base utilise les valeurs de `backend/docker-compose.yml` :

- base : `amane`
- utilisateur : `amane`
- port : `5432`

## 2. Installer les dependances

Depuis le dossier `backend` :

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## 3. Lancer l'API

Depuis le dossier `backend` :

```powershell
uvicorn main:app --reload
```

Verification rapide :

```powershell
curl http://127.0.0.1:8000/health
```

Reponse attendue :

```json
{
  "status": "ok",
  "service": "AMANE API"
}
```


Ouvre ensuite l'application dans le navigateur :

```text
http://127.0.0.1:8000/app/
```

## 4. Exemple qui fonctionne deja

Dans un deuxieme terminal, depuis le dossier `backend` :

```powershell
python demo_chat.py
```

Le script envoie une conversation complete a `/api/chat`, confirme les informations,
puis affiche le numero du rapport cree.

## 5. Meme demo avec curl

Utilise toujours le meme `session_id` pendant la conversation.

```powershell
curl -X POST http://127.0.0.1:8000/api/chat `
  -H "Content-Type: application/json" `
  -d "{\"session_id\":\"demo-001\",\"message\":\"bonjour\"}"
```

```powershell
curl -X POST http://127.0.0.1:8000/api/chat `
  -H "Content-Type: application/json" `
  -d "{\"session_id\":\"demo-001\",\"message\":\"non\"}"
```

Continue avec ces messages :

```text
situation dangereuse
Une flaque d'huile est presente pres de la ligne de production, avec risque de glissade pour les operateurs.
10/07/2026 a 14:30
Site Casablanca, atelier conditionnement, zone convoyeur 2
Aucun nom identifie
Amine El Fassi
Balisage de la zone et demande de nettoyage immediat
Chute de plain-pied, blessure et arret de production
oui
```

Quand le dernier message `oui` est envoye, l'API doit repondre avec `completed: true`
et un `report_number`.

## 6. Consulter les rapports crees

```powershell
curl http://127.0.0.1:8000/reports/
```

Cette route retourne la liste des rapports enregistres en base.

## Scenario de presentation

Tu peux presenter la demo comme ceci :

1. Ouvrir `http://127.0.0.1:8000/docs`.
2. Montrer `POST /api/chat`.
3. Envoyer les messages du scenario.
4. Montrer la confirmation avec le numero de rapport.
5. Ouvrir `GET /reports/` pour prouver que le rapport est sauvegarde.

## Demo assistant vocal

Ouvre l'application :

```text
http://127.0.0.1:8000/app/
```

Scenario de presentation :

1. Clique sur `Parler`.
2. Autorise le micro dans le navigateur.
3. Reponds oralement aux questions de l'assistant.
4. L'assistant transcrit la voix, pose la question suivante a voix haute et remplit le rapport a droite.
5. A la confirmation finale, dis `oui`.
6. Montre le numero du rapport et la liste `Rapports sauvegardes`.

Si le micro ne marche pas pendant la soutenance, utilise `Demo auto` ou le champ clavier : le parcours reste le meme.

## Architecture reelle RAG + agents

Le backend contient maintenant une premiere architecture agentique exploitable :

```text
Voix navigateur
-> POST /api/voice/message
-> SpeechToTextAdapter
-> IntentAgent
-> EmergencyAgent + RAG
-> ConversationService
-> ReportAgent + RAG
-> PostgreSQL
-> SAPService mock
-> TextToSpeechAdapter
-> Voix navigateur
```

Dossiers principaux :

- `backend/knowledge/` : base de connaissances HSE utilisee par le RAG.
- `backend/ai/rag.py` : recherche hybride, embeddings OpenAI si disponibles, fallback lexical sinon.
- `backend/agents/intent_agent.py` : detection intention/langue.
- `backend/agents/emergency_agent.py` : evaluation urgence avec contexte RAG.
- `backend/agents/report_agent.py` : enrichissement rapport, action recommandee, compatibilite SAP.
- `backend/sap/sap_service.py` : frontiere d'integration SAP, mock pour la demo.

Tester le RAG :

```powershell
curl "http://127.0.0.1:8000/api/rag/search?q=fuite%20huile%20glissade"
```

Tester le pipeline vocal :

```powershell
curl -X POST http://127.0.0.1:8000/api/voice/message `
  -H "Content-Type: application/json" `
  -d "{\"session_id\":\"demo-agent\",\"transcript\":\"Je veux signaler une fuite d'huile pres du convoyeur SONASID\"}"
```

Important : `OPENAI_API_KEY` doit rester uniquement dans `.env`. Ne jamais mettre de cle API dans le code.

## Demo avec QR code

Pour que le scan QR fonctionne sur telephone, lance FastAPI en mode reseau local depuis le dossier `backend` :

```powershell
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Sur le PC de demonstration, ouvre ensuite :

```text
http://127.0.0.1:8000/qr
```

La page affiche un QR code vers l'assistant vocal. Si le QR contient `127.0.0.1`, remplace l'adresse par l'IP locale du PC, par exemple :

```text
http://192.168.1.20:8000/app/
```

Le telephone doit etre connecte au meme reseau Wi-Fi que le PC. Apres scan, l'utilisateur arrive directement sur AMANE AI.

## Donnees enregistrees

Chaque declaration confirmee est sauvegardee dans la table `reports` avec les informations principales :

- `report_number`, `classification`, `description`, `event_datetime`, `location`
- `declarant` et `reclamant_name`
- `observed_person`, `immediate_action`, `risk_analysis`, `immediate_danger`, `status`
- `session_id`, `language`, `source`
- donnees IA/RAG : `ai_title`, `urgency`, `danger_type`, `recommended_action`, `rag_sources`
- donnees completes JSON : `raw_collected_data`, `transcript_history`, `agent_trace`, `sap_payload`

Au demarrage, l'application ajoute automatiquement les colonnes manquantes si la table `reports` existe deja.

## QR code et telephone - mode utile

Le QR local depend du serveur AMANE. Si le PC est eteint, si le serveur est ferme, ou si le reseau change, une adresse locale ou ngrok gratuit peut ne plus fonctionner.

### Option 1 - Demo locale PC / meme Wi-Fi

Depuis la racine du projet :

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\start_amane_local.ps1
```

La page QR s'ouvre sur :

```text
http://127.0.0.1:8010/qr
```

Le telephone peut ouvrir l'adresse Wi-Fi affichee par le script, mais le micro mobile exige souvent HTTPS.

### Option 2 - Telephone avec micro HTTPS via ngrok

Depuis la racine du projet :

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\start_amane_ngrok.ps1
```

Le script lance le backend, lance ngrok, recupere l'URL HTTPS et ouvre une page QR qui pointe vers :

```text
https://xxxx.ngrok-free.dev/app/
```

Sur ngrok gratuit, l'URL change a chaque relance. Pour garder le meme QR, il faut soit un domaine ngrok reserve, soit deployer AMANE sur un hebergement cloud avec HTTPS.

### Option 3 - QR permanent

Pour que le QR marche meme si VS Code est ferme, si le PC change de reseau ou pour une vraie utilisation terrain, il faut deployer AMANE sur un serveur permanent : Render, Railway, VPS, Azure, AWS, ou un serveur interne SONASID. Le QR doit alors pointer vers l'URL HTTPS permanente, par exemple :

```text
https://amane-sonasid.example.com/app/
```

## QR permanent

Un QR permanent doit pointer vers une URL HTTPS permanente. Il ne peut pas pointer vers `127.0.0.1`, une IP Wi-Fi du PC ou une URL ngrok gratuite, car ces adresses changent ou s'arrêtent quand le PC/serveur s'arrête.

### Configurer l'URL permanente

Dans `.env`, ajoute l'URL publique stable de ton application :

```env
PUBLIC_APP_URL="https://ton-domaine-permanent.com"
```

Tu peux aussi mettre directement :

```env
PUBLIC_APP_URL="https://ton-domaine-permanent.com/app/"
```

AMANE normalise automatiquement l'adresse et la page QR pointera vers :

```text
https://ton-domaine-permanent.com/app/
```

### Choix possibles pour obtenir une URL permanente

1. Hebergement cloud avec domaine HTTPS : Render, Railway, VPS, Azure, AWS, serveur interne SONASID.
2. Domaine ngrok reserve : fonctionne pour demo longue, mais demande generalement un compte/configuration ngrok avec domaine reserve.
3. Reseau local uniquement : non permanent, utile seulement en demo interne quand le PC et le telephone sont sur le meme Wi-Fi.

### Generer le QR permanent

Une fois `PUBLIC_APP_URL` configure et le backend relance, ouvre :

```text
https://ton-domaine-permanent.com/qr
```

Le QR affiche pointera vers l'assistant permanent. C'est ce QR qu'il faut imprimer ou afficher dans l'usine.
