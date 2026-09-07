import React, { useState } from 'react';
import { useInvestigationStore } from '../stores/investigation';
import { Shield, ShieldCheck, Upload, FileText, CheckCircle2, AlertTriangle, Key, Lock, Eye, Wallet, ExternalLink, Clock } from 'lucide-react';

const timeAgo = (iso: string) => {
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'just now';
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
};

export const EvidencePage: React.FC = () => {
  const { activeTargetAddress, summary, transactions, utxos, evidenceItems, investigationId, addAuditEntry } = useInvestigationStore();

  const [selectedEvidence, setSelectedEvidence] = useState<string | null>(null);
  const [verifiedItems, setVerifiedItems] = useState<Set<string>>(new Set());
  const [sealedItems, setSealedItems] = useState<Set<string>>(new Set());

  // Upload state
  const [showUpload, setShowUpload] = useState(false);
  const [uploadName, setUploadName] = useState('');
  const [uploadDesc, setUploadDesc] = useState('');
  const [customEvidence, setCustomEvidence] = useState<Array<{ id: string; title: string; description: string; timestamp: string }>>([]);

  const handleVerify = (id: string) => {
    setVerifiedItems(prev => new Set(prev).add(id));
    addAuditEntry('EVIDENCE_VERIFIED', `Evidence item ${id} verified by investigator`);
  };

  const handleSeal = (id: string) => {
    setSealedItems(prev => new Set(prev).add(id));
    addAuditEntry('EVIDENCE_SEALED', `Evidence item ${id} sealed for court admissibility`);
  };

  const handleUpload = (e: React.FormEvent) => {
    e.preventDefault();
    if (!uploadName.trim()) return;
    const newItem = {
      id: `ev-custom-${Date.now()}`,
      title: uploadName,
      description: uploadDesc || 'Manually uploaded evidence',
      timestamp: new Date().toISOString(),
    };
    setCustomEvidence(prev => [newItem, ...prev]);
    addAuditEntry('EVIDENCE_ADDED', `Evidence "${uploadName}" uploaded for investigation ${investigationId}`);
    setUploadName('');
    setUploadDesc('');
    setShowUpload(false);
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'bg-accent-red/20 text-accent-red border-accent-red/30';
      case 'high': return 'bg-accent-gold/20 text-accent-gold border-accent-gold/30';
      case 'medium': return 'bg-primary-500/20 text-primary-400 border-primary-500/30';
      default: return 'bg-accent-green/20 text-accent-green border-accent-green/30';
    }
  };

  const allEvidence = [
    ...customEvidence.map(ce => ({
      id: ce.id,
      type: 'pattern' as const,
      title: ce.title,
      description: ce.description,
      severity: 'medium' as const,
      timestamp: ce.timestamp,
      walletAddress: activeTargetAddress,
    })),
    ...evidenceItems,
  ];

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <Shield size={20} className="text-primary-400" />
            <h2 className="text-xl font-bold text-white">Evidence Vault</h2>
          </div>
          <div className="flex items-center gap-2 mt-1">
            <Wallet size={12} className="text-primary-400" />
            <span className="text-xs text-dark-400 mono">{activeTargetAddress.slice(0, 16)}…{activeTargetAddress.slice(-8)}</span>
            <span className="text-[10px] text-dark-500">•</span>
            <span className="text-xs text-dark-400">Case {investigationId}</span>
            <span className="text-[10px] text-dark-500">•</span>
            <span className="text-xs text-dark-400">{allEvidence.length} items</span>
          </div>
        </div>
        <button
          onClick={() => setShowUpload(true)}
          className="btn-ghost flex items-center gap-1 text-xs border border-primary-500/30 text-primary-400 hover:bg-primary-500/10"
        >
          <Upload size={14} /> Upload Evidence
        </button>
      </div>

      {/* Stats Bar */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {[
          { label: 'Total Evidence', value: allEvidence.length, icon: FileText, color: 'text-primary-400' },
          { label: 'Verified', value: verifiedItems.size, icon: CheckCircle2, color: 'text-accent-green' },
          { label: 'Sealed', value: sealedItems.size, icon: Lock, color: 'text-accent-gold' },
          { label: 'Critical Findings', value: evidenceItems.filter(e => e.severity === 'critical').length, icon: AlertTriangle, color: 'text-accent-red' },
        ].map(stat => (
          <div key={stat.label} className="glass-card p-3">
            <div className="flex items-center gap-2 mb-1">
              <stat.icon size={14} className={stat.color} />
              <span className="text-[10px] text-dark-400 uppercase">{stat.label}</span>
            </div>
            <div className="text-xl font-bold text-white">{stat.value}</div>
          </div>
        ))}
      </div>

      {/* Upload Modal */}
      {showUpload && (
        <div className="glass-card p-5 border border-primary-500/20">
          <h3 className="text-sm font-bold text-white mb-3">Upload Evidence to Investigation {investigationId}</h3>
          <form onSubmit={handleUpload} className="space-y-3">
            <input
              type="text"
              value={uploadName}
              onChange={e => setUploadName(e.target.value)}
              placeholder="Evidence title..."
              className="w-full px-3 py-2 bg-dark-800/50 border border-dark-700 rounded-lg text-xs text-white placeholder:text-dark-500 focus:border-primary-500/50 focus:outline-none"
            />
            <textarea
              value={uploadDesc}
              onChange={e => setUploadDesc(e.target.value)}
              placeholder="Description..."
              rows={2}
              className="w-full px-3 py-2 bg-dark-800/50 border border-dark-700 rounded-lg text-xs text-white placeholder:text-dark-500 focus:border-primary-500/50 focus:outline-none resize-none"
            />
            <div className="flex gap-2">
              <button type="submit" className="px-4 py-1.5 rounded-lg bg-primary-500/20 text-primary-400 text-xs font-bold border border-primary-500/30 hover:bg-primary-500/30">
                Upload
              </button>
              <button type="button" onClick={() => setShowUpload(false)} className="px-4 py-1.5 rounded-lg bg-dark-800 text-dark-400 text-xs border border-dark-700 hover:border-dark-600">
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Evidence List */}
      <div className="space-y-3">
        {allEvidence.map(item => (
          <div
            key={item.id}
            className={`glass-card p-4 border transition-all duration-200 cursor-pointer ${
              selectedEvidence === item.id ? 'border-primary-500/40 bg-primary-500/5' : 'border-dark-700/50 hover:border-dark-600'
            }`}
            onClick={() => setSelectedEvidence(selectedEvidence === item.id ? null : item.id)}
          >
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-2 flex-wrap">
                  <span className={`px-1.5 py-0.5 rounded text-[8px] font-bold uppercase border ${getSeverityColor(item.severity)}`}>
                    {item.severity}
                  </span>
                  <span className="px-1.5 py-0.5 rounded text-[8px] font-bold bg-dark-800 border border-dark-700 text-dark-300">
                    {item.type.replace(/_/g, ' ')}
                  </span>
                  {verifiedItems.has(item.id) && (
                    <span className="px-1.5 py-0.5 rounded text-[8px] font-bold bg-accent-green/20 text-accent-green border border-accent-green/30 flex items-center gap-1">
                      <CheckCircle2 size={8} /> VERIFIED
                    </span>
                  )}
                  {sealedItems.has(item.id) && (
                    <span className="px-1.5 py-0.5 rounded text-[8px] font-bold bg-accent-gold/20 text-accent-gold border border-accent-gold/30 flex items-center gap-1">
                      <Lock size={8} /> SEALED
                    </span>
                  )}
                  <span className="text-[10px] text-dark-500">{timeAgo(item.timestamp)}</span>
                </div>
                <h4 className="text-sm font-semibold text-white mb-1">{item.title}</h4>
                <p className="text-xs text-dark-400 leading-relaxed">{item.description}</p>
                {'txid' in item && item.txid && (
                  <div className="mt-2 flex items-center gap-2">
                    <code className="text-[10px] text-dark-500 mono">{item.txid.slice(0, 24)}…</code>
                    <a
                      href={`https://mempool.space/tx/${item.txid}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-[10px] text-primary-400 hover:underline flex items-center gap-1"
                      onClick={e => e.stopPropagation()}
                    >
                      View on Mempool <ExternalLink size={8} />
                    </a>
                  </div>
                )}
              </div>
              {'value' in item && item.value && (
                <div className="text-right shrink-0">
                  <div className="text-sm font-bold text-white">{((item.value as number) / 1e8).toFixed(4)} BTC</div>
                </div>
              )}
            </div>

            {/* Expanded actions */}
            {selectedEvidence === item.id && (
              <div className="mt-3 pt-3 border-t border-dark-700/50 flex items-center gap-2">
                {!verifiedItems.has(item.id) && (
                  <button
                    onClick={e => { e.stopPropagation(); handleVerify(item.id); }}
                    className="px-3 py-1 rounded text-[10px] font-bold bg-accent-green/10 text-accent-green border border-accent-green/30 hover:bg-accent-green/20 flex items-center gap-1"
                  >
                    <ShieldCheck size={10} /> Verify Integrity
                  </button>
                )}
                {!sealedItems.has(item.id) && (
                  <button
                    onClick={e => { e.stopPropagation(); handleSeal(item.id); }}
                    className="px-3 py-1 rounded text-[10px] font-bold bg-accent-gold/10 text-accent-gold border border-accent-gold/30 hover:bg-accent-gold/20 flex items-center gap-1"
                  >
                    <Key size={10} /> Seal for Court
                  </button>
                )}
                {'txid' in item && item.txid && (
                  <a
                    href={`https://mempool.space/tx/${item.txid}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="px-3 py-1 rounded text-[10px] font-bold bg-dark-800 text-dark-300 border border-dark-700 hover:border-dark-600 flex items-center gap-1"
                    onClick={e => e.stopPropagation()}
                  >
                    <Eye size={10} /> View Transaction
                  </a>
                )}
              </div>
            )}
          </div>
        ))}

        {allEvidence.length === 0 && (
          <div className="glass-card p-12 text-center text-dark-500 italic">
            No evidence items available. Analyze a wallet address to auto-generate evidence from blockchain data.
          </div>
        )}
      </div>
    </div>
  );
};
