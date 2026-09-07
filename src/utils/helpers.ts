import { clsx } from 'clsx';
export function cn(...inputs: (string | undefined | null | false)[]) {
  return clsx(inputs);
}
export function formatAddress(addr: string, chars = 6): string {
  if (!addr) return '';
  return `${addr.slice(0, chars + 2)}...${addr.slice(-chars)}`;
}
export function formatETH(value: number): string {
  return `${value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 4 })} ETH`;
}
export function formatCrypto(value: number, coin: string): string {
  const symbol = coin.includes('/') ? 'ETH' : coin;
  return `${value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 4 })} ${symbol}`;
}
export function formatUSD(value: number): string {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(value);
}
export function formatDate(date: string): string {
  return new Date(date).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' });
}
export function timeAgo(date: string): string {
  const seconds = Math.floor((Date.now() - new Date(date).getTime()) / 1000);
  if (seconds < 60) return `${seconds}s ago`;
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}
export function getRiskColor(score: number): string {
  if (score >= 80) return 'text-accent-red';
  if (score >= 60) return 'text-accent-gold';
  if (score >= 40) return 'text-primary-400';
  return 'text-accent-green';
}
export function getRiskBg(score: number): string {
  if (score >= 80) return 'bg-accent-red';
  if (score >= 60) return 'bg-accent-gold';
  if (score >= 40) return 'bg-primary-400';
  return 'bg-accent-green';
}
export function getSeverityColor(severity: string): string {
  switch (severity) {
    case 'critical': return 'text-accent-red';
    case 'high': return 'text-accent-gold';
    case 'medium': return 'text-primary-400';
    case 'low': return 'text-accent-green';
    default: return 'text-dark-300';
  }
}
export function getStatusColor(status: string): string {
  switch (status) {
    case 'active': return 'badge-green';
    case 'open': return 'badge-cyan';
    case 'suspended': return 'badge-gold';
    case 'closed': return 'badge-purple';
    default: return 'badge-cyan';
  }
}
export function getPriorityColor(priority: string): string {
  switch (priority) {
    case 'critical': return 'badge-red';
    case 'high': return 'badge-gold';
    case 'medium': return 'badge-cyan';
    case 'low': return 'badge-green';
    default: return 'badge-cyan';
  }
}

export function detectBlockchainFromAddress(address: string): { chain: string; coin: string; displayName: string } {
  const cleanAddr = address.trim();
  if (!cleanAddr) return { chain: 'unknown', coin: 'unknown', displayName: 'Unknown' };

  // Bitcoin Legacy (starts with 1)
  if (/^1[a-km-zA-HJ-NP-Z1-9]{25,34}$/.test(cleanAddr)) {
    return { chain: 'bitcoin', coin: 'BTC', displayName: 'Bitcoin Legacy (P2PKH)' };
  }

  // Bitcoin Nested SegWit (starts with 3)
  if (/^3[a-km-zA-HJ-NP-Z1-9]{25,34}$/.test(cleanAddr)) {
    return { chain: 'bitcoin', coin: 'BTC', displayName: 'Bitcoin Nested SegWit (P2SH)' };
  }

  // Bitcoin Native SegWit (starts with bc1q)
  if (/^bc1q[ac-qpzry9x8gf2tvdw0s3jn54khce6mua7l]{38,59}$/i.test(cleanAddr)) {
    return { chain: 'bitcoin', coin: 'BTC', displayName: 'Bitcoin Native SegWit (Bech32)' };
  }

  // Bitcoin Taproot (starts with bc1p)
  if (/^bc1p[ac-qpzry9x8gf2tvdw0s3jn54khce6mua7l]{38,59}$/i.test(cleanAddr)) {
    return { chain: 'bitcoin', coin: 'BTC', displayName: 'Bitcoin Taproot (Bech32m)' };
  }

  // Generic/Other Bitcoin SegWit address
  if (/^bc1[ac-qpzry9x8gf2tvdw0s3jn54khce6mua7l]{39,59}$/i.test(cleanAddr)) {
    return { chain: 'bitcoin', coin: 'BTC', displayName: 'Bitcoin SegWit (Bech32)' };
  }

  // Ethereum / EVM patterns (Polygon, BSC)
  if (/^0x[a-fA-F0-9]{40}$/.test(cleanAddr)) {
    return { chain: 'ethereum', coin: 'ETH/MATIC/BSC', displayName: 'EVM compatible (Ethereum / Polygon / BSC)' };
  }

  // Solana pattern
  if (/^[1-9A-HJ-NP-Za-km-z]{32,44}$/.test(cleanAddr)) {
    return { chain: 'solana', coin: 'SOL', displayName: 'Solana (SOL)' };
  }

  // Ripple (XRP)
  if (/^r[0-9a-zA-Z]{24,34}$/.test(cleanAddr)) {
    return { chain: 'ripple', coin: 'XRP', displayName: 'Ripple (XRP)' };
  }

  // Cardano (ADA)
  if (/^addr1[a-z0-9]+/i.test(cleanAddr)) {
    return { chain: 'cardano', coin: 'ADA', displayName: 'Cardano (ADA)' };
  }

  if (cleanAddr.startsWith('0x')) {
    return { chain: 'ethereum', coin: 'EVM', displayName: 'EVM compatible Chain' };
  }

  return { chain: 'unknown', coin: 'unknown', displayName: 'Unknown Coin' };
}
