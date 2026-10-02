import { Button } from "@/components/ui/8bit/button";
import { Card, CardContent } from "@/components/ui/8bit/card";
import { BrandIcon } from "@/components/site/brand-icons";
import { CodeLine } from "@/components/site/copy-button";
import { Icon } from "@/components/site/icon";
import { InstallTabs } from "@/components/site/install-tabs";
import { PixelScene } from "@/components/site/pixel-scene";
import { MobileMenu } from "@/components/site/section-nav";
import { ThemeToggle } from "@/components/site/theme";
import { formatDate, getReleases, Inline } from "@/lib/changelog";
import {
  AUTHOR,
  FOOTER,
  FOR_YOU,
  GUILD,
  HERO,
  HIRE,
  INSTALL,
  LEVELS,
  NAV,
  PATCH,
  REPO,
  SAFETY,
  SECTIONS,
  SOCIALS,
  TEAM,
  WHY,
  YOU_AND_AGENT,
} from "@/content/site";

const wrap = "mx-auto w-full max-w-6xl px-4 sm:px-6";
const band = "border-y-4 border-line-soft bg-band";
// Table cells become labelled lines on phones.
const stacked =
  "max-md:block max-md:p-0 max-md:py-1.5 max-md:before:block max-md:before:font-pixel max-md:before:text-sm max-md:before:text-muted-foreground max-md:before:content-[attr(data-label)]";

function Logo() {
  return (
    <span className="flex items-center gap-3">
      <span aria-hidden="true" className="grid size-5 grid-cols-2">
        <span className="bg-brand" />
        <span className="bg-foreground" />
        <span className="bg-foreground" />
        <span className="bg-brand" />
      </span>
      <span className="font-pixel text-base leading-none whitespace-nowrap text-foreground sm:text-lg">convert-to-wordpress</span>
    </span>
  );
}

export function Nav() {
  return (
    <header className="sticky top-0 z-40 border-b-4 border-line-soft bg-background">
      <div className="relative flex h-16 w-full items-center justify-between gap-4 px-4 sm:px-6 xl:px-8">
        <a href="#top" aria-label="convert-to-wordpress, back to the top">
          <Logo />
        </a>
        <nav aria-label="Main" className="hidden lg:block">
          <ul className="flex items-center gap-8 font-pixel text-lg">
            {NAV.map((n) => (
              <li key={n.href}>
                <a href={n.href} className="text-muted-foreground transition-colors hover:text-foreground">
                  {n.label}
                </a>
              </li>
            ))}
          </ul>
        </nav>
        <div className="flex items-center gap-3 sm:gap-4">
          <div className="hidden sm:block">
            <ThemeToggle />
          </div>
          <MobileMenu sections={SECTIONS} />
          <a
            href={REPO}
            aria-label="GitHub repository"
            className="hidden h-9 items-center gap-2 border-2 border-foreground/80 px-3 font-pixel text-base transition-colors hover:bg-secondary sm:flex"
          >
            <Icon name="github" className="size-5" />
            GitHub
          </a>
        </div>
      </div>
    </header>
  );
}

export function Hero() {
  return (
    <section id="top" aria-labelledby="hero-title" className="scanlines bg-dots border-b-4 border-line-soft">
      <div className={`${wrap} relative z-[2] grid items-center gap-14 py-16 md:py-24 lg:grid-cols-[1.45fr_1fr]`}>
        <div>
          <p className="game-tag flex items-center gap-3 text-brand-text">
            {HERO.tag}
            <span aria-hidden="true" className="blink inline-block h-3.5 w-2.5 bg-brand" />
          </p>
          <h1 id="hero-title" className="mt-6 text-[2.6rem] leading-[1.08] sm:text-5xl lg:text-[3.15rem]">{HERO.title}</h1>
          <p className="mt-6 max-w-[38ch] text-xl text-muted-foreground">{HERO.lead}</p>
          <div className="mt-10 flex flex-wrap items-center gap-6">
            <Button asChild font="normal" className="h-12 px-6 font-pixel text-lg">
              <a href={HERO.primary.href}>{HERO.primary.label}</a>
            </Button>
            <Button asChild variant="outline" font="normal" className="h-12 px-6 font-pixel text-lg">
              <a href={HERO.secondary.href}>
                <Icon name="github" className="size-5" />
                {HERO.secondary.label}
              </a>
            </Button>
          </div>
        </div>
        <div className="mx-auto w-full max-w-[560px]">
          <PixelScene labels={HERO.sceneLabels} />
        </div>
      </div>
    </section>
  );
}

