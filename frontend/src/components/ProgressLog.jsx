import { useEffect, useRef } from 'react'

function timestamp() {
  return new Date().toLocaleTimeString('en-GB', { hour12: false })
}

export default function ProgressLog({ entries }) {
  const scrollRef = useRef(null)

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [entries])

  return (
    <div className="log card">
      <div className="log-header">WIRE</div>
      <div className="log-body" ref={scrollRef}>
        {entries.length === 0 && <div className="log-line log-line--dim">standing by…</div>}
        {entries.map((entry, i) => (
          <div key={i} className={`log-line ${entry.tone ? `log-line--${entry.tone}` : ''}`}>
            <span className="log-time">{entry.time}</span>
            <span className="log-text">{entry.text}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

export function makeLogEntry(text, tone) {
  return { time: timestamp(), text, tone }
}
