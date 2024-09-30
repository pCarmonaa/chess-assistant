import React, { useState } from 'react';
import './App.css';
import ChessboardComponent from './Chessboard/Chessboard';
import Chatbot from './Chatbot/Chatbot';
import logo from './logo.png';

function App() {
  const [fen, setFen] = useState('rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1');

  return (
    <div className="App">
      <header className="App-header">
        <img src={logo} alt="Logo" className="App-logo" />
        <h1>Chess Assistant</h1>
      </header>
      <main>
        <div className="container">
          <div className="chessboard-section">
            <ChessboardComponent fen={fen} setFen={setFen} />
          </div>
          <div className="chat-container">
            <Chatbot fen={fen} />
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;
