"use client";

import { useEffect, useRef, useState } from "react";
import dynamic from "next/dynamic";
import {
  FileText, HelpCircle, User, Plus, X, LayoutDashboard, MessageSquare,
} from "lucide-react";
import {
  uploadDocument, getPipelineStatus,
  type AudienceSettings, type InsightSelection, type PipelineStatus,
} from "@/lib/api";

const AreaMap = dynamic(() => import("@/components/AreaMap"), {
  ssr: false,
  loading: () => <div className="h-[220px] w-full animate-pulse rounded-xl bg-gray-100" />,
});

const ACCENT = "#0078d4";
const ACCEPTED = ".txt,.pptx,.pdf,.md,.doc,.docx";

const AUDIENCE_TYPES = ["Business", "Academic", "Student", "Casual"];
const ENVIRONMENTS = ["Professional", "Casual"];
const SIZES = [
  { label: "Global Groups", hint: "(1,0M+)", value: 1_000_000 },
  { label: "Big Groups", hint: "(100,000 - 10,000)", value: 100_000 },
  { label: "Small Groups", hint: "(9,000 - 1,000)", value: 9_000 },
  { label: "Local Groups", hint: "(100+)", value: 100 },
];
const GENDERS = [
  { label: "General", value: "generic" },
  { label: "Oriented to Male", value: "male" },
  { label: "Oriented to Female", value: "female" },
];
const GOAL_CHIPS = ["Engagement", "Marketing", "Other options"];

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block mb-6">
      <span className="block text-sm text-gray-500 mb-1.5">{label}</span>
      {children}
    </label>
  );
}

function Radio({ checked, onChange, label, hint }: { checked: boolean; onChange: () => void; label: string; hint?: string }) {
  return (
    <label className="flex items-center gap-2 py-1.5 cursor-pointer text-sm">
      <input type="radio" checked={checked} onChange={onChange} className="accent-[#0078d4]" />
      <span className="text-gray-700">{label}</span>
      {hint && <span className="text-gray-400 ml-1">{hint}</span>}
    </label>
  );
}

