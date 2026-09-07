import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  ArrowDownRight,
  ArrowRight,
  ArrowUpRight,
  CircleDollarSign,
  Clock3,
  Plus,
  Target,
  TrendingUp,
} from 'lucide-react'
import { Link } from 'react-router-dom'
import {
  Area,
  AreaChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { Modal } from '../components/Modal'
import { MonthPicker } from '../components/MonthPicker'
import { TransactionForm } from '../components/TransactionForm'
import { api, getApiError } from '../lib/api'
import { compactCurrency, currency, localDate } from '../lib/format'
import type { Category, DashboardData, TransactionList } from '../types'

export function DashboardPage() {
  const now = new Date()
  const [month, setMonth] = useState(`${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`)
  const [formOpen, setFormOpen] = useState(false)
  const [year, monthNumber] = month.split('-').map(Number)

  const { data, isLoading, error } = useQuery({
    queryKey: ['dashboard', month],
    queryFn: () => api.get<DashboardData>('/dashboard', { params: { year, month: monthNumber } }).then((res) => res.data),
  })
  const { data: recent } = useQuery({
    queryKey: ['transactions', 'recent'],
    queryFn: () => api.get<TransactionList>('/transactions', { params: { page_size: 5 } }).then((res) => res.data),
  })
  const { data: categories = [] } = useQuery({
    queryKey: ['categories'],
    queryFn: () => api.get<Category[]>('/categories').then((res) => res.data),
  })

  const chartData = data?.cash_flow.map((item) => ({ ...item, income: Number(item.income), expenses: Number(item.expenses) })) ?? []
  const categoryData = data?.expenses_by_category.map((item) => ({ ...item, amount: Number(item.amount) })) ?? []

  return (
    <div className="page dashboard-page">
      <div className="page-heading">
        <div>
          <span className="eyebrow">PAINEL FINANCEIRO</span>
          <h1>Seu resumo <span>— veja seu mês.</span></h1>
          <p>Acompanhe os números que importam e decida seus próximos passos.</p>
        </div>
        <div className="heading-actions">
          <MonthPicker value={month} onChange={setMonth} />
          <button className="button primary" onClick={() => setFormOpen(true)}><Plus size={18} /> Novo lançamento</button>
        </div>
      </div>

      {error ? <div className="form-error" role="alert">{getApiError(error)}</div> : isLoading ? <div className="panel-loader"><span className="loader" /></div> : (
        <>
          <section className="summary-grid">
            <SummaryCard label="Saldo do mês" value={data?.summary.balance ?? '0'} icon={CircleDollarSign} tone="navy" detail={`${data?.summary.savings_rate ?? 0}% de taxa de economia`} />
            <SummaryCard label="Receitas" value={data?.summary.income ?? '0'} icon={ArrowUpRight} tone="green" detail="Valores recebidos" />
            <SummaryCard label="Despesas" value={data?.summary.expenses ?? '0'} icon={ArrowDownRight} tone="red" detail="Valores pagos" />
            <SummaryCard label="A pagar" value={data?.summary.pending_expenses ?? '0'} icon={Clock3} tone="amber" detail="Despesas pendentes" />
          </section>

          <section className="dashboard-charts">
            <article className="panel cash-flow-panel">
              <div className="panel-heading">
                <div><span className="panel-kicker">EVOLUÇÃO</span><h2>Fluxo de caixa</h2></div>
                <div className="chart-legend"><span className="income-dot">Receitas</span><span className="expense-dot">Despesas</span></div>
              </div>
              <div className="chart-wrap">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={chartData} margin={{ top: 12, right: 8, left: -12, bottom: 0 }}>
                    <defs>
                      <linearGradient id="incomeGradient" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#1b9a78" stopOpacity={0.25}/><stop offset="100%" stopColor="#1b9a78" stopOpacity={0}/></linearGradient>
                      <linearGradient id="expenseGradient" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#e05e5e" stopOpacity={0.2}/><stop offset="100%" stopColor="#e05e5e" stopOpacity={0}/></linearGradient>
                    </defs>
                    <CartesianGrid stroke="#edf0f5" vertical={false} />
                    <XAxis dataKey="month" axisLine={false} tickLine={false} tick={{ fill: '#7a8497', fontSize: 12 }} />
                    <YAxis axisLine={false} tickLine={false} tick={{ fill: '#7a8497', fontSize: 11 }} tickFormatter={(value) => compactCurrency.format(value)} />
                    <Tooltip formatter={(value) => currency.format(String(value))} contentStyle={{ border: '1px solid #e9ebf0', borderRadius: 12, boxShadow: '0 12px 30px rgba(25,35,55,.1)' }} />
                    <Area type="monotone" dataKey="income" name="Receitas" stroke="#17886b" strokeWidth={2.5} fill="url(#incomeGradient)" />
                    <Area type="monotone" dataKey="expenses" name="Despesas" stroke="#d75555" strokeWidth={2.5} fill="url(#expenseGradient)" />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </article>

            <article className="panel category-panel">
              <div className="panel-heading"><div><span className="panel-kicker">DISTRIBUIÇÃO</span><h2>Despesas por categoria</h2></div></div>
              {categoryData.length ? (
                <div className="category-chart-content">
                  <div className="donut-wrap">
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart><Pie data={categoryData} dataKey="amount" nameKey="category" innerRadius={57} outerRadius={78} paddingAngle={3}>{categoryData.map((item) => <Cell key={item.category} fill={item.color} />)}</Pie><Tooltip formatter={(value) => currency.format(String(value))} /></PieChart>
                    </ResponsiveContainer>
                    <div className="donut-label"><strong>{categoryData.length}</strong><span>categorias</span></div>
                  </div>
                  <div className="category-legend">{categoryData.slice(0, 5).map((item) => <div key={item.category}><span className="category-name"><i style={{ background: item.color }} />{item.category}</span><strong>{item.percentage}%</strong></div>)}</div>
                </div>
              ) : <div className="chart-empty"><Target size={30} /><p>Adicione despesas pagas para visualizar a distribuição.</p></div>}
            </article>
          </section>

          <article className="panel recent-panel">
            <div className="panel-heading">
              <div><span className="panel-kicker">MOVIMENTAÇÕES</span><h2>Últimos lançamentos</h2></div>
              <Link className="text-link" to="/lancamentos">Ver todos <ArrowRight size={16} /></Link>
            </div>
            {recent?.items.length ? <div className="transaction-list compact">{recent.items.map((item) => <div className="transaction-row" key={item.id}><div className="transaction-icon" style={{ background: `${item.category?.color ?? '#94a3b8'}18`, color: item.category?.color ?? '#64748b' }}><TrendingUp size={18} /></div><div className="transaction-main"><strong>{item.description}</strong><span>{item.category?.name ?? 'Sem categoria'} · {localDate(item.transaction_date)}</span></div><span className={`status-pill ${item.status}`}>{item.status === 'paid' ? 'Concluído' : 'Pendente'}</span><strong className={`transaction-value ${item.type}`}>{item.type === 'expense' ? '−' : '+'} {currency.format(item.amount)}</strong></div>)}</div> : <div className="table-empty">Nenhum lançamento por aqui ainda.</div>}
          </article>
        </>
      )}
      {formOpen && <Modal title="Novo lançamento" onClose={() => setFormOpen(false)}><TransactionForm categories={categories} onSuccess={() => setFormOpen(false)} /></Modal>}
    </div>
  )
}

function SummaryCard({ label, value, icon: Icon, tone, detail }: { label: string; value: string; icon: typeof CircleDollarSign; tone: string; detail: string }) {
  return <article className={`summary-card ${tone}`}><div className="summary-card-top"><span>{label}</span><i><Icon size={20} /></i></div><strong>{currency.format(String(value))}</strong><p>{detail}</p></article>
}
