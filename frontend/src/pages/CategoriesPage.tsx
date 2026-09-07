import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Plus, Tag, Trash2 } from 'lucide-react'
import { ConfirmDelete } from '../components/ConfirmDelete'
import { Modal } from '../components/Modal'
import { api, getApiError } from '../lib/api'
import type { Category } from '../types'

interface CategoryForm { name: string; color: string }

export function CategoriesPage() {
  const queryClient = useQueryClient()
  const [pendingDelete, setPendingDelete] = useState<Category | null>(null)
  const [modalOpen, setModalOpen] = useState(false)
  const { register, handleSubmit, reset, formState: { errors } } = useForm<CategoryForm>({ defaultValues: { name: '', color: '#6366f1' } })
  const { data: categories = [], isLoading, error } = useQuery({ queryKey: ['categories'], queryFn: () => api.get<Category[]>('/categories').then((res) => res.data) })
  const create = useMutation({
    mutationFn: (values: CategoryForm) => api.post('/categories', { ...values, icon: 'circle' }),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['categories'] }); reset(); setModalOpen(false) },
  })
  const remove = useMutation({
    mutationFn: (id: string) => api.delete(`/categories/${id}`),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['categories'] }); queryClient.invalidateQueries({ queryKey: ['transactions'] }); queryClient.invalidateQueries({ queryKey: ['dashboard'] }) },
  })

  function removeCategory(category: Category) {
    setPendingDelete(category)
  }

  return (
    <div className="page">
      <div className="page-heading"><div><span className="eyebrow">ORGANIZAÇÃO</span><h1>Categorias</h1><p>Personalize os grupos que dão sentido aos seus números.</p></div><button className="button primary" onClick={() => setModalOpen(true)}><Plus size={18} /> Nova categoria</button></div>
      {(error || remove.isError) && <div className="form-error" role="alert">{getApiError(error || remove.error)}</div>}
      <section className="category-grid">
        {isLoading ? <div className="panel-loader"><span className="loader" /></div> : categories.map((category) => (
          <article className="category-card" key={category.id}>
            <div className="category-card-icon" style={{ background: `${category.color}18`, color: category.color }}><Tag size={22} /></div>
            <div><h2>{category.name}</h2><p>Categoria personalizada</p></div>
            <button className="category-delete" onClick={() => removeCategory(category)} aria-label={`Excluir ${category.name}`}><Trash2 size={17} /></button>
            <span className="category-accent" style={{ background: category.color }} />
          </article>
        ))}
      </section>
      <aside className="category-note"><strong>Uma dica:</strong> mantenha poucas categorias, mas que realmente ajudem você a entender seus hábitos.</aside>
      {pendingDelete && <ConfirmDelete description={`Excluir a categoria “${pendingDelete.name}”? Os lançamentos serão mantidos sem categoria.`} busy={remove.isPending} onCancel={() => setPendingDelete(null)} onConfirm={() => remove.mutate(pendingDelete.id, { onSettled: () => setPendingDelete(null) })} />}
      {modalOpen && <Modal title="Nova categoria" onClose={() => setModalOpen(false)}><form className="transaction-form" onSubmit={handleSubmit((values) => create.mutate(values))}><div className="form-field full"><label htmlFor="category-name">Nome</label><input id="category-name" autoFocus placeholder="Ex.: Educação" {...register('name', { required: 'Informe um nome' })} />{errors.name && <small className="field-error">{errors.name.message}</small>}</div><div className="form-field full"><label htmlFor="category-color">Cor de identificação</label><div className="color-input"><input id="category-color" type="color" {...register('color')} /><span>Escolha uma cor para reconhecer a categoria rapidamente.</span></div></div>{create.isError && <div className="form-error">{getApiError(create.error)}</div>}<div className="form-actions"><button type="button" className="button secondary" onClick={() => setModalOpen(false)}>Cancelar</button><button className="button primary" disabled={create.isPending}>{create.isPending ? 'Criando...' : 'Criar categoria'}</button></div></form></Modal>}
    </div>
  )
}

