// Every visible word on the landing page lives here, so copy changes never touch the layout.
// House rules for this file: plain words, short sentences, no em or en dashes.

export const REPO = "https://github.com/KuyaLoy/convert-wordpress-skill";
export const AUTHOR = { name: "KuyaLoy", url: "https://github.com/KuyaLoy" };

// Footer links. Add the other profiles here when they are ready (Facebook, Threads, LinkedIn, Instagram).
export const SOCIALS: { label: string; href: string; icon: "github" }[] = [
  { label: "GitHub", href: REPO, icon: "github" },
];

export const NAV = [
  { label: "How it works", href: "#how-it-works" },
  { label: "Install", href: "#install" },
  { label: "Patch notes", href: "#patch-notes" },
];

export const HERO = {
  tag: "PRESS START",
  title: "Move your old website to WordPress.",
  lead: "An AI agent rebuilds your site in WordPress, page by page: same look, same web addresses, every word editable.",
  primary: { label: "Install the skill", href: "#install" },
  secondary: { label: "View on GitHub", href: REPO },
  sceneLabels: ["your site", "WordPress"],
};

export const FOR_YOU = {
  title: "Is it for you?",
  cards: [
    {
      icon: "home",
      title: "I have an old site and an AI app",
      body: "You run a business, a shop or a team, and you have your site's files or its GitHub link. The agent asks a few plain questions, and you say go at each checkpoint.",
      note: "Today you also need a few free tools on your computer (Python, Node.js, a local WordPress app). A guided setup that finds them for you is next.",
    },
    {
      icon: "code",
      title: "I build websites",
      body: "You get a whole team in one skill: intake, plan, local setup, a 1:1 build in ACF PRO and Contact Form 7, pixel diffs, a launch runbook and a client report.",
      note: "Any source: plain HTML, PHP, Next.js, React, Astro, Vue, Gatsby, Nuxt, SvelteKit.",
    },
  ],
  notFor:
    "Not the right tool if you want a new design, or if your AI app cannot run commands on your computer. A chat in the browser alone is not enough.",
};

export const LEVELS = {
  tag: "LEVEL MAP",
  title: "How it works",
  lead: "Nine checkpoints from your old site to a live WordPress site. The agent stops at every gate and waits for your go.",
  gate: "Every arrow is a gate: the agent stops there and waits for your go.",
  steps: [
    { name: "Intake", sprint: "Start", body: "It studies your site and asks only what it cannot find out." },
    { name: "Plan", sprint: "Sprint 0", body: "Pages, content, forms, old web addresses and decisions. No code yet." },
    { name: "Foundation", sprint: "Sprint 1", body: "WordPress on your computer, the starter theme, the design copied 1:1." },
    { name: "Pages", sprint: "Sprints 2 to 4", body: "Every section copied as it is, then made editable in ACF." },
    { name: "Forms and email", sprint: "Sprint 5", body: "Contact Form 7, spam protection and emails that arrive." },
    { name: "SEO and security", sprint: "Sprint 6", body: "Titles, redirects, structured data and hardening." },
    { name: "Final checks", sprint: "Sprint 7", body: "Every page at every screen width compared with the original." },
    { name: "Launch", sprint: "Go live", body: "You do each host step, one at a time, with a rollback ready." },
    { name: "Live check", sprint: "Report", body: "Tracking, test leads and a PDF report for the client." },
  ],
};

export const YOU_AND_AGENT = {
  title: "You stay in charge",
  you: {
    title: "You",
    items: [
      "Paste passwords and licence keys yourself. It never types them.",
      "Say go at each checkpoint.",
      "Say OK to each download and install.",
      "Do the host steps when it is time to go live.",
      "Check the test emails and the site on your phone.",
    ],
  },
  agent: {
    title: "The agent",
    items: [
      "Studies the old site and writes the plan.",
      "Sets up WordPress on your computer, with your OK.",
      "Copies every section 1:1, then makes it editable.",
      "Compares every page with the original, pixel by pixel.",
      "Keeps notes, so any agent or person can pick up where it stopped.",
      "Writes the launch steps and the client report.",
    ],
  },
};

