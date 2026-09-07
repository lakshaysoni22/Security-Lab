import React, { useState } from 'react';
import { useInvestigationStore } from '../stores/investigation';
import { Shield, AlertTriangle, CheckCircle2, Clock, Wallet, ArrowRight, ShieldAlert, Activity, FileText, Lock } from 'lucide-react';

export const IncidentResponsePage: React.FC = () => {
  const { activeTargetAddress, summary, riskScore, riskLevel, alerts, counterparties, evidenceItems, transactions, investigationId } = useInvestigationStore();
  const [completedSteps, setCompletedSteps] = useState<Set<string>>(new Set());

  const toggleStep = (id: string) => {
    setCompletedSteps(prev => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id); else next.add(id);
      return next;
    });
  };

  const criticalAlerts = alerts.filter(a => a.severity === 'critical');
  const highAlerts = alerts.filter(a => a.severity === 'high');
  const unconfirmedTxs = transactions.filter(tx => !tx.status.confirmed);
  const balanceBtc = summary ? (summary.confirmedBalance / 1e8).toFixed(4) : '—';

  // Generate dynamic incident response steps based on findings
  const responseSteps = [
    {
      id: 'identify',
      phase: 'IDENTIFICATION',
      title: 'Confirm Target Identity',
      description: `Verify ${activeTargetAddress.slice(0, 16)}… as the investigation target. Confirmed as ${summary?.scriptType || 'Unknown'} address on ${summary?.chain || 'Bitcoin Mainnet'}.`,
      status: summary ? 'actionable' : 'pending',
    },
    {
      id: 'assess',
      phase: 'ASSESSMENT',
      title: 'Risk Assessment Review',
      description: `Current risk score: ${riskScore}/100 (${riskLevel.toUpperCase()}). ${criticalAlerts.length} critical and ${highAlerts.length} high-severity alerts detected.`,
      status: riskScore > 50 ? 'critical' : riskScore > 25 ? 'warning' : 'normal',
    },
    {
      id: 'contain',
      phase: 'CONTAINMENT',
      title: 'Monitor Outgoing Transactions',
      description: unconfirmedTxs.length > 0
        ? `${unconfirmedTxs.length} unconfirmed transaction(s) in mempool. Monitor for fund movement to exchanges or mixers.`
        : 'No unconfirmed transactions detected. Current holdings are stable.',
      status: unconfirmedTxs.length > 0 ? 'warning' : 'normal',
    },
    {
      id: 'trace',
      phase: 'TRACING',
      title: 'Counterparty Mapping',
      description: `${counterparties.length} counterpart${counterparties.length !== 1 ? 'ies' : 'y'} identified. Map fund flow from target to connected addresses. Priority: addresses with highest volume.`,
      status: counterparties.length > 20 ? 'warning' : 'normal',
    },
    {
      id: 'evidence',
      phase: 'EVIDENCE',
      title: 'Preserve Digital Evidence',
      description: `${evidenceItems.length} evidence item${evidenceItems.length !== 1 ? 's' : ''} auto-generated from blockchain analysis. Seal and verify critical items for court admissibility.`,
      status: evidenceItems.length > 0 ? 'actionable' : 'pending',
    },
    {
      id: 'freeze',
      phase: 'FREEZE REQUEST',
      title: 'Coordinate Exchange Freeze',
      description: balanceBtc !== '—' && parseFloat(balanceBtc) > 1
        ? `Target holds ${balanceBtc} BTC. If funds move to identified exchanges, initiate freeze request through legal channels.`
        : 'Balance is minimal. Exchange freeze may not be required at this time.',
      status: parseFloat(balanceBtc || '0') > 10 ? 'critical' : 'normal',
    },
    {
      id: 'report',
      phase: 'REPORTING',
      title: 'Generate Investigation Report',
      description: 'Compile all findings into a formal investigation report. Include transaction timeline, counterparty analysis, and evidence chain.',
      status: 'actionable',
    },
  ];

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'critical': return 'border-accent-red/30 bg-accent-red/5';
      case 'warning': return 'border-accent-gold/30 bg-accent-gold/5';
      case 'actionable': return 'border-primary-500/30 bg-primary-500/5';
      case 'pending': return 'border-dark-700/50 bg-dark-800/30';
      default: return 'border-dark-700/50';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'critical': return <ShieldAlert size={16} className="text-accent-red" />;
      case 'warning': return <AlertTriangle size={16} className="text-accent-gold" />;
      case 'actionable': return <Activity size={16} className="text-primary-400" />;
      default: return <Clock size={16} className="text-dark-400" />;
    }
  };

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div>
        <div className="flex items-center gap-2">
          <Shield size={20} className="text-primary-400" />
          <h2 className="text-xl font-bold text-white">Incident Response</h2>
        </div>
        <div className="flex items-center gap-2 mt-1">
          <Wallet size={12} className="text-primary-400" />
          <span className="text-xs text-dark-400 mono">{activeTargetAddress.slice(0, 16)}…{activeTargetAddress.slice(-8)}</span>
          <span className="text-[10px] text-dark-500">•</span>
          <span className="text-xs text-dark-400">Case {investigationId}</span>
          <span className="text-[10px] text-dark-500">•</span>
          <span className={`text-xs font-bold ${riskLevel === 'critical' ? 'text-accent-red' : riskLevel === 'high' ? 'text-accent-gold' : 'text-accent-green'}`}>
            {riskLevel.toUpperCase()} RISK
          </span>
        </div>
      </div>

      {/* Threat Level Banner */}
      <div className={`glass-card p-4 border ${riskLevel === 'critical' ? 'border-accent-red/30 bg-accent-red/5' : riskLevel === 'high' ? 'border-accent-gold/30 bg-accent-gold/5' : 'border-primary-500/20 bg-primary-500/5'}`}>
        <div className="flex items-center justify-between">
          <div>
            <div className="text-[10px] uppercase font-bold text-dark-400 mb-1">Current Threat Assessment</div>
            <div className="flex items-center gap-3">
              <span className={`text-2xl font-bold ${riskLevel === 'critical' ? 'text-accent-red' : riskLevel === 'high' ? 'text-accent-gold' : 'text-accent-green'}`}>
                {riskScore}/100
              </span>
              <div>
                <div className="text-sm font-semibold text-white">{riskLevel.toUpperCase()} Threat Level</div>
                <div className="text-xs text-dark-400">{alerts.length} alerts • {counterparties.length} counterparties • {evidenceItems.length} evidence items</div>
              </div>
            </div>
          </div>
          <div className="text-right text-xs text-dark-400">
            <div>Balance: {balanceBtc} BTC</div>
            <div>Txns: {summary?.txCount?.toLocaleString() || '—'}</div>
          </div>
        </div>
      </div>

      {/* Progress */}
      <div className="flex items-center gap-2">
        <span className="text-xs text-dark-400">Response Progress:</span>
        <div className="flex-1 h-2 bg-dark-800 rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-primary-500 to-accent-green rounded-full transition-all"
            style={{ width: `${(completedSteps.size / responseSteps.length) * 100}%` }}
          />
        </div>
        <span className="text-xs text-dark-400">{completedSteps.size}/{responseSteps.length}</span>
      </div>

      {/* Response Steps */}
      <div className="space-y-3">
        {responseSteps.map((step, i) => (
          <div
            key={step.id}
            className={`glass-card p-4 border transition-all duration-200 ${
              completedSteps.has(step.id)
                ? 'border-accent-green/30 bg-accent-green/5 opacity-70'
                : getStatusColor(step.status)
            }`}
          >
            <div className="flex items-start gap-3">
              <button
                onClick={() => toggleStep(step.id)}
                className={`mt-0.5 w-5 h-5 rounded border flex items-center justify-center shrink-0 cursor-pointer transition-all ${
                  completedSteps.has(step.id)
                    ? 'bg-accent-green/20 border-accent-green/50 text-accent-green'
                    : 'border-dark-600 hover:border-primary-500/50'
                }`}
              >
                {completedSteps.has(step.id) && <CheckCircle2 size={12} />}
              </button>
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <span className="px-1.5 py-0.5 rounded text-[8px] font-bold bg-dark-800 border border-dark-700 text-dark-300">
                    STEP {i + 1} — {step.phase}
                  </span>
                  {!completedSteps.has(step.id) && getStatusIcon(step.status)}
                </div>
                <h4 className={`text-sm font-semibold mb-1 ${completedSteps.has(step.id) ? 'text-dark-400 line-through' : 'text-white'}`}>
                  {step.title}
                </h4>
                <p className="text-xs text-dark-400 leading-relaxed">{step.description}</p>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
