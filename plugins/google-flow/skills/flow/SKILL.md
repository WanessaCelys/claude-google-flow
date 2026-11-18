---
name: flow
description: >-
  Ferramenta para gerar imagens (Nano Banana) e vídeos (Omni) no Google Flow pelo Chrome da própria pessoa gastando poucos tokens: gera uma a uma ou em lote, monta storyboard para aprovar, junta os vídeos num só e acompanha os gastos e os créditos que sobram em cada conta. Quem decide os prompts, a duração, o estilo e o formato é a pessoa; o Claude só escreve ou sugere prompts quando ela pede. Use sempre que for preciso gerar imagem ou vídeo no Flow, Nano Banana, Omni ou Veo do Flow, montar storyboard, unir vídeos gerados ou saber quanto crédito já foi gasto. Na primeira vez, conecta a conta e pergunta as preferências. Mostra o custo e pede confirmação antes de gastar crédito.
compatibility: Claude Code no computador da pessoa, com Python 3.10+, Playwright e Google Chrome. Não funciona no claude.ai pelo navegador (precisa abrir o Chrome local).
---

# Flow: imagens e vídeos no Google Flow

Robô que controla o Chrome da própria pessoa, já logado na conta Google dela, e faz os cliques do Flow (projeto, formato, modelo, enviar referência, gerar, esperar, baixar). O Claude dá uma ordem curta e recebe o arquivo pronto, em vez de operar a tela passo a passo (muito mais barato em tokens).

**Para que serve:** fazer o trabalho braçal do Flow (gerar, esperar, baixar, organizar, juntar) com poucos tokens e com os gastos sob controle. **Quem decide é a pessoa:** os prompts, quanto tempo cada vídeo tem, o estilo e o formato. Os prompts chegam prontos (ela escreveu, ou criou com o Claude na conversa antes de chamar a skill) e são usados exatamente como estão. Para **imagem**, se ela pedir que o Claude escreva, há receitas em `receitas/`. Como o Flow e o Omni funcionam (referências, limite de fala, logo, marca): `referencias/dicas-flow-omni.md`.

## Primeiro uso (uma vez por computador)

Faça nesta ordem, explicando cada passo em linguagem simples. **Todos os comandos `flow.py` rodam de dentro da pasta `scripts/` da skill.**

1. **Instalar:** `pip install playwright imageio-ffmpeg` (não precisa baixar navegador: usa o Chrome instalado; o `imageio-ffmpeg` é para juntar vídeos). Precisa de Python 3.10+ e do Google Chrome.
2. **Conferir:** `python flow.py verificar` diz o que falta (Playwright, Chrome, login).
3. **Conectar a conta do Flow:** `python flow.py login` abre uma janela do Chrome. **A pessoa entra na própria conta Google** nessa janela e deixa ela aberta. O Claude nunca digita senha. O login fica salvo em `~/.config/flow` (ou na pasta de `FLOW_HOME`) e não precisa repetir. Avise antes: os termos do Google costumam proibir automação, com risco de bloqueio da conta; a decisão de usar é da pessoa. Enquanto a janela do robô está aberta, programas do próprio computador conseguem controlá-la: no fim do trabalho, feche com `python flow.py fechar` (o login continua salvo).
4. **Perguntas iniciais:** rode `python flow.py preferencias`. Se disser "Sem preferências salvas", faça as perguntas abaixo (numa tela de perguntas, se der) e salve as respostas.

### Perguntas iniciais

| Pergunta | Opções | Campo |
|---|---|---|
| Formato mais usado? | 9:16 (Reels, TikTok) · 16:9 (YouTube, site) · 1:1 · Depende | `--formato 9:16` / `16:9` / `1:1` / `depende` |
| Em que resolução você quer baixar os vídeos? | **720p (recomendado)**: o tamanho original do Flow, sem custo extra, ótimo para Reels, TikTok e anúncios · **1080p**: +5 créditos por vídeo, além dos créditos da geração · **Depende do vídeo** | `--download 720p` / `1080p` / `depende` |
| Tem mais de uma conta do Flow e quer que o robô use todas? | Não, só uma (recomendado) · Sim | se sim, siga `referencias/varias-contas.md` |

```bash
python flow.py preferencias --formato 9:16 --download 720p
```

**Na pergunta das várias contas, avise o risco junto com a pergunta, antes da resposta:** os termos do Google costumam proibir automação e o uso de várias contas para somar créditos, e há risco de bloqueio, inclusive da conta paga. A decisão é da pessoa. Se ela disser sim, repita o aviso antes de conectar cada conta nova.

