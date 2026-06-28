"use client";

import { useState } from "react";
import { MapContainer, TileLayer, Marker, Polygon, useMapEvents } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

// Leaflet's default marker assets break under bundlers — point them at the CDN.
const ICON = L.icon({
  iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
  shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
  iconSize: [25, 41],
  iconAnchor: [12, 41],
});

const NYC: [number, number] = [40.7128, -74.006];
type Pt = [number, number];

function describe(pts: Pt[]): string {
  if (pts.length === 0) return "";
  if (pts.length < 3) {
    const [lat, lng] = pts[pts.length - 1];
    return `NYC @ ${lat.toFixed(4)},${lng.toFixed(4)}`;
  }
  const c = pts.reduce<[number, number]>((a, p) => [a[0] + p[0], a[1] + p[1]], [0, 0]);
  return `NYC zone (${pts.length} pts) ~${(c[0] / pts.length).toFixed(3)},${(c[1] / pts.length).toFixed(3)}`;
}

function ClickCapture({ onAdd }: { onAdd: (p: Pt) => void }) {
  useMapEvents({ click: (e) => onAdd([e.latlng.lat, e.latlng.lng]) });
  return null;
}

export default function AreaMap({ onChange }: { onChange: (desc: string) => void }) {
  const [pts, setPts] = useState<Pt[]>([]);

  const add = (p: Pt) => setPts((cur) => { const n = [...cur, p]; onChange(describe(n)); return n; });
  const clear = () => { setPts([]); onChange(""); };

  return (
    <div>
      <MapContainer center={NYC} zoom={11} scrollWheelZoom={false}
        style={{ height: 220, width: "100%", borderRadius: 12 }}>
        <TileLayer
          attribution='&copy; OpenStreetMap'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <ClickCapture onAdd={add} />
        {pts.map((p, i) => <Marker key={i} position={p} icon={ICON} />)}
        {pts.length >= 3 && <Polygon positions={pts} pathOptions={{ color: "#0078d4" }} />}
      </MapContainer>
      <div className="mt-1 flex items-center justify-between text-xs text-gray-500">
        <span>{pts.length === 0
          ? "Click the map to pick a location, or add 3+ points to draw a zone"
          : describe(pts)}</span>
        {pts.length > 0 && (
          <button type="button" onClick={clear} className="text-[#0078d4] hover:underline">Clear</button>
        )}
      </div>
    </div>
  );
}
