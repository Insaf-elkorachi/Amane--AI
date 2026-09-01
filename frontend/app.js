const messagesEl = document.querySelector("#messages");
const chatForm = document.querySelector("#chatForm");
const messageInput = document.querySelector("#messageInput");
const dataList = document.querySelector("#dataList");
const reportsList = document.querySelector("#reportsList");
const stepPill = document.querySelector("#stepPill");
const sessionLabel = document.querySelector("#sessionLabel");
const completionBadge = document.querySelector("#completionBadge");
const apiDot = document.querySelector("#apiDot");
const apiStatus = document.querySelector("#apiStatus");
const apiHint = document.querySelector("#apiHint");
const demoButton = document.querySelector("#demoButton");
const newSessionButton = document.querySelector("#newSessionButton");
const reloadReportsButton = document.querySelector("#reloadReportsButton");
const refreshReportsButton = document.querySelector("#refreshReportsButton");
const micButton = document.querySelector("#micButton");
const repeatButton = document.querySelector("#repeatButton");
const galleryPhotoButton = document.querySelector("#galleryPhotoButton");
const cameraPhotoButton = document.querySelector("#cameraPhotoButton");

const photoInput = document.querySelector("#photoInput");
const cameraInput = document.querySelector("#cameraInput");
const analysisLanguageSelect = document.querySelector("#analysisLanguageSelect");
const voiceOrb = document.querySelector("#voiceOrb");
const voiceState = document.querySelector("#voiceState");
const voiceHint = document.querySelector("#voiceHint");
const liveTranscript = document.querySelector("#liveTranscript");
const assistantReplyPreview = document.querySelector("#assistantReplyPreview");
const conversationDock = document.querySelector("#conversationDock");
const reportDrawer = document.querySelector("#reportDrawer");
const conversationToggleButton = document.querySelector("#conversationToggleButton");
const conversationCloseButton = document.querySelector("#conversationCloseButton");
const reportToggleButton = document.querySelector("#reportToggleButton");
const reportCloseButton = document.querySelector("#reportCloseButton");
const languageButtons = document.querySelectorAll("[data-speech-lang]");

const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
const recognition = SpeechRecognition ? new SpeechRecognition() : null;
window.AMANE_USE_SERVER_STT = true;
let activeSpeechLang = "fr-FR";

if (recognition) {
  recognition.onstart = () => {
    isListening = true;
    isAssistantSpeaking = false;
    updateLiveVoice("\u00c9coute en cours...", "AMANE attend votre message.");
    setVoiceMode("listening", "J\u2019\u00e9coute", "Parle maintenant. AMANE choisit la meilleure transcription HSE.");
  };
  recognition.onaudiostart = () => {
    updateLiveVoice("Micro ouvert...", "Parlez maintenant. AMANE attend la transcription du navigateur.");
  };
  recognition.onsoundstart = () => {
    updateLiveVoice("Son detecte...", "Continuez a parler clairement.");
  };
  recognition.onspeechstart = () => {
    updateLiveVoice("Voix d\u00e9tect\u00e9e...", "Continuez, AMANE transcrit votre phrase.");
  };
  recognition.onspeechend = () => {
    updateLiveVoice("Parole terminee...", "AMANE recupere la transcription.");
    window.setTimeout(() => {
      if (!isListening || pendingFinalTranscript.trim() || lastInterimTranscript.trim()) return;
      try {
        recognition.stop();
      } catch (error) {
        // Some browsers already stopped recognition.
      }
    }, 900);
  };
  recognition.onnomatch = () => {
    finishListeningWithoutTranscript("Le navigateur n'a pas reconnu les mots. Reessaie avec une phrase courte.");
  };
  recognition.lang = activeSpeechLang;
  recognition.interimResults = true;
  recognition.continuous = false;
  recognition.maxAlternatives = 5;
}

const demoMessages = [
  "bonjour",
  "non",
  "situation dangereuse",
  "Une flaque d'huile est présente près de la ligne de production, avec risque de glissade pour les opérateurs.",
  "10/07/2026  14:30",
  "Site SONASID Nador, atelier conditionnement, zone convoyeur 2",
  "Aucun nom identifié",
  "Amine El Fassi",
  "Balisage de la zone et demande de nettoyage immédiat",
  "Chute de plain-pied, blessure et arrêt de production",
  "oui",
];

const reportSections = [
  {
    title: "Identification",
    fields: [
      ["report_number", "Numéro de réclamation"],
      ["declarant", "Réclamant"],
      ["event_datetime", "Date et heure"],
      ["location", "Localisation"],
    ],
  },
  {
    title: "Analyse HSE",
    fields: [
      ["classification", "Type de signalement"],
      ["immediate_danger", "Danger immédiat"],
      ["observed_person", "Personne observée"],
      ["description", "Description"],
      ["risk_analysis", "Risque potentiel"],
    ],
  },
  {
    title: "Traitement",
    fields: [
      ["immediate_action", "Action immédiate"],
      ["recommended_action", "Action recommandée IA"],
      ["urgency", "Niveau d'urgence"],
      ["status", "Statut"],
    ],
  },
];

let sessionId = createSessionId();
let isRunningDemo = false;
let isListening = false;
let lastRecognitionResultAt = 0;
let isProcessingVoice = false;
let isAssistantSpeaking = false;
let pendingFinalTranscript = "";
let lastInterimTranscript = "";
let speechSettleTimer = null;
let recognitionNoResultTimer = null;
let recognitionHardStopTimer = null;
const SPEECH_SETTLE_DELAY_MS = 3000;
let speechVoices = [];
let speechUnlocked = false;
let activeTtsAudio = null;
let activeRecorder = null;
let activeRecordingStream = null;
let activeRecordingChunks = [];
let recordingStopTimer = null;
let activeAudioContext = null;
let activeAudioMonitor = null;
let activePeakLevel = 0;
let recordingStartedAt = 0;
let speechCooldownUntil = 0;
const SERVER_STT_RECORDING_MS = 7000;
const MIN_SERVER_STT_AUDIO_BYTES = 5000;
const MIN_SERVER_STT_PEAK_LEVEL = 0.008;
const introText = "Bonjour. Je suis AMANE, votre assistant vocal HSE. Parlez naturellement pour déclarer une situation HSE.";
let lastAssistantText = introText;

function createSessionId() {
  return `voice-${Math.random().toString(16).slice(2, 10)}`;
}