export function Why() {
  return (
    <section id="why" aria-labelledby="why-title" className={`${band} py-20 md:py-28`}>
      <div className={wrap}>
        <h2 id="why-title" className="max-w-3xl text-4xl md:text-5xl">
          {WHY.title}
        </h2>
        <p className="mt-5 max-w-2xl text-muted-foreground">{WHY.lead}</p>
        <div className="pixel-frame mt-12 overflow-hidden bg-background">
          <table className="w-full border-collapse text-left text-base">
            <caption className="sr-only">What changes when your site moves to WordPress</caption>
            <thead className="max-md:sr-only">
              <tr className="font-pixel text-lg">
                <th scope="col" className="w-[28%] p-5 font-medium text-muted-foreground">
                  {WHY.columns.task}
                </th>
                <th scope="col" className="w-[36%] p-5 font-medium">
                  <span className="flex items-center gap-2">
                    <Icon name="code" className="size-5 text-muted-foreground" />
                    {WHY.columns.before}
                  </span>
                </th>
                <th scope="col" className="w-[36%] bg-brand p-5 font-medium text-ink">
                  <span className="flex items-center gap-2">
                    <Icon name="pencil" className="size-5" />
                    {WHY.columns.after}
                  </span>
                </th>
              </tr>
            </thead>
            <tbody>
              {WHY.rows.map((r, i) => (
                <tr key={r.task} className={`max-md:block max-md:p-5 ${i % 2 ? "bg-panel-2" : "bg-panel"}`}>
                  <th scope="row" className="p-5 font-pixel text-lg font-medium max-md:block max-md:p-0 max-md:pb-3">
                    {r.task}
                  </th>
                  <td data-label={WHY.columns.before} className={`p-5 text-muted-foreground ${stacked}`}>
                    {r.before}
                  </td>
                  <td data-label={WHY.columns.after} className={`p-5 ${stacked}`}>
                    <span className="flex gap-2">
                      <Icon name="check" className="mt-1 size-5 shrink-0 text-brand" />
                      {r.after}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="mt-10 max-w-3xl text-lg">{WHY.close}</p>
      </div>
    </section>
  );
}

export function ForYou() {
  return (
    <section id="for-you" aria-labelledby="for-you-title" className="py-20 md:py-28">
      <div className={wrap}>
        <h2 id="for-you-title" className="text-4xl md:text-5xl">
          {FOR_YOU.title}
        </h2>
        <div className="mt-12 grid gap-12 px-1.5 md:grid-cols-2">
          {FOR_YOU.cards.map((c) => (
            <Card key={c.title} font="normal" className="h-full text-base">
              <CardContent className="flex h-full flex-col gap-5 p-7">
                <span className="grid size-12 place-items-center bg-brand text-ink">
                  <Icon name={c.icon} className="size-7" />
                </span>
                <h3 className="text-2xl md:text-3xl">{c.title}</h3>
                <p className="text-lg text-foreground/90">{c.body}</p>
                <p className="mt-auto border-t-2 border-dashed border-line pt-5 text-base text-muted-foreground">
                  {c.note}
                </p>
              </CardContent>
            </Card>
          ))}
        </div>
        <p className="mt-12 flex max-w-3xl items-start gap-3 text-muted-foreground">
          <Icon name="flag" className="mt-1 size-5 shrink-0 text-brand" />
          {FOR_YOU.notFor}
        </p>
      </div>
    </section>
  );
}

// The nine checkpoints snake across a 3 x 3 grid on wide screens (1 2 3, then 6 5 4, then 7 8 9) and run straight
// down on phones. The DOM order stays 1 to 9 for screen readers.
function snake(i: number) {
  const row = Math.floor(i / 3);
  const col = row % 2 === 0 ? i % 3 : 2 - (i % 3);
  const nextRow = Math.floor((i + 1) / 3);
  const dir = i === 8 ? null : nextRow !== row ? "down" : row % 2 === 0 ? "right" : "left";
  return { row: row + 1, col: col + 1, dir };
}

function Arrow({ dir }: { dir: "right" | "left" | "down" }) {
  const pos = {
    right: "top-1/2 -right-[3.25rem] -translate-y-1/2",
    left: "top-1/2 -left-[3.25rem] -translate-y-1/2 rotate-180",
    down: "-bottom-[3.25rem] left-1/2 -translate-x-1/2 rotate-90",
  }[dir];
  return (
    <span aria-hidden="true" className={`absolute hidden text-brand lg:block ${pos}`}>
      <Icon name="arrow-right" className="size-9" />
    </span>
  );
}

export function LevelMap() {
  return (
    <section id="how-it-works" aria-labelledby="how-title" className={`${band} py-20 md:py-28`}>
      <div className={wrap}>
        <p className="game-tag text-brand-text">{LEVELS.tag}</p>
        <h2 id="how-title" className="mt-5 text-4xl md:text-5xl">
          {LEVELS.title}
        </h2>
        <p className="mt-5 max-w-2xl text-muted-foreground">{LEVELS.lead}</p>
        <ol className="mt-14 grid gap-14 lg:grid-cols-3">
          {LEVELS.steps.map((s, i) => {
            const p = snake(i);
            return (
              <li
                key={s.name}
                style={{ "--col": p.col, "--row": p.row } as React.CSSProperties}
                className="relative lg:col-start-(--col) lg:row-start-(--row)"
              >
                <div className="pixel-frame soft-frame h-full bg-background p-6">
                  <div className="flex items-center gap-4">
                    <span className="game-tag grid size-10 shrink-0 place-items-center bg-brand text-base text-ink">
                      {i + 1}
                    </span>
                    <span className="font-mono text-sm text-muted-foreground">{s.sprint}</span>
                  </div>
                  <h3 className="mt-4 text-2xl">{s.name}</h3>
                  <p className="mt-2 text-base text-muted-foreground">{s.body}</p>
                </div>
                {p.dir && <Arrow dir={p.dir as "right" | "left" | "down"} />}
                {i < 8 && (
                  <span aria-hidden="true" className="absolute -bottom-11 left-8 text-brand lg:hidden">
                    <Icon name="arrow-right" className="size-8 rotate-90" />
                  </span>
                )}
              </li>
            );
          })}
        </ol>
        <p className="mt-14 flex items-center gap-3 text-base text-muted-foreground">
          <Icon name="arrow-right" className="size-6 shrink-0 text-brand" />
          {LEVELS.gate}
        </p>
      </div>
    </section>
  );
}

export function YouAndAgent() {
  const cols = [
    { ...YOU_AND_AGENT.you, icon: "user", tone: "bg-panel" },
    { ...YOU_AND_AGENT.agent, icon: "android", tone: "bg-panel-2" },
  ];
  return (
    <section id="in-charge" aria-labelledby="charge-title" className="py-20 md:py-28">
      <div className={wrap}>
        <h2 id="charge-title" className="text-4xl md:text-5xl">
          {YOU_AND_AGENT.title}
        </h2>
        <div className="pixel-frame mt-12 grid md:grid-cols-2">
          {cols.map((c) => (
            <div key={c.title} className={`${c.tone} p-7 md:p-10`}>
              <h3 className="flex items-center gap-3 text-3xl">
                <Icon name={c.icon} className="size-8 text-brand" />
                {c.title}
              </h3>
              <ul className="mt-7 space-y-4">
                {c.items.map((it) => (
                  <li key={it} className="flex gap-3">
                    <Icon name="check" className="mt-1 size-5 shrink-0 text-brand" />
                    <span>{it}</span>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

export function Team() {
  return (
    <section id="team" aria-labelledby="team-title" className="pb-20 md:pb-28">
      <div className={wrap}>
        <h2 id="team-title" className="text-4xl md:text-5xl">
          {TEAM.title}
        </h2>
        <p className="mt-5 max-w-2xl text-muted-foreground">{TEAM.lead}</p>
        <ul className="mt-12 grid grid-cols-1 gap-6 px-1 min-[360px]:grid-cols-2 md:grid-cols-3 lg:grid-cols-5">
          {TEAM.roles.map((r) => (
            <li key={r.name} className="pixel-frame soft-frame flex flex-col bg-panel p-5">
              <Icon name={r.icon} className="size-8 text-brand" />
              <h3 className="mt-4 text-xl leading-tight">{r.name}</h3>
              <p className="mt-2 mb-5 text-base text-muted-foreground">{r.job}</p>
              <span
                className={`mt-auto inline-block w-fit px-2 py-1 font-pixel text-sm ${
                  r.signs ? "bg-brand text-ink" : "bg-secondary text-foreground"
                }`}
              >
                {r.signs ? TEAM.signs : TEAM.builds}
              </span>
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}

export function Install() {
  const [defaults, start] = INSTALL.steps;
  return (
    <section id="install" aria-labelledby="install-title" className={`${band} py-20 md:py-28`}>
      <div className={wrap}>
        <h2 id="install-title" className="text-4xl md:text-5xl">
          {INSTALL.title}
        </h2>
        <p className="mt-5 max-w-2xl text-muted-foreground">{INSTALL.lead}</p>
        <div className="mt-12 grid gap-14 lg:grid-cols-[1.45fr_1fr]">
          <div className="min-w-0 space-y-12">
            <InstallTabs agents={INSTALL.agents} repo={REPO} />
            <div>
              <h3 className="text-2xl">{defaults.title}</h3>
              <p className="mt-3 text-muted-foreground">{defaults.body}</p>
            </div>
            <div>
              <h3 className="text-2xl">{start.title}</h3>
              <p className="mt-3 text-muted-foreground">{start.body}</p>
              <div className="mt-5 space-y-4">
                {INSTALL.start.map((cmd) => (
                  <CodeLine key={cmd} text={cmd} />
                ))}
              </div>
              <p className="mt-6 text-muted-foreground">{INSTALL.startNote}</p>
              <ul className="mt-3 space-y-2">
                {INSTALL.prompts.map((q) => (
                  <li key={q} className="font-mono text-base text-foreground">
                    &ldquo;{q}&rdquo;
                  </li>
                ))}
              </ul>
            </div>
          </div>
          <aside aria-labelledby="needs-title" className="h-fit">
            <div className="pixel-frame bg-background p-7">
              <h3 id="needs-title" className="text-2xl">
                {INSTALL.needsTitle}
              </h3>
              <ul className="mt-6 space-y-4 text-base">
                {INSTALL.needs.map((n) => (
                  <li key={n} className="flex gap-3">
                    <Icon name="check" className="mt-1 size-5 shrink-0 text-brand" />
                    <span>{n}</span>
                  </li>
                ))}
              </ul>
              <a href={`${REPO}#install`} className="mt-7 inline-flex items-center gap-2 font-pixel text-lg text-brand-text underline">
                Full install guide
                <Icon name="arrow-right" className="size-5" />
              </a>
            </div>
          </aside>
        </div>
      </div>
    </section>
  );
}

export function Safety() {
  return (
    <section id="rules" aria-labelledby="rules-title" className="py-20 md:py-28">
      <div className={wrap}>
        <h2 id="rules-title" className="text-4xl md:text-5xl">
          {SAFETY.title}
        </h2>
        <div className="mt-12 grid gap-x-16 gap-y-10 sm:grid-cols-2">
          {SAFETY.rules.map((r) => (
            <div key={r.title} className="flex gap-5">
              <span className="grid size-12 shrink-0 place-items-center border-4 border-brand text-brand">
                <Icon name={r.icon} className="size-6" />
              </span>
              <div>
                <h3 className="text-2xl">{r.title}</h3>
                <p className="mt-2 text-muted-foreground">{r.body}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

export function PatchNotes() {
  const [latest, ...older] = getReleases(3);
  const latestItems = latest.sections.flatMap((s) => s.items.map((it) => ({ section: s.title, it })));
  const shown = latestItems.slice(0, 6);
  return (
    <section id="patch-notes" aria-labelledby="patch-title" className={`${band} py-20 md:py-28`}>
      <div className={wrap}>
        <p className="game-tag text-brand-text">{PATCH.tag}</p>
        <h2 id="patch-title" className="mt-5 text-4xl md:text-5xl">
          {PATCH.title}
        </h2>
        <div className="mt-12 grid gap-12 lg:grid-cols-[1.45fr_1fr]">
          <article className="pixel-frame h-fit bg-background p-7 md:p-9">
            <header className="flex flex-wrap items-baseline gap-x-5 gap-y-2">
              <h3 className="text-3xl">Version {latest.version}</h3>
              <time dateTime={latest.date} className="font-pixel text-lg text-muted-foreground">
                {formatDate(latest.date)}
              </time>
            </header>
            <ul className="mt-7 space-y-5">
              {shown.map(({ section, it }) => (
                <li key={it} className="flex gap-3">
                  <Icon name="check" className="mt-1 size-5 shrink-0 text-brand" />
                  <span className="text-base">
                    <span className="sr-only">{section}: </span>
                    <Inline text={it} />
                  </span>
                </li>
              ))}
            </ul>
            {latestItems.length > shown.length && (
              <p className="mt-6 text-base text-muted-foreground">
                And {latestItems.length - shown.length} more in the full changelog.
              </p>
            )}
          </article>
          <div className="space-y-10">
            {older.map((r) => (
              <article key={r.version}>
                <header className="flex flex-wrap items-baseline gap-x-4">
                  <h3 className="text-2xl">Version {r.version}</h3>
                  <time dateTime={r.date} className="font-pixel text-base text-muted-foreground">
                    {formatDate(r.date)}
                  </time>
                </header>
                <p className="mt-3 line-clamp-3 text-base text-muted-foreground">
                  <Inline text={r.sections[0]?.items[0] ?? ""} />
                </p>
              </article>
            ))}
            <div className="bg-brand p-7 text-ink">
              <h3 className="text-2xl">{PATCH.next.title}</h3>
              <p className="mt-3 text-base">{PATCH.next.body}</p>
            </div>
            <Button asChild variant="outline" font="normal" className="h-12 px-6 font-pixel text-lg">
              <a href={PATCH.full.href}>
                {PATCH.full.label}
                <Icon name="arrow-right" className="size-5" />
              </a>
            </Button>
          </div>
        </div>
      </div>
    </section>
  );
}

export function Guild() {
  return (
    <section id="contribute" aria-labelledby="guild-title" className="bg-checker py-20 md:py-28">
      <div className={`${wrap} text-center`}>
        <h2 id="guild-title" className="text-4xl md:text-5xl">
          {GUILD.title}
        </h2>
        <p className="mx-auto mt-5 max-w-2xl text-muted-foreground">{GUILD.lead}</p>
        <div className="mt-12 flex flex-wrap justify-center gap-8">
          {GUILD.actions.map((a) => (
            <Button key={a.label} asChild variant="outline" font="normal" className="h-12 bg-background px-6 font-pixel text-lg">
              <a href={a.href}>
                <Icon name={a.icon} className="size-5" />
                {a.label}
              </a>
            </Button>
          ))}
        </div>
      </div>
    </section>
  );
}

export function Hire() {
  return (
    <section id="hire" aria-labelledby="hire-title" className="py-20 md:py-28">
      <div className={`${wrap} grid items-center gap-12 lg:grid-cols-[1fr_1.1fr]`}>
        <div>
          <span className="grid size-14 place-items-center bg-brand text-ink">
            <Icon name="briefcase" className="size-8" />
          </span>
          <h2 id="hire-title" className="mt-6 text-4xl md:text-5xl">
            {HIRE.title}
          </h2>
          <p className="mt-5 max-w-xl text-lg text-muted-foreground">{HIRE.lead}</p>
        </div>
        <ul className="space-y-6 px-1">
          {HIRE.contacts.map((c) => (
            <li key={c.label}>
              <a
                href={c.href}
                className="pixel-frame group flex items-center gap-5 bg-panel p-5 transition-colors hover:bg-primary hover:text-primary-foreground"
              >
                <span className="grid size-12 shrink-0 place-items-center bg-secondary text-foreground group-hover:bg-ink group-hover:text-brand">
                  <Icon name={c.icon} className="size-6" />
                </span>
                <span className="min-w-0">
                  <span className="block font-pixel text-base text-muted-foreground group-hover:text-primary-foreground">
                    {c.label}
                  </span>
                  <span className="block text-lg [overflow-wrap:anywhere]">{c.value}</span>
                </span>
              </a>
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}

export function Footer() {
  return (
    <footer className="border-t-4 border-line-soft">
      <div className={`${wrap} grid gap-10 py-14 text-base text-muted-foreground md:grid-cols-[1fr_1.3fr]`}>
        <div className="space-y-5">
          <Logo />
          <p>
            {FOOTER.madeBy}{" "}
            <a href={AUTHOR.url} className="text-foreground underline hover:text-brand">
              {AUTHOR.name}
            </a>
          </p>
          <ul className="flex flex-wrap gap-3" aria-label="KuyaLoy online">
            {SOCIALS.map((s) => (
              <li key={s.href}>
                <a
                  href={s.href}
                  aria-label={s.label}
                  title={s.label}
                  rel="me noopener"
                  className="grid size-11 place-items-center bg-secondary text-foreground transition-colors hover:bg-brand hover:text-ink"
                >
                  <BrandIcon name={s.icon} className="size-6" />
                </a>
              </li>
            ))}
            <li>
              <a
                href={REPO}
                className="flex h-11 items-center gap-2 bg-secondary px-4 font-pixel text-base text-foreground transition-colors hover:bg-brand hover:text-ink"
              >
                <Icon name="git-branch" className="size-5" />
                The repository
              </a>
            </li>
          </ul>
        </div>
        <div className="space-y-3 text-sm">
          <p>{FOOTER.licence}</p>
          <p>{FOOTER.credits}</p>
          <p>{FOOTER.trademark}</p>
        </div>
      </div>
    </footer>
  );
}
