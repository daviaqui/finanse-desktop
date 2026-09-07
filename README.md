# FinanSee Desktop

O **FinanSee Desktop é apenas a versão desktop do FinanSee Web**. Ele reaproveita a interface, as regras financeiras e o visual do sistema web em um aplicativo local para Linux.

A versão desktop funciona offline, usa um único perfil local e salva os dados em SQLite no próprio computador. Ela não exige servidor, Docker ou conta no FinanSee Web e não sincroniza dados com a versão web.

## Recursos

- Dashboard com saldo, receitas, despesas, valores pendentes e taxa de economia.
- Gráficos de fluxo de caixa e despesas por categoria.
- Criação, edição, exclusão, busca, filtros e paginação de lançamentos.
- Categorias personalizadas e categorias iniciais.
- Backup e restauração por seletores de arquivo nativos.
- Armazenamento local persistente e cálculos monetários em centavos inteiros.

## Instalação no Fedora

A versão Linux publicada foi compilada e testada no Fedora 44 para computadores `x86_64`.

A versão disponível atualmente é a `0.1.0`. O instalador mantém `Finanse.Desktop` no nome do arquivo por compatibilidade com o pacote original; no menu e na janela, o nome exibido é **FinanSee Desktop** a partir da versão `0.1.1`.

### Pela interface gráfica

1. Abra a [versão mais recente no GitHub](https://github.com/daviaqui/finanse-desktop/releases/latest).
2. Em **Assets**, baixe o arquivo terminado em `.rpm`.
3. Abra o arquivo baixado e escolha **Instalar**. Se ele não abrir no instalador do sistema, clique com o botão direito e escolha **Abrir com → Software**.
4. Procure **Finanse Desktop** na versão `0.1.0` ou **FinanSee Desktop** nas versões `0.1.1` e posteriores.

### Pelo terminal

Baixe o RPM da [página de versões](https://github.com/daviaqui/finanse-desktop/releases/latest) e execute, ajustando o nome caso exista uma versão mais nova:

```sh
sudo dnf install ~/Downloads/Finanse.Desktop-0.1.0-1.x86_64.rpm
```

O usuário do aplicativo instalado não precisa de Python, Node.js, Rust, Docker ou terminal. A conexão com a internet é necessária apenas para baixar o instalador.

### Atualização

Baixe o RPM da nova versão e instale-o com:

```sh
sudo dnf upgrade ~/Downloads/ARQUIVO_DA_NOVA_VERSAO.rpm
```

Os dados ficam fora da pasta de instalação e são preservados durante atualizações.

### Desinstalação

```sh
sudo dnf remove finanse-desktop
```

A desinstalação preserva os dados financeiros. Para removê-los definitivamente, feche o aplicativo e apague `~/.local/share/com.finanse.desktop/`. Faça um backup antes caso queira recuperar os dados depois.

## Dados, backup e restauração

No Linux, o banco principal fica normalmente em:

```text
~/.local/share/com.finanse.desktop/finanse.sqlite3
```

O caminho efetivo aparece em **Backup e dados** dentro do aplicativo. Use **Salvar backup** para criar uma cópia consistente e **Restaurar backup** para substituir os dados atuais após confirmação.

O aplicativo valida integridade, versão, estrutura e conteúdo antes de restaurar. O arquivo de backup contém dados financeiros e não é criptografado.

## Como funciona

```text
React e TypeScript
        │ comandos Tauri
        ▼
Tauri 2 / Rust
        │ loopback + credencial temporária
        ▼
FastAPI / Python
        │
SQLite local
```

O Tauri inicia e encerra automaticamente o backend Python empacotado. O backend escuta somente em `127.0.0.1`, usa uma porta disponível escolhida pelo sistema e exige uma credencial nova a cada execução. Uma segunda abertura apenas focaliza a janela existente.

Valores monetários são enviados como strings decimais e armazenados como centavos inteiros. Somas e totais usam `Decimal`, evitando erros de ponto flutuante nos dados financeiros.

## Desenvolvimento

Esta seção é somente para quem deseja alterar ou compilar o código. Usuários que instalaram o RPM não precisam destes passos.

Pré-requisitos:

- Node.js 22 ou mais recente e npm.
- Python 3.12 a 3.14.
- Rust estável.
- Bibliotecas de desenvolvimento do Tauri.

No Fedora:

```sh
sudo dnf install gcc gcc-c++ gtk3-devel webkit2gtk4.1-devel openssl-devel librsvg2-devel patchelf
```

Instale o Rust conforme a [documentação oficial do Tauri](https://v2.tauri.app/start/prerequisites/) e, na raiz do projeto, execute:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r backend/requirements-lock.txt
npm ci
npm --prefix frontend ci
npm run dev
```

`npm run dev` compila o sidecar, inicia o frontend de desenvolvimento e abre a janela Tauri.

## Compilação para Linux

```sh
npm run build:linux
```

O comando gera os pacotes em `src-tauri/target/release/bundle/`. O build inclui o frontend, o backend PyInstaller, migrações, fontes, ícones e licenças necessários para uso offline.

O RPM deve ser compilado no sistema Linux mais antigo que se pretende suportar. Binários criados no Fedora 44 não devem ser considerados compatíveis com distribuições mais antigas sem testes.

## Testes

Depois de instalar as dependências de desenvolvimento:

```sh
.venv/bin/python scripts/check.py
npm run sidecar
.venv/bin/python scripts/smoke_sidecar.py
```

Os testes cobrem CRUD de lançamentos, dashboard, categorias, precisão monetária, migrações, persistência, autenticação local e backup/restauração. Consulte [VALIDATION.md](VALIDATION.md) para os resultados já verificados.

## Plataformas

- Fedora 44 `x86_64`: compilado, instalado e executado.
- Debian/Ubuntu: pacote `.deb` gerado anteriormente, sem instalação validada.
- Windows: estrutura portátil preparada, sem build ou execução validada.

O aplicativo não possui sincronização, atualização automática, telemetria ou importação automática do banco do FinanSee Web.

## Licença

Consulte [LICENSE](LICENSE) e [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
