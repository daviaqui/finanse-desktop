import { Landmark } from 'lucide-react'

export function Logo({ compact = false }: { compact?: boolean }) {
  return (
    <div className="logo">
      <span className="logo-mark"><Landmark size={20} strokeWidth={2.3} /></span>
      {!compact && <span>Finan<span>See</span></span>}
    </div>
  )
}

