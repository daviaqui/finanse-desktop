import { useEffect } from 'react'
import { Controller, useForm } from 'react-hook-form'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { api, getApiError } from '../lib/api'
import { today } from '../lib/format'
import type { Category, Transaction, TransactionPayload } from '../types'
import { CurrencyInput } from './CurrencyInput'
import { DatePicker } from './DatePicker'

interface Props {
  categories: Category[]
  transaction?: Transaction | null
  onSuccess: () => void
}

export function TransactionForm({ categories, transaction, onSuccess }: Props) {
  const queryClient = useQueryClient()
  const { control, register, handleSubmit, reset, watch, formState: { errors } } = useForm<TransactionPayload>({
    defaultValues: {
      description: '',
      amount: '',
      type: 'expense',
      status: 'paid',
      transaction_date: today(),
      category_id: null,
      notes: '',
    },
  })
  const type = watch('type')

  useEffect(() => {
    if (transaction) {
      reset({
        description: transaction.description,
        amount: transaction.amount,
        type: transaction.type,
        status: transaction.status,
        transaction_date: transaction.transaction_date,
        category_id: transaction.category_id,
        notes: transaction.notes ?? '',
      })
    }
  }, [transaction, reset])

  const mutation = useMutation({
    mutationFn: (payload: TransactionPayload) => {
      const body = { ...payload, category_id: payload.category_id || null, notes: payload.notes || null }
      return transaction
        ? api.patch(`/transactions/${transaction.id}`, body)
        : api.post('/transactions', body)
    },
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['transactions'] }),
        queryClient.invalidateQueries({ queryKey: ['dashboard'] }),
      ])
      onSuccess()
    },
  })

  return (
    <form className="transaction-form" onSubmit={handleSubmit((values) => mutation.mutate(values))}>
      <div className="segmented-control">
        <label className={type === 'expense' ? 'selected expense' : ''}>
          <input type="radio" value="expense" {...register('type')} /> Despesa
        </label>
        <label className={type === 'income' ? 'selected income' : ''}>
          <input type="radio" value="income" {...register('type')} /> Receita
        </label>
      </div>
      <div className="form-field full">
        <label htmlFor="description">Descrição</label>
        <input id="description" autoFocus placeholder="Ex.: Supermercado" {...register('description', { required: 'Informe uma descrição' })} />
        {errors.description && <small className="field-error">{errors.description.message}</small>}
      </div>
      <div className="form-grid">
        <div className="form-field">
          <label htmlFor="amount">Valor</label>
          <Controller
            control={control}
            name="amount"
            rules={{
              required: 'Informe o valor',
              validate: (value) => Number(value) > 0 || 'Informe um valor maior que zero',
            }}
            render={({ field, fieldState }) => (
              <CurrencyInput
                id="amount"
                name={field.name}
                value={field.value}
                onChange={field.onChange}
                onBlur={field.onBlur}
                invalid={fieldState.invalid}
                ref={field.ref}
              />
            )}
          />
          {errors.amount && <small className="field-error">{errors.amount.message}</small>}
        </div>
        <div className="form-field">
          <label htmlFor="date">Data</label>
          <Controller
            control={control}
            name="transaction_date"
            rules={{ required: true }}
            render={({ field, fieldState }) => (
              <DatePicker
                id="date"
                value={field.value}
                onChange={field.onChange}
                invalid={fieldState.invalid}
              />
            )}
          />
        </div>
        <div className="form-field">
          <label htmlFor="category">Categoria</label>
          <select id="category" {...register('category_id')}>
            <option value="">Sem categoria</option>
            {categories.map((category) => <option key={category.id} value={category.id}>{category.name}</option>)}
          </select>
        </div>
        <div className="form-field">
          <label htmlFor="status">Situação</label>
          <select id="status" {...register('status')}>
            <option value="paid">Pago / recebido</option>
            <option value="pending">Pendente</option>
          </select>
        </div>
      </div>
      <div className="form-field full">
        <label htmlFor="notes">Observações <span>(opcional)</span></label>
        <textarea id="notes" rows={3} placeholder="Adicione informações úteis..." {...register('notes')} />
      </div>
      {mutation.isError && <div className="form-error">{getApiError(mutation.error)}</div>}
      <div className="form-actions">
        <button type="button" className="button secondary" onClick={onSuccess}>Cancelar</button>
        <button className="button primary" disabled={mutation.isPending}>
          {mutation.isPending ? 'Salvando...' : transaction ? 'Salvar alterações' : 'Adicionar lançamento'}
        </button>
      </div>
    </form>
  )
}

