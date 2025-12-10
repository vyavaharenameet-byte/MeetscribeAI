import { useState, useRef } from "react";
import "./App.css";

const BACKEND = "http://127.0.0.1:8000";

function Spinner({ size = 20 }) {
  return (
    <div className="spinner" style={{ width: size, height: size }}>
      <div></div><div></div><div></div>
    </div>
  );
}

function IconFile() {
  return (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" className="icon-file" aria-hidden>
      <path d="M14 3H6a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round"/>
      <path d="M14 3v6h6" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  );
}

export default function App() {
  const [file, setFile] = useState(null);
  const [transcript, setTranscript] = useState("");
  const [minutes, setMinutes] = useState("");
  const [tasks, setTasks] = useState([]);
  const [isTranscribing, setIsTranscribing] = useState(false);
  const [isProcessingMinutes, setIsProcessingMinutes] = useState(false);
  const [isExporting, setIsExporting] = useState(false);
  const [docxUrl, setDocxUrl] = useState("");
  const [message, setMessage] = useState("");
  const inputRef = useRef();

  function handleFiles(files) {
    if (!files || files.length === 0) return;
    setFile(files[0]);
    setTranscript("");
    setMinutes("");
    setTasks([]);
    setDocxUrl("");
    setMessage("");
  }

  function onDrop(e) {
    e.preventDefault();
    handleFiles(e.dataTransfer.files);
  }
  function onDragOver(e) { e.preventDefault(); }

  async function transcribe() {
    if (!file) {
      setMessage("Please choose an audio file.");
      return;
    }
    setIsTranscribing(true);
    setMessage("");
    const fd = new FormData();
    fd.append("file", file);
    try {
      const res = await fetch(`${BACKEND}/transcribe`, { method: "POST", body: fd });
      if (!res.ok) throw new Error("Transcription failed");
      const data = await res.json();
      setTranscript(data.transcript || "");
      setMessage("Transcription complete.");
    } catch (e) {
      console.error(e);
      setMessage("Transcription failed. See console.");
    } finally {
      setIsTranscribing(false);
    }
  }

  async function generateMinutes() {
    if (!transcript || !transcript.trim()) {
      setMessage("No transcript to convert. Transcribe first.");
      return;
    }
    setIsProcessingMinutes(true);
    setMessage("");
    try {
      const res = await fetch(`${BACKEND}/summarize`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: transcript, num_sentences: 3 }),
      });
      if (!res.ok) throw new Error("Minutes generation failed");
      const data = await res.json();
      setMinutes(data.summary || "");
      setTasks((data.minutes && data.minutes.items) || []);
      setMessage("Minutes generated.");
    } catch (e) {
      console.error(e);
      setMessage("Minutes generation failed.");
    } finally {
      setIsProcessingMinutes(false);
    }
  }

  async function exportDocx() {
    if (!minutes) {
      setMessage("Generate minutes before exporting.");
      return;
    }
    setIsExporting(true);
    setMessage("");
    try {
      const res = await fetch(`${BACKEND}/docx`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title: "MeetScribe AI - Minutes", summary: minutes, minutes: { items: tasks } }),
      });
      if (!res.ok) throw new Error("docx failed");
      const data = await res.json();
      const url = `${BACKEND}${data.download}`;
      setDocxUrl(url);
      setMessage("DOCX ready.");
    } catch (e) {
      console.error(e);
      setMessage("DOCX creation failed.");
    } finally {
      setIsExporting(false);
    }
  }

  return (
    <div className="page app-root">
      <div className="grid-bg" />

      <header className="hero hero-cyber">
        <div className="hero-inner">
          <h1 className="brand">MeetScribe <span className="brand-accent">AI</span></h1>
          <p className="tagline">Record • Transcribe • Minutes of the Meeting • Export</p>
        </div>
      </header>

      <main className="main">
        <section
          className="card upload cyber-card"
          onDrop={onDrop}
          onDragOver={onDragOver}
          onClick={() => inputRef.current?.click()}
        >
          <div className="upload-left">
            <IconFile />
            <div>
              <div className="upl-title">Upload or drop audio</div>
              <div className="upl-sub">Supported: wav, mp3, m4a</div>
            </div>
          </div>

          <div className="upload-right">
            <input
              ref={inputRef}
              type="file"
              accept="audio/*"
              onChange={(e) => handleFiles(e.target.files)}
              style={{ display: "none" }}
            />
            <div className="file-info">{file ? file.name : "No file selected"}</div>

            <button
              className="btn neon"
              onClick={(e) => { e.stopPropagation(); transcribe(); }}
              disabled={isTranscribing}
            >
              {isTranscribing ? <Spinner size={18} /> : "Transcribe"}
            </button>
          </div>
        </section>

        <section className="grid-two">
          <div className="card cyber-card">
            <h3 className="section-title">Transcript</h3>
            <textarea className="mono-text" value={transcript} readOnly placeholder="Transcript will appear here..." />
            <div className="card-actions">
              <button className="btn ghost" onClick={() => { navigator.clipboard.writeText(transcript); setMessage("Copied transcript."); }}>Copy</button>
              <button className="btn ghost" onClick={() => { setTranscript(""); setMessage("Transcript cleared."); }}>Clear</button>
            </div>
          </div>

          <div className="card cyber-card">
            <h3 className="section-title">Minutes of the Meeting</h3>
            <textarea className="mono-text" value={minutes} readOnly placeholder="Minutes will appear here..." />
            <div className="card-actions">
              <button className="btn neon" onClick={generateMinutes} disabled={isProcessingMinutes}>
                {isProcessingMinutes ? <Spinner size={16} /> : "Generate Minutes"}
              </button>
              <button className="btn ghost" onClick={() => { setMinutes(""); setTasks([]); setMessage("Minutes cleared."); }}>Reset</button>
            </div>

            <div className="tasks">
              <h4>Tasks</h4>
              <ol>
                {tasks.length === 0 && <li className="muted">No tasks detected yet</li>}
                {tasks.map((t, i) => (
                  <li key={i}><span className="task-index">#{i+1}</span> {t.text}</li>
                ))}
              </ol>
            </div>
          </div>
        </section>

        <section className="card cyber-card export-row">
          <div className="export-left">
            <h3>Export</h3>
            <p className="muted">Download a formatted Word file with minutes and tasks.</p>
          </div>
          <div className="export-right">
            <button className="btn neon" onClick={exportDocx} disabled={isExporting}>
              {isExporting ? <Spinner /> : "Download DOCX"}
            </button>
            {docxUrl && <a className="download-link" href={docxUrl} target="_blank" rel="noreferrer">Open DOCX</a>}
          </div>
        </section>

        <footer className="footer cyber-footer">
          <div className="status">
            {message && <div className="msg">{message}</div>}
          </div>
          <div className="credits">Built with ❤️ by NAmeet</div>
        </footer>
      </main>
    </div>
  );
}
