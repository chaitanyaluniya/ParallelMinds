const ACCEPT = "image/jpeg,image/png,application/pdf,audio/mpeg,audio/wav,audio/mp4,audio/x-m4a";

function icon(name) {
  const ext = name.split(".").pop()?.toLowerCase();
  if (["jpg", "jpeg", "png"].includes(ext)) return "IMG";
  if (ext === "pdf") return "PDF";
  if (["mp3", "wav", "m4a"].includes(ext)) return "AUD";
  return "FILE";
}

export default function FileUpload({ query, setQuery, files, setFiles, onSend, loading }) {
  function onPick(e) {
    setFiles([...files, ...Array.from(e.target.files)]);
    e.target.value = "";
  }

  function remove(i) {
    setFiles(files.filter((_, idx) => idx !== i));
  }

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        onSend();
      }}
      className="composer"
    >
      {files.length > 0 && (
        <ul className="file-list">
          {files.map((f, i) => (
            <li key={`${f.name}-${i}`}>
              <span className="file-tag">{icon(f.name)}</span>
              <span className="file-name">{f.name}</span>
              <button type="button" className="file-remove" onClick={() => remove(i)} disabled={loading}>
                ×
              </button>
            </li>
          ))}
        </ul>
      )}
      <div className="composer-row">
        <label className="attach-btn">
          +
          <input type="file" multiple accept={ACCEPT} onChange={onPick} disabled={loading} hidden />
        </label>
        <textarea
          rows={1}
          placeholder="Message ParallelMinds..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          disabled={loading}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              onSend();
            }
          }}
        />
        <button type="submit" className="send-btn" disabled={loading || (!query.trim() && files.length === 0)}>
          ↑
        </button>
      </div>
    </form>
  );
}
