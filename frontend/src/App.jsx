import React from 'react'
import { fetchTransactions, predictTransaction, trainModel } from './services/api'
import TransactionForm from './components/TransactionForm'
import Dashboard from './components/Dashboard'
import HistoryTable from './components/HistoryTable'

export default function App() {
  const [result, setResult] = React.useState(null)
  const [records, setRecords] = React.useState([])
  const [loading, setLoading] = React.useState(false)
  const [training, setTraining] = React.useState(false)
  const [error, setError] = React.useState('')

  const loadHistory = React.useCallback(async () => {
    try {
      const response = await fetchTransactions()
      setRecords(response.data)
    } catch (err) {
      console.error(err)
    }
  }, [])

  React.useEffect(() => {
    loadHistory()
    const timer = setInterval(loadHistory, 10000)
    return () => clearInterval(timer)
  }, [loadHistory])

  const handlePredict = async (payload) => {
    setLoading(true)
    setError('')
    try {
      const response = await predictTransaction(payload)
      setResult(response.data)
      await loadHistory()
    } catch (err) {
      setError(err.response?.data?.detail || 'Prediction failed')
    } finally {
      setLoading(false)
    }
  }

  const handleTrain = async () => {
    setTraining(true)
    setError('')
    try {
      await trainModel()
    } catch (err) {
      setError(err.response?.data?.detail || 'Training failed')
    } finally {
      setTraining(false)
    }
  }

  return (
    <div className="app-shell">
      <header className="hero">
        <div>
          <p className="eyebrow">Real-time fraud detection</p>
          <h1>Fraud Detection Dashboard</h1>
          <p className="subtitle">
            FastAPI + React + scikit-learn pipeline for transaction scoring, storage, and live risk tracking.
          </p>
        </div>
        <button className="secondary" onClick={handleTrain} disabled={training}>
          {training ? 'Training...' : 'Retrain Model'}
        </button>
      </header>

      {error ? <div className="error-banner">{error}</div> : null}

      <div className="grid-layout">
        <TransactionForm onSubmit={handlePredict} loading={loading} />
        <Dashboard result={result} onTrain={handleTrain} training={training} refreshHistory={loadHistory} />
      </div>

      <HistoryTable records={records} />
    </div>
  )
}