function cleanDisplayText(text) {
  let value = String(text ?? "");
  const replacements = [
    ["??", "?"], ["??", "?"], ["??", "?"], ["??", "?"], ["??", "?"],
    ["??", "?"], ["??", "?"], ["??", "?"], ["??", "?"], ["??", "?"],
    ["????", "?"], ["????", "?"], ["????", "?"], ["????", "?"],
    ["????", "?"], ["????", "?"], ["????", "?"], ["??", "?"],
    ["?couter", "\u00e9couter"], ["r?ponse", "r\u00e9ponse"], ["d?claration", "d\u00e9claration"],
    ["r?clamation", "r\u00e9clamation"], ["donn?es", "donn\u00e9es"], ["s?curis", "s\u00e9curis"],
  ];
  for (const [bad, good] of replacements) value = value.replaceAll(bad, good);
  return value
    .replace(/\bAMEN\b/g, "AMANE")
    .replace(/\bAMANE AI\b/g, "AMANE")
    .replace(/\bson\s*acid\b/gi, "SONASID")
    .replace(/\bsonaside\b/gi, "SONASID")
    .replace(/\bcite\s+son\s+acide\s+n['?]?adore\b/gi, "Site SONASID Nador")
    .replace(/\bsite\s+casablanca\b/gi, "Site SONASID Nador");
}

function normalizeSpeechSpacing(text) {
  return String(text || "")
    .replace(/\s+/g, " ")
    .replace(/\s+([,.!?;:])/g, "$1")
    .replace(/([,.!?;:])(?=\S)/g, "$1 ")
    .trim();
}

function stripDiacritics(text) {
  return String(text || "")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "");
}

function fixAssistantNameVocative(text) {
  return String(text || "")
    .replace(/\b(bonjour|salut|salam|salem|hello|hey)\s+(?:ahmed|ahmad|amal|amel|amina|amine|amen|amene|aman)\b/gi, "$1 AMANE")
    .replace(/\b(?:ahmed|ahmad|amal|amel|amina|amine|amen|amene|aman)\s*,\s+(?:bonjour|salam|salem|hello)\b/gi, "AMANE bonjour")
    .replace(/\b(?:hey|ok|allo)\s+(?:ahmed|ahmad|amal|amel|amina|amine|amen|amene|aman)\b/gi, "$1 AMANE")
    .replace(/\b(?:parle|reponds|réponds|ecoute|écoute)\s+(?:ahmed|ahmad|amal|amel|amina|amine|amen|amene|aman)\b/gi, "$1 AMANE");
}

function fixDomainTerms(text) {
  let value = fixAssistantNameVocative(normalizeSpeechSpacing(text));

  const replacements = [
    [/\b(?:amane|amanee|amene|amen|amelle|aman|a\s*mane|a\s*men)\b/gi, "AMANE"],
    [/\b(?:sonasid|sonaside|sona\s*sid|son\s*asid|son\s*acid|son\s*acide|son\s*aside|son\s*assid|son\s*a\s*sid)\b/gi, "SONASID"],
    [/\b(?:nador|nadore|n\s*adore|nadorr)\b/gi, "Nador"],
    [/\b(?:h\s*s\s*e|achesse|hache\s*esse|ash\s*ess\s*e)\b/gi, "HSE"],
    [/\b(?:e\s*p\s*i|epi|epis)\b/gi, "EPI"],
    [/\b(?:s\s*a\s*p|sap)\b/gi, "SAP"],
    [/\b(?:site|cite|citer)\s+SONASID\s+Nador\b/gi, "Site SONASID Nador"],
    [/\b(?:site|cite|citer)\s+SONASID\s+(?:casablanca|casa)\b/gi, "Site SONASID Nador"],
    [/\b(?:casablanca|casa)\b/gi, "Nador"],
    [/\b(?:site|cite|citer)\s+son\s*(?:acid|acide|asid|aside)\s+n(?:\s+)adore\b/gi, "Site SONASID Nador"],
    [/\b(?:acierie|aciere)\b/gi, "acierie"],
    [/\b(?:laminoire|laminoir)\b/gi, "laminoir"],
    [/\b(?:four\s+electrique)\b/gi, "four electrique"],
    [/\b(?:coulee\s+continue)\b/gi, "coulee continue"],
    [/\b(?:pont\s+roulant|ponts\s+roulants)\b/gi, "pont roulant"],
    [/\b(?:poste\s+de\s+soudure|poste\s+soudure)\b/gi, "poste de soudure"],
    [/\b(?:convoyeur|convoyers?|conveyer)\b/gi, "convoyeur"],
    [/\b(?:balisage|baliser|balise)\b/gi, "balisage"],
    [/\b(?:consignation|consignation\s+des\s+energies|isolation)\b/gi, "consignation"],
    [/\b(?:zone|zonne)\s*(\d{1,2})\b/gi, "zone $1"],
  ];

  for (const [pattern, replacement] of replacements) {
    value = value.replace(pattern, replacement);
  }

  return normalizeSpeechSpacing(value);
}

function speechCandidateScore(text) {
  const normalized = stripDiacritics(fixDomainTerms(text)).toLowerCase();
  let score = normalized.length * 0.01;
  const strongTerms = [
    "amane", "sonasid", "nador", "hse", "epi", "sap", "site sonasid nador",
    "danger", "risque", "situation", "acte", "zone", "atelier", "laminoir",
    "acierie", "four electrique", "coulee continue", "pont roulant", "convoyeur",
    "balisage", "consignation", "glissade", "chute", "brulure", "soudure",
  ];
  for (const term of strongTerms) {
    if (normalized.includes(term)) score += term.length > 8 ? 6 : 3;
  }
  if (/\b(son\s*acid|son\s*acide|son\s*asid|sonaside|amen|amel|ahmed|ahmad|amal|amina|amine|nadore|n\s*adore)\b/i.test(text)) score += 4;
  if (/\b(zone|zonne)\s*\d{1,2}\b/i.test(text)) score += 5;
  if (/\b(oui|non|ah|la)\b/i.test(text)) score += 1;
  return score;
}

function bestSpeechAlternative(result) {
  let best = result[0].transcript || "";
  let bestScore = speechCandidateScore(best) + ((result[0].confidence || 0) * 2);
  for (let i = 1; i < result.length; i += 1) {
    const candidate = result[i].transcript || "";
    const score = speechCandidateScore(candidate) + ((result[i].confidence || 0) * 2);
    if (score > bestScore) {
      best = candidate;
      bestScore = score;
    }
  }
  return fixDomainTerms(best);
}

async function ensureMicrophoneReady() {
  if (!navigator.mediaDevices?.getUserMedia) return true;
  try {
    const stream = await navigator.mediaDevices?.getUserMedia({
      audio: { echoCancellation: true, noiseSuppression: true, autoGainControl: true },
    });
    stream.getTracks().forEach((track) => track.stop());
    return true;
  } catch (error) {
      clearRecognitionNoResultTimer();
      setVoiceMode("error", "Micro bloqu\u00e9", "Autorise le micro dans le navigateur, puis r\u00e9essaie.");
    updateLiveVoice("", "Le micro est refuse ou indisponible sur ce navigateur.");
    return false;
  }
}

function updateSessionLabel() {
  sessionLabel.textContent = sessionId;
}

function togglePanel(panel, forceOpen) {
  if (!panel) return;
  const shouldOpen = typeof forceOpen === "boolean" ? forceOpen : !panel.classList.contains("is-open");
  panel.classList.toggle("is-open", shouldOpen);
}

function openReportPanel() {
  togglePanel(reportDrawer, true);
}

function closeReportPanel() {
  togglePanel(reportDrawer, false);
}

function openConversationPanel() {
  if (conversationDock?.hidden) conversationDock.hidden = false;
  togglePanel(conversationDock, true);
  window.setTimeout(() => messageInput?.focus(), 80);
}

function openKeyboardFallback(reason = "") {
  const hint = reason || "Le vocal mobile n'est pas disponible dans ce navigateur.";
  setVoiceMode("error", "Micro indisponible", "Utilise le champ sous la r\u00E9ponse d'AMANE.");
  updateLiveVoice("Micro indisponible", hint + " Tu peux continuer la d\u00E9claration par \u00E9crit.");
  focusKeyboardReply();
}

function focusKeyboardReply() {
  if (!messageInput) return;
  messageInput.placeholder = "\u00C9crire une r\u00E9ponse...";
  window.setTimeout(() => messageInput?.focus(), 80);
}

function closeConversationPanel() {
  togglePanel(conversationDock, false);
}

function setVoiceMode(mode, label, hint) {
  voiceOrb.classList.remove("listening", "speaking", "error");
  if (mode) voiceOrb.classList.add(mode);
  voiceState.textContent = cleanDisplayText(label);
  voiceHint.textContent = cleanDisplayText(hint);
}

function updateLiveVoice(transcript, reply) {
  if (typeof transcript === "string" && liveTranscript) {
    liveTranscript.textContent = cleanDisplayText(transcript || "En attente de votre voix...");
  }
  if (typeof reply === "string" && assistantReplyPreview) {
    assistantReplyPreview.textContent = cleanDisplayText(reply || "AMANE affichera ici sa r\u00e9ponse.");
  }
}
function refreshSpeechVoices() {
  if (!window.speechSynthesis) return;
  speechVoices = window.speechSynthesis.getVoices();
}

function containsArabicScript(text) {
  return /[\u0600-\u06ff]/.test(text || "");
}

function splitSpeechSentences(text, maxWords = 13) {
  const chunks = [];
  const sentences = String(text || "")
    .replace(/[;:]+/g, "\u060c")
    .split(/(<=[.!\u061f\u060c])\s+/);
  for (const sentence of sentences) {
    let words = sentence.trim().split(/\s+/).filter(Boolean);
    while (words.length > maxWords) {
      chunks.push(`${words.slice(0, maxWords).join(" ")}\u060c`);
      words = words.slice(maxWords);
    }
    if (words.length) chunks.push(words.join(" "));
  }
  return chunks.join("\n").trim();
}

function arabicNumberWord(value) {
  const words = new Map([
    ["0", "\u0635\u0641\u0631"], ["1", "\u0648\u0627\u062d\u062f"], ["2", "\u062c\u0648\u062c"], ["3", "\u062b\u0644\u0627\u062b\u0629"],
    ["4", "\u0631\u0628\u0639\u0629"], ["5", "\u062e\u0645\u0633\u0629"], ["6", "\u0633\u062a\u0629"], ["7", "\u0633\u0628\u0639\u0629"],
    ["8", "\u062b\u0645\u0627\u0646\u064a\u0629"], ["9", "\u062a\u0633\u0639\u0629"], ["10", "\u0639\u0634\u0631\u0629"], ["11", "\u062d\u062f\u0627\u0634"],
    ["12", "\u0627\u062b\u0646\u0627\u0634"], ["13", "\u062b\u0644\u0627\u0637\u0627\u0634"], ["14", "\u0631\u0628\u0639\u0637\u0627\u0634"],
    ["15", "\u062e\u0645\u0633\u0637\u0627\u0634"], ["16", "\u0633\u0637\u0627\u0634"], ["17", "\u0633\u0628\u0639\u0637\u0627\u0634"],
    ["18", "\u062b\u0645\u0646\u0637\u0627\u0634"], ["19", "\u062a\u0633\u0639\u0637\u0627\u0634"], ["20", "\u0639\u0634\u0631\u064a\u0646"],
    ["23", "\u062b\u0644\u0627\u062b\u0629 \u0648\u0639\u0634\u0631\u064a\u0646"], ["50", "\u062e\u0645\u0633\u064a\u0646"],
    ["85", "\u062e\u0645\u0633\u0629 \u0648\u062b\u0645\u0627\u0646\u064a\u0646"], ["100", "\u0645\u064a\u0629"],
    ["2026", "\u0623\u0644\u0641\u064a\u0646 \u0648\u0633\u062a\u0629 \u0648\u0639\u0634\u0631\u064a\u0646"],
  ]);
  return words.get(value) || value;
}

function applySpeechPronunciation(text, lang = "fr-FR") {
  let value = cleanDisplayText(String(text || ""));
  if (lang.startsWith("ar")) {
    value = value
      .replace(/AMANE\s+AI/gi, "\u0623\u0645\u0627\u0646")
      .replace(/AMANE/gi, "\u0623\u0645\u0627\u0646")
      .replace(/SONASID/gi, "\u0635\u0648\u0646\u0627\u0633\u064a\u062f")
      .replace(/HSE/gi, "\u0627\u0644\u0633\u0644\u0627\u0645\u0629 \u0648\u0627\u0644\u0635\u062d\u0629 \u0627\u0644\u0645\u0647\u0646\u064a\u0629")
      .replace(/SST/gi, "\u0627\u0644\u0633\u0644\u0627\u0645\u0629 \u0648\u0627\u0644\u0635\u062d\u0629 \u0627\u0644\u0645\u0647\u0646\u064a\u0629")
      .replace(/EPI/gi, "\u0645\u0639\u062f\u0627\u062a \u0627\u0644\u0648\u0642\u0627\u064a\u0629 \u0627\u0644\u0634\u062e\u0635\u064a\u0629")
      .replace(/SAP/gi, "\u0646\u0638\u0627\u0645 \u0633\u0627\u0628")
      .replace(/QR/gi, "\u0631\u0645\u0632 \u0627\u0644\u0627\u0633\u062a\u062c\u0627\u0628\u0629 \u0627\u0644\u0633\u0631\u064a\u0639\u0629")
      .replace(/API/gi, "\u0648\u0627\u062c\u0647\u0629 \u0628\u0631\u0645\u062c\u0629 \u0627\u0644\u062a\u0637\u0628\u064a\u0642\u0627\u062a")
      .replace(/LLM|GPT|AI/gi, "\u0646\u0645\u0648\u0630\u062c \u0630\u0643\u0627\u0621 \u0627\u0635\u0637\u0646\u0627\u0639\u064a")
      .replace(/risque|danger/gi, "\u062e\u0637\u0631")
      .replace(/classification/gi, "\u0627\u0644\u062a\u0635\u0646\u064a\u0641")
      .replace(/action/gi, "\u0627\u0644\u0625\u062c\u0631\u0627\u0621")
      .replace(/analyse/gi, "\u062a\u062d\u0644\u064a\u0644")
      .replace(/photo/gi, "\u0635\u0648\u0631\u0629")
      .replace(/prevention|prvention/gi, "\u0627\u0644\u0648\u0642\u0627\u064a\u0629")
      .replace(/mesures/gi, "\u0625\u062c\u0631\u0627\u0621\u0627\u062a")
      .replace(/securite|scurit/gi, "\u0627\u0644\u0633\u0644\u0627\u0645\u0629")
      .replace(/%/g, " \u0641\u064a \u0627\u0644\u0645\u0627\u0626\u0629 ")
      .replace(/\//g, " \u0623\u0648 ")
      .replace(/&/g, " \u0648 ")
      .replace(/\bN\s*(\d{1,2})\b/gi, (_, n) => `\u0627\u0644\u0642\u0627\u0639\u062f\u0629 ${arabicNumberWord(n)}`)
      .replace(/\b(\d{1,4})\b/g, (_, n) => arabicNumberWord(n));
    return splitSpeechSentences(value.replace(/\s+/g, " ").trim(), 12);
  }
  return value
    .replace(/AMANE AI/g, "A-mane")
    .replace(/AMANE/g, "A-mane")
    .replace(/\bAmane\b/g, "A-mane")
    .replace(/HSE/g, "H S E")
    .replace(/SONASID/g, "Sonasid");
}

function isDarijaText(text) {
  return !containsArabicScript(text) && /\b(salam|salem|salaam|hadchi|3afak|bghit|wach|wash|kayn|kayna|khatar|mouchkil|mochkil|safy|safi|wakha|nkemlo|tsajel|daba|fayn|fin|chno|smitk)\b/i.test(text || "");
}

function latinDarijaToArabicSpeech(text) {
  let value = ` ${String(text || "")} `
    .replace(/\b3/gi, "a")
    .replace(/\b9/gi, "k")
    .replace(/\b7/gi, "h");

  const phrases = [
    ["Salam, ana AMANE", "\u0633\u0644\u0627\u0645\u060c \u0623\u0646\u0627 AMANE"],
    ["Ana AMANE", "\u0623\u0646\u0627 AMANE"],
    ["l assistant vocal dyal HSE", "\u0627\u0644\u0645\u0633\u0627\u0639\u062f \u0627\u0644\u0635\u0648\u062a\u064a \u062f\u064a\u0627\u0644 HSE"],
    ["Ila bghiti tsajli chi khatar oula anomalie", "\u0625\u0644\u0627 \u0628\u063a\u064a\u062a\u064a \u062a\u0633\u062c\u0644\u064a \u0634\u064a \u062e\u0637\u0631 \u0648\u0644\u0627 \u0623\u0646\u0648\u0645\u0627\u0644\u064a"],
    ["goul lia chnou oukaa", "\u0642\u0648\u0644 \u0644\u064a\u0627 \u0634\u0646\u0648 \u0648\u0642\u0639"],
    ["Afak chraah lia b tafsil chnou oukaa", "\u0639\u0627\u0641\u0627\u0643 \u0634\u0631\u062d \u0644\u064a\u0627 \u0628\u0627\u0644\u062a\u0641\u0635\u064a\u0644 \u0634\u0646\u0648 \u0648\u0642\u0639"],
    ["Wach kayne chi khatar daba", "\u0648\u0627\u0634 \u0643\u0627\u064a\u0646 \u0634\u064a \u062e\u0637\u0631 \u062f\u0627\u0628\u0627"],
    ["aalik oula aala nass li maak", "\u0639\u0644\u064a\u0643 \u0648\u0644\u0627 \u0639\u0644\u0649 \u0627\u0644\u0646\u0627\u0633 \u0644\u064a \u0645\u0639\u0627\u0643"],
    ["Wach hadchi fiil khatir oula wadiya khatira", "\u0648\u0627\u0634 \u0647\u0627\u062f\u0634\u064a \u0641\u0639\u0644 \u062e\u0637\u064a\u0631 \u0648\u0644\u0627 \u0648\u0636\u0639\u064a\u0629 \u062e\u0637\u064a\u0631\u0629"],
    ["Fach oukaa had lhadath", "\u0641\u0627\u0634 \u0648\u0642\u0639 \u0647\u0627\u062f \u0627\u0644\u062d\u0627\u062f\u062b"],
    ["Aatini tarikh ou l waqt", "\u0639\u0637\u064a\u0646\u064a \u0627\u0644\u062a\u0627\u0631\u064a\u062e \u0648\u0627\u0644\u0648\u0642\u062a"],
    ["Fin oukaa hadchi", "\u0641\u064a\u0646 \u0648\u0642\u0639 \u0647\u0627\u062f\u0634\u064a"],
    ["Aatini site, atelier, ou zone b dabt", "\u0639\u0637\u064a\u0646\u064a \u0627\u0644\u0645\u0648\u0642\u0639\u060c \u0627\u0644\u0623\u062a\u0644\u064a\u064a\u060c \u0623\u0648 \u0627\u0644\u0632\u0648\u0646 \u0628\u0627\u0644\u0636\u0628\u0637"],
    ["Chnou smitak", "\u0634\u0646\u0648 \u0633\u0645\u064a\u062a\u0643"],
    ["Chnou smitak oula matricule dyalek", "\u0634\u0646\u0648 \u0633\u0645\u064a\u062a\u0643 \u0648\u0644\u0627 \u0627\u0644\u0645\u0627\u062a\u0631\u064a\u0643\u0648\u0644 \u062f\u064a\u0627\u0644\u0643"],
    ["Jawbni b ah oula la", "\u062c\u0627\u0648\u0628\u0646\u064a \u0628 \u0622\u0647 \u0648\u0644\u0627 \u0644\u0627"],
    ["Ma kayn mochkil", "\u0645\u0627 \u0643\u0627\u064a\u0646 \u0645\u0634\u0643\u0644"],
  ];
  for (const [source, target] of phrases) {
    value = value.replace(new RegExp(source.replace(/[.*+^${}()|[\]\\]/g, "\\$&"), "gi"), target);
  }

  const words = new Map([
    ["salam", "\u0633\u0644\u0627\u0645"], ["ana", "\u0623\u0646\u0627"], ["afak", "\u0639\u0627\u0641\u0627\u0643"], ["aafak", "\u0639\u0627\u0641\u0627\u0643"],
    ["wach", "\u0648\u0627\u0634"], ["wash", "\u0648\u0627\u0634"], ["kayne", "\u0643\u0627\u064a\u0646"], ["kayn", "\u0643\u0627\u064a\u0646"], ["kayna", "\u0643\u0627\u064a\u0646\u0629"],
    ["chi", "\u0634\u064a"], ["khatar", "\u062e\u0637\u0631"], ["daba", "\u062f\u0627\u0628\u0627"], ["dyal", "\u062f\u064a\u0627\u0644"], ["dial", "\u062f\u064a\u0627\u0644"],
    ["chnou", "\u0634\u0646\u0648"], ["chno", "\u0634\u0646\u0648"], ["fin", "\u0641\u064a\u0646"], ["fayn", "\u0641\u064a\u0646"], ["oukaa", "\u0648\u0642\u0639"], ["youkaa", "\u064a\u0648\u0642\u0639"],
    ["hadchi", "\u0647\u0627\u062f\u0634\u064a"], ["had", "\u0647\u0627\u062f"], ["smitak", "\u0633\u0645\u064a\u062a\u0643"], ["oula", "\u0648\u0644\u0627"], ["ah", "\u0622\u0647"], ["la", "\u0644\u0627"],
    ["amane", "AMANE"], ["hse", "HSE"], ["sonasid", "SONASID"], ["nador", "Nador"],
  ]);
  for (const [source, target] of [...words.entries()].sort((a, b) => b[0].length - a[0].length)) {
    value = value.replace(new RegExp(`\\b${source}\\b`, "gi"), target);
  }
  return applySpeechPronunciation(value.replace(/\s+/g, " ").trim(), "ar-MA");
}


function prepareSpeechText(text, lang) {
  const requestedLang = String(lang || "");
  if (requestedLang.startsWith("fr") || requestedLang.startsWith("en")) {
    return applySpeechPronunciation(text, requestedLang);
  }
  if (requestedLang.startsWith("ar")) {
    return isDarijaText(text) ? latinDarijaToArabicSpeech(text) : applySpeechPronunciation(text, "ar-MA");
  }
  if (containsArabicScript(text)) {
    return applySpeechPronunciation(text, "ar-MA");
  }
  if (isDarijaText(text)) {
    return latinDarijaToArabicSpeech(text);
  }
  return applySpeechPronunciation(text, requestedLang || getSpeechLang(text));
}
function getSpeechLang(text) {
  if (containsArabicScript(text)) return "ar-MA";
  if (isDarijaText(text)) return "ar-MA";

  const normalized = text
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase();
  const frenchMarkers = [
    "bonjour", "analyse", "photo", "risque", "classification", "proposee",
    "niveau", "resume", "observ\u00e9es", "prevention", "mesures", "chantier",
    "tranchee", "fouille", "excavation", "engins", "consequences",
    "confirmez", "reclamation", "declaration", "securiser", "zone",
  ];
  if (frenchMarkers.some((word) => normalized.includes(word))) return "fr-FR";

  const englishMarkers = [
    "hello", "please", "report", "unsafe", "hazard", "risk", "immediate",
    "confirm", "successfully", "saved", "what", "where", "when", "who",
    "workshop", "location",
  ];
  const englishCount = englishMarkers.filter((word) => normalized.includes(word)).length;
  return englishCount >= 2 ? "en-US" : "fr-FR";
}

function setRecognitionLanguage(lang) {
  activeSpeechLang = lang;
  if (recognition) recognition.lang = lang;
  languageButtons.forEach((button) => {
    button.classList.toggle("is-active", button.dataset.speechLang === lang);
  });
}

function selectedConversationLanguage() {
  const activeButton = [...languageButtons].find((button) => button.classList.contains("is-active"));
  if (activeButton?.dataset.conversationLang) return activeButton.dataset.conversationLang;
  if (activeSpeechLang.startsWith("ar")) return "darija";
  if (activeSpeechLang === "en-US") return "en";
  return "fr";
}

function selectedTranscriptionLanguage() {
  if (activeSpeechLang.startsWith("ar")) return "ar";
  if (activeSpeechLang === "en-US") return "en";
  return "fr";
}

function pickVoice(lang) {
  refreshSpeechVoices();
  if (speechVoices.length === 0) return null;

  const normalizedLang = String(lang || "").toLowerCase();
  const baseLang = normalizedLang.split("-")[0];
  const voices = [...speechVoices];

  if (baseLang === "ar") {
    const arabicVoices = voices.filter((voice) => voice.lang.toLowerCase().startsWith("ar"));
    const preferredArabicVoice =
      arabicVoices.find((voice) => /microsoft|google|natural|online|arabic|arabia|saudi|egypt|morocco|maged|hoda|naayf|salma|layla/i.test(voice.name)) ||
      arabicVoices.find((voice) => voice.lang.toLowerCase() === "ar-ma") ||
      arabicVoices.find((voice) => voice.lang.toLowerCase() === "ar-sa") ||
      arabicVoices.find((voice) => voice.lang.toLowerCase() === "ar-eg") ||
      arabicVoices[0];
    if (preferredArabicVoice) return preferredArabicVoice;
  }

  return (
    voices.find((voice) => voice.lang.toLowerCase() === normalizedLang) ||
    voices.find((voice) => voice.lang.toLowerCase().startsWith(`${baseLang}-`)) ||
    null
  );
}

function unlockSpeech() {
  if (!window.speechSynthesis || speechUnlocked) return;
  refreshSpeechVoices();
  const utterance = new SpeechSynthesisUtterance(" ");
  utterance.volume = 0;
  window.speechSynthesis.speak(utterance);
  speechUnlocked = true;
}

async function playServerSpeech(text, forcedLang = null) {
  if (!text || !window.fetch || !window.Audio) return false;
  try {
    const response = await fetch("/api/tts/speak", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text, lang: forcedLang || getSpeechLang(text) }),
    });
    if (!response.ok) return false;
    const blob = await response.blob();
    const audioUrl = URL.createObjectURL(blob);
    if (activeTtsAudio) activeTtsAudio.pause();
    const audio = new Audio(audioUrl);
    activeTtsAudio = audio;
    stopRecognitionWhileSpeaking();
    window.speechSynthesis?.cancel();
    await new Promise((resolve, reject) => {
      audio.onplay = () => {
        isAssistantSpeaking = true;
        if (micButton) micButton.disabled = true;
        setVoiceMode("speaking", "AMANE parle", "\u00c9coute la r\u00e9ponse, puis clique sur le micro.");
      };
      audio.onended = () => {
        isAssistantSpeaking = false;
        speechCooldownUntil = Date.now() + 800;
        if (micButton) micButton.disabled = false;
        activeTtsAudio = null;
        URL.revokeObjectURL(audioUrl);
        setVoiceMode(null, "Pr\u00eat \u00e0 \u00e9couter", "Clique sur le micro et r\u00e9ponds \u00e0 voix haute.");
        resolve();
      };
      audio.onerror = () => {
        isAssistantSpeaking = false;
        speechCooldownUntil = Date.now() + 800;
        if (micButton) micButton.disabled = false;
        activeTtsAudio = null;
        URL.revokeObjectURL(audioUrl);
        reject(new Error("audio playback failed"));
      };
      audio.play().catch(reject);
    });
    return true;
  } catch (error) {
    return false;
  }
}

