import PlanTrace from "./PlanTrace";

export default function ChatWindow({ messages, loading }) {
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
          <div className={`bubble ${msg.role}`}>{msg.text}</div>
          {msg.role === "bot" && <PlanTrace plan={msg.plan} extracted={msg.extracted} />}
        </div>
      ))}
      {loading && (
        <div className="msg-group bot">
          <div className="bubble bot loading">
            <span className="spinner" />
            Working...
          </div>
        </div>
      )}
    </div>
  );
}
