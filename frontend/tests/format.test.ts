import assert from 'node:assert/strict'
import test from 'node:test'
import { currency } from '../src/lib/format.ts'

test('formats decimal currency strings without losing cents', () => {
  assert.equal(currency.format('900719925474099.99'), 'R$\u00a0900.719.925.474.099,99')
  assert.equal(currency.format('-1234.01'), '-R$\u00a01.234,01')
  assert.equal(currency.format('0'), 'R$\u00a00,00')
  assert.equal(currency.format('0.1'), 'R$\u00a00,10')
  assert.equal(currency.format('NaN'), '—')
})
