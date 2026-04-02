import React from 'react'

const initialState = {
  user_id: 1,
  amount: 120,
  location: 'New York',
  device_id: 'device_1',
  payment_method: 'card',
  failed_login_attempts: 0
}

export default function TransactionForm({ onSubmit, loading }) {
  const [form, setForm] = React.useState(initialState)

  const updateField = (key, value) => {
    setForm((current) => ({ ...current, [key]: value }))
  }

  const submit = (event) => {
    event.preventDefault()
    onSubmit({
      ...form,
      user_id: Number(form.user_id),
      amount: Number(form.amount),
      failed_login_attempts: Number(form.failed_login_attempts)
    })
  }

  return (
    <form className="card form-card" onSubmit={submit}>
      <div className="card-title">Transaction Input</div>
      <div className="grid">
        <label>
          User ID
          <input type="number" min="1" value={form.user_id} onChange={(e) => updateField('user_id', e.target.value)} />
        </label>
        <label>
          Amount
          <input type="number" min="1" step="0.01" value={form.amount} onChange={(e) => updateField('amount', e.target.value)} />
        </label>
        <label>
          Location
          <input type="text" value={form.location} onChange={(e) => updateField('location', e.target.value)} />
        </label>
        <label>
          Device ID
          <input type="text" value={form.device_id} onChange={(e) => updateField('device_id', e.target.value)} />
        </label>
        <label>
          Payment Method
          <select value={form.payment_method} onChange={(e) => updateField('payment_method', e.target.value)}>
            <option value="card">card</option>
            <option value="upi">upi</option>
            <option value="paypal">paypal</option>
            <option value="crypto">crypto</option>
            <option value="wire_transfer">wire_transfer</option>
          </select>
        </label>
        <label>
          Failed Login Attempts
          <input type="number" min="0" max="20" value={form.failed_login_attempts} onChange={(e) => updateField('failed_login_attempts', e.target.value)} />
        </label>
      </div>
      <button type="submit" disabled={loading}>
        {loading ? 'Analyzing...' : 'Run Fraud Check'}
      </button>
    </form>
  )
}
