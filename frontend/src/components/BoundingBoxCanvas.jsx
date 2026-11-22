import React from 'react';
import { agencyStyle } from '../api/client';

export default function BoundingBoxCanvas({ imageDataUrl, detectedHazards = [], jurisdictionMappings = [], scanning = false }) {
  if (!imageDataUrl) {
    return (
      <div className="flex min-h-[340px] items-center justify-center rounded-2xl border-2 border-brass-300 bg-black/40 px-8 text-center shadow-[inset_0_0_0_8px_rgba(7,11,18,0.9)]">
        <p className="max-w-sm text-base font-semibold leading-relaxed text-white">Εδώ εμφανίζεται η φωτογραφία της αναφοράς.</p>
      </div>
    );
  }

  const geoMap = {};
  for (const mapping of jurisdictionMappings) geoMap[mapping.hazard_id] = mapping.final_agency;

  return (
    <div className="relative w-full overflow-hidden rounded-2xl border border-white/10 bg-ink-950">
      <img src={imageDataUrl} alt="Φωτογραφία αναφοράς πολίτη" className="block h-auto w-full" />
      <svg viewBox="0 0 1000 1000" preserveAspectRatio="none" className="pointer-events-none absolute inset-0 h-full w-full">
        {detectedHazards.map((hazard) => {
          const box = hazard.bounding_box || { ymin: 80, xmin: 80, ymax: 920, xmax: 920 };
          const agency = geoMap[hazard.hazard_id] || hazard.preliminary_agency || 'CITY_OF_ATHENS';
          const style = agencyStyle(agency);
          return (
            <rect
              key={hazard.hazard_id}
              x={box.xmin}
              y={box.ymin}
              width={Math.max(0, box.xmax - box.xmin)}
              height={Math.max(0, box.ymax - box.ymin)}
              fill={style.strokeColor}
              fillOpacity="0.18"
              stroke={style.strokeColor}
              strokeWidth="8"
              rx="14"
            >
              <title>{`${style.fullLabel}: ${hazard.title_el}`}</title>
            </rect>
          );
        })}
      </svg>
      {detectedHazards.map((hazard) => {
        const box = hazard.bounding_box || { ymin: 80, xmin: 80, ymax: 920, xmax: 920 };
        const agency = geoMap[hazard.hazard_id] || hazard.preliminary_agency || 'CITY_OF_ATHENS';
        const style = agencyStyle(agency);
        const placeAbove = box.ymin > 80;
        return (
          <div
            key={`${hazard.hazard_id}-label`}
            className="pointer-events-none absolute"
            style={{
              left: `${box.xmin / 10}%`,
              top: `${box.ymin / 10}%`,
              maxWidth: '70%',
            }}
          >
            <div
              className="inline-flex max-w-full items-center gap-1 rounded-md px-1.5 py-0.5 text-[10px] font-extrabold leading-tight text-ink-950 shadow-lg"
              style={{
                background: style.strokeColor,
                transform: placeAbove ? 'translateY(calc(-100% - 4px))' : 'translateY(6px)',
              }}
            >
              <span className="truncate">{style.shortLabel}</span>
              <span className="opacity-80">·</span>
              <span className="whitespace-nowrap">Σοβαρότητα {hazard.severity_score}/10</span>
            </div>
          </div>
        );
      })}
      {scanning && <div className="vision-scan" />}
    </div>
  );
}
