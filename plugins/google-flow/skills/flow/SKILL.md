---
name: flow
description: >-
  Gera imagens (Nano Banana) e vídeos (Omni) no Google Flow pelo Chrome da própria pessoa, com um comando por geração. Use sempre que for preciso gerar imagem ou vídeo no Flow, Nano Banana, Omni ou Veo do Flow, uma a uma ou em lote: anúncios, fotos naturais de celular (UGC), cenas institucionais, fotos de produto, fundos para motion, personagens. Na primeira vez, conecta a conta e pergunta as preferências (estilo, idioma da fala, música, legendas, formato, download em 1080p). Confere o saldo, mostra o custo e pede confirmação antes de gastar crédito, e baixa o arquivo.
compatibility: Claude Code no computador da pessoa, com Python 3.10+, Playwright e Google Chrome. Não funciona no claude.ai pelo navegador (precisa abrir o Chrome local).
---

# Flow: imagens e vídeos no Google Flow

Robô que controla o Chrome da própria pessoa, já logado na conta Google dela, e faz os cliques do Flow (projeto, formato, modelo, enviar referência, gerar, esperar, baixar). O Claude dá uma ordem curta e recebe o arquivo pronto, em vez de operar a tela passo a passo (muito mais barato em tokens).

O robô é **só o motor**. O estilo do prompt está nas receitas (`receitas/`), escolhidas pelas preferências da pessoa.

## Primeiro uso (uma vez por computador)

Faça nesta ordem, explicando cada passo em linguagem simples. **Todos os comandos `flow.py` rodam de dentro da pasta `scripts/` da skill.**

1. **Instalar:** `pip install playwright` (não precisa baixar navegador: usa o Chrome instalado). Precisa de Python 3.10+ e do Google Chrome.
2. **Conferir:** `python flow.py verificar` diz o que falta (Playwright, Chrome, login).
3. **Conectar a conta do Flow:** `python flow.py login` abre uma janela do Chrome. **A pessoa entra na própria conta Google** nessa janela e deixa ela aberta. O Claude nunca digita senha. O login fica salvo em `~/.config/flow` (ou na pasta de `FLOW_HOME`) e não precisa repetir.
4. **Perguntas iniciais:** rode `python flow.py preferencias`. Se disser "Sem preferências salvas", faça as perguntas abaixo (numa tela de perguntas, se der) e salve as respostas.

### Perguntas iniciais

| Pergunta | Opções | Campo |
|---|---|---|
| Que estilo você vai gerar mais? | **Natural** (foto e vídeo de celular, pessoas reais, UGC) · **Institucional** (cena corporativa limpa) · **Produto** · **Fundos para motion** · Outro (descreva) | `--estilo natural` (ou `institucional`, `produto`, `fundo-motion`, ou o nome que a pessoa der ao próprio estilo) |
| Em que idioma as pessoas falam nos vídeos? | Português do Brasil · Inglês · Espanhol · Depende do vídeo | `--idioma pt-BR` / `en-US` / `es` / `depende` |
| Os vídeos gerados têm música? | Sem música (você põe na edição) · Com música · Depende do vídeo | `--musica sem` / `com` / `depende` |
| Legenda escrita no vídeo? | Sem (recomendado: o gerador escreve errado; legenda se põe na edição) · Com · Depende | `--legendas sem` / `com` / `depende` |
| Formato mais usado? | 9:16 (Reels, TikTok) · 16:9 (YouTube, site) · 1:1 · Depende | `--formato 9:16` / `16:9` / `1:1` / `depende` |
| Baixar os vídeos em 1080p? | Não, 720p (grátis, o tamanho original) · Sim, 1080p (**+5 créditos por vídeo**) · Depende do vídeo | `--download 720p` / `1080p` / `depende` |
| Tem mais de uma conta do Flow e quer que o robô use todas? | Não, só uma (recomendado) · Sim | se sim, siga `referencias/varias-contas.md` |

```bash
python flow.py preferencias --estilo natural --idioma pt-BR --musica depende --legendas sem --formato 9:16 --download 720p
```

**Na pergunta das várias contas, avise o risco junto com a pergunta, antes da resposta:** os termos do Google costumam proibir automação e o uso de várias contas para somar créditos, e há risco de bloqueio, inclusive da conta paga. A decisão é da pessoa. Se ela disser sim, repita o aviso antes de conectar cada conta nova.

Para mudar depois: o mesmo comando só com o campo que muda. **Quando uma preferência for "depende", pergunte a cada pedido.** Se a pessoa escolher "Outro" estilo, crie com ela uma receita nova em `receitas/<nome>.md` seguindo o formato das outras (estrutura do prompt + fecho + o que evitar) e salve `--estilo <nome>`.

