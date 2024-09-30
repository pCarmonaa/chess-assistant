import React, { useState, useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import './Chatbot.css';
import userIcon from '../assets/user-character.png';
import professorIcon from '../assets/bot-character.png';

const Chatbot = ({ fen }) => {
  const [messages, setMessages] = useState([]);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const aspects = [
    'General analysis',
    'Material',
    'Pawn structure',
    'King\'s safety',
    'Piece activity',
    'Threats',
    'Space',
    'Plans'
  ];

  useEffect(() => {
    setMessages([{ sender: 'bot', text: "Hi, I'm your chess assistant. Set a position on the board, and select the analysis you want." }]);
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleAspectSelection = async (aspect) => {
    const message = buildUserMessage(aspect);
    const userMessage = { sender: 'user', text: message };
    setMessages((prevMessages) => [...prevMessages, userMessage]);
    setLoading(true);
  
    try {
      console.log(JSON.stringify({
        aspect: aspect,
        fen: fen,
      }));
      const response = await fetch(`http://localhost:8010/proxy/analyze?aspect=${encodeURIComponent(aspect)}` +
          `&fen=${encodeURIComponent(fen)}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
  
      const data = await response.json();
      setLoading(false);
      if (response.ok) {
        const formattedAnswer = data.answer.replace(/\n/g, '  \n');
        const botMessage = { sender: 'bot', text: formattedAnswer };
        setMessages((prevMessages) => [...prevMessages, botMessage]);
      } else {
        handleError(data.error);
      }
    } catch (error) {
      setLoading(false);
      handleError('Error de conexión con el servidor.');
    }
  }; 

  const handleError = (errorMessage) => {
    setError(errorMessage);
    setTimeout(() => {
      setError(null);
    }, 5000);
  };

  const buildUserMessage = (aspect) => {
    if(aspect === 'General analysis') 
      return 'Make a complete analysis of the position.';
    else if(aspect === 'Plans')
      return 'Make an analysis of possible plans on the position.';
    else
      return `Make an analysis of the ${aspect} of the position.`;
  };

  return (
    <div className="chatbot">
      {error && (
        <div className="error-message">
          {error}
        </div>
      )}
      <div className="messages">
        {messages.map((message, index) => (
          <div
            key={index}
            className={`message-container ${message.sender === 'user' ? 'user' : 'bot'}`}
          >
            {message.sender === 'bot' && <img src={professorIcon} alt="Bot" className="icon bot-icon" />}
            {message.sender === 'user' && <img src={userIcon} alt="User" className="icon user-icon" />}
            <div className={`message ${message.sender === 'user' ? 'user' : 'bot'}`}>
              {message.sender === 'user' ? (
                message.text
              ) : (
                <ReactMarkdown>{message.text}</ReactMarkdown>
              )}
            </div>
          </div>
        ))}
        {loading && (
          <div className="loading-container">
            <div className="loading-spinner" />
            <p>Generating analysis...</p>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>
      <div className="button-container">
        {aspects.map((aspect) => (
          <button 
            key={aspect} 
            onClick={() => handleAspectSelection(aspect)} 
            disabled={loading}
          >
            {aspect}
          </button>
        ))}
      </div>
    </div>
  );
};

export default Chatbot;
