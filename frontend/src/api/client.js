export const AGENCY_STYLES = {
  CITY_OF_ATHENS: { shortLabel: 'Δήμος', fullLabel: 'Δήμος Αθηναίων', bg: 'bg-sky-500/15', border: 'border-sky-400/50', text: 'text-sky-200', strokeColor: '#38bdf8', badgeBg: '#0284c7' },
  EYDAP: { shortLabel: 'ΕΥΔΑΠ', fullLabel: 'ΕΥΔΑΠ', bg: 'bg-cyan-500/15', border: 'border-cyan-400/50', text: 'text-cyan-200', strokeColor: '#22d3ee', badgeBg: '#0891b2' },
  DEDDIE: { shortLabel: 'ΔΕΔΔΗΕ', fullLabel: 'ΔΕΔΔΗΕ', bg: 'bg-amber-500/15', border: 'border-amber-400/50', text: 'text-amber-200', strokeColor: '#f59e0b', badgeBg: '#d97706' },
  REGION_OF_ATTICA: { shortLabel: 'Περιφέρεια', fullLabel: 'Περιφέρεια Αττικής', bg: 'bg-purple-500/15', border: 'border-purple-400/50', text: 'text-purple-200', strokeColor: '#c084fc', badgeBg: '#9333ea' },
  OASA: { shortLabel: 'ΟΑΣΑ', fullLabel: 'ΟΑΣΑ', bg: 'bg-emerald-500/15', border: 'border-emerald-400/50', text: 'text-emerald-200', strokeColor: '#34d399', badgeBg: '#059669' },
  KEP_MITOS: { shortLabel: 'ΚΕΠ / Μίτος', fullLabel: 'ΚΕΠ / Μίτος', bg: 'bg-rose-500/15', border: 'border-rose-400/50', text: 'text-rose-200', strokeColor: '#fb7185', badgeBg: '#e11d48' },
};

export const AGENCY_ORDER = ['CITY_OF_ATHENS', 'EYDAP', 'DEDDIE', 'REGION_OF_ATTICA', 'OASA', 'KEP_MITOS'];

export const CITIZEN_APPS = [
  { agency: 'CITY_OF_ATHENS', app: 'Novoville', hint: 'Δήμος' },
  { agency: 'EYDAP', app: 'EydApp', hint: 'ύδρευση' },
  { agency: 'DEDDIE', app: 'MyDEDDIE', hint: 'ρεύμα' },
  { agency: 'REGION_OF_ATTICA', app: 'Περιφέρεια', hint: 'λεωφόροι' },
];

export const PIPELINE_AGENTS = [
  { n: 1, short: 'Εντοπισμός', name: 'Vision Triage', detail: 'Πολλαπλές βλάβες σε ένα κάδρο' },
  { n: 2, short: 'Αρμοδιότητα', name: 'GIS & OSM', detail: 'Οδός, κοινότητα, κανόνας Αθήνας' },
  { n: 3, short: 'SLA', name: 'OASA & SLA', detail: 'Στάσεις και ευαίσθητα σημεία' },
  { n: 4, short: 'Μίτος', name: 'Μίτος', detail: 'Διαδικασίες και δικαιολογητικά' },
  { n: 5, short: 'Έλεγχος', name: 'Critic', detail: 'Συνοχή, γεωγραφία, Open311' },
  { n: 6, short: 'Απόφαση', name: 'Decision', detail: 'Webhooks και ενιαία απόδειξη' },
];

export const URGENCY_LABELS = {
  LOW: 'Χαμηλή',
  MEDIUM: 'Μέτρια',
  HIGH_VULNERABLE_ZONE: 'Ευάλωτη ζώνη',
  HIGH_CRITICAL_TRANSIT_HUB: 'Κόμβος ΟΑΣΑ',
  CRITICAL_SAFETY_HAZARD: 'Κρίσιμη ασφάλεια',
};

export const HAZARD_LABELS = {
  BROKEN_SIDEWALK: 'Πεζοδρόμιο',
  ROAD_POTHOLE: 'Λακκούβα',
  WATER_LEAK_MANHOLE: 'Φρεάτιο / διαρροή',
  SEWAGE_OVERFLOW: 'Λύματα',
  STREETLIGHT_OUTAGE: 'Φωτισμός',
  EXPOSED_POWER_CABLE: 'Εκτεθειμένο καλώδιο',
  TRAFFIC_SIGNAL_FAULT: 'Φωτεινός σηματοδότης',
  ABANDONED_VEHICLE: 'Εγκαταλελειμμένο όχημα',
  ILLEGAL_DUMPING_BULKY: 'Ογκώδη απορρίμματα',
  DAMAGED_BUS_STOP: 'Στάση',
  FALLEN_TREE_BRANCH: 'Κλαδί',
  ACCESSIBILITY_RAMP_BLOCKED: 'Προσβασιμότητα',
  ADMINISTRATIVE_QUERY: 'Διοικητικό αίτημα',
};