Para mudar depois: o mesmo comando só com o campo que muda. **Quando uma preferência for "depende", pergunte a cada pedido.**

### Fim da configuração (diga sempre, com as respostas dela)

> Tudo pronto: conta conectada e preferências salvas (formato, resolução, contas).
> Agora é só pedir. Exemplos:
> - "gera esta imagem: [seu prompt]"
> - "gera um vídeo de 10 s com esta imagem: [prompt]"
> - "quero um vídeo de 30 s com estas cenas: [roteiro e prompts]": mostro as opções de divisão e o storyboard antes de gastar.
>
> Os prompts são seus: uso exatamente como você mandar. Antes de qualquer geração mostro o custo e espero o seu ok.

## Antes de cada geração

1. Leia as preferências (`flow.py preferencias`).
2. **Use o prompt da pessoa exatamente como está**, sem reescrever, traduzir ou "melhorar": quem conhece o resultado que quer é ela. Só ajuste os parâmetros do comando (formato, duração, referências). Se notar algo que costuma dar erro (veja `referencias/dicas-flow-omni.md`: texto pedido na imagem, fala longa demais para a duração, marca sem logo anexado), avise em uma linha e pergunte se ela quer mudar. Vários prompts: monte um `lote`, um item por prompt.
3. **Sem prompt:** peça o prompt. Para **imagem**, se ela pedir que o Claude escreva, use a receita do tipo (`receitas/natural.md` para foto de celular, `institucional.md`, `produto.md`) e mostre o prompt antes de gerar. Prompt de vídeo é dela (ou criado com o Claude na conversa, antes de chamar a skill).
4. **Duração, formato e estilo são dela.** Se ela não disse a duração de um vídeo, pergunte; mostre a tabela de créditos por duração como informação (10 s é o mais barato por segundo: 1,5 crédito/s), sem escolher por ela.
5. **Sempre mostre o custo antes de produzir, em toda geração**, mesmo quando for zero. Uma tabela curta: cada item (imagem ou vídeo), duração, resolução, créditos de cada um, o total e o saldo que sobra (`flow.py saldo`). Imagem aparece como "0 créditos". Só gere depois do ok explícito da pessoa; vídeo só com `--confirmo` depois desse ok.
6. **Depois de gerar, diga quanto gastou e quanto sobrou.** O robô anota cada geração (`flow.py gastos` mostra o acumulado por tipo e por conta; `flow.py saldo`, o saldo de agora).

## Modo projeto (pedido com várias cenas)

Quando o pedido tem várias cenas ou peças (um comercial, uma leva de criativos, uma sequência de fotos), não gere uma por uma. O roteiro, os prompts, as durações e as transições são da pessoa; o trabalho da skill é organizar, mostrar o custo, gerar e juntar. Siga estas etapas, parando para a aprovação dela onde está marcado. O motivo: imagem não gasta crédito e vídeo gasta, então tudo o que puder ser decidido na imagem é decidido antes de qualquer vídeo.

