import { useCallback, useRef, useState } from 'react'
import TopicForm from './components/TopicForm.jsx'
import PipelineTrace from './components/PipelineTrace.jsx'
import ProgressLog, { makeLogEntry } from './components/ProgressLog.jsx'
import ResultView from './components/ResultView.jsx'
import { generateJob, getJobResult, resumeJob, streamJob } from './api.js'

const RUNNING_STATUSES = new Set(['queued', 'running'])


export default function App() {
  const [job, setJob] = useState(null) // { job_id, topic, status }
  const [currentNode, setCurrentNode] = useState(null)
  const [visitedNodes, setVisitedNodes] = useState(new Set())
  const [sectionsDone, setSectionsDone] = useState(0)
  const [sectionsTotal, setSectionsTotal] = useState(null)
  const [logEntries, setLogEntries] = useState([])
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)

  const closeStreamRef = useRef(null)

  const appendLog = useCallback((text, tone) => {
    setLogEntries((prev) => [...prev, makeLogEntry(text, tone)])
  }, [])

  function resetForNewJob() {
    setCurrentNode(null)
    setVisitedNodes(new Set())
    setSectionsDone(0)
    setSectionsTotal(null)
    setLogEntries([])
    setResult(null)
    setError(null)
  }

  function attachStream(jobId) {
    closeStreamRef.current?.()
    closeStreamRef.current = streamJob(
      jobId,
      (payload) => handleStreamEvent(jobId, payload),
      () => appendLog('connection interrupted — retrying…', 'alert')
    )
  }

  async function handleStreamEvent(jobId, payload) {
    if (payload.event === 'status') {
      setJob((prev) => (prev ? { ...prev, status: payload.status } : prev))
      if (payload.status === 'running') appendLog('pipeline started')
      if (payload.status === 'failed') {
        appendLog(payload.error || 'job failed', 'alert')
        setError(payload.error || 'The job failed.')
      }
    }

    if (payload.event === 'progress') {
      setCurrentNode(payload.node)
      setVisitedNodes((prev) => new Set(prev).add(payload.node))
      if (typeof payload.sections_done === 'number') setSectionsDone(payload.sections_done)
      if (payload.sections_total) setSectionsTotal(payload.sections_total)
      if (payload.detail) appendLog(payload.detail)
    }

    if (payload.event === 'end') {
      const latest = await getJobResult(jobId).catch(() => null)
      if (latest) {
        setResult(latest.content)
        appendLog('story filed', 'evidence')
      }
      setJob((prev) => (prev ? { ...prev, status: prev.status === 'failed' ? 'failed' : 'completed' } : prev))
    }
  }

  async function handleSubmit(payload) {
    resetForNewJob()
    try {
      const res = await generateJob(payload)
      setJob({ job_id: res.job_id, topic: payload.topic, status: res.status })
      appendLog(`dispatched — job ${res.job_id}`)
      attachStream(res.job_id)
    } catch (err) {
      setError(err.message)
      appendLog(`failed to dispatch: ${err.message}`, 'alert')
    }
  }