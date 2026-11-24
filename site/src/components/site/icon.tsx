import {
  Android,
  ArrowRight,
  Brush,
  Bug,
  Calendar,
  Check,
  Code,
  Copy,
  Crown,
  Database,
  Eye,
  Flag,
  GitBranch,
  GitMerge,
  Github,
  Home,
  Close,
  Lock,
  Menu,
  Monitor,
  Moon,
  Mouse,
  Pencil,
  Play,
  Shield,
  Sparkles,
  Sun,
  User,
} from "pixelarticons/react";

// One icon family for the whole site: Pixelarticons (MIT).
const ICONS = {
  android: Android,
  "arrow-right": ArrowRight,
  brush: Brush,
  bug: Bug,
  calendar: Calendar,
  check: Check,
  code: Code,
  copy: Copy,
  crown: Crown,
  database: Database,
  eye: Eye,
  flag: Flag,
  "git-branch": GitBranch,
  "git-merge": GitMerge,
  github: Github,
  home: Home,
  close: Close,
  lock: Lock,
  menu: Menu,
  monitor: Monitor,
  moon: Moon,
  mouse: Mouse,
  pencil: Pencil,
  play: Play,
  shield: Shield,
  sparkles: Sparkles,
  sun: Sun,
  user: User,
} as const;

export type IconName = keyof typeof ICONS;

export function Icon({ name, className = "size-6" }: { name: IconName | string; className?: string }) {
  const Svg = ICONS[name as IconName];
  if (!Svg) return null;
  return <Svg aria-hidden="true" focusable="false" className={className} />;
}
