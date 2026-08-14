import ReactMarkdown from 'react-markdown'

export default function ResultView({ content, topic }) {
  if (!content) return null

  return (
    <div className="result card">
      <div className="result-header">
        <span className="result-eyebrow">Filed story</span>
        <span className="result-topic">{topic}</span>
      </div>
      <div className="result-body">
        <ReactMarkdown>{content}</ReactMarkdown>
      </div>
    </div>
  )
}
