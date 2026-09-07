import { useEffect, useId, useRef, useState } from 'react'
import { CalendarDays, ChevronDown, ChevronLeft, ChevronRight } from 'lucide-react'

const MONTHS = [
  'Janeiro',
  'Fevereiro',
  'Março',
  'Abril',
  'Maio',
  'Junho',
  'Julho',
  'Agosto',
  'Setembro',
  'Outubro',
  'Novembro',
  'Dezembro',
]

type MonthPickerProps = {
  value: string
  onChange: (value: string) => void
}

export function MonthPicker({ value, onChange }: MonthPickerProps) {
  const [selectedYear, selectedMonth] = value.split('-').map(Number)
  const [isOpen, setIsOpen] = useState(false)
  const [visibleYear, setVisibleYear] = useState(selectedYear)
  const rootRef = useRef<HTMLDivElement>(null)
  const triggerRef = useRef<HTMLButtonElement>(null)
  const dialogId = useId()

  useEffect(() => {
    setVisibleYear(selectedYear)
  }, [selectedYear])

  useEffect(() => {
    if (!isOpen) return

    function handlePointerDown(event: PointerEvent) {
      if (!rootRef.current?.contains(event.target as Node)) setIsOpen(false)
    }

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key !== 'Escape') return
      setIsOpen(false)
      triggerRef.current?.focus()
    }

    document.addEventListener('pointerdown', handlePointerDown)
    document.addEventListener('keydown', handleKeyDown)
    return () => {
      document.removeEventListener('pointerdown', handlePointerDown)
      document.removeEventListener('keydown', handleKeyDown)
    }
  }, [isOpen])

  function chooseMonth(monthIndex: number) {
    onChange(`${visibleYear}-${String(monthIndex + 1).padStart(2, '0')}`)
    setIsOpen(false)
    triggerRef.current?.focus()
  }

  function chooseCurrentMonth() {
    const now = new Date()
    onChange(`${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`)
    setIsOpen(false)
    triggerRef.current?.focus()
  }

  return (
    <div className="month-picker-shell" ref={rootRef}>
      <button
        ref={triggerRef}
        className="month-picker"
        type="button"
        aria-label={`Selecionar mês. Mês selecionado: ${MONTHS[selectedMonth - 1]} de ${selectedYear}`}
        aria-haspopup="dialog"
        aria-expanded={isOpen}
        aria-controls={dialogId}
        onClick={() => setIsOpen((open) => !open)}
      >
        <CalendarDays size={18} aria-hidden="true" />
        <span>{MONTHS[selectedMonth - 1]} {selectedYear}</span>
        <ChevronDown className={isOpen ? 'open' : ''} size={15} aria-hidden="true" />
      </button>

      {isOpen && (
        <div className="picker-popover month-picker-popover" id={dialogId} role="dialog" aria-label="Escolher mês e ano">
          <div className="picker-header">
            <button type="button" aria-label={`Mostrar o ano ${visibleYear - 1}`} onClick={() => setVisibleYear((year) => year - 1)}>
              <ChevronLeft size={18} aria-hidden="true" />
            </button>
            <strong aria-live="polite">{visibleYear}</strong>
            <button type="button" aria-label={`Mostrar o ano ${visibleYear + 1}`} onClick={() => setVisibleYear((year) => year + 1)}>
              <ChevronRight size={18} aria-hidden="true" />
            </button>
          </div>

          <div className="picker-option-grid">
            {MONTHS.map((monthName, index) => {
              const isSelected = visibleYear === selectedYear && index + 1 === selectedMonth
              return (
                <button
                  className={isSelected ? 'selected' : ''}
                  type="button"
                  key={monthName}
                  aria-pressed={isSelected}
                  onClick={() => chooseMonth(index)}
                >
                  {monthName.slice(0, 3)}
                </button>
              )
            })}
          </div>

          <button className="picker-today" type="button" onClick={chooseCurrentMonth}>Ir para o mês atual</button>
        </div>
      )}
    </div>
  )
}