0. **Duração e divisão (antes do storyboard):** quando a pessoa pede um vídeo de X segundos e ainda não disse como dividir, rode `python flow.py opcoes X` (com `--1080p` se ela baixa em 1080p) e mostre as opções: quantos clipes de quantos segundos, a duração final (a mais próxima, quando não fecha exato) e os créditos de cada uma. Ela escolhe; só depois monte o storyboard. Não há limite de duração total; o recomendado é **até 1 minuto** (avise quando passar disso, sem impedir).
1. **Imagens de referência (pergunte se ela não mandou):** "Tem uma ou mais imagens de referência (cenário, personagem como pessoa, avatar, mascote ou animação 3D, produto, logo)? Pode enviar." Não suponha que existe personagem: muitos vídeos não têm. Personagem, avatar e pessoa são a mesma coisa aqui. Se ela mandou imagens e quer **o mesmo personagem e o mesmo cenário, sem alteração**, ponha `"sem_alteracao": true` no `projeto.json` (ou só na cena): o robô acrescenta no fim de cada prompt "Use only the attached images as reference: keep the character and the setting exactly as they appear in them…", e o storyboard mostra o prompt já com essa frase. Só se o roteiro tiver um personagem (pessoa, avatar, animal, mascote, desenho) que aparece em mais de uma cena e ela não mandou imagem dele, ofereça: "Quer que eu crie primeiro uma imagem do personagem, para ele ficar igual em todas as cenas?" Com imagem pronta (foto, desenho, logo do mascote), ele entra em `personagens` com `"foto"`. Sem imagem, entra com `"prompt_imagem"` (o da pessoa, ou escrito pelo Claude se ela pedir) e o robô gera uma **imagem de referência** antes das cenas, no estilo do vídeo (foto real, animação 3D, desenho...). O motivo: sem referência definida, a primeira cena inventa a aparência e cada cena copia a anterior, e ela vai mudando aos poucos; com a referência aprovada, todas copiam da mesma fonte. Nas cenas em que o personagem aparece, ponha a imagem dele (`personagem_<nome>.jpg` ou a imagem enviada) em `referencias` e, no vídeo, em `imagens_extra` quando a imagem da cena não o mostrar bem.
2. **Organizar o que a pessoa mandou:** cenas, prompts, durações, imagens de referência e transições vão para o `projeto.json`, sem mudar o conteúdo. Faltou algo (duração de uma cena, qual imagem usar), pergunte.
3. **Storyboard → aprovação (sempre, mesmo que a pessoa não peça):** escreva `<projeto>/projeto.json` (formato em `referencias/storyboard-modelo.md`) e rode `python flow.py storyboard <projeto>/projeto.json --itens imagens --abrir`. Isso cria e abre `storyboard.html` (barra de tempo no topo com os segundos de cada cena, as transições e a duração final; tabela com créditos; aviso de saldo; cada cena com fala, prompts e transição) e o `itens_imagens.json` do lote. Mostre também o resumo na conversa e espere o ok. A aprovação e os pedidos de mudança são na conversa: para trocar um prompt, uma duração ou uma transição, altere o `projeto.json` e gere o storyboard de novo.
4. **Imagens em lote:** se há imagem de personagem a gerar, primeiro só ela: `python flow.py storyboard <projeto>/projeto.json --itens personagens` e `python flow.py lote <projeto>/itens_personagens.json`; mostre e espere o ok da aparência. Depois as cenas: `python flow.py lote <projeto>/itens_imagens.json` (pula o que já existe). Com personagem que não foi definido antes, a cena em que ele aparece melhor vem primeiro e serve de referência para as outras.
5. **Aprovação das imagens:** rode o `storyboard` de novo (agora com as imagens aparecendo na página), confira mãos, rosto, objetos e texto e pergunte. Refaça só as reprovadas (apague o arquivo e rode o lote de novo: ele pula as que já existem).
6. **Vídeos em lote:** `python flow.py storyboard <projeto>/projeto.json --itens videos` e `python flow.py lote <projeto>/itens_videos.json --confirmo --max <total aprovado>`, só depois de mostrar de novo o custo dos vídeos e receber o ok.
7. **Juntar:** una os clipes na ordem do roteiro com as transições do storyboard (`flow.py juntar`, veja abaixo). Não gasta crédito.
8. **Entrega:** a pasta do projeto com os arquivos numerados, o vídeo final, o `projeto.json` (todos os prompts, para refazer ou ajustar) e o `storyboard.html`.

Narração em off, legenda e motion design não fazem parte desta skill.

**Cada projeto é isolado.** Use só o que a pessoa mandou para este projeto e os arquivos da pasta dele. Não reaproveite prompts, roteiros, falas, personagens nem imagens de outro projeto, de outra conversa ou de outra pessoa, a não ser que ela peça. Tudo fica no computador dela (a pasta do projeto e `~/.config/flow`, com login, preferências e gastos); o robô só fala com o Google Flow.

## Juntar os vídeos (sem crédito)

Une os clipes num vídeo só, no computador da pessoa (não usa o Flow). Todos ficam no mesmo tamanho (9:16 = 720×1280, 16:9 = 1280×720, 1:1) e a 30 quadros por segundo; clipe sem som ganha silêncio.

```bash
python flow.py juntar cena01.mp4 cena02.mp4 cena03.mp4 --saida final.mp4 [--transicao corte] [--musica fundo.mp3] [--volume-musica 0.15] [--formato 9:16]
```
- **Trecho de um clipe:** `cena01.mp4@0-6` usa só do segundo 0 ao 6 (aproveite a parte boa de um clipe em vez de gerar de novo).
- **Transições (clássicas, 0,4 s cada):** `corte` (corte seco, padrão), `suave` (uma cena se dissolve na outra), `esmaecer-preto`, `esmaecer-branco`, `deslizar-esquerda`, `deslizar-direita`, `aproximar` e `afastar`. Uma para todas (`--transicao esmaecer-preto`) ou uma por junção, na ordem: `--transicao corte,deslizar-esquerda,corte,esmaecer-branco` (são N−1 junções para N vídeos). No modo projeto, use as transições do storyboard.
- **Música:** só se a pessoa mandar o arquivo; entra em loop, baixa (15%), por baixo das falas. Lembre que a música precisa ter licença para uso comercial se o vídeo for para cliente ou anúncio.
- Precisa do ffmpeg: se faltar, instale com `pip install imageio-ffmpeg` (não precisa de mais nada).
- Não sobrescreve: se o arquivo final já existe, escolha outro nome.