export function agencyStyle(code) {
  return AGENCY_STYLES[code] || AGENCY_STYLES.CITY_OF_ATHENS;
}

export function formatDuration(ms) {
  if (ms == null || Number.isNaN(Number(ms))) return '—';
  const n = Number(ms);
  if (n < 1000) return `${n} ms`;
  return `${(n / 1000).toFixed(n >= 10000 ? 0 : 1)} s`;
}

export function formatWhen(iso) {
  if (!iso) return '';
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return '';
  return date.toLocaleString('el-GR', {
    day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit',
  });
}

export function urgencyLabel(code) {
  return URGENCY_LABELS[code] || code || '—';
}

export function ticketCoords(ticket) {
  const payload = ticket?.payload_sent || {};
  const lat = Number(payload.lat ?? payload.latitude ?? ticket?.latitude);
  const lon = Number(payload.long ?? payload.lng ?? payload.longitude ?? ticket?.longitude);
  if (!Number.isFinite(lat) || !Number.isFinite(lon)) return null;
  if (Math.abs(lat) < 1 || Math.abs(lon) < 1) return null;
  return { lat, lon };
}

export async function fetchHealth() {
  const r = await fetch('/api/health');
  if (!r.ok) throw new Error('Ο διακομιστής δεν απαντά');
  return r.json();
}

export async function fetchDemoPresets() {
  const r = await fetch('/api/presets');
  if (!r.ok) throw new Error('Τα σενάρια demo δεν φορτώθηκαν');
  const d = await r.json();
  return d.presets || [];
}

export async function fetchExecutiveDashboard() {
  const r = await fetch('/api/executive/dashboard');
  if (!r.ok) throw new Error('Το executive dashboard δεν φορτώθηκε');
  return r.json();
}

export async function requestExecutiveAiBriefing(key) {
  const r = await fetch('/api/executive/ai-briefing', {
    method: 'POST',
    headers: key ? { 'X-Llm-Api-Key': key } : {},
  });
  if (!r.ok) {
    const detail = await readError(r);
    throw new Error(detail);
  }
  return r.json();
}

async function readError(res) {
  try {
    const data = await res.json();
    if (typeof data?.detail === 'string') return data.detail;
    if (Array.isArray(data?.detail)) return data.detail.map((d) => d.msg || d).join(' ');
  } catch { /* response was not JSON */ }
  return 'Η κλήση απέτυχε';
}

export async function streamIncidentPipeline({
  citizenComment, latitude, longitude, presetId, imageFile, geminiApiKey,
  onAgentStart, onAgentComplete, onPipelineComplete, onError,
}) {
  const fd = new FormData();
  fd.append('citizen_comment', citizenComment || '');
  fd.append('latitude', String(latitude));
  fd.append('longitude', String(longitude));
  if (presetId && !imageFile) fd.append('preset_id', presetId);
  if (imageFile) fd.append('image', imageFile);

  const res = await fetch('/api/incidents/stream', {
    method: 'POST',
    headers: geminiApiKey ? { 'X-Llm-Api-Key': geminiApiKey } : {},
    body: fd,
  });
  if (!res.ok) throw new Error(await readError(res));
  if (!res.body) throw new Error('Ο browser δεν έλαβε ροή SSE');

  const reader = res.body.getReader();
  const decoder = new TextDecoder('utf-8');
  let buffer = '';
  let finished = false;

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const blocks = buffer.split(/\r?\n\r?\n/);
    buffer = blocks.pop() || '';

    for (const block of blocks) {
      if (!block.trim()) continue;
      let evType = 'message';
      let dataStr = '';
      for (const line of block.split(/\r?\n/)) {
        if (line.startsWith('event:')) evType = line.slice(6).trim();
        else if (line.startsWith('data:')) dataStr += line.slice(5).trim();
      }
      if (!dataStr) continue;
      let parsed;
      try { parsed = JSON.parse(dataStr); } catch { continue; }
      if (evType === 'agent_start' && onAgentStart) onAgentStart(parsed);
      else if (evType === 'agent_complete' && onAgentComplete) onAgentComplete(parsed);
      else if (evType === 'pipeline_complete' && onPipelineComplete) {
        finished = true;
        onPipelineComplete(parsed);
      } else if (evType === 'error' && onError) onError(parsed);
    }
  }

  if (!finished) throw new Error('Η ροή έκλεισε πριν εκδοθεί η ενιαία απόδειξη.');
}
