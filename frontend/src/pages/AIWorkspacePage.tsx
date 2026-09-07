import React, { useState, useRef, useEffect } from 'react';
import { useInvestigationStore } from '../stores/investigation';
import { 
  MessageSquare, Send, Sparkles, Wallet, Shield, Activity, 
  Database, Globe, Clock, AlertTriangle, ArrowUpRight, ArrowDownRight
} from 'lucide-react';

export const AIWorkspacePage: React.FC = () => {
  const { activeTargetAddress, summary, transactions, counterparties, riskScore, riskLevel, alerts, evidenceItems, investigationId } = useInvestigationStore();

  const [chatLog, setChatLog] = useState<Array<{ sender: 'user' | 'ai'; text: string }>>([]);
  const [input, setInput] = useState('');
  const [isThinking, setIsThinking] = useState(false);
  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatLog]);

  // Initialize with investigation context
  useEffect(() => {
    if (summary && chatLog.length === 0) {
      setChatLog([{
        sender: 'ai',
        text: `**Co-Investigator Workspace Ready**\n\nActive Target: \`${activeTargetAddress.slice(0, 20)}…\`\nCase: ${investigationId}\nRisk: ${riskScore}/100 (${riskLevel.toUpperCase()})\nBalance: ${(summary.confirmedBalance / 1e8).toFixed(4)} BTC\nTransactions: ${summary.txCount.toLocaleString()}\nCounterparties: ${counterparties.length}\n\nAsk me anything about this investigation.`,
      }]);
    }
  }, [summary]);

  const generateAIResponse = (question: string): string => {
    const q = question.toLowerCase();

    if (q.includes('risk') || q.includes('threat')) {
      const critCount = alerts.filter(a => a.severity === 'critical').length;
      const highCount = alerts.filter(a => a.severity === 'high').length;
      return `**Risk Assessment for ${activeTargetAddress.slice(0, 16)}…**\n\n- Risk Score: **${riskScore}/100** (${riskLevel.toUpperCase()})\n- Critical Alerts: ${critCount}\n- High Alerts: ${highCount}\n- Total Alerts: ${alerts.length}\n\n${riskScore >= 50 ? '⚠️ This wallet shows elevated risk indicators. Review counterparty connections and large transfers.' : '✅ Risk level is within acceptable range.'}`;
    }

    if (q.includes('balance') || q.includes('fund') || q.includes('money')) {
      return `**Financial Summary**\n\n- Confirmed Balance: **${summary ? (summary.confirmedBalance / 1e8).toFixed(4) : '—'} BTC**\n- Total Received: ${summary ? (summary.totalReceived / 1e8).toFixed(4) : '—'} BTC\n- Total Sent: ${summary ? (summary.totalSent / 1e8).toFixed(4) : '—'} BTC\n- Net Flow: ${summary ? ((summary.totalReceived - summary.totalSent) / 1e8).toFixed(4) : '—'} BTC`;
    }

    if (q.includes('counterpart') || q.includes('connect') || q.includes('address')) {
      const top5 = counterparties.slice(0, 5);
      return `**Top Counterparties (${counterparties.length} total)**\n\n${top5.map((cp, i) => `${i + 1}. \`${cp.address.slice(0, 16)}…\` — ${cp.direction} — ${cp.txCount} txns — ${((cp.totalIn + cp.totalOut) / 1e8).toFixed(4)} BTC`).join('\n') || 'No counterparties detected.'}`;
    }

    if (q.includes('transaction') || q.includes('tx') || q.includes('activity')) {
      const recent = transactions.slice(0, 5);
      return `**Recent Transactions (${transactions.length} loaded)**\n\n${recent.map(tx => `- \`${tx.txid.slice(0, 16)}…\` | ${tx.status.confirmed ? 'Confirmed' : 'Pending'} | Fee: ${(tx.fee / 1e8).toFixed(6)} BTC`).join('\n') || 'No transactions available.'}`;
    }

    if (q.includes('evidence')) {
      return `**Evidence Summary (${evidenceItems.length} items)**\n\n${evidenceItems.slice(0, 5).map(ev => `- **${ev.title}** (${ev.severity}) — ${ev.description.slice(0, 80)}…`).join('\n') || 'No evidence items generated.'}`;
    }

    if (q.includes('summar') || q.includes('overview') || q.includes('report')) {
      return `**Investigation Overview — ${investigationId}**\n\n- Target: \`${activeTargetAddress}\`\n- Chain: ${summary?.chain || 'Bitcoin Mainnet'}\n- Script: ${summary?.scriptType || '—'}\n- Balance: ${summary ? (summary.confirmedBalance / 1e8).toFixed(4) : '—'} BTC\n- Txns: ${summary?.txCount?.toLocaleString() || '—'}\n- Risk: ${riskScore}/100 (${riskLevel.toUpperCase()})\n- Counterparties: ${counterparties.length}\n- Alerts: ${alerts.length}\n- Evidence: ${evidenceItems.length} items\n- First Seen: ${summary?.firstSeen ? new Date(summary.firstSeen).toLocaleDateString() : '—'}\n- Last Active: ${summary?.lastSeen ? new Date(summary.lastSeen).toLocaleDateString() : '—'}`;
    }

    return `I can help with analysis of **${activeTargetAddress.slice(0, 16)}…**\n\nTry asking about:\n- Risk assessment\n- Balance and funds\n- Counterparties\n- Recent transactions\n- Evidence items\n- Investigation summary`;
  };

  const handleSend = () => {
    if (!input.trim()) return;
    const userMsg = input.trim();
    setChatLog(prev => [...prev, { sender: 'user', text: userMsg }]);
    setInput('');
    setIsThinking(true);

    setTimeout(() => {
      const response = generateAIResponse(userMsg);
      setChatLog(prev => [...prev, { sender: 'ai', text: response }]);
      setIsThinking(false);
    }, 600);
  };

  return (
    <div className="flex gap-6 animate-fade-in h-[calc(100vh-140px)]">
      {/* Left: Context Panel */}
      <div className="w-72 shrink-0 space-y-4 overflow-y-auto">
        <div className="glass-card p-4 border border-primary-500/20">
          <div className="flex items-center gap-2 mb-3">
            <Sparkles size={14} className="text-primary-400" />
            <span className="text-xs font-bold text-white">Investigation Context</span>
          </div>
          <div className="space-y-2 text-xs">
            <div className="flex items-center gap-2">
              <Wallet size={12} className="text-primary-400" />
              <code className="text-dark-300 mono text-[10px]">{activeTargetAddress.slice(0, 18)}…</code>
            </div>
            <div className="flex justify-between">
              <span className="text-dark-400">Case</span>
              <span className="text-primary-400 font-bold">{investigationId}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-dark-400">Balance</span>
              <span className="text-white">{summary ? `${(summary.confirmedBalance / 1e8).toFixed(4)} BTC` : '—'}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-dark-400">Txns</span>
              <span className="text-white">{summary?.txCount?.toLocaleString() || '—'}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-dark-400">Risk</span>
              <span className={`font-bold ${riskLevel === 'critical' ? 'text-accent-red' : riskLevel === 'high' ? 'text-accent-gold' : 'text-accent-green'}`}>
                {riskScore}% ({riskLevel})
              </span>
            </div>
          </div>
        </div>

        {/* Quick Stats */}
        <div className="glass-card p-4">
          <span className="text-[10px] text-dark-400 uppercase font-semibold">Quick Metrics</span>
          <div className="mt-2 space-y-1.5">
            {[
              { icon: AlertTriangle, label: 'Alerts', value: alerts.length, color: 'text-accent-gold' },
              { icon: Globe, label: 'Counterparties', value: counterparties.length, color: 'text-primary-400' },
              { icon: Database, label: 'Evidence', value: evidenceItems.length, color: 'text-accent-green' },
              { icon: Shield, label: 'UTXOs', value: summary ? `${(summary.confirmedBalance / 1e8).toFixed(2)}` : '—', color: 'text-white' },
            ].map(m => (
              <div key={m.label} className="flex items-center justify-between text-xs">
                <div className="flex items-center gap-1.5">
                  <m.icon size={10} className={m.color} />
                  <span className="text-dark-400">{m.label}</span>
                </div>
                <span className="text-white font-bold">{m.value}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Suggested Prompts */}
        <div className="glass-card p-4">
          <span className="text-[10px] text-dark-400 uppercase font-semibold">Suggested Queries</span>
          <div className="mt-2 space-y-1">
            {[
              'What is the risk assessment?',
              'Show balance and funds',
              'List top counterparties',
              'Show recent transactions',
              'Give investigation summary',
            ].map(prompt => (
              <button
                key={prompt}
                onClick={() => { setInput(prompt); }}
                className="w-full text-left px-2 py-1.5 rounded text-[10px] text-dark-300 hover:text-primary-400 hover:bg-dark-800/50 transition-colors"
              >
                → {prompt}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Right: Chat Area */}
      <div className="flex-1 flex flex-col glass-card overflow-hidden">
        {/* Chat Header */}
        <div className="p-4 border-b border-dark-700/50 flex items-center gap-2">
          <Sparkles size={16} className="text-primary-400" />
          <span className="text-sm font-bold text-white">AI Co-Investigator</span>
          <span className="text-[10px] text-dark-500">• Connected to live investigation data</span>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {chatLog.map((msg, i) => (
            <div key={i} className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-[80%] p-3 rounded-xl text-xs leading-relaxed ${
                msg.sender === 'user'
                  ? 'bg-primary-500/20 text-white border border-primary-500/30 rounded-br-sm'
                  : 'bg-dark-800/50 text-dark-200 border border-dark-700/50 rounded-bl-sm'
              }`}>
                <div className="whitespace-pre-wrap">{msg.text}</div>
              </div>
            </div>
          ))}
          {isThinking && (
            <div className="flex justify-start">
              <div className="bg-dark-800/50 border border-dark-700/50 p-3 rounded-xl rounded-bl-sm">
                <div className="flex items-center gap-2 text-xs text-dark-400">
                  <div className="flex gap-1">
                    <div className="w-1.5 h-1.5 bg-primary-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                    <div className="w-1.5 h-1.5 bg-primary-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                    <div className="w-1.5 h-1.5 bg-primary-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                  </div>
                  Analyzing…
                </div>
              </div>
            </div>
          )}
          <div ref={chatEndRef} />
        </div>

        {/* Input */}
        <div className="p-4 border-t border-dark-700/50">
          <div className="flex gap-2">
            <input
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleSend()}
              placeholder="Ask about the active investigation..."
              className="flex-1 px-4 py-2.5 bg-dark-800/50 border border-dark-700 rounded-xl text-xs text-white placeholder:text-dark-500 focus:border-primary-500/50 focus:outline-none"
            />
            <button
              onClick={handleSend}
              disabled={!input.trim()}
              className="px-4 py-2.5 bg-primary-500/20 text-primary-400 rounded-xl border border-primary-500/30 hover:bg-primary-500/30 disabled:opacity-30 transition-all"
            >
              <Send size={14} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
