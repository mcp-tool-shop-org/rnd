<p align="center">
  <a href="README.ja.md">日本語</a> | <a href="README.zh.md">中文</a> | <a href="README.es.md">Español</a> | <a href="README.fr.md">Français</a> | <a href="README.hi.md">हिन्दी</a> | <a href="README.it.md">Italiano</a> | <a href="README.md">English</a>
</p>

<p align="center">
  <img src="https://raw.githubusercontent.com/mcp-tool-shop-org/brand/main/logos/rnd/readme.png" alt="Research and Development" width="400">
</p>

<p align="center">
  <a href="https://github.com/mcp-tool-shop-org/rnd/actions/workflows/ci.yml"><img src="https://github.com/mcp-tool-shop-org/rnd/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <a href="https://codecov.io/gh/mcp-tool-shop-org/rnd"><img src="https://codecov.io/gh/mcp-tool-shop-org/rnd/branch/main/graph/badge.svg" alt="Coverage"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="MIT License"></a>
  <a href="https://mcp-tool-shop-org.github.io/rnd/"><img src="https://img.shields.io/badge/Landing_Page-live-blue" alt="Landing Page"></a>
</p>

O banco de pesquisa do estúdio. As descobertas de qualquer área chegam rapidamente como entradas curtas em Markdown, com cada fonte identificada e cada afirmação marcada como verificada ou não. Os experimentos ficam ao lado das entradas que testam. Catálogos externos são espelhados e avaliados, e um registro lista as ferramentas do estúdio que a pesquisa pode utilizar. Um único comando pesquisa tudo isso.

## Onde está localizado: o banco de dados antes de readouts

Dois armazenamentos contêm o conhecimento do estúdio, e eles desempenham funções diferentes.

