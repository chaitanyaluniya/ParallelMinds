import axios from "axios";
import { useState } from "react";
import ChatWindow from "./components/ChatWindow";
import FileUpload from "./components/FileUpload";

export default function App() {
  const [query, setQuery] = useState("");
  const [files, setFiles] = useState([]);
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);

  async function handleSend() {
    const text = query.trim();
    if (!text && files.length === 0) return;

    const userText = text || `Uploaded ${files.length} file(s)`;
    setMessages((m) => [...m, { role: "user", text: userText }]);
    setLoading(true);

    const form = new FormData();
    form.append("query", text);
    files.forEach((f) => form.append("files", f));

    try {
      const { data } = await axios.post("/api/process", form);
      if (data.need_clr) {
        setMessages((m) => [...m, { role: "bot", text: data.question }]);
      } else {
        setMessages((m) => [
          ...m,
          {
            role: "bot",
            text: data.answer || "No response",
            plan: data.plan,
            extracted: data.extracted,
          },
        ]);
      }
    } catch (err) {
      const msg = err.response?.data?.detail || err.message || "Request failed";
      setMessages((m) => [...m, { role: "bot", text: String(msg) }]);
    } finally {
      setLoading(false);
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
          <ChatWindow messages={messages} loading={loading} />
        </main>
        <footer className="footer">
          <FileUpload
            query={query}
            setQuery={setQuery}
            files={files}
            setFiles={setFiles}
            onSend={handleSend}
            loading={loading}
          />
        </footer>
      </div>
    </div>
  );
}