function stopRecognitionWhileSpeaking() {
  pendingFinalTranscript = "";
  lastInterimTranscript = "";
  if (speechSettleTimer) {
    window.clearTimeout(speechSettleTimer);
    speechSettleTimer = null;
  }
  if (activeRecorder && activeRecorder.state !== "inactive") {
    stopServerRecording();
  }
  if (!recognition) return;
  if (isListening) {
    try {
      recognition.stop();
    } catch (error) {
      // Browser may already have stopped recognition.
    }
    isListening = false;
  }
  micButton?.setAttribute("aria-label", "Parler avec AMANE");
}
async function speak(text, forcedLang = null) {
  lastAssistantText = text;

  const serverSpeechOk = await playServerSpeech(text, forcedLang);
  if (serverSpeechOk) return;

  if (!window.speechSynthesis) {
    setVoiceMode("error", "Voix indisponible", "Votre navigateur ne prend pas en charge la synth\u00e8se vocale.");
    return;
  }

  refreshSpeechVoices();
  stopRecognitionWhileSpeaking();
  window.speechSynthesis?.cancel();

  const lang = forcedLang || getSpeechLang(text);
  const spokenText = prepareSpeechText(text, lang);
  const selectedVoice = pickVoice(lang);
  const browserLang = selectedVoice?.lang || (lang.startsWith("ar") ? "ar-SA" : lang);
  const utterance = new SpeechSynthesisUtterance(spokenText);
  utterance.lang = browserLang;
  utterance.rate = browserLang.startsWith("ar") ? 0.82 : 0.98;
  utterance.pitch = browserLang.startsWith("ar") ? 0.96 : 1;
  utterance.volume = 1;

  if (selectedVoice) utterance.voice = selectedVoice;
  if (lang.startsWith("ar")) {
    console.info("AMANE Arabic voice", selectedVoice ? `${selectedVoice.name} (${selectedVoice.lang})` : "no Arabic voice found, using ar-SA fallback");
  }

  utterance.onstart = () => {
    isAssistantSpeaking = true;
    if (micButton) micButton.disabled = true;
    setVoiceMode("speaking", "AMANE parle", "\u00c9coute la r\u00e9ponse, puis clique sur le micro.");
  };
  utterance.onend = () => {
    isAssistantSpeaking = false;
    speechCooldownUntil = Date.now() + 800;
    if (micButton) micButton.disabled = false;
    setVoiceMode(null, "Pr\u00eat \u00e0 \u00e9couter", "Clique sur le micro et r\u00e9ponds \u00e0 voix haute.");
  };
  utterance.onerror = () => {
    isAssistantSpeaking = false;
    speechCooldownUntil = Date.now() + 800;
    if (micButton) micButton.disabled = false;
    setVoiceMode("error", "Voix bloqu\u00e9e", "Clique sur R\u00e9p\u00e9ter ou v\u00e9rifie le volume du navigateur.");
  };

  window.speechSynthesis.speak(utterance);
  window.speechSynthesis.resume();
}

