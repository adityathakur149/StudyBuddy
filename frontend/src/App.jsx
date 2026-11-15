import { useState } from 'react';
import { BookOpen, Upload, Send, FileText, CheckCircle2, Sparkles, HelpCircle } from 'lucide-react';
import axios from 'axios';

function App() {
  const [messages, setMessages] = useState([
    {
      sender: 'bot',
      text: 'Hello! I am your RAG Study Assistant. Upload a lecture PDF or course notes on the left, and ask me any questions!',
      citations: []
    }
  ]);
  const [input, setInput] = useState('');
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadSuccess, setUploadSuccess] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleFileUpload = async (e) => {
    const selectedFile = e.target.files[0];
    if (!selectedFile) return;

    setFile(selectedFile);
    setUploading(true);
    setUploadSuccess(false);

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      await axios.post('/api/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      setUploadSuccess(true);
      setMessages((prev) => [
        ...prev,
        {
          sender: 'bot',
          text: `✅ Successfully processed and indexed "${selectedFile.name}". You can now ask questions about this document!`,
          citations: []
        }
      ]);
    } catch (err) {
      console.error(err);
      alert('Failed to upload PDF document');
    } finally {
      setUploading(false);
    }
  };

  const handleSend = async (e) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userMsg = input.trim();
    setInput('');
    setMessages((prev) => [...prev, { sender: 'user', text: userMsg }]);
    setLoading(true);

    try {
      const res = await axios.post('/api/query', { question: userMsg });
      setMessages((prev) => [
        ...prev,
        {
          sender: 'bot',
          text: res.data.answer,
          citations: res.data.citations || []
        }
      ]);
    } catch (err) {
      console.error(err);
      setMessages((prev) => [
        ...prev,
        {
          sender: 'bot',
          text: '❌ Apologies, I ran into an issue retrieving an answer. Please check your backend connection.',
          citations: []
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-container">
      <nav className="navbar">
        <div className="brand">
          <div className="brand-icon">
            <BookOpen size={20} />
          </div>
          <span className="brand-title">StudyBuddy AI</span>
        </div>
        <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '6px' }}>
          <Sparkles size={16} color="var(--cyan-accent)" />
          RAG Vector Retrieval Engine Active
        </div>
      </nav>

      <div className="main-content">
        <aside className="sidebar">
          <h3 style={{ fontSize: '1rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <FileText size={18} color="var(--accent-primary)" />
            Document Ingestion
          </h3>

          <label className="dropzone">
            <input type="file" accept=".pdf" onChange={handleFileUpload} style={{ display: 'none' }} />
            <Upload size={32} color="var(--accent-primary)" style={{ marginBottom: '10px' }} />
            <p style={{ fontWeight: 600, fontSize: '0.9rem', marginBottom: '4px' }}>
              {uploading ? 'Processing PDF...' : 'Click or Drag PDF here'}
            </p>
            <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
              Supports PDFs up to 1,000+ pages
            </p>
          </label>

          {file && (
            <div style={{ background: 'rgba(255,255,255,0.03)', padding: '12px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.85rem' }}>
                <FileText size={16} color="var(--cyan-accent)" />
                <span style={{ flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {file.name}
                </span>
                {uploadSuccess && <CheckCircle2 size={16} color="#10b981" />}
              </div>
            </div>
          )}

          <div style={{ marginTop: 'auto', padding: '12px', background: 'rgba(99, 102, 241, 0.05)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-glow)' }}>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <HelpCircle size={14} color="var(--accent-primary)" />
              Powered by LangChain, ChromaDB & PyMuPDF
            </p>
          </div>
        </aside>

        <section className="chat-section">
          <div className="chat-messages">
            {messages.map((msg, idx) => (
              <div
                key={idx}
                className={`message-bubble ${msg.sender === 'user' ? 'message-user' : 'message-bot'}`}
              >
                <p>{msg.text}</p>
                {msg.citations && msg.citations.length > 0 && (
                  <div style={{ marginTop: '12px' }}>
                    <p style={{ fontSize: '0.78rem', fontWeight: 700, color: 'var(--cyan-accent)', marginBottom: '4px' }}>
                      📌 Sources & Citations:
                    </p>
                    {msg.citations.map((cit, cIdx) => (
                      <div key={cIdx} className="citation-card">
                        <strong>{cit.source} (Page {cit.page_number})</strong>
                        <p style={{ marginTop: '4px', fontStyle: 'italic' }}>"{cit.snippet}"</p>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))}
            {loading && (
              <div className="message-bubble message-bot" style={{ fontStyle: 'italic', color: 'var(--text-muted)' }}>
                ⚡ Searching ChromaDB vectors & drafting response...
              </div>
            )}
          </div>

          <form className="input-bar" onSubmit={handleSend}>
            <input
              type="text"
              className="chat-input"
              placeholder="Ask a question about your uploaded PDF notes..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
            />
            <button type="submit" className="send-btn" disabled={loading}>
              <Send size={18} />
            </button>
          </form>
        </section>
      </div>
    </div>
  );
}

export default App;
