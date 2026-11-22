// Muscat Nights · tokens and rules as data. Mirrors tokens.css. Keep both in sync.
export const colors = {
  navy: '#0F1B2B', navy2: '#13202F', sand: '#FFF4E8', peach: '#FFC9A3', coral: '#F26B5B', coral2: '#F59A62',
  gold: '#FFD08A', teal: '#2FB7B0', rose: '#E9849A', mist: '#B9C6D3', dim: '#7F8EA0', red: '#E5484D',
  silver: '#D7DDE4', bronze: '#D9A27A',
} as const;

export const fonts = {
  display: "'Archivo', Impact, sans-serif", displayAxes: "'wdth' 66",
  serif: "'Fraunces', Georgia, serif", serifAxes: "'SOFT' 100, 'WONK' 1",
  ui: "'Manrope', system-ui, sans-serif", mono: "'JetBrains Mono', monospace", arabic: "'Reem Kufi', sans-serif",
} as const;

/** Rep level from series points. Thresholds are config: confirm with the organiser. Rep never goes down. */
export const REP_LEVELS = [
  { id: 'legend', label: 'Legend', min: 100, color: colors.gold },
  { id: 'known',  label: 'Known',  min: 90,  color: colors.coral },
  { id: 'rising', label: 'Rising', min: 80,  color: colors.teal },
  { id: 'rookie', label: 'Rookie', min: 0,   color: colors.dim },
] as const;
export const repFor = (points: number) => REP_LEVELS.find(l => points >= l.min)!;

/** Crew card tier from current table position. */
export const TIERS = [
  { id: 'legend', label: 'LEGEND', maxRank: 1 },
  { id: 'elite',  label: 'ELITE',  maxRank: 3 },
  { id: 'pro',    label: 'PRO',    maxRank: 8 },
  { id: 'street', label: 'STREET', maxRank: Infinity },
] as const;
export const tierFor = (rank: number) => TIERS.find(t => rank <= t.maxRank)!;

export const SEASON = {
  name: 'Muscat Nights', nameAr: 'ليالي مسقط', volume: 10, month: 'December 2026',
  prizePoolOMR: 402, seasonPrizesOMR: [75, 50, 30], nightlyVoucherOMR: 28, // 14 OMR to each of the night's two champions
  finaleSessionNo: 9, finaleDoublePoints: true,
  bossKillBonus: { enabled: false, points: 3 }, // NOT approved yet. Keep false until the organiser signs off.
} as const;
