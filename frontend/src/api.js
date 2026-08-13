// In dev, Vite proxies /api -> http://localhost:8000 (see vite.config.js).
// In production (Docker/Railway), set VITE_API_BASE_URL to the deployed
// backend URL and requests go straight there instead of through a proxy.
const BASE = import.meta.env.VITE_API_BASE_URL || '/api'

async function asJson(res) {
  if (!res.ok) {
    let detail = res.statusText
    try {
      const body = await res.json()
      detail = body.detail || detail
    } catch {
      /* response wasn't JSON, keep statusText */
    }
    throw new Error(detail)
  }
  return res.json()
}

export async function generateJob({ topic, mode, recency_days }) {
  const res = await fetch(`${BASE}/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ topic, mode: mode || undefined, recency_days: recency_days || undefined }),
  })
  return asJson(res)
}

export async function getJobStatus(jobId) {
  const res = await fetch(`${BASE}/jobs/${jobId}`)
  return asJson(res)
}

export async function getJobResult(jobId) {
  const res = await fetch(`${BASE}/jobs/${jobId}/result`)
  return asJson(res)
}

export async function resumeJob(jobId) {
  const res = await fetch(`${BASE}/jobs/${jobId}/resume`, { method: 'POST' })
  return asJson(res)
}

/**
 * Opens an SSE connection for a job and calls onEvent for every parsed
 * message. Returns a close() function. The backend sends heartbeat comment
 * lines (": heartbeat") which EventSource ignores automatically — no
 * special handling needed here.
 */
export function streamJob(jobId, onEvent, onError) {
  const source = new EventSource(`${BASE}/jobs/${jobId}/stream`)

  source.onmessage = (evt) => {
    try {
      const payload = JSON.parse(evt.data)
      onEvent(payload)
      if (payload.event === 'end') {
        source.close()
      }
    } catch (err) {
      console.error('Failed to parse SSE payload', err)
    }
  }

  source.onerror = (err) => {
    onError?.(err)
    // EventSource auto-retries on transient errors; if the job is already
    // done the backend has closed the stream cleanly via the 'end' event
    // above, so this mainly fires on real connection loss.
  }

  return () => source.close()
}