export const TEAM = {
  title: "A full team, one role at a time",
  lead: "Builders build, reviewers check, and nobody approves their own work.",
  roles: [
    { icon: "crown", name: "Owner", job: "Scope and the 1:1 rule", signs: true },
    { icon: "calendar", name: "Manager", job: "Plan, board, notes, updates", signs: true },
    { icon: "git-branch", name: "Lead developer", job: "Architecture and every review", signs: true },
    { icon: "brush", name: "Front-end developer", job: "Markup, CSS, fonts, images", signs: false },
    { icon: "database", name: "WordPress developer", job: "Fields, seeder, forms, SEO", signs: false },
    { icon: "eye", name: "UI", job: "Looks the same at every width", signs: true },
    { icon: "mouse", name: "UX", job: "Works the same, easy to edit", signs: true },
    { icon: "shield", name: "Security", job: "Secrets, escaping, hardening", signs: true },
    { icon: "bug", name: "Tester", job: "Pixel, text, SEO and form tests", signs: true },
    { icon: "check", name: "QA", job: "Real browsers, phones, live site", signs: true },
  ],
  signs: "Signs a gate",
  builds: "Builds",
};

export const INSTALL = {
  title: "Install",
  lead: "Clone the skill into your agent's skills folder. The folder must be named convert-to-wordpress.",
  agents: [
    { id: "claude", label: "Claude Code", folder: "~/.claude/skills/convert-to-wordpress" },
    { id: "codex", label: "Codex", folder: "~/.agents/skills/convert-to-wordpress" },
    { id: "cursor", label: "Cursor", folder: "~/.cursor/skills/convert-to-wordpress" },
    { id: "gemini", label: "Gemini CLI", folder: "~/.gemini/skills/convert-to-wordpress" },
    { id: "antigravity", label: "Antigravity", folder: "~/.gemini/config/skills/convert-to-wordpress" },
    { id: "other", label: "Others", folder: "~/.agents/skills/convert-to-wordpress" },
  ],
  steps: [
    {
      title: "Add your defaults",
      body: "Copy profile.example.json to profile.local.json and fill in your name, your local WordPress tool and your host. It stays on your computer.",
    },
    {
      title: "Start",
      body: "Give it your site as a GitHub link, a zip or a folder. It makes a copy, so your original is never touched.",
    },
  ],
  start: [
    "/convert-to-wordpress https://github.com/you/your-site",
    "/convert-to-wordpress ~/Downloads/my-site.zip",
    "/convert-to-wordpress ./my-site",
  ],
  startNote: "In Codex, type $convert-to-wordpress instead. Or just ask in plain words:",
  prompts: [
    "Convert the site in my-site.zip to WordPress.",
    "Continue the WordPress conversion.",
    "Where are we?",
  ],
  needsTitle: "What your computer needs",
  needs: [
    "Python 3.9 or later and Node.js 18 or later",
    "A local WordPress tool: Laragon, Local, MAMP, XAMPP, DDEV or wp-env",
    "PHP 8.1 to 8.4, and git for GitHub links",
    "Your own licences for ACF PRO and Duplicator Pro (paid plugins)",
  ],
};

export const SAFETY = {
  title: "House rules it never breaks",
  rules: [
    { icon: "lock", title: "Never types your secrets", body: "Passwords, licence keys and API keys are pasted by you, in the right file." },
    { icon: "flag", title: "Asks before it acts", body: "Every download, plugin install, database change, delete and live step waits for your OK." },
    { icon: "copy", title: "Never touches your original", body: "It works on a copy of your site. The original files stay exactly as they are." },
    { icon: "shield", title: "Keeps the plan private", body: "Planning files are blocked on the web server and left out of the launch package." },
  ],
};

export const PATCH = {
  tag: "PATCH NOTES",
  title: "What's new",
  full: { label: "Full changelog", href: `${REPO}/blob/main/CHANGELOG.md` },
  next: {
    title: "Next level",
    body: "A setup check that finds your local WordPress tool (Laragon, XAMPP, MAMP, Local and more), capture of a live site when you have no files, and a plain-words mode for beginners.",
  },
};

export const GUILD = {
  title: "Help make it better",
  lead: "Found a problem, tried it on a setup we have not, or fixed something? Every report and fix helps the next person.",
  actions: [
    { label: "Report a problem", href: `${REPO}/issues/new?template=bug.yml`, icon: "bug" },
    { label: "Share your setup", href: `${REPO}/issues/new?template=setup.yml`, icon: "monitor" },
    { label: "Send a fix", href: `${REPO}/blob/main/CONTRIBUTING.md`, icon: "git-merge" },
  ],
};

export const FOOTER = {
  madeBy: "Made by",
  licence: "Free software under the GNU GPL, version 2 or later.",
  credits:
    "Starter themes: Barebones by Benchmark Studios and _tw by Greg Sullivan. Pixel UI: 8bitcn/ui and Pixelarticons.",
  trademark: "WordPress is a trademark of the WordPress Foundation. This project is not affiliated with it.",
};
