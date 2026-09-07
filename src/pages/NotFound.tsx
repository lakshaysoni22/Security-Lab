import { useApp } from "../context/AppContext";
import { Icon } from "../components/ui/Icon";
import { PremiumButton } from "../components/ui/primitives";

export function NotFound() {
  const { navigate } = useApp();
  return (
    <div className="mx-auto grid min-h-[70vh] max-w-2xl place-items-center px-5 pt-28 text-center sm:px-8">
      <div>
        <div className="relative mx-auto grid h-20 w-20 place-items-center rounded-2xl bg-danger/10 text-danger ring-1 ring-danger/30">
          <Icon name="alert" size={36} />
          <span className="absolute inset-0 rounded-2xl bg-danger/10 blur-xl" aria-hidden="true" />
        </div>
        <div className="mt-6 font-mono text-xs uppercase tracking-[0.3em] text-subtle">
          Error · 404
        </div>
        <h1 className="mt-3 font-display text-4xl font-bold sm:text-5xl">Route not found</h1>
        <p className="mx-auto mt-4 max-w-md text-muted-foreground">
          The page you requested isn't part of this cyber range. Head back to base and pick up
          an investigation.
        </p>
        <div className="mt-9 flex flex-col justify-center gap-3 sm:flex-row">
          <PremiumButton iconRight="arrow-right" onClick={() => navigate({ name: "labs" })}>
            Go to labs
          </PremiumButton>
          <PremiumButton variant="outline" icon="compass" onClick={() => navigate({ name: "home" })}>
            Return home
          </PremiumButton>
        </div>
      </div>
    </div>
  );
}