## Antes de cada geração

1. Leia as preferências (`flow.py preferencias`).
2. **A pessoa trouxe o prompt pronto?** Use exatamente o texto dela, sem reescrever, traduzir ou "melhorar": quem conhece o resultado que quer é ela. Só ajuste os parâmetros do comando (formato, duração, referências). Se notar algo que costuma dar erro (texto ou logo pedido na imagem, fala longa demais para a duração, câmera descrita antes da cena), avise em uma linha e pergunte se ela quer mudar. Vários prompts prontos: monte um `lote` com eles, um item por prompt. Se ela usa sempre a mesma estrutura, ofereça guardar como receita própria (`receitas/<nome>.md` + `--estilo <nome>`), para os próximos pedidos sem prompt seguirem o jeito dela.
3. **Sem prompt pronto:** escreva seguindo a receita do estilo pedido (ou do estilo salvo), com o idioma, a música e as legendas das preferências (ou do que a pessoa disse para este pedido).
4. **Sempre mostre o custo antes de produzir, em toda geração**, mesmo quando for zero. Uma tabela curta: cada item (imagem ou vídeo), duração, resolução, créditos de cada um, o total e o saldo que sobra (`flow.py saldo`). Imagem aparece como "0 créditos". Só gere depois do ok explícito da pessoa; vídeo só com `--confirmo` depois desse ok.

## Modo projeto (pedido com várias cenas)

Quando o pedido tem várias cenas ou peças (um anúncio com cenas, uma leva de criativos, uma sequência de fotos), não gere uma por uma. Siga estas etapas, parando para a aprovação da pessoa onde está marcado. O motivo: imagem não gasta crédito e vídeo gasta, então tudo o que puder ser decidido na imagem é decidido antes de qualquer vídeo.

1. **Roteiro:** lista de cenas, cada uma com o que acontece, a fala (se houver) e a duração. A soma das durações fecha o total pedido.
2. **Storyboard → aprovação:** siga o modelo de `referencias/storyboard-modelo.md`: tabela resumo (cena, duração, arquivos, créditos e total), o saldo que sobra (e o que fazer se não cobrir tudo) e os prompts em blocos abaixo da tabela. Se a pessoa trouxe prompts prontos, eles entram como estão. Espere o ok.
3. **Imagens em lote:** monte `<projeto>/itens.json` só com as imagens (nomes numerados: `cena01.jpg`, `cena02.jpg`…) e rode `flow.py lote`. A mesma pessoa em várias cenas: gere primeiro a cena em que ela aparece melhor, e use essa imagem como `referencias` nas outras.
4. **Aprovação das imagens:** mostre cada imagem e confira mãos, rosto, objetos e texto. Refaça só as reprovadas (apague o arquivo e rode o lote de novo: ele pula as que já existem).
5. **Vídeos em lote:** acrescente ao `itens.json` os vídeos das imagens aprovadas (`cena01.mp4`…). Mostre de novo a tabela de custo dos vídeos e só rode com `--confirmo` depois do ok.
6. **Entrega:** a pasta do projeto com os arquivos numerados na ordem do roteiro e o `itens.json` (que guarda todos os prompts usados, para refazer ou ajustar depois).

A montagem final (cortes, narração, legenda, música, motion) não faz parte desta skill.

## Comandos

| Para quê | Comando |
| --- | --- |
| Conferir a instalação | `python flow.py verificar` |
| Conectar a conta | `python flow.py login` |
| Ver o saldo | `python flow.py saldo` |
| Ver ou mudar preferências | `python flow.py preferencias [--estilo …] [--idioma …] [--musica …] [--legendas …] [--formato …]` |
| Imagem (sem crédito) | `python flow.py imagem --prompt-arquivo p.txt --saida img.jpg [--ref outra.jpg] [--formato 9:16]` |
| Vídeo a partir de imagem | `python flow.py video --prompt-arquivo p.txt --imagem img.jpg --saida clipe.mp4 --segundos 8 --confirmo` |
| Vídeo só com texto | o mesmo, sem `--imagem` |
| Vídeo de teste mais barato | acrescente `--resolucao 360p --max N` |
| Vídeo + versão 1080p (+5 créditos) | acrescente `--baixar 1080p` |
| 1080p de um vídeo já gerado (+5 créditos) | `python flow.py ampliar <link da página do vídeo no Flow> --saida clipe_1080p.mp4 --confirmo` |
| Várias de uma vez | `python flow.py lote itens.json [--confirmo] [--max N]` |
| O Flow mudou a tela | `python flow.py mapear` |

