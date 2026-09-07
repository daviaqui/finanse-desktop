import { lazy, Suspense, useEffect, useState } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'
import { invoke, isTauri } from '@tauri-apps/api/core'
import { Layout } from './components/Layout'
import { Logo } from './components/Logo'

const CategoriesPage = lazy(() => import('./pages/CategoriesPage').then((m) => ({ default: m.CategoriesPage })))
const DashboardPage = lazy(() => import('./pages/DashboardPage').then((m) => ({ default: m.DashboardPage })))
const TransactionsPage = lazy(() => import('./pages/TransactionsPage').then((m) => ({ default: m.TransactionsPage })))
const DataPage = lazy(() => import('./pages/DataPage').then((m) => ({ default: m.DataPage })))

type BackendStatus = { state: string; message: string }
export function App() {
  const [status, setStatus] = useState<BackendStatus>({ state: 'loading', message: 'Preparando seu banco de dados local…' })
  useEffect(() => {
    let active = true
    async function check() {
      try {
        if (!isTauri()) throw new Error('Abra o FinanSee Desktop pelo ícone do aplicativo. Em desenvolvimento, use npm run dev na pasta principal.')
        const next = await invoke<BackendStatus>('backend_status')
        if (active) setStatus(next)
      } catch (error) {
        if (active) setStatus({ state: 'error', message: String(error) })
      }
    }
    void check()
    const timer = setInterval(check, 1500)
    return () => { active = false; clearInterval(timer) }
  }, [])
  if (status.state !== 'ready') return (
    <div className="desktop-startup" role={status.state === 'error' ? 'alert' : 'status'}>
      <Logo />
      {status.state === 'loading' && <span className="loader" />}
      <h1>{status.state === 'error' ? 'Não foi possível abrir seus dados' : 'Abrindo FinanSee Desktop'}</h1>
      <p>{status.message}</p>
      {status.state === 'error' && <p>Feche o aplicativo e abra novamente. Se o problema continuar, verifique o espaço livre e as permissões da pasta de dados. Seus dados permanecem no computador.</p>}
    </div>
  )
  return (
    <Suspense fallback={<div className="app-loader" role="status"><span className="loader" /><span>Carregando…</span></div>}>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<DashboardPage />} />
          <Route path="/lancamentos" element={<TransactionsPage />} />
          <Route path="/categorias" element={<CategoriesPage />} />
          <Route path="/dados" element={<DataPage />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Suspense>
  )
}
