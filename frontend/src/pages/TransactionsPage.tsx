import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { ChevronLeft, ChevronRight, Edit3, Filter, Plus, Search, Trash2 } from 'lucide-react'
import { EmptyState } from '../components/EmptyState'
import { ConfirmDelete } from '../components/ConfirmDelete'
import { Modal } from '../components/Modal'
import { TransactionForm } from '../components/TransactionForm'
import { api, getApiError } from '../lib/api'
import { currency, localDate } from '../lib/format'
import type { Category, Transaction, TransactionList, TransactionStatus, TransactionType } from '../types'

export function TransactionsPage() {
  const queryClient = useQueryClient()
  const [pendingDelete, setPendingDelete] = useState<Transaction | null>(null)
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [type, setType] = useState<TransactionType | ''>('')
  const [status, setStatus] = useState<TransactionStatus | ''>('')
  const [editing, setEditing] = useState<Transaction | null>(null)
  const [formOpen, setFormOpen] = useState(false)

  const params = { page, page_size: 12, search: search || undefined, transaction_type: type || undefined, transaction_status: status || undefined }
  const { data, isLoading, error } = useQuery({
    queryKey: ['transactions', params],
    queryFn: () => api.get<TransactionList>('/transactions', { params }).then((res) => res.data),
  })
  const { data: categories = [] } = useQuery({ queryKey: ['categories'], queryFn: () => api.get<Category[]>('/categories').then((res) => res.data) })
  const remove = useMutation({
    mutationFn: (id: string) => api.delete(`/transactions/${id}`),
    onSuccess: () => { if (data?.items.length === 1 && page > 1) setPage(page - 1); queryClient.invalidateQueries({ queryKey: ['transactions'] }); queryClient.invalidateQueries({ queryKey: ['dashboard'] }) },
  })

  function openEdit(transaction: Transaction) { setEditing(transaction); setFormOpen(true) }
  function closeForm() { setEditing(null); setFormOpen(false) }
  function removeItem(transaction: Transaction) {
    setPendingDelete(transaction)
  }

  return (
    <div className="page">
      <div className="page-heading">
        <div><span className="eyebrow">HISTÓRICO</span><h1>Lançamentos</h1><p>Consulte e organize tudo o que entra e sai.</p></div>
        <button className="button primary" onClick={() => setFormOpen(true)}><Plus size={18} /> Novo lançamento</button>
      </div>
      {remove.isError && <div className="form-error" role="alert">{getApiError(remove.error)}</div>}
      <section className="panel transactions-panel">
        <div className="filters-bar">
          <label className="search-input"><Search size={18} /><input value={search} onChange={(event) => { setSearch(event.target.value); setPage(1) }} placeholder="Buscar lançamento..." /></label>
          <div className="filters-label"><Filter size={16} /> Filtros</div>
          <select value={type} onChange={(event) => { setType(event.target.value as TransactionType | ''); setPage(1) }}><option value="">Todos os tipos</option><option value="income">Receitas</option><option value="expense">Despesas</option></select>
          <select value={status} onChange={(event) => { setStatus(event.target.value as TransactionStatus | ''); setPage(1) }}><option value="">Todas as situações</option><option value="paid">Concluídos</option><option value="pending">Pendentes</option></select>
        </div>
        {error ? <div className="form-error" role="alert">{getApiError(error)}</div> : isLoading ? <div className="panel-loader"><span className="loader" /></div> : data?.items.length ? (
          <>
            <div className="data-table-wrap"><table className="data-table"><thead><tr><th>Descrição</th><th>Categoria</th><th>Data</th><th>Situação</th><th className="right">Valor</th><th aria-label="Ações" /></tr></thead><tbody>{data.items.map((item) => <tr key={item.id}><td><div className="description-cell"><i style={{ background: item.category?.color ?? '#94a3b8' }} /><div><strong>{item.description}</strong>{item.notes && <span>{item.notes}</span>}</div></div></td><td><span className="category-chip">{item.category?.name ?? 'Sem categoria'}</span></td><td>{localDate(item.transaction_date)}</td><td><span className={`status-pill ${item.status}`}>{item.status === 'paid' ? 'Concluído' : 'Pendente'}</span></td><td className={`right transaction-value ${item.type}`}>{item.type === 'expense' ? '−' : '+'} {currency.format(item.amount)}</td><td><div className="row-actions"><button title="Editar" onClick={() => openEdit(item)}><Edit3 size={16} /></button><button title="Excluir" className="danger" onClick={() => removeItem(item)}><Trash2 size={16} /></button></div></td></tr>)}</tbody></table></div>
            <div className="pagination"><span>{data.total} {data.total === 1 ? 'lançamento' : 'lançamentos'}</span><div><button disabled={page === 1} onClick={() => setPage((value) => value - 1)}><ChevronLeft size={17} /></button><span>Página {page} de {data.pages}</span><button disabled={page === data.pages} onClick={() => setPage((value) => value + 1)}><ChevronRight size={17} /></button></div></div>
          </>
        ) : <EmptyState title="Nenhum lançamento encontrado" description="Ajuste os filtros ou adicione seu primeiro lançamento." />}
      </section>
      {pendingDelete && <ConfirmDelete description={`Excluir o lançamento “${pendingDelete.description}”?`} busy={remove.isPending} onCancel={() => setPendingDelete(null)} onConfirm={() => remove.mutate(pendingDelete.id, { onSettled: () => setPendingDelete(null) })} />}
      {formOpen && <Modal title={editing ? 'Editar lançamento' : 'Novo lançamento'} onClose={closeForm}><TransactionForm categories={categories} transaction={editing} onSuccess={closeForm} /></Modal>}
    </div>
  )
}