## Comandos

| Para quê | Comando |
| --- | --- |
| Conferir a instalação | `python flow.py verificar` |
| Conectar a conta | `python flow.py login` |
| Ver o saldo | `python flow.py saldo` |
| Ver ou mudar preferências | `python flow.py preferencias [--formato …] [--download …]` |
| Imagem (sem crédito) | `python flow.py imagem --prompt-arquivo p.txt --saida img.jpg [--ref outra.jpg] [--formato 9:16]` |
| Vídeo a partir de imagem | `python flow.py video --prompt-arquivo p.txt --imagem img.jpg --saida clipe.mp4 --segundos 8 --confirmo` |
| Vídeo só com texto | o mesmo, sem `--imagem` |
| Vídeo + versão 1080p (+5 créditos) | acrescente `--baixar 1080p` |
| 1080p de um vídeo já gerado (+5 créditos) | `python flow.py ampliar <link da página do vídeo no Flow> --saida clipe_1080p.mp4 --confirmo` |
| Várias de uma vez | `python flow.py lote itens.json [--confirmo] [--max N]` |
| Storyboard visual + itens do lote (sem crédito) | `python flow.py storyboard projeto.json [--itens imagens\|videos] [--abrir]` |
| Juntar os clipes num vídeo só (sem crédito) | `python flow.py juntar a.mp4 b.mp4 c.mp4 --saida final.mp4 [--transicao corte,suave]` |
| Opções de duração e custo para um vídeo de X s | `python flow.py opcoes 30 [--1080p]` |
| Quanto já gastou (por tipo e por conta) | `python flow.py gastos [--dias 7]` |
| Fechar a janela do robô no fim do trabalho | `python flow.py fechar` |
| O Flow mudou a tela | `python flow.py mapear` |

- Use `--prompt-arquivo` para prompts longos (evita problema de aspas). `--ref` repete: várias imagens entram juntas (mesma pessoa, mesmo estilo).
- **O Flow devolve JPEG:** dê nomes `.jpg` às imagens.
- **Formatos:** imagem 16:9, 4:3, 1:1, 3:4, 9:16. Vídeo 16:9 e 9:16. Sem `--formato`, vale o das preferências (ou 9:16).
- **Resolução do vídeo:** gerado sempre em **720p**, o tamanho original do Flow e o recomendado. Se a pessoa quiser 1080p, ele é pedido no download (`--baixar 1080p`, +5 créditos por vídeo).
- `lote`: JSON com uma lista de `{"tipo": "imagem"|"video", "prompt": "...", "saida": "...", "referencias": [...], "imagem": "...", "segundos": 8, "formato": "9:16", "baixar": "1080p", "max": N}`. Caminhos relativos à pasta do JSON. Pula o que já existe e para na primeira falha, dizendo o que ficou faltando.

## Modelos e créditos (lidos no Flow em 16/11/2026; o Google muda isso, confira com `saldo` e no menu)

Imagem: Nano Banana 2.1, sem crédito. Vídeo (720p, 1 cópia), escolhido pela duração:

| Clipe | Modelo | Créditos |
| --- | --- | --- |
| 4 s | Omni 1.1 Flash | 7 |
| 6 s | Omni 1.1 Flash | 10 |
| 8 s | Omni 1.1 Flash | 12 |
| 10 s | Omni 1.1 Flash | 15 |
| 11 s | Omni 1.2 Flash | 36 |
| 12 s | Omni 1.2 Flash | 42 |
| 15 s | Omni 1.2 Flash | 60 |

**Download em 1080p (opcional):** depois de gerado, o Flow oferece a versão ampliada em 1080p por **+5 créditos por vídeo** (baixar em 720p, o tamanho original, não tem custo extra além dos créditos da geração; 4K exige upgrade do plano). Some esses 5 créditos na tabela de custo sempre que a preferência for 1080p e passe `--baixar 1080p` no vídeo (ou `"baixar": "1080p"` no item do lote): o robô salva `clipe.mp4` (720p) e `clipe_1080p.mp4`. O robô **não** usa a preferência sozinho, para nenhum crédito sair fora da tabela. O Flow leva alguns minutos ampliando (~1,5 min num vídeo de 15 s). Pedir de novo o 1080p de um vídeo já ampliado não cobrou outra vez (16/11/2026).

