// API currency strings retain all cents, including aggregate totals above Number precision.
export const currency = {
  format(value: string | number): string {
    const text = typeof value === 'number' ? value.toFixed(2) : value
    const match = /^(-?)(\d+)(?:\.(\d{1,2}))?$/.exec(text)
    if (!match) return '—'
    const [, sign, integer, fraction = ''] = match
    return `${sign}R$\u00a0${integer.replace(/\B(?=(\d{3})+(?!\d))/g, '.')},${fraction.padEnd(2, '0')}`
  },
}

export const compactCurrency = new Intl.NumberFormat('pt-BR', {
  style: 'currency',
  currency: 'BRL',
  notation: 'compact',
  maximumFractionDigits: 1,
})

export function localDate(value: string): string {
  return new Intl.DateTimeFormat('pt-BR', { day: '2-digit', month: 'short', year: 'numeric' })
    .format(new Date(`${value}T12:00:00`))
    .replace('.', '')
}

export function today(): string {
  const now = new Date()
  const offset = now.getTimezoneOffset()
  return new Date(now.getTime() - offset * 60_000).toISOString().slice(0, 10)
}

