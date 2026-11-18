# Histórico de versões

## 1.0.0 (18/11/2026)

Primeira versão pública.

**A ferramenta:** gera imagens (Nano Banana) e vídeos (Omni) no Google Flow pelo Chrome da própria pessoa, gastando poucos tokens. Quem decide os prompts, a duração, o estilo e o formato é a pessoa; os prompts são usados exatamente como ela mandar.

- **Primeiro uso:** conecta a conta (a pessoa faz o login; o Claude nunca digita senha), avisa o risco de bloqueio com os termos do Google e faz 3 perguntas: formato, resolução de download (720p recomendado; 1080p custa +5 créditos por vídeo) e se usa uma ou várias contas. Termina com uma mensagem fixa com exemplos de pedido.
- **Custos sob controle:** mostra a tabela de créditos antes de qualquer geração, mesmo quando é zero, e só gera vídeo depois do ok (`--confirmo`, com teto). Confere o preço no menu do Flow antes de clicar. Registra cada gasto (`gastos`) e mostra o saldo (`saldo`).
- **Duração:** `opcoes X` mostra os jeitos de dividir um vídeo de X segundos em clipes, com o custo de cada um. Não há limite de duração; o recomendado é até 1 minuto.
- **Modo projeto e storyboard:** a pessoa aprova tudo numa página antes de gastar. Barra de tempo com as cenas em tons de laranja, transições e duração final; tabela de créditos; aviso de saldo; bloco com todas as imagens de referência enviadas (personagens, cenário, produto, logo); cada cena com imagem, fala, prompts e transição. Tarja no topo com a assinatura da autora.
- **Personagens (opcional):** pessoa, avatar, animal, mascote ou desenho que aparece em várias cenas. Com imagem enviada, usa como está; sem imagem, gera primeiro a imagem do personagem (0 crédito) para aprovar a aparência, e todas as cenas usam essa mesma referência.
- **Sem alteração:** quando a pessoa quer o mesmo personagem e o mesmo cenário das imagens enviadas, o robô acrescenta ao prompt "use only the attached images as reference…".
- **Juntar os vídeos (sem crédito):** transições clássicas (corte, suave, esmaecer preto ou branco, deslizar para a esquerda ou a direita, aproximar, afastar), trechos de um clipe (`clipe.mp4@0-6`) e música opcional. O vídeo final sai em H.264 yuv420p, que abre em celular, WhatsApp e Instagram.
- **Receitas de prompt de imagem** (só quando a pessoa pede ao Claude para escrever): foto natural de celular, institucional e produto.
- **Proteções:** não gera duas vezes nem cobra de novo se o download falhar (marcador); não sobrescreve arquivo; não adivinha quando aparecem duas mídias novas ao mesmo tempo; não baixa a imagem de referência no lugar da nova; desliga o modo Agente do Flow; recusa porta de outro Chrome.
- **Quando o Flow recusa:** o robô percebe em segundos e mostra o aviso (nada é cobrado). Se o aviso for de "atividade incomum", manda parar e não tentar contornar.
- **Isolamento:** cada projeto usa só o que a pessoa mandou para ele. Tudo fica no computador dela; o robô só fala com o Google Flow.
- **Várias contas** (opcional, com aviso de risco).