function addMessage(text, type = "system", isEmergency = false) {
  const node = document.createElement("div");
  node.className = `message ${type}${isEmergency ? " emergency" : ""}`;
  node.dir = "auto";
  node.textContent = cleanDisplayText(text);
  messagesEl.appendChild(node);
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

function formatValue(value) {
  if (value === true) return "Oui";
  if (value === false) return "Non";
  if (value === null || value === undefined || value === "") return "Non renseign\u00e9";
  if (Array.isArray(value)) return value.join(", ");
  if (typeof value === "object") return JSON.stringify(value);
  return cleanDisplayText(value);
}

function statusLabel(value) {
  if (!value) return "En cours";
  return String(value).replace(/_/g, " ");
}

function renderData(data = {}) {
  dataList.innerHTML = "";

  if (Object.keys(data).length === 0) {
    const empty = document.createElement("p");
    empty.className = "empty-state";
    empty.textContent = "Les informations du rapport se remplissent pendant l'\u00e9change vocal.";
    dataList.appendChild(empty);
    return;
  }

  const summary = document.createElement("div");
  summary.className = "report-summary";

  const reportNumber = document.createElement("strong");
  reportNumber.textContent = data.report_number || "R\u00e9clamation en cours";

  const summaryMeta = document.createElement("span");
  summaryMeta.textContent = `${formatValue(data.classification)} ? ${formatValue(data.declarant)}`;

  const badgeRow = document.createElement("div");
  badgeRow.className = "report-badges";

  const statusBadge = document.createElement("span");
  statusBadge.className = "table-badge";
  statusBadge.textContent = statusLabel(data.status || (data.report_number ? "enregistr\u00e9" : "en cours"));

  const dangerBadge = document.createElement("span");
  dangerBadge.className = `table-badge ${data.immediate_danger ? "danger" : "ok"}`;
  dangerBadge.textContent = data.immediate_danger ? "Danger imm\u00e9diat" : "Sans urgence imm\u00e9diate";

  badgeRow.append(statusBadge, dangerBadge);
  summary.append(reportNumber, summaryMeta, badgeRow);
  dataList.appendChild(summary);

  for (const section of reportSections) {
    const sectionNode = document.createElement("section");
    sectionNode.className = "report-section";

    const title = document.createElement("h3");
    title.textContent = section.title;

    const table = document.createElement("table");
    table.className = "report-table";

    const tbody = document.createElement("tbody");
    for (const [key, labelText] of section.fields) {
      if (!(key in data) && key !== "status") continue;
      if (["recommended_action", "urgency", "danger_type"].includes(key) && !data[key]) continue;

      const row = document.createElement("tr");
      const label = document.createElement("th");
      const detail = document.createElement("td");

      label.scope = "row";
      label.textContent = labelText;
      detail.textContent = key === "status" ? statusLabel(data[key]) : formatValue(data[key]);

      row.append(label, detail);
      tbody.appendChild(row);
    }

    table.appendChild(tbody);
    sectionNode.append(title, table);
    dataList.appendChild(sectionNode);
  }
}

function renderReports(reports = []) {
  reportsList.innerHTML = "";

  if (reports.length === 0) {
    const empty = document.createElement("p");
    empty.className = "empty-state";
    empty.textContent = "Aucun rapport sauvegard\u00e9 pour le moment.";
    reportsList.appendChild(empty);
    return;
  }

  const table = document.createElement("table");
  table.className = "saved-reports-table";
  table.innerHTML = `
    <thead>
      <tr>
        <th>Num\u00e9ro</th>
        <th>R\u00e9clamant</th>
        <th>Type</th>
        <th>Statut</th>
        <th>PDF</th>
      </tr>
    </thead>
  `;

  const tbody = document.createElement("tbody");
  for (const report of reports) {
    const row = document.createElement("tr");
    row.innerHTML = `
      <td><strong>${formatValue(report.report_number)}</strong></td>
      <td>${formatValue(report.reclamant_name || report.declarant)}</td>
      <td>${formatValue(report.classification)}</td>
      <td><span class="table-badge">${statusLabel(report.status)}</span></td>
      <td><a class="pdf-action" href="/reports/${report.id}/pdf" target="_blank" rel="noreferrer">PDF</a></td>
    `;
    tbody.appendChild(row);
  }

  table.appendChild(tbody);
  reportsList.appendChild(table);
}

async function checkApi() {
  try {
    const response = await fetch("/health");
    if (!response.ok) throw new Error("API indisponible");
    apiDot.className = "status-dot online";
    apiStatus.textContent = "API connect\u00e9e";
    apiHint.textContent = "FastAPI r\u00e9pond";
  } catch (error) {
    apiDot.className = "status-dot offline";
    apiStatus.textContent = "API connect\u00e9e";
    apiHint.textContent = "V\u00e9rifier uvicorn";
  }
}


async function readApiError(response) {
  const text = await response.text();
  if (!text) return "Erreur API sans detail.";
  try {
    const payload = JSON.parse(text);
    if (typeof payload.detail === "string") return payload.detail;
    return JSON.stringify(payload.detail || payload);
  } catch (error) {
    return text;
  }
}

function showApiError(error, contextText = "") {
  const detail = error.message || "Erreur inconnue.";
  const message = `Erreur API: ${detail}`;
  updateLiveVoice(contextText, message);
  addMessage(message, "system", true);
  setVoiceMode("error", "Erreur API", "Le backend a retourne une erreur detaillee dans la conversation.");
}

async function loadReports() {
  reportsList.innerHTML = '<p class="empty-state">Chargement des rapports...</p>';
  try {
    const response = await fetch("/reports/");
    if (!response.ok) throw new Error(await response.text());
    const reports = await response.json();
    renderReports(reports);
  } catch (error) {
    reportsList.innerHTML = '<p class="empty-state">Impossible de charger les rapports.</p>';
  }
}


function getPhotoSpokenQuestion(payload) {
  const questions = payload.vision.questions;
  if (Array.isArray(questions)) {
    const question = questions.find((item) => String(item || "").trim());
    if (question) return String(question).trim();
  }

  const response = String(payload.response || "");
  const match = response.match(/(:Question AMANE|AMANE question|\u0633\u0624\u0627\u0644 AMANE)\s*:\s*([^\n]+)/i);
  if (match?.[1]) return match[1].trim();

  const language = selectedPhotoAnalysisLanguage();
  if (language === "fr") return "Confirmez-vous cette analyse photo HSE ";
  if (language === "en") return "Do you confirm this HSE photo analysis";
  return "\u0647\u0644 \u062a\u0624\u0643\u062f \u0647\u0630\u0627 \u0627\u0644\u062a\u062d\u0644\u064a\u0644 \u0627\u0644\u062e\u0627\u0635 \u0628\u0635\u0648\u0631\u0629 HSE\u061f";
}

function selectedPhotoAnalysisLanguage() {
  return analysisLanguageSelect.value || "ar";
}

function photoSpeechLang() {
  const language = selectedPhotoAnalysisLanguage();
  if (language === "fr") return "fr-FR";
  if (language === "en") return "en-US";
  return "ar-MA";
}

function photoAnalysisUiText() {
  const language = selectedPhotoAnalysisLanguage();
  if (language === "fr") {
    return {
      detail: "AMANE analyse la photo HSE...",
      transcript: "Photo risque HSE",
      reply: "Analyse visuelle en cours...",
      user: "Photo de risque envoy\u00e9e \u00e0 AMANE.",
    };
  }
  if (language === "en") {
    return {
      detail: "AMANE is analyzing the HSE photo...",
      transcript: "HSE risk photo",
      reply: "Visual analysis in progress...",
      user: "Risk photo sent to AMANE.",
    };
  }
  return {
    detail: "AMANE \u064a\u062d\u0644\u0644 \u0627\u0644\u0635\u0648\u0631\u0629 HSE...",
    transcript: "\u0635\u0648\u0631\u0629 \u062e\u0637\u0631 HSE",
    reply: "\u0627\u0644\u062a\u062d\u0644\u064a\u0644 \u0627\u0644\u0628\u0635\u0631\u064a \u0642\u064a\u062f \u0627\u0644\u0625\u0646\u062c\u0627\u0632...",
    user: "\u062a\u0645 \u0625\u0631\u0633\u0627\u0644 \u0635\u0648\u0631\u0629 \u062e\u0637\u0631 \u0625\u0644\u0649 AMANE.",
  };
}


async function resizeRiskPhotoForUpload(file) {
  if (!file || !file.type.startsWith("image/")) return file;
  const maxSide = 1600;
  const quality = 0.88;

  try {
    const bitmap = await createImageBitmap(file);
    const scale = Math.min(1, maxSide / Math.max(bitmap.width, bitmap.height));
    if (scale >= 1 && file.size <= 1800 * 1024) return file;

    const canvas = document.createElement("canvas");
    canvas.width = Math.max(1, Math.round(bitmap.width * scale));
    canvas.height = Math.max(1, Math.round(bitmap.height * scale));
    const context = canvas.getContext("2d", { alpha: false });
    context.drawImage(bitmap, 0, 0, canvas.width, canvas.height);
    bitmap.close?.();

    const blob = await new Promise((resolve) => canvas.toBlob(resolve, "image/jpeg", quality));
    if (!blob) return file;

    return new File([blob], (file.name || "photo").replace(/.[^.]+$/, "") + "-amane.jpg", {
      type: "image/jpeg",
      lastModified: Date.now(),
    });
  } catch (error) {
    return file;
  }
}

async function sendRiskPhoto(file) {
  if (!file) return;
  unlockSpeech();
  const uiText = photoAnalysisUiText();
  setVoiceMode("listening", "Analyse photo HSE", uiText.detail);
  updateLiveVoice(uiText.transcript, uiText.reply);
  addMessage(uiText.user, "user");

  const formData = new FormData();
  formData.append("session_id", sessionId);
  formData.append("analysis_language", selectedPhotoAnalysisLanguage());
  const uploadFile = await resizeRiskPhotoForUpload(file);
  formData.append("photo", uploadFile);

  const response = await fetch("/api/vision/classify-risk", {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const text = await response.text();
    addMessage("Erreur analyse photo. V\u00e9rifie l’API et r\u00e9essaie.", "system", true);
  }

  const payload = await response.json();
  stepPill.textContent = payload.step;
  completionBadge.textContent = payload.completed ? "Termin\u00e9" : "En cours";
  completionBadge.classList.toggle("done", payload.completed);
  addMessage(payload.response, "system", payload.emergency);
  const spokenQuestion = getPhotoSpokenQuestion(payload);
  updateLiveVoice(uiText.transcript, payload.response);
  renderData(payload.collected_data);
  focusKeyboardReply();

  speak(spokenQuestion, photoSpeechLang());
}
async function sendMessage(message, { silentUser = false, voice = true, source = null } = {}) {
  const cleanMessage = fixDomainTerms(message);
  updateLiveVoice(cleanMessage, "AMANE analyse votre d\u00e9claration...");
  if (!silentUser) addMessage(cleanMessage, "user");

  const response = await fetch("/api/voice/message", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      session_id: sessionId,
      transcript: cleanMessage,
      source: source || (recognition ? "browser_speech_recognition" : "keyboard_fallback"),
      preferred_language: selectedConversationLanguage(),
    }),
  });

  if (!response.ok) {
    throw new Error(await readApiError(response));
  }

  const payload = await response.json();
  stepPill.textContent = payload.step;
  completionBadge.textContent = payload.completed ? "Termin\u00e9" : "En cours";
  completionBadge.classList.toggle("done", payload.completed);
  addMessage(payload.response, "system", payload.emergency);
  updateLiveVoice(cleanMessage, payload.response);
  renderData(payload.collected_data);

  if (voice) speak(payload.response);

  if (payload.completed) {
    setVoiceMode(null, "D\u00e9claration enregistr\u00e9e", "Merci. La r\u00e9clamation est transmise \u00e0 l\u2019\u00e9quipe HSE.");
  }

  return payload;
}

