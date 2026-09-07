# Validação — FinanSee Desktop

Validação local realizada em 6–7 de setembro de 2026. Nenhum banco do FinanSee Web foi acessado ou importado.

Este documento preserva o histórico dos testes técnicos. Depois deles, o RPM publicado na Release `v0.1.0` foi baixado novamente, instalado pelo DNF e aberto sem depender dos arquivos de desenvolvimento.

Em 7 de setembro de 2026, a limpeza para a versão `0.1.1` foi revalidada com os 32 testes do backend, Ruff, ESLint, teste do frontend, build Vite, `cargo check`, `cargo fmt`, Clippy, teste Rust, smoke test do sidecar e geração dos pacotes `.rpm` e `.deb`. O RPM local manteve o nome técnico `finanse-desktop`, necessário para atualizar a versão `0.1.0`, e o atalho gerado exibiu `FinanSee Desktop`. Esses pacotes `0.1.1` foram inspecionados localmente e não foram publicados nem instalados.

## Ambiente verificado

- Fedora Linux 44, x86_64, glibc 2.43; sessão gráfica Wayland.
- GTK3 3.24.52 e WebKitGTK 4.1 / WebKit 2.52.5.
- Python 3.14.7, PyInstaller 6.19.0.
- Node.js 22.23.1, npm 10.9.8, Vite 6.4.3.
- Rust 1.98.1; Tauri 2.11.5; tauri-driver 2.0.6.
- Rust e pacotes de desenvolvimento Linux foram obtidos em `.toolchain/`, dentro do projeto, sem instalar pacotes no sistema. As dependências Python e npm foram instaladas nesta pasta, a partir dos registros de pacotes.

## Resultados

| Verificação | Resultado |
| --- | --- |
| Backend (`pytest`) | **32 testes passaram** |
| Python / scripts (`ruff check`) | **Passou** |
| Frontend (`eslint`) | **Passou** |
| Formatação monetária no frontend (`node --test`) | **Passou**, incluindo totais acima da precisão inteira de JavaScript |
| TypeScript + build Vite | **Passou**; fontes e demais assets empacotados |
| Rust (`cargo check`) | **Passou** |
| Rust (`cargo fmt --check`) | **Passou** |
| Rust (`cargo clippy -- -D warnings`) | **Passou** |
| Teste Rust de restrições da comunicação nativa (`cargo test --release`) | **1 teste passou** |
| PyInstaller, executável Linux | **Gerado e executado com PATH vazio** |
| Compilação Tauri otimizada | **Passou** |
| Pacotes Linux `.deb` e `.rpm` | **Gerados e inspecionados** |
| Janela Tauri compilada com WebKitWebDriver | **Executada e validada** |
| Backup/restauração por diálogos nativos | **Executados e validados com AT-SPI** |
| Windows | **Não compilado nem testado** |

Dois avisos de depreciação aparecem nos testes Python, relativos à integração de teste Starlette/httpx e ao alias `BlockingPortal` do AnyIO. Não houve falhas de teste. O PyInstaller também informa imports opcionais ausentes de drivers MySQL/pysqlite2; o executável utiliza `sqlite3` da biblioteca padrão e passou nos testes empacotados.

## Comportamentos exercitados

**API e banco:** criação, leitura, alteração e exclusão de lançamentos; filtros combinados, busca em português, paginação estável; criação e conflitos de categorias; exclusão com preservação dos lançamentos; categorias iniciais sem reaparecer depois de apagadas; isolamento no perfil local; valores em centavos inteiros; limites de valor, casas decimais e campos nulos; dashboard, pendências e fronteiras mensais; migrações em banco novo e banco desktop existente; rejeição de revisão futura; backup/restauração, confirmação obrigatória, recuperação dos dados anteriores e rejeição de arquivos inválidos sem mudar dados atuais.

**Executável Python independente:** inicialização, health check protegido, recusa de credencial incorreta, porta dinâmica, instâncias em portas diferentes, bloqueio de uma segunda instância para o mesmo perfil, transação, backup, restauração, persistência ao reiniciar, troca de credencial e encerramento por comando ou EOF do pai. Tudo em pastas temporárias com dados sintéticos.

**Janela real:** abertura automática do dashboard, quatro cards, interface em português, ausência de login, navegação, oito categorias iniciais, criação de categoria, criação/edição/busca/exclusão de lançamento com valor de R$ 123,45, localização correta do banco, ausência de assets remotos, ausência de token em localStorage e segunda abertura encerrada sem duplicar a aplicação. O bloqueio do perfil foi liberado após fechar a janela.

**Diálogos nativos:** seleção de destino e salvamento do backup; abertura e cancelamento do seletor de restauração; seleção do backup, confirmação nativa de substituição e restauração bem-sucedida. Uma categoria criada depois do backup desapareceu após restaurar, e a interface atualizou os dados.

O WebKitWebDriver desta máquina não implementou injeção de cliques físicos, tanto em Wayland quanto na tentativa com XWayland. Os testes da interface dispararam eventos DOM na **janela Tauri real**, mantendo React, IPC, backend empacotado e SQLite reais. Os diálogos nativos foram operados através de AT-SPI; não foram substituídos por mocks.

Os registros e capturas com dados sintéticos foram gerados em `build/validation/` e removidos durante a limpeza posterior.

## Repetir os testes gráficos no Linux

Depois de compilar com os comandos do README e instalar `tauri-driver`/`WebKitWebDriver`:

```sh
python3 scripts/smoke_desktop.py
```

Para incluir os diálogos nativos, use o Python do sistema com PyGObject e a typelib AT-SPI disponíveis:

```sh
FINANSE_NATIVE_PROBE=1 GTK_A11Y=always NO_AT_BRIDGE=0 python3 scripts/smoke_desktop.py
```

Esses testes criam um perfil temporário separado; não usam o perfil real do aplicativo.

O toolchain isolado usado na validação foi removido. Instale os pré-requisitos descritos no README para repetir a compilação.

## Instaladores

- RPM `0.1.0-1.x86_64`, publicado na Release `v0.1.0`.
- Pacote `.deb` gerado e inspecionado, mas não publicado nem instalado.

O RPM inclui os dois executáveis, o atalho `.desktop`, os ícones, a licença MIT e os avisos/licenças de fontes, sem banco pré-populado. O arquivo baixado da Release foi comparado com o artefato original e os hashes SHA-256 eram iguais.

## Limitações verificadas

- O RPM foi instalado e executado no mesmo Fedora 44 usado para compilá-lo; ainda não foi testado em outra máquina limpa.
- O `.deb` foi gerado e inspecionado, mas não testado em Debian/Ubuntu. A glibc e bibliotecas vinculadas limitam a compatibilidade: este build não representa suporte verificado a distribuições mais antigas.
- O aplicativo Linux depende de GTK3/WebKitGTK e bibliotecas básicas do sistema. Para instalação totalmente offline, esses pacotes de sistema devem estar presentes ou disponíveis localmente.
- Windows tem caminhos, nome do sidecar e configuração de WebView2 offline preparados, mas não há compilação/execução Windows verificada.
- O RPM publicado não é assinado. Não há atualizador, sincronização, criptografia do banco ou importação automática do banco web.
- Backups aceitos têm até 256 MiB. Cópias automáticas de recuperação não são removidas automaticamente.
