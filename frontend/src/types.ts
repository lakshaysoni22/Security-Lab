export interface User {
  id: string;
  email: string;
  username: string;
  role: string;
  isActive: boolean;
  mfaEnabled: boolean;
  createdAt: string;
  lastLogin?: string;
  department?: string;
}

export interface Case {
  id: string;
  caseNumber: string;
  title: string;
  description: string;
  priority: 'low' | 'medium' | 'high' | 'critical';
  status: 'open' | 'active' | 'suspended' | 'closed';
  investigatorId: string;
  investigatorName: string;
  department: string;
  notes?: string;
  createdAt: string;
  updatedAt: string;
  closedAt?: string;
  walletCount: number;
  evidenceCount: number;
}

export interface RiskIndicator {
  type: string;
  severity: 'critical' | 'high' | 'medium' | 'low';
  description: string;
  score: number;
}

export interface WalletProfile {
  address: string;
  chain: string;
  balance: number;
  balanceUSD: number;
  totalTransactions: number;
  incomingTxns: number;
  outgoingTxns: number;
  firstActivity: string;
  lastActivity: string;
  totalVolumeIn: number;
  totalVolumeOut: number;
  riskScore: number;
  riskIndicators: RiskIndicator[];
  tags: string[];
  isContract: boolean;
  label?: string;
  decentralizationLevel?: number;
}

export interface Transaction {
  hash: string;
  from: string;
  to: string;
  value: number;
  valueUSD: number;
  gasUsed: number;
  gasPrice: number;
  timestamp: string;
  blockNumber: number;
  chain: string;
  status: string;
  method?: string;
}

export interface Evidence {
  id: string;
  caseId: string;
  type?: string;
  title?: string;
  filename?: string;
  fileSize?: string;
  fileHash?: string;
  uploadedBy: string;
  uploadedByName?: string;
  uploadTime?: string;
  createdAt?: string;
  description?: string;
  downloadUrl?: string;
  chainOfCustody?: any[];
  metadata?: any;
}

export interface WatchlistEntry {
  id: string;
  address: string;
  chain: string;
  alias?: string;
  riskScore?: number;
  status: string;
  createdAt: string;
  tag?: string;
  category?: string;
  notes?: string;
  addedBy?: string;
  lastActivity?: string;
  alertCount?: number;
}

export interface Alert {
  id: string;
  watchlistId?: string;
  severity: 'critical' | 'high' | 'medium' | 'low';
  type: string;
  message: string;
  address?: string;
  isRead: boolean;
  createdAt: string;
  chain?: string;
}

export interface AuditLog {
  id: string;
  userId?: string;
  userName?: string;
  username?: string;
  role?: string;
  action: string;
  resource?: string;
  resourceId?: string;
  ipAddress: string;
  caseRef?: string;
  createdAt?: string;
  timestamp?: string;
  status?: string;
}

export interface DashboardStats {
  activeCases: number;
  openInvestigations: number;
  watchedWallets: number;
  totalEvidence: number;
  recentAlerts: number;
  totalUsers: number;
  casesThisMonth: number;
  closedCases: number;
}

export interface TimelineEntry {
  id: string;
  type: string;
  title: string;
  description: string;
  timestamp: string;
  user: string;
  caseRef?: string;
}

export interface Report {
  id: string;
  caseId: string;
  caseNumber: string;
  title: string;
  format: string;
  generatedBy: string;
  createdAt: string;
  fileSize: string;
}

export interface GraphNode {
  id: string;
  label: string;
  type: string;
  balance?: number;
  riskScore?: number;
  tags?: string[];
}

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  value: number;
  txCount?: number;
}