Duração fora da tabela: o robô lê o preço que o Flow mostra e só gera se couber no `--max` aprovado pela pessoa. **O Omni 1.1 sai do Flow em 5/12/2026**; depois disso rode com `FLOW_OMNI=1.2` (o 1.2 custa o dobro nas mesmas durações).

## Proteções (não tire)

- Vídeo só gera com `--confirmo`, depois de a pessoa aprovar o custo. Mostre antes o total de créditos.
- Confere o saldo e o "A geração vai usar N créditos" do próprio Flow antes de gerar; se divergir do combinado (ou passar do `--max`), para sem gastar.
- Nunca clica em "Fazer upgrade" nem "Adicionar créditos".
- Nunca digita senha. Se o Flow pedir "Direitos de uso desta imagem" (1ª vez), a pessoa aceita na janela e roda de novo.
- A tela do Flow é aberta sempre em português (`?hl=pt-BR`), qualquer que seja o idioma da conta, porque os botões são achados pelo nome em português. Isso não muda o idioma da fala nos vídeos (isso é o prompt).

## Qualidade: o que faz a diferença

O mesmo prompt gera uma imagem diferente a cada vez; o que se garante é o nível, não a cópia. O nível vem de:
1. **O prompt** (é da pessoa; para foto com cara de celular, a receita `natural`). As notas de `referencias/dicas-flow-omni.md` evitam os erros comuns da ferramenta.
2. **Mesma pessoa em várias imagens:** passe a imagem já aprovada com `--ref` e comece o prompt com "Same woman/man as in the attached photo…".
3. **Conferir antes de virar vídeo:** mãos (dedos, terceira mão), objetos que mudam, texto ou logo na imagem, rosto deformado. Errou: gere de novo (imagem não gasta crédito). Só a imagem aprovada vira vídeo.

## Receitas de prompt de imagem (opcionais)

Só quando a pessoa pede que o Claude escreva o prompt de uma imagem:
- `receitas/natural.md`: foto de celular, pessoas reais, UGC, depoimento, antes e depois.
- `receitas/institucional.md`: cena corporativa limpa, editorial.
- `receitas/produto.md`: foto de produto em fundo limpo.

## Várias contas

O normal é uma conta só. Se a pessoa respondeu sim na pergunta inicial, ou pedir depois, leia `referencias/varias-contas.md` (como conectar, ordem de uso e o risco com os termos do Google).

## Quando falhar

O erro diz onde parou. Nada foi gasto se o erro vier antes de "Conta N, X créditos". **Gerou mas não baixou:** rode o mesmo comando de novo; o robô guarda um marcador (`<saida>.gerado.json`) e só baixa, sem gerar nem gastar outra vez. **Duas mídias novas ao mesmo tempo** (outra pessoa ou outro robô gerando no mesmo projeto): o robô não adivinha; mostre as candidatas à pessoa, veja no Flow qual é a deste pedido, escreva o nome no campo `nome` do marcador e rode de novo. Para evitar, use um projeto do Flow só para o robô (o padrão: ele cria o dele). O robô não sobrescreve arquivo que já existe. Tela mudou: `mapear` e corrija **só os nomes de botões** do dicionário `SELETORES` em `scripts/flow.py`; nunca mexa em `PROIBIDOS`, nas conferências de custo nem no `--confirmo`, e mostre a mudança à pessoa antes de usar. Urgente: `referencias/flow-navegador.md` (fazer pelo Chrome com o Claude, mais caro). Vídeo só com texto é um recurso novo: se o robô parar nesses casos, avise a pessoa e ofereça o caminho testado (vídeo a partir de imagem, 720p).

**O Flow recusou** ("talvez viole nossas políticas… não houve cobrança"): o robô para em segundos e mostra o aviso; nada foi gasto. O prompt é da pessoa: mostre o aviso e proponha um caminho antes de mudar. O que costuma travar: foto real com muitas pessoas usada junto com o personagem, e o mesmo personagem em certos ambientes. O que costuma passar: usar a foto real do lugar sozinha como imagem inicial da cena (sem a personagem) e deixar a personagem entrar no vídeo como segunda imagem. Não fique tentando variações às cegas: depois de 2 recusas, pare e pergunte.
