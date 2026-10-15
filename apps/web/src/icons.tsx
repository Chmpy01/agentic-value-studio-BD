import {
  Activity,
  BadgeCheck,
  BrainCircuit,
  Briefcase,
  Building2,
  ChartColumn,
  Circle,
  Database,
  GitMerge,
  Handshake,
  Layers,
  Network,
  Play,
  Radio,
  Shield,
  Sparkles,
  Target,
  User,
  Users,
  Waypoints,
  Workflow,
  type LucideIcon,
} from 'lucide-react'

const ICONS: Record<string, LucideIcon> = {
  activity: Activity,
  badge: BadgeCheck,
  brain: BrainCircuit,
  briefcase: Briefcase,
  building: Building2,
  chart: ChartColumn,
  database: Database,
  handshake: Handshake,
  layers: Layers,
  merge: GitMerge,
  network: Network,
  play: Play,
  radio: Radio,
  shield: Shield,
  spark: Sparkles,
  target: Target,
  user: User,
  users: Users,
  waypoints: Waypoints,
  workflow: Workflow,
}

export function Icon({ name, size = 18 }: { name?: string; size?: number }) {
  const Glyph = ICONS[name || ''] || Circle
  return <Glyph size={size} strokeWidth={1.75} aria-hidden="true" />
}