export default function Home() {
  const [logoOk, setLogoOk] = useState(true);
  const [file, setFile] = useState<File | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  const [audienceType, setAudienceType] = useState("Business");
  const [environment, setEnvironment] = useState("Professional");
  const [area, setArea] = useState("");
  const [size, setSize] = useState(9_000);
  const [gender, setGender] = useState("generic");
  const [minAge, setMinAge] = useState(20);
  const [maxAge, setMaxAge] = useState(45);
  const [format, setFormat] = useState<"dashboard" | "chat">("dashboard");

  const [mainGoal, setMainGoal] = useState("");
  const [extraGoals, setExtraGoals] = useState<string[]>([]);
  const [goals, setGoals] = useState<string[]>([]);
  const [insights, setInsights] = useState<InsightSelection>({
    detect_strengts: true, detect_weakness: true, detect_potential: false, general_report: false,
  });

  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [productId, setProductId] = useState<string | null>(null);
  const [status, setStatus] = useState<PipelineStatus | null>(null);

  const toggleGoal = (g: string) =>
    setGoals((cur) => (cur.includes(g) ? cur.filter((x) => x !== g) : [...cur, g]));
  const toggleInsight = (k: keyof InsightSelection) =>
    setInsights((cur) => ({ ...cur, [k]: !cur[k] }));
  const setExtra = (i: number, v: string) =>
    setExtraGoals((cur) => cur.map((g, idx) => (idx === i ? v : g)));
  const removeExtra = (i: number) =>
    setExtraGoals((cur) => cur.filter((_, idx) => idx !== i));

  async function handleSend() {
    if (!file) { setError("Please upload a document first."); return; }
    setSending(true);
    setError(null);
    setStatus(null);
    const allGoals = [mainGoal, ...extraGoals].map((g) => g.trim()).filter(Boolean).join(" | ");
    const settings: AudienceSettings = {
      audience_type: audienceType,
      audience_enviroment: environment,
      audience_area: area,
      audience_size: size,
      gender_dstn: gender,
      age_dstn: `${minAge}-${maxAge}`,
      main_goal: allGoals,
      response_goal: goals.join(", "),
    };
    try {
      const res = await uploadDocument(file, settings, insights);
      setProductId(res.id_product);
    } catch (e) {
      setError(e instanceof Error ? e.message : "upload failed");
    } finally {
      setSending(false);
    }
  }

  useEffect(() => {
    if (!productId) return;
    let active = true;
    const tick = async () => {
      try {
        const s = await getPipelineStatus(productId);
        if (active) setStatus(s);
        if (active && s.product.status !== "analyzed") setTimeout(tick, 3000);
      } catch {
        if (active) setTimeout(tick, 4000);
      }
    };
    tick();
    return () => { active = false; };
  }, [productId]);

  const inputCls = "w-full rounded-full bg-gray-200/70 px-4 py-2.5 text-sm text-gray-700 outline-none focus:ring-2 focus:ring-[#0078d4]/40";

  return (
    <div className="min-h-screen bg-gray-50 text-gray-800">
      {/* ── header ── */}
      <header className="flex items-center justify-between px-8 py-4 border-b border-gray-200 bg-white">
        {logoOk ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img src="/logo.png" alt="ONLOOKER" className="h-9 w-auto" onError={() => setLogoOk(false)} />
        ) : (
          <div className="flex items-center gap-1 text-2xl font-semibold tracking-tight text-gray-700">
            <span style={{ color: ACCENT }}>O</span>NL<span style={{ color: ACCENT }}>OO</span>KER
          </div>
        )}
        <nav className="flex items-center gap-8 text-sm text-gray-600">
          <a className="hover:text-gray-900" href="#">Dashboard</a>
          <a className="hover:text-gray-900" href="#">Documentation</a>
          <span className="flex h-8 w-8 items-center justify-center rounded-full bg-gray-100"><HelpCircle size={18} /></span>
          <span className="flex h-9 w-9 items-center justify-center rounded-full bg-gray-100"><User size={20} /></span>
        </nav>
      </header>

      <main className="mx-auto max-w-7xl px-8 py-6">
        {/* ── upload ── */}
        <div className="flex items-center justify-between mb-2">
          <h1 className="flex items-center gap-2 text-lg text-gray-600">
            <FileText size={18} /> Upload The Characteristics of Your Service
          </h1>
          <span className="text-xs text-gray-400">{ACCEPTED.replaceAll(",", ", ")}</span>
        </div>
        <button
          onClick={() => fileRef.current?.click()}
          className="w-full rounded-2xl border border-dashed border-gray-300 bg-gray-100 py-6 text-sm text-gray-500 hover:bg-gray-200/60"
        >
          {file ? `📄 ${file.name}` : "Click to upload a document"}
        </button>
        <input ref={fileRef} type="file" accept={ACCEPTED} hidden
          onChange={(e) => { setFile(e.target.files?.[0] ?? null); setError(null); }} />

        {/* ── two columns ── */}
        <div className="mt-8 grid grid-cols-1 gap-8 lg:grid-cols-2">
          {/* LEFT */}
          <section>
            <h2 className="text-xl text-gray-700">Configure Your Audience</h2>
            <p className="mb-4 text-xs text-gray-400">Keep in mind that this is the audience you want to attract to your project; this is your audience&apos;s profile.</p>
            <div className="rounded-2xl border border-gray-200 bg-white p-6">
              <div className="grid grid-cols-1 gap-x-10 md:grid-cols-2 md:divide-x md:divide-gray-100">
                {/* col 1 */}
                <div className="md:pr-8">
                  <Field label="Type of Audience">
                    <select value={audienceType} onChange={(e) => setAudienceType(e.target.value)} className={inputCls}>
                      {AUDIENCE_TYPES.map((t) => <option key={t}>{t}</option>)}
                    </select>
                  </Field>
                  <Field label="Environment">
                    <select value={environment} onChange={(e) => setEnvironment(e.target.value)} className={inputCls}>
                      {ENVIRONMENTS.map((t) => <option key={t}>{t}</option>)}
                    </select>
                  </Field>
                  <Field label="Area (Optional) — New York City">
                    <AreaMap onChange={setArea} />
                  </Field>

                  <p className="mt-2 mb-2 text-sm text-gray-500">Select Format</p>
                  <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                    {([
                      { id: "dashboard", Icon: LayoutDashboard, title: "Dashboard", desc: "See the scores and feature scores given by the audience to your service." },
                      { id: "chat", Icon: MessageSquare, title: "Chat", desc: "The audience is a chatbot you can interact with and ask specific questions." },
                    ] as const).map(({ id, Icon, title, desc }) => (
                      <button key={id} onClick={() => setFormat(id)}
                        className={`rounded-xl border p-3 text-left transition ${format === id ? "border-[#0078d4] bg-[#0078d4]/5" : "border-gray-200 bg-gray-50 hover:bg-gray-100"}`}>
                        <div className="flex items-center gap-2 text-sm font-medium text-gray-700"><Icon size={16} /> {title}</div>
                        <p className="mt-1 text-xs text-gray-400">{desc}</p>
                      </button>
                    ))}
                  </div>
                </div>

                {/* col 2 */}
                <div className="mt-8 md:mt-0 md:pl-8">
                  <p className="mb-3 text-sm font-semibold text-gray-600">Extra Characteristics</p>

                  <p className="mt-3 mb-1 text-sm text-gray-500">Gender Distribution</p>
                  {GENDERS.map((g) => (
                    <Radio key={g.value} checked={gender === g.value} onChange={() => setGender(g.value)} label={g.label} />
                  ))}

                  <p className="mt-5 mb-1 text-sm text-gray-500">Audience Size</p>
                  {SIZES.map((s) => (
                    <Radio key={s.value} checked={size === s.value} onChange={() => setSize(s.value)} label={s.label} hint={s.hint} />
                  ))}

                  <p className="mt-5 mb-1 text-sm text-gray-500">Age Distribution</p>
                  <p className="mb-2 text-xs font-medium text-gray-600">{minAge} - {maxAge} years</p>
                  <div className="dual-range">
                    <div className="absolute left-0 right-0 top-1/2 h-1 -translate-y-1/2 rounded bg-gray-200" />
                    <div className="absolute top-1/2 h-1 -translate-y-1/2 rounded bg-[#0078d4]"
                      style={{ left: `${minAge}%`, right: `${100 - maxAge}%` }} />
                    <input type="range" min={0} max={100} value={minAge}
                      onChange={(e) => setMinAge(Math.min(+e.target.value, maxAge))} />
                    <input type="range" min={0} max={100} value={maxAge}
                      onChange={(e) => setMaxAge(Math.max(+e.target.value, minAge))} />
                  </div>
                </div>
              </div>
            </div>
          </section>

          {/* RIGHT */}
          <section>
            <div className="flex items-start justify-between">
              <div>
                <h2 className="text-xl text-gray-700">Describe your Goals</h2>
                <p className="mb-4 text-xs text-gray-400">Define your specific goals here, including desired audience responses or core product objectives.</p>
              </div>
              <span className="text-xs text-gray-400">Optional*</span>
            </div>

            <div className="rounded-2xl border border-gray-200 bg-white p-6">
              <p className="mb-2 text-base text-gray-700">Main Goal</p>
              <textarea value={mainGoal} onChange={(e) => setMainGoal(e.target.value)} rows={4}
                placeholder="Type your primary goal here ..."
                className="w-full resize-none rounded-xl bg-gray-100 p-3 text-sm text-gray-700 outline-none focus:ring-2 focus:ring-[#0078d4]/40" />

              {extraGoals.map((g, i) => (
                <div key={i} className="mt-2 flex items-start gap-2">
                  <textarea value={g} onChange={(e) => setExtra(i, e.target.value)} rows={2}
                    placeholder={`Additional goal ${i + 1} ...`}
                    className="w-full resize-none rounded-xl bg-gray-100 p-3 text-sm text-gray-700 outline-none focus:ring-2 focus:ring-[#0078d4]/40" />
                  <button onClick={() => removeExtra(i)} className="mt-1 text-gray-400 hover:text-red-500"><X size={16} /></button>
                </div>
              ))}

              <div className="mt-3 flex flex-wrap items-center gap-2 text-xs text-gray-500">
                <span>Oriented to Generate:</span>
                {GOAL_CHIPS.map((g) => (
                  <button key={g} onClick={() => toggleGoal(g)}
                    className={`rounded-full px-3 py-1 ${goals.includes(g) ? "bg-[#0078d4] text-white" : "bg-gray-200 text-gray-600 hover:bg-gray-300"}`}>{g}</button>
                ))}
              </div>
              <div className="mt-3 flex justify-center">
                <button onClick={() => setExtraGoals((cur) => [...cur, ""])} title="Add another goal"
                  className="flex h-8 w-8 items-center justify-center rounded-full bg-gray-100 text-gray-500 hover:bg-[#0078d4] hover:text-white">
                  <Plus size={16} />
                </button>
              </div>
            </div>

            <div className="mt-10">
              <h3 className="mb-3 text-lg text-gray-700">Insights to Generate</h3>
              {([
                ["detect_strengts", "Detect Strenghts Of My Product"],
                ["detect_weakness", "Detect Weakness of My Product"],
                ["detect_potential", "Detect Potentialities of my Product"],
                ["general_report", "General Report"],
              ] as const).map(([k, label]) => (
                <label key={k} className="flex items-center gap-3 py-2 text-sm text-gray-700 cursor-pointer">
                  <input type="checkbox" checked={insights[k]} onChange={() => toggleInsight(k)} className="h-4 w-4 accent-[#0078d4]" />
                  {label}
                </label>
              ))}
            </div>
          </section>
        </div>

        {/* ── send + status ── */}
        <div className="mt-8 flex flex-col items-end gap-2">
          {error && <p className="text-sm text-red-600">{error}</p>}
          {!file && !error && <p className="text-xs text-gray-400">Upload a document to enable analysis.</p>}
          <button onClick={handleSend} disabled={sending}
            className="rounded-lg px-12 py-2.5 text-sm font-medium text-white shadow-sm transition disabled:cursor-not-allowed disabled:opacity-60"
            style={{ backgroundColor: ACCENT }}>
            {sending ? "Sending…" : "Send"}
          </button>
        </div>

        {status && (
          <div className="mt-6 rounded-2xl border border-gray-200 bg-white p-6">
            <p className="text-sm text-gray-600">
              Product <code className="text-xs">{status.product.id_product}</code> — status:{" "}
              <span className="font-medium" style={{ color: ACCENT }}>{status.product.status}</span>
              {" · "}{status.n_responses} audience responses
            </p>
            {status.analysis && (
              <div className="mt-3 grid grid-cols-1 gap-4 text-sm md:grid-cols-2">
                {status.analysis.strengths?.length ? (
                  <div><p className="font-medium text-green-700">Strengths</p><ul className="list-disc pl-5 text-gray-600">{status.analysis.strengths.map((s, i) => <li key={i}>{s}</li>)}</ul></div>
                ) : null}
                {status.analysis.weakness?.length ? (
                  <div><p className="font-medium text-red-700">Weaknesses</p><ul className="list-disc pl-5 text-gray-600">{status.analysis.weakness.map((s, i) => <li key={i}>{s}</li>)}</ul></div>
                ) : null}
                {status.analysis.points_with_potential?.length ? (
                  <div><p className="font-medium text-amber-700">Potential</p><ul className="list-disc pl-5 text-gray-600">{status.analysis.points_with_potential.map((s, i) => <li key={i}>{s}</li>)}</ul></div>
                ) : null}
                {status.analysis.audience_response_analysis ? (
                  <div><p className="font-medium text-gray-700">Report</p><p className="text-gray-600">{status.analysis.audience_response_analysis}</p></div>
                ) : null}
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}
