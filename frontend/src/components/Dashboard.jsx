import React from 'react'

function classifyTone(label) {
  if (label === 'Fraud') return 'danger'
  if (label === 'Suspicious') return 'warning'
  return 'safe'
}

export default function Dashboard({ result, onTrain, training, refreshHistory }) {
  if (!result) {
    return (
      <div className="card result-card">
        <div className="card-title">Fraud Risk</div>
        <p>Submit a transaction to see the prediction, score, and risk factors.</p>
        <button
          className="secondary"
          onClick={async () => {
            await onTrain()
            await refreshHistory()
          }}
          disabled={training}
        >
          {training ? 'Training...' : 'Train Model'}
        </button>
      </div>
    )
  }

  const tone = classifyTone(result.classification)

  return (
    <div className={`card result-card ${tone}`}>
      <div className="card-title">Fraud Risk</div>
      <div className="score-row">
        <div className="score">{result.risk_score}</div>
        <div>
          <div className="classification">{result.classification}</div>
          <div className="probability">Fraud probability: {(result.fraud_probability * 100).toFixed(1)}%</div>
        </div>
      </div>
      <div className="risk-bar">
        <div className="risk-fill" style={{ width: `${result.risk_score}%` }} />
      </div>
      <div className="risk-factors">
        {result.risk_factors.map((factor) => (
          <span key={factor} className="pill">{factor}</span>
        ))}
      </div>
    </div>
  )
}
