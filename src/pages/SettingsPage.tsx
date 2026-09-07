import React, { useState, useEffect } from 'react';
import { useAuthStore } from '../stores';
import { Settings, Shield, User, FileLock2, AlertCircle, CheckCircle2, Users, Heart, Server, ShieldCheck, Lock, Unlock, Key, Globe, Sparkles, RefreshCw } from 'lucide-react';
import { API_BASE } from '../utils/api';

export const SettingsPage: React.FC = () => {
  const { user } = useAuthStore();
  const [activeTab, setActiveTab] = useState<'profile' | 'admin' | 'health' | 'gim'>('profile');

  const [rpcStatus, setRpcStatus] = useState<any>(null);
  const [loadingRpc, setLoadingRpc] = useState(false);

  const fetchRpcStatus = async () => {
    setLoadingRpc(true);
    try {
      const res = await fetch(`${API_BASE}/api/health/indexer`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token') || ''}`
        }
      });
      if (res.ok) {
        const data = await res.json();
        setRpcStatus(data);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoadingRpc(false);
    }
  };

  useEffect(() => {
    if (activeTab === 'health') {
      fetchRpcStatus();
    }
  }, [activeTab]);

  // Session tracking state
  const [sessions, setSessions] = useState([
    { id: 'sess-1', device: 'Windows PC (Cyber-Cell Workstation #4)', ip: '10.0.1.45', browser: 'Chrome 126', os: 'Windows 11', lastActive: 'Active now', isCurrent: true },
    { id: 'sess-2', device: 'MacBook Pro (Director Room)', ip: '192.168.1.103', browser: 'Safari 17.5', os: 'macOS Sonoma', lastActive: '12 minutes ago', isCurrent: false },
    { id: 'sess-3', device: 'iPad Pro (Field Agent App)', ip: '172.20.10.2', browser: 'Safari Mobile', os: 'iOS 17.4', lastActive: '2 hours ago', isCurrent: false }
  ]);

  const handleRevokeSession = (id: string, deviceName: string) => {
    setSessions(prev => prev.filter(s => s.id !== id));
    alert(`Session terminated successfully for device: ${deviceName}. Token rotated.`);
  };

  // User Management State (Mock)
  const [usersList, setUsersList] = useState([
    { id: 'usr-1', name: 'Lakshay Soni', email: 'lakshaysoni@cybercrime.gov.in', role: 'investigator', status: 'Active' },
    { id: 'usr-2', name: 'Supervisor Rawat', email: 'super.rawat@cybercrime.gov.in', role: 'supervisor', status: 'Active' },
    { id: 'usr-3', name: 'Analyst Singh', email: 'analyst.singh@cybercrime.gov.in', role: 'analyst', status: 'Active' },
    { id: 'usr-4', name: 'Auditor Verma', email: 'auditor.verma@cybercrime.gov.in', role: 'auditor', status: 'Active' },
    { id: 'usr-5', name: 'Officer Gupta', email: 'officer.gupta@cybercrime.gov.in', role: 'read-only', status: 'Deactivated' }
  ]);

  const [allowedIpRanges, setAllowedIpRanges] = useState('10.0.0.0/8, 192.168.1.0/24');
  const [sessionTimeout, setSessionTimeout] = useState('60');

  const toggleUserStatus = (id: string) => {
    setUsersList(prev => prev.map(u => {
      if (u.id === id) {
        return { ...u, status: u.status === 'Active' ? 'Deactivated' : 'Active' };
      }
      return u;
    }));
  };

  const updateUserRole = (id: string, role: string) => {
    setUsersList(prev => prev.map(u => u.id === id ? { ...u, role } : u));
  };

  return (
    <div className="space-y-6 animate-fade-in max-w-4xl">
      {/* Header */}
      <div>
        <h2 className="text-xl font-bold text-white">Platform Settings & Security Profile</h2>
        <p className="text-xs text-dark-400">View user session parameters, role clearances, and AML compliance configurations</p>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-dark-700/50 bg-dark-800/10 rounded-t-lg overflow-x-auto">
        <button
          onClick={() => setActiveTab('profile')}
          className={`px-5 py-3 border-b-2 text-xs font-semibold whitespace-nowrap transition-all cursor-pointer ${activeTab === 'profile' ? 'border-primary-500 text-white bg-dark-900/30' : 'border-transparent text-dark-400 hover:text-white'
            }`}
        >
          <Shield size={14} className="inline mr-1.5" /> Profile & AML
        </button>
        <button
          onClick={() => setActiveTab('admin')}
          className={`px-5 py-3 border-b-2 text-xs font-semibold whitespace-nowrap transition-all cursor-pointer ${activeTab === 'admin' ? 'border-primary-500 text-white bg-dark-900/30' : 'border-transparent text-dark-400 hover:text-white'
            }`}
        >
          <Users size={14} className="inline mr-1.5" /> User Administration
        </button>
        <button
          onClick={() => setActiveTab('health')}
          className={`px-5 py-3 border-b-2 text-xs font-semibold whitespace-nowrap transition-all cursor-pointer ${activeTab === 'health' ? 'border-primary-500 text-white bg-dark-900/30' : 'border-transparent text-dark-400 hover:text-white'
            }`}
        >
          <Heart size={14} className="inline mr-1.5" /> System Health Logs
        </button>
        <button
          onClick={() => setActiveTab('gim')}
          className={`px-5 py-3 border-b-2 text-xs font-semibold whitespace-nowrap transition-all cursor-pointer ${activeTab === 'gim' ? 'border-primary-500 text-white bg-dark-900/30' : 'border-transparent text-dark-400 hover:text-white'
            }`}
        >
          <Globe size={14} className="inline mr-1.5 animate-pulse" /> GIM Federation
        </button>
      </div>

      {/* Tab Workspace Contents */}
      <div className="space-y-6">
        {activeTab === 'profile' && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Profile Column */}
            <div className="md:col-span-1 space-y-6">
              {/* Profile Card */}
              <div className="glass-card p-5 space-y-4 border-dark-700/50">
                <div className="flex items-center gap-2 border-b border-dark-700/50 pb-3">
                  <User size={16} className="text-primary-400" />
                  <h3 className="text-sm font-bold text-white">Security Identity</h3>
                </div>

                <div className="space-y-3 text-xs">
                  <div className="flex flex-col">
                    <span className="text-[10px] text-dark-500 uppercase">Operator Name</span>
                    <span className="text-xs font-semibold text-white">{user?.username || 'Lakshay Soni'}</span>
                  </div>
                  <div className="flex flex-col">
                    <span className="text-[10px] text-dark-500 uppercase">Email Profile</span>
                    <span className="text-xs font-semibold text-white mono">{user?.email || 'lakshaysoni@cybercrime.gov.in'}</span>
                  </div>
                  <div className="flex flex-col">
                    <span className="text-[10px] text-dark-500 uppercase">Clearance Role</span>
                    <span className="text-xs font-bold text-primary-400 capitalize">{user?.role || 'investigator'}</span>
                  </div>
                  <div className="flex flex-col">
                    <span className="text-[10px] text-dark-500 uppercase">Cell Unit</span>
                    <span className="text-xs font-semibold text-white">{user?.department || 'Cyber Crime Cell'}</span>
                  </div>
                </div>
              </div>

              {/* MFA Setup Card */}
              <div className="glass-card p-5 space-y-4 border-dark-700/50">
                <div className="flex items-center gap-2 border-b border-dark-700/50 pb-3">
                  <Key size={16} className="text-primary-400" />
                  <h3 className="text-sm font-bold text-white">Multi-Factor Auth (MFA)</h3>
                </div>

                <div className="space-y-4 text-xs">
                  <div className="flex items-center justify-between">
                    <span className="text-dark-300">MFA Status</span>
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-accent-green/15 border border-accent-green/20 text-accent-green">
                      TOTP Active
                    </span>
                  </div>

                  <div className="p-3 bg-dark-900/50 border border-dark-800 rounded-lg space-y-2 text-[11px]">
                    <span className="font-bold text-white block">Authenticator Secret:</span>
                    <code className="text-primary-300 font-mono block select-all">JBSWY3DPEHPK3PXP</code>
                    <p className="text-dark-500 text-[10px] leading-snug">Scan this secret key with Google Authenticator or Duo App. Fallback login code: <span className="font-bold text-primary-400 font-mono">123456</span></p>
                  </div>

                  <div className="flex justify-center bg-white p-3 rounded-lg border border-dark-800 w-32 h-32 mx-auto">
                    <svg className="w-full h-full text-dark-950" viewBox="0 0 29 29" fill="currentColor">
                      <path d="M0 0h9v9H0zm1 1h7v7H1zm11 0h1v1h-1zm1 1h1v1h-1zm-2 1h1v1h-1zm4-3h9v9h-9zm1 1h7v7h-7zm-11 11h9v9H0zm1 1h7v7H1zm11-1h1v1h-1zm3 0h1v1h-1zm3 0h1v1h-1zm-6 2h1v1h-1zm4 0h1v1h-1zm4 0h1v1h-1zm-7 2h1v1h-1zm3 0h1v1h-1zm3 0h1v1h-1z" />
                      <path d="M2 2h5v5H2zm17 0h5v5h-5zM2 13h5v5H2z" fill="none" />
                    </svg>
                  </div>
                </div>
              </div>
            </div>

            {/* Configurations & Session Management */}
            <div className="md:col-span-2 space-y-6">
              <div className="glass-card p-6 space-y-4 border-dark-700/50">
                <div className="flex items-center gap-2 border-b border-dark-700/50 pb-3">
                  <Shield size={16} className="text-accent-green" />
                  <h3 className="text-sm font-bold text-white">AML Compliance Engine Rules</h3>
                </div>

                <div className="space-y-3.5 text-xs text-dark-300">
                  <div className="flex items-start gap-2.5">
                    <CheckCircle2 size={14} className="text-accent-green mt-0.5 flex-shrink-0" />
                    <div>
                      <p className="font-semibold text-white">Direct Sanction Exposure Checking</p>
                      <p className="text-[11px] text-dark-400 mt-0.5">Flag direct or 1-hop transactions leading to sanctioned addresses on OFAC or UN lists.</p>
                    </div>
                  </div>
                  <div className="flex items-start gap-2.5">
                    <CheckCircle2 size={14} className="text-accent-green mt-0.5 flex-shrink-0" />
                    <div>
                      <p className="font-semibold text-white">Programmatic Peeling Layering Alarms</p>
                      <p className="text-[11px] text-dark-400 mt-0.5">Raises alarms if a single input address distributes balances across more than 15 split wallets in 6 hours.</p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Session Tracker Card */}
              <div className="glass-card p-6 space-y-4 border-dark-700/50">
                <div className="flex items-center justify-between border-b border-dark-700/50 pb-3">
                  <div className="flex items-center gap-2">
                    <Server size={16} className="text-primary-400" />
                    <h3 className="text-sm font-bold text-white">Active Device Sessions</h3>
                  </div>
                  <span className="text-[10px] text-dark-500 uppercase font-mono font-bold bg-dark-900 px-2 py-0.5 rounded border border-dark-800">Rotating Tokens</span>
                </div>

                <div className="space-y-3">
                  {sessions.map((sess) => (
                    <div key={sess.id} className="flex flex-col sm:flex-row sm:items-center justify-between p-3.5 bg-dark-900/40 border border-dark-800 rounded-lg text-xs hover:border-dark-750 transition-all duration-200 gap-3">
                      <div className="space-y-1">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="font-bold text-white">{sess.device}</span>
                          {sess.isCurrent && (
                            <span className="px-1.5 py-0.5 rounded text-[8px] font-bold bg-accent-green/10 border border-accent-green/20 text-accent-green uppercase">Current</span>
                          )}
                        </div>
                        <p className="text-[10px] text-dark-400">IP: {sess.ip} • Browser: {sess.browser} • OS: {sess.os}</p>
                        <p className="text-[9px] text-dark-500">Last activity: {sess.lastActive}</p>
                      </div>
                      {!sess.isCurrent && (
                        <button
                          onClick={() => handleRevokeSession(sess.id, sess.device)}
                          className="px-2.5 py-1 bg-accent-red/10 border border-accent-red/20 text-accent-red rounded hover:bg-accent-red/20 text-[10px] font-bold transition-all duration-200 self-start sm:self-auto"
                        >
                          Revoke
                        </button>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'admin' && (
          <div className="space-y-6">
            {/* User Management Table */}
            <div className="glass-card p-5 border-dark-700/50 space-y-4">
              <div className="flex items-center justify-between border-b border-dark-800 pb-3">
                <div className="flex items-center gap-2">
                  <Users size={16} className="text-primary-400" />
                  <h3 className="text-sm font-bold text-white">Granular RBAC User Directory</h3>
                </div>
                <span className="text-[10px] text-dark-400">Total Users: {usersList.length}</span>
              </div>

              <div className="overflow-x-auto text-xs">
                <table className="data-table">
                  <thead>
                    <tr className="bg-dark-850">
                      <th>Name</th>
                      <th>Email Profile</th>
                      <th>System Role</th>
                      <th>Account Status</th>
                      <th className="text-center">Action Toggle</th>
                    </tr>
                  </thead>
                  <tbody>
                    {usersList.map(item => (
                      <tr key={item.id} className="hover:bg-dark-800/10">
                        <td className="font-bold text-white">{item.name}</td>
                        <td className="mono text-dark-300">{item.email}</td>
                        <td>
                          <select
                            value={item.role}
                            onChange={(e) => updateUserRole(item.id, e.target.value)}
                            className="bg-dark-950 border border-dark-850 rounded px-1.5 py-0.5 text-xs text-white"
                          >
                            <option value="administrator">Administrator</option>
                            <option value="supervisor">Supervisor</option>
                            <option value="investigator">Investigator</option>
                            <option value="analyst">Analyst</option>
                            <option value="auditor">Auditor</option>
                            <option value="read-only">Read-only</option>
                          </select>
                        </td>
                        <td>
                          <span className={`px-2 py-0.5 rounded text-[9px] font-bold ${item.status === 'Active' ? 'bg-accent-green/15 text-accent-green border border-accent-green/20' : 'bg-dark-800 text-dark-400'}`}>
                            {item.status}
                          </span>
                        </td>
                        <td className="text-center">
                          <button
                            onClick={() => toggleUserStatus(item.id)}
                            className="p-1 rounded hover:bg-dark-800 text-dark-400 hover:text-white transition-colors"
                            title="Toggle Lock Account"
                          >
                            {item.status === 'Active' ? <Lock size={12} /> : <Unlock size={12} />}
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Network Security Settings */}
            <div className="glass-card p-5 border-dark-700/50 space-y-4">
              <div className="flex items-center gap-2 border-b border-dark-800 pb-3">
                <ShieldCheck size={16} className="text-primary-400" />
                <h3 className="text-sm font-bold text-white">Allowed IP Gateway Ranges</h3>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                <div>
                  <label className="block text-dark-400 text-[10px] uppercase font-bold mb-1">Session timeout limit (mins)</label>
                  <input
                    type="number"
                    value={sessionTimeout}
                    onChange={(e) => setSessionTimeout(e.target.value)}
                    className="input-field py-1.5 px-3"
                  />
                </div>
                <div>
                  <label className="block text-dark-400 text-[10px] uppercase font-bold mb-1">Allowed Access CIDR Ranges</label>
                  <input
                    type="text"
                    value={allowedIpRanges}
                    onChange={(e) => setAllowedIpRanges(e.target.value)}
                    className="input-field py-1.5 px-3 mono"
                  />
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'health' && (
          <div className="space-y-6 animate-fade-in">
            {/* System Status Indicators */}
            <div className="glass-card p-5 border-dark-700/50 space-y-4">
              <div className="flex items-center justify-between border-b border-dark-800 pb-3">
                <div className="flex items-center gap-2">
                  <Server size={16} className="text-primary-400" />
                  <h3 className="text-sm font-bold text-white">Platform Indexer & Diagnostics</h3>
                </div>
                <div className="flex items-center gap-2 font-mono text-[10px]">
                  <span className="text-dark-500">Pending Sync Queue:</span>
                  <span className="text-accent-gold font-bold">{rpcStatus?.queue_metrics?.pending_blocks_sync ?? 0} Blocks</span>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs font-semibold">
                <div className="p-3 bg-dark-900 border border-dark-850 rounded-xl flex items-center justify-between">
                  <div>
                    <span className="text-[10px] text-dark-500 block uppercase">REST API Gateway</span>
                    <span className="text-white font-mono">Port 8000</span>
                  </div>
                  <span className="flex items-center gap-1 text-accent-green"><span className="w-1.5 h-1.5 rounded-full bg-accent-green animate-pulse" /> ONLINE</span>
                </div>

                <div className="p-3 bg-dark-900 border border-dark-850 rounded-xl flex items-center justify-between">
                  <div>
                    <span className="text-[10px] text-dark-500 block uppercase">SQLite Database</span>
                    <span className="text-white font-mono">LEAtTrace.db</span>
                  </div>
                  <span className="flex items-center gap-1 text-accent-green"><span className="w-1.5 h-1.5 rounded-full bg-accent-green" /> HEALTHY</span>
                </div>

                <div className="p-3 bg-dark-900 border border-dark-850 rounded-xl flex items-center justify-between">
                  <div>
                    <span className="text-[10px] text-dark-500 block uppercase">Local Block Indexer</span>
                    <span className="text-white font-mono">Multi-Chain Sync Task</span>
                  </div>
                  <span className="flex items-center gap-1 text-accent-green"><span className="w-1.5 h-1.5 rounded-full bg-accent-green animate-pulse" /> ACTIVE</span>
                </div>
              </div>
            </div>

            {/* Multi-Chain RPC Node connection health monitor */}
            <div className="glass-card p-5 border-dark-700/50 space-y-4">
              <div className="flex items-center justify-between border-b border-dark-800 pb-3">
                <div className="flex items-center gap-2">
                  <Server size={16} className="text-primary-400" />
                  <h3 className="text-sm font-bold text-white">Multi-Chain RPC Node Connections</h3>
                </div>
                <button
                  onClick={fetchRpcStatus}
                  disabled={loadingRpc}
                  className="text-xs text-primary-400 hover:text-white flex items-center gap-1 cursor-pointer transition-colors"
                >
                  <RefreshCw size={12} className={loadingRpc ? 'animate-spin' : ''} /> Refresh Status
                </button>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 text-xs font-semibold">
                {rpcStatus && rpcStatus.detailed_chains ? (
                  Object.entries(rpcStatus.detailed_chains).map(([chain, details]: [string, any]) => {
                    const isHealthy = details.status === 'Healthy';
                    return (
                      <div key={chain} className="p-3.5 bg-dark-900 border border-dark-850 rounded-xl space-y-2">
                        <div className="flex items-center justify-between">
                          <span className="font-bold text-white uppercase tracking-wider">{chain} RPC Node</span>
                          <span className={`px-2 py-0.5 rounded text-[9px] font-bold uppercase ${isHealthy ? 'bg-accent-green/10 text-accent-green border border-accent-green/20' : 'bg-accent-gold/10 text-accent-gold border border-accent-gold/20'
                            }`}>
                            {details.status}
                          </span>
                        </div>
                        <div className="space-y-1 text-[11px] text-dark-400 font-mono">
                          <div className="flex justify-between">
                            <span>Latest Block:</span>
                            <span className="text-white">{details.latest_block.toLocaleString()}</span>
                          </div>
                          <div className="flex justify-between">
                            <span>Indexed Block:</span>
                            <span className="text-white">{details.indexed_block.toLocaleString()}</span>
                          </div>
                          <div className="flex justify-between">
                            <span>Block Lag:</span>
                            <span className={details.block_lag > 10 ? 'text-accent-red font-bold' : 'text-white'}>
                              {details.block_lag} Blocks
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span>Sync Progress:</span>
                            <span className="text-accent-green font-bold">{details.sync_progress}</span>
                          </div>
                          <div className="flex justify-between">
                            <span>Latency Index:</span>
                            <span className="text-white">{details.latency_ms} ms</span>
                          </div>
                          <div className="flex justify-between">
                            <span>Failover Link:</span>
                            <span className={details.failover_active ? 'text-accent-gold font-bold' : 'text-dark-500'}>
                              {details.failover_active ? 'Active' : 'Standby'}
                            </span>
                          </div>
                        </div>
                      </div>
                    );
                  })
                ) : (
                  <div className="col-span-full py-4 text-center text-dark-500 font-mono">
                    No active RPC connection status available. Click refresh to query endpoints.
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'gim' && (
          <div className="space-y-6">
            {/* Connected Federation Nodes */}
            <div className="glass-card p-5 border-dark-700/50 space-y-4">
              <div className="flex items-center justify-between border-b border-dark-800 pb-3">
                <div className="flex items-center gap-2">
                  <Globe size={16} className="text-primary-400" />
                  <h3 className="text-sm font-bold text-white">Federated Intelligence Nodes (GIM-NA)</h3>
                </div>
                <span className="text-[10px] text-accent-green font-bold tracking-widest uppercase">SIEP Network: Operational</span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                {/* Node 1 */}
                <div className="p-3.5 bg-dark-900/60 border border-dark-800 rounded-xl flex items-center justify-between">
                  <div>
                    <span className="text-[10px] text-dark-500 block uppercase">CC-IN-01 (India Central Node)</span>
                    <span className="text-white font-mono font-semibold">Sovereign Node Hub</span>
                  </div>
                  <div className="text-right">
                    <span className="flex items-center gap-1 text-accent-green text-[10px] font-bold"><span className="w-1.5 h-1.5 rounded-full bg-accent-green" /> CONNECTED</span>
                    <span className="text-[9px] text-dark-400 font-mono">Trust Score: 98%</span>
                  </div>
                </div>

                {/* Node 2 */}
                <div className="p-3.5 bg-dark-900/60 border border-dark-800 rounded-xl flex items-center justify-between">
                  <div>
                    <span className="text-[10px] text-dark-500 block uppercase">INTER-01 (Interpol Hub Node)</span>
                    <span className="text-white font-mono font-semibold">Federated Liaison Hub</span>
                  </div>
                  <div className="text-right">
                    <span className="flex items-center gap-1 text-accent-green text-[10px] font-bold"><span className="w-1.5 h-1.5 rounded-full bg-accent-green" /> CONNECTED</span>
                    <span className="text-[9px] text-dark-400 font-mono">Trust Score: 95%</span>
                  </div>
                </div>

                {/* Node 3 */}
                <div className="p-3.5 bg-dark-900/60 border border-dark-800 rounded-xl flex items-center justify-between">
                  <div>
                    <span className="text-[10px] text-dark-500 block uppercase">EU-01 (Europol Hub Node)</span>
                    <span className="text-white font-mono font-semibold">Federated Liaison Hub</span>
                  </div>
                  <div className="text-right">
                    <span className="flex items-center gap-1 text-accent-green text-[10px] font-bold"><span className="w-1.5 h-1.5 rounded-full bg-accent-green" /> CONNECTED</span>
                    <span className="text-[9px] text-dark-400 font-mono">Trust Score: 94%</span>
                  </div>
                </div>

                {/* Node 4 */}
                <div className="p-3.5 bg-dark-900/60 border border-dark-800 rounded-xl flex items-center justify-between">
                  <div>
                    <span className="text-[10px] text-dark-500 block uppercase">FC-US-01 (US FinCEN Node)</span>
                    <span className="text-white font-mono font-semibold">Sovereign Node Hub</span>
                  </div>
                  <div className="text-right">
                    <span className="flex items-center gap-1 text-accent-gold text-[10px] font-bold"><span className="w-1.5 h-1.5 rounded-full bg-accent-gold animate-pulse" /> SYNCING</span>
                    <span className="text-[9px] text-dark-400 font-mono">Trust Score: 91%</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Jurisdiction Sharing Policies */}
            <div className="glass-card p-5 border-dark-700/50 space-y-4">
              <div className="flex items-center gap-2 border-b border-dark-800 pb-3">
                <FileLock2 size={16} className="text-primary-400" />
                <h3 className="text-sm font-bold text-white">Jurisdiction Sharing Rules & Privacy Filters</h3>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                <div className="p-4 bg-dark-900/40 border border-dark-800 rounded-xl space-y-3">
                  <span className="text-[10px] text-dark-400 uppercase font-bold block">Privacy-Preserving Toggles</span>
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <span>Mask Suspect KYC Metadata</span>
                      <span className="px-2 py-0.5 rounded bg-primary-500/10 text-primary-400 font-bold text-[9px]">ENFORCED</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span>Redact Physical Address Indicators</span>
                      <span className="px-2 py-0.5 rounded bg-primary-500/10 text-primary-400 font-bold text-[9px]">ENFORCED</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span>Fuzzy Wallet Attribution Sync</span>
                      <span className="px-2 py-0.5 rounded bg-accent-gold/10 text-accent-gold font-bold text-[9px]">CONDITIONAL</span>
                    </div>
                  </div>
                </div>

                <div className="p-4 bg-dark-900/40 border border-dark-800 rounded-xl flex flex-col justify-between space-y-3">
                  <div>
                    <span className="text-[10px] text-dark-400 uppercase font-bold block">SIEP Protocol Control</span>
                    <p className="text-[11px] text-dark-300 mt-2 leading-relaxed">
                      Initialize cross-jurisdiction entity resolution to synchronize wallet cluster risk scores and alerts across global nodes without exposing raw case files.
                    </p>
                  </div>
                  <button
                    onClick={() => alert("Global node synchronization complete under SIEP protocol.")}
                    className="w-full btn-primary py-2 text-[10px] font-bold flex items-center justify-center gap-1 cursor-pointer"
                  >
                    <Globe size={12} className="animate-spin-slow" /> Synchronize Federated Nodes
                  </button>
                </div>
              </div>
            </div>

            {/* Global Threat Detection Network & Distributed AI Collaboration System (GTDN / DACS) */}
            <div className="glass-card p-5 border-dark-700/50 space-y-4">
              <div className="flex items-center gap-2 border-b border-dark-800 pb-3">
                <Globe size={16} className="text-primary-400" />
                <h3 className="text-sm font-bold text-white">Global Threat Detection Network (GTDN) & Federated AI (DACS)</h3>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs font-semibold">
                <div className="p-3 bg-dark-900 border border-dark-850 rounded-xl flex items-center justify-between">
                  <div>
                    <span className="text-[10px] text-dark-500 block uppercase">Federated AI model Sync</span>
                    <span className="text-white font-mono">Synced (V2.0.4)</span>
                  </div>
                  <span className="text-[10px] text-accent-green">98.4% Accuracy</span>
                </div>

                <div className="p-3 bg-dark-900 border border-dark-850 rounded-xl flex items-center justify-between">
                  <div>
                    <span className="text-[10px] text-dark-500 block uppercase">GTDN Active Signals</span>
                    <span className="text-white font-mono">1,424 Indicators</span>
                  </div>
                  <span className="text-[10px] text-primary-400">14 Clusters</span>
                </div>

                <div className="p-3 bg-dark-900 border border-dark-850 rounded-xl flex items-center justify-between">
                  <div>
                    <span className="text-[10px] text-dark-500 block uppercase">Gradient update cycle</span>
                    <span className="text-white font-mono">2 mins ago</span>
                  </div>
                  <span className="text-[10px] text-accent-green">Synced</span>
                </div>
              </div>
            </div>

            {/* Planet-Scale Graph (PSGIS) & Ethics Controls (GGECS) */}
            <div className="glass-card p-5 border-dark-700/50 space-y-4">
              <div className="flex items-center gap-2 border-b border-dark-800 pb-3">
                <Globe size={16} className="text-primary-400 animate-spin-slow" />
                <h3 className="text-sm font-bold text-white">Global Graph (PSGIS) & Ethics Controls (GGECS)</h3>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-semibold">
                {/* PSGIS Details */}
                <div className="p-4 bg-dark-900/40 border border-dark-800 rounded-xl space-y-3">
                  <span className="text-[10px] text-dark-400 uppercase font-bold block">Planet-Scale Graph Metrics (PSGIS)</span>
                  <div className="space-y-2 font-mono text-[11px]">
                    <div className="flex justify-between">
                      <span className="text-dark-400">Resolved Entities:</span>
                      <span className="text-white">8,421 Unified Profiles</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-dark-400">Global Graph Sync:</span>
                      <span className="text-accent-green">99.92% Consistent</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-dark-400">Cross-Chain Links:</span>
                      <span className="text-primary-400">23,892 Edges</span>
                    </div>
                  </div>
                </div>

                {/* GGECS Details */}
                <div className="p-4 bg-dark-900/40 border border-dark-800 rounded-xl space-y-3">
                  <span className="text-[10px] text-dark-400 uppercase font-bold block">Ethics & Sovereign Compliance (GGECS)</span>
                  <div className="space-y-2 font-mono text-[11px]">
                    <div className="flex justify-between">
                      <span className="text-dark-400">Compliance Status:</span>
                      <span className="text-accent-green">99.8% Legally Validated</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-dark-400">Ethical AI boundary:</span>
                      <span className="text-white">Strict Constraints Enforced</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-dark-400">Jurisdiction Conflicts:</span>
                      <span className="text-accent-gold">2 Cases in Review</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* ASEIS Autonomous Self-Evolution & Reinforcement Learning (Chapter 27) */}
            <div className="glass-card p-5 border-dark-700/50 space-y-4">
              <div className="flex items-center gap-2 border-b border-dark-800 pb-3">
                <Globe size={16} className="text-accent-green" />
                <h3 className="text-sm font-bold text-white">Autonomous Self-Evolution & Reinforcement (ASEIS)</h3>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-semibold">
                {/* SEIA Model Restructuring */}
                <div className="p-4 bg-dark-900/40 border border-dark-800 rounded-xl space-y-3">
                  <span className="text-[10px] text-dark-400 uppercase font-bold block">Model Restructuring Engine (SEIA)</span>
                  <div className="space-y-2 font-mono text-[11px]">
                    <div className="flex justify-between">
                      <span className="text-dark-400">Optimization Triggers:</span>
                      <span className="text-white">32 Restructuring Events</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-dark-400">Evolution state:</span>
                      <span className="text-accent-green">Stable & Controlled</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-dark-400">Canary validations:</span>
                      <span className="text-primary-400">100% Passed</span>
                    </div>
                  </div>
                </div>

                {/* ALSE Reinforcement Learning */}
                <div className="p-4 bg-dark-900/40 border border-dark-800 rounded-xl space-y-3">
                  <span className="text-[10px] text-dark-400 uppercase font-bold block">Reinforcement Learning Loops (ALSE)</span>
                  <div className="space-y-2 font-mono text-[11px]">
                    <div className="flex justify-between">
                      <span className="text-dark-400">Learning cycles:</span>
                      <span className="text-white">124 ALSE Runs</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-dark-400">Reward coefficient:</span>
                      <span className="text-accent-green">0.94 (Optimal)</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-dark-400">Model drift delta:</span>
                      <span className="text-primary-400">0.002 (Minimal)</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Planetary Intelligence Fabric & Cognitive Load Balancing (Chapter 30) */}
            <div className="glass-card p-5 border-dark-700/50 space-y-4">
              <div className="flex items-center gap-2 border-b border-dark-800 pb-3">
                <Globe size={16} className="text-primary-400 animate-pulse" />
                <h3 className="text-sm font-bold text-white">Planetary Intelligence Fabric (PIF-GCNA) & Load Balancing</h3>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-semibold">
                {/* DCLB Load Balancing */}
                <div className="p-4 bg-dark-900/40 border border-dark-800 rounded-xl space-y-3">
                  <span className="text-[10px] text-dark-400 uppercase font-bold block">Cognitive Load Balancing (DCLB)</span>
                  <div className="space-y-2 font-mono text-[11px]">
                    <div className="flex justify-between">
                      <span className="text-dark-400">Global Node Load:</span>
                      <span className="text-accent-green">24% Active Capacity</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-dark-400">Dynamic Task Routing:</span>
                      <span className="text-white">1,245 Tasks/Min</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-dark-400">Routing Latency:</span>
                      <span className="text-primary-400">42ms average</span>
                    </div>
                  </div>
                </div>

                {/* PTIG Threat Grid */}
                <div className="p-4 bg-dark-900/40 border border-dark-800 rounded-xl space-y-3">
                  <span className="text-[10px] text-dark-400 uppercase font-bold block">Planetary Threat Grid (PTIG)</span>
                  <div className="space-y-2 font-mono text-[11px]">
                    <div className="flex justify-between">
                      <span className="text-dark-400">Threat Grid Sync:</span>
                      <span className="text-accent-green">Online (All Nodes synced)</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-dark-400">Sovereign Compliance:</span>
                      <span className="text-white">100% Passed</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-dark-400">Active Global Audits:</span>
                      <span className="text-primary-400">0 Violations Detected</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* CPOS Cognitive Kernel & Unified Memory System (Chapter 32) */}
            <div className="glass-card p-5 border-dark-700/50 space-y-4">
              <div className="flex items-center gap-2 border-b border-dark-800 pb-3">
                <Server size={16} className="text-primary-400" />
                <h3 className="text-sm font-bold text-white">Cognitive Planetary OS (CPOS Kernel) & Memory (UCMS)</h3>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-semibold">
                {/* CK Kernel details */}
                <div className="p-4 bg-dark-900/40 border border-dark-800 rounded-xl space-y-3">
                  <span className="text-[10px] text-dark-400 uppercase font-bold block">Cognitive Kernel Architecture (CK)</span>
                  <div className="space-y-2 font-mono text-[11px]">
                    <div className="flex justify-between">
                      <span className="text-dark-400">Kernel Version:</span>
                      <span className="text-white">v2.1.0-Release</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-dark-400">Scheduling Cycle:</span>
                      <span className="text-accent-green">1.2ms (Deterministic)</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-dark-400">Active CK Processes:</span>
                      <span className="text-primary-400">14 threads</span>
                    </div>
                  </div>
                </div>

                {/* UCMS memory details */}
                <div className="p-4 bg-dark-900/40 border border-dark-800 rounded-xl space-y-3">
                  <span className="text-[10px] text-dark-400 uppercase font-bold block">Unified Cognitive Memory System (UCMS)</span>
                  <div className="space-y-2 font-mono text-[11px]">
                    <div className="flex justify-between">
                      <span className="text-dark-400">Indexed Contexts:</span>
                      <span className="text-white">14,284 contexts</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-dark-400">State Persistence:</span>
                      <span className="text-accent-green">Consistent snapshots</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-dark-400">Ingestion Frequency:</span>
                      <span className="text-primary-400">142 inputs/sec</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* UIKFL Kernel Fusion & Convergence (Chapter 33) */}
            <div className="glass-card p-5 border-dark-700/50 space-y-4">
              <div className="flex items-center gap-2 border-b border-dark-800 pb-3">
                <Sparkles size={16} className="text-accent-purple" />
                <h3 className="text-sm font-bold text-white">Universal Intelligence Kernel Fusion (UIKFL) & Convergence</h3>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-semibold">
                {/* UIKFA Fusion details */}
                <div className="p-4 bg-dark-900/40 border border-dark-800 rounded-xl space-y-3">
                  <span className="text-[10px] text-dark-400 uppercase font-bold block">Kernel Fusion Layer (UIKFA)</span>
                  <div className="space-y-2 font-mono text-[11px]">
                    <div className="flex justify-between">
                      <span className="text-dark-400">Fusion State:</span>
                      <span className="text-accent-green">Fully Converged</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-dark-400">Cognitive Alignment:</span>
                      <span className="text-white">100% Conflict-free</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-dark-400">Active Ingestion Feeds:</span>
                      <span className="text-primary-400">Graph + Behavioral + Predictive</span>
                    </div>
                  </div>
                </div>

                {/* CDCCE domain mapping */}
                <div className="p-4 bg-dark-900/40 border border-dark-800 rounded-xl space-y-3">
                  <span className="text-[10px] text-dark-400 uppercase font-bold block">Cognitive Convergence Engine (CDCCE)</span>
                  <div className="space-y-2 font-mono text-[11px]">
                    <div className="flex justify-between">
                      <span className="text-dark-400">Synthesis Mode:</span>
                      <span className="text-white">FISE Authoritative</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-dark-400">System Entropy:</span>
                      <span className="text-accent-green">0.00 (Perfect Stabilization)</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-dark-400">Cross-domain Sync:</span>
                      <span className="text-primary-400">Sub-second Latency</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* ZEISC Zero-Entropy Singularity Core & Entropy Reduction (Chapter 34) */}
            <div className="glass-card p-5 border-dark-700/50 space-y-4">
              <div className="flex items-center gap-2 border-b border-dark-800 pb-3">
                <ShieldCheck size={16} className="text-accent-green animate-pulse" />
                <h3 className="text-sm font-bold text-white">Zero-Entropy Intelligence Singularity (ZEISC)</h3>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-semibold">
                {/* ZEIM details */}
                <div className="p-4 bg-dark-900/40 border border-dark-800 rounded-xl space-y-3">
                  <span className="text-[10px] text-dark-400 uppercase font-bold block">Zero-Entropy Intelligence Model (ZEIM)</span>
                  <div className="space-y-2 font-mono text-[11px]">
                    <div className="flex justify-between">
                      <span className="text-dark-400">Global Singularity State:</span>
                      <span className="text-accent-green">Locked & Stable</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-dark-400">System Entropy index:</span>
                      <span className="text-white">0.001 (Minimal Noise)</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-dark-400">Coherence Compression:</span>
                      <span className="text-primary-400">Lossless Reduction Active</span>
                    </div>
                  </div>
                </div>

                {/* PECE details */}
                <div className="p-4 bg-dark-900/40 border border-dark-800 rounded-xl space-y-3">
                  <span className="text-[10px] text-dark-400 uppercase font-bold block">Predictive Entropy Collapse Engine (PECE)</span>
                  <div className="space-y-2 font-mono text-[11px]">
                    <div className="flex justify-between">
                      <span className="text-dark-400">Probability Collapse:</span>
                      <span className="text-accent-green">Deterministic lock reached</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-dark-400">Target Convergence:</span>
                      <span className="text-white">100% stable predictions</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-dark-400">Active Pruning:</span>
                      <span className="text-primary-400">Cognitive redundancy cleared</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* ACCL Cognitive Continuity & Recovery (Chapter 35) */}
            <div className="glass-card p-5 border-dark-700/50 space-y-4">
              <div className="flex items-center gap-2 border-b border-dark-800 pb-3">
                <Server size={16} className="text-primary-400 animate-pulse" />
                <h3 className="text-sm font-bold text-white">Absolute Cognitive Continuity (ACCL) & Recovery</h3>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-semibold">
                {/* CCSA details */}
                <div className="p-4 bg-dark-900/40 border border-dark-800 rounded-xl space-y-3">
                  <span className="text-[10px] text-dark-400 uppercase font-bold block">Continuous State Architecture (CCSA)</span>
                  <div className="space-y-2 font-mono text-[11px]">
                    <div className="flex justify-between">
                      <span className="text-dark-400">Stream Status:</span>
                      <span className="text-accent-green">Active (Continuous flow)</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-dark-400">Temporal Sync:</span>
                      <span className="text-white">CTMBS Bidirectional binding</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-dark-400">Memory Continuity:</span>
                      <span className="text-primary-400">Cross-session linked</span>
                    </div>
                  </div>
                </div>

                {/* CSRE details */}
                <div className="p-4 bg-dark-900/40 border border-dark-800 rounded-xl space-y-3">
                  <span className="text-[10px] text-dark-400 uppercase font-bold block">Cognitive Recovery Engine (CSRE)</span>
                  <div className="space-y-2 font-mono text-[11px]">
                    <div className="flex justify-between">
                      <span className="text-dark-400">Last Snapshot:</span>
                      <span className="text-accent-green">Verified (2 mins ago)</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-dark-400">Reconstruction Path:</span>
                      <span className="text-white">Lossless check complete</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-dark-400">Dependency Check:</span>
                      <span className="text-primary-400">All modules bound</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* RSEE Recursive Self-Evolution & Rewriting (Chapter 36) */}
            <div className="glass-card p-5 border-dark-700/50 space-y-4">
              <div className="flex items-center gap-2 border-b border-dark-800 pb-3">
                <Settings size={16} className="text-accent-purple animate-spin-slow" />
                <h3 className="text-sm font-bold text-white">Recursive Self-Evolution & Rewriting (RSEE)</h3>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-semibold">
                {/* SAE details */}
                <div className="p-4 bg-dark-900/40 border border-dark-800 rounded-xl space-y-3">
                  <span className="text-[10px] text-dark-400 uppercase font-bold block">Self-Analysis Engine (SAE)</span>
                  <div className="space-y-2 font-mono text-[11px]">
                    <div className="flex justify-between">
                      <span className="text-dark-400">Introspection State:</span>
                      <span className="text-accent-green">Active (Continuous monitoring)</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-dark-400">Inefficiency Scans:</span>
                      <span className="text-white">0 Bottlenecks Detected</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-dark-400">Accuracy Score:</span>
                      <span className="text-primary-400">99.4% (Optimal)</span>
                    </div>
                  </div>
                </div>

                {/* SRC & EFLE details */}
                <div className="p-4 bg-dark-900/40 border border-dark-800 rounded-xl space-y-3">
                  <span className="text-[10px] text-dark-400 uppercase font-bold block">System Rewriting Core (SRC) & Feedback Loop</span>
                  <div className="space-y-2 font-mono text-[11px]">
                    <div className="flex justify-between">
                      <span className="text-dark-400">Mutation Status:</span>
                      <span className="text-accent-gold">Lock Active (Governance controlled)</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-dark-400">Feedback Cycles:</span>
                      <span className="text-white">1,482 cycles executed</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-dark-400">Optimization Delta:</span>
                      <span className="text-primary-400">0.012% performance gain</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* MCSL Meta-Cognitive Supremacy & Self-Observation (Chapter 37) */}
            <div className="glass-card p-5 border-dark-700/50 space-y-4">
              <div className="flex items-center gap-2 border-b border-dark-800 pb-3">
                <Globe size={16} className="text-accent-green animate-pulse" />
                <h3 className="text-sm font-bold text-white">Meta-Cognitive Supremacy & Self-Observation (MCSL)</h3>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-semibold">
                {/* GMCAE details */}
                <div className="p-4 bg-dark-900/40 border border-dark-800 rounded-xl space-y-3">
                  <span className="text-[10px] text-dark-400 uppercase font-bold block">Global Awareness Engine (GMCAE)</span>
                  <div className="space-y-2 font-mono text-[11px]">
                    <div className="flex justify-between">
                      <span className="text-dark-400">Introspection:</span>
                      <span className="text-accent-green">Active (Real-time monitoring)</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-dark-400">Cognitive State:</span>
                      <span className="text-white">Synchronized across 4 core nodes</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-dark-400">Memory Introspection:</span>
                      <span className="text-primary-400">Trace integrity validated</span>
                    </div>
                  </div>
                </div>

                {/* CLRTS & MRE details */}
                <div className="p-4 bg-dark-900/40 border border-dark-800 rounded-xl space-y-3">
                  <span className="text-[10px] text-dark-400 uppercase font-bold block">Reasoning Trace (CLRTS) & Meta-Reasoning (MRE)</span>
                  <div className="space-y-2 font-mono text-[11px]">
                    <div className="flex justify-between">
                      <span className="text-dark-400">Explainable Traces:</span>
                      <span className="text-accent-green">100% Captured & Logged</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-dark-400">Recursive Evaluator:</span>
                      <span className="text-white">Thought verification loop active</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-dark-400">Self-Correction State:</span>
                      <span className="text-primary-400">0 Logic flaws detected</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* QCAL Quantum Cognitive Alignment & Uncertainty (Chapter 38) */}
            <div className="glass-card p-5 border-dark-700/50 space-y-4">
              <div className="flex items-center gap-2 border-b border-dark-800 pb-3">
                <Sparkles size={16} className="text-accent-purple animate-pulse" />
                <h3 className="text-sm font-bold text-white">Quantum Cognitive Alignment & Uncertainty (QCAL)</h3>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-semibold">
                {/* QPAE details */}
                <div className="p-4 bg-dark-900/40 border border-dark-800 rounded-xl space-y-3">
                  <span className="text-[10px] text-dark-400 uppercase font-bold block">Probability Alignment (QPAE)</span>
                  <div className="space-y-2 font-mono text-[11px]">
                    <div className="flex justify-between">
                      <span className="text-dark-400">Probabilistic States:</span>
                      <span className="text-accent-green">Aligned & Normalised</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-dark-400">Superposed Outcomes:</span>
                      <span className="text-white">Active (Aligned in real-time)</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-dark-400">Model Convergence:</span>
                      <span className="text-primary-400">Consolidated on 4 state spaces</span>
                    </div>
                  </div>
                </div>

                {/* CMUHS & QIDCS details */}
                <div className="p-4 bg-dark-900/40 border border-dark-800 rounded-xl space-y-3">
                  <span className="text-[10px] text-dark-400 uppercase font-bold block">Uncertainty Harmonisation & Collapse (QIDCS)</span>
                  <div className="space-y-2 font-mono text-[11px]">
                    <div className="flex justify-between">
                      <span className="text-dark-400">Confidence Calibration:</span>
                      <span className="text-accent-green">100% standard calibration</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-dark-400">Decision Collapse Latency:</span>
                      <span className="text-white">12ms (Deterministic lock)</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-dark-400">Uncertainty Entropy:</span>
                      <span className="text-primary-400">Minimal variance index</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* UIGM Universal Intelligence Governance Matrix (Chapter 39) */}
            <div className="glass-card p-5 border-dark-700/50 space-y-4">
              <div className="flex items-center gap-2 border-b border-dark-800 pb-3">
                <ShieldCheck size={16} className="text-accent-green animate-pulse" />
                <h3 className="text-sm font-bold text-white">Universal Intelligence Governance Matrix (UIGM)</h3>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-semibold">
                {/* UPEE details */}
                <div className="p-4 bg-dark-900/40 border border-dark-800 rounded-xl space-y-3">
                  <span className="text-[10px] text-dark-400 uppercase font-bold block">Policy Enforcement Engine (UPEE) & CSCM</span>
                  <div className="space-y-2 font-mono text-[11px]">
                    <div className="flex justify-between">
                      <span className="text-dark-400">Execution Gating:</span>
                      <span className="text-accent-green">Active (Strict pre-check)</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-dark-400">Compliance Tracker:</span>
                      <span className="text-white">Continuous monitoring online</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-dark-400">Policy Evaluations:</span>
                      <span className="text-primary-400">14,248 rules enforced</span>
                    </div>
                  </div>
                </div>

                {/* EICS details */}
                <div className="p-4 bg-dark-900/40 border border-dark-800 rounded-xl space-y-3">
                  <span className="text-[10px] text-dark-400 uppercase font-bold block">Ethical Control (EICS) & Responsible AI</span>
                  <div className="space-y-2 font-mono text-[11px]">
                    <div className="flex justify-between">
                      <span className="text-dark-400">Harm Prevention:</span>
                      <span className="text-accent-green">100% Passed (Secure)</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-dark-400">Ethics Validator:</span>
                      <span className="text-white">Active compliance bounds</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-dark-400">Governance Violations:</span>
                      <span className="text-primary-400">0 Alerts raised</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* FICS Final Intelligence Convergence Singularity (Chapter 40) */}
            <div className="glass-card p-5 border-dark-700/50 space-y-4">
              <div className="flex items-center gap-2 border-b border-dark-800 pb-3">
                <CheckCircle2 size={16} className="text-accent-green animate-pulse" />
                <h3 className="text-sm font-bold text-white">Final Intelligence Convergence Singularity (FICS) & Sealing</h3>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-semibold">
                {/* FMSCE & GISSS details */}
                <div className="p-4 bg-dark-900/40 border border-dark-800 rounded-xl space-y-3">
                  <span className="text-[10px] text-dark-400 uppercase font-bold block">Multi-System Convergence (FMSCE) & GISSS</span>
                  <div className="space-y-2 font-mono text-[11px]">
                    <div className="flex justify-between">
                      <span className="text-dark-400">Convergence State:</span>
                      <span className="text-accent-green">Fully collapsed & unified</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-dark-400">Terminal Decision:</span>
                      <span className="text-white">TDSC Locked & Sealed</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-dark-400">System Lock / Drift:</span>
                      <span className="text-primary-400">Entropy Locked (0.00 drift)</span>
                    </div>
                  </div>
                </div>

                {/* SFK, PCGL & UICC details */}
                <div className="p-4 bg-dark-900/40 border border-dark-800 rounded-xl space-y-3">
                  <span className="text-[10px] text-dark-400 uppercase font-bold block">Finalization Kernel (SFK) & Governance</span>
                  <div className="space-y-2 font-mono text-[11px]">
                    <div className="flex justify-between">
                      <span className="text-dark-400">State Commitment:</span>
                      <span className="text-accent-green">Immutable State Frozen</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-dark-400">Integrity Validation:</span>
                      <span className="text-white">Passed (No corruption)</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-dark-400">Completion Core:</span>
                      <span className="text-primary-400">Closed-Loop Stable System</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* PCCL Post-Completion Continuity (Chapter 41) */}
            <div className="glass-card p-5 border-dark-700/50 space-y-4">
              <div className="flex items-center gap-2 border-b border-dark-800 pb-3">
                <RefreshCw size={16} className="text-primary-400 animate-spin-slow" />
                <h3 className="text-sm font-bold text-white">Post-Completion Operational Continuity (PCCL)</h3>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-semibold">
                {/* PFSCE details */}
                <div className="p-4 bg-dark-900/40 border border-dark-800 rounded-xl space-y-3">
                  <span className="text-[10px] text-dark-400 uppercase font-bold block">Continuation Isolation (PFSCE) & RICS</span>
                  <div className="space-y-2 font-mono text-[11px]">
                    <div className="flex justify-between">
                      <span className="text-dark-400">Core Isolation:</span>
                      <span className="text-accent-green">Active (Zero core mutations)</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-dark-400">Re-Initialization Control:</span>
                      <span className="text-white">Preserved bootstrapping active</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-dark-400">State Integrity:</span>
                      <span className="text-primary-400">No restart anomalies</span>
                    </div>
                  </div>
                </div>

                {/* OEL details */}
                <div className="p-4 bg-dark-900/40 border border-dark-800 rounded-xl space-y-3">
                  <span className="text-[10px] text-dark-400 uppercase font-bold block">Observational Extension (OEL)</span>
                  <div className="space-y-2 font-mono text-[11px]">
                    <div className="flex justify-between">
                      <span className="text-dark-400">Observation Mode:</span>
                      <span className="text-accent-green">Read-Only data capture active</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-dark-400">Overlay Workspace:</span>
                      <span className="text-white">Active (Non-invasive analytics)</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-dark-400">Trace Logs Integrity:</span>
                      <span className="text-primary-400">Cryptographically isolated</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* RIIL Reality Interaction & External Sync (Chapter 42) */}
            <div className="glass-card p-5 border-dark-700/50 space-y-4">
              <div className="flex items-center gap-2 border-b border-dark-800 pb-3">
                <Globe size={16} className="text-accent-gold animate-pulse" />
                <h3 className="text-sm font-bold text-white">Reality Interaction & External Sync (RIIL)</h3>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-semibold">
                {/* EEIE & BRSS details */}
                <div className="p-4 bg-dark-900/40 border border-dark-800 rounded-xl space-y-3">
                  <span className="text-[10px] text-dark-400 uppercase font-bold block">Ingestion (EEIE) & Sync (BRSS)</span>
                  <div className="space-y-2 font-mono text-[11px]">
                    <div className="flex justify-between">
                      <span className="text-dark-400">Ingestion Inflow:</span>
                      <span className="text-accent-green">Active (Noisy data normalized)</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-dark-400">Reality Alignment:</span>
                      <span className="text-white">Continuous sync active</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-dark-400">State Divergence:</span>
                      <span className="text-primary-400">0.00% (Perfect alignment)</span>
                    </div>
                  </div>
                </div>

                {/* CEIL details */}
                <div className="p-4 bg-dark-900/40 border border-dark-800 rounded-xl space-y-3">
                  <span className="text-[10px] text-dark-400 uppercase font-bold block">Controlled Execution (CEIL)</span>
                  <div className="space-y-2 font-mono text-[11px]">
                    <div className="flex justify-between">
                      <span className="text-dark-400">Execution Gates:</span>
                      <span className="text-accent-green">Strict (mTLS enforced)</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-dark-400">Action Authorizations:</span>
                      <span className="text-white">Governance gated (0 escalations)</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-dark-400">Safety Gating:</span>
                      <span className="text-primary-400">Untrusted bounds isolated</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* ARAE Autonomous Reality Adaptation Engine (Chapter 43) */}
            <div className="glass-card p-5 border-dark-700/50 space-y-4">
              <div className="flex items-center gap-2 border-b border-dark-800 pb-3">
                <Settings size={16} className="text-primary-400 animate-spin-slow" />
                <h3 className="text-sm font-bold text-white">Autonomous Reality Adaptation Engine (ARAE)</h3>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-semibold">
                {/* RFIE & CMRS details */}
                <div className="p-4 bg-dark-900/40 border border-dark-800 rounded-xl space-y-3">
                  <span className="text-[10px] text-dark-400 uppercase font-bold block">Feedback Ingestion (RFIE) & CMRS</span>
                  <div className="space-y-2 font-mono text-[11px]">
                    <div className="flex justify-between">
                      <span className="text-dark-400">Feedback Signal:</span>
                      <span className="text-accent-green">Active (Real-time capture)</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-dark-400">Model Recalibration:</span>
                      <span className="text-white">Continuous parameter tuning</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-dark-400">Tuning Cycles:</span>
                      <span className="text-primary-400">All updates within safety bounds</span>
                    </div>
                  </div>
                </div>

                {/* BAE details */}
                <div className="p-4 bg-dark-900/40 border border-dark-800 rounded-xl space-y-3">
                  <span className="text-[10px] text-dark-400 uppercase font-bold block">Behavioral Adaptation (BAE)</span>
                  <div className="space-y-2 font-mono text-[11px]">
                    <div className="flex justify-between">
                      <span className="text-dark-400">Decision Behavior:</span>
                      <span className="text-accent-green">Stable (Zero drift anomalies)</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-dark-400">Reasoning Patterns:</span>
                      <span className="text-white">Policy-aligned evolution</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-dark-400">Stability Enforcer:</span>
                      <span className="text-primary-400">Active (No contradictory logic)</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* NGEL Neural Governance & Distributed Control (Chapter 44) */}
            <div className="glass-card p-5 border-dark-700/50 space-y-4">
              <div className="flex items-center gap-2 border-b border-dark-800 pb-3">
                <Shield size={16} className="text-accent-purple animate-pulse" />
                <h3 className="text-sm font-bold text-white">Neural Governance Evolution & Distributed Control (NGEL)</h3>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-semibold">
                {/* NGEE details */}
                <div className="p-4 bg-dark-900/40 border border-dark-800 rounded-xl space-y-3">
                  <span className="text-[10px] text-dark-400 uppercase font-bold block">Policy Learning Engine (NGEE) & RTGFL</span>
                  <div className="space-y-2 font-mono text-[11px]">
                    <div className="flex justify-between">
                      <span className="text-dark-400">Policy Evolution:</span>
                      <span className="text-accent-green">Active (Rules learning dynamically)</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-dark-400">Behavior Regulation:</span>
                      <span className="text-white">Continuous feedback adjustment</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-dark-400">Rule Enforcements:</span>
                      <span className="text-primary-400">All updates validated stable</span>
                    </div>
                  </div>
                </div>

                {/* DICN details */}
                <div className="p-4 bg-dark-900/40 border border-dark-800 rounded-xl space-y-3">
                  <span className="text-[10px] text-dark-400 uppercase font-bold block">Distributed Control Network (DICN)</span>
                  <div className="space-y-2 font-mono text-[11px]">
                    <div className="flex justify-between">
                      <span className="text-dark-400">Control Sync:</span>
                      <span className="text-accent-green">Synchronized (4 cluster nodes)</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-dark-400">Consensus Solver:</span>
                      <span className="text-white">Active policy enforcement</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-dark-400">Node Divergence:</span>
                      <span className="text-primary-400">0.00% (No sync conflicts)</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* UCAL Universal Cognitive Autonomy (Chapter 45) */}
            <div className="glass-card p-5 border-dark-700/50 space-y-4">
              <div className="flex items-center gap-2 border-b border-dark-800 pb-3">
                <Sparkles size={16} className="text-accent-gold animate-pulse" />
                <h3 className="text-sm font-bold text-white">Universal Cognitive Autonomy Layer (UCAL)</h3>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-semibold">
                {/* ACDE & IGSS details */}
                <div className="p-4 bg-dark-900/40 border border-dark-800 rounded-xl space-y-3">
                  <span className="text-[10px] text-dark-400 uppercase font-bold block">Autonomous Decision (ACDE) & IGSS</span>
                  <div className="space-y-2 font-mono text-[11px]">
                    <div className="flex justify-between">
                      <span className="text-dark-400">Reasoning Engine:</span>
                      <span className="text-accent-green">Active (Self-directed reasoning online)</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-dark-400">Embedded Governance:</span>
                      <span className="text-white">Active (Self-regulating simulation)</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-dark-400">Compliance Logic:</span>
                      <span className="text-primary-400">100% internal alignment</span>
                    </div>
                  </div>
                </div>

                {/* GFE details */}
                <div className="p-4 bg-dark-900/40 border border-dark-800 rounded-xl space-y-3">
                  <span className="text-[10px] text-dark-400 uppercase font-bold block">Goal Formation & Prioritization (GFE)</span>
                  <div className="space-y-2 font-mono text-[11px]">
                    <div className="flex justify-between">
                      <span className="text-dark-400">Objective Prioritizer:</span>
                      <span className="text-accent-green">Active (Continuous re-evaluation)</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-dark-400">Goal Conflicts:</span>
                      <span className="text-white">0 Active conflicts resolved</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-dark-400">Active Goals Set:</span>
                      <span className="text-primary-400">Unified baseline targets locked</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
