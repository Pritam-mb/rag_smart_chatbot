import React, { useState } from 'react'
import axios from 'axios'

export default function ChatBox() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [coords, setCoords] = useState(null)

  const append = (from, text) => setMessages((m) => [...m, { from, text }])

  const useLocation = () => {
    if (!navigator.geolocation) return alert('Geolocation not supported')
    navigator.geolocation.getCurrentPosition(
      (p) => setCoords({ lat: p.coords.latitude, lon: p.coords.longitude }),
      (err) => alert('Unable to get location: ' + err.message)
    )
  }

  const send = async () => {
    if (!input.trim()) return
    const message = input.trim()
    append('user', message)
    setInput('')
    setLoading(true)

    try {
      const payload = { message }
      if (coords) {
        payload.lat = coords.lat
        payload.lon = coords.lon
      }

      const res = await axios.post('/api/chat', payload)
      if (res.data?.reply) {
        append('bot', res.data.reply)
      } else if (res.data?.error) {
        append('bot', 'Error: ' + res.data.error)
      } else {
        append('bot', 'No reply from server.')
      }
    } catch (err) {
      console.error(err)
      append('bot', 'Request failed: ' + (err.response?.data?.detail || err.message))
    } finally {
      setLoading(false)
    }
  }

  const onKey = (e) => { if (e.key === 'Enter') send() }

  return (
    <div className="chatbox">
      <div className="controls">
        <button onClick={useLocation} className="btn small">Use my location</button>
        <div className="location-label">{coords ? `Lat: ${coords.lat.toFixed(4)}, Lon: ${coords.lon.toFixed(4)}` : 'Location not set'}</div>
      </div>

      <div className="messages">
        {messages.map((m, i) => (
          <div key={i} className={`msg ${m.from}`}>
            <div className="msg-text" dangerouslySetInnerHTML={{ __html: m.text.replace(/\n/g, '<br/>') }} />
          </div>
        ))}
        {loading && <div className="msg bot">Thinking...</div>}
      </div>

      <div className="composer">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={onKey}
          placeholder="Ask a medical question (e.g. 'What are dengue symptoms?')"
        />
        <button onClick={send} className="btn">Send</button>
      </div>
    </div>
  )
}
import React, { useState } from 'react'

export default function ChatBox() {
  const [text, setText] = useState('')
  const [messages, setMessages] = useState([])

  async function send() {
    if (!text) return
    setMessages((m) => [...m, { from: 'user', text }])
    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: text })
      })
      const data = await res.json()
      setMessages((m) => [...m, { from: 'bot', text: data.answer || JSON.stringify(data) }])
    } catch (err) {
      setMessages((m) => [...m, { from: 'bot', text: 'Error contacting API' }])
    }
    setText('')
  }

  return (
    <div>
      <div style={{border:'1px solid #ddd',padding:10,height:300,overflow:'auto'}}>
        {messages.map((m,i) => (
          <div key={i} style={{margin:6}}><b>{m.from}:</b> {m.text}</div>
        ))}
      </div>
      <div style={{marginTop:8}}>
        <input value={text} onChange={(e)=>setText(e.target.value)} style={{width:'70%'}} />
        <button onClick={send} style={{marginLeft:8}}>Send</button>
      </div>
    </div>
  )
}
