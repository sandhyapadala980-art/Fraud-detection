import React from 'react'

export default function HistoryTable({ records }) {
  return (
    <div className="card history-card">
      <div className="card-title">Transaction History</div>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Time</th>
              <th>User</th>
              <th>Amount</th>
              <th>Location</th>
              <th>Prediction</th>
              <th>Score</th>
            </tr>
          </thead>
          <tbody>
            {records.length === 0 ? (
              <tr>
                <td colSpan="6" className="empty">No transactions yet.</td>
              </tr>
            ) : (
              records.map((row) => (
                <tr key={row.id}>
                  <td>{new Date(row.created_at).toLocaleString()}</td>
                  <td>{row.user_id}</td>
                  <td>${Number(row.amount).toFixed(2)}</td>
                  <td>{row.location}</td>
                  <td>{row.classification}</td>
                  <td>{row.risk_score}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
