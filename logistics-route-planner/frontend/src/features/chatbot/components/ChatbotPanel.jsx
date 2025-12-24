import { useState, useRef, useEffect } from 'react';
import { MessageSquare, Send, Sparkles, TrendingUp, AlertCircle, Users, Calendar } from 'lucide-react';
import { post } from '../../../lib/api';

/**
 * ChatbotPanel - Interactive chatbot for logistics queries
 * 
 * Features:
 * - Quick question suggestions
 * - Chat history
 * - Tool call visualization
 * - AI-powered responses
 */
export function ChatbotPanel() {
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState('');
    const [pending, setPending] = useState(false);
    const messagesEndRef = useRef(null);

    // Suggested questions
    const suggestedQuestions = [
        {
            icon: TrendingUp,
            text: "What are the best practices for express delivery optimization?",
            category: "Best Practices"
        },
        {
            icon: AlertCircle,
            text: "What SLO metrics should I monitor for route express-delivery?",
            category: "Monitoring"
        },
        {
            icon: Users,
            text: "Who should I contact for driver support escalation?",
            category: "Support"
        },
        {
            icon: Calendar,
            text: "Is the express-delivery route ready for production launch?",
            category: "Readiness"
        },
        {
            icon: Sparkles,
            text: "Calculate metrics for a 150km route taking 3 hours",
            category: "Calculations"
        },
        {
            icon: MessageSquare,
            text: "What are the critical success factors for last-mile delivery?",
            category: "Strategy"
        }
    ];

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const handleSendMessage = async (messageText = input) => {
        if (!messageText.trim() || pending) return;

        const userMessage = {
            role: 'user',
            content: messageText,
            timestamp: new Date().toISOString()
        };

        setMessages(prev => [...prev, userMessage]);
        setInput('');
        setPending(true);

        try {
            // Send to agent endpoint with the question as context
            const response = await post('/ai/route-readiness', {
                route_slug: 'express-delivery', // Default route
                launch_date: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
                audience_role: 'Driver',
                audience_experience: 'intermediate',
                include_risks: true,
                query: messageText // Add the query
            });

            const assistantMessage = {
                role: 'assistant',
                content: response.gemini_insight || response.summary,
                recommendations: response.recommended_actions,
                toolCalls: response.tool_calls,
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
        setInput(question);
        handleSendMessage(question);
    };

    return (
        <div className="chatbot-container">
            <div className="card-header">
                <h2>
                    <MessageSquare size={24} style={{ display: 'inline-block', marginRight: '8px', verticalAlign: 'middle' }} />
                    AI Logistics Assistant
                </h2>
                <p>Ask questions about routes, delivery optimization, and logistics best practices</p>
            </div>

            {/* Suggested Questions (show when no messages) */}
            {messages.length === 0 && (
                <div className="suggested-questions">
                    <h3 style={{ fontSize: '14px', color: '#888', marginBottom: '16px', textAlign: 'center' }}>
                        Quick Questions
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

                                {/* Show recommendations if available */}
                                {message.recommendations && message.recommendations.length > 0 && (
                                    <div className="message-recommendations">
                                        <strong style={{ fontSize: '13px', color: '#666', display: 'block', marginBottom: '8px' }}>
                                            Recommendations:
                                        </strong>
                                        {message.recommendations.map((rec, i) => (
                                            <div key={i} className="recommendation-item">
                                                <span className={`priority-badge priority-${rec.priority}`}>
                                                    {rec.priority}
                                                </span>
                                                <strong>{rec.title}</strong>
                                                <p style={{ fontSize: '13px', color: '#666', margin: '4px 0 0 0' }}>
                                                    {rec.detail}
                                                </p>
                                            </div>
                                        ))}
                                    </div>
                                )}

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
                <form
                    onSubmit={(e) => {
                        e.preventDefault();
                        handleSendMessage();
                    }}
                    className="chat-input-form"
                >
                    <input
                        type="text"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        placeholder="Ask about routes, delivery optimization, SLO metrics..."
                        disabled={pending}
                        className="chat-input"
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
