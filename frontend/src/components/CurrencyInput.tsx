import { forwardRef, type ChangeEvent, type ClipboardEvent, type KeyboardEvent } from 'react'

const MAX_DIGITS = 14

type CurrencyInputProps = {
  id: string
  name: string
  value: string
  onChange: (value: string) => void
  onBlur: () => void
  invalid?: boolean
}

function decimalToDigits(value: string) {
  if (!value) return ''
  const [integer = '0', fraction = ''] = value.replace(',', '.').split('.')
  return `${integer.replace(/\D/g, '')}${fraction.replace(/\D/g, '').padEnd(2, '0').slice(0, 2)}`
    .replace(/^0+/, '')
}

function digitsToDecimal(value: string) {
  const digits = value.replace(/\D/g, '').slice(0, MAX_DIGITS).replace(/^0+/, '')
  if (!digits) return ''
  const padded = digits.padStart(3, '0')
  const integer = padded.slice(0, -2).replace(/^0+(?=\d)/, '')
  return `${integer}.${padded.slice(-2)}`
}

function formatCurrency(value: string) {
  const digits = decimalToDigits(value).padStart(3, '0')
  if (!value) return ''
  const integer = digits.slice(0, -2).replace(/^0+(?=\d)/, '')
  const groupedInteger = integer.replace(/\B(?=(\d{3})+(?!\d))/g, '.')
  return `${groupedInteger},${digits.slice(-2)}`
}

export const CurrencyInput = forwardRef<HTMLInputElement, CurrencyInputProps>(function CurrencyInput(
  { id, name, value, onChange, onBlur, invalid = false },
  ref,
) {
  const displayValue = formatCurrency(value)

  function replaceFromDigits(digits: string) {
    onChange(digitsToDecimal(digits))
  }

  function handleKeyDown(event: KeyboardEvent<HTMLInputElement>) {
    if (event.ctrlKey || event.metaKey || event.altKey) return

    if (/^\d$/.test(event.key)) {
      event.preventDefault()
      const hasSelection = event.currentTarget.selectionStart !== event.currentTarget.selectionEnd
      const currentDigits = hasSelection ? '' : decimalToDigits(value)
      replaceFromDigits(`${currentDigits}${event.key}`)
      return
    }

    if (event.key === 'Backspace') {
      event.preventDefault()
      const hasSelection = event.currentTarget.selectionStart !== event.currentTarget.selectionEnd
      const currentDigits = hasSelection ? '' : decimalToDigits(value).slice(0, -1)
      replaceFromDigits(currentDigits)
      return
    }

    if (event.key === 'Delete') {
      event.preventDefault()
      onChange('')
      return
    }

    if (event.key === ',' || event.key === '.') event.preventDefault()
  }

  function handleChange(event: ChangeEvent<HTMLInputElement>) {
    replaceFromDigits(event.target.value.replace(/\D/g, ''))
  }

  function handlePaste(event: ClipboardEvent<HTMLInputElement>) {
    event.preventDefault()
    const pastedDigits = event.clipboardData.getData('text').replace(/\D/g, '')
    if (!pastedDigits) return
    const isAllSelected = event.currentTarget.selectionStart === 0
      && event.currentTarget.selectionEnd === displayValue.length
    const currentDigits = isAllSelected ? '' : decimalToDigits(value)
    replaceFromDigits(`${currentDigits}${pastedDigits}`)
  }

  return (
    <div className={`money-input${invalid ? ' invalid' : ''}`}>
      <span aria-hidden="true">R$</span>
      <input
        ref={ref}
        id={id}
        name={name}
        type="text"
        inputMode="numeric"
        autoComplete="off"
        placeholder="0,00"
        value={displayValue}
        aria-invalid={invalid}
        onBlur={onBlur}
        onChange={handleChange}
        onKeyDown={handleKeyDown}
        onPaste={handlePaste}
      />
    </div>
  )
})
