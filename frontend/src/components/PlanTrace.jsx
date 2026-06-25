import { useState } from "react";

function Extracted({ items }) {
  const [open, setOpen] = useState(false);
  if (!items?.length) return null;

  return (
    <div className="sub-panel">
      <button type="button" className="panel-toggle" onClick={() => setOpen(!open)}>
        <span className="panel-label">Extracted text</span>
        <span className="panel-icon">{open ? "−" : "+"}</span>
      </button>
      {open && (
        <div className="extracted-list">
          {items.map((item, i) => (
            <div key={i} className="extracted-item">
              <div className="extracted-head">
                <span className="file-tag">{item.type?.toUpperCase()}</span>
                <span>{item.name || item.type}</span>
              </div>
              <pre>{item.text || "(empty)"}</pre>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default function PlanTrace({ plan, extracted, live, usage }) {
  const [open, setOpen] = useState(true);
  if (!plan?.length && !extracted?.length) return null;

  return (
    <div className="meta-panel">
      {plan?.length > 0 && (
        <div className="sub-panel">
          <button type="button" className="panel-toggle" onClick={() => setOpen(!open)}>
            <span className="panel-label">{live ? "Tools running" : "Plan trace"}</span>
            <span className="panel-icon">{open ? "−" : "+"}</span>
          </button>
          {open && (
            <ol className={`plan-list ${live ? "plan-live" : ""}`}>
              {plan.map((step, i) => (
                <li key={step.step} className={step.status === "running" ? "active" : ""}>
                  <span className="step-num">{step.step}</span>
                  <span className="step-tool">{step.tool}</span>
                  <span className={`step-status ${step.status}`}>{step.status}</span>
                  {i < plan.length - 1 && <span className="step-line" />}
                </li>
              ))}
            </ol>
          )}
        </div>
      )}
      {!live && <Extracted items={extracted} />}
      {usage && !live && (
        <div className="usage-tag">
          {usage.tokens_in} in · {usage.tokens_out} out · {usage.cost_label}
        </div>
      )}
    </div>
  );
}
