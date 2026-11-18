# Histórico de versões

## 1.3.3 (18/11/2026)
- Quando o Flow recusa uma geração ("talvez viole nossas políticas"), o robô percebe em segundos e mostra o aviso, em vez de esperar 8 minutos. Orientação na skill do que fazer.
- O vídeo final do `juntar` sai em yuv420p (antes podia sair em yuv444p, que não abre em celular, WhatsApp e Instagram) e com início rápido para a web.
- O modo Agente do Flow fica sempre desligado: o robô confere ao abrir o projeto e antes de cada pedido (com ele ligado, o pedido vira conversa e não gera). Fecha também o painel lateral.
- `storyboard --abrir` agora abre de verdade no Windows.
- **Personagens (opcional):** no início do projeto a skill pergunta se há imagens de referência e se algum personagem (pessoa, animal, mascote, desenho) aparece em mais de uma cena, sem supor que exista. Sem imagem pronta, gera primeiro a imagem do personagem (0 crédito) para aprovar a aparência, e todas as cenas usam essa mesma referência (ele não vai mudando de cena em cena). Aparece no storyboard como "Personagem". Novo `--itens personagens`.
- Mensagem fixa de fim da configuração, com exemplos de pedido.
- Pergunta de referências simples: "Tem uma ou mais imagens de referência (cenário, personagem como pessoa, avatar, mascote ou animação 3D, produto, logo)?".
- Correção: logo depois de gerar, a página da mídia às vezes ainda mostra a imagem de referência; o robô baixava essa no lugar da nova. Agora compara o baixado com as referências e espera a imagem nova.
- Regra de isolamento: cada projeto usa só o que a pessoa mandou para ele.
- Storyboard com a assinatura "criado por Wanessa Celys" fixa no canto de cima, à direita.

## 1.3.2 (18/11/2026)
- Pergunta inicial da resolução mais clara: "Em que resolução você quer baixar os vídeos?", com **720p (recomendado)** primeiro e o custo do 1080p ao lado.

## 1.3.1 (18/11/2026)
- Transições clássicas no `juntar`: suave, esmaecer-preto, esmaecer-branco, deslizar-esquerda, deslizar-direita, aproximar e afastar (este feito sob medida: a cena encolhe até o centro e revela a próxima). Os nomes antigos (deslizar, zoom, círculo) continuam aceitos.

## 1.3.0 (18/11/2026)

**Foco:** a skill é a ferramenta; quem decide os prompts, a duração, o estilo e o formato é a pessoa. Os prompts chegam prontos (escritos por ela ou criados com o Claude na conversa) e são usados como estão.

**Novo**
- `opcoes 30`: jeitos de dividir um vídeo de X segundos em clipes, com a duração final e os créditos de cada opção, para a pessoa escolher antes do storyboard.
- Storyboard com barra de tempo no topo: as cenas lado a lado com os segundos, as transições e a duração final.
- `gastos`: registro local de cada imagem, vídeo e 1080p gerados, com a conta e o saldo que sobrou; depois de gerar, o Claude diz quanto gastou e quanto sobrou.
- Guia técnico `referencias/dicas-flow-omni.md` (referências, limite de fala, sem texto na tela, marca e logo, conferir antes de juntar).

**Mudou**
- Receitas só de imagem e opcionais (natural/foto de celular, institucional, produto), usadas apenas quando a pessoa pede que o Claude escreva um prompt de imagem. Saíram as receitas de vídeo e a de fundo para motion.
- Perguntas iniciais reduzidas ao que a ferramenta usa: formato, download em 1080p e várias contas.

## 1.2.0 (17/11/2026)

**Novo**
- `storyboard`: página visual do projeto (tabela com créditos, aviso de saldo, cada cena com fala, prompts, transição e a imagem quando já existe) e os itens do lote de cada etapa, a partir de um `projeto.json`. No modo projeto é gerado sempre, mesmo sem a pessoa pedir.
- `juntar`: uma transição por junção (`corte,deslizar,suave`), novas transições (deslizar, círculo, zoom) e trecho de um clipe (`cena01.mp4@0-6`).
- Clipes de 10 s por padrão, com várias ações e movimentos de câmera dirigidos dentro do clipe (mais barato por segundo).
- Vídeo com mais de uma imagem de referência (`imagens_extra`), para o clipe que passa por dois ambientes.

**Corrigido**
- Imagem passa a usar a conta escolhida (antes, sempre a conta 1).
- `juntar` com corte seguido de transição falhava (base de tempo); agora funciona, com teste que roda o ffmpeg de verdade. Em falha, não deixa arquivo final quebrado.
- Duas mídias novas ao mesmo tempo no projeto (outra pessoa gerando): o robô para e pergunta qual é a sua, em vez de baixar a errada.
- Receita natural: o Omni troca a marca do cliente pela marca famosa do mesmo tipo de objeto; agora o prompt trava a marca e proíbe logos de outras marcas, e cada vídeo é conferido antes de juntar.

## 1.1.0 (17/11/2026)

**Novo**
- `juntar`: une os clipes num vídeo só, com corte seco ou transição suave e música de fundo opcional. Roda no computador, sem crédito (ffmpeg via `pip install imageio-ffmpeg`).
- `fechar`: fecha a janela do robô no fim do trabalho (o login continua salvo).
- `verificar` mostra se o ffmpeg para juntar vídeos está instalado.

**Corrigido**
- Imagens: desde 17/11/2026 o Flow mostra só uma miniatura WebP na grade. O robô agora abre a imagem e baixa o tamanho original (1K, JPEG).

**Segurança** (auditoria independente)
- Lote recusa tipo desconhecido (`"Video"`, `"image"`…) antes de qualquer gasto: antes, um tipo escrito errado podia gerar vídeo sem confirmação.
- O `--max` passa a incluir os +5 créditos do 1080p.
- Gerou mas não baixou: rodar de novo só baixa, sem gerar e gastar outra vez (marcador `<saida>.gerado.json`).
- O custo é conferido de novo logo antes de clicar em gerar.
- O robô só se conecta ao Chrome do perfil dele: recusa outro Chrome ou programa na mesma porta.
- Caminhos do lote só dentro da pasta do projeto; nenhum comando sobrescreve arquivo existente; `ampliar` só aceita links do Flow.
- Fechar a janela de uma conta não fecha mais as das outras contas.
- Envio de imagens por pasta temporária própria, sempre apagada.
- Os testes nunca abrem o navegador.

## 1.0.1 (17/11/2026)
- Vídeo sempre gerado em 720p (o tamanho original, recomendado); saiu a opção de 360p.
- Texto mais claro: 720p não tem custo extra no download, mas o vídeo sempre gasta os créditos da geração.

## 1.0.0 (16/11/2026)
- Primeira versão pública: perguntas iniciais, receitas de prompt, modo projeto com storyboard e lote, download em 1080p, vídeo só com texto, várias contas (opcional, com aviso de risco) e custo mostrado antes de qualquer geração.
