import axios, { AxiosError } from 'axios'
import { invoke } from '@tauri-apps/api/core'

// Preserve the original API contract. HTTP and the credential remain in Rust.
export const api = axios.create({
  baseURL: '/api/v1',
  headers: { 'Content-Type': 'application/json' },
  adapter: async (config) => {
    const result = await invoke<{ status: number; data: unknown }>('api_request', {
      method: (config.method ?? 'get').toUpperCase(),
      path: axios.getUri(config),
      body: config.data ? JSON.parse(config.data) : null,
    })
    const response = { ...result, statusText: '', headers: {}, config }
    if (result.status >= 400) throw new AxiosError('Falha na operação', 'ERR_BAD_RESPONSE', config, null, response)
    return response
  },
})

export function getApiError(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail
    if (typeof detail === 'string') return detail
  }
  if (typeof error === 'string') return error
  if (error instanceof Error) return error.message
  return 'Não foi possível concluir a operação. Tente novamente.'
}
