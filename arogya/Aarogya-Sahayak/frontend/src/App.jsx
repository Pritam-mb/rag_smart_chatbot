import React from 'react'
import ChatBox from './components/ChatBox'

export default function App() {
  return (
    <div className="app-root">
      <header className="app-header">
        <h1>Arogya Sahayak</h1>
        <p className="subtitle">Medical assistant chat — simple, safe, and local</p>
      </header>
      <main className="app-main">
        <ChatBox />
      </main>
      <footer className="app-footer">Built with ❤️ — Frontend only (does not change backend)</footer>
    </div>
  )
}

