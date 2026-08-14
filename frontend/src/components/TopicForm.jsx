import { useState } from 'react'

export default function TopicForm({ onSubmit, disabled }) {
  const [topic, setTopic] = useState('')
  const [showAdvanced, setShowAdvanced] = useState(false)
  const [mode, setMode] = useState('')
  const [recencyDays, setRecencyDays] = useState('')

  function handleSubmit(e) {
    e.preventDefault()
    if (!topic.trim() || disabled) return
    onSubmit({
      topic: topic.trim(),
      mode: mode || undefined,
      recency_days: recencyDays ? Number(recencyDays) : undefined,
    })
  }

  return (
    <form className="topic-form" onSubmit={handleSubmit}>
      <label className="topic-label" htmlFor="topic">
        Assign a story
      </label>
      <div className="topic-row">
        <input
          id="topic"
          type="text"
          value={topic}
          onChange={(e) => setTopic(e.target.value)}
          placeholder="e.g. Rice blast disease resistance breeding in Assam"
          disabled={disabled}
          autoFocus
        />
        <button type="submit" disabled={disabled || !topic.trim()}>
          {disabled ? 'Running…' : 'Dispatch'}
        </button>
      </div>

      <button
        type="button"
        className="advanced-toggle"
        onClick={() => setShowAdvanced((v) => !v)}
      >
        {showAdvanced ? '− advanced' : '+ advanced'}
      </button>

      {showAdvanced && (
        <div className="advanced-row">
          <label>
            Mode
            <select value={mode} onChange={(e) => setMode(e.target.value)} disabled={disabled}>
              <option value="">Auto (router decides)</option>
              <option value="closed_book">Closed book</option>
              <option value="hybrid">Hybrid</option>
              <option value="open_book">Open book</option>
            </select>
          </label>
          <label>
            Recency (days)
            <input
              type="number"
              min="1"
              value={recencyDays}
              onChange={(e) => setRecencyDays(e.target.value)}
              disabled={disabled}
              placeholder="e.g. 30"
            />
          </label>
        </div>
      )}
    </form>
  )
}
