import React, { useEffect, useState } from 'react'

const LineChart = ({ labels = [], values = [], color = '#f59e0b', height = 200 }) => {
  if (!labels.length || !values.length) return null
  const max = Math.max(...values)
  const min = Math.min(...values)
  const pad = (max - min) * 0.1 || 1
  const yMax = max + pad
  const yMin = Math.max(0, min - pad)
  const points = values.map((v, i) => {
    const x = (i / (values.length - 1)) * 100
    const y = 100 - ((v - yMin) / (yMax - yMin)) * 100
    return `${x},${y}`
  }).join(' ')

  return (
    <svg viewBox="0 0 100 100" preserveAspectRatio="none" style={{ width: '100%', height }}>
      <polyline
        fill="none"
        stroke={color}
        strokeWidth="1.5"
        points={points}
      />
    </svg>
  )
}

const FinanceChart = ({ userId }) => {
  const [timeseries, setTimeseries] = useState({ labels: [], values: [] })
  const [byCategory, setByCategory] = useState({ labels: [], series: [] })
  const [forecast, setForecast] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const loadTimeseries = async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await fetch(`/api/finance/timeseries?user_id=${encodeURIComponent(userId || '')}`)
      const data = await res.json()
      setTimeseries({ labels: data.labels || [], values: data.values || [] })
    } catch (e) {
      setError('Failed to load timeseries')
    } finally {
      setLoading(false)
    }
  }

  const loadForecast = async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await fetch(`/api/finance/forecast?user_id=${encodeURIComponent(userId || '')}&days_ahead=14`)
      const data = await res.json()
      setForecast(data)
    } catch (e) {
      setError('Failed to load forecast')
    } finally {
      setLoading(false)
    }
  }

  const loadTimeseriesByCategory = async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await fetch(`/api/finance/timeseries-by-category?user_id=${encodeURIComponent(userId || '')}`)
      const data = await res.json()
      setByCategory({ labels: data.labels || [], series: data.series || [] })
    } catch (e) {
      setError('Failed to load per-category timeseries')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadTimeseries()
  }, [])

  return (
    <div style={{ background: 'var(--bg-secondary)', border: '1px solid var(--border-color)', borderRadius: 12, padding: 16, margin: '12px 0' }}>
      <div style={{ display: 'flex', gap: 8, marginBottom: 12 }}>
        <button className="prompt-btn" onClick={loadTimeseries}>Spending Trend</button>
        <button className="prompt-btn" onClick={loadTimeseriesByCategory}>Per-Category Trend</button>
        <button className="prompt-btn" onClick={loadForecast}>Forecast (Prophet)</button>
      </div>
      {loading && <div style={{ color: 'var(--text-muted)' }}>Loading...</div>}
      {error && <div style={{ color: 'var(--text-danger)' }}>{error}</div>}
      {!loading && timeseries.labels.length > 0 && (
        <div>
          <div style={{ fontWeight: 600, marginBottom: 8 }}>Spending Trend</div>
          <LineChart labels={timeseries.labels} values={timeseries.values} />
        </div>
      )}
      {!loading && forecast && (
        <div style={{ marginTop: 16 }}>
          <div style={{ fontWeight: 600, marginBottom: 8 }}>Forecast</div>
          <LineChart labels={forecast.history?.labels || []} values={forecast.history?.values || []} color="#60a5fa" />
          <LineChart labels={forecast.forecast?.labels || []} values={forecast.forecast?.values || []} color="#ef4444" />
        </div>
      )}

      {!loading && byCategory.labels.length > 0 && (
        <div style={{ marginTop: 16 }}>
          <div style={{ fontWeight: 600, marginBottom: 8 }}>Per-Category Trend</div>
          {/* Legend */}
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginBottom: 8 }}>
            {byCategory.series.map((s, idx) => {
              const colors = ['#f59e0b', '#10b981', '#3b82f6', '#ef4444', '#a855f7', '#f97316']
              const color = colors[idx % colors.length]
              return (
                <div key={idx} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                  <span style={{ width: 12, height: 12, background: color, display: 'inline-block', borderRadius: 2 }}></span>
                  <span style={{ fontSize: 12 }}>{s.category}</span>
                </div>
              )
            })}
          </div>
          {byCategory.series.map((s, idx) => {
            const colors = ['#f59e0b', '#10b981', '#3b82f6', '#ef4444', '#a855f7', '#f97316']
            const color = colors[idx % colors.length]
            return (
              <LineChart key={idx} labels={byCategory.labels} values={s.values} color={color} />
            )
          })}
        </div>
      )}
    </div>
  )
}

export default FinanceChart


