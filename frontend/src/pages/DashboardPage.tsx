import React from 'react';
import {
  Wallet, ArrowUpRight, ArrowDownRight, Activity, TrendingUp,
  AlertTriangle, Clock, RefreshCw, Copy, ExternalLink, Shield,
  Cpu, Hash, Layers, Zap, Target, ArrowRight
} from 'lucide-react';
import {
  AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, PieChart, Pie, Cell
} from 'recharts';
import { useNavStore } from '../stores';
import { useInvestigationStore } from '../stores/investigation';
import type { LiveTransaction } from '../stores/investigation';

// ─── Helpers ──────────────────────────────────────────────────────────────────

const satToBtc = (sat: number) => (sat / 1e8).toFixed(8);
const satToBtcShort = (sat: number) => {
  const btc = sat / 1e8;
  if (btc >= 1000) return `${(btc / 1000).toFixed(2)}K`;
  if (btc >= 1) return btc.toFixed(4);
  return btc.toFixed(8);
};

const truncateAddr = (addr: string, len = 10) =>
  addr.length > len * 2 ? `${addr.slice(0, len)}…${addr.slice(-len)}` : addr;

const timeAgo = (iso: string) => {
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'just now';
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  const days = Math.floor(hrs / 24);
  return `${days}d ago`;
};

const formatTimestamp = (unix: number) => {
  const d = new Date(unix * 1000);
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
};

// ─── Component ───────────────────────────────────────────────────────────────

