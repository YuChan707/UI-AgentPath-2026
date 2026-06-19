"use client";

import { useState, useEffect } from "react";
import { useStore } from "@/lib/store";

const API_BASE =
  (typeof process !== "undefined" && process.env.NEXT_PUBLIC_API_URL) ||
  "http://localhost:8000";

function toPersonaType(audience: string): string {
  if (audience === "Academic Researchers") return "executive";
  if (audience === "Business Executive") return "executive";
  if (audience === "Student") return "customer";
  return "customer";
}

function toRegion(location: string): string {
  const l = location.toLowerCase();
  if (l.includes("japan") || l.includes("tokyo") || l === "jp") return "jp";
  if (l.includes("uk") || l.includes("london") || l.includes("cambridge")) return "uk";
  if (l.includes("germany") || l.includes("berlin") || l === "de") return "de";
  return "us";
}

function toFocusArea(area: string): string {
  const map: Record<string, string> = {
    "Sciences": "science",
    "Technology": "technology",
    "Healthcare": "healthcare",
    "Research": "research",
    "Organization": "business",
    "Micro (Single Station)": "business",
  };
  return map[area] ?? "business";
}

const STORAGE_KEY = "onlooker_session_configured";

interface Props {
  onComplete?: () => void;
}

export default function SessionSettingsModal({ onComplete }: Readonly<Props>) {
  const [visible, setVisible] = useState(false);
  const [audience, setAudience] = useState("Academic Researchers");
  const [environment, setEnvironment] = useState("Controlled Laboratory");
  const [complexity, setComplexity] = useState("Standard POV");
  const [area, setArea] = useState("Micro (Single Station)");
  const [location, setLocation] = useState("");
  const [focusPeople, setFocusPeople] = useState("");
  const [loading, setLoading] = useState(false);

  const setSessionConfig = useStore((s) => s.setSessionConfig);
  const setSessionId = useStore((s) => s.setSessionId);

  useEffect(() => {
    if (globalThis.window !== undefined && !localStorage.getItem(STORAGE_KEY)) {
      setVisible(true);
    }
  }, []);

  const handleCancel = () => {
    setVisible(false);
    localStorage.setItem(STORAGE_KEY, "1");
    onComplete?.();
  };

  const handleStart = async () => {
    const personaType = toPersonaType(audience);
    const region = toRegion(location);
    const focusArea = toFocusArea(area);

    setSessionConfig({ personaType, region, focusArea, environment, complexity });
    setLoading(true);
    try {
      const params = new URLSearchParams({ persona_type: personaType, region, focus_area: focusArea });
      const res = await fetch(`${API_BASE}/session/start?${params}`, { method: "POST" });
      if (res.ok) {
        const data = await res.json();
        setSessionId(data.session_id);
      }
    } catch {
      // offline mode — continue without session
    } finally {
      setLoading(false);
    }

    localStorage.setItem(STORAGE_KEY, "1");
    setVisible(false);
    onComplete?.();
  };

  if (!visible) return null;

  return (
    <div
      className="fixed inset-0 z-[200] flex items-center justify-center"
      style={{ background: "rgba(0,0,0,0.45)", backdropFilter: "blur(2px)" }}
    >
      <div
        className="bg-white rounded-2xl shadow-2xl w-full max-w-[520px] mx-4 overflow-hidden"
        style={{ border: "1px solid rgba(0,0,0,0.08)" }}
      >
        {/* Header */}
        <div className="px-8 pt-8 pb-4">
          <h2 style={{ fontSize: 22, fontWeight: 700, color: "#111827", marginBottom: 6 }}>
            Session Settings
          </h2>
          <p style={{ fontSize: 13, color: "#6b7280", lineHeight: 1.5 }}>
            Configure the AI parameters for the current observation environment.
          </p>
        </div>

        {/* Divider */}
        <div style={{ height: 1, background: "#f3f4f6", marginBottom: 8 }} />

        {/* Form grid */}
        <div className="px-8 pb-6 grid grid-cols-2 gap-x-6 gap-y-5">
          {/* TYPE OF AUDIENCE */}
          <Field label="Type of Audience">
            <select value={audience} onChange={(e) => setAudience(e.target.value)}>
              <option>Academic Researchers</option>
              <option>Business Executive</option>
              <option>Student</option>
              <option>Casual (General)</option>
            </select>
          </Field>

          {/* ENVIRONMENT */}
          <Field label="Environment">
            <select value={environment} onChange={(e) => setEnvironment(e.target.value)}>
              <option>Controlled Laboratory</option>
              <option>Professional Presentation</option>
              <option>Casual Presentation</option>
            </select>
          </Field>

          {/* COMPLEXITY */}
          <Field label="Complexity">
            <select value={complexity} onChange={(e) => setComplexity(e.target.value)}>
              <option>Standard POV</option>
              <option>Low Level</option>
              <option>Medium Level</option>
              <option>High Level</option>
            </select>
          </Field>

          {/* AREA */}
          <Field label="Area">
            <select value={area} onChange={(e) => setArea(e.target.value)}>
              <option>Micro (Single Station)</option>
              <option>Sciences</option>
              <option>Technology</option>
              <option>Healthcare</option>
              <option>Research</option>
              <option>Organization</option>
            </select>
          </Field>

          {/* LOCATION */}
          <Field label="Location">
            <input
              type="text"
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              placeholder="e.g. Seattle HQ - Room 402"
            />
          </Field>

          {/* FOCUS PEOPLE */}
          <Field label="Focus People">
            <input
              type="text"
              value={focusPeople}
              onChange={(e) => setFocusPeople(e.target.value)}
              placeholder="e.g. Subject-A, User-882"
            />
          </Field>
        </div>

        {/* Actions */}
        <div
          className="px-8 py-5 flex items-center justify-end gap-4"
          style={{ borderTop: "1px solid #f3f4f6" }}
        >
          <button
            onClick={handleCancel}
            style={{ fontSize: 13, fontWeight: 600, color: "#6b7280", letterSpacing: "0.04em", textTransform: "uppercase", background: "none", border: "none", cursor: "pointer" }}
          >
            Cancel
          </button>
          <button
            onClick={handleStart}
            disabled={loading}
            style={{
              fontSize: 13,
              fontWeight: 700,
              color: "#fff",
              background: loading ? "#93c5fd" : "#0078d4",
              border: "none",
              borderRadius: 8,
              padding: "10px 24px",
              cursor: loading ? "not-allowed" : "pointer",
              letterSpacing: "0.06em",
              textTransform: "uppercase",
              transition: "background 0.15s",
            }}
          >
            {loading ? "Starting…" : "Start Session"}
          </button>
        </div>
      </div>
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex flex-col gap-2">
      <label
        style={{
          fontSize: 10,
          fontWeight: 700,
          color: "#374151",
          textTransform: "uppercase",
          letterSpacing: "0.1em",
        }}
      >
        {label}
      </label>
      <div
        style={{
          borderBottom: "1.5px solid #d1d5db",
          paddingBottom: 6,
        }}
      >
        {/* Shared styling applied via global CSS or inline on children */}
        <style>{`
          .ss-field select, .ss-field input {
            width: 100%;
            background: transparent;
            border: none;
            outline: none;
            font-size: 14px;
            color: #111827;
            padding: 0;
            appearance: none;
            cursor: pointer;
          }
          .ss-field select option { color: #111827; }
        `}</style>
        <div className="ss-field">{children}</div>
      </div>
    </div>
  );
}
