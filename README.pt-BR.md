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

Duas áreas armazenam o conhecimento do estúdio, e elas desempenham funções diferentes.

| | Pesquisa e Desenvolvimento (este repositório) | [readouts](https://github.com/mcp-tool-shop-org/readouts) |
|---|---|---|
| Função | o banco: entrada, experimentos, questões em aberto | a estante: bases de conhecimento verificadas |
| Ritmo | uma entrada em minutos, as afirmações começam em `unverified` | criado e verificado por grupos de estudo |
| Formato | entradas em Markdown, um tópico cada | uma base de conhecimento SQLite por domínio |
| Quão bagunçado | bagunçado de propósito: afirmações contestadas, becos sem saída e resultados intermediários permanecem visíveis | nada bagunçado: cada linha tem sua fonte e é verificada |

O conhecimento se move em uma direção:

1. **Banco.** Uma descoberta chega aqui como uma entrada. Suas afirmações começam em `[unverified]` e são marcadas com `[verified]`, apenas com uma nota do que as verificou. As medições feitas em nossas próprias máquinas são inseridas como fontes `rig`, com seus mecanismos em `experiments/`.
2. **Estante interna.** Uma vez que as afirmações de suporte de um tópico se sustentem, ele é construído em uma base de conhecimento no repositório de trabalho privado readouts ou adicionado a uma existente. **A promoção faz parte do encerramento de um experimento** (O Diretor, 2026-10-09). Quando o resultado de um experimento é confirmado aqui, sua atualização readouts-internal segue na mesma sessão ou na próxima, com seus gráficos. Nada fica no banco por mais de uma semana. Atualizações pequenas e regulares são melhores do que uma grande. O arquivo README de um experimento registra sua promoção como uma linha abaixo de seu resultado: "Promovido: readouts-internal `<kb>` onda `<n>`, `<date>`", ou por que ainda não.
3. **Estante pública.** Uma base de conhecimento é publicada no repositório público readouts quando é adicionada à lista de permissões de exportação.

`rnd readouts` pesquisa todas as bases de conhecimento readouts a partir daqui, então um único acesso alcança ambas as áreas. Pesquise o banco primeiro, a estante em segundo lugar e, em seguida, pesquise a lacuna.

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
python -m rnd sql "SELECT tier, count(*) FROM sources GROUP BY tier"
python -m rnd change "what changed"         # add a changelog fragment under changes/ (nano by default)
python -m rnd bump --note "release note"    # release PR: apply changes/ fragments, bump version + CHANGELOG
```

Cada comando de listagem recebe `--json` para agentes. `rnd.cmd` (Windows) e `rnd.sh` (shells POSIX) são wrappers finos, então o comando funciona a partir de qualquer diretório.

Para usar a ferramenta em outros projetos, instale-a a partir de PyPI:

```bash
pip install mcptoolshop-rnd
```

Isso instala o comando `rnd`, não a biblioteca: as entradas estão neste repositório. O comando encontra uma biblioteca nesta ordem: `--library DIR`, depois `$RND_ROOT` e, em seguida, a pasta mais próxima acima ou na pasta atual que contém `entries/` e `instruments/`. Fora de uma biblioteca, ele para com `NO_LIBRARY`; apenas `rnd readouts` funciona sem uma.

Em Python, importe `mcptoolshop_rnd`: esse nome sempre funciona. `rnd` é mantido como um alias de compatibilidade, mas um pacote PyPI não relacionado também é chamado de `rnd`, e se ambos estiverem instalados, ele pode substituir o alias. O comando `rnd` e `python -m mcptoolshop_rnd` continuam funcionando de qualquer maneira.

A biblioteca muda diariamente, então as versões têm cinco segmentos, `MAJOR.MINOR.PATCH.MICRO.NANO`. Os três primeiros versionam a ferramenta `rnd`; MICRO marca uma mudança estrutural na biblioteca e NANO uma atualização comum. As atualizações comuns adicionam um fragmento de registro de alterações em `changes/` por meio de `rnd change`; no momento do lançamento, `rnd bump` consome todos os fragmentos, move a versão uma vez pelo nível de fragmento mais alto e escreve uma seção CHANGELOG.

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
| `rnd.misses.jsonl` | Log de pesquisa local de acertos zero ao lado de `rnd.db` (`RND_NO_USAGE=1` desativa) | gerado; não está no git |

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
comportamento git-diff. `rnd check` relata qualquer fragmento malformado como um erro.

## Números vinculados

Um experimento pode manter números de resumo seguros para o público em
`experiments/<id>/results.json` e vincular números em entradas, resumos ou
notas de experimento imediatamente após o literal:

```markdown
The judge scored 84.2%<!-- rnd:experiments/e4b/results.json#accuracy:.1% --> on the held-out split.
```

- Markdown bruto, `grep` e o índice SQLite mantêm o literal simples (`84.2%`);
GitHub e Starlight renderizam `84.2%` sem nenhum marcador ou link visível.
- `rnd sync [paths…]` reescreve literais vinculados de `results.json` usando a especificação de formato do Python; `rnd sync --check` sai com código `1` sem gravar se algum literal for diferente.
- `rnd check` trata qualquer literal vinculado fora de sincronia, arquivo ausente ou chave ausente como um erro e alerta sobre afirmações `[verified]` cujo `(via: …)` nomeia um experimento do repositório enquanto ainda mantêm números não vinculados.

## IDs e links de afirmações

As afirmações podem conter IDs estáveis e determinísticos `c-<hex>` e relações explícitas
(`supersedes`, `contradicts`, `supports`) com afirmações mais antigas por ID:

```bash
python -m rnd claims                               # list indexed claims (--state superseded, --json)
python -m rnd claims assign <entry>                # add deterministic c-<hex> ids to one entry's claims
python -m rnd reconcile <entry>                    # mark older claims (superseded / disputed / supported-by)
```

`rnd reconcile <entry>` grava apenas o ID (se ausente), o estado atualizado e a
relação inversa (`superseded-by`, `contradicted-by`, `supported-by`) na
linha da afirmação mais antiga em seu próprio arquivo, sem tocar em sua frase ou em qualquer outra
linha. `rnd check` gera erros em IDs de destino quebrados ou links unilaterais e sugere executar `rnd reconcile`. `rnd search` e `rnd show` marcam `superseded` e
`disputed` afirmações e nomeiam a afirmação que as substituiu ou contradisse.

## Perguntas em aberto

As perguntas em aberto existem como arquivos Markdown individuais em `questions/` com o status
`open`, `investigating`, `answered` ou `parked`:

```bash
python -m rnd new-question "Does X hold on Y?" --field systems
python -m rnd questions --status open --json
```

Quando o `status` de uma pergunta é `answered`, sua lista de metadados `answered_by`
deve nomear pelo menos um ID de afirmação existente; `rnd check` trata uma pergunta `answered`
sem um ID de afirmação existente como um erro. As perguntas são indexadas em
`rnd.db` e retornadas por `rnd search` e `rnd show`.

## Registro de falhas de pesquisa local

Quando `rnd search` não retorna correspondências, ele anexa uma linha JSON (`time` e
`query`) a um arquivo `.misses.jsonl` local ao lado de `rnd.db` (`rnd.misses.jsonl`
na raiz do repositório, ignorado pelo Git; ou `<db>.misses.jsonl` ao lado de `--db` / `RND_DB`).
Nada mais é registrado, nada é enviado pela rede, `RND_NO_USAGE=1`
desativa o registro e a exclusão do arquivo o remove completamente.
`rnd stats --usage` imprime a contagem total de falhas e as consultas mais frequentes que não foram encontradas.

## Arquivos de instrumento e extras opcionais

- **Arquivos de instrumento (`instruments/*.md`):** editados apenas pelo responsável de P&D em uma
diferença revisada cuja descrição lista cada arquivo de instrumento alterado, nunca por um
passo ou comando que resume conteúdo externo (`rnd watch`, `rnd probe`,
`rnd collect`, `rnd catalog sync`).
- **Dependências principais e extras:** o núcleo de `rnd` permanece apenas na biblioteca padrão do Python.
Qualquer extra opcional reside em um grupo de adesão e é importado de forma preguiçosa; um
comando que precisa de um extra ausente falha com `MISSING_EXTRA` e uma dica de instalação.

## Pacotes de dados

Dados processados muito grandes ou volumosos para o clone são oferecidos como um **pacote de dados**: os bytes residem
em um repositório de conjunto de dados do Hugging Face (privado até a publicação), e a biblioteca mantém apenas um pequeno
manifesto. O modelo de integridade vem de
[research-packs](https://github.com/mcp-tool-shop-org/research-packs): um manifesto, um SHA-256 para
cada arquivo, uma verificação de um comando e uma listagem.

```bash
rnd datapack build natural-errors --source experiments/natural-errors  # reads datapacks/natural-errors/spec.json
rnd datapack list
hf download mcp-tool-shop/rnd-natural-errors --repo-type dataset --local-dir ne
rnd datapack verify natural-errors --copy ne/files                      # PASS when every byte matches
```

- **Cada arquivo precisa de uma licença** na especificação. As saídas do modelo carregam os termos do modelo (por
exemplo, "Criado com Llama" para as saídas do Llama 3.1). `rnd datapack build` recusa um pacote que
deixa um arquivo sem cobertura.
- **Cada modelo de geração é fixado** (digest Ollama, revisão do HF ou ID do modelo da API), com seu papel.
- **`rnd check` valida cada manifesto** e falha em um manifesto editado manualmente.
- O upload carrega `datapack.json` ao lado dos arquivos, para que qualquer pessoa possa verificar sem este repositório:
`pip install mcptoolshop-rnd`.

## Registros de experimentos coletados

Um repositório de ferramentas confirma suas próprias especificações pré-registradas e registros de execução (recibos de interlock),
da mesma forma que cada repositório confirma seu mapa do Atlas. A biblioteca publica apenas uma cópia resumida dos
números, criada por `rnd collect` a partir do repositório de ferramentas em commits fixos:

```bash
rnd collect                 # list the experiments that collect records
rnd collect e4b             # read each source with git show, trim it, write experiments/e4b/results/
rnd collect e4b --check     # recompute every output; exit 1 if any differs from the committed file
```

- **`experiments/<name>/collect.json`** nomeia o repositório, o clone irmão do qual ele é lido
(`--clone` substitui), e cada fonte: seu caminho, o commit, o SHA-256 de seus bytes, a
saída e a função de resumo no `extract.py` do experimento.
- **Uma fonte fixada nunca muda.** Bytes que não correspondem mais ao hash do fixo são recusados.
- **Cada registro carrega a proveniência:** o repositório, o caminho da fonte e o SHA-256 dos
bytes resumidos.
- **Cada saída é segura para o público antes de ser gravada.** Nenhum caminho de máquina, diretório pessoal ou
campo de ambiente sobrevive, e um módulo de experimento pode adicionar uma proteção mais rigorosa. Nada é
gravado em caso de recusa.

## Testando uma ferramenta antes de um teste

`rnd probe <url> …` responde às primeiras perguntas sobre uma ferramenta ou modelo da própria API de cada fonte,
não de um resumo de uma página da web:

- **GitHub** (através de `gh api`, para que ele use seu login GitHub CLI): a licença, se está arquivado, o
último envio, a versão mais recente e uma pesquisa de código por "telemetria". Uma correspondência é um indicativo para ler, nunca uma prova;
zero correspondências também não são prova.
- **Hugging Face:** a tag de licença ou, para "outro", o nome e o link da licença do cartão; restrições; a última alteração.
- **PyPI e npm:** a licença, a versão mais recente e quando foi publicada.
- **rnd em si:** uma pesquisa exata por palavra do nome, para que você saiba se a biblioteca já o possui.

Uma fonte que não pode ser alcançada é relatada como desconhecida, com o motivo.

## Monitorando fontes

`rnd watch` verifica as fontes em [docs/watchlist.json](docs/watchlist.json) e relata o que é novo desde
a última verificação:

- O blog técnico da NVIDIA;
- a versão do kit de ferramentas CUDA;
- os novos modelos da NVIDIA no Hugging Face;
- o catálogo de habilidades da NVIDIA;
- os lançamentos dos mecanismos e ferramentas que o estúdio executa, como Ollama, OpenVINO, PyTorch, ComfyUI e Claude Code.

```bash
python -m rnd watch                  # what's new; records what it saw
python -m rnd watch --no-save --json # look without recording
python -m rnd watch --only ollama    # one source
```

O que é detectado é armazenado num ficheiro de estado fora do repositório (`$RND_WATCH_STATE`, caso contrário `~/.rnd/watch-state.json`).
A primeira verificação de uma fonte é uma linha de base: regista os itens atuais e não reporta nenhum como novo. Uma versão prévia nunca é reportada como a versão mais recente de uma fonte; se houver uma versão prévia mais recente, ela é mostrada ao lado da versão mais recente. As notas de lançamento GitHub e as mensagens de commit são armazenadas no output JSON, para que o utilizador não tenha de obter cada página. Uma fonte que não pode ser alcançada é reportada como desconhecida, e o seu estado é deixado como está, para que nada seja ignorado silenciosamente.

O comando é a metade determinística de um ritual semanal (Director, 2026-10-13). Um explorador lê os novos itens, testa qualquer ferramenta candidata com `rnd probe`, verifica a biblioteca com `rnd search --exact` e escreve um relatório curto e classificado: o que arquivar, o que tentar e o que ignorar. Adicione uma fonte através de um pedido de alteração e explique por que é importante.

## Relação com outras ferramentas do estúdio

- **readouts** é a estante verificada que este banco alimenta (ver acima).
- **research-os** cria um pacote de evidências congelado e restrito para um tópico. Um tópico do qual uma decisão depende pode evoluir para um pacote research-os, ligado à entrada.
- **repo-knowledge** indexa os próprios repositórios do estúdio; esta biblioteca cobre o conhecimento de fora deles.
- Os resultados recolhidos durante a conceção de algo também pertencem aqui, para que sobrevivam à sessão que os produziu.

Consulte `python -m rnd tools` para o registo completo de instrumentos e [docs/standards.md](docs/standards.md) para saber como o fluxo de trabalho se compara com os padrões de fluxo de trabalho do estúdio.

## Segurança e confiança

- **Dados acessados:** ficheiros dentro deste repositório (`entries/`, `questions/`, `changes/`, `instruments/`, `catalogs/`, `experiments/`), o índice `rnd.db` e o seu ficheiro de registo local de falhas `rnd.misses.jsonl`. `rnd readouts` abre as bases de conhecimento readouts em modo de **apenas leitura**. `rnd sql` é executado numa ligação de apenas leitura.
- **Dados não acessados:** nada fora do repositório e da área de trabalho readouts. Não armazena credenciais e não lê nenhuma.
- **Rede:** nenhuma, exceto `rnd catalog sync`, `rnd probe` e `rnd watch`, que leem metadados públicos ou chamam a API do GitHub por meio do seu próprio login na CLI `gh` quando você os executa.
- **Permissões:** acesso normal a ficheiros. Sem privilégios elevados, sem serviço em segundo plano.
- **Registo de utilização apenas local:** nada é recolhido ou enviado para nenhum lugar. Quando `rnd search` não retorna correspondências, adiciona uma linha (hora UTC e consulta) a `rnd.misses.jsonl` ao lado de `rnd.db` (ignorado pelo Git no repositório, ou `<db>.misses.jsonl` ao lado de `--db` / `$RND_DB`). Defina `RND_NO_USAGE=1` para desativá-lo e elimine `.misses.jsonl` a qualquer momento para limpá-lo. Nenhum outro dado de utilização é registado.
- **Higiene do repositório público:** antes de cada envio, a árvore é verificada para detetar caminhos do diretório pessoal e a identidade do operador.

Reporte vulnerabilidades conforme descrito em [SECURITY.md](SECURITY.md).

## Testes

```bash
bash verify.sh                               # tests, library check, index build, smoke
python -m unittest discover -s tests -t .    # tests only
```

## Estado e licença

Mantido pelo estúdio e em uso diário. Código: [MIT](LICENSE). Entradas: CC BY 4.0. O espelho das competências da NVIDIA em `catalogs/nvidia-skills/catalog.json` reproduz os nomes e descrições das competências de [NVIDIA/skills](https://github.com/NVIDIA/skills) sob as licenças desse projeto (Apache-2.0 para o código, CC-BY-4.0 para o texto das competências).

---

<p align="center">Built by <a href="https://mcp-tool-shop.github.io/">MCP Tool Shop</a></p>
