import PlanTrace from "./PlanTrace";

const HEADING = /^(ONE-LINE:|BULLETS:|PARAGRAPH:)/;

function BotText({ text }) {
  return text.split("\n").map((line, i) => (
    <span key={i}>
      {i > 0 && <br />}
      {HEADING.test(line) ? <strong className="answer-heading">{line}</strong> : line}
    </span>
  ));
}

export default function ChatWindow({ messages, loading, live }) {
  return (
    <div className="messages">
      {messages.length === 0 && !loading && (
        <div className="empty">
          <p>ParallelMinds Agent</p>
          <span>Upload a PDF, image, or audio file and ask anything.</span>
        </div>
      )}
      {messages.map((msg, i) => (
        <div key={i} className={`msg-group ${msg.role}`}>
          <div className={`bubble ${msg.role}`}>
            {msg.role === "bot" ? <BotText text={msg.text} /> : msg.text}
          </div>
          {msg.role === "bot" && <PlanTrace plan={msg.plan} extracted={msg.extracted} />}
        </div>
      ))}
      {loading && live && (
        <div className="msg-group bot">
          <div className="bubble bot">
            {live.text ? <BotText text={live.text} /> : <span className="muted">Thinking...</span>}
          </div>
          <PlanTrace plan={live.plan} extracted={live.extracted} live />
        </div>
      )}
    </div>
  );
}
