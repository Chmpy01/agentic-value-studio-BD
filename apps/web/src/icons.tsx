import {
  Activity,
  Building2,
  ChartColumn,
  Check,
  Circle,
  Compass,
  Database,
  Handshake,
  Layers,
  MapPin,
  Network,
  Play,
  Radio,
  Shield,
  Sparkles,
  Target,
  Users,
  Waypoints,
  type LucideIcon,
} from 'lucide-react'

const ICONS: Record<string, LucideIcon> = {
  activity: Activity,
  building: Building2,
  chart: ChartColumn,
  check: Check,
  compass: Compass,
  database: Database,
  'map-pin': MapPin,
  handshake: Handshake,
  layers: Layers,
  network: Network,
  play: Play,
  radio: Radio,
  shield: Shield,
  spark: Sparkles,
  target: Target,
  users: Users,
  waypoints: Waypoints,
  briefcase: Layers,
}

export function Icon({ name, size = 18 }: { name?: string; size?: number }) {
  const Glyph = ICONS[name || ''] || Circle
  return <Glyph size={size} strokeWidth={1.75} aria-hidden="true" />
}
