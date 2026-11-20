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

## Onde está: o banco antes de readouts

Duas áreas de armazenamento contêm o conhecimento do estúdio, e elas desempenham funções diferentes.

| | Pesquisa e Desenvolvimento (este repositório) | [readouts](https://github.com/mcp-tool-shop-org/readouts) |
|---|---|---|
| Função | o banco: entrada, experimentos, questões em aberto | a estante: bases de conhecimento verificadas |
| Ritmo | uma entrada em minutos, as afirmações começam em `unverified` | criado e verificado por grupos de estudo |
| Formato | entradas em Markdown, um tópico por vez | uma base de conhecimento SQLite por domínio |
| Quão bagunçado | bagunçado de propósito: afirmações contestadas, becos sem saída e resultados intermediários permanecem visíveis | nada bagunçado: cada linha tem sua fonte e é verificada |

O conhecimento se move em uma direção:

1. **Banco.** Uma descoberta chega aqui como uma entrada. Suas afirmações começam em `[unverified]` e são marcadas com `[verified]`, apenas com uma nota do que as verificou. As medições feitas em nossas próprias máquinas são inseridas como fontes `rig`, com seus mecanismos em `experiments/`.
2. **Estante interna.** Uma vez que as afirmações de suporte de um tópico se sustentem, ele é construído em uma base de conhecimento no repositório de trabalho privado readouts ou adicionado a um. **A promoção faz parte do encerramento de um experimento** (O Diretor, 2026-10-09). Quando o resultado de um experimento é confirmado aqui, sua atualização readouts-internal segue na mesma sessão ou na próxima, com seus gráficos. Nada fica no banco por mais de uma semana. Atualizações pequenas e regulares são melhores do que uma grande. O arquivo README de um experimento registra sua promoção como uma linha abaixo de seu resultado: "Promovido: readouts-internal `<kb>` onda `<n>`, `<date>`", ou por que ainda não.
3. **Estante pública.** Uma base de conhecimento é publicada no repositório público readouts quando é adicionada à lista de permissões de exportação.

`rnd readouts` pesquisa todas as bases de conhecimento readouts a partir daqui, então um único acesso alcança ambas as áreas de armazenamento. Pesquise o banco primeiro, a estante em segundo lugar e, em seguida, pesquise a lacuna.

A pesquisa aqui não se limita aos próprios campos do estúdio. Cada entrada registra duas coisas separadamente: qual é o conhecimento e o que ele significa para o estúdio (`relevance: act | watch | reference`). `reference` é um bom veredicto.

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
python -m rnd new-question "Why does X happen?" --field audio
python -m rnd sync --check                  # verify numbers bound to experiments/<id>/results.json
python -m rnd check                         # validate every file (exit 1 on errors)
python -m rnd similar 2026-10-07-cuda-graphs --limit 3  # closest claims in other entries (read-only)
python -m rnd digest --since v1.1.24.0.14   # entries, claims and questions changed since a tag or date
python -m rnd sql "SELECT tier, count(*) FROM sources GROUP BY tier"
python -m rnd change "what changed"         # add a changelog fragment under changes/ (nano by default)
python -m rnd bump --note "release note"    # release PR: apply changes/ fragments, bump version + CHANGELOG
```

Cada comando de listagem recebe `--json` para agentes. `rnd.cmd` (Windows) e `rnd.sh` (shells POSIX) são wrappers finos, então o comando funciona a partir de qualquer diretório.

Para usar a ferramenta de outros projetos, instale-a a partir de PyPI:

```bash
pip install mcptoolshop-rnd
```

Isso instala o comando `rnd`, não a biblioteca: as entradas estão neste repositório. O comando encontra uma biblioteca nesta ordem: `--library DIR`, depois `$RND_ROOT` e, em seguida, a pasta mais próxima em ou acima do diretório atual que contém `entries/` e `instruments/`. Fora de uma biblioteca, ele para com `NO_LIBRARY`; apenas `rnd readouts` funciona sem uma.

Em Python, importe `mcptoolshop_rnd`: esse nome sempre funciona. `rnd` é mantido como um alias de compatibilidade, mas um pacote PyPI não relacionado também é chamado de `rnd`, e se ambos estiverem instalados, ele pode substituir o alias. O comando `rnd` e `python -m mcptoolshop_rnd` continuam funcionando de qualquer maneira.

A biblioteca muda diariamente, então as versões têm cinco segmentos, `MAJOR.MINOR.PATCH.MICRO.NANO`. Os três primeiros versionam a ferramenta `rnd`; MICRO marca uma mudança estrutural na biblioteca e NANO uma atualização comum. As atualizações comuns adicionam um fragmento de registro de alterações abaixo de `changes/` por meio de `rnd change`; no momento do lançamento, `rnd bump` consome todos os fragmentos, move a versão uma vez pelo nível de fragmento mais alto e escreve uma seção CHANGELOG.

Códigos de saída: `0` ok · `1` arquivos de biblioteca inválidos · `2` erro de uso ou não encontrado · `3` falha em tempo de execução (uma ferramenta externa ou um erro inesperado). Os erros imprimem um código, uma mensagem e uma dica; `--debug` adiciona o rastreamento da pilha.

## Layout

| Caminho | O que | Quem edita |
|------|------|-----------|
| `entries/YYYY/*.md` | Entradas de pesquisa: a fonte da verdade | pessoas e agentes |
| `questions/*.md` | Perguntas de pesquisa abertas e respondidas | pessoas e agentes |
| `changes/*.md` | Fragmentos de registro de alterações não lançados (`rnd change`) | pessoas e agentes (`rnd bump` consome) |
| `experiments/<name>/` | Mecanismos, entradas fixas, `results.json` e recibos de resultados | pessoas e agentes |
| `experiments/<name>/collect.json` | Registros coletados de um repositório de ferramentas em commits fixos (`rnd collect`) | pessoas |
| `instruments/*.md` | Ferramentas e protocolos de estúdio que o assento pode usar (`kind: instrument`) | Apenas o assento de P&D (diferença revisada) |
| `catalogs/<name>/source.json` | De onde vem um catálogo | pessoas |
| `catalogs/<name>/catalog.json` | Instantâneo fixo de `rnd catalog sync` | gerado; nunca edite manualmente |
| `catalogs/<name>/review.json` | Ajuste e notas do estúdio por família e item | pessoas |
| `datapacks/<name>/spec.json` | O que um pacote de dados contém: padrões glob de inclusão, licenças, geradores, host | pessoas |
| `datapacks/<name>/datapack.json` | Manifesto de `rnd datapack build`: SHA-256 de cada arquivo, licenças, fixações | gerado; nunca edite manualmente |
| `datapacks/<name>/hosted.json` | Onde o upload foi feito (revisão do repositório) | após um upload |
| `mcptoolshop_rnd/` | A CLI | código |
| `rnd/` | Alias de compatibilidade para `mcptoolshop_rnd` | código |
| `rnd.db` | SQLite FTS5 índice, reconstruído automaticamente quando os arquivos são alterados | gerado; não está no git |
| `rnd.misses.jsonl` | Log de pesquisa local de zero acertos ao lado de `rnd.db` (`RND_NO_USAGE=1` desativa) | gerado; não está no git |

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
- [verified] [c-a1b2c3d4] A checked statement. (via: what checked it, date)
## Sources
- [primary] https://… — publisher
```

- **Níveis de fonte:** `primary` (documentação do fornecedor, artigos, repositórios), `secondary` (artigos respeitáveis), `aggregator` (sites de resumo, saída de pesquisa de IA), `user` (fornecido por uma pessoa: slides, notas), `rig` (medido em nossas próprias máquinas).
- **Confiança da afirmação:** `unverified`, `verified`, `disputed`, `wrong`, `superseded`. Uma afirmação `verified` ou `wrong` deve dizer o que a verificou com `(via: …)`.
- `[[entry-id]]` vincula entradas; `rnd show` lista backlinks.

## Fragmentos de registro de alterações

As atualizações não editam `mcptoolshop_rnd/__init__.py` ou `CHANGELOG.md` diretamente, portanto,
os ramos paralelos nunca entram em conflito na linha de versão:

```bash
python -m rnd change "Add study of XYZ"                # writes changes/YYYY-MM-DD-<hex>-<slug>.md (level: nano)
python -m rnd change "New tool feature" --level minor  # levels: nano | micro | patch | minor | major
python -m rnd bump --dry-run                           # preview version bump from changes/ fragments
python -m rnd bump                                     # release PR: bump once, update CHANGELOG.md, delete fragments
```

Sem arquivos em `changes/`, `rnd bump [nano|micro|…] [--note …]` mantém seu
comportamento git-diff. Tanto `__init__.py` quanto `CHANGELOG.md` são armazenados em cache por meio de
arquivos temporários e trocados com `os.replace`, revertendo `__init__.py` se a
troca do CHANGELOG falhar. Se uma falha deixar `__init__.py` à frente de `CHANGELOG.md`,
executar novamente no nível correspondente completa o incremento e qualquer outro nível
é rejeitado com `BAD_CHANGELOG`. Resta uma lacuna: uma falha após a troca de ambos os arquivos, mas antes da exclusão dos fragmentos em `changes/`, os deixa no
lugar, e uma nova execução incrementaria uma segunda vez, portanto, exclua esses fragmentos manualmente primeiro. `rnd check` relata qualquer
fragmento malformado como um erro.

## Números vinculados

Um experimento pode manter números de resumo seguros para o público em
`experiments/<id>/results.json` e vincular números em entradas, resumos ou
notas de experimento imediatamente após o literal:

```markdown
The judge scored 84.2%<!-- rnd:experiments/e4b/results.json#accuracy:.1% --> on the held-out split.
```

- Markdown bruto, `grep` e o índice SQLite mantêm o literal simples (`84.2%`);
GitHub e Starlight renderizam `84.2%` sem nenhum marcador ou link visível.
- `rnd sync [paths…]` reescreve literais vinculados de `results.json` usando a
  especificação de formato do Python; `rnd sync --check` sai com código `1` sem gravar se algum
  literal for diferente.
- `rnd check` trata qualquer literal vinculado fora de sincronia, arquivo ausente ou chave ausente
como um erro e emite um aviso em `[verified]`, quando o `(via: …)` nomeia um experimento de repositório
enquanto ainda mantém números não vinculados — ignorando inteiros simples (sem
ponto decimal, sinal de porcentagem, separador de milhares ou unidade final) que
se combinam com a palavra precedente no título ou nas tags da entrada ou seguem
`RTX` ou `GTX` (3–4 dígitos) ou `CUDA`, `PTX`, `Gemma`, `Llama`, `Qwen`,
`Claude`, `GPT` ou `Phi` (1–2 dígitos).

## IDs e links de afirmações

As afirmações podem conter IDs estáveis e determinísticos `c-<hex>` e relações explícitas
(`supersedes`, `contradicts`, `supports`) com afirmações mais antigas por ID:

```bash
python -m rnd claims                               # list indexed claims (--state superseded, --json)
python -m rnd claims assign <entry>                # add deterministic c-<hex> ids to one entry's claims
python -m rnd similar <entry> [--limit 5]          # closest claims in other entries (read-only)
python -m rnd reconcile <entry>                    # mark older claims (superseded / disputed / supported-by)
```

`rnd similar <entry>` executa uma consulta somente leitura SQLite FTS5 BM25 em `claims_fts`
para cada afirmação de `<entry>` em relação a outras entradas (`--limit` tem o padrão de 5),
marca `superseded` ou `disputed` com o que as substituiu ou contradisse,
imprime as cláusulas exatas `(supersedes: id)` / `(contradicts: id)` / `(supports: id)`
e o comando `rnd reconcile <entry>`, e nunca grava `rnd.db` ou qualquer
entrada. `rnd reconcile <entry>` grava apenas o ID (se ausente), o estado atualizado e a
relação inversa (`superseded-by`, `contradicted-by`, `supported-by`) na
linha da afirmação mais antiga em seu próprio arquivo, sem tocar em sua frase ou em qualquer outra
linha (deixando uma afirmação `[wrong]` `[wrong]` quando contradita). Tanto
`rnd claims assign` quanto `rnd reconcile` rejeitam (`MULTIPLE_CLAIMS_HEADINGS`)
sem gravar se uma entrada contiver mais de um cabeçalho real `## Claims`.
`rnd check` emite erros em IDs de destino quebrados, links unilaterais (sugerindo executar
`rnd reconcile` ou remover a cláusula e redefinir um estado `superseded` ou `disputed`) ou uma cerca de código não fechada,
e emite um aviso em uma afirmação `[superseded]` sem um link `(superseded-by: …)`.
`rnd search` e `rnd show` marcam as afirmações `superseded` e `disputed` e nomeiam a
afirmação que as substituiu ou contradisse.

## O que mudou (resumo)

`rnd digest --since <git ref or YYYY-MM-DD> [--json]` compara a biblioteca em um
commit anterior (analisado de objetos git na memória sem tocar na árvore de trabalho, índice git, `rnd.db` ou arquivos temporários) com a árvore atual:

```bash
python -m rnd digest --since v1.1.24.0.14
python -m rnd digest --since 2026-11-19 --json
```

Ele relata entradas adicionadas, afirmações adicionadas, afirmações removidas, alterações de estado de afirmação
(`old_state -> new_state` com o que as substituiu ou contradisse) e
perguntas abertas, respondidas (com os IDs das afirmações de resposta) e colocadas em espera, juntamente com
contagens. Uma data `YYYY-MM-DD` é resolvida para o commit mais recente ao longo da
linha do primeiro pai (`first-parent`) do branch atual (`HEAD`) cuja data do committer seja nesse dia ou
anterior a ele. As afirmações correspondem por `id` quando ambos os lados têm uma, caso contrário, por
`(entry, exact text)`, portanto, uma afirmação reformulada sem um ID aparece como uma afirmação
removida e uma afirmação adicionada, nunca como uma alteração de estado.

## Perguntas abertas

As perguntas abertas são armazenadas como arquivos Markdown individuais em `questions/` com o status
`open`, `investigating`, `answered` ou `parked`:

```bash
python -m rnd new-question "Does X hold on Y?" --field systems
python -m rnd questions --status open --json
```

Quando o `status` de uma pergunta é `answered`, sua lista `answered_by` no cabeçalho
deve nomear pelo menos um ID de afirmação existente; `rnd check` trata uma pergunta `answered`
sem um ID de afirmação existente como um erro. As perguntas são indexadas em
`rnd.db` e retornadas por `rnd search` e `rnd show`.

## Registro de falhas de pesquisa local

Quando `rnd search` não retorna correspondências, ele anexa uma linha JSON (`time` e
`query`) a um arquivo `.misses.jsonl` local ao lado de `rnd.db` (`rnd.misses.jsonl`
na raiz do repositório, ignorado pelo Git; ou `<stem>.misses.jsonl` ao lado de `--db` / `RND_DB`,
então `--db foo.db` grava `foo.misses.jsonl` ao lado dele, não `foo.db.misses.jsonl`).
Nada mais é registrado, nada é enviado pela rede, `RND_NO_USAGE=1`
desativa o registro e a exclusão do arquivo o remove completamente.
`rnd stats --usage` imprime a contagem total de falhas e as consultas mais frequentes que falharam.

## Arquivos de instrumento e extras opcionais

- **Arquivos de instrumento (`instruments/*.md`):** editados apenas pelo responsável pela pesquisa e desenvolvimento em um
diff revisado cuja descrição lista cada arquivo de instrumento alterado, nunca por uma
etapa ou comando que resume conteúdo externo (`rnd watch`, `rnd probe`,
`rnd collect`, `rnd catalog sync`).
- **Dependências e extras principais:** o núcleo de `rnd` permanece apenas na biblioteca padrão do Python. Qualquer extra opcional está em um grupo opcional e é importado de forma preguiçosa; um
comando que precisa de um extra ausente falha com `MISSING_EXTRA` e uma dica de instalação.

## Pacotes de dados

Dados processados muito grandes ou volumosos para o clone são oferecidos como um **pacote de dados**: os bytes estão
em um repositório de conjunto de dados do Hugging Face (privado até a publicação), e a biblioteca mantém apenas um manifesto pequeno. O modelo de integridade vem de
[research-packs](https://github.com/mcp-tool-shop-org/research-packs): um manifesto, um SHA-256 para
cada arquivo, uma verificação de um comando e uma listagem.

```bash
rnd datapack build natural-errors --source experiments/natural-errors  # reads datapacks/natural-errors/spec.json
rnd datapack list
hf download mcp-tool-shop/rnd-natural-errors --repo-type dataset --local-dir ne
rnd datapack verify natural-errors --copy ne/files                      # PASS when every byte matches
```

- **Cada arquivo precisa de uma licença** na especificação. As saídas do modelo carregam os termos do modelo (por
exemplo, "Criado com Llama" para as saídas do Llama 3.1). `rnd datapack build` rejeita um pacote que
deixa um arquivo sem cobertura.
- **Cada modelo de geração é fixado** (digest Ollama, revisão do HF ou ID do modelo da API), com seu papel.
- **`rnd check` valida cada manifesto** e falha em um manifesto editado manualmente.
- O upload carrega `datapack.json` ao lado dos arquivos, para que qualquer pessoa possa verificar sem este repositório:
`pip install mcptoolshop-rnd`.

## Registros de experimentos coletados

Um repositório de ferramentas confirma suas próprias especificações e registros de execução pré-registrados (interlock's recibos),
da mesma forma que cada repositório confirma seu mapa do Atlas. A biblioteca publica apenas uma cópia resumida dos
números, criada por `rnd collect` a partir do repositório de ferramentas em commits fixos:

```bash
rnd collect                 # list the experiments that collect records
rnd collect e4b             # read each source with git show, trim it, write experiments/e4b/results/
rnd collect e4b --check     # recompute every output; exit 1 if any differs from the committed file
```

- **`experiments/<name>/collect.json`** identifica o repositório, o clone irmão de onde os dados são lidos
(`--clone` substitui) e cada fonte: seu caminho, o commit, o SHA-256 de seus bytes, a
saída e a função de corte no `extract.py` do experimento.
- **Uma fonte fixa nunca muda.** Bytes que não correspondem mais ao hash da referência são rejeitados.
- **Cada registro carrega informações de origem:** o repositório, o caminho da fonte e o SHA-256 dos
bytes cortados.
- **Cada saída é segura para uso público antes de ser gravada.** Nenhum caminho de máquina, diretório pessoal ou
campo de ambiente é preservado, e um módulo de experimento pode adicionar uma proteção mais rigorosa. Nada é
gravado em caso de rejeição.

## Testando uma ferramenta antes de um teste

`rnd probe <url> …` responde às primeiras perguntas sobre uma ferramenta ou modelo a partir da própria API de cada fonte,
não a partir de um resumo de uma página da web:

- **GitHub** (através de `gh api`, portanto, usa seu login GitHub CLI): a licença, se está arquivado, o
último envio, a versão mais recente e uma pesquisa de código por "telemetria". Um resultado é um indicativo para ler, nunca uma prova;
zero resultados também não são prova.
- **Hugging Face:** a tag de licença ou, para "outro", o nome e o link da licença do cartão; restrições; a última alteração.
- **PyPI e npm:** a licença, a versão mais recente e quando foi publicado.
- **O próprio rnd:** uma pesquisa exata por palavra do nome, para que você saiba se a biblioteca já o contém.

Uma fonte que não pode ser acessada é relatada como desconhecida, com o motivo.

## Monitorando fontes

`rnd watch` verifica as fontes em [docs/watchlist.json](docs/watchlist.json) e relata o que é novo desde
a última verificação:

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

O que foi detetado é guardado num ficheiro de estado fora do repositório (`--state`, caso contrário `$RND_WATCH_STATE`, caso contrário `Path.home() / ".rnd" / "watch-state.json"`, `~/.rnd/watch-state.json`), a menos que `--no-save` seja fornecido.
A primeira verificação de uma fonte é uma linha de base: regista os itens atuais e indica que não há itens novos. Uma versão pré-lançamento nunca é relatada como a versão mais recente de uma fonte; se houver uma versão pré-lançamento mais recente, ela será mostrada ao lado da versão mais recente. As notas de lançamento GitHub e as mensagens de commit são guardadas no resultado JSON, para que o utilizador não tenha de aceder a cada página. Uma fonte que não pode ser alcançada é indicada como desconhecida e o seu estado é mantido inalterado, para que nada seja ignorado silenciosamente.

O comando é a metade determinística de um ritual semanal (Director, 2026-10-13). Um explorador lê os novos itens,
testa qualquer ferramenta candidata com `rnd probe`, verifica a biblioteca com `rnd search --exact` e escreve um breve
relatório classificado: o que arquivar, o que tentar e o que ignorar. Adicione uma fonte por meio de uma solicitação de pull e explique por que ela
é importante.

## Relação com outras ferramentas do estúdio

- **readouts** é a estante verificada que este banco alimenta (veja acima).
- **research-os** cria um pacote de evidências congelado e restrito para um tópico. Um tópico no qual
uma decisão depende pode evoluir para um pacote research-os, vinculado à entrada.
- **repo-knowledge** indexa os próprios repositórios do estúdio; esta biblioteca cobre
conhecimento de fora deles.
- As descobertas coletadas durante o projeto de algo também pertencem aqui, para que sobrevivam
à sessão que as produziu.

Veja `python -m rnd tools` para o registro completo de instrumentos e
[docs/standards.md](docs/standards.md) para como o fluxo de trabalho se compara aos
padrões de fluxo de trabalho do estúdio.

## Segurança e confiança

- **Dados gravados**, dependendo de onde são armazenados:
- **Dentro deste repositório** (a biblioteca: `--library`, caso contrário `$RND_ROOT`, caso contrário a pasta mais próxima em ou acima do diretório de trabalho que contém `entries/` e `instruments/`, caso contrário a cópia local do repositório a partir da qual o pacote é executado): `rnd new` (um novo arquivo em `entries/` ou `instruments/`, nunca sobrescrevendo), `rnd new-question` (`questions/`), `rnd new-experiment`,
  `rnd runs record` e `rnd collect <name>` (`experiments/<name>/`),
  `rnd claims assign`, `rnd reconcile` e `rnd sync` (linhas de afirmação e números vinculados em arquivos Markdown existentes), `rnd change` (`changes/`), `rnd bump`
  (`mcptoolshop_rnd/__init__.py` e `CHANGELOG.md`, por meio de arquivos temporários
  ao lado de cada um, e exclui os fragmentos de `changes/` que usou),
  `rnd catalog sync` (`catalogs/<name>/catalog.json`), `rnd datapack build`
  (`datapacks/<name>/datapack.json`) e `rnd layout` (`docs/layout.json`).
- **O índice:** `rnd.db`, ou o caminho fornecido por `--db` ou `$RND_DB`, com um arquivo temporário `.db.tmp` ao lado dele enquanto está sendo construído. `rnd build` o grava, e cada comando que lê o índice (`search`, `show`, `list`, `tools`,
`stats`, `catalog`, `claims`, `questions`, `sql`, `runs`, `ledger`, `where`,
`probe`) o reconstrói primeiro quando um arquivo de origem é alterado. O registro de falhas de pesquisa `rnd.misses.jsonl` fica ao lado dele (veja abaixo).
- **Sua pasta pessoal:** `rnd watch` grava seu arquivo de itens visualizados em `--state`, caso contrário
`$RND_WATCH_STATE`, caso contrário `~/.rnd/watch-state.json` (construído no código como
`Path.home() / ".rnd" / "watch-state.json"`), onde permanece entre as execuções. Ele é gravado por meio de um arquivo `.tmp` ao lado dele.
`--no-save` ignora a gravação.
- **Os armazenamentos de dados brutos, fora deste repositório:** `rnd raw ingest`, `rnd raw private` e
`rnd raw relicense` gravam no armazenamento público (`--public`, caso contrário `$RND_DATA`,
caso contrário `../rnd-data`) e no armazenamento privado (`--private`, caso contrário `$RND_DATA_PRIVATE`, caso contrário `../rnd-data-private`
ao lado da biblioteca; quando `rnd raw` é executado fora de uma biblioteca, `rnd-data-private`
ao lado do armazenamento público). `rnd raw ingest` também coloca
cada arquivo com mais de 256 KB no armazenamento de blobs, em `blobs/` na pasta
nomeada por `$RND_DATA_STORE_D` ou pela entrada `"d"` do armazenamento público
`store.local.json` (não há padrão; sem um, a ingestão é recusada). Os blobs são gravados por meio de um arquivo `.tmp` ao lado deles e marcados como somente leitura. Com `--link`, um novo blob é
um link físico para o arquivo de origem, portanto, **esse arquivo de origem também se torna somente leitura** (um blob
já no armazenamento é deixado intacto, assim como sua origem); sem `--link`, a
origem não é alterada. `rnd raw ingest --update` exclui nos dois armazenamentos os arquivos pequenos anteriores de uma execução antes de gravar os novos. `--dry-run` não grava nada.
- **Lido, nunca gravado:** `rnd readouts` (modo somente leitura do SQLite), clones de origem do `rnd collect` (`git show`), `rnd raw verify`, `rnd datapack verify --copy`,
  `rnd runs record --from`, `rnd abmine`, e `rnd similar` e `rnd digest`,
  que funcionam na memória e não gravam nada em lugar nenhum: nenhum arquivo temporário, nenhuma
  alteração na árvore de trabalho, no índice git ou no `rnd.db`.
- **Código que ele executa:** `rnd collect <name>`, com ou sem `--check`, carrega e executa
  `experiments/<name>/extract.py` (ou o módulo nomeado pelo `collect.json` dessa pasta)
  da biblioteca (`mcptoolshop_rnd/collect.py:142-149`). O Python pode
  armazenar em cache o bytecode desse módulo em `experiments/<name>/__pycache__/`. O `rnd` limita
  o que ele próprio grava a `experiments/<name>/`; não limita o que o código do próprio
  módulo faz, portanto, execute-o apenas em uma biblioteca em que você confia.
- **Fora do comando `rnd`:** o pacote também inclui
`mcptoolshop_rnd.localbuilders`, o conjunto de ferramentas do experimento local-builders. Nenhum comando `rnd` o executa. Quando executado diretamente (por exemplo,
`python -m mcptoolshop_rnd.localbuilders.runner`), na máquina alugada para a qual
foi escrito e em parte como root, ele cria, exclui e altera o proprietário e as permissões dos arquivos sob os caminhos
que seu chamador passa (caminhos de trabalho, pasta pessoal, histórico, ambiente virtual, recibo, log,
relatório, diretório secreto e sonda de contenção), e seu avaliador usa uma pasta temporária na pasta temporária do sistema operacional, removida quando termina.
- **Dados não tocados:** nenhum comando `rnd` grava, exclui ou altera um arquivo
em qualquer outro lugar. Ele não armazena credenciais e não lê nenhuma.
- **Rede:** nenhuma, exceto `rnd catalog sync`, `rnd probe` e `rnd watch`,
  que leem metadados públicos ou chamam a API do GitHub por meio do seu próprio login na CLI `gh`
  quando você os executa.
- **Permissões:** acesso normal a arquivos. Nenhum comando `rnd` precisa de privilégios elevados e não há nenhum serviço em segundo plano.
- **Log de uso somente local:** nada é coletado ou enviado para lugar nenhum. Quando `rnd search`
não retorna correspondências, ele anexa uma linha (hora UTC e consulta) a `rnd.misses.jsonl`
ao lado de `rnd.db` (ignorada pelo Git no repositório; com `--db foo.db`, `foo.misses.jsonl`
ao lado dele, não `foo.db.misses.jsonl`, e da mesma forma para `$RND_DB`). Defina
`RND_NO_USAGE=1` para desativá-lo e exclua o arquivo `.misses.jsonl` a qualquer
momento para limpá-lo. Nenhum outro dado de uso é registrado.
- **Higiene do repositório público:** antes de cada envio, a árvore é verificada em busca de
caminhos de diretório pessoal e identidade do operador.

Relate vulnerabilidades conforme descrito em [SECURITY.md](SECURITY.md).

## Testes

```bash
bash verify.sh                               # tests, library check, index build, smoke
python -m unittest discover -s tests -t .    # tests only
```

## Status e licença

Mantido pelo estúdio e em uso diário. Código: [MIT](LICENSE). Entradas: CC BY
4.0. O espelho de habilidades da NVIDIA em `catalogs/nvidia-skills/catalog.json`
reproduz os nomes e descrições das habilidades de
[NVIDIA/skills](https://github.com/NVIDIA/skills) sob as licenças desse projeto
(Apache-2.0 para código, CC-BY-4.0 para texto de habilidade).

---

<p align="center">Built by <a href="https://mcp-tool-shop.github.io/">MCP Tool Shop</a></p>
