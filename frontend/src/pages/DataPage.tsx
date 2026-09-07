import { useEffect, useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { invoke } from '@tauri-apps/api/core'
import { Download, Upload } from 'lucide-react'
import { getApiError } from '../lib/api'

export function DataPage() {
  const [directory, setDirectory] = useState('')
  const [busy, setBusy] = useState(false)
  const [message, setMessage] = useState('')
  const [error, setError] = useState(false)
  const queryClient = useQueryClient()
  useEffect(() => { invoke<string>('data_directory').then(setDirectory).catch((e) => { setError(true); setMessage(getApiError(e)) }) }, [])
  async function run(operation: 'backup_data' | 'restore_data') {
    setBusy(true); setMessage(''); setError(false)
    try {
      const result = await invoke<string | null>(operation)
      if (result) {
        if (operation === 'restore_data') queryClient.clear()
        setMessage(result)
      }
    } catch (e) { setError(true); setMessage(getApiError(e)) }
    finally { setBusy(false) }
  }
  return <div className="page">
    <div className="page-heading"><div><span className="eyebrow">SEU COMPUTADOR, SEUS DADOS</span><h1>Backup e dados</h1><p>Uma cópia de segurança mantém seu histórico protegido.</p></div></div>
    <section className="panel data-panel">
      <h2>Perfil local</h2><p>Seus lançamentos ficam salvos neste computador, mesmo depois de fechar ou atualizar o aplicativo.</p>
      <label>Pasta de dados</label><code className="data-path">{directory || 'Carregando…'}</code>
      <h2>Salvar uma cópia</h2><p>Escolha onde guardar seu backup. Você pode copiá-lo para um dispositivo externo. O arquivo contém seu histórico financeiro e não é criptografado.</p>
      <button className="button primary" disabled={busy} onClick={() => void run('backup_data')}><Download size={18} /> Salvar backup</button>
      <h2>Restaurar um backup</h2><p>Substitui os dados atuais pelos dados do arquivo escolhido. Você precisará confirmar. Uma cópia dos dados atuais será preservada na pasta de dados.</p>
      <button className="button secondary" disabled={busy} onClick={() => void run('restore_data')}><Upload size={18} /> Restaurar backup</button>
      {busy && <p role="status">Conclua a seleção na janela do sistema e aguarde…</p>}
      {message && <p className={error ? 'form-error' : 'data-success'} role={error ? 'alert' : 'status'}>{message}</p>}
    </section>
  </div>
}
