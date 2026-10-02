import {
  Footer,
  ForYou,
  Guild,
  Hero,
  Hire,
  Install,
  LevelMap,
  Nav,
  PatchNotes,
  Safety,
  Team,
  Why,
  YouAndAgent,
} from "@/components/site/sections";
import { SectionRail } from "@/components/site/section-nav";
import { HERO, SECTIONS } from "@/content/site";

export default function Home() {
  return (
    <>
      <Nav />
      <div className="flex-1 xl:grid xl:grid-cols-[minmax(0,1fr)_16rem]">
        <main id="main" tabIndex={-1} className="min-w-0 outline-none">
          <Hero />
          <Why />
          <ForYou />
          <LevelMap />
          <YouAndAgent />
          <Team />
          <Install />
          <Safety />
          <PatchNotes />
          <Guild />
          <Hire />
        </main>
        <aside className="hidden border-l-4 border-line-soft xl:block">
          <SectionRail sections={SECTIONS} cta={HERO.primary} />
        </aside>
      </div>
      <Footer />
    </>
  );
}
