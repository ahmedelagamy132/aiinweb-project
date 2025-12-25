import { useState, useRef, useEffect } from 'react';
import { MessageSquare, Send, Cloud, Calculator, TrendingUp, MapPin, Clock } from 'lucide-react';
import { post } from '../../../lib/api';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

/**
 * ChatbotPanel - Conversational AI for route planning and logistics
 * 
 * Features:
 * - Suggested questions for quick start
 * - Real-time weather and traffic data
 * - Route calculations and optimization
 * - Natural language queries
 */
export function ChatbotPanel() {
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState('');
    const [pending, setPending] = useState(false);
    const messagesEndRef = useRef(null);

    // Suggested questions for users
    const suggestedQuestions = [
        {
            icon: Cloud,
            text: "What's the weather in San Francisco?",
            category: "Weather"
        },
        {
            icon: MapPin,
            text: "How do I plan an optimal delivery route?",
            category: "Route Planning"
        },
        {
            icon: TrendingUp,
            text: "What factors affect route efficiency?",
            category: "Optimization"
        },
        {
            icon: Calculator,
            text: "How is fuel consumption calculated?",
            category: "Metrics"
        },
        {
            icon: Clock,
            text: "What are best practices for time window management?",
            category: "Tips"
        },
        {
            icon: MessageSquare,
            text: "What are best practices for last-mile delivery?",
            category: "Best Practices"
        }
    ];

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const handleSendMessage = async (e, questionText = null) => {
        e?.preventDefault();
        
        const messageText = questionText || input.trim();
        if (!messageText || pending) return;

        const userMessage = {
            role: 'user',
            content: messageText,
            timestamp: new Date().toISOString()
        };

        setMessages(prev => [...prev, userMessage]);
        setInput('');
        setPending(true);

        try {
            // Call the chat endpoint
            const response = await post('/ai/chat', {
                question: messageText
            });

            const assistantMessage = {
                role: 'assistant',
                content: response.answer,
                toolCalls: response.tool_calls || [],
                ragContexts: response.rag_contexts || [],
                timestamp: new Date().toISOString()
            };

            setMessages(prev => [...prev, assistantMessage]);
        } catch (error) {
            const errorMessage = {
                role: 'assistant',
                content: `Sorry, I encountered an error: ${error.message}`,
                isError: true,
                timestamp: new Date().toISOString()
            };
            setMessages(prev => [...prev, errorMessage]);
        } finally {
            setPending(false);
        }
    };

    const handleQuickQuestion = (question) => {
        handleSendMessage(null, question);
    };

    return (
        <div className="chatbot-container">
            <div className="card-header">
                <h2>
                    <MessageSquare size={24} style={{ display: 'inline-block', marginRight: '8px', verticalAlign: 'middle' }} />
                    AI Logistics Assistant
                </h2>
                <p>Ask me anything about logistics routes, weather, traffic, and delivery optimization</p>
            </div>

            {/* Suggested Questions (show when no messages) */}
            {messages.length === 0 && (
                <div className="suggested-questions">
                    <h3 style={{ fontSize: '14px', color: '#888', marginBottom: '16px', textAlign: 'center' }}>
                        Try These Questions
                    </h3>
                    <div className="suggestions-grid">
                        {suggestedQuestions.map((suggestion, index) => {
                            const Icon = suggestion.icon;
                            return (
                                <button
                                    key={index}
                                    className="suggestion-card"
                                    onClick={() => handleQuickQuestion(suggestion.text)}
                                >
                                    <Icon size={20} style={{ marginBottom: '8px', color: '#4f46e5' }} />
                                    <span className="suggestion-category">{suggestion.category}</span>
                                    <p className="suggestion-text">{suggestion.text}</p>
                                </button>
                            );
                        })}
                    </div>
                </div>
            )}

            {/* Chat Messages */}
            {messages.length > 0 && (
                <div className="chat-messages">
                    {messages.map((message, index) => (
                        <div key={index} className={`message message-${message.role}`}>
                            <div className="message-content">
                                <div className="message-text markdown-content">
                                    <ReactMarkdown 
                                        remarkPlugins={[remarkGfm]}
                                        components={{
                                            // Style tables
                                            table: ({node, ...props}) => (
                                                <table style={{ borderCollapse: 'collapse', width: '100%', marginTop: '12px', marginBottom: '12px' }} {...props} />
                                            ),
                                            th: ({node, ...props}) => (
                                                <th style={{ border: '1px solid #ddd', padding: '8px', background: '#f0f0f0', textAlign: 'left' }} {...props} />
                                            ),
                                            td: ({node, ...props}) => (
                                                <td style={{ border: '1px solid #ddd', padding: '8px' }} {...props} />
                                            ),
                                            // Style headings
                                            h2: ({node, ...props}) => (
                                                <h2 style={{ fontSize: '18px', fontWeight: '600', marginTop: '16px', marginBottom: '8px', color: '#1a1a1a' }} {...props} />
                                            ),
                                            h3: ({node, ...props}) => (
                                                <h3 style={{ fontSize: '16px', fontWeight: '600', marginTop: '12px', marginBottom: '6px', color: '#333' }} {...props} />
                                            ),
                                            // Style lists
                                            ul: ({node, ...props}) => (
                                                <ul style={{ marginTop: '8px', marginBottom: '8px', paddingLeft: '20px' }} {...props} />
                                            ),
                                            ol: ({node, ...props}) => (
                                                <ol style={{ marginTop: '8px', marginBottom: '8px', paddingLeft: '20px' }} {...props} />
                                            ),
                                            li: ({node, ...props}) => (
                                                <li style={{ marginBottom: '4px', lineHeight: '1.6' }} {...props} />
                                            ),
                                            // Style code blocks
                                            code: ({node, inline, ...props}) => 
                                                inline ? (
                                                    <code style={{ background: '#f4f4f4', padding: '2px 6px', borderRadius: '3px', fontSize: '13px' }} {...props} />
                                                ) : (
                                                    <code style={{ display: 'block', background: '#f4f4f4', padding: '12px', borderRadius: '6px', overflow: 'auto', fontSize: '13px' }} {...props} />
                                                ),
                                            // Style links
                                            a: ({node, ...props}) => (
                                                <a style={{ color: '#4f46e5', textDecoration: 'none' }} target="_blank" rel="noopener noreferrer" {...props} />
                                            ),
                                            // Style horizontal rules
                                            hr: ({node, ...props}) => (
                                                <hr style={{ border: 'none', borderTop: '1px solid #e0e0e0', margin: '16px 0' }} {...props} />
                                            ),
                                            // Style paragraphs
                                            p: ({node, ...props}) => (
                                                <p style={{ marginBottom: '8px', lineHeight: '1.6' }} {...props} />
                                            )
                                        }}
                                    >
                                        {message.content}
                                    </ReactMarkdown>
                                </div>

                                {/* Show tool calls if available */}
                                {message.toolCalls && message.toolCalls.length > 0 && (
                                    <details className="message-tools" style={{ marginTop: '12px' }}>
                                        <summary style={{ cursor: 'pointer', fontSize: '13px', color: '#666' }}>
                                            🔧 Tools Used ({message.toolCalls.length})
                                        </summary>
                                        <div className="tools-list">
                                            {message.toolCalls.map((tool, i) => (
                                                <div key={i} className="tool-item">
                                                    <code className="tool-name">{tool.tool}</code>
                                                    {tool.arguments && Object.keys(tool.arguments).length > 0 && (
                                                        <div className="tool-args">
                                                            {Object.entries(tool.arguments).map(([key, value]) => (
                                                                <span key={key} className="tool-arg">
                                                                    {key}: <strong>{JSON.stringify(value)}</strong>
                                                                </span>
                                                            ))}
                                                        </div>
                                                    )}
                                                    {tool.output && (
                                                        <details style={{ marginTop: '8px' }}>
                                                            <summary style={{ fontSize: '12px', color: '#888', cursor: 'pointer' }}>
                                                                View Output
                                                            </summary>
                                                            <pre style={{ 
                                                                fontSize: '11px', 
                                                                background: '#f8f8f8', 
                                                                padding: '8px', 
                                                                borderRadius: '4px',
                                                                overflow: 'auto',
                                                                maxHeight: '200px',
                                                                marginTop: '4px'
                                                            }}>
                                                                {tool.output}
                                                            </pre>
                                                        </details>
                                                    )}
                                                </div>
                                            ))}
                                        </div>
                                    </details>
                                )}

                                {/* Show RAG contexts if available */}
                                {message.ragContexts && message.ragContexts.length > 0 && (
                                    <details className="message-rag" style={{ marginTop: '12px' }}>
                                        <summary style={{ cursor: 'pointer', fontSize: '13px', color: '#666' }}>
                                            📚 Knowledge Sources ({message.ragContexts.length})
                                        </summary>
                                        <div className="rag-list">
                                            {message.ragContexts.map((ctx, i) => (
                                                <div key={i} style={{ 
                                                    padding: '8px', 
                                                    background: '#f0f9ff', 
                                                    borderRadius: '4px', 
                                                    marginTop: '8px',
                                                    fontSize: '12px'
                                                }}>
                                                    <div style={{ fontWeight: '600', color: '#0369a1', marginBottom: '4px' }}>
                                                        {ctx.source}
                                                    </div>
                                                    <div style={{ color: '#666', lineHeight: '1.5' }}>
                                                        {ctx.content.substring(0, 200)}...
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    </details>
                                )}
                            </div>
                            <div className="message-timestamp">
                                {new Date(message.timestamp).toLocaleTimeString()}
                            </div>
                        </div>
                    ))}
                    {pending && (
                        <div className="message message-assistant">
                            <div className="message-content">
                                <div className="typing-indicator">
                                    <span></span>
                                    <span></span>
                                    <span></span>
                                </div>
                            </div>
                        </div>
                    )}
                    <div ref={messagesEndRef} />
                </div>
            )}

            {/* Input Area */}
            <div className="chat-input-area">
                <form onSubmit={(e) => { e.preventDefault(); handleSendMessage(); }} className="chat-input-form">
                    <input
                        type="text"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        placeholder="Ask about weather, routes, traffic, metrics, optimization..."
                        disabled={pending}
                        className="chat-input"
                        autoFocus
                    />
                    <button
                        type="submit"
                        disabled={!input.trim() || pending}
                        className="chat-send-btn"
                    >
                        <Send size={20} />
                    </button>
                </form>
            </div>
        </div>
    );
}
