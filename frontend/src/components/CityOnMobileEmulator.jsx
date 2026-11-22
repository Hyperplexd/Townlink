import React, { useEffect, useState } from 'react';
import { Camera, CheckCircle2, MapPin, Send } from 'lucide-react';
import { CITIZEN_APPS, agencyStyle, formatDuration, urgencyLabel } from '../api/client';

function useAthensClock() {
  const [label, setLabel] = useState('');
  useEffect(() => {
    const tick = () => {
      setLabel(new Date().toLocaleTimeString('el-GR', { hour: '2-digit', minute: '2-digit', timeZone: 'Europe/Athens' }));
    };
    tick();
    const id = setInterval(tick, 30000);
    return () => clearInterval(id);
  }, []);
  return label;
}

export default function CityOnMobileEmulator({
  presets,
  selectedPresetId,
  onSelectPreset,
  citizenComment,
  setCitizenComment,
  latitude,
  setLatitude,
  longitude,
  setLongitude,
  locationLabel,
  imagePreviewUrl,
  onUploadCustomImage,
  onSubmitIncident,
  isRunning,
  completedReport,
  history,
  onRecallReport,
}) {
  const clock = useAthensClock();
  const decision = completedReport?.decision_output;
  const mitos = completedReport?.mitos_output;
  const tickets = decision?.dispatched_tickets || [];
  const dispatched = new Set(tickets.map((ticket) => ticket.target_agency));
  const replaced = CITIZEN_APPS.filter((app) => dispatched.has(app.agency));
  const savedCount = replaced.length || decision?.apps_saved_count || 0;
  const documents = (mitos?.matched_procedures || []).flatMap((procedure) => procedure.required_documents_el || []);

  return (
    <div className="flex flex-col items-center gap-3 xl:h-full xl:min-h-0 xl:gap-2">
    {/*
      <section className="ops-panel w-full shrink-0 p-2.5">
        <div className="mb-1.5 flex items-baseline justify-between gap-3">
          <h2 className="font-serif text-lg text-brass-200">Σενάρια κριτών</h2>
          <span className="text-[11px] uppercase tracking-[0.16em] text-white/40">1 κλικ</span>
        </div>
        <div className="space-y-2">
          {presets.map((preset) => {
            const selected = selectedPresetId === preset.id;
            return (
              <button
                key={preset.id}
                type="button"
                onClick={() => onSelectPreset(preset)}
                className={`w-full rounded-xl border px-2.5 py-2 text-left transition ${selected ? 'border-brass-300/70 bg-brass-300/10' : 'border-white/10 bg-ink-950/50 hover:border-white/20'}`}
              >
                <div className="text-[10px] font-bold uppercase tracking-[0.14em] text-brass-300">{preset.badge_el || 'Demo'}</div>
                <div className="mt-0.5 text-sm font-semibold text-white">{preset.title_el}</div>
                {preset.location_label_el && <div className="mt-1 text-xs text-white/55">{preset.location_label_el}</div>}
              </button>
            );
          })}
          {!presets.length && <p className="text-sm text-white/50">Τα σενάρια φορτώνουν από το backend.</p>}
        </div>
        {history?.length > 0 && (
          <div className="mt-3 border-t border-white/10 pt-3">
            <div className="mb-2 text-[10px] font-bold uppercase tracking-[0.14em] text-white/40">Αποδείξεις συνεδρίας</div>
            <div className="flex flex-wrap gap-1.5">
              {history.map((report) => (
                <button
                  key={report.report_id}
                  type="button"
                  onClick={() => onRecallReport(report)}
                  className={`rounded-full border px-2.5 py-1 text-[11px] font-semibold ${completedReport?.report_id === report.report_id ? 'border-brass-300 text-brass-200' : 'border-white/15 text-white/70 hover:text-white'}`}
                >
                  {report.report_id}
                </button>
              ))}
            </div>
          </div>
        )}
      </section>
    */}
      <div className="phone-shell xl:min-h-0 xl:w-full xl:flex-1">
        <div className="phone-island" />
        <div className="phone-screen">
          <div className="flex items-center justify-between px-5 pb-2 pt-8 text-[11px] font-semibold text-[#5c6b80]">
            <span>{clock || '—'}</span>
            <span>Athens · LTE</span>
          </div>
          <header className="bg-city-800 px-5 py-4 text-white">
            <div className="text-[10px] font-bold uppercase tracking-[0.22em] text-brass-300">CityOn</div>
            <div className="font-serif text-[1.65rem] leading-none">Νέα αναφορά</div>
            <p className="mt-1 text-xs text-white/70">Ανέβασε μία φωτογραφία. Οι υπηρεσίες μοιράζονται μόνες τους.</p>
          </header>

          <div className="phone-scroll space-y-3 px-4 py-4">
            <div className="flex items-start gap-2 rounded-2xl bg-white px-3 py-2.5 shadow-sm">
              <MapPin className="mt-0.5 h-4 w-4 shrink-0 text-city-700" />
              <div className="min-w-0">
                <div className="text-sm font-semibold text-[#162033]">{locationLabel || 'Σημείο στην Αθήνα'}</div>
                <div className="font-mono text-[11px] text-[#6d6254]">{Number(latitude).toFixed(5)}, {Number(longitude).toFixed(5)}</div>
              </div>
            </div>

            <label className="relative block cursor-pointer overflow-hidden rounded-2xl bg-[#e7e0d4]">
              <input
                type="file"
                accept="image/*"
                className="sr-only"
                onChange={(event) => {
                  const file = event.target.files?.[0];
                  if (file) onUploadCustomImage(file);
                  event.target.value = '';
                }}
              />
              <img src={imagePreviewUrl?.startsWith('blob:') ? imagePreviewUrl : '/frame-camera.jpg'} alt="Προσθέστε φωτογραφία" className="block h-auto w-full" />
              <span className="absolute bottom-2 right-2 inline-flex items-center gap-1 rounded-full bg-city-800/90 px-2.5 py-1 text-[11px] font-bold text-white">
                <Camera className="h-3.5 w-3.5" /> Αλλαγή
              </span>
            </label>

            <textarea
              rows={3}
              value={citizenComment}
              onChange={(event) => setCitizenComment(event.target.value)}
              className="w-full resize-none rounded-2xl border border-[#e4d9c8] bg-white px-3 py-2.5 text-sm text-[#162033] outline-none ring-city-500 placeholder:text-[#9a8d7c] focus:ring-2"
              placeholder="Περιγράψτε τι βλέπετε στο δρόμο..."
            />

            {/* <details className="rounded-2xl bg-white px-3 py-2 text-xs text-[#5c5348] shadow-sm">
              <summary className="cursor-pointer font-semibold text-[#162033]">Προσαρμογή GPS για το demo</summary>
              <div className="mt-2 grid grid-cols-2 gap-2">
                <label className="block">
                  <span className="text-[10px] uppercase tracking-wider">Γεωγρ. πλάτος</span>
                  <input type="number" step="0.00001" value={latitude} onChange={(event) => setLatitude(event.target.value)} className="mt-1 w-full rounded-lg border border-[#e4d9c8] px-2 py-1.5 font-mono text-[#162033]" />
                </label>
                <label className="block">
                  <span className="text-[10px] uppercase tracking-wider">Γεωγρ. μήκος</span>
                  <input type="number" step="0.00001" value={longitude} onChange={(event) => setLongitude(event.target.value)} className="mt-1 w-full rounded-lg border border-[#e4d9c8] px-2 py-1.5 font-mono text-[#162033]" />
                </label>
              </div>
            </details> */}

            <button
              type="button"
              disabled={isRunning}
              onClick={onSubmitIncident}
              className="flex w-full items-center justify-center gap-2 rounded-2xl bg-city-800 py-3 text-sm font-bold text-white transition hover:bg-city-700 disabled:cursor-wait disabled:opacity-70"
            >
              <Send className="h-4 w-4" />
              {isRunning ? 'Δρομολόγηση στις υπηρεσίες...' : 'Αποστολή αναφοράς'}
            </button>

            {isRunning && !decision && (
              <div className="rounded-2xl bg-city-800 px-3.5 py-3 text-white" aria-live="polite">
                <div className="text-[10px] font-bold uppercase tracking-[0.16em] text-brass-300">CityOn</div>
                <p className="mt-1 text-sm leading-snug">Η αναφορά σας ελέγχεται και χωρίζεται στις αρμόδιες υπηρεσίες. Δεν χρειάζεται να ανοίξετε άλλη εφαρμογή.</p>
              </div>
            )}

            {decision && (
              <article className="receipt-paper overflow-hidden rounded-2xl border border-[#e6dcc8]" aria-live="polite">
                <div className="bg-city-800 px-3.5 py-3 text-white">
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-[10px] font-bold uppercase tracking-[0.18em] text-brass-300">Ενιαία απόδειξη</span>
                    <CheckCircle2 className="h-4 w-4 text-emerald-300" />
                  </div>
                  <div className="mt-1 font-mono text-[11px] text-white/70">{completedReport.report_id}</div>
                </div>
                <div className="space-y-3 px-3.5 py-3">
                  <div>
                    <div className="font-serif text-4xl leading-none text-city-800">{savedCount}</div>
                    <p className="mt-1 text-sm font-semibold text-[#162033]">
                      {savedCount === 1 ? 'εφαρμογή που δεν χρειάστηκε να ανοίξετε' : 'εφαρμογές που δεν χρειάστηκε να ανοίξετε'}
                    </p>
                  </div>
                  <ul className="grid grid-cols-2 gap-1.5">
                    {CITIZEN_APPS.map((app) => {
                      const hit = dispatched.has(app.agency);
                      return (
                        <li key={app.agency} className={`rounded-xl px-2 py-1.5 text-[11px] ${hit ? 'bg-emerald-50 text-emerald-900' : 'bg-white/70 text-[#8a8175]'}`}>
                          <div className={`font-bold ${hit ? '' : 'line-through'}`}>{app.app}</div>
                          <div>{hit ? 'καλύφθηκε εδώ' : app.hint}</div>
                        </li>
                      );
                    })}
                  </ul>
                  <p className="text-sm leading-snug text-[#243044]">{decision.citizen_unified_message_el}</p>
                  <div className="space-y-2">
                    {tickets.map((ticket) => {
                      const style = agencyStyle(ticket.target_agency);
                      return (
                        <div key={ticket.ticket_id} className="rounded-xl bg-white px-2.5 py-2 shadow-sm">
                          <div className="flex items-center justify-between gap-2">
                            <span className="text-[10px] font-extrabold uppercase tracking-wider" style={{ color: style.badgeBg }}>{ticket.agency_display_name_el || style.fullLabel}</span>
                            <span className="text-[10px] font-semibold text-[#6d6254]">SLA {ticket.target_sla_hours}ω</span>
                          </div>
                          <div className="mt-0.5 font-mono text-[12px] font-semibold text-city-800">#{ticket.ticket_id}</div>
                          <div className="text-[12px] text-[#243044]">{ticket.ticket_title_el}</div>
                          <div className="mt-0.5 text-[10px] text-[#6d6254]">{urgencyLabel(ticket.urgency_level)} · HTTP {ticket.http_status_code}</div>
                        </div>
                      );
                    })}
                  </div>
                  {(documents.length > 0 || mitos?.citizen_guidance_el) && (
                    <div className="rounded-xl bg-white px-2.5 py-2">
                      <div className="text-[10px] font-extrabold uppercase tracking-[0.14em] text-[#8a5a2a]">Μίτος · δικαιολογητικά</div>
                      {mitos?.citizen_guidance_el && <p className="mt-1 text-[12px] leading-snug text-[#243044]">{mitos.citizen_guidance_el}</p>}
                      {documents.length > 0 && (
                        <ul className="mt-1.5 list-disc space-y-0.5 pl-4 text-[12px] text-[#243044]">
                          {documents.slice(0, 6).map((doc) => <li key={doc}>{doc}</li>)}
                        </ul>
                      )}
                    </div>
                  )}
                  <p className="text-center text-[10px] text-[#8a8175]">
                    Ολοκληρώθηκε σε {formatDuration(decision.total_pipeline_duration_ms)} · Open311 / utility webhooks
                  </p>
                </div>
              </article>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
