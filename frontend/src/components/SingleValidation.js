import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';

const SingleValidation = () => {
  // State for ICD search
  const [icdQuery, setIcdQuery] = useState('');
  const [icdResults, setIcdResults] = useState([]);
  const [selectedIcd, setSelectedIcd] = useState(null);
  const [showIcdDropdown, setShowIcdDropdown] = useState(false);
  
  // State for ACHI search
  const [achiQuery, setAchiQuery] = useState('');
  const [achiResults, setAchiResults] = useState([]);
  const [selectedAchi, setSelectedAchi] = useState(null);
  const [showAchiDropdown, setShowAchiDropdown] = useState(false);
  
  // Validation state
  const [validationResult, setValidationResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  // Refs for click outside detection
  const icdRef = useRef(null);
  const achiRef = useRef(null);
  
  // Debounce timers
  const icdTimerRef = useRef(null);
  const achiTimerRef = useRef(null);
  
  // Search ICD codes
  useEffect(() => {
    if (icdQuery.length >= 2) {
      // Clear previous timer
      if (icdTimerRef.current) {
        clearTimeout(icdTimerRef.current);
      }
      
      // Set new timer (300ms debounce)
      icdTimerRef.current = setTimeout(() => {
        axios.get(`/api/search/icd/${encodeURIComponent(icdQuery)}`)
          .then(response => {
            setIcdResults(response.data);
            setShowIcdDropdown(true);
          })
          .catch(err => {
            console.error('ICD search error:', err);
            setIcdResults([]);
          });
      }, 300);
    } else {
      setIcdResults([]);
      setShowIcdDropdown(false);
    }
    
    return () => {
      if (icdTimerRef.current) {
        clearTimeout(icdTimerRef.current);
      }
    };
  }, [icdQuery]);
  
  // Search ACHI codes
  useEffect(() => {
    if (achiQuery.length >= 2) {
      // Clear previous timer
      if (achiTimerRef.current) {
        clearTimeout(achiTimerRef.current);
      }
      
      // Set new timer (300ms debounce)
      achiTimerRef.current = setTimeout(() => {
        axios.get(`/api/search/achi/${encodeURIComponent(achiQuery)}`)
          .then(response => {
            setAchiResults(response.data);
            setShowAchiDropdown(true);
          })
          .catch(err => {
            console.error('ACHI search error:', err);
            setAchiResults([]);
          });
      }, 300);
    } else {
      setAchiResults([]);
      setShowAchiDropdown(false);
    }
    
    return () => {
      if (achiTimerRef.current) {
        clearTimeout(achiTimerRef.current);
      }
    };
  }, [achiQuery]);
  
  // Click outside to close dropdowns
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (icdRef.current && !icdRef.current.contains(event.target)) {
        setShowIcdDropdown(false);
      }
      if (achiRef.current && !achiRef.current.contains(event.target)) {
        setShowAchiDropdown(false);
      }
    };
    
    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);
  
  // Handle ICD selection
  const handleSelectIcd = (code) => {
    setSelectedIcd(code);
    setIcdQuery(`${code.code} - ${code.description}`);
    setShowIcdDropdown(false);
    setValidationResult(null); // Clear previous result
  };
  
  // Handle ACHI selection
  const handleSelectAchi = (code) => {
    setSelectedAchi(code);
    setAchiQuery(`${code.code} - ${code.description}`);
    setShowAchiDropdown(false);
    setValidationResult(null); // Clear previous result
  };
  
  // Handle validation
  const handleValidate = async () => {
    if (!selectedIcd || !selectedAchi) {
      setError('Please select both ICD and ACHI codes');
      return;
    }
    
    setLoading(true);
    setError(null);
    setValidationResult(null);
    
    try {
      const response = await axios.post('/api/validate', {
        icd_code: selectedIcd.code,
        achi_code: selectedAchi.code
      });
      
      setValidationResult(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Validation failed. Please try again.');
      console.error('Validation error:', err);
    } finally {
      setLoading(false);
    }
  };
  
  // Get result container class based on confidence and validity
  const getResultClass = () => {
    if (!validationResult) return '';
    
    const { is_valid, confidence } = validationResult;
    
    if (is_valid) {
      if (confidence >= 0.90) return 'valid-high';
      if (confidence >= 0.75) return 'valid-moderate';
      return 'uncertain';
    } else {
      if (confidence >= 0.90) return 'invalid-high';
      if (confidence >= 0.75) return 'invalid-moderate';
      return 'uncertain';
    }
  };
  
  // Get source badge class
  const getSourceBadgeClass = (source) => {
    if (source === 'database_exact') return 'database';
    if (source.includes('ai')) return 'ai';
    return 'error';
  };
  
  // Get source label
  const getSourceLabel = (source) => {
    if (source === 'database_exact') return 'Database Match';
    if (source === 'ai_with_examples') return 'AI with Examples';
    if (source === 'ai_inference') return 'AI Inference';
    return 'Error';
  };
  
  return (
    <div className="validation-container">
      <h2 className="validation-title">Code Pair Validation</h2>
      
      {/* ICD Search */}
      <div className="form-group" ref={icdRef}>
        <label htmlFor="icd-search">ICD-10-AM Diagnosis Code</label>
        <input
          id="icd-search"
          type="text"
          placeholder="Type code or diagnosis (e.g., K02 or dental caries)..."
          value={icdQuery}
          onChange={(e) => setIcdQuery(e.target.value)}
          onFocus={() => icdResults.length > 0 && setShowIcdDropdown(true)}
        />
        
        {showIcdDropdown && icdResults.length > 0 && (
          <div className="dropdown-results">
            {icdResults.map((result, index) => (
              <div
                key={index}
                className="dropdown-item"
                onClick={() => handleSelectIcd(result)}
              >
                <span className="dropdown-item-code">{result.code}</span>
                <span className="dropdown-item-desc">{result.description}</span>
              </div>
            ))}
          </div>
        )}
      </div>
      
      {/* ACHI Search */}
      <div className="form-group" ref={achiRef}>
        <label htmlFor="achi-search">ACHI Procedure Code</label>
        <input
          id="achi-search"
          type="text"
          placeholder="Type code or procedure (e.g., 92209 or nebuliser)..."
          value={achiQuery}
          onChange={(e) => setAchiQuery(e.target.value)}
          onFocus={() => achiResults.length > 0 && setShowAchiDropdown(true)}
        />
        
        {showAchiDropdown && achiResults.length > 0 && (
          <div className="dropdown-results">
            {achiResults.map((result, index) => (
              <div
                key={index}
                className="dropdown-item"
                onClick={() => handleSelectAchi(result)}
              >
                <span className="dropdown-item-code">{result.code}</span>
                <span className="dropdown-item-desc">{result.description}</span>
              </div>
            ))}
          </div>
        )}
      </div>
      
      {/* Selected Codes Display */}
      {(selectedIcd || selectedAchi) && (
        <div className="selected-codes">
          {selectedIcd && (
            <div className="selected-code">
              <strong>Selected ICD:</strong>
              <span>{selectedIcd.code} - {selectedIcd.description}</span>
            </div>
          )}
          {selectedAchi && (
            <div className="selected-code">
              <strong>Selected ACHI:</strong>
              <span>{selectedAchi.code} - {selectedAchi.description}</span>
            </div>
          )}
        </div>
      )}
      
      {/* Validate Button */}
      <button
        className="validate-button"
        onClick={handleValidate}
        disabled={!selectedIcd || !selectedAchi || loading}
      >
        {loading ? 'Validating...' : 'Validate Code Pair'}
      </button>
      
      {/* Error Display */}
      {error && (
        <div className="results-container invalid-high">
          <div className="result-status invalid">Error</div>
          <p>{error}</p>
        </div>
      )}
      
      {/* Loading State */}
      {loading && (
        <div className="loading">
          Validating with AI
        </div>
      )}
      
      {/* Validation Results */}
      {validationResult && !loading && (
        <div className={`results-container ${getResultClass()}`}>
          <div className={`result-status ${validationResult.is_valid ? 'valid' : 'invalid'}`}>
            {validationResult.is_valid ? 'Valid Pairing' : 'Invalid Pairing'}
          </div>
          
          <div className="result-section">
            <h3>Clinical Reasoning</h3>
            <p>{validationResult.reasoning}</p>
          </div>
          
          <div className="result-section">
            <h3>Confidence</h3>
            <div className="confidence-display">
              <div className="confidence-bar">
                <div 
                  className="confidence-fill" 
                  style={{ width: `${validationResult.confidence * 100}%` }}
                />
              </div>
              <span className="confidence-text">
                {(validationResult.confidence * 100).toFixed(1)}%
              </span>
            </div>
          </div>
          
          <div className="result-section">
            <h3>Certainty Explanation</h3>
            <p>{validationResult.certainty_explanation}</p>
          </div>
          
          <div className="result-section">
            <h3>Validation Source</h3>
            <p>
              <span className={`source-badge ${getSourceBadgeClass(validationResult.source)}`}>
                {getSourceLabel(validationResult.source)}
              </span>
              {validationResult.similar_examples_count > 0 && (
                <span style={{ marginLeft: '1rem', color: '#4a5568' }}>
                  ({validationResult.similar_examples_count} similar examples used)
                </span>
              )}
            </p>
          </div>
        </div>
      )}
    </div>
  );
};

export default SingleValidation;

