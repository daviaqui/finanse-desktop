# Finanse Desktop

Aplicativo de finanças pessoais offline, com a interface React/TypeScript e a lógica FastAPI reaproveitadas do projeto **Sistema Financeiro**. A instalação abre uma janela Tauri 2 e inicia seu próprio backend Python empacotado; o usuário final não precisa de Docker, Python, Node.js, terminal ou conexão para usar as funções financeiras.

## Funcionalidades

- Dashboard mensal: receitas recebidas, despesas pagas, saldo, despesas pendentes e taxa de economia.

- Fluxo de caixa dos últimos seis meses e despesas pagas por categoria.

- Lançamentos: criação, edição, exclusão confirmada, busca, filtros por tipo/situação e paginação. A API também preserva filtros por categoria e intervalo de datas.

- Categorias personalizadas e oito categorias iniciais. Excluir uma categoria mantém seus lançamentos sem categoria.

- Um perfil local, sem cadastro, login ou sincronização externa.

- Backup e restauração através de diálogos nativos, com confirmação antes da substituição e cópia de recuperação dos dados anteriores.

- Fontes DM Sans/Manrope, ícones, scripts, estilos, Python e migrações empacotados localmente.

O projeto original foi tratado como somente leitura. Apenas arquivos de código, testes e licença foram reutilizados. Não foram copiados arquivos `.env`, bancos, dados financeiros, dependências instaladas ou histórico Git. Nenhum banco do projeto web é acessado ou importado automaticamente.

## Abrir o aplicativo no Linux

Um checkout contém somente o código-fonte: siga **Desenvolvimento** abaixo para instalar as dependências e abrir o aplicativo. Executáveis e instaladores precisam ser gerados pela compilação.

Depois de compilar, você pode registrar um atalho local e procurar **Finanse Desktop** no menu de aplicativos:

```sh
python3 scripts/install_user_launcher.py
```

O script valida e cria `~/.local/share/applications/com.finanse.desktop.desktop`, apontando para o executável desta pasta. Não altera associações de arquivos nem instala pacotes no sistema. Mantenha a pasta do projeto no mesmo lugar enquanto usar esse atalho. A instalação pelo RPM/DEB fornece um atalho independente da pasta do projeto.

## Desenvolvimento

Pré-requisitos **apenas para desenvolver/compilar**: Node.js 22+, npm, Python 3.12–3.14, Rust estável e bibliotecas nativas do Tauri. A versão verificada do toolchain está em `VALIDATION.md`. As dependências npm, Python e Rust estão fixadas pelos arquivos `package-lock.json`, `backend/requirements-lock.txt` e `src-tauri/Cargo.lock`.

Em Fedora, os pacotes de desenvolvimento usuais são:

```
sudo dnf install gcc gcc-c++ gtk3-devel webkit2gtk4.1-devel openssl-devel librsvg2-devel patchelf
```

Em Debian/Ubuntu com WebKitGTK 4.1 disponível:

```
sudo apt install build-essential libgtk-3-dev libwebkit2gtk-4.1-dev libssl-dev librsvg2-dev patchelf
```

