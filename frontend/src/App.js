import React from 'react';
import './App.css';
import SingleValidation from './components/SingleValidation';

function App() {
  return (
    <div className="App">
      <header className="App-header">
        <h1>ICD-10-AM & ACHI Code Validation System</h1>
        <p className="subtitle">Professional Medical Code Validation with AI</p>
      </header>
      
      <main className="App-main">
        <SingleValidation />
      </main>
      
      <footer className="App-footer">
        <p>Powered by GPT-4.1 Mini | RAG-Enhanced Validation</p>
      </footer>
    </div>
  );
}

export default App;

