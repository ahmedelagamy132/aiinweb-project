import { useState, useRef, useEffect } from 'react';
import { MessageSquare, Send, Cloud, Calculator, TrendingUp, MapPin, Clock } from 'lucide-react';
import { post } from '../../../lib/api';

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
            icon: Calculator,
            text: "Calculate metrics for a 150km route with 8 stops",
            category: "Calculations"
        },
        {
            icon: TrendingUp,
            text: "Optimize my delivery route stops for efficiency",
            category: "Optimization"
        },
        {
            icon: MapPin,
            text: "Check traffic conditions in Los Angeles",
            category: "Traffic"
        },
        {
            icon: Clock,
            text: "Validate route timing for afternoon deliveries",
            category: "Validation"
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
                                <div className="message-text">{message.content}</div>

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
