import { AppProvider, useApp } from "./context/AppContext";
import { Navbar } from "./components/Navbar";
import { Footer } from "./components/Footer";
import { AchievementToast } from "./components/AchievementToast";
import { AuroraBackground } from "./components/fx/AuroraBackground";
import { ScrollProgress } from "./components/fx/ScrollProgress";
import { Home } from "./pages/Home";
import { Labs } from "./pages/Labs";
import { Learning } from "./pages/Learning";
import { Resources } from "./pages/Resources";
import { Dashboard } from "./pages/Dashboard";
import { Progress } from "./pages/Progress";
import { Achievements } from "./pages/Achievements";
import { About } from "./pages/About";
import { Safety } from "./pages/Safety";
import { NotFound } from "./pages/NotFound";
import { LabWorkspace } from "./pages/LabWorkspace";

function CurrentView() {
  const { route } = useApp();
  switch (route.name) {
    case "home":
      return <Home />;
    case "labs":
      return <Labs />;
    case "learning":
      return <Learning />;
    case "resources":
      return <Resources />;
    case "dashboard":
      return <Dashboard />;
    case "progress":
      return <Progress />;
    case "achievements":
      return <Achievements />;
    case "about":
      return <About />;
    case "safety":
      return <Safety />;
    case "lab":
      return <LabWorkspace labId={route.labId} />;
    case "notfound":
    default:
      return <NotFound />;
  }
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
