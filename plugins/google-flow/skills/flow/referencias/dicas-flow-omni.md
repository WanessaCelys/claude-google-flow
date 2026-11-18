# Como o Flow e o Omni funcionam (técnico, sem estilo)

O prompt é da pessoa. Estas notas são só sobre o funcionamento da ferramenta, para nada dar errado na hora de gerar. Leia quando for preparar uma geração ou quando a pessoa perguntar por que algo saiu diferente.

## Imagem (Nano Banana, sem crédito)
- O Flow devolve **JPEG**: dê nomes `.jpg` às saídas.
- **Mesma pessoa, produto ou lugar em outra imagem:** passe a imagem aprovada com `--ref` (pode repetir `--ref` para várias). Prompts que começam com "Same woman/man as in the attached photo: keep the exact face, hair, clothes…" mantêm melhor.
- Texto pedido dentro da imagem costuma sair com letras erradas. Se a pessoa pedir texto, avise do risco.
- O mesmo prompt gera um resultado diferente a cada vez. Imagem não gasta crédito: refazer é de graça.

## Vídeo (Omni)
- **Imagens de referência:** a imagem anexada (`--imagem`, pode repetir) define personagem, roupa e lugar. Com várias imagens (personagem, lugar, produto, logo), o prompt deve dizer qual é qual, pelo nome do arquivo.
- **Fala:** cerca de 4,6 palavras por segundo (8 s ≈ 32 palavras, 10 s ≈ 46). Fala longa demais sai cortada ou acelerada; avise se o prompt passar disso.
- **Sem legenda nem texto na tela:** se a pessoa não quer texto, o prompt precisa dizer ("No captions, no subtitles, no text overlays"). Sem isso, às vezes aparece texto.
- **Marca e logo:** o Omni completa objetos genéricos com a marca mais famosa daquele tipo (um freezer genérico pode virar o freezer de uma marca de sorvete famosa). Quando a marca da pessoa aparece num objeto, o que funciona é anexar o logo como imagem, escrever o texto exato da marca e pedir "no other brand logos". Se o prompt dela não tiver isso e a marca importar, avise antes de gastar.
- **Duração:** quem escolhe é a pessoa. Créditos no Omni 1.1: 4 s = 7, 6 s = 10, 8 s = 12, 10 s = 15 (10 s é o mais barato por segundo). Duração fora da tabela: o robô lê o preço no Flow e exige `--max`.

## Antes de juntar
- Confira cada vídeo com 1 quadro por segundo (`ffmpeg -i clipe.mp4 -vf "fps=1,scale=150:-1,tile=10x1" -frames:v 1 folha.jpg`): marca trocada, lugar inventado, objeto que some, mãos.
- Se só uma parte do clipe ficou boa, use o trecho no `juntar` (`clipe.mp4@0-6`) em vez de gerar de novo.