export const DashboardPage: React.FC = () => {
  const { setPage } = useNavStore();
  const {
    activeTargetAddress,
    summary,
    transactions,
    utxos,
    isLoading,
    error,
    refreshTargetData
  } = useInvestigationStore();

  const [lastRefresh, setLastRefresh] = React.useState<Date>(new Date());
  const [copied, setCopied] = React.useState(false);

  // Refresh target data on mount & when address changes
  React.useEffect(() => {
    void refreshTargetData();
  }, [activeTargetAddress, refreshTargetData]);

  // Auto-refresh every 60s
  React.useEffect(() => {
    const interval = setInterval(() => {
      void refreshTargetData();
      setLastRefresh(new Date());
    }, 60_000);
    return () => clearInterval(interval);
  }, [refreshTargetData]);

  const handleCopyAddress = () => {
    void navigator.clipboard.writeText(activeTargetAddress);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  // ── Compute Live Stats from Investigation Store ────────────────────────────

  const coinSymbol = summary?.coinSymbol || 'BTC';
  const balanceNum = summary?.formattedBalance ?? (summary ? summary.confirmedBalance / 1e8 : 0);
  const receivedNum = summary?.formattedReceived ?? (summary ? summary.totalReceived / 1e8 : 0);
  const sentNum = summary?.formattedSent ?? (summary ? summary.totalSent / 1e8 : 0);

  const balanceStr = summary ? `${balanceNum.toLocaleString()} ${coinSymbol}` : '—';
  const totalReceivedStr = summary ? `${receivedNum.toLocaleString()} ${coinSymbol}` : '—';
  const totalSentStr = summary ? `${sentNum.toLocaleString()} ${coinSymbol}` : '—';
  const txCount = summary?.txCount ?? 0;
  const utxoCount = utxos.length;
  const totalFees = transactions.reduce((sum, tx) => sum + (tx.fee || 0), 0);

  // Unique addresses interacted with (counterparties)
  const counterparties = React.useMemo(() => {
    const addrs = new Set<string>();
    transactions.forEach(tx => {
      tx.vin.forEach(inp => {
        if (inp.prevout?.scriptpubkey_address && inp.prevout.scriptpubkey_address !== activeTargetAddress) {
          addrs.add(inp.prevout.scriptpubkey_address);
        }
      });
      tx.vout.forEach(out => {
        if (out.scriptpubkey_address && out.scriptpubkey_address !== activeTargetAddress) {
          addrs.add(out.scriptpubkey_address);
        }
      });
    });
    return addrs;
  }, [transactions, activeTargetAddress]);

  // ── Stat Cards — all from live Mempool / Investigation Store ──────────────

  const statCards = [
    { label: 'Confirmed Balance',  value: balanceStr,          icon: Wallet,       color: 'from-primary-500/20 to-primary-500/5',   iconColor: 'text-primary-400' },
    { label: 'Total Transactions', value: txCount.toLocaleString(), icon: Activity,     color: 'from-accent-green/20 to-accent-green/5', iconColor: 'text-accent-green' },
    { label: 'Live UTXOs',         value: utxoCount.toLocaleString(), icon: Layers,     color: 'from-accent-purple/20 to-accent-purple/5', iconColor: 'text-accent-purple' },
    { label: 'Total Received',     value: totalReceivedStr,    icon: ArrowDownRight, color: 'from-cyber-teal/20 to-cyber-teal/5', iconColor: 'text-cyber-teal' },
    { label: 'Total Sent',         value: totalSentStr,        icon: ArrowUpRight,   color: 'from-accent-gold/20 to-accent-gold/5', iconColor: 'text-accent-gold' },
    { label: 'Counterparties',     value: counterparties.size.toLocaleString(), icon: Target,  color: 'from-accent-red/20 to-accent-red/5', iconColor: 'text-accent-red' },
  ];

  // ── Transaction Volume Chart — real data grouped by month ──────────────────

  const volumeChartData = React.useMemo(() => {
    if (transactions.length === 0) return [];
    const monthMap: Record<string, { inflow: number; outflow: number; fees: number; count: number }> = {};

    transactions.forEach(tx => {
      const blockTime = tx.status.block_time;
      if (!blockTime) return;
      const d = new Date(blockTime * 1000);
      const key = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`;
      if (!monthMap[key]) monthMap[key] = { inflow: 0, outflow: 0, fees: 0, count: 0 };

      // Calculate inflow (received by target)
      tx.vout.forEach(out => {
        if (out.scriptpubkey_address === activeTargetAddress) {
          monthMap[key].inflow += out.value;
        }
      });
      // Calculate outflow (sent by target)
      tx.vin.forEach(inp => {
        if (inp.prevout?.scriptpubkey_address === activeTargetAddress) {
          monthMap[key].outflow += inp.prevout.value;
        }
      });

      monthMap[key].fees += tx.fee || 0;
      monthMap[key].count += 1;
    });

    return Object.entries(monthMap)
      .sort(([a], [b]) => a.localeCompare(b))
      .slice(-12) // last 12 months
      .map(([month, data]) => ({
        month: new Date(month + '-01').toLocaleDateString('en-US', { month: 'short', year: '2-digit' }),
        Inflow: +(data.inflow / 1e8).toFixed(4),
        Outflow: +(data.outflow / 1e8).toFixed(4),
        Txns: data.count,
      }));
  }, [transactions, activeTargetAddress]);

  // ── Fund Flow Pie — Inflow vs Outflow distribution ────────────────────────

  const fundFlowData = React.useMemo(() => {
    if (!summary) return [];
    const received = summary.formattedReceived ?? (summary.totalReceived / 1e8);
    const sent = summary.formattedSent ?? (summary.totalSent / 1e8);
    if (!received && !sent) return [];
    return [
      { name: 'Received', value: +(received || 0).toFixed(4), color: '#00ff88' },
      { name: 'Sent', value: +(sent || 0).toFixed(4), color: '#ff3366' },
    ];
  }, [summary]);

  // ── Recent Transactions — real live data ──────────────────────────────────

  const recentTxs = transactions.slice(0, 6);

  // ── Top UTXO holders (largest UTXOs) ──────────────────────────────────────

  const topUtxos = React.useMemo(() => {
    return [...utxos]
      .sort((a, b) => b.value - a.value)
      .slice(0, 5);
  }, [utxos]);

  // No full-page blocker — always render the dashboard layout

  return (
    <div className="space-y-6 animate-fade-in">

      {/* ═══ Active Target Investigation Banner ═══ */}
      <div className="glass-card p-6 relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-r from-primary-500/8 via-transparent to-accent-green/5" />
        <div className="absolute top-0 right-0 w-64 h-64 bg-primary-500/5 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2" />
        <div className="relative">
          <div className="flex items-start justify-between flex-wrap gap-4">
            <div>
              <div className="flex items-center gap-3 mb-2 flex-wrap text-[10px] font-semibold tracking-widest uppercase">
                <div className="flex items-center gap-1.5 text-accent-green">
                  <div className="w-1.5 h-1.5 rounded-full bg-accent-green animate-pulse" />
                  <span>Active Investigation Target</span>
                </div>
                {summary && (
                  <span className="text-dark-500">• {summary.chain} • {summary.scriptType}</span>
                )}
              </div>
              <h1 className="text-2xl font-bold text-white mb-1">Intelligence Overview</h1>
              <p className="text-sm text-dark-400">Live blockchain metrics for active target wallet</p>
            </div>
            <div className="flex items-center gap-2 text-[10px] text-dark-500 mt-1">
              <RefreshCw size={11} className={isLoading ? 'animate-spin' : ''} />
              <span>Updated {timeAgo(lastRefresh.toISOString())}</span>
            </div>
          </div>

          {/* Target Address Display */}
          <div className="mt-4 flex items-center gap-3 flex-wrap">
            <div className="flex items-center gap-2 px-4 py-2.5 rounded-lg bg-dark-800/80 border border-dark-700/50">
              <Wallet size={14} className="text-primary-400" />
              <span className="mono text-xs text-white tracking-wide">{activeTargetAddress}</span>
            </div>
            <button
              onClick={handleCopyAddress}
              className="p-2 rounded-lg bg-dark-800/50 border border-dark-700/50 hover:bg-dark-700/50 transition-colors"
              title="Copy address"
            >
              <Copy size={13} className={copied ? 'text-accent-green' : 'text-dark-400'} />
            </button>
            <a
              href={`https://mempool.space/address/${activeTargetAddress}`}
              target="_blank"
              rel="noopener noreferrer"
              className="p-2 rounded-lg bg-dark-800/50 border border-dark-700/50 hover:bg-dark-700/50 transition-colors"
              title="View on Mempool.space"
            >
              <ExternalLink size={13} className="text-dark-400" />
            </a>
            <button
              onClick={() => setPage('blockchain')}
              className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-primary-500/15 border border-primary-500/30 text-primary-400 text-[11px] font-medium hover:bg-primary-500/25 transition-colors"
            >
              <span>Full Analysis</span>
              <ArrowRight size={12} />
            </button>
          </div>

          {/* Quick Summary Badges */}
          {summary && (
            <div className="mt-3 flex items-center gap-3 flex-wrap text-[10px]">
              {summary.firstSeen && (
                <span className="px-2 py-1 rounded bg-dark-800/60 text-dark-300">
                  First Seen: {new Date(summary.firstSeen).toLocaleDateString()}
                </span>
              )}
              {summary.lastSeen && (
                <span className="px-2 py-1 rounded bg-dark-800/60 text-dark-300">
                  Last Active: {new Date(summary.lastSeen).toLocaleDateString()}
                </span>
              )}
              <span className="px-2 py-1 rounded bg-dark-800/60 text-dark-300">
                Unconfirmed: {satToBtc(summary.unconfirmedBalance)} BTC
              </span>
            </div>
          )}
        </div>
      </div>

      {/* ═══ Live Stat Cards ═══ */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        {statCards.map((stat) => {
          const Icon = stat.icon;
          return (
            <div key={stat.label} className="glass-card-hover p-4 relative overflow-hidden group cursor-pointer">
              <div className={`absolute inset-0 bg-gradient-to-br ${stat.color} opacity-0 group-hover:opacity-100 transition-opacity duration-300`} />
              <div className="relative">
                <div className="flex items-center justify-between mb-3">
                  <Icon size={18} className={stat.iconColor} />
                </div>
                <p className="text-xl font-bold text-white truncate">{stat.value}</p>
                <p className="text-[11px] text-dark-400 mt-1">{stat.label}</p>
              </div>
            </div>
          );
        })}
      </div>

      {/* ═══ Charts Row ═══ */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

        {/* Transaction Volume Chart (real grouped by month) */}
        <div className="lg:col-span-2 glass-card p-5">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-sm font-semibold text-white">Transaction Volume</h3>
              <p className="text-[11px] text-dark-400">Monthly inflow vs outflow ({coinSymbol})</p>
            </div>
            <div className="flex items-center gap-4 text-[10px]">
              <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-accent-green" /> Inflow</span>
              <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-accent-red" /> Outflow</span>
            </div>
          </div>
          {volumeChartData.length > 0 ? (
            <ResponsiveContainer width="100%" height={220}>
              <AreaChart data={volumeChartData}>
                <defs>
                  <linearGradient id="colorInflow" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#00ff88" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#00ff88" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="colorOutflow" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#ff3366" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#ff3366" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#1a1f36" />
                <XAxis dataKey="month" tick={{ fill: '#78819a', fontSize: 11 }} axisLine={false} />
                <YAxis tick={{ fill: '#78819a', fontSize: 11 }} axisLine={false} />
                <Tooltip contentStyle={{ backgroundColor: '#1a1f36', border: '1px solid #2a3253', borderRadius: 8, fontSize: 12, color: '#fff' }} />
                <Area type="monotone" dataKey="Inflow" stroke="#00ff88" fillOpacity={1} fill="url(#colorInflow)" strokeWidth={2} />
                <Area type="monotone" dataKey="Outflow" stroke="#ff3366" fillOpacity={1} fill="url(#colorOutflow)" strokeWidth={2} />
              </AreaChart>
            </ResponsiveContainer>
          ) : (
            <div className="flex items-center justify-center h-[220px] text-dark-500 text-xs">
              {activeTargetAddress ? 'Analyze a wallet to see transaction volume chart.' : 'No target address set.'}
            </div>
          )}
        </div>

        {/* Fund Flow Pie — Received vs Sent */}
        <div className="glass-card p-5">
          <h3 className="text-sm font-semibold text-white mb-4">Fund Flow Distribution</h3>
          {fundFlowData.length > 0 ? (
            <>
              <ResponsiveContainer width="100%" height={180}>
                <PieChart>
                  <Pie data={fundFlowData} cx="50%" cy="50%" innerRadius={50} outerRadius={75} paddingAngle={5} dataKey="value">
                    {fundFlowData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip contentStyle={{ backgroundColor: '#1a1f36', border: '1px solid #2a3253', borderRadius: 8, fontSize: 12, color: '#fff' }}
                    formatter={(value: number) => `${value} ${coinSymbol}`}
                  />
                </PieChart>
              </ResponsiveContainer>
              <div className="grid grid-cols-2 gap-2 mt-2">
                {fundFlowData.map((item) => (
                  <div key={item.name} className="flex items-center gap-2 text-[11px]">
                    <span className="w-2 h-2 rounded-full" style={{ backgroundColor: item.color }} />
                    <span className="text-dark-300">{item.name}</span>
                    <span className="text-white font-semibold ml-auto">{item.value} {coinSymbol}</span>
                  </div>
                ))}
              </div>
            </>
          ) : (
            <div className="flex items-center justify-center h-[180px] text-dark-500 text-xs">
              No fund flow data available.
            </div>
          )}
        </div>
      </div>

      {/* ═══ Bottom Row ═══ */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

        {/* Recent Transactions — from live Mempool data */}
        <div className="lg:col-span-2 glass-card p-5">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-white">Recent Transactions</h3>
            <button onClick={() => setPage('blockchain')} className="text-[11px] text-primary-400 hover:text-primary-300">View All</button>
          </div>
          <div className="space-y-2">
            {recentTxs.length > 0 ? recentTxs.map((tx) => {
              // Determine if target is sender or receiver
              const isSender = tx.vin.some(inp => inp.prevout?.scriptpubkey_address === activeTargetAddress);
              const isReceiver = tx.vout.some(out => out.scriptpubkey_address === activeTargetAddress);
              const direction = isSender && isReceiver ? 'self' : isSender ? 'sent' : 'received';

              // Calculate amount relevant to target
              let targetAmount = 0;
              if (direction === 'received' || direction === 'self') {
                tx.vout.forEach(out => {
                  if (out.scriptpubkey_address === activeTargetAddress) targetAmount += out.value;
                });
              } else {
                tx.vin.forEach(inp => {
                  if (inp.prevout?.scriptpubkey_address === activeTargetAddress) targetAmount += inp.prevout.value;
                });
              }

              return (
                <div key={tx.txid} className="flex items-center gap-3 p-3 rounded-lg bg-dark-800/30 hover:bg-dark-800/50 transition-colors border border-transparent hover:border-dark-700/50">
                  <div className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 ${
                    direction === 'received' ? 'text-accent-green bg-accent-green/15' :
                    direction === 'sent' ? 'text-accent-red bg-accent-red/15' :
                    'text-accent-gold bg-accent-gold/15'
                  }`}>
                    {direction === 'received' ? <ArrowDownRight size={14} /> :
                     direction === 'sent' ? <ArrowUpRight size={14} /> :
                     <Activity size={14} />}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between">
                      <a
                        href={`https://mempool.space/tx/${tx.txid}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="mono text-xs text-primary-400 hover:text-primary-300 truncate max-w-[200px]"
                      >
                        {truncateAddr(tx.txid, 8)}
                      </a>
                      <span className={`text-xs font-semibold ${
                        direction === 'received' ? 'text-accent-green' : direction === 'sent' ? 'text-accent-red' : 'text-accent-gold'
                      }`}>
                        {direction === 'received' ? '+' : direction === 'sent' ? '-' : '↔'}{satToBtcShort(targetAmount)} BTC
                      </span>
                    </div>
                    <div className="flex items-center gap-2 mt-1 text-[10px] text-dark-500">
                      <span className={`px-1.5 py-0.5 rounded text-[9px] font-medium ${
                        tx.status.confirmed ? 'bg-accent-green/10 text-accent-green' : 'bg-accent-gold/10 text-accent-gold'
                      }`}>
                        {tx.status.confirmed ? 'Confirmed' : 'Pending'}
                      </span>
                      {tx.status.block_time && (
                        <span>{formatTimestamp(tx.status.block_time)}</span>
                      )}
                      <span className="ml-auto">Fee: {(tx.fee / 1e8).toFixed(8)} BTC</span>
                    </div>
                  </div>
                </div>
              );
            }) : (
              <p className="text-xs text-dark-500 text-center py-4">No transactions found for this target.</p>
            )}
          </div>
        </div>

        {/* Top UTXOs & Address Details */}
        <div className="glass-card p-5">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-white">Largest UTXOs</h3>
            <Layers size={14} className="text-dark-400" />
          </div>
          <div className="space-y-3">
            {topUtxos.length > 0 ? topUtxos.map((utxo, i) => (
              <div key={`${utxo.txid}-${utxo.vout}`} className="flex items-center gap-3 p-2.5 rounded-lg bg-dark-800/30">
                <div className="w-6 h-6 rounded flex items-center justify-center bg-primary-500/15 text-primary-400 text-[10px] font-bold">
                  {i + 1}
                </div>
                <div className="flex-1 min-w-0">
                  <a
                    href={`https://mempool.space/tx/${utxo.txid}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="mono text-[11px] text-primary-400 hover:text-primary-300 truncate block"
                  >
                    {truncateAddr(utxo.txid, 6)}:{utxo.vout}
                  </a>
                  <div className="flex items-center gap-2 mt-0.5 text-[10px] text-dark-500">
                    <span className={`px-1 py-0.5 rounded text-[9px] ${
                      utxo.status.confirmed ? 'text-accent-green bg-accent-green/10' : 'text-accent-gold bg-accent-gold/10'
                    }`}>
                      {utxo.status.confirmed ? `Block #${utxo.status.block_height}` : 'Unconfirmed'}
                    </span>
                  </div>
                </div>
                <span className="text-xs font-semibold text-white whitespace-nowrap">
                  {satToBtcShort(utxo.value)} BTC
                </span>
              </div>
            )) : (
              <p className="text-xs text-dark-500 text-center py-4">No UTXOs found.</p>
            )}
          </div>

          {/* Fee Analysis mini card */}
          {transactions.length > 0 && (
            <div className="mt-4 p-3 rounded-lg bg-dark-800/50 border border-dark-700/30">
              <div className="flex items-center gap-2 mb-2">
                <Zap size={12} className="text-accent-gold" />
                <span className="text-[11px] font-semibold text-white">Fee Analysis</span>
              </div>
              <div className="grid grid-cols-2 gap-2 text-[10px]">
                <div>
                  <span className="text-dark-500">Total Fees Paid</span>
                  <p className="text-white font-medium">{(totalFees / 1e8).toFixed(8)} BTC</p>
                </div>
                <div>
                  <span className="text-dark-500">Avg Fee/Tx</span>
                  <p className="text-white font-medium">{(totalFees / transactions.length / 1e8).toFixed(8)} BTC</p>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="glass-card p-4 border border-accent-red/30">
          <div className="flex items-center gap-2">
            <AlertTriangle size={14} className="text-accent-red" />
            <span className="text-xs text-accent-red">{error}</span>
          </div>
        </div>
      )}
    </div>
  );
};
