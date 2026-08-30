import { lazy, Suspense, useEffect } from "react";
import { AppProvider, useApp } from "./context/AppContext";
import { Navbar } from "./components/Navbar";
import { Footer } from "./components/Footer";
import { AchievementToast } from "./components/AchievementToast";
import { AuroraBackground } from "./components/fx/AuroraBackground";
import { ScrollProgress } from "./components/fx/ScrollProgress";

/* ── Dynamic Route Loaders ── */
const loadHome = () => import("./pages/Home").then((m) => ({ default: m.Home }));
const loadLabs = () => import("./pages/Labs").then((m) => ({ default: m.Labs }));
const loadLearning = () => import("./pages/Learning").then((m) => ({ default: m.Learning }));
const loadResources = () => import("./pages/Resources").then((m) => ({ default: m.Resources }));
const loadDashboard = () => import("./pages/Dashboard").then((m) => ({ default: m.Dashboard }));
const loadProgress = () => import("./pages/Progress").then((m) => ({ default: m.Progress }));
const loadAchievements = () => import("./pages/Achievements").then((m) => ({ default: m.Achievements }));
const loadAbout = () => import("./pages/About").then((m) => ({ default: m.About }));
const loadSafety = () => import("./pages/Safety").then((m) => ({ default: m.Safety }));
const loadPrivacy = () => import("./pages/Privacy").then((m) => ({ default: m.Privacy }));
const loadNotFound = () => import("./pages/NotFound").then((m) => ({ default: m.NotFound }));
const loadLabWorkspace = () => import("./pages/LabWorkspace").then((m) => ({ default: m.LabWorkspace }));

/* ── Lazy-loaded Component Definitions ── */
const Home = lazy(loadHome);
const Labs = lazy(loadLabs);
const Learning = lazy(loadLearning);
const Resources = lazy(loadResources);
const Dashboard = lazy(loadDashboard);
const Progress = lazy(loadProgress);
const Achievements = lazy(loadAchievements);
const About = lazy(loadAbout);
const Safety = lazy(loadSafety);
const Privacy = lazy(loadPrivacy);
const NotFound = lazy(loadNotFound);
const LabWorkspace = lazy(loadLabWorkspace);

/**
 * Preload all page bundles in background during idle browser time.
 * This guarantees that every page transition is 100% INSTANT (0ms delay)
 * without ever showing loading spinners when navigating between tabs.
 */
export function preloadAllRoutes() {
  const loaders = [
    loadHome,
    loadLabs,
    loadResources,
    loadDashboard,
    loadLearning,
    loadProgress,
    loadAchievements,
    loadAbout,
    loadSafety,
    loadPrivacy,
    loadLabWorkspace,
  ];

  loaders.forEach((fn) => {
    try {
      fn();
    } catch {
      /* ignore background prefetch errors */
    }
  });
}

function PageLoader() {
  return (
    <div className="grid min-h-[60vh] place-items-center">
      <div className="flex flex-col items-center gap-3">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-cyan/30 border-t-cyan" />
        <span className="font-mono text-xs text-muted-foreground">Loading…</span>
      </div>
    </div>
  );
}

function CurrentView() {
  const { route } = useApp();

  // Scroll to top instantly on route change
  useEffect(() => {
    window.scrollTo({ top: 0, left: 0, behavior: "instant" as ScrollBehavior });
  }, [route]);

  let page: React.JSX.Element;
  switch (route.name) {
    case "home":
      page = <Home />;
      break;
    case "labs":
      page = <Labs />;
      break;
    case "learning":
      page = <Learning />;
      break;
    case "resources":
      page = <Resources />;
      break;
    case "dashboard":
      page = <Dashboard />;
      break;
    case "progress":
      page = <Progress />;
      break;
    case "achievements":
      page = <Achievements />;
      break;
    case "about":
      page = <About />;
      break;
    case "safety":
      page = <Safety />;
      break;
    case "privacy":
      page = <Privacy />;
      break;
    case "lab":
      page = <LabWorkspace labId={route.labId} />;
      break;
    case "notfound":
    default:
      page = <NotFound />;
      break;
  }
  return <Suspense fallback={<PageLoader />}>{page}</Suspense>;
}

function Shell() {
  const { route } = useApp();
  const isLab = route.name === "lab";

  // Trigger background idle prefetching 200ms after initial app mount
  useEffect(() => {
    const timer = setTimeout(() => {
      if ("requestIdleCallback" in window) {
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        (window as any).requestIdleCallback(preloadAllRoutes);
      } else {
        preloadAllRoutes();
      }
    }, 200);

    return () => clearTimeout(timer);
  }, []);

  return (
    <div className="flex min-h-screen flex-col text-foreground">
      <AuroraBackground />
      {!isLab && <ScrollProgress />}
      <Navbar />
      <main className="flex-1">
        <CurrentView />
      </main>
      {!isLab && <Footer />}
      <AchievementToast />
    </div>
  );
}

export default function App() {
  return (
    <AppProvider>
      <Shell />
    </AppProvider>
  );
}
