import { existsSync } from 'node:fs'
import { spawnSync } from 'node:child_process'
import { fileURLToPath } from 'node:url'
import path from 'node:path'

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')
const python = path.join(root, '.venv', process.platform === 'win32' ? 'Scripts/python.exe' : 'bin/python')
if (!existsSync(python)) {
  console.error('Crie a .venv e instale backend/requirements-lock.txt antes de compilar. Consulte o README.')
  process.exit(1)
}
const result = spawnSync(python, [path.join(root, 'scripts/build_sidecar.py')], {
  cwd: root, stdio: 'inherit', env: { ...process.env, PYINSTALLER_CONFIG_DIR: path.join(root, 'build', 'pyinstaller-cache') },
})
if (result.error) console.error(result.error.message)
process.exit(result.status ?? 1)
