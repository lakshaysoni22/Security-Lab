import React, { useState } from 'react';
import { useNavStore } from '../stores';
import { useInvestigationStore } from '../stores/investigation';
import { FolderOpen, Wallet, Shield, Clock, AlertTriangle, CheckCircle2, Activity, FileText, Sparkles, ArrowRight } from 'lucide-react';

const timeAgo = (iso: string) => {
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'just now';
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
};

export const CasesPage: React.FC = () => {
  const { setPage } = useNavStore();
  const { activeTargetAddress, summary, transactions, counterparties, riskScore, riskLevel, investigationId, investigationStartedAt, alerts, evidenceItems, auditLog, addAuditEntry } = useInvestigationStore();

  const [notes, setNotes] = useState<Array<{ id: string; text: string; timestamp: string }>>([]);
  const [newNote, setNewNote] = useState('');
  const [activeTab, setActiveTab] = useState<'summary' | 'timeline' | 'notes' | 'evidence' | 'alerts'>('summary');

  const handleAddNote = () => {
    if (!newNote.trim()) return;
    setNotes(prev => [{ id: `note-${Date.now()}`, text: newNote, timestamp: new Date().toISOString() }, ...prev]);
    addAuditEntry('NOTE_ADDED', `Investigation note added for case ${investigationId}`);
    setNewNote('');
  };

  const balanceBtc = summary ? (summary.confirmedBalance / 1e8).toFixed(4) : '—';
  const txCount = summary?.txCount?.toLocaleString() || '—';

  // Case pipeline stages
  const stages = [
    { id: 1, name: 'Target Identified', done: !!activeTargetAddress },
    { id: 2, name: 'Blockchain Analysis', done: !!summary },
    { id: 3, name: 'Risk Assessment', done: riskScore > 0 },
    { id: 4, name: 'Evidence Collection', done: evidenceItems.length > 0 },
    { id: 5, name: 'Counterparty Mapping', done: counterparties.length > 0 },
    { id: 6, name: 'Report Generation', done: false },
    { id: 7, name: 'Case Closure', done: false },
  ];
  const currentStage = stages.filter(s => s.done).length + 1;

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <FolderOpen size={20} className="text-primary-400" />
            <h2 className="text-xl font-bold text-white">Case Management</h2>
          </div>
          <div className="flex items-center gap-2 mt-1">
            <Wallet size={12} className="text-primary-400" />
            <span className="text-xs text-dark-400 mono">{activeTargetAddress.slice(0, 16)}…{activeTargetAddress.slice(-8)}</span>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span className={`px-2.5 py-1 rounded text-[10px] font-bold border ${
            riskLevel === 'critical' ? 'bg-accent-red/20 text-accent-red border-accent-red/30' :
            riskLevel === 'high' ? 'bg-accent-gold/20 text-accent-gold border-accent-gold/30' :
            'bg-primary-500/20 text-primary-400 border-primary-500/30'
          }`}>
            {riskLevel.toUpperCase()} PRIORITY
          </span>
          <span className="px-2.5 py-1 rounded text-[10px] font-bold bg-accent-green/20 text-accent-green border border-accent-green/30">
            ACTIVE
          </span>
        </div>
      </div>

      {/* Case Info Card */}
      <div className="glass-card p-5 border border-primary-500/20">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <span className="text-[10px] text-dark-400 uppercase">Case ID</span>
            <div className="text-sm font-bold text-primary-400 mono mt-0.5">{investigationId}</div>
          </div>
          <div>
            <span className="text-[10px] text-dark-400 uppercase">Started</span>
            <div className="text-sm font-bold text-white mt-0.5">{new Date(investigationStartedAt).toLocaleDateString()}</div>
          </div>
          <div>
            <span className="text-[10px] text-dark-400 uppercase">Balance</span>
            <div className="text-sm font-bold text-white mt-0.5">{balanceBtc} BTC</div>
          </div>
          <div>
            <span className="text-[10px] text-dark-400 uppercase">Risk Score</span>
            <div className={`text-sm font-bold mt-0.5 ${riskLevel === 'critical' ? 'text-accent-red' : riskLevel === 'high' ? 'text-accent-gold' : 'text-accent-green'}`}>
              {riskScore}/100
            </div>
          </div>
        </div>
      </div>

      {/* Pipeline */}
      <div className="glass-card p-4">
        <div className="text-[10px] text-dark-400 uppercase font-semibold mb-3">Investigation Pipeline</div>
        <div className="flex items-center gap-1 overflow-x-auto">
          {stages.map((stage, i) => (
            <React.Fragment key={stage.id}>
              <div className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-[10px] font-bold whitespace-nowrap ${
                stage.done
                  ? 'bg-accent-green/20 text-accent-green border border-accent-green/30'
                  : stage.id === currentStage
                    ? 'bg-primary-500/20 text-primary-400 border border-primary-500/30 animate-pulse'
                    : 'bg-dark-800 text-dark-500 border border-dark-700'
              }`}>
                {stage.done ? <CheckCircle2 size={10} /> : <span className="w-3 text-center">{stage.id}</span>}
                {stage.name}
              </div>
              {i < stages.length - 1 && <ArrowRight size={12} className="text-dark-600 shrink-0" />}
            </React.Fragment>
          ))}
        </div>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-1 border-b border-dark-700/50 pb-1">
        {(['summary', 'timeline', 'notes', 'evidence', 'alerts'] as const).map(tab => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-3 py-1.5 rounded-t text-xs font-bold capitalize transition-all ${
              activeTab === tab
                ? 'bg-primary-500/20 text-primary-400 border-b-2 border-primary-400'
                : 'text-dark-400 hover:text-white'
            }`}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      {activeTab === 'summary' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="glass-card p-4">
            <h3 className="text-sm font-bold text-white mb-3">Investigation Summary</h3>
            <div className="space-y-2 text-xs">
              <div className="flex justify-between"><span className="text-dark-400">Target Address</span><code className="text-white mono">{activeTargetAddress.slice(0, 20)}…</code></div>
              <div className="flex justify-between"><span className="text-dark-400">Script Type</span><span className="text-white">{summary?.scriptType || '—'}</span></div>
              <div className="flex justify-between"><span className="text-dark-400">Chain</span><span className="text-white">{summary?.chain || '—'}</span></div>
              <div className="flex justify-between"><span className="text-dark-400">Total Transactions</span><span className="text-white">{txCount}</span></div>
              <div className="flex justify-between"><span className="text-dark-400">Counterparties</span><span className="text-white">{counterparties.length}</span></div>
              <div className="flex justify-between"><span className="text-dark-400">First Seen</span><span className="text-white">{summary?.firstSeen ? new Date(summary.firstSeen).toLocaleDateString() : '—'}</span></div>
              <div className="flex justify-between"><span className="text-dark-400">Last Active</span><span className="text-white">{summary?.lastSeen ? new Date(summary.lastSeen).toLocaleDateString() : '—'}</span></div>
            </div>
          </div>
          <div className="glass-card p-4">
            <h3 className="text-sm font-bold text-white mb-3">Financial Overview</h3>
            <div className="space-y-2 text-xs">
              <div className="flex justify-between"><span className="text-dark-400">Confirmed Balance</span><span className="text-white font-bold">{balanceBtc} BTC</span></div>
              <div className="flex justify-between"><span className="text-dark-400">Total Received</span><span className="text-accent-green">{summary ? (summary.totalReceived / 1e8).toFixed(4) : '—'} BTC</span></div>
              <div className="flex justify-between"><span className="text-dark-400">Total Sent</span><span className="text-accent-red">{summary ? (summary.totalSent / 1e8).toFixed(4) : '—'} BTC</span></div>
              <div className="flex justify-between"><span className="text-dark-400">Alerts</span><span className="text-accent-gold">{alerts.length}</span></div>
              <div className="flex justify-between"><span className="text-dark-400">Evidence Items</span><span className="text-primary-400">{evidenceItems.length}</span></div>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'timeline' && (
        <div className="glass-card p-4">
          <h3 className="text-sm font-bold text-white mb-3">Investigation Timeline</h3>
          <div className="space-y-2">
            {auditLog.slice(0, 20).map(entry => (
              <div key={entry.id} className="flex items-start gap-3 p-2 rounded-lg hover:bg-dark-800/30">
                <div className="w-2 h-2 rounded-full bg-primary-400 mt-1.5 shrink-0" />
                <div>
                  <div className="text-xs text-white">{entry.detail}</div>
                  <div className="text-[10px] text-dark-500">{timeAgo(entry.timestamp)} • {entry.action}</div>
                </div>
              </div>
            ))}
            {auditLog.length === 0 && <div className="text-center text-dark-500 text-sm italic py-6">No timeline events yet.</div>}
          </div>
        </div>
      )}

      {activeTab === 'notes' && (
        <div className="glass-card p-4">
          <h3 className="text-sm font-bold text-white mb-3">Investigation Notes</h3>
          <div className="flex gap-2 mb-4">
            <input
              value={newNote}
              onChange={e => setNewNote(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleAddNote()}
              placeholder="Add investigation note..."
              className="flex-1 px-3 py-2 bg-dark-800/50 border border-dark-700 rounded-lg text-xs text-white placeholder:text-dark-500 focus:border-primary-500/50 focus:outline-none"
            />
            <button onClick={handleAddNote} className="px-4 py-2 bg-primary-500/20 text-primary-400 text-xs font-bold rounded-lg border border-primary-500/30 hover:bg-primary-500/30">
              Add
            </button>
          </div>
          <div className="space-y-2">
            {notes.map(note => (
              <div key={note.id} className="p-3 rounded-lg bg-dark-800/30 border border-dark-700/50">
                <div className="text-xs text-white">{note.text}</div>
                <div className="text-[10px] text-dark-500 mt-1">{timeAgo(note.timestamp)}</div>
              </div>
            ))}
            {notes.length === 0 && <div className="text-center text-dark-500 text-sm italic py-4">No notes yet.</div>}
          </div>
        </div>
      )}

      {activeTab === 'evidence' && (
        <div className="glass-card p-4">
          <h3 className="text-sm font-bold text-white mb-3">Case Evidence ({evidenceItems.length} items)</h3>
          <div className="space-y-2">
            {evidenceItems.map(ev => (
              <div key={ev.id} className="flex items-center justify-between p-2 rounded-lg hover:bg-dark-800/30">
                <div className="flex items-center gap-2">
                  <FileText size={14} className="text-primary-400" />
                  <div>
                    <div className="text-xs text-white">{ev.title}</div>
                    <div className="text-[10px] text-dark-500">{ev.type.replace(/_/g, ' ')} • {ev.severity}</div>
                  </div>
                </div>
                {'value' in ev && ev.value && <span className="text-xs text-white font-mono">{(ev.value / 1e8).toFixed(4)} BTC</span>}
              </div>
            ))}
            {evidenceItems.length === 0 && <div className="text-center text-dark-500 text-sm italic py-4">No evidence items.</div>}
          </div>
        </div>
      )}

      {activeTab === 'alerts' && (
        <div className="glass-card p-4">
          <h3 className="text-sm font-bold text-white mb-3">Case Alerts ({alerts.length})</h3>
          <div className="space-y-2">
            {alerts.map(alert => (
              <div key={alert.id} className="flex items-center gap-2 p-2 rounded-lg hover:bg-dark-800/30">
                {alert.severity === 'critical' ? <AlertTriangle size={14} className="text-accent-red" /> :
                 alert.severity === 'high' ? <AlertTriangle size={14} className="text-accent-gold" /> :
                 <Activity size={14} className="text-primary-400" />}
                <div className="flex-1">
                  <div className="text-xs text-white">{alert.message}</div>
                  <div className="text-[10px] text-dark-500">{alert.severity} • {alert.type.replace(/_/g, ' ')}</div>
                </div>
              </div>
            ))}
            {alerts.length === 0 && <div className="text-center text-dark-500 text-sm italic py-4">No alerts.</div>}
          </div>
        </div>
      )}
    </div>
  );
};
