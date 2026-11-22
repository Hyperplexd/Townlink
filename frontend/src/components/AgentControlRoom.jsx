import React, { useState } from 'react';
import { Check, Copy, Cpu, ShieldCheck } from 'lucide-react';
import BoundingBoxCanvas from './BoundingBoxCanvas';
import {
  HAZARD_LABELS,
  PIPELINE_AGENTS,
  agencyStyle,
  formatDuration,
  urgencyLabel,
} from '../api/client';

function TrustRing({ score = 0 }) {
  const pct = Math.round(Number(score) * 100);
  const radius = 28;
  const circ = 2 * Math.PI * radius;
  const dash = circ * Math.max(0, Math.min(1, Number(score) || 0));
  return (
    <svg viewBox="0 0 72 72" className="h-16 w-16 shrink-0" aria-label={`Δείκτης εμπιστοσύνης ${pct}%`}>
      <circle cx="36" cy="36" r={radius} fill="none" stroke="rgba(255,255,255,0.08)" strokeWidth="6" />
      <circle
        cx="36"
        cy="36"
        r={radius}
        fill="none"
        stroke="#e4c36a"
        strokeWidth="6"
        strokeLinecap="round"
        strokeDasharray={`${dash} ${circ - dash}`}
        transform="rotate(-90 36 36)"
      />
      <text x="36" y="40" textAnchor="middle" fill="#f8f1e2" fontSize="16" fontWeight="700" fontFamily="Manrope, sans-serif">{pct}</text>
    </svg>
  );
}

function WebhookInspector({ tickets }) {
  const [activeId, setActiveId] = useState(tickets[0]?.ticket_id || '');
  const [copied, setCopied] = useState(false);
  const active = tickets.find((ticket) => ticket.ticket_id === activeId) || tickets[0];
  if (!active) {
    return <p className="text-sm text-white/50">Τα JSON εμφανίζονται μόλις ο Agent απόφασης ολοκληρώσει τα HTTP POST προς τους φορείς.</p>;
  }
  const body = { payload_sent: active.payload_sent, webhook_response: active.webhook_response };

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(JSON.stringify(body, null, 2));
      setCopied(true);
      setTimeout(() => setCopied(false), 1400);
    } catch { /* clipboard unavailable */ }
  };

  return (
    <div>
      <div className="flex gap-1.5 overflow-x-auto pb-2">
        {tickets.map((ticket) => {
          const style = agencyStyle(ticket.target_agency);
          const on = ticket.ticket_id === active.ticket_id;
          return (
            <button
              key={ticket.ticket_id}
              type="button"
              onClick={() => setActiveId(ticket.ticket_id)}
              className={`shrink-0 rounded-full border px-2.5 py-1 text-[11px] font-bold ${on ? 'text-ink-950' : 'border-white/10 text-white/70'}`}
              style={on ? { background: style.strokeColor, borderColor: style.strokeColor } : undefined}
            >
              {style.shortLabel} · {ticket.ticket_id}
            </button>
          );
        })}
      </div>
      <div className="mb-2 flex flex-wrap items-center gap-2 text-[11px] text-white/60">
        <span className="rounded-md bg-emerald-400/15 px-1.5 py-0.5 font-bold text-emerald-200">HTTP {active.http_status_code}</span>
        <span>{active.protocol_standard}</span>
        <span className="truncate font-mono text-white/45">{active.webhook_endpoint_url}</span>
        <button type="button" onClick={copy} className="ml-auto inline-flex items-center gap-1 rounded-md border border-white/10 px-2 py-1 font-semibold text-white/80 hover:text-white">
          {copied ? <Check className="h-3.5 w-3.5" /> : <Copy className="h-3.5 w-3.5" />}
          {copied ? 'Αντιγράφηκε' : 'Αντιγραφή JSON'}
        </button>
      </div>
      <pre className="max-h-36 overflow-auto rounded-xl bg-black/40 p-2 font-mono text-[10px] leading-snug text-emerald-100/90">{JSON.stringify(body, null, 2)}</pre>
    </div>
  );
}

