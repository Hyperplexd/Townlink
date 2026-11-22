import React, { useEffect, useState } from 'react';
import { KeyRound, LayoutDashboard, Radio, Smartphone } from 'lucide-react';
import CityOnMobileEmulator from './components/CityOnMobileEmulator';
import AgentControlRoom from './components/AgentControlRoom';
import ExecutiveDashboard from './components/ExecutiveDashboard';
import { CITIZEN_APPS, PIPELINE_AGENTS, fetchDemoPresets, fetchHealth, formatDuration, streamIncidentPipeline } from './api/client';

function Mark() {
  return (
    <svg viewBox="0 0 36 36" className="h-8 w-8 shrink-0" aria-hidden="true">
      <rect width="36" height="36" rx="10" fill="#0a4d82" />
      <path d="M7 23.5h22" stroke="#e4c36a" strokeWidth="1.6" />
      <path d="M9 23.5c.4-6.2 4.2-10 9-10s8.6 3.8 9 10" fill="none" stroke="#f4efe6" strokeWidth="1.6" />
      <circle cx="18" cy="13.2" r="1.5" fill="#e4c36a" />
    </svg>
  );
}

export default function App() {
  const [tab, setTab] = useState('studio');
  const [apiKey, setApiKey] = useState(() => localStorage.getItem('KEY') || '');
  const [draftKey, setDraftKey] = useState(() => localStorage.getItem('KEY') || '');
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [health, setHealth] = useState(null);
  const [presets, setPresets] = useState([]);
  const [presetId, setPresetId] = useState('');
  const [comment, setComment] = useState('');
  const [lat, setLat] = useState(37.981969);
  const [lon, setLon] = useState(23.732121);
  const [locationLabel, setLocationLabel] = useState('');
  const [preview, setPreview] = useState('');
  const [imageFile, setImageFile] = useState(null);
  const [running, setRunning] = useState(false);
  const [elapsed, setElapsed] = useState(0);
  const [activeAgents, setActiveAgents] = useState({});
  const [traces, setTraces] = useState([]);
  const [report, setReport] = useState(null);
  const [history, setHistory] = useState([]);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchDemoPresets()
      .then((list) => {
        setPresets(list);
        if (list.length) applyPreset(list[0]);
      })
      .catch((err) => setError(err.message));
    fetchHealth().then(setHealth).catch(() => setHealth({ status: 'down' }));
  }, []);

  useEffect(() => {
    if (!running) return undefined;
    const started = Date.now();
    setElapsed(0);
    const id = setInterval(() => setElapsed(Date.now() - started), 200);
    return () => clearInterval(id);
  }, [running]);

  const replacePreview = (url) => {
    setPreview((current) => {
      if (current && current.startsWith('blob:')) URL.revokeObjectURL(current);
      return url;
    });
  };

  const applyPreset = (preset) => {
    setPresetId(preset.id);
    setComment(preset.citizen_comment || '');
    setLat(preset.latitude);
    setLon(preset.longitude);
    setLocationLabel(preset.location_label_el || '');
    setImageFile(null);
    replacePreview(preset.image_data_url || '');
    setReport(null);
    setTraces([]);
    setActiveAgents({});
    setError('');
  };

  const uploadImage = (file) => {
    setImageFile(file);
    setPresetId('');
    replacePreview(URL.createObjectURL(file));
    setReport(null);
    setTraces([]);
    setActiveAgents({});
    setError('');
  };

  const recallReport = (saved) => {
    setReport(saved);
    setTraces(saved.agent_traces || []);
    setActiveAgents({});
    setComment(saved.citizen_comment || '');
    setLat(saved.latitude);
    setLon(saved.longitude);
    setLocationLabel(saved.geo_output?.formatted_address_el || '');
    setImageFile(null);
    if (saved.image_data_url) replacePreview(saved.image_data_url);
    setError('');
  };

  const run = async () => {
    setRunning(true);
    setError('');
    setTraces([]);
    setReport(null);
    setActiveAgents({});
    try {
      await streamIncidentPipeline({
        citizenComment: comment,
        latitude: Number(lat),
        longitude: Number(lon),
        presetId,
        imageFile,
        geminiApiKey: apiKey,
        onAgentStart: (event) => setActiveAgents((prev) => ({ ...prev, [event.agent_number]: event.message_el })),
        onAgentComplete: (trace) => setTraces((prev) => [...prev.filter((item) => item.agent_number !== trace.agent_number), trace].sort((a, b) => a.agent_number - b.agent_number)),
        onPipelineComplete: (next) => {
          setReport(next);
          setHistory((prev) => [next, ...prev.filter((item) => item.report_id !== next.report_id)].slice(0, 6));
        },
        onError: (err) => setError(err.message || 'Σφάλμα ροής'),
      });
    } catch (err) {
      setError(err.message || 'Η αποστολή δεν ολοκληρώθηκε');
    } finally {
      setRunning(false);
    }
  };

  const llmReady = Boolean(apiKey) || Boolean(health?.llm_api_key_configured) || Boolean(health?.gemini_api_key_configured);
  const providerName = health?.llm_provider === 'openrouter' ? 'OpenRouter' : 'Gemini';
  const doneCount = traces.length;

  const saveKey = () => {
    const next = draftKey.trim();
    setApiKey(next);
    if (next) localStorage.setItem('KEY', next);
    else localStorage.removeItem('KEY');
    setSettingsOpen(false);
  };

  const studioLocked = tab === 'studio';

  return (
    <div className={`flex min-h-screen flex-col ${studioLocked ? 'xl:h-dvh xl:overflow-hidden' : ''}`}>
      <header className="z-30 shrink-0 border-b border-white/10 bg-ink-950/80 backdrop-blur-md">
        <div className="mx-auto flex w-full max-w-[1920px] flex-wrap items-center gap-3 px-3 py-2 lg:px-4">
          <Mark />
          <div className="mr-auto min-w-[200px]">
            <div className="font-serif text-lg leading-none text-white">TownLink</div>
            <div className="mt-0.5 text-[11px] text-white/50">Πλατφόρμα Διακλαδικής Διαλειτουργικότητας & Έξυπνης Δρομολόγησης</div>
          </div>
          <button
            type="button"
            onClick={() => { setDraftKey(apiKey); setSettingsOpen((open) => !open); }}
            className={`inline-flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-xs font-bold ${llmReady ? 'border-emerald-400/30 text-emerald-200' : 'border-rose-400/40 text-rose-200'}`}
          >
            <Radio className="h-3.5 w-3.5" />
            {health?.status === 'down' ? 'Backend εκτός' : llmReady ? `${providerName} έτοιμο` : 'Χωρίς κλειδί'}
          </button>
          <div className="flex rounded-full border border-white/10 bg-black/30 p-1">
            <button type="button" onClick={() => setTab('studio')} className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 text-xs font-bold ${tab === 'studio' ? 'bg-white text-ink-950' : 'text-white/60 hover:text-white'}`}>
              <Smartphone className="h-3.5 w-3.5" /> Studio
            </button>
            <button type="button" onClick={() => setTab('executive')} className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 text-xs font-bold ${tab === 'executive' ? 'bg-white text-ink-950' : 'text-white/60 hover:text-white'}`}>
              <LayoutDashboard className="h-3.5 w-3.5" /> Executive
            </button>
          </div>
        </div>
        {settingsOpen && (
          <div className="mx-auto w-full max-w-[1920px] px-3 pb-2 lg:px-4">
            <div className="ops-panel flex flex-wrap items-end gap-2 p-3">
              <label className="min-w-[240px] flex-1 text-xs text-white/60">
                Προαιρετικό κλειδί συνεδρίας
                <input
                  type="password"
                  value={draftKey}
                  onChange={(event) => setDraftKey(event.target.value)}
                  placeholder={`Αντικαθιστά το ${providerName === 'OpenRouter' ? 'OPENROUTER_API_KEY' : 'GEMINI_API_KEY'} του .env`}
                  className="mt-1 w-full rounded-xl border border-white/10 bg-ink-950 px-3 py-2 text-sm text-white outline-none ring-brass-300 focus:ring-2"
                />
              </label>
              <button type="button" onClick={saveKey} className="inline-flex items-center gap-1 rounded-xl bg-brass-300 px-3 py-2 text-xs font-extrabold text-ink-950">
                <KeyRound className="h-3.5 w-3.5" /> Αποθήκευση
              </button>
            </div>
          </div>
        )}
      </header>

      <main className={`mx-auto flex w-full max-w-[1920px] flex-1 flex-col px-3 lg:px-4 ${studioLocked ? 'min-h-0 py-2' : 'py-5'}`}>
        {tab === 'studio' ? (
          <div className="flex min-h-0 flex-1 flex-col gap-2">
            <section className="ops-panel flex shrink-0 flex-wrap items-center gap-3 px-3 py-1.5">
              <div className="min-w-[180px] flex-1">
                <div className="text-[10px] font-bold uppercase tracking-[0.18em] text-white/35">Σήμερα</div>
                <div className="mt-0.5 flex flex-wrap gap-1">
                  {CITIZEN_APPS.map((app) => (
                    <span key={app.app} className="rounded-full border border-white/10 px-2 py-0.5 text-[11px] text-white/45 line-through">{app.app}</span>
                  ))}
                </div>
              </div>
              <div className="hidden h-6 w-px bg-white/10 sm:block" />
              <div className="min-w-[180px] flex-1">
                <div className="text-[10px] font-bold uppercase tracking-[0.18em] text-brass-300">Με το TownLink</div>
                <p className="text-sm leading-snug text-white">Μία αναφορά στο CityOn. Η ευθύνη μοιράζεται αυτόματα.</p>
              </div>
            </section>

            <ol className="grid shrink-0 grid-cols-2 gap-1.5 sm:grid-cols-3 xl:grid-cols-6">
              {PIPELINE_AGENTS.map((agent) => {
                const trace = traces.find((item) => item.agent_number === agent.n);
                const live = activeAgents[agent.n];
                const status = trace ? 'done' : live ? 'run' : 'idle';
                return (
                  <li key={agent.n} className={`ops-panel px-2.5 py-1.5 ${status === 'run' ? 'agent-running border-brass-300/40' : ''}`}>
                    <div className="flex items-center justify-between text-[10px] font-bold uppercase tracking-[0.14em]">
                      <span className="text-white/35">0{agent.n}</span>
                      <span className={status === 'done' ? 'text-emerald-300' : status === 'run' ? 'text-brass-200' : 'text-white/30'}>
                        {status === 'done' ? formatDuration(trace.duration_ms) : status === 'run' ? 'live' : '—'}
                      </span>
                    </div>
                    <div className="text-[13px] font-bold leading-tight text-white">{agent.short}</div>
                  </li>
                );
              })}
            </ol>

            {!llmReady && health && health.status !== 'down' && (
              <div role="status" className="rounded-2xl border border-brass-300/30 bg-brass-300/10 px-4 py-3 text-sm text-brass-200">
                Δεν υπάρχει κλειδί μοντέλου. Βάλε τιμή στο <span className="font-mono">GEMINI_API_KEY</span> ή στο <span className="font-mono">OPENROUTER_API_KEY</span> του .env, αλλιώς η αποστολή δεν ξεκινά.
              </div>
            )}
            {error && <div role="alert" className="rounded-2xl border border-rose-400/30 bg-rose-950/60 px-4 py-3 text-sm text-rose-100">{error}</div>}

            <div className="studio-stage grid min-h-0 flex-1 items-start gap-3 lg:grid-cols-[minmax(280px,22rem)_minmax(0,1fr)] lg:items-stretch xl:grid-cols-[minmax(250px,19rem)_minmax(0,1.55fr)_minmax(360px,0.78fr)] xl:overflow-hidden">
              <div className="min-h-0 min-w-0 lg:row-span-2 xl:row-span-1 xl:h-full xl:overflow-hidden">
                <CityOnMobileEmulator
                  presets={presets}
                  selectedPresetId={presetId}
                  onSelectPreset={applyPreset}
                  citizenComment={comment}
                  setCitizenComment={setComment}
                  latitude={lat}
                  setLatitude={(value) => { setLat(value); setLocationLabel(''); }}
                  longitude={lon}
                  setLongitude={(value) => { setLon(value); setLocationLabel(''); }}
                  locationLabel={locationLabel}
                  imagePreviewUrl={preview}
                  onUploadCustomImage={uploadImage}
                  onSubmitIncident={run}
                  isRunning={running}
                  completedReport={report}
                  history={history}
                  onRecallReport={recallReport}
                />
              </div>
              <AgentControlRoom
                activeAgents={activeAgents}
                completedTraces={traces}
                completedReport={report}
                imagePreviewUrl={preview}
                running={running}
                elapsedMs={elapsed}
                onOpenExecutive={() => setTab('executive')}
              />
            </div>

            <p className="shrink-0 px-1 text-center text-[10px] leading-snug text-white/35">
              Κανόνας αρμοδιότητας: δημοτικοί δρόμοι στον Δήμο · φρεάτια και διαρροές στην ΕΥΔΑΠ · ηλεκτροδότηση στον ΔΕΔΔΗΕ · κεντρικές λεωφόροι και φωτεινοί σηματοδότες στην Περιφέρεια Αττικής.
              {running && <span className="text-brass-200"> · {doneCount}/6 agents</span>}
            </p>
          </div>
        ) : (
          <ExecutiveDashboard geminiApiKey={apiKey} />
        )}
      </main>
    </div>
  );
}
