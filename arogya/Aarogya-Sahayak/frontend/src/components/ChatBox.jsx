import React, { useState } from 'react'
import axios from 'axios'

export default function ChatBox() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [coords, setCoords] = useState(null)
  const [file, setFile] = useState(null)
  const [uploading, setUploading] = useState(false)

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

  // PDF upload handlers
  const onFileChange = (e) => {
    const f = e.target.files?.[0]
    setFile(f || null)
  }

  const uploadReport = async () => {
    if (!file) return alert('Please select a PDF file first')
    if (!file.name.toLowerCase().endsWith('.pdf')) return alert('Only PDF files allowed')

    setUploading(true)
    append('user', `Uploaded file: ${file.name}`)

    try {
      const form = new FormData()
      form.append('file', file)

      const res = await axios.post('/api/upload-report', form, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })

      if (res.data?.status) {
        // backend may return preview or status message
        const preview = res.data.preview ? '\n\n' + res.data.preview : ''
        append('bot', res.data.status + preview)
      } else if (res.data?.error) {
        append('bot', 'Upload error: ' + res.data.error)
      } else {
        append('bot', 'PDF uploaded.')
      }

      setFile(null)
      const fileInput = document.getElementById('pdf-upload-input')
      if (fileInput) fileInput.value = ''

    } catch (err) {
      console.error(err)
      append('bot', 'Upload failed: ' + (err.response?.data?.detail || err.message))
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="chatbox">
      <div className="controls">
        <button onClick={useLocation} className="btn small">Use my location</button>
        <div className="location-label">{coords ? `Lat: ${coords.lat.toFixed(4)}, Lon: ${coords.lon.toFixed(4)}` : 'Location not set'}</div>
      </div>

      {/* upload controls moved into composer for compact UI */}

      <div className="messages">
        {messages.map((m, i) => (
          <div key={i} className={`msg ${m.from}`}>
            <div className="msg-text" dangerouslySetInnerHTML={{ __html: m.text.replace(/\n/g, '<br/>') }} />
          </div>
        ))}
        {loading && <div className="msg bot">Thinking...</div>}
      </div>

      <div className="composer">
        <label className="file-label">
          <input id="pdf-upload-input" type="file" accept="application/pdf" onChange={onFileChange} />
          <span className="upload-icon">📎</span>
        </label>

        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={onKey}
          placeholder="Ask a medical question (e.g. 'What are dengue symptoms?')"
        />

        <button className="btn upload-btn" onClick={uploadReport} disabled={uploading}>{uploading ? 'Uploading...' : 'Upload PDF'}</button>
        <button onClick={send} className="btn send-btn" disabled={loading}>{loading ? 'Sending...' : 'Send'}</button>
        <div className="composer-filename">{file ? file.name : ''}</div>
      </div>
    </div>
  )
}
// import React, { useState } from 'react'
// import axios from 'axios'

// export default function ChatBox() {
//   const [messages, setMessages] = useState([])
//   const [input, setInput] = useState('')
//   const [loading, setLoading] = useState(false)
//   const [coords, setCoords] = useState(null)

//   const append = (from, text) => setMessages((m) => [...m, { from, text }])

//   const useLocation = () => {
//     if (!navigator.geolocation) return alert('Geolocation not supported')
//     navigator.geolocation.getCurrentPosition(
//       (p) => setCoords({ lat: p.coords.latitude, lon: p.coords.longitude }),
//       (err) => alert('Unable to get location: ' + err.message)
//     )
//   }

//   const send = async () => {
//     if (!input.trim()) return
//     const message = input.trim()
//     append('user', message)
//     setInput('')
//     setLoading(true)

//     try {
//       const payload = { message }
//       if (coords) {
//         payload.lat = coords.lat
//         payload.lon = coords.lon
//       }

//       const res = await axios.post('/api/chat', payload)
//       if (res.data?.reply) {
//         append('bot', res.data.reply)
//       } else if (res.data?.error) {
//         append('bot', 'Error: ' + res.data.error)
//       } else {
//         append('bot', 'No reply from server.')
//       }
//     } catch (err) {
//       console.error(err)
//       append('bot', 'Request failed: ' + (err.response?.data?.detail || err.message))
//     } finally {
//       setLoading(false)
//     }
//   }

//   const onKey = (e) => { if (e.key === 'Enter') send() }

//   return (
//     <div className="chatbox">
//       <div className="controls">
//         <button onClick={useLocation} className="btn small">Use my location</button>
//         <div className="location-label">{coords ? `Lat: ${coords.lat.toFixed(4)}, Lon: ${coords.lon.toFixed(4)}` : 'Location not set'}</div>
//       </div>

//       <div className="messages">
//         {messages.map((m, i) => (
//           <div key={i} className={`msg ${m.from}`}>
//             <div className="msg-text" dangerouslySetInnerHTML={{ __html: m.text.replace(/\n/g, '<br/>') }} />
//           </div>
//         ))}
//         {loading && <div className="msg bot">Thinking...</div>}
//       </div>

//       <div className="composer">
//         <input
//           value={input}
//           onChange={(e) => setInput(e.target.value)}
//           onKeyDown={onKey}
//           placeholder="Ask a medical question (e.g. 'What are dengue symptoms?')"
//         />
//         <button onClick={send} className="btn">Send</button>
//       </div>
//     </div>
//   )
// }

