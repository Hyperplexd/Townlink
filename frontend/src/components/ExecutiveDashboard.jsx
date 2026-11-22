import React, { useEffect, useMemo, useRef, useState } from 'react';
import { Loader2, RefreshCw, Sparkles } from 'lucide-react';
import {
  AGENCY_ORDER,
  agencyStyle,
  fetchExecutiveDashboard,
  formatWhen,
  requestExecutiveAiBriefing,
  ticketCoords,
  urgencyLabel,
} from '../api/client';

const EMPTY_TICKETS = [];

function escapeHtml(value) {
  return String(value ?? '').replace(/[&<>"']/g, (char) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
  }[char]));
}

export default function ExecutiveDashboard({ geminiApiKey }) {
  const mapNode = useRef(null);
  const mapRef = useRef(null);
  const layerRef = useRef(null);
  const fittedKey = useRef('');
  const [data, setData] = useState(null);
  const [loadError, setLoadError] = useState('');
  const [loading, setLoading] = useState(true);
  const [selectedId, setSelectedId] = useState('');
  const [briefing, setBriefing] = useState(null);
  const [briefingError, setBriefingError] = useState('');
  const [briefingBusy, setBriefingBusy] = useState(false);

  const load = () => {
    setLoading(true);
    setLoadError('');
    fetchExecutiveDashboard()
      .then((payload) => {
        setData(payload);
        setSelectedId((current) => current || payload.tickets?.[0]?.ticket_id || '');
      })
      .catch((error) => setLoadError(error.message))
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  useEffect(() => {
    const node = mapNode.current;
    if (!node || !window.L) return undefined;
    const map = window.L.map(node, { zoomControl: true });
    const esriAttr = 'Tiles &copy; Esri &mdash; Esri, DeLorme, NAVTEQ';
    window.L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}', {
      attribution: esriAttr,
      maxZoom: 16,
    }).addTo(map);
    window.L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Reference/MapServer/tile/{z}/{y}/{x}', {
      maxZoom: 16,
      pane: 'overlayPane',
    }).addTo(map);
    map.setMaxZoom(16);
    map.setView([37.9838, 23.7275], 13);
    mapRef.current = map;
    layerRef.current = window.L.layerGroup().addTo(map);
    const timer = setTimeout(() => map.invalidateSize(), 200);
    return () => {
      clearTimeout(timer);
      map.remove();
      mapRef.current = null;
      layerRef.current = null;
      if (node._leaflet_id) node._leaflet_id = undefined;
    };
  }, []);

  const tickets = data?.tickets || EMPTY_TICKETS;
  const ticketKey = tickets.map((ticket) => ticket.ticket_id).join('|');

  useEffect(() => {
    const map = mapRef.current;
    const layer = layerRef.current;
    if (!map || !layer || !window.L) return;
    layer.clearLayers();
    const points = [];
    tickets.forEach((ticket, index) => {
      const coords = ticketCoords(ticket);
      if (!coords) return;
      const latlng = [coords.lat + (index % 6) * 0.00018, coords.lon + (index % 4) * 0.00018];
      points.push(latlng);
      const style = agencyStyle(ticket.target_agency);
      const selected = ticket.ticket_id === selectedId;
      const icon = window.L.divIcon({
        className: 'civic-pin',
        html: `<span class="civic-pin-dot${selected ? ' is-selected' : ''}" style="--pin:${style.strokeColor}"></span>`,
        iconSize: [22, 22],
        iconAnchor: [11, 11],
      });
      const marker = window.L.marker(latlng, { icon, zIndexOffset: selected ? 400 : 0 });
      marker.bindPopup(
        `<strong>${escapeHtml(ticket.ticket_id)}</strong><br/>${escapeHtml(ticket.agency_display_name_el || style.fullLabel)}<br/>${escapeHtml(ticket.ticket_title_el)}<br/>SLA ${escapeHtml(ticket.target_sla_hours)}ω`,
      );
      marker.on('click', () => setSelectedId(ticket.ticket_id));
      marker.addTo(layer);
      if (selected) marker.openPopup();
    });
    if (fittedKey.current !== ticketKey && points.length) {
      fittedKey.current = ticketKey;
      if (points.length === 1) map.setView(points[0], 15);
      else map.fitBounds(points, { padding: [36, 36], maxZoom: 15 });
    }
  }, [ticketKey, selectedId, tickets]);

  const focusTicket = (ticketId) => {
    setSelectedId(ticketId);
    const ticket = tickets.find((item) => item.ticket_id === ticketId);
    const coords = ticket && ticketCoords(ticket);
    if (coords && mapRef.current) mapRef.current.flyTo([coords.lat, coords.lon], 16, { duration: 0.55 });
  };

  const agencyRows = useMemo(() => {
    const counts = data?.agency_breakdown || {};
    const codes = AGENCY_ORDER.filter((code) => code in counts || AGENCY_ORDER.includes(code));
    const max = Math.max(1, ...codes.map((code) => counts[code] || 0));
    return codes.map((code) => ({ code, count: counts[code] || 0, max, style: agencyStyle(code) }));
  }, [data]);

  const communities = Object.entries(data?.community_breakdown || {});
  const agenciesLive = Object.values(data?.agency_breakdown || {}).filter((count) => count > 0).length;

  const askBriefing = async () => {
    setBriefingBusy(true);
    setBriefingError('');
    try {
      setBriefing(await requestExecutiveAiBriefing(geminiApiKey));
    } catch (error) {
      setBriefingError(error.message || 'Η αναφορά δεν συντάχθηκε');
    } finally {
      setBriefingBusy(false);
    }
  };

  const kpis = [
    { label: 'Ενεργά tickets', value: data?.total_dispatched_tickets ?? '—', note: 'απεσταλμένα στους φορείς' },
    { label: 'Κρίσιμα SLA', value: data?.critical_sla_count ?? '—', note: 'έως 8 ώρες ή κόμβος ΟΑΣΑ' },
    { label: 'Φορείς σε κίνηση', value: data ? agenciesLive : '—', note: 'από 6 κανάλια webhook' },
    { label: 'Αναφορές πολιτών', value: data?.recent_reports?.length ?? '—', note: 'κλεισμένες ροές σε αυτή τη συνεδρία' },
  ];

  return (
    <div className="space-y-4">
      <section className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <p className="text-[11px] font-bold uppercase tracking-[0.18em] text-brass-300">Δήμος Αθηναίων</p>
          <h2 className="font-serif text-4xl text-white">Administration</h2>
          <p className="mt-1 max-w-xl text-sm text-white/55">Ανοιχτά tickets στον χάρτη της πόλης, με το χρώμα του φορέα που τα ανέλαβε.</p>
        </div>
        <button type="button" onClick={load} className="inline-flex items-center gap-2 rounded-full border border-white/15 px-3 py-1.5 text-xs font-bold text-white/80 hover:text-white">
          <RefreshCw className={`h-3.5 w-3.5 ${loading ? 'animate-spin' : ''}`} /> Ανανέωση
        </button>
      </section>

      {loadError && <div role="alert" className="rounded-2xl border border-rose-400/30 bg-rose-950/50 px-4 py-3 text-sm text-rose-100">{loadError}</div>}

      <section className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {kpis.map((kpi) => (
          <article key={kpi.label} className="ops-panel px-4 py-3">
            <div className="text-[11px] font-bold uppercase tracking-[0.14em] text-white/40">{kpi.label}</div>
            <div className="mt-1 font-serif text-4xl text-white">{kpi.value}</div>
            <div className="text-xs text-white/45">{kpi.note}</div>
          </article>
        ))}
      </section>

      <div className="grid gap-4 lg:grid-cols-12">
        <section className="ops-panel p-3 lg:col-span-8">
          <div className="mb-2 flex items-center justify-between px-1">
            <h3 className="text-sm font-bold text-white">Χάρτης Αθήνας</h3>
            <span className="text-[11px] text-white/40">Dark Gray · ζωντανά tickets</span>
          </div>
          <div ref={mapNode} className="h-[520px] w-full overflow-hidden rounded-2xl" />
          {!window.L && <p className="mt-2 text-xs text-rose-200">Ο χάρτης δεν φορτώθηκε.</p>}
        </section>

        <section className="ops-panel flex flex-col p-4 lg:col-span-4">
          <h3 className="text-sm font-bold text-white">Φορτίο ανά φορέα</h3>
          <ul className="mt-3 space-y-2">
            {agencyRows.map((row) => (
              <li key={row.code}>
                <div className="mb-1 flex items-center justify-between text-xs">
                  <span className="font-semibold" style={{ color: row.style.strokeColor }}>{row.style.fullLabel}</span>
                  <span className="font-mono text-white/70">{row.count}</span>
                </div>
                <div className="h-1.5 overflow-hidden rounded-full bg-white/10">
                  <div className="h-full rounded-full" style={{ width: `${(row.count / row.max) * 100}%`, background: row.style.strokeColor }} />
                </div>
              </li>
            ))}
          </ul>
          <div className="mt-4">
            <h3 className="text-sm font-bold text-white">Δημοτικές κοινότητες</h3>
            {communities.length === 0 ? (
              <p className="mt-2 text-xs leading-relaxed text-white/50">Οι κοινότητες γράφονται από τον Agent γεωγραφίας μόλις κλείσει μια αναφορά πολίτη. Ο χάρτης δείχνει ήδη τα απεσταλμένα tickets.</p>
            ) : (
              <ul className="mt-2 flex flex-wrap gap-1.5">
                {communities.map(([name, count]) => (
                  <li key={name} className="rounded-full border border-white/10 px-2 py-1 text-[11px] text-white/75">{name} · {count}</li>
                ))}
              </ul>
            )}
          </div>
          <div className="mt-auto pt-4">
            <button type="button" disabled={briefingBusy} onClick={askBriefing} className="inline-flex w-full items-center justify-center gap-2 rounded-2xl bg-brass-300 px-3 py-2.5 text-sm font-extrabold text-ink-950 hover:bg-brass-200 disabled:opacity-70">
              {briefingBusy ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />}
              Στρατηγική αναφορά AI
            </button>
            {briefingError && <p className="mt-2 text-xs text-rose-200">{briefingError}</p>}
          </div>
        </section>
      </div>

      {briefing && (
        <section className="ops-panel p-5">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div className="max-w-3xl">
              <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-brass-300">Αναφορά προς τον Δήμαρχο</p>
              <h3 className="mt-1 font-serif text-3xl leading-tight text-white">{briefing.headline_summary_el}</h3>
            </div>
            <div className="text-right">
              <div className="font-serif text-4xl text-brass-200">{briefing.estimated_efficiency_gain_pct}%</div>
              <div className="text-[11px] uppercase tracking-[0.14em] text-white/40">εκτιμώμενο όφελος</div>
            </div>
          </div>
          <div className="mt-4 grid gap-4 md:grid-cols-2">
            <div>
              <h4 className="text-xs font-bold uppercase tracking-[0.14em] text-white/40">Συσχετίσεις φορέων</h4>
              <ul className="mt-2 space-y-1.5 text-sm text-white/80">
                {(briefing.cross_agency_clusters_el || []).map((item) => <li key={item}>· {item}</li>)}
              </ul>
            </div>
            <div>
              <h4 className="text-xs font-bold uppercase tracking-[0.14em] text-white/40">Προτεραιότητα αποστολής</h4>
              <ol className="mt-2 list-decimal space-y-1.5 pl-4 text-sm text-white/80">
                {(briefing.priority_dispatch_recommendations_el || []).map((item) => <li key={item}>{item}</li>)}
              </ol>
            </div>
          </div>
        </section>
      )}

      <section className="ops-panel overflow-hidden">
        <div className="flex items-center justify-between px-4 py-3">
          <h3 className="text-sm font-bold text-white">Μητρώο tickets</h3>
          <span className="text-[11px] text-white/40">Κλικ για εστίαση στον χάρτη</span>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full min-w-[720px] text-left text-xs">
            <thead className="text-[10px] uppercase tracking-[0.14em] text-white/35">
              <tr>
                <th className="px-4 py-2 font-semibold">Πρωτόκολλο</th>
                <th className="px-3 py-2 font-semibold">Φορέας</th>
                <th className="px-3 py-2 font-semibold">Θέμα</th>
                <th className="px-3 py-2 font-semibold">SLA</th>
                <th className="px-3 py-2 font-semibold">Επείγον</th>
                <th className="px-3 py-2 font-semibold">HTTP</th>
              </tr>
            </thead>
            <tbody>
              {tickets.map((ticket) => {
                const style = agencyStyle(ticket.target_agency);
                const selected = ticket.ticket_id === selectedId;
                return (
                  <tr
                    key={ticket.ticket_id}
                    role="button"
                    tabIndex={0}
                    onClick={() => focusTicket(ticket.ticket_id)}
                    onKeyDown={(event) => {
                      if (event.key === 'Enter' || event.key === ' ') {
                        event.preventDefault();
                        focusTicket(ticket.ticket_id);
                      }
                    }}
                    className={`cursor-pointer border-t border-white/5 ${selected ? 'bg-brass-300/10' : 'hover:bg-white/5'}`}
                  >
                    <td className="px-4 py-2.5 font-mono font-semibold text-white">
                      {ticket.ticket_id}
                      <div className="font-sans text-[10px] font-normal text-white/35">{formatWhen(ticket.created_at)}</div>
                    </td>
                    <td className="px-3 py-2.5 font-bold" style={{ color: style.strokeColor }}>{style.shortLabel}</td>
                    <td className="px-3 py-2.5 text-white/80">{ticket.ticket_title_el}</td>
                    <td className="px-3 py-2.5 text-white">{ticket.target_sla_hours}ω</td>
                    <td className="px-3 py-2.5 text-white/70">{urgencyLabel(ticket.urgency_level)}</td>
                    <td className="px-3 py-2.5 font-mono text-emerald-200">{ticket.http_status_code}</td>
                  </tr>
                );
              })}
              {!tickets.length && (
                <tr><td colSpan={6} className="px-4 py-6 text-white/45">Δεν υπάρχουν απεσταλμένα tickets.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
