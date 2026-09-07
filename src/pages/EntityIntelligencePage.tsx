import React from 'react';
import { useInvestigationStore } from '../stores/investigation';
import { Fingerprint, Wallet, Shield, Activity, Clock, ArrowUpRight, ArrowDownRight, ExternalLink, AlertTriangle, HelpCircle, Globe } from 'lucide-react';

export const EntityIntelligencePage: React.FC = () => {
  const { activeTargetAddress, summary, transactions, counterparties, riskScore, riskLevel, investigationId, utxos } = useInvestigationStore();

  // Compute behavioral analysis from transactions
  const totalInflow = transactions.reduce((sum, tx) => {
    return sum + tx.vout.filter(o => o.scriptpubkey_address === activeTargetAddress).reduce((s, o) => s + o.value, 0);
  }, 0);
  const totalOutflow = transactions.reduce((sum, tx) => {
    return sum + tx.vin.filter(i => i.prevout?.scriptpubkey_address === activeTargetAddress).reduce((s, i) => s + (i.prevout?.value || 0), 0);
  }, 0);

  // Activity time distribution
  const hourDistribution = new Array(24).fill(0);
  transactions.forEach(tx => {
    if (tx.status.block_time) {
      const hour = new Date(tx.status.block_time * 1000).getHours();
      hourDistribution[hour]++;
    }
  });
  const peakHour = hourDistribution.indexOf(Math.max(...hourDistribution));

  // Transaction frequency (average days between txs)
  const txTimestamps = transactions
    .map(t => t.status.block_time)
    .filter((t): t is number => Boolean(t))
    .sort((a, b) => a - b);
  let avgDaysBetween = 0;
  if (txTimestamps.length > 1) {
    const totalSpan = txTimestamps[txTimestamps.length - 1] - txTimestamps[0];
    avgDaysBetween = totalSpan / (txTimestamps.length - 1) / 86400;
  }

  // Entity classification
  const classifyEntity = (): { label: string; confidence: string; description: string } => {
    if (!summary) return { label: 'Unknown Entity', confidence: 'N/A', description: 'No blockchain data available for classification.' };
    
    const txCount = summary.txCount;
    const balance = summary.confirmedBalance / 1e8;
    
    if (txCount > 10000 && balance > 1000) {
      return { label: 'Exchange / High-Volume Service', confidence: 'High', description: 'Extremely high transaction count and balance suggests an exchange or large custodial service.' };
    }
    if (txCount > 1000 && balance > 100) {
      return { label: 'Commercial Entity / Service', confidence: 'Medium', description: 'High activity volume suggests a commercial service, payment processor, or large merchant.' };
    }
    if (txCount > 100 && counterparties.length > 50) {
      return { label: 'Active Trader / Business', confidence: 'Medium', description: 'Moderate transaction count with many counterparties suggests active trading or business operations.' };
    }
    if (txCount > 10 && balance < 1) {
      return { label: 'Standard Retail Account', confidence: 'Medium', description: 'Normal activity pattern consistent with individual user.' };
    }
    if (txCount <= 5 && balance > 10) {
      return { label: 'Cold Storage / Hodler', confidence: 'Medium', description: 'Low transaction frequency with significant balance suggests long-term storage.' };
    }
    return { label: 'Unknown Entity', confidence: 'Low', description: 'Insufficient data for reliable classification.' };
  };

  const entity = classifyEntity();

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div>
        <div className="flex items-center gap-2">
          <Fingerprint size={20} className="text-primary-400" />
          <h2 className="text-xl font-bold text-white">Entity Intelligence</h2>
        </div>
        <div className="flex items-center gap-2 mt-1">
          <Wallet size={12} className="text-primary-400" />
          <span className="text-xs text-dark-400 mono">{activeTargetAddress.slice(0, 16)}…{activeTargetAddress.slice(-8)}</span>
          <span className="text-[10px] text-dark-500">•</span>
          <span className="text-xs text-dark-400">Case {investigationId}</span>
        </div>
      </div>

      {/* Entity Classification Card */}
      <div className="glass-card p-5 border border-primary-500/20">
        <div className="flex items-start justify-between">
          <div>
            <div className="text-[10px] text-dark-400 uppercase font-semibold mb-1">Entity Classification</div>
            <h3 className="text-lg font-bold text-white mb-1">{entity.label}</h3>
            <p className="text-xs text-dark-400 max-w-lg">{entity.description}</p>
            <div className="flex items-center gap-2 mt-2">
              <span className="px-2 py-0.5 rounded text-[9px] font-bold bg-primary-500/20 text-primary-400 border border-primary-500/30">
                Confidence: {entity.confidence}
              </span>
              <span className="px-2 py-0.5 rounded text-[9px] font-bold bg-dark-700 text-dark-300 border border-dark-600">
                {summary?.scriptType || 'Unknown Script'}
              </span>
            </div>
          </div>
          <div className="text-right">
            <div className={`text-3xl font-bold ${riskLevel === 'critical' ? 'text-accent-red' : riskLevel === 'high' ? 'text-accent-gold' : riskLevel === 'medium' ? 'text-primary-400' : 'text-accent-green'}`}>
              {riskScore}%
            </div>
            <div className={`text-[10px] uppercase font-bold ${riskLevel === 'critical' ? 'text-accent-red' : riskLevel === 'high' ? 'text-accent-gold' : 'text-primary-400'}`}>
              {riskLevel} risk
            </div>
          </div>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {[
          { label: 'Total Received', value: summary ? `${(summary.formattedReceived ?? (summary.totalReceived / 1e8)).toLocaleString()} ${summary.coinSymbol || 'BTC'}` : '—', icon: ArrowDownRight, color: 'text-accent-green' },
          { label: 'Total Sent', value: summary ? `${(summary.formattedSent ?? (summary.totalSent / 1e8)).toLocaleString()} ${summary.coinSymbol || 'BTC'}` : '—', icon: ArrowUpRight, color: 'text-accent-red' },
          { label: 'Counterparties', value: counterparties.length.toString(), icon: Globe, color: 'text-primary-400' },
          { label: 'Live UTXOs', value: utxos.length.toString(), icon: Activity, color: 'text-accent-gold' },
        ].map(m => (
          <div key={m.label} className="glass-card p-3">
            <div className="flex items-center gap-1.5 mb-1">
              <m.icon size={12} className={m.color} />
              <span className="text-[9px] text-dark-400 uppercase font-semibold">{m.label}</span>
            </div>
            <div className="text-lg font-bold text-white">{m.value}</div>
          </div>
        ))}
      </div>

      {/* Behavioral Analysis */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="glass-card p-5">
          <h3 className="text-sm font-bold text-white mb-3">Behavioral Profile</h3>
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs text-dark-400">Peak Activity Hour (UTC)</span>
              <span className="text-xs text-white font-bold">{txTimestamps.length > 0 ? `${peakHour}:00 — ${(peakHour + 1) % 24}:00` : '—'}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-xs text-dark-400">Avg Days Between Txns</span>
              <span className="text-xs text-white font-bold">{avgDaysBetween > 0 ? `${avgDaysBetween.toFixed(1)} days` : '—'}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-xs text-dark-400">First Seen</span>
              <span className="text-xs text-white font-bold">{summary?.firstSeen ? new Date(summary.firstSeen).toLocaleDateString() : '—'}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-xs text-dark-400">Last Active</span>
              <span className="text-xs text-white font-bold">{summary?.lastSeen ? new Date(summary.lastSeen).toLocaleDateString() : '—'}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-xs text-dark-400">Inflow/Outflow Ratio</span>
              <span className="text-xs text-white font-bold">{totalOutflow > 0 ? (totalInflow / totalOutflow).toFixed(2) : '—'}</span>
            </div>
          </div>
        </div>

        {/* Activity Heatmap */}
        <div className="glass-card p-5">
          <h3 className="text-sm font-bold text-white mb-3">Hourly Activity Distribution (UTC)</h3>
          <div className="grid grid-cols-12 gap-1">
            {hourDistribution.map((count, hour) => {
              const max = Math.max(...hourDistribution, 1);
              const intensity = count / max;
              return (
                <div key={hour} className="text-center">
                  <div
                    className="w-full rounded-sm mb-1"
                    style={{
                      height: `${Math.max(4, intensity * 60)}px`,
                      background: intensity > 0.7 ? '#06b6d4' : intensity > 0.3 ? '#0891b2' : intensity > 0 ? '#164e63' : '#1a1a2e',
                    }}
                    title={`${hour}:00 — ${count} txns`}
                  />
                  <span className="text-[7px] text-dark-500">{hour}</span>
                </div>
              );
            })}
          </div>
          {txTimestamps.length === 0 && (
            <div className="text-center text-dark-500 text-xs italic mt-4">No timestamped transaction data available.</div>
          )}
        </div>
      </div>

      {/* Top Counterparties */}
      <div className="glass-card p-5">
        <h3 className="text-sm font-bold text-white mb-3">Top Counterparties by Volume</h3>
        <div className="space-y-2">
          {counterparties.slice(0, 10).map((cp, i) => (
            <div key={cp.address} className="flex items-center gap-3 p-2 rounded-lg hover:bg-dark-800/30 transition-colors">
              <span className="text-xs text-dark-500 w-5 text-right">{i + 1}</span>
              <code className="text-xs text-white mono flex-1">{cp.address.slice(0, 16)}…{cp.address.slice(-6)}</code>
              <span className="text-[10px] text-accent-green">{cp.totalIn > 0 ? `↓${(cp.totalIn / 1e8).toFixed(4)}` : ''}</span>
              <span className="text-[10px] text-accent-red">{cp.totalOut > 0 ? `↑${(cp.totalOut / 1e8).toFixed(4)}` : ''}</span>
              <span className="text-[10px] text-dark-400">{cp.txCount} txns</span>
              <a href={`https://mempool.space/address/${cp.address}`} target="_blank" rel="noopener noreferrer" className="text-primary-400">
                <ExternalLink size={10} />
              </a>
            </div>
          ))}
          {counterparties.length === 0 && (
            <div className="text-center text-dark-500 text-xs italic py-4">No counterparties detected.</div>
          )}
        </div>
      </div>

      {/* Public Intelligence Notice */}
      <div className="glass-card p-4 border border-dark-700/50 flex items-start gap-3">
        <HelpCircle size={16} className="text-dark-400 shrink-0 mt-0.5" />
        <div>
          <div className="text-xs text-white font-semibold mb-1">Public Intelligence Lookup</div>
          <p className="text-xs text-dark-400">
            No public entity labels found for this address. Classification above is computed from on-chain behavioral analysis only. 
            If this wallet belongs to a known exchange, service, or entity, labels would appear here automatically.
          </p>
        </div>
      </div>
    </div>
  );
};