- Use `--prompt-arquivo` para prompts longos (evita problema de aspas). `--ref` repete: várias imagens entram juntas (mesma pessoa, mesmo estilo).
- **O Flow devolve JPEG:** dê nomes `.jpg` às imagens.
- **Formatos:** imagem 16:9, 4:3, 1:1, 3:4, 9:16. Vídeo 16:9 e 9:16. Sem `--formato`, vale o das preferências (ou 9:16).
- **Resolução do vídeo:** 720p (padrão) ou 360p. O Flow não tem 1080p para o Omni.
- `lote`: JSON com uma lista de `{"tipo": "imagem"|"video", "prompt": "...", "saida": "...", "referencias": [...], "imagem": "...", "segundos": 8, "formato": "9:16", "resolucao": "720p", "baixar": "1080p", "max": N}`. Caminhos relativos à pasta do JSON. Pula o que já existe e para na primeira falha, dizendo o que ficou faltando.

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

**Download em 1080p (opcional):** depois de gerado, o Flow oferece a versão ampliada em 1080p por **+5 créditos por vídeo** (o 720p é o tamanho original e não custa nada; 4K exige upgrade do plano). Some esses 5 créditos na tabela de custo sempre que a preferência for 1080p e passe `--baixar 1080p` no vídeo (ou `"baixar": "1080p"` no item do lote): o robô salva `clipe.mp4` (720p) e `clipe_1080p.mp4`. O robô **não** usa a preferência sozinho, para nenhum crédito sair fora da tabela. O Flow leva alguns minutos ampliando (~1,5 min num vídeo de 15 s). Pedir de novo o 1080p de um vídeo já ampliado não cobrou outra vez (16/11/2026).

360p custa cerca de metade (10 s ≈ 7 créditos no 1.1); como esse preço não está na tabela, o robô lê o valor que o Flow mostra e só gera se couber no `--max`. **Teto seguro para o `--max`: o preço da mesma duração em 720p** (assim o teste nunca custa mais que o vídeo final). **O Omni 1.1 sai do Flow em 5/12/2026**; depois disso rode com `FLOW_OMNI=1.2` (o 1.2 custa o dobro nas mesmas durações).

## Proteções (não tire)

- Vídeo só gera com `--confirmo`, depois de a pessoa aprovar o custo. Mostre antes o total de créditos.
- Confere o saldo e o "A geração vai usar N créditos" do próprio Flow antes de gerar; se divergir do combinado (ou passar do `--max`), para sem gastar.
- Nunca clica em "Fazer upgrade" nem "Adicionar créditos".
- Nunca digita senha. Se o Flow pedir "Direitos de uso desta imagem" (1ª vez), a pessoa aceita na janela e roda de novo.
- A tela do Flow é aberta sempre em português (`?hl=pt-BR`), qualquer que seja o idioma da conta, porque os botões são achados pelo nome em português. Isso não muda o idioma da fala nos vídeos (isso é o prompt).

## Qualidade: o que faz a diferença

O mesmo prompt gera uma imagem diferente a cada vez; o que se garante é o nível, não a cópia. O nível vem de:
1. **O prompt seguir a receita** (sobretudo a `natural`, que é o que dá cara de foto de celular de verdade).
2. **Mesma pessoa em várias imagens:** passe a imagem já aprovada com `--ref` e comece o prompt com "Same woman/man as in the attached photo…".
3. **Conferir antes de virar vídeo:** mãos (dedos, terceira mão), objetos que mudam, texto ou logo na imagem, rosto deformado. Errou: gere de novo (imagem não gasta crédito). Só a imagem aprovada vira vídeo.

## Estilos de prompt (receitas)

- `receitas/natural.md`: foto e vídeo de celular, pessoas reais, UGC, depoimento, diálogo, antes e depois.
- `receitas/institucional.md`: cena corporativa limpa, editorial.
- `receitas/produto.md`: foto de produto em fundo limpo.
- `receitas/fundo-motion.md`: fundos e texturas para motion e vídeo, sem rosto nem texto.
- Receitas novas da pessoa ficam na mesma pasta.

## Várias contas

O normal é uma conta só. Se a pessoa respondeu sim na pergunta inicial, ou pedir depois, leia `referencias/varias-contas.md` (como conectar, ordem de uso e o risco com os termos do Google).

## Quando falhar

O erro diz onde parou. Nada foi gasto se o erro vier antes de "Conta N, X créditos". Tela mudou: `mapear` e corrija só o dicionário `SELETORES` em `scripts/flow.py`. Urgente: `referencias/flow-navegador.md` (fazer pelo Chrome com o Claude, mais caro). Vídeo só com texto e 360p são recursos novos: se o robô parar nesses casos, avise a pessoa e ofereça o caminho testado (vídeo a partir de imagem, 720p).