function resetUi({ speakIntro = true } = {}) {
  sessionId = createSessionId();
  updateSessionLabel();
  messagesEl.innerHTML = "";
  closeConversationPanel();
  closeReportPanel();
  stepPill.textContent = "start";
  completionBadge.textContent = "En cours";
  completionBadge.classList.remove("done");
  renderData({});
  addMessage(introText, "system");
  updateLiveVoice("", "");
  setVoiceMode(null, "Pr\u00eat \u00e0 \u00e9couter", recognition ? "Clique sur le micro et parle naturellement." : "Reconnaissance vocale non support\u00e9e, utilise le clavier.");
  if (speakIntro) speak(introText);
}

async function flushFinalTranscript() {
  const transcript = fixDomainTerms((pendingFinalTranscript || lastInterimTranscript).trim());
  pendingFinalTranscript = "";
  lastInterimTranscript = "";
  speechSettleTimer = null;
  clearRecognitionNoResultTimer();
  clearRecognitionHardStopTimer();

  if (!transcript || isProcessingVoice) return;

  isProcessingVoice = true;
  setVoiceMode(null, "Voix transcrite", "Texte re\u00e7u, AMANE pr\u00e9pare sa r\u00e9ponse.");
  updateLiveVoice(transcript, "AMANE analyse votre d\u00e9claration...");
  addMessage(transcript, "user");
  messageInput.value = transcript;

  try {
    await sendMessage(transcript, { silentUser: true, voice: true });
    messageInput.value = "";
  } catch (error) {
    updateLiveVoice(transcript, "Erreur API. V\u00e9rifie le backend et la base de donn\u00e9es.");
    addMessage("Erreur API. V\u00e9rifie le backend et la base de donn\u00e9es.", "system", true);
    setVoiceMode("error", "Erreur API", "Le texte est affich\u00e9, mais l\u2019envoi a \u00e9chou\u00e9.");
  } finally {
    isProcessingVoice = false;
  }
}

