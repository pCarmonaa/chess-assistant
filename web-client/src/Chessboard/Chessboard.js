import React, { useState, useEffect } from 'react';
import './Chessboard.css';
import { Chessboard as ReactChessboard } from 'react-chessboard';
import { Chess } from 'chess.js';
import { FaArrowLeft, FaArrowRight, FaSyncAlt, FaUndo } from 'react-icons/fa';

const ChessboardComponent = ({ fen, setFen }) => {
  const [game, setGame] = useState(new Chess(fen));
  const [pgn, setPgn] = useState(game.pgn());
  const [history, setHistory] = useState([]);
  const [orientation, setOrientation] = useState('white');
  const [selectedSquares, setSelectedSquares] = useState([]);

  useEffect(() => {
    const handleKeyDown = (event) => {
      if (event.key === 'ArrowLeft') {
        goBack();
      } else if (event.key === 'ArrowRight') {
        goForward();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
    };
  });

  const onDrop = (sourceSquare, targetSquare, piece) => {
    try {
      var promotion = piece[1].toLowerCase();
      const move = game.move({
        from: sourceSquare,
        to: targetSquare,
        promotion: promotion,
      });

      if (move === null) 
        return false;

      setFen(game.fen());
      setPgn(game.pgn({ max_width: 5, newline_char: ' ' }));
      setHistory(game.history());
      return true;
    } 
    catch (e) {
      return false;
    }
  };

  const handleFenChange = (event) => {
    const currentFen = game.fen();
    try {
      const newFen = event.target.value;
      setFen(newFen);
      const newGame = new Chess(newFen);
      setGame(newGame);
      setPgn(newGame.pgn({ max_width: 5, newline_char: ' ' }));
      setHistory(newGame.history());
    }
    catch {
      setFen(currentFen);
    }
  };

  const handlePgnChange = (event) => {
    const newPgn = event.target.value;
    setPgn(newPgn);
    try {
      game.loadPgn(newPgn);
      setFen(game.fen());
      setHistory(game.history());
    } 
    catch {}
  };

  const goBack = () => {
    game.undo();
    setFen(game.fen());
    setPgn(game.pgn({ max_width: 5, newline_char: ' ' }));
  };

  const goForward = () => {
    const moves = game.history({ verbose: true });
    const nextMove = history[moves.length];
    if (nextMove) {
      game.move(nextMove);
      setFen(game.fen());
      setPgn(game.pgn({ max_width: 5, newline_char: ' ' }));
    }
  };

  const flipBoard = () => {
    setOrientation(orientation === 'white' ? 'black' : 'white');
  };

  const handleRightClick = (square) => {
    setSelectedSquares((prevSelectedSquares) => {
      if (prevSelectedSquares.includes(square)) {
        return prevSelectedSquares.filter((s) => s !== square);
      } else {
        return [...prevSelectedSquares, square];
      }
    });
  };

  const handleLeftClick = () => {
    setSelectedSquares([]);
  };

  const customSquareStyles = selectedSquares.reduce((acc, square) => {
    acc[square] = {
      backgroundColor: 'rgba(240, 99, 92, 0.5)',
      boxShadow: '0 0 10px rgba(240, 99, 92, 0.9)',
    };
    return acc;
  }, {});

  const resetBoard = () => {
    const newGame = new Chess();
    setGame(newGame);
    setFen(newGame.fen());
    setPgn(newGame.pgn());
    setHistory([]);
    setSelectedSquares([]);
  };

  return (
    <div className="chessboard-wrapper">
      <div className="info-container">
        <div className="fen-input">
          <label htmlFor="fen">FEN: </label>
          <textarea id="fen" value={fen} onChange={handleFenChange} />
        </div>
        <div className="pgn-input">
          <label htmlFor="pgn">PGN: </label>
          <textarea id="pgn" value={pgn} onChange={handlePgnChange} />
        </div>
      </div>
      <div className="chessboard-container">
        <button className="reset-button" onClick={resetBoard}>
          <FaUndo />
        </button>
        <button className="flip-button" onClick={flipBoard}>
          <FaSyncAlt />
        </button>
        <ReactChessboard
          position={fen}
          onPieceDrop={onDrop}
          boardWidth={700}
          boardOrientation={orientation}
          customSquareStyles={customSquareStyles}
          onSquareRightClick={handleRightClick}
          onSquareClick={handleLeftClick}
        />
        <div className="controls">
          <div className="navigation-buttons">
            <button onClick={goBack}>
              <FaArrowLeft />
            </button>
            <button onClick={goForward}>
              <FaArrowRight />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChessboardComponent;
