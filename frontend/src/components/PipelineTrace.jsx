import './PipelineTrace.css'

// Fixed stages shown on the trace. "worker" fans out to N parallel workers
// server-side, but we render it as a single station with a live counter
// (sections_done/sections_total) rather than trying to draw N dynamic nodes.
const STAGES = [
  { key: 'router', label: 'Router' },
  { key: 'research', label: 'Research' },
  { key: 'orchestrator', label: 'Plan' },
  { key: 'worker', label: 'Write' },
  { key: 'merge_content', label: 'Merge' },
  { key: 'editor', label: 'Edit' },
  { key: 'decide_images', label: 'Images' },
  { key: 'generate_and_place_images', label: 'Render' },
]

function stageState(stageKey, currentNode, visitedNodes, jobStatus) {
  if (jobStatus === 'failed' && stageKey === currentNode) return 'failed'
  if (visitedNodes.has(stageKey) && stageKey !== currentNode) return 'done'
  if (stageKey === currentNode) return 'active'
  return 'idle'
}

export default function PipelineTrace({ currentNode, visitedNodes, jobStatus, sectionsDone, sectionsTotal }) {
  return (
    <div className="trace" role="img" aria-label={`Pipeline stage: ${currentNode || 'idle'}`}>
      {STAGES.map((stage, i) => {
        const state = stageState(stage.key, currentNode, visitedNodes, jobStatus)
        const isLast = i === STAGES.length - 1
        return (
          <div className="trace-segment" key={stage.key}>
            <div className={`trace-node trace-node--${state}`}>
              <span className="trace-node-label">{stage.label}</span>
              {stage.key === 'worker' && sectionsTotal ? (
                <span className="trace-node-count">
                  {sectionsDone}/{sectionsTotal}
                </span>
              ) : null}
            </div>
            {!isLast && <div className={`trace-wire trace-wire--${state === 'idle' ? 'idle' : 'lit'}`} />}
          </div>
        )
      })}
    </div>
  )
}