function clearRecognitionNoResultTimer() {
  if (recognitionNoResultTimer) {
    window.clearTimeout(recognitionNoResultTimer);
    recognitionNoResultTimer = null;
  }
}

function clearRecognitionHardStopTimer() {
  if (recognitionHardStopTimer) {
    window.clearTimeout(recognitionHardStopTimer);
    recognitionHardStopTimer = null;
  }
}

function finishListeningWithoutTranscript(message = "Choisis la bonne langue, parle plus pres du micro, ou ecris dans le champ.") {
  clearRecognitionNoResultTimer();
  clearRecognitionHardStopTimer();
  try {
    recognition?.stop();
  } catch (error) {
    // Some browsers already stop recognition after silence.
  }
  isListening = false;
  pendingFinalTranscript = "";
  lastInterimTranscript = "";
  micButton?.setAttribute("aria-label", "Parler avec AMANE");
  setVoiceMode("error", "Voix non transcrite", "Le navigateur a entendu une voix, mais n'a pas fourni de texte.");
  updateLiveVoice("Aucune transcription recue", message);
  focusKeyboardReply();
}

function stopServerRecording() {
  if (recordingStopTimer) {
    window.clearTimeout(recordingStopTimer);
    recordingStopTimer = null;
  }
  if (activeRecorder && activeRecorder.state !== "inactive") {
    activeRecorder.stop();
    return true;
  }
  return false;
}

function secondsLabel(milliseconds) {
  return `${Math.round(milliseconds / 1000)} secondes`;
}

