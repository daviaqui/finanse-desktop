import { useState } from 'react'
import { NavLink, Outlet, useLocation } from 'react-router-dom'
import {
  ChartPie,
  LayoutDashboard,
  Menu,
  ReceiptText,
  DatabaseBackup,
  Tags,
  X,
} from 'lucide-react'
import { Logo } from './Logo'

const navigation = [
  { to: '/', label: 'Visão geral', icon: LayoutDashboard },
  { to: '/lancamentos', label: 'Lançamentos', icon: ReceiptText },
  { to: '/categorias', label: 'Categorias', icon: Tags },
  { to: '/dados', label: 'Backup e dados', icon: DatabaseBackup },
]

export function Layout() {
  const user = { name: "Meu perfil", email: "Local • offline" }
  const [menuOpen, setMenuOpen] = useState(false)
  const location = useLocation()

  const title = navigation.find((item) => item.to === location.pathname)?.label ?? 'FinanSee'

  return (
    <div className="app-shell">
      {menuOpen && <button className="sidebar-backdrop" aria-label="Fechar menu" onClick={() => setMenuOpen(false)} />}
      <aside className={`sidebar ${menuOpen ? 'open' : ''}`}>
        <div className="sidebar-head">
          <Logo />
          <button className="icon-button mobile-only" onClick={() => setMenuOpen(false)}><X size={20} /></button>
        </div>
        <nav className="main-nav" aria-label="Navegação principal">
          <p className="nav-caption">MENU</p>
          {navigation.map(({ to, label, icon: Icon }) => (
            <NavLink key={to} to={to} end={to === '/'} onClick={() => setMenuOpen(false)}>
              <Icon size={19} />
              <span>{label}</span>
            </NavLink>
          ))}
        </nav>
        <div className="sidebar-insight">
          <ChartPie size={22} />
          <strong>Organize hoje.</strong>
          <p>Pequenas decisões constroem grandes resultados.</p>
        </div>
        <div className="user-menu">
          <div className="avatar">{user.name.slice(0, 2).toUpperCase()}</div>
          <div className="user-copy">
            <strong>{user.name}</strong>
            <span>{user.email}</span>
          </div>
        </div>
      </aside>
      <main className="main-content">
        <header className="mobile-header">
          <button className="icon-button" onClick={() => setMenuOpen(true)}><Menu size={22} /></button>
          <span>{title}</span>
          <div className="avatar avatar-small">{user.name.slice(0, 1).toUpperCase()}</div>
        </header>
        <Outlet />
      </main>
    </div>
  )
}
