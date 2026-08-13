import { useCallback, useRef, useState } from 'react'
import TopicForm from './components/TopicForm.jsx'
import PipelineTrace from './components/PipelineTrace.jsx'
import ProgressLog, { makeLogEntry } from './components/ProgressLog.jsx'
import ResultView from './components/ResultView.jsx'
import { generateJob, getJobResult, resumeJob, streamJob } from './api.js'

const RUNNING_STATUSES = new Set(['queued', 'running'])