function stopAudioMeter() {
  if (activeAudioMonitor) {
    window.cancelAnimationFrame(activeAudioMonitor);
    activeAudioMonitor = null;
  }
  if (activeAudioContext) {
    activeAudioContext.close().catch(() => {});
    activeAudioContext = null;
  }
}

function startAudioMeter(stream) {
  stopAudioMeter();
  activePeakLevel = 0;

  const AudioContextClass = window.AudioContext || window.webkitAudioContext;
  if (!AudioContextClass) return;

  try {
    activeAudioContext = new AudioContextClass();
    const source = activeAudioContext.createMediaStreamSource(stream);
    const analyser = activeAudioContext.createAnalyser();
    analyser.fftSize = 1024;
    source.connect(analyser);

    const data = new Uint8Array(analyser.fftSize);
    const readLevel = () => {
      analyser.getByteTimeDomainData(data);
      let peak = 0;
      for (const sample of data) {
        peak = Math.max(peak, Math.abs(sample - 128) / 128);
      }
      activePeakLevel = Math.max(activePeakLevel, peak);
      activeAudioMonitor = window.requestAnimationFrame(readLevel);
    };
    readLevel();
  } catch (error) {
    stopAudioMeter();
  }
}

async function transcribeAudioBlob(blob) {
  const formData = new FormData();
  const extension = blob.type.includes("mp4") ? "m4a" : "webm";
  formData.append("audio", blob, `amane-voice.${extension}`);
  formData.append("language", selectedTranscriptionLanguage());

  const response = await fetch("/api/stt/transcribe", {
    method: "POST",
    body: formData,
  });

  if (!response.ok) throw new Error(await readApiError(response));
  const payload = await response.json();
  return fixDomainTerms(payload.text || "");
}

async function startServerTranscription() {
  if (!navigator.mediaDevices?.getUserMedia || !window.MediaRecorder) return false;

  if (activeRecorder && activeRecorder.state !== "inactive") {
    stopServerRecording();
    return true;
  }

  const stream = await navigator.mediaDevices.getUserMedia({
    audio: { echoCancellation: false, noiseSuppression: false, autoGainControl: true },
  });
  const mimeType = MediaRecorder.isTypeSupported("audio/webm;codecs=opus")
    ? "audio/webm;codecs=opus"
    : MediaRecorder.isTypeSupported("audio/mp4")
      ? "audio/mp4"
      : "";

  activeRecordingStream = stream;
  activeRecordingChunks = [];
  activePeakLevel = 0;
  recordingStartedAt = Date.now();
  startAudioMeter(stream);
  activeRecorder = mimeType ? new MediaRecorder(stream, { mimeType }) : new MediaRecorder(stream);

  activeRecorder.ondataavailable = (event) => {
    if (event.data?.size) activeRecordingChunks.push(event.data);
  };

  activeRecorder.onerror = () => {
    stopAudioMeter();
    activeRecordingStream?.getTracks().forEach((track) => track.stop());
    activeRecordingStream = null;
    isListening = false;
    setVoiceMode("error", "Micro indisponible", "L'enregistrement audio a echoue. Utilise le clavier ou reessaie.");
  };

  activeRecorder.onstop = async () => {
    const chunks = activeRecordingChunks;
    const streamToStop = activeRecordingStream;
    const audioPeak = activePeakLevel;
    const recordingDurationMs = Math.max(0, Date.now() - recordingStartedAt);
    activeRecorder = null;
    activeRecordingStream = null;
    activeRecordingChunks = [];
    activePeakLevel = 0;
    recordingStartedAt = 0;
    stopAudioMeter();
    streamToStop?.getTracks().forEach((track) => track.stop());
    isListening = false;
    micButton?.setAttribute("aria-label", "Parler avec AMANE");

    if (!chunks.length || isProcessingVoice) {
      setVoiceMode(null, "Pret a ecouter", "Clique sur le micro et parle naturellement.");
      return;
    }

    const blob = new Blob(chunks, { type: mimeType || "audio/webm" });
    if (blob.size < MIN_SERVER_STT_AUDIO_BYTES || (recordingDurationMs > 1500 && audioPeak < MIN_SERVER_STT_PEAK_LEVEL)) {
      setVoiceMode("error", "Je n'ai pas bien entendu", "Vérifie que le micro est autorisé, puis réessaie.");
      updateLiveVoice(
        "Voix non détectée",
        "Rapproche-toi du micro, parle clairement, puis clique à nouveau."
      );
      focusKeyboardReply();
      return;
    }

    isProcessingVoice = true;
    setVoiceMode("listening", "Transcription", "AMANE convertit votre voix en texte.");
    updateLiveVoice("Voix reçue", "AMANE prépare la réponse.");

    try {
      const transcript = await transcribeAudioBlob(blob);
      if (!transcript) throw new Error("Aucune parole detectee");
      updateLiveVoice(transcript, "AMANE analyse votre declaration...");
      messageInput.value = transcript;
      await sendMessage(transcript, {
        silentUser: false,
        voice: true,
        source: "openai_audio_transcription",
      });
      messageInput.value = "";
    } catch (error) {
      showApiError(error, "Aucune transcription exploitable");
      focusKeyboardReply();
    } finally {
      isProcessingVoice = false;
    }
  };

  if (activeTtsAudio) {
    activeTtsAudio.pause();
    activeTtsAudio = null;
  }
  window.speechSynthesis?.cancel();
  isAssistantSpeaking = false;
  isListening = true;
  micButton?.setAttribute("aria-label", "Arreter l'ecoute");
  updateLiveVoice("Je vous écoute...", "Parlez naturellement. AMANE s'arrête automatiquement.");
  setVoiceMode("listening", "J'écoute", `Parlez maintenant pendant ${secondsLabel(SERVER_STT_RECORDING_MS)}.`);
  activeRecorder.start(250);
  recordingStopTimer = window.setTimeout(() => stopServerRecording(), SERVER_STT_RECORDING_MS);
  return true;
}

function scheduleRecognitionNoResultTimer() {
  clearRecognitionNoResultTimer();
  recognitionNoResultTimer = window.setTimeout(() => {
    if (!isListening || pendingFinalTranscript.trim() || lastInterimTranscript.trim() || isProcessingVoice) return;
    finishListeningWithoutTranscript("Le navigateur a ouvert le micro, mais n'a pas transforme la parole en texte.");
  }, 10000);
}

function scheduleRecognitionHardStopTimer() {
  clearRecognitionHardStopTimer();
  recognitionHardStopTimer = window.setTimeout(() => {
    if (!isListening || pendingFinalTranscript.trim() || lastInterimTranscript.trim() || isProcessingVoice) return;
    finishListeningWithoutTranscript("Aucun texte final n'a ete recu. Reessaie en parlant plus lentement, ou utilise le champ texte.");
  }, 14000);
}

function scheduleFinalTranscriptFlush() {
  if (speechSettleTimer) window.clearTimeout(speechSettleTimer);
  setVoiceMode("listening", "Je vous \u00e9coute", "AMANE attend 3 secondes avant de r\u00e9pondre.");
  speechSettleTimer = window.setTimeout(() => {
    flushFinalTranscript();
  }, SPEECH_SETTLE_DELAY_MS);
}
async function startListening(event = null) {
  if (event) {
    event.preventDefault();
    event.stopPropagation();
  }
  if (window.AMANE_USE_SERVER_STT === true && activeRecorder && activeRecorder.state !== "inactive") {
    stopServerRecording();
    return;
  }

  if (isAssistantSpeaking || activeTtsAudio || Date.now() < speechCooldownUntil) {
    updateLiveVoice("AMANE parle encore", "Attends la fin de la voix, puis clique sur le micro.");
    setVoiceMode("speaking", "AMANE parle", "\u00c9coute la r\u00e9ponse, puis clique sur le micro.");
    return;
  }

  updateLiveVoice("Clic micro re\u00e7u", "AMANE v\u00e9rifie le micro...");
  setVoiceMode("listening", "Test micro", "Demande d?autorisation du micro en cours.");
  unlockSpeech();

  if (!window.isSecureContext && !["localhost", "127.0.0.1"].includes(window.location.hostname)) {
    openKeyboardFallback("Adresse non s\u00e9curis\u00e9e: le micro mobile exige HTTPS. Utilise ngrok HTTPS ou un h\u00e9bergement permanent.");
    return;
  }

  if (window.AMANE_USE_SERVER_STT === true) {
    try {
      const serverSttStarted = await startServerTranscription();
      if (serverSttStarted) return;
    } catch (error) {
      setVoiceMode("error", "Micro indisponible", `Erreur audio: ${error?.message || error?.name || "inconnue"}. Utilise le champ texte.`);
      updateLiveVoice("Le micro n'a pas demarre", "AMANE attend votre message au clavier.");
      focusKeyboardReply();
      return;
    }
  }

  const micReady = await ensureMicrophoneReady();
  if (!micReady) return;
  updateLiveVoice("Permission micro OK", "AMANE lance la reconnaissance vocale...");

  if (!recognition) {
    openKeyboardFallback("La reconnaissance vocale n'est pas support\u00e9e ici. Sur iPhone, ouvre l'application avec Safari/Chrome en HTTPS, ou utilise le clavier.");
    return;
  }

  if (isListening) {
    recognition.stop();
    if (pendingFinalTranscript.trim()) {
      flushFinalTranscript();
    }
    return;
  }

  if (activeTtsAudio) {
    activeTtsAudio.pause();
    activeTtsAudio = null;
  }
  window.speechSynthesis?.cancel();
  isAssistantSpeaking = false;
  pendingFinalTranscript = "";
  lastInterimTranscript = "";
  clearRecognitionNoResultTimer();
  clearRecognitionHardStopTimer();
  isListening = true;
  micButton?.setAttribute("aria-label", "Arr\u00eater l\u2019\u00e9coute");
  updateLiveVoice("\u00c9coute en cours...", "AMANE attend votre message.");
  setVoiceMode("listening", "J\u2019\u00e9coute", "Parle maintenant. AMANE choisit la meilleure transcription HSE.");
  try {
    recognition.lang = activeSpeechLang;
    recognition.start();
    scheduleRecognitionNoResultTimer();
    scheduleRecognitionHardStopTimer();
  } catch (error) {
    isListening = false;
    clearRecognitionNoResultTimer();
    clearRecognitionHardStopTimer();
    setVoiceMode("error", "Reconnaissance non lanc\u00e9e", `Erreur navigateur: ${error?.message || error?.name || "inconnue"}. Utilise le champ texte.`);
    updateLiveVoice("Le micro n?a pas d\u00e9marr\u00e9", "AMANE attend votre message au clavier.");
    focusKeyboardReply();
  }
}

