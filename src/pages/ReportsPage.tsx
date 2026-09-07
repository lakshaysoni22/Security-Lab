import React, { useState } from 'react';
import { useInvestigationStore } from '../stores/investigation';
import { FileText, Download, Wallet, Shield, Activity, Clock, Printer, Copy, CheckCircle2 } from 'lucide-react';

export const ReportsPage: React.FC = () => {
  const { activeTargetAddress, summary, transactions, utxos, counterparties, riskScore, riskLevel, investigationId, evidenceItems, alerts, addAuditEntry } = useInvestigationStore();
  const [generatedReports, setGeneratedReports] = useState<Array<{ id: string; title: string; generatedAt: string; type: string }>>([]);
  const [activeReport, setActiveReport] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  const handleGenerateReport = (type: string, title: string) => {
    const report = {
      id: `rpt-${Date.now()}`,
      title,
      generatedAt: new Date().toISOString(),
      type,
    };
    setGeneratedReports(prev => [report, ...prev]);
    setActiveReport(report.id);
    addAuditEntry('REPORT_GENERATED', `Report "${title}" generated for ${activeTargetAddress.slice(0, 16)}…`);
  };

  const balanceBtc = summary ? (summary.confirmedBalance / 1e8).toFixed(4) : '—';
  const totalReceivedBtc = summary ? (summary.totalReceived / 1e8).toFixed(4) : '—';
  const totalSentBtc = summary ? (summary.totalSent / 1e8).toFixed(4) : '—';

  const fullReportText = `
═══════════════════════════════════════════════════════
BLOCKCHAIN INVESTIGATION REPORT
═══════════════════════════════════════════════════════
Investigation ID: ${investigationId}
Target Address:   ${activeTargetAddress}
Generated:        ${new Date().toISOString()}
Chain:            ${summary?.chain || 'Bitcoin Mainnet'}
Script Type:      ${summary?.scriptType || '—'}

═══════════════════════════════════════════════════════
FINANCIAL SUMMARY
═══════════════════════════════════════════════════════
Confirmed Balance:    ${balanceBtc} BTC
Total Received:       ${totalReceivedBtc} BTC
Total Sent:           ${totalSentBtc} BTC
Transaction Count:    ${summary?.txCount?.toLocaleString() || '—'}
Live UTXOs:           ${utxos.length}
Counterparties:       ${counterparties.length}

═══════════════════════════════════════════════════════
RISK ASSESSMENT
═══════════════════════════════════════════════════════
Risk Score:           ${riskScore}/100
Risk Level:           ${riskLevel.toUpperCase()}
Alerts Generated:     ${alerts.length}
Critical Alerts:      ${alerts.filter(a => a.severity === 'critical').length}
Evidence Items:       ${evidenceItems.length}

═══════════════════════════════════════════════════════
ACTIVITY TIMELINE
═══════════════════════════════════════════════════════
First Seen:           ${summary?.firstSeen ? new Date(summary.firstSeen).toLocaleDateString() : '—'}
Last Active:          ${summary?.lastSeen ? new Date(summary.lastSeen).toLocaleDateString() : '—'}

═══════════════════════════════════════════════════════
TOP COUNTERPARTIES
═══════════════════════════════════════════════════════
${counterparties.slice(0, 10).map((cp, i) => `${i + 1}. ${cp.address} (${cp.direction}, ${cp.txCount} txns, ${((cp.totalIn + cp.totalOut) / 1e8).toFixed(4)} BTC)`).join('\n') || 'No counterparties detected.'}

═══════════════════════════════════════════════════════
RECENT TRANSACTIONS (Last 10)
═══════════════════════════════════════════════════════
${transactions.slice(0, 10).map(tx => `TX: ${tx.txid.slice(0, 20)}… | ${tx.status.confirmed ? 'Confirmed' : 'Pending'} | Fee: ${(tx.fee / 1e8).toFixed(8)} BTC | Block: ${tx.status.block_height || 'Mempool'}`).join('\n') || 'No transactions.'}
`.trim();

  const handleCopyReport = () => {
    void navigator.clipboard.writeText(fullReportText);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const reportTemplates = [
    { type: 'full', title: 'Full Investigation Report', desc: 'Complete blockchain analysis with all findings, transactions, and risk assessment.' },
    { type: 'financial', title: 'Financial Summary', desc: 'Balance, inflow/outflow, and transaction volume summary.' },
    { type: 'risk', title: 'Risk Assessment Report', desc: 'Risk score breakdown, alerts, and behavioral indicators.' },
    { type: 'counterparty', title: 'Counterparty Analysis', desc: 'All detected counterparty addresses with volume and direction analysis.' },
  ];

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div>
        <div className="flex items-center gap-2">
          <FileText size={20} className="text-primary-400" />
          <h2 className="text-xl font-bold text-white">Investigation Reports</h2>
        </div>
        <div className="flex items-center gap-2 mt-1">
          <Wallet size={12} className="text-primary-400" />
          <span className="text-xs text-dark-400 mono">{activeTargetAddress.slice(0, 16)}…{activeTargetAddress.slice(-8)}</span>
          <span className="text-[10px] text-dark-500">•</span>
          <span className="text-xs text-dark-400">Case {investigationId}</span>
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {[
          { label: 'Balance', value: `${balanceBtc} BTC`, icon: Wallet },
          { label: 'Risk Score', value: `${riskScore}%`, icon: Shield },
          { label: 'Transactions', value: summary?.txCount?.toLocaleString() || '—', icon: Activity },
          { label: 'Generated Reports', value: generatedReports.length.toString(), icon: FileText },
        ].map(s => (
          <div key={s.label} className="glass-card p-3">
            <div className="flex items-center gap-1.5 mb-1">
              <s.icon size={12} className="text-primary-400" />
              <span className="text-[9px] text-dark-400 uppercase font-semibold">{s.label}</span>
            </div>
            <div className="text-lg font-bold text-white">{s.value}</div>
          </div>
        ))}
      </div>

      {/* Report Templates */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {reportTemplates.map(tmpl => (
          <div key={tmpl.type} className="glass-card p-4 hover:border-primary-500/30 border border-dark-700/50 transition-all">
            <h3 className="text-sm font-bold text-white mb-1">{tmpl.title}</h3>
            <p className="text-xs text-dark-400 mb-3">{tmpl.desc}</p>
            <button
              onClick={() => handleGenerateReport(tmpl.type, tmpl.title)}
              className="px-3 py-1.5 rounded-lg bg-primary-500/20 text-primary-400 text-xs font-bold border border-primary-500/30 hover:bg-primary-500/30 flex items-center gap-1"
            >
              <FileText size={12} /> Generate
            </button>
          </div>
        ))}
      </div>

      {/* Live Report Preview */}
      {summary && (
        <div className="glass-card p-5">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-bold text-white">Live Report Preview</h3>
            <div className="flex items-center gap-2">
              <button
                onClick={handleCopyReport}
                className="px-3 py-1 rounded text-[10px] font-bold bg-dark-800 text-dark-300 border border-dark-700 hover:border-dark-600 flex items-center gap-1"
              >
                {copied ? <><CheckCircle2 size={10} /> Copied!</> : <><Copy size={10} /> Copy</>}
              </button>
              <button
                onClick={() => window.print()}
                className="px-3 py-1 rounded text-[10px] font-bold bg-dark-800 text-dark-300 border border-dark-700 hover:border-dark-600 flex items-center gap-1"
              >
                <Printer size={10} /> Print
              </button>
            </div>
          </div>
          <pre className="text-[10px] text-dark-300 mono whitespace-pre-wrap bg-dark-900/50 p-4 rounded-lg border border-dark-700/50 max-h-[500px] overflow-y-auto leading-relaxed">
            {fullReportText}
          </pre>
        </div>
      )}

      {/* Generated Reports History */}
      {generatedReports.length > 0 && (
        <div className="glass-card p-5">
          <h3 className="text-sm font-bold text-white mb-3">Generated Reports</h3>
          <div className="space-y-2">
            {generatedReports.map(rpt => (
              <div key={rpt.id} className="flex items-center justify-between p-2 rounded-lg hover:bg-dark-800/30 transition-colors">
                <div className="flex items-center gap-2">
                  <FileText size={14} className="text-primary-400" />
                  <span className="text-xs text-white">{rpt.title}</span>
                  <span className="text-[10px] text-dark-500">{new Date(rpt.generatedAt).toLocaleString()}</span>
                </div>
                <Download size={14} className="text-dark-400 cursor-pointer hover:text-primary-400" />
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