Consulte os [pré-requisitos oficiais do Tauri](https://v2.tauri.app/start/prerequisites/) para outras distribuições. As primeiras instalações de dependências exigem internet; o aplicativo instalado não depende delas.

Na raiz deste projeto:

```
python3 -m venv .venv  
.venv/bin/python -m pip install -r backend/requirements-lock.txt  
npm ci  
npm --prefix frontend ci  
npm run dev
```

`npm run dev` gera o sidecar, inicia o Vite em `127.0.0.1:5173` e abre o Tauri. Abra pela janela desktop: carregar o Vite num navegador comum exibe uma orientação, pois as operações passam pela comunicação nativa. A porta fixa 5173 é exclusiva do servidor de desenvolvimento; o aplicativo instalado usa uma porta de backend escolhida pelo sistema operacional.

No Windows, crie a venv com `py -3 -m venv .venv` e use `.venv\\Scripts\\python.exe` nos comandos Python. O script npm encontra automaticamente a venv de cada plataforma. É necessário o toolchain MSVC e os pré-requisitos Windows do Tauri.

## Compilação e distribuição

```
npm run build:linux                 \# sidecar + frontend + pacotes .rpm e .deb  
npm run check:desktop               \# mesma compilação, sem gerar instaladores  
npm run sidecar                    \# gera apenas o executável Python
```

Os instaladores ficam em `src-tauri/target/release/bundle/`. O executável desktop e `finanse-backend` ficam lado a lado em `src-tauri/target/release/`; mantenha ambos juntos ao executar diretamente. O sidecar intermediário fica em `dist/` e em `src-tauri/binaries/` com o sufixo do target Rust. **Cada build Tauri reconstrói o sidecar**, evitando distribuir código Python antigo.

Para tentar um instalador Windows, execute em um computador Windows:

```
npm run tauri -- build --bundles nsis
```

A configuração usa o instalador **offline** do WebView2, que é incorporado durante o build Windows. Não há build Windows verificado nesta entrega. PyInstaller deve rodar na plataforma de destino; não basta passar um target Windows a um build Linux.

Os pacotes Linux usam GTK3/WebKitGTK 4.1 e as bibliotecas básicas da distribuição. Esses componentes de sistema precisam estar presentes para instalação/execução offline. O binário herda a versão mínima da glibc e das bibliotecas do sistema onde foi compilado; gere uma versão na distribuição mais antiga que pretende suportar. O pacote produzido em Fedora 44 não deve ser presumido compatível com Ubuntu antigo. Não foram habilitados atualização automática, telemetria, publicação ou assinatura de código.

## Armazenamento e atualizações

O identificador permanente é `com.finanse.desktop`. O Tauri fornece a pasta de dados do sistema:

| Sistema | Local padrão |
| - | - |
| Linux | `$XDG\_DATA\_HOME/com.finanse.desktop/`, ou `~/.local/share/com.finanse.desktop/` |
| Windows | `%APPDATA%\\com.finanse.desktop\\` |


O arquivo principal é `finanse.sqlite3`. Durante o uso, o SQLite pode criar `finanse.sqlite3-wal` e `finanse.sqlite3-shm`. `desktop.lock` protege o perfil contra acesso por outro sidecar. O caminho efetivo aparece na tela **Backup e dados**.

A pasta fica fora da instalação e não é apagada em reinicializações ou atualizações. Não altere o identificador do aplicativo ao atualizar. As categorias padrão são criadas somente quando o perfil é criado pela primeira vez; categorias apagadas não reaparecem ao reiniciar.

As migrações Alembic são específicas do desktop: `desktop\_001` cria o esquema SQLite e `desktop\_002` adiciona o índice de consultas por perfil/data. Elas são executadas automaticamente antes de liberar a interface. Antes de atualizar um banco existente, o aplicativo salva `pre-upgrade-\<revisão\>.sqlite3`. Bancos de versões futuras e bancos web não são tratados como bancos desktop compatíveis.

## Backup e restauração

1. Abra **Backup e dados → Salvar backup**, escolha o destino e confirme caso o arquivo já exista.

2. Guarde a cópia em outra pasta ou dispositivo. O arquivo contém dados financeiros e não é criptografado.

3. Para restaurar, escolha **Restaurar backup**, selecione um `.sqlite3` criado pelo Finanse Desktop e confirme **Substituir**.

O backup usa a API de backup online do SQLite; copiar apenas o arquivo principal enquanto há WAL aberto não é equivalente. O novo arquivo é produzido temporariamente e renomeado para o destino depois de concluído.

Na restauração, o aplicativo verifica tamanho (até 256 MiB), identificador, integridade, revisão, esquema exato, ausência de estruturas extras, chaves estrangeiras, perfil e valores dos registros. A cópia selecionada é aberta somente para leitura, copiada para uma área temporária e novamente validada. Migrações necessárias são aplicadas nessa cópia, preservando o arquivo selecionado. Os dados atuais são salvos em `pre-restore-\<id\>.sqlite3`; então o SQLite substitui o conteúdo do banco vivo dentro de uma transação de escrita. Requisições ao banco ficam serializadas durante a operação. A interface descarta seus dados em cache após o sucesso.

Arquivos de recuperação `pre-restore-\*.sqlite3` e `pre-upgrade-\*.sqlite3` também podem ser selecionados para restauração. O banco vivo e seus arquivos internos não podem ser sobrescritos pelo diálogo de backup. Não há rotação automática das cópias de recuperação; remova cópias antigas somente depois de confirmar que possui um backup útil.

## Arquitetura e precisão

```
React + TypeScript (assets locais, HashRouter)  
              │ comandos Tauri  
              ▼  
Rust: ciclo de vida, instância única, diálogos e HTTP restrito  
              │ 127.0.0.1:\<porta dinâmica\> + credencial de 256 bits  
              ▼  
FastAPI / SQLAlchemy / lógica original em Decimal  
              │  
SQLite em WAL + migrações Alembic + backup online
```

A credencial muda a cada inicialização, é enviada ao processo Python por stdin e fica somente em memória. Não é incluída em argumentos, arquivos, `localStorage` ou respostas ao frontend. O cliente HTTP nativo ignora proxies e redirecionamentos. A comunicação genérica permite apenas rotas financeiras conhecidas; backup e restauração passam por comandos nativos separados. O backend exige a credencial inclusive no health check, recusa cabeçalhos Origin e não expõe login, documentação ou CORS. O frontend não recebe permissão de shell, acesso genérico a arquivos ou HTTP.

A porta é reservada com `bind(("127.0.0.1", 0))` e o mesmo socket é entregue ao Uvicorn, sem intervalo para outro processo ocupar a porta. A segunda abertura foca a janela existente; um lock adicional protege o banco entre processos. Ao fechar, o Tauri solicita encerramento e aguarda um prazo limitado; o backend também observa EOF do stdin para encerrar se o pai desaparecer.

**Dinheiro:** a API usa strings decimais; SQLAlchemy converte para **centavos inteiros** (`BIGINT` com verificação `typeof(amount)='integer'`) ao persistir. São aceitos valores positivos de até `999999999999.99`, com no máximo duas casas decimais. `Decimal` faz as somas e subtrações do dashboard. Cards e tabelas formatam strings sem converter para ponto flutuante. A geometria e os eixos dos gráficos usam números aproximados; os valores persistidos e os totais financeiros permanecem exatos.

**SQLite:** UUIDs usam o tipo portátil do SQLAlchemy; enums têm restrições CHECK; chaves estrangeiras são habilitadas em cada conexão; exclusão de categoria preserva lançamentos via SET NULL. Datas são datas civis sem conversão de fuso, timestamps usam CURRENT\_TIMESTAMP. A busca preserva comparação sem diferenciar maiúsculas/minúsculas em português por casefold. As consultas continuam restritas ao mesmo UUID de perfil. A tabela de usuários foi mantida para reaproveitar relacionamentos, mas guarda apenas um perfil sintético com autenticação web desabilitada.

## Validação

```
.venv/bin/python -m pytest -q backend/tests  
.venv/bin/ruff check backend scripts  
npm --prefix frontend run lint  
npm --prefix frontend test  
npm --prefix frontend run build  
cargo fmt --manifest-path src-tauri/Cargo.toml -- --check  
cargo clippy --manifest-path src-tauri/Cargo.toml -- -D warnings  
cargo test --manifest-path src-tauri/Cargo.toml  
npm run sidecar  
.venv/bin/python scripts/smoke\_sidecar.py  
npm run check:desktop
```

O teste de sidecar usa somente dados sintéticos em pastas temporárias e executa o binário com PATH vazio. Para a janela real no Linux, instale `tauri-driver` (`cargo install tauri-driver --locked`) e disponibilize `WebKitWebDriver`; veja `scripts/smoke\_desktop.py` e `VALIDATION.md`.

Os testes do backend foram adaptados dos testes do projeto web. A cobertura adicional verifica centavos, arredondamento inválido, filtros, paginação estável, exclusão de categorias, migrações novas/existentes, recuperação, arquivos corrompidos/incompatíveis, autenticação local e persistência. Não executam comandos no projeto original nem carregam sua configuração.

## Problemas de inicialização

A janela mostra o carregamento até o backend responder e exibe uma mensagem se ocorrer falha ou timeout. Verifique espaço em disco e acesso à pasta informada. Se outro processo ainda estiver finalizando, aguarde alguns segundos e abra novamente. Não apague a pasta de dados para corrigir um problema de inicialização. Um banco de versão futura deve ser aberto com a versão correspondente do aplicativo; uma cópia válida pode ser recuperada em uma instalação compatível.

Consulte `VALIDATION.md` para distinguir o que foi testado nesta máquina das limitações de plataforma.