| | Pesquisa e Desenvolvimento (este repositório). | [readouts](https://github.com/mcp-tool-shop-org/readouts) |
|---|---|---|
| Função. | O banco: entrada, experimentos, questões em aberto. | A estante: bases de conhecimento verificadas. |
| Ritmo. | Uma entrada em minutos, as afirmações começam em `unverified`. | Criado e verificado por grupos de estudo. |
| Formato. | Entradas em Markdown, um tópico por vez. | Uma base de conhecimento SQLite por domínio. |
| Quão desorganizado. | Desorganizado de propósito: afirmações contestadas, becos sem saída e resultados intermediários permanecem visíveis. | Nada desorganizado: cada linha tem sua fonte e é verificada. |

O conhecimento se move em uma direção:

1. **Banco de dados.** Um resultado é registrado aqui como uma entrada. As suas alegações começam em `[unverified]`,
e são marcadas em `[verified]` apenas com uma nota do que as verificou.
As medições feitas nas nossas próprias máquinas são registadas como fontes em `rig`, com o seu
código em `experiments/`.
2. **Prateleira interna.** Uma vez que as alegações de suporte de carga de um tópico se confirmem, são integradas
numa base de conhecimento no repositório de trabalho privado em readouts, ou adicionadas a um.
**A promoção faz parte do encerramento de um experimento** (o Diretor, 2026-10-09). Quando
o resultado de um experimento é registado aqui, a sua atualização em readouts-internal segue
na mesma sessão ou na sessão seguinte, com os seus gráficos. Nada fica no banco de dados
por mais de uma semana. Atualizações pequenas e regulares são melhores do que uma grande. O
ficheiro README de um experimento regista a sua promoção como uma linha abaixo do seu resultado:
"Promovido: readouts-internal `<kb>` onda `<n>`, `<date>`", ou por que ainda não.
3. **Prateleira pública.** Uma base de conhecimento é publicada no repositório público readouts
quando é adicionada à lista de permissões de exportação.

`rnd readouts` pesquisa todas as bases de conhecimento readouts a partir daqui, então um único registro
acessa ambos os armazenamentos. Pesquise primeiro o banco de dados, depois a prateleira e, em seguida, analise a lacuna.

A pesquisa aqui não se limita aos próprios campos do estúdio. Cada entrada registra duas coisas separadamente: qual é o conhecimento e o que ele significa para o estúdio (`relevance: act | watch | reference`). `reference` é um veredicto bom.

## Use-o

Requer Python 3.10 ou posterior e nada mais (apenas a biblioteca padrão). Funciona em Windows, macOS e Linux. A partir da raiz do repositório:

```bash
python -m rnd search cuda graphs            # full-text over entries + catalogues (stemmed: pair finds pairs)
python -m rnd search --exact PAIR           # whole words, same case: the product, not the word
python -m rnd probe https://github.com/NVIDIA/NeMo-Relay   # licence, release, telemetry hits, already in rnd?
python -m rnd show 2026-10-07-cuda-graphs   # one entry, with backlinks
python -m rnd list --relevance act          # what needs doing
python -m rnd tools                         # instruments this seat can use
python -m rnd readouts splice glitch --any  # search the readouts knowledge bases too
python -m rnd catalog lanes                 # NVIDIA skills by lane, with studio fit
python -m rnd catalog list --fit adjacent   # skills worth using when the need arises
python -m rnd new "Paper title" --kind paper --field audio --tag pitch
python -m rnd check                         # validate every file (exit 1 on errors)
python -m rnd sql "SELECT tier, count(*) FROM sources GROUP BY tier"
python -m rnd bump --note "what changed"  # micro version bump + CHANGELOG section
```

Cada comando de listagem recebe `--json` para agentes. `rnd.cmd` (Windows) e `rnd.sh` (shells POSIX) são wrappers finos, então o comando funciona a partir de qualquer diretório.

Para usar a ferramenta de outros projetos, instale-a a partir de PyPI:

```bash
pip install mcptoolshop-rnd
```

Isso instala o comando `rnd`, não a biblioteca: as entradas estão neste repositório. O comando encontra uma biblioteca nesta ordem: `--library DIR`, depois `$RND_ROOT` e, em seguida, a pasta mais próxima acima ou na pasta atual que contém `entries/` e `instruments/`. Fora de uma biblioteca, ele para com `NO_LIBRARY`; apenas `rnd readouts` funciona sem uma.

Em Python, importe `mcptoolshop_rnd`: esse nome sempre funciona. `rnd` é mantido como um alias de compatibilidade, mas um pacote PyPI não relacionado também é chamado de `rnd`, e se ambos estiverem instalados, ele pode substituir o alias. O comando `rnd` e `python -m mcptoolshop_rnd` continuam funcionando de qualquer maneira.

A biblioteca muda diariamente, então as versões têm cinco segmentos, `MAJOR.MINOR.PATCH.MICRO.NANO`. Os três primeiros versionam a ferramenta `rnd`; MICRO marca uma mudança estrutural na biblioteca e NANO uma atualização comum. `rnd bump` aumenta o último segmento por padrão e escreve uma seção CHANGELOG dos arquivos alterados desde a última tag, para que cada atualização tenha sua própria versão pequena e marcada.

Códigos de saída: `0` ok · `1` arquivos de biblioteca inválidos · `2` erro de uso ou não encontrado · `3` falha em tempo de execução (uma ferramenta externa ou um erro inesperado). Os erros imprimem um código, uma mensagem e uma dica; `--debug` adiciona o rastreamento da pilha.

## Layout

| Caminho. | O que. | Quem edita. |
|------|------|-----------|
| `entries/YYYY/*.md` | Entradas de pesquisa: a fonte da verdade. | Pessoas e agentes. |
| `experiments/<name>/` | Mecanismos, entradas fixas e recibos de resultados para medições de equipamentos. | Pessoas e agentes. |
| `experiments/<name>/collect.json` | Registros coletados de um repositório de ferramentas em commits fixos (`rnd collect`). | Pessoas. |
| `instruments/*.md` | Ferramentas e protocolos do estúdio que o assento pode usar (`kind: instrument`). | Pessoas e agentes. |
| `catalogs/<name>/source.json` | De onde vem um catálogo. | Pessoas. |
| `catalogs/<name>/catalog.json` | Instantâneo fixo de `rnd catalog sync`. | Gerado; nunca edite manualmente. |
| `catalogs/<name>/review.json` | Ajuste e notas do estúdio por família e item. | Pessoas. |
| `datapacks/<name>/spec.json` | O que um pacote de dados contém: incluir globos, licenças, geradores, host. | Pessoas. |
| `datapacks/<name>/datapack.json` | Manifesto de `rnd datapack build`: SHA-256 de cada arquivo, licenças, fixações. | Gerado; nunca edite manualmente. |
| `datapacks/<name>/hosted.json` | Onde o upload foi feito (revisão do repositório). | Após um upload. |
| `mcptoolshop_rnd/` | A CLI. | Código. |
| `rnd/` | Alias de compatibilidade para `mcptoolshop_rnd`. | Código. |
| `rnd.db` | SQLite FTS5 índice, reconstruído automaticamente quando os arquivos são alterados. | Gerado; não está no git. |

## Formato de entrada

```markdown
---
id: 2026-10-07-cuda-graphs        # defaults to the file name
title: CUDA Graphs
date: 2026-10-07
kind: concept                     # finding concept release paper tool catalog rig-fact event question decision instrument
relevance: reference              # act | watch | reference
fields: [gpu-computing]           # any research field, open vocabulary
tags: [cuda-graphs, pytorch]
---

## Summary
## Key points
## Studio relevance
## Claims
- [unverified] A checkable statement.
- [verified] A checked statement. (via: what checked it, date)
## Sources
- [primary] https://… — publisher
```

- **Níveis de fonte:** `primary` (documentação do fornecedor, artigos, repositórios), `secondary` (relatos respeitáveis), `aggregator` (sites de resumo, saída de pesquisa de IA), `user` (fornecido por uma pessoa: slides, notas), `rig` (medido em nossas máquinas).
- **Confiança da afirmação:** `unverified`, `verified`, `disputed`, `wrong`. Uma afirmação `verified` ou `wrong` deve indicar o que a verificou com `(via: …)`.
- `[[entry-id]]` vincula entradas; `rnd show` lista backlinks.

## Pacotes de dados

Dados processados que são muito grandes ou volumosos para o clone são oferecidos como um **pacote de dados**: os bytes estão em um repositório de conjunto de dados do Hugging Face (privado até a publicação), e a biblioteca mantém apenas um manifesto pequeno. O modelo de integridade vem de [research-packs](https://github.com/mcp-tool-shop-org/research-packs): um manifesto, um SHA-256 para cada arquivo, uma verificação de um comando e uma listagem.

```bash
rnd datapack build natural-errors --source experiments/natural-errors  # reads datapacks/natural-errors/spec.json
rnd datapack list
hf download mcp-tool-shop/rnd-natural-errors --repo-type dataset --local-dir ne
rnd datapack verify natural-errors --copy ne/files                      # PASS when every byte matches
```

- **Cada arquivo precisa de uma licença** nas especificações. As saídas do modelo carregam os termos do modelo (por
exemplo, "Criado com Llama" para as saídas do Llama 3.1). `rnd datapack build` rejeita um pacote que
deixa um arquivo sem licença.
- **Cada modelo de geração é fixado** (hash Ollama, revisão do HF ou ID do modelo da API), com seu papel.
- **`rnd check` valida cada manifesto** e falha se um deles for editado manualmente.
- O upload carrega `datapack.json` junto com os arquivos, para que qualquer pessoa possa verificar sem este repositório:
`pip install mcptoolshop-rnd`.

## Registros de experimentos coletados

Um repositório de ferramentas registra suas próprias especificações e registros de execução pré-registrados (os comprovantes de interlock),
da mesma forma que cada repositório registra seu mapa do Atlas. A biblioteca publica apenas uma cópia resumida dos
números, criada por `rnd collect` a partir do repositório de ferramentas em commits fixos:

```bash
rnd collect                 # list the experiments that collect records
rnd collect e4b             # read each source with git show, trim it, write experiments/e4b/results/
rnd collect e4b --check     # recompute every output; exit 1 if any differs from the committed file
```

- **`experiments/<name>/collect.json`** nomeia o repositório, o clone irmão do qual ele é lido (`--clone` substitui), e cada fonte: seu caminho, o commit, o SHA-256 de seus bytes, a saída e a função de resumo no `extract.py` do experimento.
- **Uma fonte fixada nunca muda.** Bytes que não correspondem mais ao hash da fixação são rejeitados.
- **Cada registro carrega a proveniência:** o repositório, o caminho da fonte e o SHA-256 dos bytes resumidos.
- **Cada saída é segura para o público antes de ser gravada.** Nenhum caminho de máquina, diretório pessoal ou campo de ambiente sobrevive, e um módulo de experimento pode adicionar uma proteção mais rigorosa. Nada é gravado em caso de rejeição.

## Testando uma ferramenta antes de um teste

`rnd probe <url> …` responde às primeiras perguntas sobre uma ferramenta ou modelo a partir da própria API de cada fonte, e não a partir de um resumo de uma página da web:

- **GitHub** (através de `gh api`, por isso usa o seu login GitHub CLI): a licença, se está arquivado,
o último envio, a versão mais recente e uma pesquisa de código por "telemetria". Um resultado é um ponto de partida para ler, nunca uma prova;
zero resultados também não são prova.
- **Hugging Face:** a etiqueta de licença, ou para "outro", o nome e o link da licença do cartão; restrições; a última alteração.
- **PyPI e npm:** a licença, a versão mais recente e quando foi publicada.
- **rnd em si:** uma pesquisa exata da palavra para o nome, para que saiba se a biblioteca já o contém.

Uma fonte que não pode ser acessada é relatada como desconhecida, com o motivo.

## Monitorando fontes

`rnd watch` verifica as fontes em [docs/watchlist.json](docs/watchlist.json) e relata o que é novo desde a última verificação:

- O blog técnico da NVIDIA;
- a versão do kit de ferramentas CUDA;
- os novos modelos da NVIDIA no Hugging Face;
- o catálogo de habilidades da NVIDIA;
- os lançamentos dos mecanismos e ferramentas que o estúdio usa, como Ollama, OpenVINO, PyTorch, ComfyUI e Claude Code.

```bash
python -m rnd watch                  # what's new; records what it saw
python -m rnd watch --no-save --json # look without recording
python -m rnd watch --only ollama    # one source
```

What it saw is kept in a state file outside the repository (`$RND_WATCH_STATE`, else `~/.rnd/watch-state.json`).
A source's first check is a baseline: it records the current items and reports none as new. A pre-release is never reported as a source's latest version; a newer one is shown beside it. GitHub release notes and commit messages are kept in the JSON output, so a reader doesn't have to fetch each page. A source that
can't be reached is reported as unknown, and its state is left alone so nothing is skipped silently.

O comando é a metade determinística de um ritual semanal (Director, 2026-10-13). Um explorador lê os novos itens, testa qualquer ferramenta candidata com `rnd probe`, verifica a biblioteca com `rnd search --exact` e escreve um relatório curto e classificado: o que arquivar, o que tentar e o que ignorar. Adicione uma fonte por meio de uma solicitação de pull e diga por que ela é importante.

## Relação com outras ferramentas do estúdio

- **readouts** é a prateleira verificada para a qual este banco de dados fornece dados (veja acima).
- **research-os** cria um pacote de evidências congelado e restrito para um tópico. Um tópico no qual
uma decisão depende pode ser promovido a um pacote research-os, vinculado à entrada.
- **repo-knowledge** indexa os próprios repositórios do estúdio; esta biblioteca cobre
conhecimento de fora deles.
- As descobertas coletadas durante o projeto de algo também pertencem a este local, para que sobrevivam
à sessão que as produziu.

Veja `python -m rnd tools` para o registro completo de instrumentos e [docs/standards.md](docs/standards.md) para como o fluxo de trabalho se compara aos padrões de fluxo de trabalho do estúdio.

## Segurança e confiança

- **Dados acessados:** arquivos dentro deste repositório (`entries/`, `instruments/`,
`catalogs/`, `experiments/`) e o índice `rnd.db`, que ele reconstrói. `rnd
readouts` opens the readouts knowledge bases **read-only**. `rnd sql` é executado
contra uma conexão somente leitura.
- **Dados não acessados:** nada fora do repositório e do checkout readouts. Ele
não armazena credenciais e não lê nenhuma.
- **Rede:** nenhuma, exceto `rnd catalog sync`, que chama a API GitHub
através do seu próprio login CLI `gh` quando você a executa.
- **Permissões:** acesso normal a arquivos. Nenhum direito elevado, nenhum serviço em segundo plano.
- **Sem telemetria.** Nada é coletado ou enviado.
- **Higiene do repositório público:** antes de cada envio, a árvore é verificada em busca de
caminhos do diretório pessoal e identidade do operador.

Relate vulnerabilidades conforme descrito em [SECURITY.md](SECURITY.md).

## Testes

```bash
bash verify.sh                               # tests, library check, index build, smoke
python -m unittest discover -s tests -t .    # tests only
```

## Status e licença

Mantido pelo estúdio e em uso diário. Código: [MIT](LICENSE). Entradas: CC BY 4.0. O espelho de habilidades da NVIDIA em `catalogs/nvidia-skills/catalog.json` reproduz os nomes e descrições das habilidades de [NVIDIA/skills](https://github.com/NVIDIA/skills) sob as licenças desse projeto (Apache-2.0 para código, CC-BY-4.0 para texto de habilidades).

---

<p align="center">Built by <a href="https://mcp-tool-shop.github.io/">MCP Tool Shop</a></p>
