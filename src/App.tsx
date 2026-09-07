import React, { useEffect, lazy, Suspense } from 'react';
import { useAuthStore, useNavStore, useAlertStore } from './stores';
import { WS_BASE } from './utils/api';
import { LayoutDashboard, FolderOpen, Search, Bell, Sparkles } from 'lucide-react';
import { LoginPage } from './pages/LoginPage';
import { Sidebar } from './components/layout/Sidebar';
import { Header } from './components/layout/Header';
import { StatusBar } from './components/layout/StatusBar';
import { ShortcutsModal } from './components/modals/ShortcutsModal';

// Lazy-loaded pages for extreme speed and code-splitting performance
const DashboardPage = lazy(() => import('./pages/DashboardPage').then(m => ({ default: m.DashboardPage })));
const CasesPage = lazy(() => import('./pages/CasesPage').then(m => ({ default: m.CasesPage })));
const BlockchainPage = lazy(() => import('./pages/BlockchainPage').then(m => ({ default: m.BlockchainPage })));
const GraphPage = lazy(() => import('./pages/GraphPage').then(m => ({ default: m.GraphPage })));
const EvidencePage = lazy(() => import('./pages/EvidencePage').then(m => ({ default: m.EvidencePage })));
const WatchlistPage = lazy(() => import('./pages/WatchlistPage').then(m => ({ default: m.WatchlistPage })));
const AlertsPage = lazy(() => import('./pages/AlertsPage').then(m => ({ default: m.AlertsPage })));
const ReportsPage = lazy(() => import('./pages/ReportsPage').then(m => ({ default: m.ReportsPage })));
const AIWorkspacePage = lazy(() => import('./pages/AIWorkspacePage').then(m => ({ default: m.AIWorkspacePage })));
const EntityIntelligencePage = lazy(() => import('./pages/EntityIntelligencePage').then(m => ({ default: m.EntityIntelligencePage })));
const AuditPage = lazy(() => import('./pages/AuditPage').then(m => ({ default: m.AuditPage })));
const SettingsPage = lazy(() => import('./pages/SettingsPage').then(m => ({ default: m.SettingsPage })));
const IncidentResponsePage = lazy(() => import('./pages/IncidentResponsePage').then(m => ({ default: m.IncidentResponsePage })));
const SocDashboardPage = lazy(() => import('./pages/SocDashboardPage').then(m => ({ default: m.SocDashboardPage })));

import { NotFoundPage } from './pages/NotFoundPage';

// ─── Error Boundary ─────────────────────────────────────────────────────────
interface ErrorBoundaryState { hasError: boolean; error: Error | null }
class ErrorBoundary extends React.Component<React.PropsWithChildren, ErrorBoundaryState> {
  constructor(props: React.PropsWithChildren) {
    super(props);
    this.state = { hasError: false, error: null };
  }
  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }
  componentDidCatch(error: Error, info: React.ErrorInfo) {
    console.error('[LEATrace] Uncaught render error:', error, info);
  }
  render() {
    if (this.state.hasError) {
      return (
        <NotFoundPage
          errorTitle="System Error Encountered"
          errorMessage={this.state.error?.message || "An unexpected error occurred. The requested module has drifted out of orbit."}
          onRetry={() => { this.setState({ hasError: false, error: null }); window.location.reload(); }}
        />
      );
    }
    return this.props.children;
  }
}

// Page Fallback Loader
const PageLoader: React.FC = () => (
  <div className="flex items-center justify-center h-64 w-full">
    <div className="flex flex-col items-center gap-3">
      <div className="w-8 h-8 border-2 border-primary-500/30 border-t-primary-400 rounded-full animate-spin" />
      <span className="text-xs font-mono text-dark-400">Loading module...</span>
    </div>
  </div>
);

