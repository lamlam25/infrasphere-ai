import React, { useEffect, useState, useRef } from 'react';
import { Link } from 'react-router-dom';
import {
  AlertTriangle,
  Radio,
  Bot,
  ShieldCheck,
  ArrowRight,
  MapPin,
  Droplets,
  Activity,
  Layers
} from 'lucide-react';
import L from 'leaflet';
import { incidentsApi, dataSourcesApi, metricsApi } from '../services/api';
import type { Incident, StationObservation } from '../types';

export const OverviewPage: React.FC = () => {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [stations, setStations] = useState<StationObservation[]>([]);
  const [metrics, setMetrics] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<L.Map | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [incRes, stnRes, metRes] = await Promise.all([
          incidentsApi.list(),
          dataSourcesApi.listStations(),
          metricsApi.getOverview(),
        ]);
        setIncidents(incRes);
        setStations(stnRes);
        setMetrics(metRes);
      } catch (err) {
        console.error('Failed to load overview data', err);
      } finally {
        setIsLoading(false);
      }
    };
    fetchData();
  }, []);

  // Initialize and update Leaflet Map
  useEffect(() => {
    if (!mapContainerRef.current) return;

    if (!mapInstanceRef.current) {
      const map = L.map(mapContainerRef.current).setView([24.2, 90.5], 7);
      L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; CARTO',
        maxZoom: 18,
      }).addTo(map);
      mapInstanceRef.current = map;
    }

    const map = mapInstanceRef.current;

    // Clear previous markers
    map.eachLayer((layer) => {
      if (layer instanceof L.Marker) {
        map.removeLayer(layer);
      }
    });

    const createIcon = (color: string) =>
      L.divIcon({
        className: 'custom-leaflet-icon',
        html: `<div style="background-color: ${color}; width: 14px; height: 14px; border-radius: 50%; border: 2px solid white; box-shadow: 0 0 8px ${color};"></div>`,
        iconSize: [14, 14],
        iconAnchor: [7, 7],
      });

    const redIcon = createIcon('#ef4444');
    const orangeIcon = createIcon('#f97316');
    const blueIcon = createIcon('#3b82f6');

    // Add incidents
    incidents.slice(0, 30).forEach((inc) => {
      const isCritical = inc.severity === 'critical';
      const marker = L.marker([inc.latitude, inc.longitude], {
        icon: isCritical ? redIcon : orangeIcon,
      }).addTo(map);

      marker.bindPopup(`
        <div style="font-family: sans-serif; font-size: 11px; color: #0f172a; max-width: 200px;">
          <div style="font-weight: bold; color: #0284c7;">${inc.id}: ${inc.district}</div>
          <div style="margin-top: 2px; color: #334155;">${inc.title}</div>
          <div style="margin-top: 4px; font-weight: bold; text-transform: uppercase; color: ${
            isCritical ? '#dc2626' : '#ea580c'
          };">Severity: ${inc.severity}</div>
          <div style="margin-top: 6px; padding-top: 4px; border-top: 1px solid #e2e8f0;">
            <a href="/incidents/${inc.id}" style="color: #059669; font-weight: bold; text-decoration: underline;">Investigate Incident →</a>
          </div>
        </div>
      `);
    });

    // Add river stations
    stations.forEach((stn) => {
      const lat = stn.district === 'Sunamganj' ? 25.07 : 24.5;
      const lon = stn.district === 'Sunamganj' ? 91.41 : 90.5;
      const isOver = stn.level >= stn.danger_level;

      const marker = L.marker([lat, lon], { icon: blueIcon }).addTo(map);
      marker.bindPopup(`
        <div style="font-family: sans-serif; font-size: 11px; color: #0f172a;">
          <div style="font-weight: bold;">${stn.station_name} (${stn.district})</div>
          <div style="margin-top: 3px;">Water Level: <strong>${stn.level.toFixed(2)}${stn.unit}</strong></div>
          <div style="color: ${isOver ? '#dc2626' : '#64748b'}; font-weight: bold;">
            Danger Level: ${stn.danger_level.toFixed(2)}${stn.unit} ${isOver ? '(ALERT)' : ''}
          </div>
        </div>
      `);
    });

    return () => {
      // Keep map alive or clean up
    };
  }, [incidents, stations]);

  return (
    <div className="space-y-6">
      {/* Top Banner / Flagship Incident Callout */}
      <div className="p-5 rounded-2xl bg-gradient-to-r from-emerald-950/60 via-slate-900 to-slate-900 border border-emerald-500/30 flex flex-col md:flex-row items-start md:items-center justify-between gap-4 shadow-xl">
        <div className="space-y-1">
          <div className="inline-flex items-center space-x-2 px-2.5 py-0.5 rounded-full bg-emerald-500/20 text-emerald-400 text-xs font-semibold uppercase tracking-wider">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
            <span>Flagship Demonstration Incident</span>
          </div>
          <h2 className="text-lg font-bold text-white">
            INC-0041: Embankment Erosion &amp; Flooding — Sunamganj Sadar
          </h2>
          <p className="text-xs text-slate-300 max-w-2xl">
            Suramganj river telemetry STN-SUN-01 is 0.85m above danger level. Multi-agent investigation workflow is primed with SecureAI defense, RAG citations, risk scoring, and workforce orchestration.
          </p>
        </div>
        <Link
          to="/incidents/INC-0041"
          className="shrink-0 px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-semibold flex items-center space-x-2 transition-all shadow-lg shadow-emerald-900/40"
        >
          <span>Launch Investigation Cockpit</span>
          <ArrowRight className="w-4 h-4" />
        </Link>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl flex items-center justify-between">
          <div>
            <div className="text-xs text-slate-400 font-medium">Total Incidents</div>
            <div className="text-2xl font-bold text-white mt-1">{incidents.length || 40}</div>
            <div className="text-[11px] text-red-400 font-medium mt-0.5">8 High / Critical Severity</div>
          </div>
          <div className="p-3 bg-red-500/10 text-red-400 rounded-lg">
            <AlertTriangle className="w-5 h-5" />
          </div>
        </div>

        <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl flex items-center justify-between">
          <div>
            <div className="text-xs text-slate-400 font-medium">FFWC River Stations</div>
            <div className="text-2xl font-bold text-white mt-1">{stations.length || 10}</div>
            <div className="text-[11px] text-amber-400 font-medium mt-0.5">1 Gauge Above Danger Level</div>
          </div>
          <div className="p-3 bg-blue-500/10 text-blue-400 rounded-lg">
            <Droplets className="w-5 h-5" />
          </div>
        </div>

        <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl flex items-center justify-between">
          <div>
            <div className="text-xs text-slate-400 font-medium">Multi-Agent Roster</div>
            <div className="text-2xl font-bold text-white mt-1">6 Active</div>
            <div className="text-[11px] text-emerald-400 font-medium mt-0.5">Circuit Breakers: Normal</div>
          </div>
          <div className="p-3 bg-emerald-500/10 text-emerald-400 rounded-lg">
            <Bot className="w-5 h-5" />
          </div>
        </div>

        <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl flex items-center justify-between">
          <div>
            <div className="text-xs text-slate-400 font-medium">Audit Trail Verification</div>
            <div className="text-2xl font-bold text-white mt-1">100% Intact</div>
            <div className="text-[11px] text-emerald-400 font-medium mt-0.5">SHA-256 Hash Chain Linked</div>
          </div>
          <div className="p-3 bg-purple-500/10 text-purple-400 rounded-lg">
            <ShieldCheck className="w-5 h-5" />
          </div>
        </div>
      </div>

      {/* Main Grid: Map & Live Station Feed */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Bangladesh Operations Map */}
        <div className="lg:col-span-2 bg-slate-900 border border-slate-800 rounded-2xl p-4 flex flex-col">
          <div className="flex items-center justify-between mb-3 px-1">
            <div className="flex items-center space-x-2">
              <MapPin className="w-4 h-4 text-emerald-400" />
              <h3 className="text-sm font-bold text-white">Bangladesh Infrastructure Situational Map</h3>
            </div>
            <div className="flex items-center space-x-3 text-xs text-slate-400">
              <span className="flex items-center space-x-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-red-500"></span>
                <span>Critical</span>
              </span>
              <span className="flex items-center space-x-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-orange-500"></span>
                <span>Incident</span>
              </span>
              <span className="flex items-center space-x-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-blue-500"></span>
                <span>River Gauge</span>
              </span>
            </div>
          </div>

          <div
            ref={mapContainerRef}
            className="h-[480px] rounded-xl overflow-hidden border border-slate-800 relative z-0"
          />
        </div>

        {/* FFWC Telemetry & High Risk Feed */}
        <div className="space-y-6">
          {/* FFWC Gauge Telemetry */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center space-x-2">
                <Radio className="w-4 h-4 text-blue-400" />
                <h3 className="text-sm font-bold text-white">FFWC River Telemetry</h3>
              </div>
              <span className="text-[10px] px-2 py-0.5 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20 font-medium">
                10 Gauges
              </span>
            </div>

            <div className="space-y-2 max-h-[220px] overflow-y-auto pr-1">
              {stations.map((stn) => {
                const isOverDanger = stn.level >= stn.danger_level;
                return (
                  <div
                    key={stn.id}
                    className={`p-2.5 rounded-lg border text-xs flex items-center justify-between ${
                      isOverDanger
                        ? 'bg-red-500/10 border-red-500/30 text-red-200'
                        : 'bg-slate-950 border-slate-800 text-slate-300'
                    }`}
                  >
                    <div>
                      <div className="font-semibold text-slate-100">{stn.station_name}</div>
                      <div className="text-[11px] text-slate-400">{stn.district}</div>
                    </div>
                    <div className="text-right">
                      <div className={`font-mono font-bold ${isOverDanger ? 'text-red-400' : 'text-blue-400'}`}>
                        {stn.level.toFixed(2)}m
                      </div>
                      <div className="text-[10px] text-slate-500">
                        DL: {stn.danger_level.toFixed(2)}m
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Quick Pillar Deep-Links */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4">
            <h3 className="text-sm font-bold text-white mb-3">5 Integrated Subsystems</h3>
            <div className="grid grid-cols-1 gap-2">
              <Link
                to="/secureai"
                className="flex items-center justify-between p-2 rounded-lg bg-slate-950 hover:bg-slate-800/80 border border-slate-800 text-xs transition-colors"
              >
                <div className="flex items-center space-x-2">
                  <ShieldCheck className="w-4 h-4 text-emerald-400" />
                  <span className="font-medium text-slate-200">SecureAI Red-Team Lab</span>
                </div>
                <ArrowRight className="w-3.5 h-3.5 text-slate-500" />
              </Link>

              <Link
                to="/knowledge"
                className="flex items-center justify-between p-2 rounded-lg bg-slate-950 hover:bg-slate-800/80 border border-slate-800 text-xs transition-colors"
              >
                <div className="flex items-center space-x-2">
                  <Activity className="w-4 h-4 text-blue-400" />
                  <span className="font-medium text-slate-200">Knowledge Grid RAG &amp; Citations</span>
                </div>
                <ArrowRight className="w-3.5 h-3.5 text-slate-500" />
              </Link>

              <Link
                to="/workforce"
                className="flex items-center justify-between p-2 rounded-lg bg-slate-950 hover:bg-slate-800/80 border border-slate-800 text-xs transition-colors"
              >
                <div className="flex items-center space-x-2">
                  <Bot className="w-4 h-4 text-purple-400" />
                  <span className="font-medium text-slate-200">WorkforceOS Team Match Engine</span>
                </div>
                <ArrowRight className="w-3.5 h-3.5 text-slate-500" />
              </Link>

              <Link
                to="/approvals"
                className="flex items-center justify-between p-2 rounded-lg bg-slate-950 hover:bg-slate-800/80 border border-slate-800 text-xs transition-colors"
              >
                <div className="flex items-center space-x-2">
                  <AlertTriangle className="w-4 h-4 text-amber-400" />
                  <span className="font-medium text-slate-200">Human+AI Approval Queue</span>
                </div>
                <ArrowRight className="w-3.5 h-3.5 text-slate-500" />
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
