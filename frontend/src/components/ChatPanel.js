const ChatPanel = ({ messages, loading }) => {
  return (
    <div className="chat-panel">
      <h3>🤖 AI Assistant</h3>
      <p className="subtext">
        Describe your interaction → AI will fill the form
      </p>

      <div className="chat-messages">
        {messages.length === 0 && (
          <p className="placeholder">
            Try: "Met Dr. Ravi yesterday, positive discussion..."
          </p>
        )}

        {messages.map((msg, i) => (
          <div key={i} className={`msg ${msg.role}`}>
            {msg.text}
          </div>
        ))}

        {loading && <div className="msg ai">Thinking...</div>}
      </div>
    </div>
  );
};

export default ChatPanel;