const App: React.FC = () => {
  const { isAuthenticated, hydrateAuth } = useAuthStore();
  const { currentPage, sidebarOpen, setPage, showShortcuts, setShowShortcuts } = useNavStore();
  const { alerts } = useAlertStore();
  const unreadCount = alerts.filter((a) => !a.isRead).length;

  // Hydrate authentication from localStorage on mount
  useEffect(() => {
    hydrateAuth();
  }, [hydrateAuth]);

  // Background idle route preloader for 0ms tab navigation
  useEffect(() => {
    const preloadRoutes = () => {
      import('./pages/DashboardPage');
      import('./pages/CasesPage');
      import('./pages/BlockchainPage');
      import('./pages/GraphPage');
      import('./pages/EvidencePage');
      import('./pages/WatchlistPage');
      import('./pages/AlertsPage');
      import('./pages/ReportsPage');
      import('./pages/AIWorkspacePage');
      import('./pages/EntityIntelligencePage');
      import('./pages/AuditPage');
      import('./pages/SettingsPage');
      import('./pages/IncidentResponsePage');
      import('./pages/SocDashboardPage');
    };

    if ('requestIdleCallback' in window) {
      (window as any).requestIdleCallback(preloadRoutes);
    } else {
      setTimeout(preloadRoutes, 150);
    }
  }, []);

  // Real-time Event Streaming System WebSocket hook
  useEffect(() => {
    if (!isAuthenticated) return;

    let ws: WebSocket | null = null;
    let reconnectTimeout: any = null;
    let heartbeatInterval: any = null;

    const connectWebSocket = () => {
      try {
        const token = localStorage.getItem('token');
        if (!token) return;

        ws = new WebSocket(`${WS_BASE}/api/streaming/alerts?token=${token}`);

        ws.onopen = () => {
          console.log('[WebSocket] Real-time event alert stream connected.');

          heartbeatInterval = setInterval(() => {
            if (ws && ws.readyState === WebSocket.OPEN) {
              ws.send(JSON.stringify({ type: 'ping' }));
            }
          }, 30000);
        };

        ws.onmessage = (event) => {
          try {
            const rawAlert = JSON.parse(event.data);
            if (rawAlert.type === 'pong') return;

            const mappedAlert = {
              id: rawAlert.id,
              severity: rawAlert.severity || 'high',
              type: rawAlert.type || 'real-time',
              message: rawAlert.message || '',
              address: rawAlert.address,
              isRead: false,
              createdAt: rawAlert.timestamp || new Date().toISOString(),
              chain: rawAlert.chain
            };

            useAlertStore.setState((state) => ({
              alerts: [mappedAlert, ...state.alerts]
            }));
          } catch {
            // Ignore parse errors
          }
        };

        ws.onclose = () => {
          if (heartbeatInterval) clearInterval(heartbeatInterval);
        };

        ws.onerror = () => {
          ws?.close();
        };

      } catch {
        // Suppress unhandled network exceptions when offline
      }
    };

    connectWebSocket();

    return () => {
      if (ws) ws.close();
      if (reconnectTimeout) clearTimeout(reconnectTimeout);
      if (heartbeatInterval) clearInterval(heartbeatInterval);
    };
  }, [isAuthenticated]);

  // Global keyboard shortcuts listener
  useEffect(() => {
    if (!isAuthenticated) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      // Ctrl + K -> Focus Search
      if (e.ctrlKey && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        const searchInput = document.getElementById('global-search-input');
        if (searchInput) {
          searchInput.focus();
        }
      }

      // Ctrl + N -> Go to Cases
      if (e.ctrlKey && e.key.toLowerCase() === 'n') {
        e.preventDefault();
        setPage('cases');
      }

      // Ctrl + E -> Go to Evidence
      if (e.ctrlKey && e.key.toLowerCase() === 'e') {
        e.preventDefault();
        setPage('evidence');
      }

      // Ctrl + R -> Go to Reports
      if (e.ctrlKey && e.key.toLowerCase() === 'r') {
        e.preventDefault();
        setPage('reports');
      }

      // Ctrl + G -> Go to Graph
      if (e.ctrlKey && e.key.toLowerCase() === 'g') {
        e.preventDefault();
        setPage('graph');
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isAuthenticated, setPage]);

  if (!isAuthenticated) {
    return <LoginPage />;
  }

  // Page dispatcher mapping nav-ids to components
  const renderPage = () => {
    switch (currentPage) {
      case 'dashboard':
        return <DashboardPage />;
      case 'cases':
        return <CasesPage />;
      case 'blockchain':
        return <BlockchainPage />;
      case 'graph':
        return <GraphPage />;
      case 'evidence':
        return <EvidencePage />;
      case 'watchlist':
        return <WatchlistPage />;
      case 'alerts':
        return <AlertsPage />;
      case 'reports':
        return <ReportsPage />;
      case 'ai':
        return <AIWorkspacePage />;
      case 'entities':
        return <EntityIntelligencePage />;
      case 'audit':
        return <AuditPage />;
      case 'settings':
        return <SettingsPage />;
      case 'incident':
        return <IncidentResponsePage />;
      case 'soc':
        return <SocDashboardPage />;
      case '404':
        return <NotFoundPage />;
      default:
        return <DashboardPage />;
    }
  };

  return (
    <div className="min-h-[100dvh] bg-dark-950 text-white flex flex-col relative overflow-x-hidden">
      <div className="flex flex-1 min-w-0 max-w-full">
        {/* Navigation Sidebar */}
        <Sidebar />

        {/* Mobile Sidebar Backdrop Overlay */}
        {sidebarOpen && (
          <div
            className="fixed inset-0 bg-black/70 backdrop-blur-sm z-[105] md:hidden cursor-pointer animate-fade-in"
            onClick={() => useNavStore.setState({ sidebarOpen: false })}
          />
        )}

        {/* Main content body */}
        <div
          className={`flex-1 flex flex-col min-h-[100dvh] pb-20 md:pb-8 transition-snappy gpu-accelerated pl-0 min-w-0 max-w-full overflow-x-hidden
            ${sidebarOpen ? 'md:pl-64' : 'md:pl-[72px]'}`}
        >
          <Header />
          <main className="flex-1 p-3 sm:p-6 mt-16 overflow-y-auto min-w-0 max-w-full">
            <Suspense fallback={<PageLoader />}>
              {renderPage()}
            </Suspense>
          </main>
        </div>
      </div>

      {/* Bottom Mobile Navigation */}
      <div className="fixed bottom-0 left-0 right-0 h-16 bg-dark-900/90 backdrop-blur-xl border-t border-dark-700/50 flex items-center justify-around md:hidden z-[100] safe-bottom">
        <button
          onClick={() => setPage('dashboard')}
          className={`flex flex-col items-center gap-1 text-[10px] font-medium transition-colors ${currentPage === 'dashboard' ? 'text-primary-400 font-semibold' : 'text-dark-400 hover:text-white'}`}
        >
          <LayoutDashboard size={20} />
          <span>Dashboard</span>
        </button>
        <button
          onClick={() => setPage('cases')}
          className={`flex flex-col items-center gap-1 text-[10px] font-medium transition-colors ${currentPage === 'cases' ? 'text-primary-400 font-semibold' : 'text-dark-400 hover:text-white'}`}
        >
          <FolderOpen size={20} />
          <span>Cases</span>
        </button>
        <button
          onClick={() => setPage('blockchain')}
          className={`flex flex-col items-center gap-1 text-[10px] font-medium transition-colors ${currentPage === 'blockchain' ? 'text-primary-400 font-semibold' : 'text-dark-400 hover:text-white'}`}
        >
          <Search size={20} />
          <span>Search</span>
        </button>
        <button
          onClick={() => setPage('alerts')}
          className={`flex flex-col items-center gap-1 text-[10px] font-medium transition-colors relative ${currentPage === 'alerts' ? 'text-primary-400 font-semibold' : 'text-dark-400 hover:text-white'}`}
        >
          <Bell size={20} />
          {unreadCount > 0 && (
            <span className="absolute top-0 right-1 w-4 h-4 bg-accent-red rounded-full text-[9px] font-bold flex items-center justify-center text-white">
              {unreadCount}
            </span>
          )}
          <span>Alerts</span>
        </button>
        <button
          onClick={() => setPage('ai')}
          className={`flex flex-col items-center gap-1 text-[10px] font-medium transition-colors ${currentPage === 'ai' ? 'text-primary-400 font-semibold' : 'text-dark-400 hover:text-white'}`}
        >
          <Sparkles size={20} />
          <span>AI Workspace</span>
        </button>
      </div>

      {/* Dynamic Background Task Status Bar */}
      <StatusBar />
      <ShortcutsModal isOpen={showShortcuts} onClose={() => setShowShortcuts(false)} />
    </div>
  );
};

export default function AppWithBoundary() {
  return (
    <ErrorBoundary>
      <App />
    </ErrorBoundary>
  );
}

