export type TransactionType = 'income' | 'expense'
export type TransactionStatus = 'paid' | 'pending'

export interface User {
  id: string
  name: string
  email: string
  created_at: string
}

export interface Category {
  id: string
  name: string
  color: string
  icon: string
  created_at: string
}

export interface Transaction {
  id: string
  description: string
  amount: string
  type: TransactionType
  status: TransactionStatus
  transaction_date: string
  category_id: string | null
  category: Category | null
  notes: string | null
  created_at: string
}

export interface TransactionPayload {
  description: string
  amount: string
  type: TransactionType
  status: TransactionStatus
  transaction_date: string
  category_id: string | null
  notes?: string | null
}

export interface TransactionList {
  items: Transaction[]
  total: number
  page: number
  page_size: number
  pages: number
}

export interface DashboardData {
  summary: {
    income: string
    expenses: string
    balance: string
    pending_expenses: string
    savings_rate: number
  }
  cash_flow: Array<{ month: string; income: string; expenses: string }>
  expenses_by_category: Array<{
    category: string
    color: string
    amount: string
    percentage: number
  }>
}

