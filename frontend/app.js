const e = React.createElement;
const { useEffect, useMemo, useState } = React;

const api = axios.create({
  baseURL: 'http://127.0.0.1:8001',
  headers: { 'Content-Type': 'application/json' }
});

const initialForm = {
  user_id: 1,
  amount: 120,
  location: 'New York',
  device_id: 'device_1',
  payment_method: 'card',
  failed_login_attempts: 0
};

function classifyTone(label) {
  if (label === 'Fraud') return 'danger';
  if (label === 'Suspicious') return 'warning';
  return 'safe';
}

function TransactionForm({ onSubmit, loading }) {
  const [form, setForm] = useState(initialForm);

  const setField = (key, value) => setForm((current) => ({ ...current, [key]: value }));

  const submit = (event) => {
    event.preventDefault();
    onSubmit({
      ...form,
      user_id: Number(form.user_id),
      amount: Number(form.amount),
      failed_login_attempts: Number(form.failed_login_attempts)
    });
  };

  return e(
    'form',
    { className: 'card form-card', onSubmit: submit },
    e('div', { className: 'card-title' }, 'Transaction Input'),
    e(
      'div',
      { className: 'grid' },
      e(
        'label',
        null,
        'User ID',
        e('input', { type: 'number', min: '1', value: form.user_id, onChange: (event) => setField('user_id', event.target.value) })
      ),
      e(
        'label',
        null,
        'Amount',
        e('input', { type: 'number', min: '1', step: '0.01', value: form.amount, onChange: (event) => setField('amount', event.target.value) })
      ),
      e(
        'label',
        null,
        'Location',
        e('input', { type: 'text', value: form.location, onChange: (event) => setField('location', event.target.value) })
      ),
      e(
        'label',
        null,
        'Device ID',
        e('input', { type: 'text', value: form.device_id, onChange: (event) => setField('device_id', event.target.value) })
      ),
      e(
        'label',
        null,
        'Payment Method',
        e(
          'select',
          { value: form.payment_method, onChange: (event) => setField('payment_method', event.target.value) },
          e('option', { value: 'card' }, 'card'),
          e('option', { value: 'upi' }, 'upi'),
          e('option', { value: 'paypal' }, 'paypal'),
          e('option', { value: 'crypto' }, 'crypto'),
          e('option', { value: 'wire_transfer' }, 'wire_transfer')
        )
      ),
      e(
        'label',
        null,
        'Failed Login Attempts',
        e('input', { type: 'number', min: '0', max: '20', value: form.failed_login_attempts, onChange: (event) => setField('failed_login_attempts', event.target.value) })
      )
    ),
    e('button', { type: 'submit', disabled: loading }, loading ? 'Analyzing...' : 'Run Fraud Check')
  );
}

function Dashboard({ result, onTrain, training, refreshHistory }) {
  if (!result) {
    return e(
      'div',
      { className: 'card result-card' },
      e('div', { className: 'card-title' }, 'Fraud Risk'),
      e('p', null, 'Submit a transaction to see the prediction, score, and risk factors.'),
      e(
        'button',
        {
          className: 'secondary',
          onClick: async () => {
            await onTrain();
            await refreshHistory();
          },
          disabled: training
        },
        training ? 'Training...' : 'Train Model'
      )
    );
  }

  const tone = classifyTone(result.classification);

  return e(
    'div',
    { className: `card result-card ${tone}` },
    e('div', { className: 'card-title' }, 'Fraud Risk'),
    e(
      'div',
      { className: 'score-row' },
      e('div', { className: 'score' }, result.risk_score),
      e(
        'div',
        null,
        e('div', { className: 'classification' }, result.classification),
        e('div', { className: 'probability' }, `Fraud probability: ${(result.fraud_probability * 100).toFixed(1)}%`)
      )
    ),
    e('div', { className: 'risk-bar' }, e('div', { className: 'risk-fill', style: { width: `${result.risk_score}%` } })),
    e(
      'div',
      { className: 'risk-factors' },
      result.risk_factors.map((factor) => e('span', { key: factor, className: 'pill' }, factor))
    )
  );
}

function HistoryTable({ records }) {
  return e(
    'div',
    { className: 'card history-card' },
    e('div', { className: 'card-title' }, 'Transaction History'),
    e(
      'div',
      { className: 'table-wrap' },
      e(
        'table',
        null,
        e(
          'thead',
          null,
          e(
            'tr',
            null,
            e('th', null, 'Time'),
            e('th', null, 'User'),
            e('th', null, 'Amount'),
            e('th', null, 'Location'),
            e('th', null, 'Prediction'),
            e('th', null, 'Score')
          )
        ),
        e(
          'tbody',
          null,
          records.length === 0
            ? e('tr', null, e('td', { colSpan: '6', className: 'empty' }, 'No transactions yet.'))
            : records.map((row) =>
                e(
                  'tr',
                  { key: row.id },
                  e('td', null, new Date(row.created_at).toLocaleString()),
                  e('td', null, row.user_id),
                  e('td', null, `$${Number(row.amount).toFixed(2)}`),
                  e('td', null, row.location),
                  e('td', null, row.classification),
                  e('td', null, row.risk_score)
                )
              )
        )
      )
    )
  );
}

function App() {
  const [result, setResult] = useState(null);
  const [records, setRecords] = useState([]);
  const [loading, setLoading] = useState(false);
  const [training, setTraining] = useState(false);
  const [error, setError] = useState('');

  const loadHistory = async () => {
    try {
      const response = await api.get('/transactions');
      setRecords(response.data);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    loadHistory();
    const timer = setInterval(loadHistory, 10000);
    return () => clearInterval(timer);
  }, []);

  const handlePredict = async (payload) => {
    setLoading(true);
    setError('');
    try {
      const response = await api.post('/predict', payload);
      setResult(response.data);
      await loadHistory();
    } catch (err) {
      setError(err?.response?.data?.detail || 'Prediction failed');
    } finally {
      setLoading(false);
    }
  };

  const handleTrain = async () => {
    setTraining(true);
    setError('');
    try {
      await api.post('/train', {});
    } catch (err) {
      setError(err?.response?.data?.detail || 'Training failed');
    } finally {
      setTraining(false);
    }
  };

  return e(
    'div',
    { className: 'app-shell' },
    e(
      'header',
      { className: 'hero' },
      e(
        'div',
        null,
        e('p', { className: 'eyebrow' }, 'Real-time fraud detection'),
        e('h1', null, 'Fraud Detection Dashboard'),
        e('p', { className: 'subtitle' }, 'FastAPI + React + scikit-learn pipeline for transaction scoring, storage, and live risk tracking.')
      ),
      e('button', { className: 'secondary', onClick: handleTrain, disabled: training }, training ? 'Training...' : 'Retrain Model')
    ),
    error ? e('div', { className: 'error-banner' }, error) : null,
    e(
      'div',
      { className: 'grid-layout' },
      e(TransactionForm, { onSubmit: handlePredict, loading }),
      e(Dashboard, { result, onTrain: handleTrain, training, refreshHistory: loadHistory })
    ),
    e(HistoryTable, { records })
  );
}

ReactDOM.createRoot(document.getElementById('root')).render(
  e(React.StrictMode, null, e(App))
);
