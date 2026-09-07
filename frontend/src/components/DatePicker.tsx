import { useEffect, useId, useLayoutEffect, useRef, useState } from 'react'
import { createPortal } from 'react-dom'
import { CalendarDays, ChevronLeft, ChevronRight } from 'lucide-react'

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
const WEEKDAYS = ['Dom', 'Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb']
const YEAR_PAGE_SIZE = 12
const POPOVER_WIDTH = 286

type PickerView = 'days' | 'months' | 'years'

type DatePickerProps = {
  id: string
  value: string
  onChange: (value: string) => void
  invalid?: boolean
}

function parseDate(value: string) {
  const [year, month, day] = value.split('-').map(Number)
  if (!year || !month || !day) return new Date()
  return new Date(year, month - 1, day, 12)
}

function serializeDate(date: Date) {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

function formatDate(value: string) {
  const date = parseDate(value)
  return new Intl.DateTimeFormat('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  }).format(date)
}

function sameDay(first: Date, second: Date) {
  return first.getFullYear() === second.getFullYear()
    && first.getMonth() === second.getMonth()
    && first.getDate() === second.getDate()
}

function buildCalendarDays(visibleDate: Date) {
  const year = visibleDate.getFullYear()
  const month = visibleDate.getMonth()
  const firstWeekday = new Date(year, month, 1, 12).getDay()
  return Array.from({ length: 42 }, (_, index) => new Date(year, month, index - firstWeekday + 1, 12))
}

export function DatePicker({ id, value, onChange, invalid = false }: DatePickerProps) {
  const selectedDate = parseDate(value)
  const [isOpen, setIsOpen] = useState(false)
  const [view, setView] = useState<PickerView>('days')
  const [visibleDate, setVisibleDate] = useState(selectedDate)
  const [popoverStyle, setPopoverStyle] = useState<React.CSSProperties>({})
  const triggerRef = useRef<HTMLButtonElement>(null)
  const popoverRef = useRef<HTMLDivElement>(null)
  const dialogId = useId()

  useEffect(() => {
    setVisibleDate(parseDate(value))
  }, [value])

  useEffect(() => {
    if (!isOpen) return

    function handlePointerDown(event: PointerEvent) {
      const target = event.target as Node
      if (!triggerRef.current?.contains(target) && !popoverRef.current?.contains(target)) closePicker(false)
    }

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === 'Escape') closePicker(true)
    }

    document.addEventListener('pointerdown', handlePointerDown)
    document.addEventListener('keydown', handleKeyDown)
    return () => {
      document.removeEventListener('pointerdown', handlePointerDown)
      document.removeEventListener('keydown', handleKeyDown)
    }
  }, [isOpen])

  useLayoutEffect(() => {
    if (!isOpen || !triggerRef.current) return

    function positionPopover() {
      const trigger = triggerRef.current
      const popover = popoverRef.current
      if (!trigger) return

      const rect = trigger.getBoundingClientRect()
      const popoverHeight = popover?.offsetHeight ?? 310
      const left = Math.min(
        Math.max(12, rect.right - POPOVER_WIDTH),
        window.innerWidth - POPOVER_WIDTH - 12,
      )
      const spaceBelow = window.innerHeight - rect.bottom - 8
      const spaceAbove = rect.top - 8
      const placeAbove = spaceBelow < popoverHeight && spaceAbove > spaceBelow
      const top = placeAbove
        ? Math.max(12, rect.top - popoverHeight - 8)
        : rect.bottom + 8
      const maxHeight = placeAbove ? spaceAbove - 4 : spaceBelow - 4

      setPopoverStyle({ left, top, maxHeight: Math.max(220, maxHeight) })
    }

    positionPopover()
    window.addEventListener('resize', positionPopover)
    window.addEventListener('scroll', positionPopover, true)
    return () => {
      window.removeEventListener('resize', positionPopover)
      window.removeEventListener('scroll', positionPopover, true)
    }
  }, [isOpen, view, visibleDate])

  function closePicker(restoreFocus: boolean) {
    setIsOpen(false)
    setView('days')
    if (restoreFocus) requestAnimationFrame(() => triggerRef.current?.focus())
  }

  function openPicker() {
    setVisibleDate(parseDate(value))
    setView('days')
    setIsOpen(true)
  }

  function shiftPeriod(direction: -1 | 1) {
    setVisibleDate((current) => {
      if (view === 'days') return new Date(current.getFullYear(), current.getMonth() + direction, 1, 12)
      if (view === 'months') return new Date(current.getFullYear() + direction, current.getMonth(), 1, 12)
      return new Date(current.getFullYear() + direction * YEAR_PAGE_SIZE, current.getMonth(), 1, 12)
    })
  }

  function chooseDay(date: Date) {
    onChange(serializeDate(date))
    closePicker(true)
  }

  function chooseMonth(month: number) {
    setVisibleDate((current) => new Date(current.getFullYear(), month, 1, 12))
    setView('days')
  }

  function chooseYear(year: number) {
    setVisibleDate((current) => new Date(year, current.getMonth(), 1, 12))
    setView('months')
  }

  function chooseToday() {
    const today = new Date()
    onChange(serializeDate(today))
    closePicker(true)
  }

  const year = visibleDate.getFullYear()
  const month = visibleDate.getMonth()
  const yearPageStart = Math.floor(year / 10) * 10
  const headerLabel = view === 'days'
    ? `${MONTHS[month]} ${year}`
    : view === 'months'
      ? String(year)
      : `${yearPageStart} – ${yearPageStart + YEAR_PAGE_SIZE - 1}`

  const popover = isOpen && (
    <div
      ref={popoverRef}
      className="picker-popover date-picker-popover"
      id={dialogId}
      role="dialog"
      aria-label="Escolher dia, mês e ano"
      style={popoverStyle}
    >
      <div className="picker-header">
        <button type="button" aria-label="Período anterior" onClick={() => shiftPeriod(-1)}>
          <ChevronLeft size={18} aria-hidden="true" />
        </button>
        <button
          className="picker-header-label"
          type="button"
          aria-label={view === 'days' ? 'Escolher mês' : view === 'months' ? 'Escolher ano' : headerLabel}
          onClick={() => {
            if (view === 'days') setView('months')
            if (view === 'months') setView('years')
          }}
        >
          {headerLabel}
        </button>
        <button type="button" aria-label="Próximo período" onClick={() => shiftPeriod(1)}>
          <ChevronRight size={18} aria-hidden="true" />
        </button>
      </div>

      {view === 'days' && (
        <>
          <div className="date-picker-weekdays" aria-hidden="true">
            {WEEKDAYS.map((weekday) => <span key={weekday}>{weekday}</span>)}
          </div>
          <div className="date-picker-days">
            {buildCalendarDays(visibleDate).map((date) => {
              const isSelected = sameDay(date, selectedDate)
              const isToday = sameDay(date, new Date())
              const isOutsideMonth = date.getMonth() !== month
              return (
                <button
                  className={`${isSelected ? 'selected ' : ''}${isToday ? 'today ' : ''}${isOutsideMonth ? 'outside-month' : ''}`}
                  type="button"
                  key={serializeDate(date)}
                  aria-label={new Intl.DateTimeFormat('pt-BR', { dateStyle: 'long' }).format(date)}
                  aria-pressed={isSelected}
                  onClick={() => chooseDay(date)}
                >
                  {date.getDate()}
                </button>
              )
            })}
          </div>
        </>
      )}

      {view === 'months' && (
        <div className="picker-option-grid">
          {MONTHS.map((monthName, index) => (
            <button
              className={index === month ? 'selected' : ''}
              type="button"
              key={monthName}
              aria-pressed={index === month}
              onClick={() => chooseMonth(index)}
            >
              {monthName.slice(0, 3)}
            </button>
          ))}
        </div>
      )}

      {view === 'years' && (
        <div className="picker-option-grid">
          {Array.from({ length: YEAR_PAGE_SIZE }, (_, index) => yearPageStart + index).map((optionYear) => (
            <button
              className={optionYear === year ? 'selected' : ''}
              type="button"
              key={optionYear}
              aria-pressed={optionYear === year}
              onClick={() => chooseYear(optionYear)}
            >
              {optionYear}
            </button>
          ))}
        </div>
      )}

      <button className="picker-today" type="button" onClick={chooseToday}>Ir para hoje</button>
    </div>
  )

  return (
    <div className="date-picker-shell">
      <button
        ref={triggerRef}
        className="date-picker-trigger"
        id={id}
        type="button"
        aria-label={`Selecionar data. Data selecionada: ${formatDate(value)}`}
        aria-haspopup="dialog"
        aria-expanded={isOpen}
        aria-controls={dialogId}
        aria-invalid={invalid}
        onClick={() => isOpen ? closePicker(false) : openPicker()}
      >
        <span>{formatDate(value)}</span>
        <CalendarDays size={17} aria-hidden="true" />
      </button>
      {popover && createPortal(popover, document.body)}
    </div>
  )
}
