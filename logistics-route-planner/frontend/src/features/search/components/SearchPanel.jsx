import React, { useState } from 'react';
import { Search, FileText, BookOpen } from 'lucide-react';
import { get } from '../../../lib/api';

/**
 * SearchPanel - RAG document search interface
 */
export function SearchPanel() {
    const [query, setQuery] = useState('');
    const [results, setResults] = useState([]);
    const [pending, setPending] = useState(false);
    const [error, setError] = useState('');

    const handleSearch = async (e) => {
        e.preventDefault();
        if (!query.trim()) return;

        setPending(true);
        setError('');
        
        try {
            const data = await get(`/ai/search?query=${encodeURIComponent(query)}&k=5`);
            setResults(data.results || []);
        } catch (err) {
            setError(err.message || 'Search failed');
            setResults([]);
        } finally {
            setPending(false);
        }
    };

    return (
        <div>
            <div className="card-header">
                <h2><Search size={24} style={{ display: 'inline-block', marginRight: '8px', verticalAlign: 'middle' }} />Document Search</h2>
                <p>Search through logistics knowledge base using semantic search powered by SentenceTransformers</p>
            </div>

            <form onSubmit={handleSearch} className="form" style={{ marginBottom: '2rem' }}>
                <div className="form-group">
                    <label htmlFor="searchQuery">Search Query</label>
                    <input
                        type="text"
                        id="searchQuery"
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        placeholder="e.g., driver safety, last mile delivery, vehicle maintenance"
                        autoFocus
                    />
                    <small className="text-secondary">
                        Semantic search understands meaning: "truck" will match "vehicle", "fleet"
                    </small>
                </div>

                <button type="submit" disabled={pending || !query.trim()}>
                    {pending ? 'Searching...' : (
                        <><Search size={16} style={{ display: 'inline-block', marginRight: '6px', verticalAlign: 'middle' }} />Search Documents</>
                    )}
                </button>
            </form>

            {error && <div className="alert alert-error">{error}</div>}

            {results.length > 0 && (
                <div className="search-results">
                    <h3><BookOpen size={20} style={{ display: 'inline-block', marginRight: '8px', verticalAlign: 'middle' }} />Found {results.length} Results</h3>
                    <div className="results-grid">
                        {results.map((result, index) => (
                            <div key={index} className="search-result-card">
                                <div className="result-header">
                                    <span className="result-source"><FileText size={16} style={{ display: 'inline-block', marginRight: '6px', verticalAlign: 'middle' }} />{result.source}</span>
                                    <span className="result-score">
                                        Score: {(1 / (1 + result.score)).toFixed(3)}
                                    </span>
                                </div>
                                <div className="result-content">
                                    {result.content}
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {!pending && results.length === 0 && query && (
                <div className="text-secondary" style={{ textAlign: 'center', padding: '2rem' }}>
                    No results found. Try different keywords.
                </div>
            )}
        </div>
    );
}