if (recognition) {
  recognition.onresult = (event) => {
    if (isAssistantSpeaking && !isListening) {
      pendingFinalTranscript = "";
      lastInterimTranscript = "";
      return;
    }
    lastRecognitionResultAt = Date.now();
    clearRecognitionNoResultTimer();
    clearRecognitionHardStopTimer();

    let interimTranscript = "";
    let finalTranscript = "";
    for (let index = event.resultIndex; index < event.results.length; index += 1) {
      const phrase = bestSpeechAlternative(event.results[index]);
      if (event.results[index].isFinal) {
        finalTranscript += ` ${phrase}`;
      } else {
        interimTranscript += ` ${phrase}`;
      }
    }

    if (finalTranscript.trim()) {
      pendingFinalTranscript = `${pendingFinalTranscript} ${finalTranscript}`.trim();
      lastInterimTranscript = "";
      scheduleFinalTranscriptFlush();
    } else if (interimTranscript.trim()) {
      lastInterimTranscript = interimTranscript.trim();
      scheduleFinalTranscriptFlush();
    }

    const visibleTranscript = fixDomainTerms((pendingFinalTranscript || lastInterimTranscript || interimTranscript).trim());
    if (visibleTranscript) {
      updateLiveVoice(
        visibleTranscript,
        pendingFinalTranscript ? "AMANE attend la fin de votre phrase..." : "Transcription en cours..."
      );
    }
  };
  recognition.onerror = (event) => {
    const errorType = event.error || "unknown";
    const justTranscribed = Date.now() - lastRecognitionResultAt < 2500;

    if (isProcessingVoice) return;

    if (["no-speech", "aborted"].includes(errorType) || justTranscribed) {
      if (lastInterimTranscript.trim()) {
        flushFinalTranscript();
        return;
      }
      finishListeningWithoutTranscript("Aucun texte n'a ete recu. Essaie une phrase plus courte ou utilise le champ texte.");
      return;
    }

    if (errorType === "not-allowed") {
      clearRecognitionNoResultTimer();
      clearRecognitionHardStopTimer();
      setVoiceMode("error", "Micro bloqu\u00e9", "Autorise le micro dans le navigateur, puis r\u00e9essaie.");
      updateLiveVoice("", "Le navigateur bloque l\u2019acc\u00e8s au micro.");
      return;
    }

    setVoiceMode(null, "Pr\u00eat \u00e0 \u00e9couter", "Je n\u2019ai pas re\u00e7u de transcription. Clique sur le micro et parle \u00e0 nouveau.");
    updateLiveVoice("En attente de votre voix...", "AMANE affichera ici sa r\u00e9ponse.");
  };

  recognition.onend = () => {
    clearRecognitionNoResultTimer();
    clearRecognitionHardStopTimer();
    if (pendingFinalTranscript.trim() || lastInterimTranscript.trim()) {
      scheduleFinalTranscriptFlush();
    } else if (!isProcessingVoice && !isAssistantSpeaking && !voiceOrb.classList.contains("error")) {
      finishListeningWithoutTranscript("La voix a ete detectee, mais le navigateur n'a pas donne de texte final.");
      return;
    }
    isListening = false;
    micButton?.setAttribute("aria-label", "Parler avec AMANE");
    if (!isProcessingVoice && !voiceOrb.classList.contains("speaking") && !voiceOrb.classList.contains("error")) {
      setVoiceMode(null, "Pr\u00eat \u00e0 \u00e9couter", "Clique sur le micro et r\u00e9ponds \u00e0 voix haute.");
    }
  };
}

async function runDemo() {
  unlockSpeech();

  if (isRunningDemo) return;
  isRunningDemo = true;
  demoButton.disabled = true;
  newSessionButton.disabled = true;
  resetUi({ speakIntro: false });

  try {
    for (const message of demoMessages) {
      await new Promise((resolve) => setTimeout(resolve, 500));
      setVoiceMode("listening", "Simulation voix d\u00e9clarant", message);
      addMessage(message, "user");
      await sendMessage(message, { silentUser: true, voice: true });
    }
  } catch (error) {
    addMessage("Erreur pendant la d\u00e9mo. V\u00e9rifie que l’API et PostgreSQL sont lanc\u00e9s.", "system", true);
  } finally {
    isRunningDemo = false;
    demoButton.disabled = false;
    newSessionButton.disabled = false;
  }
}

chatForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  unlockSpeech();

  const message = fixDomainTerms(messageInput.value.trim());
  if (!message) return;

  messageInput.value = "";
  try {
    await sendMessage(message, { voice: true, source: "keyboard_fallback" });
  } catch (error) {
    addMessage("Erreur API. V\u00e9rifie le backend et la base de donn\u00e9es.", "system", true);
  }
});

conversationToggleButton?.addEventListener("click", () => {
  if (conversationDock.classList.contains("is-open")) {
    closeConversationPanel();
  } else {
    openConversationPanel();
  }
});
conversationCloseButton?.addEventListener("click", closeConversationPanel);
reportToggleButton?.addEventListener("click", () => togglePanel(reportDrawer));
reportCloseButton?.addEventListener("click", closeReportPanel);
languageButtons.forEach((button) => {
  button.addEventListener("click", () => setRecognitionLanguage(button.dataset.speechLang));
});
micButton?.addEventListener("click", startListening);
galleryPhotoButton?.addEventListener("click", () => photoInput?.click());
cameraPhotoButton?.addEventListener("click", () => cameraInput?.click());


async function handleRiskPhotoInput(input) {
  const file = input?.files?.[0];
  if (!file) return;
  try {
    await sendRiskPhoto(file);
  } catch (error) {
    addMessage("Erreur analyse photo. V\u00e9rifie l’API et r\u00e9essaie.", "system", true);
    setVoiceMode("error", "Photo non analys\u00e9e", "La photo n'a pas pu \u00eatre envoy\u00e9e ou analys\u00e9e.");
  } finally {
    input.value = "";
  }
}

photoInput?.addEventListener("change", async () => handleRiskPhotoInput(photoInput));
cameraInput?.addEventListener("change", async () => handleRiskPhotoInput(cameraInput));
repeatButton?.addEventListener("click", () => {
  unlockSpeech();
  speak(lastAssistantText);
});
demoButton?.addEventListener("click", runDemo);
newSessionButton?.addEventListener("click", () => resetUi());
reloadReportsButton?.addEventListener("click", loadReports);
refreshReportsButton?.addEventListener("click", loadReports);

if (window.speechSynthesis) {
  refreshSpeechVoices();
  window.speechSynthesis.onvoiceschanged = refreshSpeechVoices;
}

updateSessionLabel();
renderData({});
renderReports([]);
addMessage(introText, "system");
  updateLiveVoice("", "");
  setVoiceMode(null, "Pr\u00eat \u00e0 \u00e9couter", recognition ? "Clique sur le micro et parle naturellement." : "Reconnaissance vocale non support\u00e9e, utilise le clavier.");
checkApi();
loadReports();






















































