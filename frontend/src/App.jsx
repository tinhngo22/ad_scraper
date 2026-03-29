import { useState, useEffect } from 'react'
import './App.css'

const API = ''

async function apiFetch(path, options = {}) {
  const res = await fetch(API + path, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || 'Request failed')
  return data
}

function StepCard({ number, title, children }) {
  return (
    <div className="step-card">
      <div className="step-header">
        <span className="step-number">{number}</span>
        <h2 className="step-title">{title}</h2>
      </div>
      <div className="step-body">{children}</div>
    </div>
  )
}

function StatusBadge({ status }) {
  const colors = { idle: '#64748b', loading: '#f59e0b', success: '#22c55e', error: '#ef4444' }
  return (
    <span style={{ color: colors[status] || colors.idle, fontWeight: 600, fontSize: '0.85rem' }}>
      {status === 'loading' ? '⏳ Running…' : status === 'success' ? '✓ Done' : status === 'error' ? '✗ Error' : '—'}
    </span>
  )
}

let nextId = 3

export default function App() {
  const [url, setUrl] = useState('')
  const [targets, setTargets] = useState([])
  const [results, setResults] = useState([])
  const [extracted, setExtracted] = useState([])
  const [fields, setFields] = useState([
    { id: 1, name: '', description: '' },
    { id: 2, name: '', description: '' },
  ])

  const [s1, setS1] = useState({ status: 'idle', msg: '' })
  const [s2, setS2] = useState({ status: 'idle', msg: '' })
  const [s3, setS3] = useState({ status: 'idle', msg: '' })

  function updateField(id, key, value) {
    setFields(prev => prev.map(f => f.id === id ? { ...f, [key]: value } : f))
  }

  function addField() {
    setFields(prev => [...prev, { id: nextId++, name: '', description: '' }])
  }

  function removeField(id) {
    setFields(prev => prev.filter(f => f.id !== id))
  }

  useEffect(() => {
    apiFetch('/api/targets').then(d => setTargets(d.targets || [])).catch(() => {})
    apiFetch('/api/results').then(d => setResults(d.results || [])).catch(() => {})
    apiFetch('/api/extracted').then(d => setExtracted(d.results || [])).catch(() => {})
  }, [])

  async function handleScrapeCategory() {
    if (!url.trim()) return
    setS1({ status: 'loading', msg: '' })
    try {
      const d = await apiFetch('/api/scrape-category', {
        method: 'POST',
        body: JSON.stringify({ url: url.trim() }),
      })
      const t = await apiFetch('/api/targets')
      setTargets(t.targets || [])
      setS1({ status: 'success', msg: `Found ${d.targets_count} target pages` })
    } catch (e) {
      setS1({ status: 'error', msg: e.message })
    }
  }

  async function handleScrapePages() {
    setS2({ status: 'loading', msg: '' })
    try {
      const d = await apiFetch('/api/scrape-pages', { method: 'POST' })
      const r = await apiFetch('/api/results')
      setResults(r.results || [])
      setS2({ status: 'success', msg: `Scraped ${d.count} pages` })
    } catch (e) {
      setS2({ status: 'error', msg: e.message })
    }
  }

  async function handleExtract() {
    const validFields = fields.filter(f => f.name.trim() && f.description.trim())
    if (validFields.length === 0) {
      setS3({ status: 'error', msg: 'Add at least one field with a name and description.' })
      return
    }
    setS3({ status: 'loading', msg: '' })
    try {
      const d = await apiFetch('/api/extract', {
        method: 'POST',
        body: JSON.stringify({ fields: validFields.map(f => ({ name: f.name.trim(), description: f.description.trim() })) }),
      })
      setExtracted(d.results || [])
      setS3({ status: 'success', msg: `Extracted ${d.count} entries` })
    } catch (e) {
      setS3({ status: 'error', msg: e.message })
    }
  }

  return (
    <div>
      <header className="app-header">
        <h1>Ad Scraper</h1>
        <p>Wikipedia attraction data pipeline</p>
      </header>

      <StepCard number="1" title="Scrape Category Page">
        <p className="step-desc">Enter a Wikipedia category URL to collect target page links.</p>
        <div className="input-row">
          <input
            className="url-input"
            type="text"
            placeholder="https://en.wikipedia.org/wiki/Category:..."
            value={url}
            onChange={e => setUrl(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleScrapeCategory()}
          />
          <button className="btn btn-primary" onClick={handleScrapeCategory} disabled={s1.status === 'loading'}>
            Scrape
          </button>
        </div>
        <div className="status-row">
          <StatusBadge status={s1.status} />
          {s1.msg && <span className="status-msg">{s1.msg}</span>}
        </div>
        {targets.length > 0 && (
          <details className="collapsible">
            <summary>{targets.length} targets collected</summary>
            <ul className="target-list">
              {targets.map(t => <li key={t}><code>{t}</code></li>)}
            </ul>
          </details>
        )}
      </StepCard>

      <StepCard number="2" title="Scrape Individual Pages">
        <p className="step-desc">Fetch each target page and extract infobox data. Requires step 1 first.</p>
        <div className="action-row">
          <button
            className="btn btn-primary"
            onClick={handleScrapePages}
            disabled={s2.status === 'loading' || targets.length === 0}
          >
            Scrape {targets.length > 0 ? `${targets.length} pages` : 'Pages'}
          </button>
          <StatusBadge status={s2.status} />
          {s2.msg && <span className="status-msg">{s2.msg}</span>}
        </div>
        {results.length > 0 && (
          <details className="collapsible">
            <summary>{results.length} raw entries in data/raw.json</summary>
            <div className="raw-list">
              {results.map((r, i) => (
                <div key={i} className="raw-entry">
                  <strong>{r.name}</strong>
                  <p className="raw-text">{r.infobox_text?.slice(0, 120)}…</p>
                </div>
              ))}
            </div>
          </details>
        )}
      </StepCard>

      <StepCard number="3" title="Extract with AI">
        <p className="step-desc">Define the fields you want Gemini to extract from each page's infobox.</p>

        <div className="fields-header">
          <span className="fields-label">Field name</span>
          <span className="fields-label">Description</span>
        </div>

        {fields.map((f, i) => (
          <div key={f.id} className="field-row">
            <input
              className="url-input"
              type="text"
              placeholder={`e.g. open_year`}
              value={f.name}
              onChange={e => updateField(f.id, 'name', e.target.value)}
            />
            <input
              className="url-input"
              type="text"
              placeholder={`e.g. The year the attraction opened`}
              value={f.description}
              onChange={e => updateField(f.id, 'description', e.target.value)}
            />
            {fields.length > 1 && (
              <button className="btn-remove" onClick={() => removeField(f.id)} title="Remove field">×</button>
            )}
          </div>
        ))}

        <button className="btn-add-field" onClick={addField}>+ Add field</button>

        <div className="action-row">
          <button
            className="btn btn-accent"
            onClick={handleExtract}
            disabled={s3.status === 'loading' || results.length === 0}
          >
            Extract Data
          </button>
          <StatusBadge status={s3.status} />
          {s3.msg && <span className="status-msg">{s3.msg}</span>}
        </div>
      </StepCard>

      {extracted.length > 0 && (() => {
        const columns = Object.keys(extracted[0])
        return (
          <section className="results-section">
            <h2 className="results-title">Results ({extracted.length})</h2>
            <div className="table-wrapper">
              <table className="results-table">
                <thead>
                  <tr>{columns.map(col => <th key={col}>{col}</th>)}</tr>
                </thead>
                <tbody>
                  {extracted.map((row, i) => (
                    <tr key={i}>
                      {columns.map(col => <td key={col}>{row[col]}</td>)}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        )
      })()}
    </div>
  )
}
