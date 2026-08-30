import { lazy, Suspense } from "react";
import { AppProvider, useApp } from "./context/AppContext";
import { Navbar } from "./components/Navbar";
import { Footer } from "./components/Footer";
import { AchievementToast } from "./components/AchievementToast";
import { AuroraBackground } from "./components/fx/AuroraBackground";
import { ScrollProgress } from "./components/fx/ScrollProgress";

/* ── Lazy-loaded pages (code-split into separate chunks) ── */
const Home = lazy(() => import("./pages/Home").then((m) => ({ default: m.Home })));
const Labs = lazy(() => import("./pages/Labs").then((m) => ({ default: m.Labs })));
const Learning = lazy(() => import("./pages/Learning").then((m) => ({ default: m.Learning })));
const Resources = lazy(() => import("./pages/Resources").then((m) => ({ default: m.Resources })));
const Dashboard = lazy(() => import("./pages/Dashboard").then((m) => ({ default: m.Dashboard })));
const Progress = lazy(() => import("./pages/Progress").then((m) => ({ default: m.Progress })));
const Achievements = lazy(() => import("./pages/Achievements").then((m) => ({ default: m.Achievements })));
const About = lazy(() => import("./pages/About").then((m) => ({ default: m.About })));
const Safety = lazy(() => import("./pages/Safety").then((m) => ({ default: m.Safety })));
const Privacy = lazy(() => import("./pages/Privacy").then((m) => ({ default: m.Privacy })));
const NotFound = lazy(() => import("./pages/NotFound").then((m) => ({ default: m.NotFound })));
const LabWorkspace = lazy(() => import("./pages/LabWorkspace").then((m) => ({ default: m.LabWorkspace })));

/* Minimal loading spinner shown while a lazy chunk is fetched */
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
