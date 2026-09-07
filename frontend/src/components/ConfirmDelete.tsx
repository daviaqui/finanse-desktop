import { Modal } from './Modal'

export function ConfirmDelete({ description, busy, onCancel, onConfirm }: { description: string; busy: boolean; onCancel: () => void; onConfirm: () => void }) {
  return <Modal title="Confirmar exclusão" onClose={onCancel}>
    <p>{description}</p>
    <div className="form-actions">
      <button className="button secondary" onClick={onCancel} disabled={busy}>Cancelar</button>
      <button className="button primary" onClick={onConfirm} disabled={busy}>{busy ? 'Excluindo…' : 'Excluir'}</button>
    </div>
  </Modal>
}
