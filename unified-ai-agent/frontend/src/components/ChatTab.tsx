import React, { useState, useRef, useEffect } from 'react';
import { api } from '../api/client';
import { ChatMessage, Citation, DetectedNeed } from '../types';
import { Send, Bot, User, ChevronDown, ChevronUp, BookOpen, AlertCircle, Sparkles, Loader2 } from 'lucide-react';

export const ChatTab: React.FC = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'welcome',
      sender: 'agent',
      text: "Namaste! I am your Unified Citizen AI Advisor. You can ask me about government schemes, financial assistance, startup support, or application procedures. How can I help you today?",
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [expandedTrace, setExpandedTrace] = useState<Record<string, boolean>>({});
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const toggleTrace = (id: string) => {
    setExpandedTrace(prev => ({ ...prev, [id]: !prev[id] }));
  };

  const handleSend = async (textToSend?: string) => {
    const query = textToSend || input;
    if (!query.trim() || isLoading) return;

    const userMsg: ChatMessage = {
      id: 'user-' + Date.now(),
      sender: 'citizen',
      text: query.trim(),
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages(prev => [...prev, userMsg]);
    if (!textToSend) setInput('');
    setIsLoading(true);

    try {
      const response = await api.chat(query.trim());
      const agentMsg: ChatMessage = {
        id: 'agent-' + Date.now(),
        sender: 'agent',
        text: response.response || response.answer || "No response received.",
        thought_trace_summary: response.thought_trace_summary,
        citations: response.citations || response.sources || [],
        detected_needs: response.detected_needs || [],
        tool_calls: response.tool_calls_executed || response.tools_called || [],
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages(prev => [...prev, agentMsg]);
    } catch (err: any) {
      const errorMsg: ChatMessage = {
        id: 'error-' + Date.now(),
        sender: 'agent',
        text: "I encountered an issue processing your request: " + (err.message || "Unknown error") + ". Please try again.",
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages(prev => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  const quickPrompts = [
    "What schemes can help my DPIIT-recognized startup?",
    "Check PM Kisan eligibility criteria",
    "I need financial assistance for agriculture and seeds",
  ];

  return (
    <div className="flex flex-col h-[calc(100vh-12rem)] max-w-5xl mx-auto bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
      {/* Messages Scroll Area */}
      <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-6">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex items-start gap-3 ${msg.sender === 'citizen' ? 'flex-row-reverse' : 'flex-row'}`}
          >
            <div
              className={`w-9 h-9 rounded-full flex items-center justify-center shrink-0 shadow-sm ${
                msg.sender === 'citizen'
                  ? 'bg-govblue-600 text-white'
                  : 'bg-emerald-600 text-white'
              }`}
            >
              {msg.sender === 'citizen' ? <User className="w-5 h-5" /> : <Bot className="w-5 h-5" />}
            </div>

            <div
              className={`max-w-[85%] sm:max-w-[75%] rounded-2xl p-4 shadow-sm ${
                msg.sender === 'citizen'
                  ? 'bg-govblue-600 text-white rounded-tr-none'
                  : 'bg-slate-50 text-slate-900 border border-slate-200 rounded-tl-none'
              }`}
            >
              {/* Message text */}
              <div className="text-sm leading-relaxed whitespace-pre-wrap">{msg.text}</div>

              {/* Detected Needs Badges */}
              {msg.detected_needs && msg.detected_needs.length > 0 && (
                <div className="mt-3 pt-3 border-t border-slate-200 flex flex-wrap gap-1.5 items-center">
                  <span className="text-xs font-semibold text-slate-500 mr-1 flex items-center">
                    <Sparkles className="w-3.5 h-3.5 mr-1 text-amber-500" />
                    Identified Needs:
                  </span>
                  {msg.detected_needs.map((need, idx) => (
                    <span
                      key={idx}
                      className={`text-xs px-2.5 py-0.5 rounded-full font-medium ${
                        need.urgency === 'HIGH' || need.urgency === 'CRITICAL'
                          ? 'bg-rose-100 text-rose-800 border border-rose-200'
                          : need.urgency === 'MEDIUM'
                          ? 'bg-amber-100 text-amber-800 border border-amber-200'
                          : 'bg-blue-100 text-blue-800 border border-blue-200'
                      }`}
                    >
                      {need.category} ({need.urgency})
                    </span>
                  ))}
                </div>
              )}

              {/* Verified Citations Chips */}
              {msg.citations && msg.citations.length > 0 && (
                <div className="mt-3 pt-3 border-t border-slate-200">
                  <span className="text-xs font-semibold text-slate-500 flex items-center mb-1.5">
                    <BookOpen className="w-3.5 h-3.5 mr-1 text-govblue-600" />
                    Statutory Citations:
                  </span>
                  <div className="flex flex-wrap gap-2">
                    {msg.citations.map((c, idx) => (
                      <div
                        key={idx}
                        className="text-xs bg-white border border-slate-300 rounded-lg p-2 text-slate-700 shadow-2xs hover:border-govblue-500 transition-colors"
                      >
                        <div className="font-semibold text-govblue-700">
                          {c.scheme_name || (c as any).scheme}
                        </div>
                        <div className="text-slate-500 text-[11px] mt-0.5">
                          Section: {c.section} | Page {c.page_number ?? (c as any).page}
                        </div>
                        {(c.clause_text || (c as any).content) && (
                          <div className="text-[11px] text-slate-600 mt-1 italic line-clamp-2">
                            "{c.clause_text || (c as any).content}"
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Collapsible Thought Trace Summary */}
              {msg.thought_trace_summary && (
                <div className="mt-2.5 pt-2 border-t border-slate-200">
                  <button
                    onClick={() => toggleTrace(msg.id)}
                    className="flex items-center text-xs text-slate-500 hover:text-slate-800 font-medium"
                  >
                    <span>Agent Reasoning Trace</span>
                    {expandedTrace[msg.id] ? (
                      <ChevronUp className="w-3.5 h-3.5 ml-1" />
                    ) : (
                      <ChevronDown className="w-3.5 h-3.5 ml-1" />
                    )}
                  </button>
                  {expandedTrace[msg.id] && (
                    <div className="mt-2 p-2.5 bg-slate-100 rounded-lg text-xs font-mono text-slate-700 whitespace-pre-wrap border border-slate-200">
                      {msg.thought_trace_summary}
                    </div>
                  )}
                </div>
              )}

              <div
                className={`text-[10px] mt-2 text-right ${
                  msg.sender === 'citizen' ? 'text-blue-100' : 'text-slate-400'
                }`}
              >
                {msg.timestamp}
              </div>
            </div>
          </div>
        ))}
        {isLoading && (
          <div className="flex items-start gap-3">
            <div className="w-9 h-9 rounded-full bg-emerald-600 text-white flex items-center justify-center shrink-0 shadow-sm">
              <Bot className="w-5 h-5" />
            </div>
            <div className="bg-slate-50 border border-slate-200 rounded-2xl rounded-tl-none p-4 shadow-sm flex items-center space-x-2 text-slate-600">
              <Loader2 className="w-4 h-4 animate-spin text-govblue-600" />
              <span className="text-sm">Consulting statutory guidelines & database...</span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Suggested Prompts */}
      <div className="px-4 py-2 bg-slate-50 border-t border-slate-200 flex flex-wrap gap-2 items-center">
        <span className="text-xs text-slate-500 font-medium">Try asking:</span>
        {quickPrompts.map((prompt, idx) => (
          <button
            key={idx}
            disabled={isLoading}
            onClick={() => handleSend(prompt)}
            className="text-xs bg-white hover:bg-govblue-50 hover:text-govblue-700 text-slate-700 border border-slate-200 px-3 py-1 rounded-full transition-colors truncate max-w-[280px]"
          >
            {prompt}
          </button>
        ))}
      </div>

      {/* Input Area */}
      <div className="p-4 bg-white border-t border-slate-200">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSend();
          }}
          className="flex items-center gap-2"
        >
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type your question in English or regional context..."
            disabled={isLoading}
            className="flex-1 px-4 py-2.5 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-govblue-500 focus:border-transparent text-sm disabled:bg-slate-100"
          />
          <button
            type="submit"
            disabled={isLoading || !input.trim()}
            className="px-4 py-2.5 bg-govblue-600 text-white rounded-lg hover:bg-govblue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center shadow-sm"
          >
            <Send className="w-4 h-4" />
          </button>
        </form>
      </div>
    </div>
  );
};
