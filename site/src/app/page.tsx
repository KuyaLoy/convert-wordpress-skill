import {
  Footer,
  ForYou,
  Guild,
  Hero,
  Install,
  LevelMap,
  Nav,
  PatchNotes,
  Safety,
  Team,
  YouAndAgent,
} from "@/components/site/sections";

export default function Home() {
  return (
    <>
      <Nav />
      <main id="main" tabIndex={-1} className="flex-1 outline-none">
        <Hero />
        <ForYou />
        <LevelMap />
        <YouAndAgent />
        <Team />
        <Install />
        <Safety />
        <PatchNotes />
        <Guild />
      </main>
      <Footer />
    </>
  );
}
