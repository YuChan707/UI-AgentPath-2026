"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { X, Upload, FileText, FileImage, CheckCircle2, XCircle } from "lucide-react";
import { useStore, FileQueueItem } from "@/lib/store";

interface Props {
  onClose: () => void;
}

const MAX_STORAGE_MB = 100;
const ACCEPTED = ".pptx,.docx,.pdf,.txt";
const ACCEPTED_TYPES = [".pptx", ".docx", ".pdf", ".txt"];

function fileIcon(name: string) {
  const ext = name.split(".").pop()?.toLowerCase() ?? "";
  if (ext === "pdf") return <FileImage size={18} color="#c4362c" strokeWidth={2} />;
  return <FileText size={18} color="#0078d4" strokeWidth={2} />;
}

function fmtBytes(bytes: number): string {
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

interface UploadEntry extends FileQueueItem {
  progress: number;
  done: boolean;
}

export default function UploadResourcesModal({ onClose }: Readonly<Props>) {
  const { fileQueue, enqueueFile, dequeueFile } = useStore();
  const [dragging, setDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Progress simulation per file uid
  const [progressMap, setProgressMap] = useState<Record<number, number>>({});

  // When a new file is added, animate its progress to 100
  useEffect(() => {
    fileQueue.forEach((item) => {
      if (progressMap[item.uid] === undefined) {
        setProgressMap((p) => ({ ...p, [item.uid]: 0 }));
        let current = 0;
        const tick = setInterval(() => {
          current += Math.random() * 18 + 8;
          if (current >= 100) {
            current = 100;
            clearInterval(tick);
          }
          setProgressMap((p) => ({ ...p, [item.uid]: Math.round(current) }));
        }, 80);
      }
    });
    // cleanup entries no longer in queue
    setProgressMap((p) => {
      const uids = new Set(fileQueue.map((f) => f.uid));
      const next = { ...p };
      Object.keys(next).forEach((k) => { if (!uids.has(Number(k))) delete next[Number(k)]; });
      return next;
    });
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [fileQueue]);

  const totalBytes = fileQueue.reduce((s, f) => s + f.file.size, 0);
  const usedMB = totalBytes / (1024 * 1024);
  const usedPct = Math.min((usedMB / MAX_STORAGE_MB) * 100, 100);

  const addFiles = useCallback((files: File[]) => {
    setError(null);
    const available = 3 - fileQueue.length;
    if (available <= 0) {
      setError("Maximum 3 files reached. Remove a file first.");
      return;
    }
    const filtered = files.filter((f) => {
      const ext = "." + (f.name.split(".").pop()?.toLowerCase() ?? "");
      return ACCEPTED_TYPES.includes(ext);
    });
    if (filtered.length === 0) {
      setError("Only .pptx, .docx, .pdf, .txt files are supported.");
      return;
    }
    filtered.slice(0, available).forEach((f) => enqueueFile(f));
  }, [fileQueue.length, enqueueFile]);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    addFiles(Array.from(e.target.files ?? []));
    e.target.value = "";
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    addFiles(Array.from(e.dataTransfer.files));
  };

  return (
    <div
      className="fixed inset-0 z-[200] flex items-center justify-center"
      style={{ background: "rgba(0,0,0,0.45)", backdropFilter: "blur(2px)" }}
      onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}
    >
      <div
        className="bg-white rounded-2xl shadow-2xl w-full max-w-[440px] mx-4 overflow-hidden"
        style={{ border: "1px solid rgba(0,0,0,0.08)" }}
      >
        {/* Header */}
        <div className="px-6 pt-6 pb-4 flex items-center justify-between">
          <h2 style={{ fontSize: 18, fontWeight: 700, color: "#111827" }}>Upload Resources</h2>
          <button
            onClick={onClose}
            className="flex items-center justify-center w-8 h-8 rounded-full transition-colors"
            style={{ background: "#f3f4f6" }}
            onMouseEnter={(e) => ((e.currentTarget as HTMLElement).style.background = "#e5e7eb")}
            onMouseLeave={(e) => ((e.currentTarget as HTMLElement).style.background = "#f3f4f6")}
          >
            <X size={16} color="#374151" strokeWidth={2.5} />
          </button>
        </div>

        <div className="px-6 pb-6 flex flex-col gap-4">
          {/* Drop zone */}
          <div
            onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
            onDragLeave={() => setDragging(false)}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            className="rounded-xl flex flex-col items-center justify-center gap-2 cursor-pointer transition-colors"
            style={{
              border: `2px dashed ${dragging ? "#0078d4" : "#d1d5db"}`,
              background: dragging ? "rgba(0,120,212,0.04)" : "#fafafa",
              padding: "28px 20px",
            }}
          >
            <div
              className="w-12 h-12 rounded-full flex items-center justify-center"
              style={{ background: "rgba(0,120,212,0.10)" }}
            >
              <Upload size={22} color="#0078d4" strokeWidth={2} />
            </div>
            <p style={{ fontSize: 14, fontWeight: 500, color: "#374151", textAlign: "center", lineHeight: 1.5 }}>
              Drag and drop your files here
              <br />
              <span style={{ color: "#9ca3af", fontWeight: 400 }}>or </span>
              <span style={{ color: "#0078d4", fontWeight: 600 }}>Browse files</span>
            </p>
            <div className="flex gap-2 flex-wrap justify-center">
              {ACCEPTED_TYPES.map((t) => (
                <span
                  key={t}
                  style={{
                    fontSize: 10,
                    fontFamily: "monospace",
                    fontWeight: 600,
                    background: "#f3f4f6",
                    color: "#6b7280",
                    borderRadius: 4,
                    padding: "2px 8px",
                  }}
                >
                  {t}
                </span>
              ))}
            </div>
          </div>
          <input
            ref={fileInputRef}
            type="file"
            multiple
            accept={ACCEPTED}
            style={{ display: "none" }}
            onChange={handleInputChange}
          />

          {/* Error */}
          {error && (
            <div className="flex items-center gap-2 px-3 py-2 rounded-lg" style={{ background: "rgba(196,54,44,0.07)" }}>
              <XCircle size={14} color="#c4362c" strokeWidth={2} />
              <span style={{ fontSize: 12, color: "#c4362c" }}>{error}</span>
            </div>
          )}

          {/* Current uploads */}
          {fileQueue.length > 0 && (
            <div>
              <p style={{ fontSize: 10, fontWeight: 700, color: "#6b7280", textTransform: "uppercase", letterSpacing: "0.1em", marginBottom: 10 }}>
                Current Uploads
              </p>
              <div className="flex flex-col gap-3">
                {fileQueue.map((item) => {
                  const pct = progressMap[item.uid] ?? 0;
                  const done = pct >= 100;
                  return (
                    <div
                      key={item.uid}
                      className="flex items-center gap-3 rounded-xl px-3 py-3"
                      style={{ background: "#f9fafb", border: "1px solid #f3f4f6" }}
                    >
                      <div className="flex-shrink-0">{fileIcon(item.name)}</div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between mb-1">
                          <span style={{ fontSize: 13, fontWeight: 600, color: "#111827", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", maxWidth: 200 }}>
                            {item.name}
                          </span>
                          {done
                            ? <CheckCircle2 size={16} color="#107c10" strokeWidth={2} />
                            : (
                              <button onClick={() => dequeueFile(item.uid)} style={{ background: "none", border: "none", cursor: "pointer", padding: 0, lineHeight: 0 }}>
                                <XCircle size={16} color="#9ca3af" strokeWidth={2} />
                              </button>
                            )
                          }
                        </div>
                        <div className="flex items-center gap-2">
                          <span style={{ fontSize: 11, color: "#6b7280", flexShrink: 0 }}>
                            {fmtBytes(item.file.size)} •{" "}
                            <span style={{ color: done ? "#107c10" : "#0078d4", fontWeight: 600 }}>
                              {done ? "Uploaded" : `${pct}% completed`}
                            </span>
                          </span>
                        </div>
                        <div className="mt-1.5 rounded-full overflow-hidden" style={{ height: 4, background: "#e5e7eb" }}>
                          <div
                            style={{
                              height: "100%",
                              width: `${pct}%`,
                              background: done ? "#107c10" : "#0078d4",
                              transition: "width 0.1s linear",
                              borderRadius: 9999,
                            }}
                          />
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Storage bar */}
          <div
            className="flex items-center gap-3 rounded-lg px-3 py-2"
            style={{ background: "#f9fafb", border: "1px solid #f3f4f6" }}
          >
            <span style={{ fontSize: 11, color: "#6b7280", flexShrink: 0 }}>
              Storage used: {usedMB.toFixed(1)} MB / {MAX_STORAGE_MB} MB
            </span>
            <div className="flex-1 rounded-full overflow-hidden" style={{ height: 4, background: "#e5e7eb" }}>
              <div style={{ height: "100%", width: `${usedPct}%`, background: "#0078d4", borderRadius: 9999 }} />
            </div>
          </div>

          {/* Actions */}
          <div className="flex items-center justify-end gap-3 pt-1">
            <button
              onClick={onClose}
              style={{ fontSize: 13, fontWeight: 600, color: "#6b7280", background: "none", border: "none", cursor: "pointer", letterSpacing: "0.02em" }}
            >
              Cancel
            </button>
            <button
              onClick={onClose}
              style={{
                fontSize: 13,
                fontWeight: 700,
                color: "#fff",
                background: "#0078d4",
                border: "none",
                borderRadius: 8,
                padding: "9px 24px",
                cursor: "pointer",
                letterSpacing: "0.04em",
              }}
            >
              Done
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
