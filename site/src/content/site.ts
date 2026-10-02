// Every visible word on the landing page lives here, so copy changes never touch the layout.
// House rules for this file: plain words, short sentences, no em or en dashes.

export const REPO = "https://github.com/KuyaLoy/convert-wordpress-skill";
export const AUTHOR = { name: "KuyaLoy", url: "https://github.com/KuyaLoy" };

// Footer links: the author's profiles. Icons: pixel brand marks (components/site/brand-icons.tsx).
export const SOCIALS: { label: string; href: string; icon: string }[] = [
  { label: "GitHub", href: AUTHOR.url, icon: "github" },
  { label: "LinkedIn", href: "https://www.linkedin.com/in/mynameisloloy/", icon: "linkedin" },
  { label: "Facebook", href: "https://www.facebook.com/robin.tapiru/", icon: "facebook" },
  { label: "Instagram", href: "https://www.instagram.com/tapiru_robin/", icon: "instagram" },
  { label: "Threads", href: "https://www.threads.com/@tapiru_robin", icon: "threads" },
  { label: "X", href: "https://x.com/BUKO_roll", icon: "x" },
];

export const NAV = [
  { label: "How it works", href: "#how-it-works" },
  { label: "Install", href: "#install" },
  { label: "What's new", href: "#patch-notes" },
];

// The sticky menu on the right (and the Menu button on small screens). Same order as the page.
export const SECTIONS = [
  { id: "top", label: "Start" },
  { id: "why", label: "Why WordPress" },
  { id: "for-you", label: "Is it for you?" },
  { id: "how-it-works", label: "How it works" },
  { id: "in-charge", label: "You stay in charge" },
  { id: "team", label: "The team" },
  { id: "install", label: "Install" },
  { id: "rules", label: "House rules" },
  { id: "patch-notes", label: "What's new" },
  { id: "contribute", label: "Help make it better" },
  { id: "hire", label: "Need a developer?" },
];

export const HERO = {
  tag: "PRESS START",
  title: "Turn any website into WordPress.",
  lead: "Built with AI or by hand? An agent rebuilds it in WordPress: same look, same web addresses, every word editable.",
  primary: { label: "Install the skill", href: "#install" },
  secondary: { label: "View on GitHub", href: REPO },
  sceneLabels: ["your site", "WordPress, editable"],
};

export const WHY = {
  title: "AI builds the site. WordPress lets you run it.",
  lead: "AI apps hand you code, not a CMS. Every change means another prompt or a developer. WordPress gives your team a dashboard.",
  columns: { task: "When you want to", before: "A site made of code", after: "The same site in WordPress" },
  rows: [
    { task: "Change a word or a photo", before: "Edit the code, or prompt the AI again", after: "Type it in the dashboard" },
    { task: "Add a page", before: "Ask a developer, or prompt again", after: "Pick a layout and fill in the fields" },
    { task: "Take enquiries", before: "A form script someone has to keep working", after: "Contact Form 7, with every lead saved" },
    { task: "Look after SEO", before: "Titles and redirects live in the code", after: "Titles, descriptions and redirects in the dashboard" },
  ],
  close: "The design and the web addresses stay the same, so visitors see the site they know. Your team can just run it now.",
};

export const FOR_YOU = {
  title: "Is it for you?",
  cards: [
    {
      icon: "sparkles",
      title: "I made my site with AI",
      body: "You built it with an AI app or a site builder, and now you or your client want to edit it without code. Give the agent its files or GitHub link, answer a few plain questions, and say go at each checkpoint.",
      note: "Today you also need a few free tools on your computer (Python, Node.js, a local WordPress app). A guided setup that finds them for you is next.",
    },
    {
      icon: "code",
      title: "I build websites",
      body: "Your client wants to edit their own site. You get a whole team in one skill: plan, local setup, a 1:1 build in ACF PRO and Contact Form 7, pixel diffs, a launch runbook and a client report.",
      note: "Any source: plain HTML, PHP, Next.js, React, Astro, Vue, Gatsby, Nuxt, SvelteKit.",
    },
  ],
  notFor:
    "Not the right tool if you want a new design, or if your AI app cannot run commands on your computer. A chat in the browser alone is not enough.",
};

export const LEVELS = {
  tag: "LEVEL MAP",
  title: "How it works",
  lead: "Nine checkpoints from your current site to a live WordPress site. The agent stops at every gate and waits for your go.",
  gate: "Every arrow is a gate: the agent stops there and waits for your go.",
  steps: [
    { name: "Intake", sprint: "Start", body: "It studies your site and asks only what it cannot find out." },
    { name: "Plan", sprint: "Sprint 0", body: "Pages, content, forms, web addresses to keep or redirect, decisions. No code yet." },
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
      "Studies your site and writes the plan.",
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

export const HIRE = {
  title: "Need a developer?",
  lead: "I'm KuyaLoy, the developer behind this skill. If you would rather have the conversion done for you, or want a hand with yours, get in touch.",
  contacts: [
    {
      label: "Email",
      value: "robintapiru0894@gmail.com",
      href: "mailto:robintapiru0894@gmail.com?subject=WordPress%20conversion",
      icon: "mail",
    },
    { label: "Phone", value: "+971 56 594 4497", href: "tel:+971565944497", icon: "phone" },
    { label: "Website", value: "robintapiru.com", href: "https://robintapiru.com", icon: "globe" },
  ],
};

export const FOOTER = {
  madeBy: "Made by",
  licence: "Free software under the GNU GPL, version 2 or later.",
  credits:
    "Starter themes: Barebones by Benchmark Studios and _tw by Greg Sullivan. Pixel UI: 8bitcn/ui and Pixelarticons. Social icons: HackerNoon Pixel Icon Library.",
  trademark: "WordPress is a trademark of the WordPress Foundation. This project is not affiliated with it.",
};