export default function AgentControlRoom({
  activeAgents,
  completedTraces,
  completedReport,
  imagePreviewUrl,
  running,
  elapsedMs,
  onOpenExecutive,
}) {
  const traceMap = {};
  for (const trace of completedTraces) traceMap[trace.agent_number] = trace;

  const visionOut = completedReport?.vision_output || traceMap[1]?.structured_output;
  const geoOut = completedReport?.geo_output || traceMap[2]?.structured_output;
  const slaOut = completedReport?.sla_output || traceMap[3]?.structured_output;
  const mitosOut = completedReport?.mitos_output || traceMap[4]?.structured_output;
  const validationOut = completedReport?.validation_output || traceMap[5]?.structured_output;
  const decisionOut = completedReport?.decision_output || traceMap[6]?.structured_output;
  const hazards = visionOut?.detected_hazards || [];
  const mappings = geoOut?.jurisdiction_mappings || [];
  const tickets = decisionOut?.dispatched_tickets || [];
  const insight = decisionOut?.executive_insight;
  const parallel = Boolean(activeAgents[3] && activeAgents[4] && !traceMap[3] && !traceMap[4]);

  return (
    <>
    <div className="flex min-h-0 min-w-0 flex-col gap-2 xl:h-full xl:overflow-y-auto xl:pr-1">
      <section className="ops-panel flex shrink-0 flex-wrap items-center justify-between gap-2 px-3 py-2">
        <div className="flex items-center gap-2.5">
          <span className={`flex h-8 w-8 items-center justify-center rounded-lg bg-city-700/40 text-sky-300 ${running ? 'agent-running' : ''}`}>
            <Cpu className="h-4 w-4" />
          </span>
          <div>
            <h2 className="font-serif text-xl leading-none text-white">Μηχανοστάσιο</h2>
            <p className="mt-0.5 text-[11px] text-white/50">Έξι agents · ζωντανά events SSE · πραγματικά webhooks</p>
          </div>
        </div>
        <div className="text-right">
          <div className="font-mono text-sm text-brass-200">{running ? formatDuration(elapsedMs) : formatDuration(decisionOut?.total_pipeline_duration_ms)}</div>
          <div className="text-[10px] uppercase tracking-[0.14em] text-white/40">{running ? 'σε εξέλιξη' : decisionOut ? 'ολοκληρώθηκε' : 'σε αναμονή'}</div>
        </div>
      </section>

      <section className="ops-panel p-3">
        <div className="mb-2 flex flex-wrap items-end justify-between gap-2">
          <div>
            <h3 className="text-sm font-bold text-sky-300">Vision AI · 2D πλαίσια</h3>
            <p className="text-[11px] leading-snug text-white/45">{visionOut?.scene_summary_el || 'Κανονικοποιημένα πλαίσια 0–1000, ένα χρώμα ανά αρμόδια υπηρεσία.'}</p>
          </div>
          {visionOut?.multi_agency_split_detected && (
            <span className="rounded-full bg-brass-300/15 px-2 py-1 text-[11px] font-bold text-brass-200">Διάσπαση σε πολλούς φορείς</span>
          )}
        </div>
        <BoundingBoxCanvas
          imageDataUrl={completedReport?.image_data_url || (imagePreviewUrl?.startsWith('blob:') || running ? imagePreviewUrl : '')}
          detectedHazards={hazards}
          jurisdictionMappings={mappings}
          scanning={running && Boolean(activeAgents[1]) && !traceMap[1]}
        />
        <div className="mt-2 flex flex-wrap gap-1">
          {['CITY_OF_ATHENS', 'EYDAP', 'DEDDIE', 'REGION_OF_ATTICA'].map((code) => {
            const style = agencyStyle(code);
            return (
              <span key={code} className="inline-flex items-center gap-1.5 rounded-full border border-white/10 px-2 py-1 text-[10px] font-bold text-white/75">
                <span className="h-2 w-2 rounded-full" style={{ background: style.strokeColor }} />
                {style.fullLabel}
              </span>
            );
          })}
        </div>
        {hazards.length > 0 && (
          <ul className="mt-2 grid gap-1.5 sm:grid-cols-2">
            {hazards.map((hazard) => {
              const mapping = mappings.find((item) => item.hazard_id === hazard.hazard_id);
              const agency = mapping?.final_agency || hazard.preliminary_agency;
              const style = agencyStyle(agency);
              return (
                <li key={hazard.hazard_id} className="rounded-lg border border-white/10 bg-black/20 px-2.5 py-1.5">
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-[11px] font-extrabold uppercase tracking-wider" style={{ color: style.strokeColor }}>{style.shortLabel}</span>
                    <span className="text-[11px] text-white/50">{HAZARD_LABELS[hazard.category] || hazard.category} · {Math.round((hazard.confidence || 0) * 100)}%</span>
                  </div>
                  <div className="mt-0.5 text-sm font-semibold text-white">{hazard.title_el}</div>
                  <div className="text-xs text-white/55">Σοβαρότητα {hazard.severity_score}/10{mapping ? ` · ${mapping.department_el}` : ''}</div>
                </li>
              );
            })}
          </ul>
        )}
      </section>

      <section className="grid gap-1.5 sm:grid-cols-2 xl:grid-cols-3">
        {PIPELINE_AGENTS.map((agent) => {
          const trace = traceMap[agent.n];
          const live = activeAgents[agent.n];
          const status = trace ? 'done' : live ? 'run' : 'idle';
          return (
            <article
              key={agent.n}
              className={`ops-panel px-2.5 py-2 ${status === 'run' ? 'agent-running border-brass-300/50' : ''} ${status === 'done' ? 'border-emerald-400/30' : ''}`}
            >
              <div className="flex items-start justify-between gap-2">
                <div>
                  <div className="text-[10px] font-bold uppercase tracking-[0.16em] text-white/35">Agent {agent.n}</div>
                  <h3 className="text-sm font-bold text-white">{trace?.agent_name_el || agent.name}</h3>
                </div>
                <span className={`rounded-full px-2 py-0.5 text-[10px] font-bold ${status === 'done' ? 'bg-emerald-400/15 text-emerald-200' : status === 'run' ? 'bg-brass-300/15 text-brass-200' : 'bg-white/5 text-white/40'}`}>
                  {status === 'done' ? 'έτοιμο' : status === 'run' ? 'τρέχει' : 'αναμονή'}
                </span>
              </div>
              <p className="mt-0.5 text-[11px] leading-snug text-white/50">{status === 'run' ? live : trace?.summary_el || agent.detail}</p>
              <div className="mt-1 flex flex-wrap items-center gap-1">
                {status === 'done' && <span className="font-mono text-[11px] text-brass-200">{formatDuration(trace.duration_ms)}</span>}
                {(trace?.api_calls_made || []).map((api) => (
                  <span key={api} className="rounded-md bg-white/5 px-1.5 py-0.5 text-[10px] text-sky-200/90">{api}</span>
                ))}
                {parallel && (agent.n === 3 || agent.n === 4) && (
                  <span className="rounded-md bg-brass-300/10 px-1.5 py-0.5 text-[10px] font-bold text-brass-200">παράλληλα</span>
                )}
              </div>
            </article>
          );
        })}
      </section>
    </div>

    <div className="flex min-h-0 min-w-0 flex-col gap-2 lg:col-start-2 xl:col-start-auto xl:h-full xl:overflow-y-auto xl:pr-1">
      <section className="ops-panel p-2.5">
        <div className="flex items-start gap-2.5">
          <TrustRing score={validationOut?.overall_trust_score || 0} />
          <div className="min-w-0 flex-1">
            <h3 className="flex items-center gap-1.5 text-sm font-bold text-white"><ShieldCheck className="h-4 w-4 text-brass-300" /> Critic · εμπιστοσύνη</h3>
            <p className="mt-0.5 text-[11px] leading-snug text-white/55">{validationOut?.critic_summary_el || 'Ο Agent 5 ελέγχει συνοχή εικόνας-κειμένου, γεωγραφία και πληρότητα σύμβασης Open311 πριν την αποστολή.'}</p>
            {validationOut && (
              <div className="mt-1.5 flex flex-wrap gap-1 text-[11px] font-semibold">
                <span className={`rounded-full px-2 py-0.5 ${validationOut.approved_for_dispatch ? 'bg-emerald-400/15 text-emerald-200' : 'bg-rose-400/15 text-rose-200'}`}>
                  {validationOut.approved_for_dispatch ? 'Εγκεκριμένο για αποστολή' : 'Μπλοκαρισμένο'}
                </span>
                <span className="rounded-full bg-white/5 px-2 py-0.5 text-white/70">Εικόνα/κείμενο {validationOut.image_text_consistency ? 'ΟΚ' : 'όχι'}</span>
                <span className="rounded-full bg-white/5 px-2 py-0.5 text-white/70">Γεωγραφία {validationOut.geospatial_consistency ? 'ΟΚ' : 'όχι'}</span>
              </div>
            )}
          </div>
        </div>
        <ul className="mt-1.5 space-y-0.5">
          {(validationOut?.validation_checks || []).map((check) => (
            <li key={check.check_name} className="flex gap-1.5 text-[11px] leading-snug">
              <span className={`font-bold ${check.passed ? 'text-emerald-300' : 'text-rose-300'}`}>{check.passed ? '✓' : '!'}</span>
              <span>
                <span className="font-semibold text-white">{check.check_name}</span>
                <span className="text-white/50"> — {check.details_el}</span>
              </span>
            </li>
          ))}
          {(validationOut?.corrective_overrides_applied || []).map((note) => (
            <li key={note} className="text-[11px] text-brass-200">Διόρθωση: {note}</li>
          ))}
        </ul>
      </section>

      <section className="ops-panel p-2.5">
        <h3 className="text-sm font-bold text-white">Σειρά επέμβασης & αρμοδιότητα</h3>
        <div className="mt-1.5 grid gap-2 min-[1500px]:grid-cols-[minmax(0,1.15fr)_minmax(0,0.85fr)]">
          {insight ? (
            <div className="space-y-1">
              {insight.cascading_risk_detected && (
                <span className="inline-flex rounded-full bg-rose-400/15 px-2 py-0.5 text-[11px] font-bold text-rose-200">Διαδοχικός κίνδυνος</span>
              )}
              <p className="text-xs leading-snug text-brass-200">{insight.inter_agency_coordination_plan_el}</p>
              <p className="text-[11px] leading-snug text-white/70">{insight.executive_recommendation_el}</p>
              <div className="text-[10px] font-semibold uppercase tracking-[0.14em] text-white/40">Κοινωνικός αντίκτυπος {insight.estimated_social_impact_score}/100</div>
            </div>
          ) : (
            <p className="text-sm text-white/50">Το σχέδιο συνεργείων γράφεται από τον Agent απόφασης: ποιος μπαίνει πρώτος στο σημείο και γιατί.</p>
          )}
          {geoOut && (
            <dl className="grid grid-cols-2 gap-1 text-[11px]">
              <div className="rounded-lg bg-black/20 px-2 py-1">
                <dt className="text-white/40">Διεύθυνση</dt>
                <dd className="font-semibold leading-snug text-white">{geoOut.formatted_address_el || geoOut.street_name}</dd>
              </div>
              <div className="rounded-lg bg-black/20 px-2 py-1">
                <dt className="text-white/40">Κοινότητα</dt>
                <dd className="font-semibold leading-snug text-white">{geoOut.municipal_community_name_el || '—'}</dd>
              </div>
              <div className="rounded-lg bg-black/20 px-2 py-1">
                <dt className="text-white/40">Ιεραρχία OSM</dt>
                <dd className="font-semibold leading-snug text-white">{geoOut.osm_highway_type || '—'}</dd>
              </div>
              <div className="rounded-lg bg-black/20 px-2 py-1">
                <dt className="text-white/40">Λεωφόρος Περιφέρειας</dt>
                <dd className="font-semibold leading-snug text-white">{geoOut.is_major_regional_avenue ? 'Ναι · Περιφέρεια Αττικής' : 'Όχι · δημοτικό δίκτυο'}</dd>
              </div>
            </dl>
          )}
        </div>
        {mappings.length > 0 && (
          <ul className="mt-1.5 grid gap-1.5 sm:grid-cols-2">
            {mappings.map((mapping) => {
              const style = agencyStyle(mapping.final_agency);
              return (
                <li key={mapping.hazard_id} className="text-[11px] leading-snug">
                  <div className="font-bold" style={{ color: style.strokeColor }}>{mapping.agency_name_el} · {mapping.department_el}</div>
                  <p className="text-white/55">{mapping.jurisdiction_reasoning_el}</p>
                </li>
              );
            })}
          </ul>
        )}
      </section>

      {(slaOut || mitosOut) && (
        <div className="grid gap-2 min-[1500px]:grid-cols-2">
          <section className="ops-panel p-2.5">
            <h3 className="text-sm font-bold text-emerald-200">Πλαίσιο πόλης · ΟΑΣΑ</h3>
            {slaOut ? (
              <div className="mt-1.5 space-y-1 text-[12px]">
                <div className="text-xs font-bold uppercase tracking-[0.14em] text-white/45">{urgencyLabel(slaOut.overall_urgency)}{slaOut.is_near_transit_hub ? ' · κοντά σε στάση' : ''}</div>
                {(slaOut.nearest_oasa_stops || []).length === 0 && <p className="text-white/55">Καμία στάση ΟΑΣΑ μέσα στην ακτίνα ελέγχου.</p>}
                <ul className="space-y-1.5">
                  {(slaOut.nearest_oasa_stops || []).map((stop) => (
                    <li key={stop.stop_code} className="rounded-lg bg-black/20 px-2 py-1 text-[11px]">
                      <div className="font-semibold text-white">{stop.stop_name_el}</div>
                      <div className="text-white/50">{Math.round(stop.distance_meters)} μ. · {stop.stop_code}{(stop.routes_serving || []).length ? ` · ${stop.routes_serving.join(', ')}` : ''}</div>
                    </li>
                  ))}
                </ul>
                {(slaOut.nearby_sensitive_pois || []).length > 0 && (
                  <p className="text-xs text-white/60">Ευαίσθητα σημεία: {slaOut.nearby_sensitive_pois.join(' · ')}</p>
                )}
                <ul className="space-y-1">
                  {(slaOut.hazard_sla_assessments || []).map((item) => (
                    <li key={item.hazard_id} className="text-xs text-white/70">
                      <span className="font-semibold text-white">{item.target_sla_hours}ω</span> · προτεραιότητα {item.priority_score}/100 · {item.sla_justification_el}
                    </li>
                  ))}
                </ul>
              </div>
            ) : <p className="mt-2 text-sm text-white/50">Ο Agent SLA ρωτά το telematics του ΟΑΣΑ και το OSM για σχολεία και νοσοκομεία.</p>}
          </section>
          <section className="ops-panel p-2.5">
            <h3 className="text-sm font-bold text-rose-200">Μίτος · διαδικασίες</h3>
            {mitosOut ? (
              <div className="mt-1.5 space-y-1">
                <p className="text-sm text-white/70">{mitosOut.citizen_guidance_el}</p>
                {(mitosOut.matched_procedures || []).map((procedure) => (
                  <article key={procedure.procedure_id} className="rounded-lg bg-black/20 px-2 py-1.5 text-[11px] leading-snug">
                    <div className="font-semibold text-white">{procedure.title_el}</div>
                    <div className="text-white/45">{procedure.organization_el} · {procedure.estimated_cost_el}</div>
                    {(procedure.steps_el || []).length > 0 && (
                      <ol className="mt-1 list-decimal space-y-0.5 pl-4 text-white/65">
                        {procedure.steps_el.slice(0, 4).map((step) => <li key={step}>{step}</li>)}
                      </ol>
                    )}
                    {procedure.url && <a href={procedure.url} target="_blank" rel="noreferrer" className="mt-1 inline-block text-brass-200 underline-offset-2 hover:underline">Καρτέλα διαδικασίας</a>}
                  </article>
                ))}
                {(mitosOut.search_keywords_used || []).length > 0 && (
                  <p className="text-[11px] text-white/40">Όροι: {mitosOut.search_keywords_used.join(' · ')}</p>
                )}
              </div>
            ) : <p className="mt-2 text-sm text-white/50">Ο Agent Μίτος φέρνει επίσημα δικαιολογητικά από το api.mitos.gov.gr.</p>}
          </section>
        </div>
      )}

      <section className="ops-panel p-2.5">
        <div className="mb-1.5 flex flex-wrap items-center justify-between gap-2">
          <div>
            <h3 className="text-sm font-bold text-white">Επιθεωρητής</h3>
            <p className="text-xs text-white/45">Το JSON που έφυγε και η απάντηση HTTP του φορέα.</p>
          </div>
          {decisionOut && (
            <button type="button" onClick={onOpenExecutive} className="rounded-full bg-brass-300 px-3 py-1.5 text-xs font-extrabold text-ink-950 hover:bg-brass-200">
              Administration
            </button>
          )}
        </div>
        <WebhookInspector tickets={tickets} />
      </section>
    </div>
    </>
  );
}
