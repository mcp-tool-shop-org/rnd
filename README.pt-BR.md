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

## Onde está: o banco antes das leituras

Duas coleções armazenam o conhecimento do estúdio, e elas desempenham funções diferentes.

| | Pesquisa e Desenvolvimento (este repositório) | [readouts](https://github.com/mcp-tool-shop-org/readouts) |
|---|---|---|
| Função | o banco: entrada, experimentos, questões em aberto | a estante: bases de conhecimento verificadas |
| Ritmo | uma entrada em minutos, as afirmações começam em `unverified` | criado e verificado por grupos de estudo |
| Formato | entradas em Markdown, um tópico por vez | uma base de conhecimento SQLite por domínio |
| Desordem | esperado: afirmações contestadas, becos sem saída e resultados intermediários permanecem visíveis | nenhum: as linhas são provenientes e verificadas |

O conhecimento se move em uma direção:

1. **Banco.** Uma descoberta chega aqui como uma entrada. Suas afirmações começam em `[unverified]` e são marcadas com `[verified]`, apenas com uma nota do que as verificou. As medições feitas em nossas próprias máquinas são inseridas como fontes `rig`, com seus mecanismos sob `experiments/`.
2. **Estante interna.** Uma vez que as afirmações de suporte de um tópico se sustentem, ele é construído em uma base de conhecimento no repositório de trabalho privado das leituras ou adicionado a ele.
3. **Estante pública.** Uma base de conhecimento é publicada no repositório público de leituras quando é adicionada à lista de permissões de exportação.

`rnd readouts` pesquisa todas as bases de conhecimento de leituras a partir daqui, então um único local alcança ambas as coleções. Pesquise o banco primeiro, a estante em segundo lugar e, em seguida, pesquise a lacuna.

A pesquisa aqui não se limita aos próprios campos do estúdio. Cada entrada registra duas coisas separadamente: qual é o conhecimento e o que ele significa para o estúdio (`relevance: act | watch | reference`). `reference` é um veredicto bom.

## Use-o

Requer Python 3.10 ou posterior e nada mais (apenas a biblioteca padrão). Funciona em Windows, macOS e Linux. A partir da raiz do repositório:

```bash
python -m rnd search cuda graphs            # full-text over entries + catalogues
python -m rnd show 2026-10-07-cuda-graphs   # one entry, with backlinks
python -m rnd list --relevance act          # what needs doing
python -m rnd tools                         # instruments this seat can use
python -m rnd readouts splice glitch --any  # search the readouts knowledge bases too
python -m rnd catalog lanes                 # NVIDIA skills by lane, with studio fit
python -m rnd catalog list --fit adjacent   # skills worth using when the need arises
python -m rnd new "Paper title" --kind paper --field audio --tag pitch
python -m rnd check                         # validate every file (exit 1 on errors)
python -m rnd sql "SELECT tier, count(*) FROM sources GROUP BY tier"
```

Cada comando de listagem recebe `--json` para agentes. `rnd.cmd` (Windows) e `rnd.sh` (shells POSIX) são wrappers finos, então o comando funciona de qualquer diretório.

Códigos de saída: `0` ok · `1` arquivos de biblioteca inválidos · `2` erro de uso ou não encontrado · `3` falha em tempo de execução (uma ferramenta externa ou um erro inesperado). Os erros imprimem um código, uma mensagem e uma dica; `--debug` adiciona o rastreamento da pilha.

## Layout

| Caminho | O que | Quem edita |
|------|------|-----------|
| `entries/YYYY/*.md` | Entradas de pesquisa: a fonte da verdade | pessoas e agentes |
| `experiments/<name>/` | Mecanismos, entradas fixas e recibos de resultados para medições de equipamentos | pessoas e agentes |
| `instruments/*.md` | Ferramentas e protocolos do estúdio que o local pode usar (`kind: instrument`) | pessoas e agentes |
| `catalogs/<name>/source.json` | De onde vem um catálogo | pessoas |
| `catalogs/<name>/catalog.json` | Instantâneo fixo de `rnd catalog sync` | gerado; nunca edite manualmente |
| `catalogs/<name>/review.json` | Ajuste e notas do estúdio por família e item | pessoas |
| `rnd/` | A CLI | código |
| `rnd.db` | Índice SQLite FTS5, reconstruído automaticamente quando os arquivos são alterados | gerado; não está no git |

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
- **Confiança da afirmação:** `unverified`, `verified`, `disputed`, `wrong`. Uma afirmação `verified` ou `wrong` deve dizer o que a verificou com `(via: …)`.
- `[[entry-id]]` vincula entradas; `rnd show` lista backlinks.

## Relação com outras ferramentas do estúdio

- **readouts** é a estante verificada que este banco alimenta (veja acima).
- **research-os** cria um pacote de evidências congelado e com acesso restrito para um tópico. Um tópico no qual uma decisão depende pode ser promovido a um pacote research-os, vinculado a partir da entrada.
- **repo-knowledge** indexa os próprios repositórios do estúdio; esta biblioteca cobre o conhecimento de fora deles.
- As descobertas coletadas durante o projeto de algo também pertencem aqui, para que sobrevivam à sessão que as produziu.

Veja `python -m rnd tools` para o registro completo de instrumentos e [docs/standards.md](docs/standards.md) para como o fluxo de trabalho se compara aos padrões de fluxo de trabalho do estúdio.

## Segurança e confiança

- **Dados acessados:** arquivos dentro deste repositório (`entries/`, `instruments/`, `catalogs/`, `experiments/`) e o índice `rnd.db`, que ele reconstrói. `rnd readouts` opens the readouts knowledge bases **read-only**. `rnd sql` é executado em uma conexão somente leitura.
- **Dados não acessados:** nada fora do repositório e do checkout de leituras. Não armazena credenciais e não lê nenhuma.
- **Rede:** nenhuma, exceto `rnd catalog sync`, que chama a API do GitHub por meio do seu próprio login CLI `gh` quando você a executa.
- **Permissões:** acesso normal a arquivos. Nenhum direito elevado, nenhum serviço em segundo plano.
- **Sem telemetria.** Nada é coletado ou enviado.
- **Higiene do repositório público:** antes de cada envio, a árvore é verificada em busca de caminhos do diretório pessoal e identidade do operador.

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
