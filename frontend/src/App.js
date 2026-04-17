import { useState } from "react";
import FormPanel from "./components/FormPanel";
import ChatPanel from "./components/ChatPanel";
import ChatInput from "./components/ChatInput";
import "./App.css";

function App() {
  const [formData, setFormData] = useState({});
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);

  const sendMessage = async (message) => {
    setLoading(true);

    try {
      const res = await fetch("http://127.0.0.1:8000/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ message })
      });

      const data = await res.json();

      setMessages((prev) => [
        ...prev,
        { role: "user", text: message },
        { role: "ai", text: data.response }
      ]);

      if (data.data) {
        setFormData(data.data);
      }

    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { role: "ai", text: "⚠️ Backend error" }
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app">
      {/* LEFT */}
      <div className="form-section">
        <FormPanel formData={formData} />
      </div>

      {/* RIGHT */}
      <div className="chat-section">
        <ChatPanel messages={messages} loading={loading} />
        <ChatInput onSend={sendMessage} />
      </div>
    </div>
  );
}

export default App;