import React, { useEffect, useState } from 'react'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js'
import { Line } from 'react-chartjs-2'

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
)

const FinanceChart = ({ userId, startDate, endDate }) => {
  const [spendingChart, setSpendingChart] = useState(null)
  const [forecastChart, setForecastChart] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [activeChart, setActiveChart] = useState('spending')

  // Resolve theme-aware colors from CSS variables
  const getThemeColors = () => {
    const root = document.documentElement
    const styles = getComputedStyle(root)
    return {
      textPrimary: styles.getPropertyValue('--text-primary').trim() || '#ffffff',
      textSecondary: styles.getPropertyValue('--text-secondary').trim() || '#b3b3b3',
      borderColor: styles.getPropertyValue('--border-color').trim() || '#2a2a2a',
      // Tooltip uses a high-contrast dark background for both themes
      tooltipBg: 'rgba(0, 0, 0, 0.85)',
      tooltipBorder: styles.getPropertyValue('--border-color').trim() || '#2a2a2a',
    }
  }

  const loadSpendingChart = async () => {
    setLoading(true)
    setError(null)
    try {
      const params = new URLSearchParams()
      if (userId) params.append('user_id', userId)
      if (startDate) params.append('start_date', startDate)
      if (endDate) params.append('end_date', endDate)
      
      const res = await fetch(`/api/finance/chart/spending?${params.toString()}`)
      const data = await res.json()
      
      if (data.success) {
        setSpendingChart(data)
        setActiveChart('spending')
      } else {
        setError(data.error || 'Failed to load spending chart')
      }
    } catch (e) {
      setError('Failed to load spending chart')
    } finally {
      setLoading(false)
    }
  }

  const loadForecastChart = async () => {
    setLoading(true)
    setError(null)
    try {
      const params = new URLSearchParams()
      if (userId) params.append('user_id', userId)
      params.append('days_ahead', '7')
      
      const res = await fetch(`/api/finance/chart/forecast?${params.toString()}`)
      const data = await res.json()
      
      if (data.success) {
        setForecastChart(data)
        setActiveChart('forecast')
      } else {
        setError(data.error || 'Failed to load forecast chart')
      }
    } catch (e) {
      setError('Failed to load forecast chart')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadSpendingChart()
  }, [startDate, endDate])

  const renderChart = () => {
    if (activeChart === 'spending' && spendingChart) {
      const theme = getThemeColors()
      const sanitizeOptions = (opts) => {
        const safe = opts ? { ...opts } : {}
        safe.plugins = safe.plugins ? { ...safe.plugins } : {}
        safe.plugins.tooltip = safe.plugins.tooltip ? { ...safe.plugins.tooltip } : {}
        // Replace stringified callback with real function if needed
        const cb = safe.plugins.tooltip.callbacks
        if (!cb || typeof cb !== 'object') {
          safe.plugins.tooltip.callbacks = {}
        } else {
          safe.plugins.tooltip.callbacks = { ...cb }
        }
        safe.plugins.tooltip.callbacks.label = function (context) {
          const y = context?.parsed?.y ?? null
          return `Chi tiêu: ${y != null ? y.toLocaleString('vi-VN') : '0'} VND`
        }
        return safe
      }
      const normalizedOptions = sanitizeOptions(spendingChart.options)
      return (
        <div>
          <h3 style={{ marginBottom: '16px', color: 'var(--text-primary)' }}>{spendingChart.title}</h3>
          <Line 
            data={spendingChart.data} 
            options={{
              ...normalizedOptions,
              plugins: {
                ...normalizedOptions.plugins,
                tooltip: {
                  ...normalizedOptions.plugins.tooltip,
                  backgroundColor: theme.tooltipBg,
                  titleColor: '#ffffff',
                  bodyColor: '#ffffff',
                  borderColor: theme.tooltipBorder,
                  borderWidth: 1
                },
                legend: {
                  ...(normalizedOptions.plugins?.legend || {}),
                  labels: {
                    ...((normalizedOptions.plugins?.legend && normalizedOptions.plugins.legend.labels) || {}),
                    color: theme.textSecondary
                  }
                }
              },
              scales: {
                ...normalizedOptions.scales,
                x: {
                  ...(normalizedOptions.scales?.x || {}),
                  grid: {
                    color: theme.borderColor
                  },
                  ticks: {
                    color: theme.textSecondary
                  }
                },
                y: {
                  ...(normalizedOptions.scales?.y || {}),
                  grid: {
                    color: theme.borderColor
                  },
                  ticks: {
                    color: theme.textSecondary
                  }
                }
              }
            }}
          />
        </div>
      )
    }
    
    if (activeChart === 'forecast' && forecastChart) {
      const theme = getThemeColors()
      const sanitizeOptions = (opts) => {
        const safe = opts ? { ...opts } : {}
        safe.plugins = safe.plugins ? { ...safe.plugins } : {}
        safe.plugins.tooltip = safe.plugins.tooltip ? { ...safe.plugins.tooltip } : {}
        const cb = safe.plugins.tooltip.callbacks
        if (!cb || typeof cb !== 'object') {
          safe.plugins.tooltip.callbacks = {}
        } else {
          safe.plugins.tooltip.callbacks = { ...cb }
        }
        safe.plugins.tooltip.callbacks.label = function (context) {
          const y = context?.parsed?.y
          const label = context?.dataset?.label || ''
          return `${label}: ${y != null ? y.toLocaleString('vi-VN') + ' VND' : 'N/A'}`
        }
        return safe
      }
      const normalizedOptions = sanitizeOptions(forecastChart.options)
      return (
        <div>
          <h3 style={{ marginBottom: '16px', color: 'var(--text-primary)' }}>{forecastChart.title}</h3>
          <Line 
            data={forecastChart.data} 
            options={{
              ...normalizedOptions,
              plugins: {
                ...normalizedOptions.plugins,
                tooltip: {
                  ...normalizedOptions.plugins.tooltip,
                  backgroundColor: theme.tooltipBg,
                  titleColor: '#ffffff',
                  bodyColor: '#ffffff',
                  borderColor: theme.tooltipBorder,
                  borderWidth: 1
                },
                legend: {
                  ...(normalizedOptions.plugins?.legend || {}),
                  labels: {
                    ...((normalizedOptions.plugins?.legend && normalizedOptions.plugins.legend.labels) || {}),
                    color: theme.textSecondary
                  }
                }
              },
              scales: {
                ...normalizedOptions.scales,
                x: {
                  ...(normalizedOptions.scales?.x || {}),
                  grid: {
                    color: theme.borderColor
                  },
                  ticks: {
                    color: theme.textSecondary
                  }
                },
                y: {
                  ...(normalizedOptions.scales?.y || {}),
                  grid: {
                    color: theme.borderColor
                  },
                  ticks: {
                    color: theme.textSecondary
                  }
                }
              }
            }}
          />
        </div>
      )
    }
    
    return null
  }

  return (
    <div style={{ 
      background: 'var(--bg-secondary)', 
      border: '1px solid var(--border-color)', 
      borderRadius: 12, 
      padding: 20, 
      margin: '12px 0' 
    }}>
      <div style={{ display: 'flex', gap: 8, marginBottom: 20 }}>
        <button 
          className={`prompt-btn ${activeChart === 'spending' ? 'active' : ''}`}
          onClick={loadSpendingChart}
          style={{
            background: activeChart === 'spending' ? 'var(--accent-color)' : 'var(--bg-primary)',
            color: activeChart === 'spending' ? 'white' : 'var(--text-primary)'
          }}
        >
          📊 Biểu đồ chi tiêu
        </button>
        <button 
          className={`prompt-btn ${activeChart === 'forecast' ? 'active' : ''}`}
          onClick={loadForecastChart}
          style={{
            background: activeChart === 'forecast' ? 'var(--accent-color)' : 'var(--bg-primary)',
            color: activeChart === 'forecast' ? 'white' : 'var(--text-primary)'
          }}
        >
          🔮 Dự báo 7 ngày tới
        </button>
      </div>
      
      {loading && (
        <div style={{ 
          color: 'var(--text-muted)', 
          textAlign: 'center', 
          padding: '40px 0',
          fontSize: '16px'
        }}>
          Đang tải biểu đồ...
        </div>
      )}
      
      {error && (
        <div style={{ 
          color: 'var(--text-danger)', 
          textAlign: 'center', 
          padding: '20px 0',
          background: 'rgba(239, 68, 68, 0.1)',
          borderRadius: 8,
          border: '1px solid rgba(239, 68, 68, 0.3)'
        }}>
          {error}
        </div>
      )}
      
      {!loading && !error && renderChart()}
    </div>
  )
}

export default FinanceChart


