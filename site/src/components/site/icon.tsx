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
  Lock,
  Monitor,
  Mouse,
  Shield,
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
  lock: Lock,
  monitor: Monitor,
  mouse: Mouse,
  shield: Shield,
  user: User,
} as const;

export type IconName = keyof typeof ICONS;

export function Icon({ name, className = "size-6" }: { name: IconName | string; className?: string }) {
  const Svg = ICONS[name as IconName];
  if (!Svg) return null;
  return <Svg aria-hidden="true" focusable="false" className={className} />;
}
