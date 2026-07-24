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
const recognition = SpeechRecognition ?new SpeechRecognition() : null;
let activeSpeechLang = "fr-FR";

if (recognition) {
  recognition.lang = activeSpeechLang;
  recognition.interimResults = true;
  recognition.continuous = true;
  recognition.maxAlternatives = 5;
}

const demoMessages = [
  "bonjour",
  "non",
  "situation dangereuse",
  "Une flaque d'huile est pr?sente pr?s de la ligne de production, avec risque de glissade pour les op?rateurs.",
  "10/07/2026 ? 14:30",
  "Site SONASID Nador, atelier conditionnement, zone convoyeur 2",
  "Aucun nom identifi?",
  "Amine El Fassi",
  "Balisage de la zone et demande de nettoyage imm?diat",
  "Chute de plain-pied, blessure et arr?t de production",
  "oui",
];

const reportSections = [
  {
    title: "Identification",
    fields: [
      ["report_number", "Num?ro de r?clamation"],
      ["declarant", "R?clamant"],
      ["event_datetime", "Date et heure"],
      ["location", "Localisation"],
    ],
  },
  {
    title: "Analyse HSE",
    fields: [
      ["classification", "Type de signalement"],
      ["immediate_danger", "Danger imm?diat"],
      ["observed_person", "Personne observ?e"],
      ["description", "Description"],
      ["risk_analysis", "Risque potentiel"],
    ],
  },
  {
    title: "Traitement",
    fields: [
      ["immediate_action", "Action imm?diate"],
      ["recommended_action", "Action recommand?e IA"],
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
let speechSettleTimer = null;
const SPEECH_SETTLE_DELAY_MS = 3000;
let speechVoices = [];
let speechUnlocked = false;
let activeTtsAudio = null;
const introText = "Bonjour. Je suis AMANE, votre assistant vocal HSE. Parlez naturellement pour dÃ©clarer une situation HSE.";
let lastAssistantText = introText;

function createSessionId() {
  return `voice-${Math.random().toString(16).slice(2, 10)}`;
}

function cleanDisplayText(text) {
  let value = String(text ?? "");
  const replacements = [
    ["\u00C3\u0192\u00C2\u00A9", "\u00E9"],
    ["\u00C3\u0192\u00C2\u00A8", "\u00E8"],
    ["\u00C3\u0192\u00C2\u00AA", "\u00EA"],
    ["\u00C3\u0192\u00C2\u00AB", "\u00EB"],
    ["\u00C3\u0192 ", "\u00E0"],
    ["\u00C3\u0192\u00C2\u00A0", "\u00E0"],
    ["\u00C3\u0192\u00C2\u00A2", "\u00E2"],
    ["\u00C3\u0192\u00C2\u00AE", "\u00EE"],
    ["\u00C3\u0192\u00C2\u00AF", "\u00EF"],
    ["\u00C3\u0192\u00C2\u00B4", "\u00F4"],
    ["\u00C3\u0192\u00C2\u00B9", "\u00F9"],
    ["\u00C3\u0192\u00C2\u00BB", "\u00FB"],
    ["\u00C3\u0192\u00C2\u00A7", "\u00E7"],
    ["\u00C3\u00A9", "\u00E9"],
    ["\u00C3\u00A8", "\u00E8"],
    ["\u00C3\u00AA", "\u00EA"],
    ["\u00C3\u00AB", "\u00EB"],
    ["\u00C3 ", "\u00E0"],
    ["\u00C3\u00A0", "\u00E0"],
    ["\u00C3\u00A2", "\u00E2"],
    ["\u00C3\u00AE", "\u00EE"],
    ["\u00C3\u00AF", "\u00EF"],
    ["\u00C3\u00B4", "\u00F4"],
    ["\u00C3\u00B9", "\u00F9"],
    ["\u00C3\u00BB", "\u00FB"],
    ["\u00C3\u00A7", "\u00E7"],
    ["\u00C3\u2030", "\u00C9"],
    ["\u00C3\u20AC", "\u00C0"],
    ["\u00E2\u20AC\u2122", "'"],
    ["\u00E2\u20AC\u0153", "\""],
    ["\u00E2\u20AC\u009D", "\""],
    ["\u00E2\u20AC\u201C", "-"],
    ["\u00E2\u20AC\u201D", "-"],
    ["\u00C2\u00B7", "\u00B7"],
    ["\u00C2", ""]
  ];
  for (const [source, target] of replacements) {
    value = value.split(source).join(target);
  }
  return value;
}
function stripDiacritics(text) {
  return String(text || "")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "");
}

function normalizeSpeechSpacing(text) {
  return String(text || "")
    .replace(/\s+/g, " ")
    .replace(/\s+([,.!?;:])/g, "$1")
    .trim();
}


function fixAssistantNameVocative(text) {
  return String(text || "")
    .replace(/\b(bonjour|salut|salam|salem|hello|hey)\s+(?:ahmed|ahmad|amal|amel|amina|amine|amen|amene|aman)\b/gi, "$1 AMANE")
    .replace(/\b(?:ahmed|ahmad|amal|amel|amina|amine|amen|amene|aman)\s*,?\s+(?:bonjour|salam|salem|hello)\b/gi, "AMANE bonjour")
    .replace(/\b(?:hey|ok|allo)\s+(?:ahmed|ahmad|amal|amel|amina|amine|amen|amene|aman)\b/gi, "$1 AMANE")
    .replace(/\b(?:parle|reponds|rÃ©ponds|ecoute|Ã©coute)\s+(?:ahmed|ahmad|amal|amel|amina|amine|amen|amene|aman)\b/gi, "$1 AMANE");
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
    [/\b(?:site|cite|citer)\s+son\s*(?:acid|acide|asid|aside)\s+n(?:\s+)?adore\b/gi, "Site SONASID Nador"],
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
  ];  for (const [pattern, replacement] of replacements) {
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
  let best = result[0]?.transcript || "";
  let bestScore = speechCandidateScore(best) + ((result[0]?.confidence || 0) * 2);
  for (let i = 1; i < result.length; i += 1) {
    const candidate = result[i]?.transcript || "";
    const score = speechCandidateScore(candidate) + ((result[i]?.confidence || 0) * 2);
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
    const stream = await navigator.mediaDevices.getUserMedia({
      audio: { echoCancellation: true, noiseSuppression: true, autoGainControl: true },
    });
    stream.getTracks().forEach((track) => track.stop());
    return true;
  } catch (error) {
    setVoiceMode("error", "Micro bloque", "Autorise le micro dans le navigateur. Sur telephone, utilise une URL HTTPS.");
    updateLiveVoice("", "Le micro est refuse ou indisponible sur ce navigateur.");
    return false;
  }
}

function updateSessionLabel() {
  sessionLabel.textContent = sessionId;
}

function togglePanel(panel, forceOpen) {
  if (!panel) return;
  const shouldOpen = typeof forceOpen === "boolean" ?forceOpen : !panel.classList.contains("is-open");
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
  window.setTimeout(() => messageInput.focus(), 80);
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
    assistantReplyPreview.textContent = cleanDisplayText(reply || "AMANE affichera ici sa rÃ©ponse.");
  }
}
function refreshSpeechVoices() {
  if (!window.speechSynthesis) return;
  speechVoices = window.speechSynthesis.getVoices();
}

function containsArabicScript(text) {
  return /[\u0600-\u06ff]/.test(text || "");
}

function applySpeechPronunciation(text, lang = "fr-FR") {
  let value = String(text || "");
  if (lang.startsWith("ar")) {
    return value
      .replace(/AMANE AI/g, "\u0623\u0645\u0627\u0646")
      .replace(/AMANE/g, "\u0623\u0645\u0627\u0646")
      .replace(/HSE/g, "\u0625\u062a\u0634 \u0625\u0633 \u0625\u064a")
      .replace(/SONASID/g, "\u0633\u0648\u0646\u0627\u0633\u064a\u062f");
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
    value = value.replace(new RegExp(source.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"), "gi"), target);
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
  if (containsArabicScript(text)) {
    return applySpeechPronunciation(text, "ar-MA");
  }
  if (isDarijaText(text)) {
    return latinDarijaToArabicSpeech(text);
  }
  return applySpeechPronunciation(text, lang);
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
    "niveau", "resume", "observes", "prevention", "mesures", "chantier",
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
  if (activeSpeechLang === "ar-MA") return "darija";
  if (activeSpeechLang === "en-US") return "en";
  return "fr";
}

function pickVoice(lang) {
  refreshSpeechVoices();
  if (speechVoices.length === 0) return null;

  const baseLang = lang.split("-")[0];
  return (
    speechVoices.find((voice) => voice.lang.toLowerCase() === lang.toLowerCase()) ||
    speechVoices.find((voice) => voice.lang.toLowerCase().startsWith(`${baseLang}-`)) ||
    speechVoices.find((voice) => voice.default) ||
    speechVoices[0]
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
        setVoiceMode("speaking", "AMANE parle", "Ã‰coute la rÃ©ponse, puis clique sur le micro.");
      };
      audio.onended = () => {
        isAssistantSpeaking = false;
        activeTtsAudio = null;
        URL.revokeObjectURL(audioUrl);
        setVoiceMode(null, "PrÃªt Ã  Ã©couter", "Clique sur le micro et rÃ©ponds Ã  voix haute.");
        resolve();
      };
      audio.onerror = () => {
        isAssistantSpeaking = false;
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
  if (!recognition) return;
  pendingFinalTranscript = "";
  if (speechSettleTimer) {
    window.clearTimeout(speechSettleTimer);
    speechSettleTimer = null;
  }
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
    setVoiceMode("error", "Voix indisponible", "Votre navigateur ne prend pas en charge la synthese vocale.");
    return;
  }

  refreshSpeechVoices();
  stopRecognitionWhileSpeaking();
  window.speechSynthesis.cancel();

  const lang = forcedLang || getSpeechLang(text);
  const spokenText = prepareSpeechText(text, lang);
  const utterance = new SpeechSynthesisUtterance(spokenText);
  utterance.lang = lang;
  utterance.rate = lang.startsWith("ar") ? 0.9 : 0.98;
  utterance.pitch = 1;
  utterance.volume = 1;

  const selectedVoice = pickVoice(lang);
  if (selectedVoice) utterance.voice = selectedVoice;

  utterance.onstart = () => {
    isAssistantSpeaking = true;
    setVoiceMode("speaking", "AMANE parle", "Ã‰coute la rÃ©ponse, puis clique sur le micro.");
  };
  utterance.onend = () => {
    isAssistantSpeaking = false;
    setVoiceMode(null, "PrÃªt Ã  Ã©couter", "Clique sur le micro et rÃ©ponds Ã  voix haute.");
  };
  utterance.onerror = () => {
    isAssistantSpeaking = false;
    setVoiceMode("error", "Voix bloquÃ©e", "Clique sur RÃ©pÃ©ter ou vÃ©rifie le volume du navigateur.");
  };

  window.speechSynthesis.speak(utterance);
  window.speechSynthesis.resume();
}

function addMessage(text, type = "system", isEmergency = false) {
  const node = document.createElement("div");
  node.className = `message ${type}${isEmergency ?" emergency" : ""}`;
  node.dir = "auto";
  node.textContent = cleanDisplayText(text);
  messagesEl.appendChild(node);
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

function formatValue(value) {
  if (value === true) return "Oui";
  if (value === false) return "Non";
  if (value === null || value === undefined || value === "") return "Non renseignÃ©";
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
    empty.textContent = "Les informations du rapport se remplissent pendant l'ÃƒÂ©change vocal.";
    dataList.appendChild(empty);
    return;
  }

  const summary = document.createElement("div");
  summary.className = "report-summary";

  const reportNumber = document.createElement("strong");
  reportNumber.textContent = data.report_number || "RÃƒÂ©clamation en cours";

  const summaryMeta = document.createElement("span");
  summaryMeta.textContent = `${formatValue(data.classification)} Ã‚Â· ${formatValue(data.declarant)}`;

  const badgeRow = document.createElement("div");
  badgeRow.className = "report-badges";

  const statusBadge = document.createElement("span");
  statusBadge.className = "table-badge";
  statusBadge.textContent = statusLabel(data.status || (data.report_number ? "enregistrÃ©" : "en cours"));

  const dangerBadge = document.createElement("span");
  dangerBadge.className = `table-badge ${data.immediate_danger ?"danger" : "ok"}`;
  dangerBadge.textContent = data.immediate_danger ? "Danger immÃƒÂ©diat" : "Sans urgence immÃƒÂ©diate";

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
      detail.textContent = key === "status" ?statusLabel(data[key]) : formatValue(data[key]);

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
    empty.textContent = "Aucun rapport sauvegardÃƒÂ© pour le moment.";
    reportsList.appendChild(empty);
    return;
  }

  const table = document.createElement("table");
  table.className = "saved-reports-table";
  table.innerHTML = `
    <thead>
      <tr>
        <th>NumÃƒÂ©ro</th>
        <th>RÃƒÂ©clamant</th>
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
    apiStatus.textContent = "API connectÃƒÂ©e";
    apiHint.textContent = "FastAPI rÃ©pond";
  } catch (error) {
    apiDot.className = "status-dot offline";
    apiStatus.textContent = "API hors ligne";
    apiHint.textContent = "VÃƒÂ©rifier uvicorn";
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
  const detail = error?.message || "Erreur inconnue.";
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
  const questions = payload?.vision?.questions;
  if (Array.isArray(questions)) {
    const question = questions.find((item) => String(item || "").trim());
    if (question) return String(question).trim();
  }

  const response = String(payload?.response || "");
  const match = response.match(/(?:Question AMANE|AMANE question|\u0633\u0624\u0627\u0644 AMANE)\s*:\s*([^\n]+)/i);
  if (match?.[1]) return match[1].trim();

  const language = selectedPhotoAnalysisLanguage();
  if (language === "fr") return "Confirmez-vous cette analyse photo HSE ?";
  if (language === "en") return "Do you confirm this HSE photo analysis?";
  return "\u0647\u0644 \u062a\u0624\u0643\u062f \u0647\u0630\u0627 \u0627\u0644\u062a\u062d\u0644\u064a\u0644 \u0627\u0644\u062e\u0627\u0635 \u0628\u0635\u0648\u0631\u0629 HSE\u061f";
}

function selectedPhotoAnalysisLanguage() {
  return analysisLanguageSelect?.value || "ar";
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
      user: "Photo de risque envoyee a AMANE.",
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
  if (!file || !file.type?.startsWith("image/")) return file;
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
    throw new Error(text || "Erreur analyse photo");
  }

  const payload = await response.json();
  stepPill.textContent = payload.step;
  completionBadge.textContent = payload.completed ? "TerminÃƒÂ©" : "En cours";
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
  updateLiveVoice(cleanMessage, "AMANE analyse votre dÃƒÂ©claration...");
  if (!silentUser) addMessage(cleanMessage, "user");

  const response = await fetch("/api/voice/message", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      session_id: sessionId,
      transcript: cleanMessage,
      source: source || (recognition ?"browser_speech_recognition" : "keyboard_fallback"),
      preferred_language: selectedConversationLanguage(),
    }),
  });

  if (!response.ok) {
    throw new Error(await readApiError(response));
  }

  const payload = await response.json();
  stepPill.textContent = payload.step;
  completionBadge.textContent = payload.completed ? "TerminÃƒÂ©" : "En cours";
  completionBadge.classList.toggle("done", payload.completed);
  addMessage(payload.response, "system", payload.emergency);
  updateLiveVoice(cleanMessage, payload.response);
  renderData(payload.collected_data);

  if (voice) speak(payload.response);

  if (payload.completed) {
    setVoiceMode(null, "DÃ©claration enregistrÃ©e", "Merci. La rÃ©clamation est transmise Ã  l'Ã©quipe HSE.");
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
  setVoiceMode(null, "PrÃªt Ã  Ã©couter", recognition ? "Clique sur le micro et parle naturellement." : "Reconnaissance vocale non supportÃ©e, utilise le clavier.");
  if (speakIntro) speak(introText);
}

async function flushFinalTranscript() {
  const transcript = fixDomainTerms(pendingFinalTranscript.trim());
  pendingFinalTranscript = "";
  speechSettleTimer = null;

  if (!transcript || isProcessingVoice) return;

  isProcessingVoice = true;
  setVoiceMode(null, "Voix transcrite", "Texte reÃ§u, AMANE prÃ©pare sa rÃ©ponse.");
  updateLiveVoice(transcript, "AMANE analyse votre dÃ©claration...");
  addMessage(transcript, "user");
  messageInput.value = transcript;

  try {
    await sendMessage(transcript, { silentUser: true, voice: true });
    messageInput.value = "";
  } catch (error) {
    updateLiveVoice(transcript, "Erreur API. VÃ©rifie le backend et la base de donnÃ©es.");
    addMessage("Erreur API. VÃ©rifie le backend et la base de donnÃ©es.", "system", true);
    setVoiceMode("error", "Erreur API", "Le texte est affichÃ©, mais l'envoi a Ã©chouÃ©.");
  } finally {
    isProcessingVoice = false;
  }
}

function scheduleFinalTranscriptFlush() {
  if (speechSettleTimer) window.clearTimeout(speechSettleTimer);
  setVoiceMode("listening", "Je vous ecoute", "AMANE attend 3 secondes avant de repondre.");
  speechSettleTimer = window.setTimeout(() => {
    flushFinalTranscript();
  }, SPEECH_SETTLE_DELAY_MS);
}
async function startListening() {
  unlockSpeech();

  if (!recognition) {
    openKeyboardFallback("La reconnaissance vocale n'est pas supportÃ©e ici. Sur iPhone, ouvre l'application avec Safari/Chrome en HTTPS, ou utilise le clavier.");
    return;
  }

  if (!window.isSecureContext && !["localhost", "127.0.0.1"].includes(window.location.hostname)) {
    openKeyboardFallback("Adresse non sÃ©curisÃ©e: le micro mobile exige HTTPS. Utilise ngrok HTTPS ou un hÃ©bergement permanent.");
    return;
  }

  const micReady = await ensureMicrophoneReady();
  if (!micReady) return;

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
  pendingFinalTranscript = "";
  isListening = true;
  micButton.setAttribute("aria-label", "Arreter l'ecoute");
  updateLiveVoice("Ecoute en cours...", "AMANE attend votre message.");
  setVoiceMode("listening", "J'ecoute", "Parle maintenant. AMANE choisit la meilleure transcription HSE.");
  try {
    recognition.lang = activeSpeechLang;
    recognition.start();
  } catch (error) {
    isListening = false;
    setVoiceMode("error", "Micro deja actif", "Attends une seconde puis reclique sur le micro.");
  }
}

if (recognition) {
  recognition.onresult = (event) => {
    if (isAssistantSpeaking) {
      pendingFinalTranscript = "";
      return;
    }
    lastRecognitionResultAt = Date.now();

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
      scheduleFinalTranscriptFlush();
    }

    const visibleTranscript = fixDomainTerms((pendingFinalTranscript || interimTranscript).trim());
    if (visibleTranscript) {
      updateLiveVoice(
        visibleTranscript,
        pendingFinalTranscript ?"AMANE attend la fin de votre phrase..." : "Transcription en cours..."
      );
    }
  };
  recognition.onerror = (event) => {
    const errorType = event?.error || "unknown";
    const justTranscribed = Date.now() - lastRecognitionResultAt < 2500;

    if (isProcessingVoice) return;

    if (["no-speech", "aborted"].includes(errorType) || justTranscribed) {
      isListening = false;
      micButton.setAttribute("aria-label", "Parler avec AMANE");
      if (!voiceOrb.classList.contains("speaking")) {
        setVoiceMode(null, "PrÃªt Ã  Ã©couter", "Clique sur le micro et parle naturellement.");
      }
      return;
    }

    if (errorType === "not-allowed") {
      setVoiceMode("error", "Micro bloquÃ©", "Autorise le micro dans le navigateur, puis rÃ©essaie.");
      updateLiveVoice("", "Le navigateur bloque l'accÃ¨s au micro.");
      return;
    }

    setVoiceMode(null, "PrÃªt Ã  Ã©couter", "Je n'ai pas reÃ§u de transcription. Clique sur le micro et parle Ã  nouveau.");
    updateLiveVoice("En attente de votre voix...", "AMANE affichera ici sa rÃ©ponse.");
  };

  recognition.onend = () => {
    if (pendingFinalTranscript.trim()) {
      scheduleFinalTranscriptFlush();
    }
    isListening = false;
    micButton.setAttribute("aria-label", "Parler avec AMANE");
    if (!isProcessingVoice && !voiceOrb.classList.contains("speaking") && !voiceOrb.classList.contains("error")) {
      setVoiceMode(null, "PrÃªt Ã  Ã©couter", "Clique sur le micro et rÃ©ponds Ã  voix haute.");
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
      setVoiceMode("listening", "Simulation voix dÃƒÂ©clarant", message);
      addMessage(message, "user");
      await sendMessage(message, { silentUser: true, voice: true });
    }
  } catch (error) {
    addMessage("Erreur pendant la dÃƒÂ©mo. VÃƒÂ©rifie que l'API et PostgreSQL sont lancÃƒÂ©s.", "system", true);
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
    addMessage("Erreur API. VÃ©rifie le backend et la base de donnÃ©es.", "system", true);
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
    addMessage("Erreur analyse photo. Verifie l API et reessaie.", "system", true);
    setVoiceMode("error", "Photo non analysee", "La photo n a pas pu etre envoyee ou analysee.");
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
  setVoiceMode(null, "PrÃªt Ã  Ã©couter", recognition ? "Clique sur le micro et parle naturellement." : "Reconnaissance vocale non supportÃ©e, utilise le clavier.");
checkApi();
loadReports();






















































