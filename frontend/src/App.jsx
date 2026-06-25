import { useEffect, useState } from "react";
import axios from "axios";
import ChatWindow from "./components/ChatWindow";
import FileUpload from "./components/FileUpload";

const API = (import.meta.env.VITE_API_URL || "").replace(/\/$/, "");

function sid() {
  let id = sessionStorage.getItem("pm_sid");
  if (!id) {
    id = crypto.randomUUID();
    sessionStorage.setItem("pm_sid", id);
  }
  return id;
}

function read_sse(res, on_ev) {
  const reader = res.body.getReader();
  const dec = new TextDecoder();
  let buf = "";

  return reader.read().then(function pump({ done, value }) {
    if (done) return;
    buf += dec.decode(value, { stream: true });
    const blocks = buf.split("\n\n");
    buf = blocks.pop() || "";
    for (const block of blocks) {
      if (!block.startsWith("data: ")) continue;
      on_ev(JSON.parse(block.slice(6)));
    }
    return reader.read().then(pump);
  });
}

export default function App() {
  const [query, setQuery] = useState("");
  const [files, setFiles] = useState([]);
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [live, setLive] = useState(null);
  const [cost, setCost] = useState(null);
  const [sessionId] = useState(sid);

  useEffect(() => {
    if (!query.trim() && files.length === 0) {
      setCost(null);
      return;
    }
    const t = setTimeout(async () => {
      const form = new FormData();
      form.append("query", query);
      form.append("session_id", sessionId);
      form.append(
        "files_meta",
        JSON.stringify(files.map((f) => ({ name: f.name, size: f.size, type: f.type }))),
      );
      try {
        const { data } = await axios.post(`${API}/api/estimate`, form);
        setCost(data);
      } catch {
        setCost(null);
      }
    }, 350);
    return () => clearTimeout(t);
  }, [query, files, sessionId]);

  async function handleSend() {
    const text = query.trim();
    if (!text && files.length === 0) return;

    const userText = text || `Uploaded ${files.length} file(s)`;
    setMessages((m) => [...m, { role: "user", text: userText }]);
    setLoading(true);
    setLive({ text: "", plan: [], extracted: [] });

    const form = new FormData();
    form.append("query", text);
    form.append("session_id", sessionId);
    files.forEach((f) => form.append("files", f));

    try {
      const res = await fetch(`${API}/api/stream`, { method: "POST", body: form });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || res.statusText);
      }

      let final = null;
      await read_sse(res, (ev) => {
        if (ev.type === "plan") {
          setLive((s) => ({ ...s, plan: ev.plan }));
        }
        if (ev.type === "token") {
          setLive((s) => ({ ...s, text: (s?.text || "") + ev.text }));
        }
        if (ev.type === "done") {
          final = ev;
          setLive((s) => ({
            ...s,
            text: ev.answer || s?.text || "",
            plan: ev.plan || s?.plan,
            extracted: ev.extracted || s?.extracted,
          }));
          if (ev.usage) {
            setCost({ ...ev.usage, estimate: false });
          }
        }
      });

      if (final?.need_clr) {
        setMessages((m) => [...m, { role: "bot", text: final.question, usage: final.usage }]);
      } else if (final) {
        setMessages((m) => [
          ...m,
          {
            role: "bot",
            text: final.answer || "No response",
            plan: final.plan,
            extracted: final.extracted,
            usage: final.usage,
          },
        ]);
      }
    } catch (err) {
      setMessages((m) => [...m, { role: "bot", text: String(err.message || "Request failed") }]);
    } finally {
      setLoading(false);
      setLive(null);
      setQuery("");
      setFiles([]);
    }
  }

  return (
    <div className="shell">
      <div className="app">
        <header className="header">
          <div>
            <h1>ParallelMinds</h1>
            <p>Multi-modal agent</p>
          </div>
          <span className="badge">Live</span>
        </header>
        <main className="main">
          <ChatWindow messages={messages} loading={loading} live={live} />
        </main>
        <footer className="footer">
          <FileUpload
            query={query}
            setQuery={setQuery}
            files={files}
            setFiles={setFiles}
            onSend={handleSend}
            loading={loading}
            cost={cost}
            maxMb={25}
          />
        </footer>
      </div>
    </div>
  );
}
