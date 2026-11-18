# projeto.json e storyboard (modo projeto)

O storyboard é sempre gerado no modo projeto, mesmo que a pessoa não peça: é onde ela vê o projeto inteiro e o custo antes de qualquer gasto. Ele sai do `projeto.json` pelo comando `flow.py storyboard`, igual para todo mundo, e gasta poucos tokens (o Claude escreve o JSON uma vez; a página é montada pelo robô).

## Formato do projeto.json

```json
{
  "titulo": "Loja X · comercial 30 s",
  "formato": "9:16",
  "estilo": "natural (UGC)", "idioma": "pt-BR", "musica": "sem música", "legendas": "sem legendas", "download": "720p",
  "saldo": 36,
  "cenas": [
    {
      "descricao": "Gancho: o que acontece, em uma frase",
      "segundos": 4,
      "fala": "Frase dita na cena (ou vazio)",
      "transicao": "corte",
      "referencias": ["ref/fachada.png"],
      "prompt_imagem": "prompt da imagem (o da pessoa)",
      "prompt_video": "prompt do vídeo (o da pessoa)",
      "imagens_extra": ["ref_loja.jpg"],
      "baixar": "1080p"
    }
  ]
}
```
- As cenas viram `cena01.jpg`/`cena01.mp4`, `cena02…` na ordem. Referências são caminhos dentro da pasta do projeto (fotos reais em `ref/`, imagens de cenas anteriores pelo nome).
- `transicao` é a passagem **para a próxima** cena: `corte`, `suave`, `esmaecer-preto`, `esmaecer-branco`, `deslizar-esquerda`, `deslizar-direita`, `aproximar` ou `afastar`. A última cena não precisa.
- `saldo`: o resultado de `flow.py saldo` (com várias contas, a soma das contas que vão pagar).
- `segundos`: a duração que a pessoa escolheu (para informação: 10 s é o mais barato por segundo). `imagens_extra`: imagens a mais para o vídeo (ex.: o segundo ambiente que o clipe atravessa).
- `baixar: "1080p"` só se a pessoa pediu (+5 créditos); `max` só para duração fora da tabela.
- Cena só de imagem: deixe `prompt_video` vazio. Vídeo só com texto: deixe `prompt_imagem` vazio.

## Comandos
- `flow.py storyboard projeto.json --itens imagens --abrir` → `storyboard.html` + `itens_imagens.json` (etapa das imagens).
- Depois das imagens, o mesmo comando mostra as imagens na página para a aprovação.
- `flow.py storyboard projeto.json --itens videos` → `itens_videos.json` (só das imagens aprovadas).

## Na conversa
Além de abrir a página, mostre um resumo curto: a tabela (cena, duração, transição, créditos), o total, o saldo e a pergunta da etapa ("Posso gerar as N imagens (0 créditos)?"). Os prompts completos ficam na página.

## Quando o saldo não cobre tudo
Diga quanto falta e dê as saídas, sem escolher pela pessoa:
- gerar agora todas as imagens (de graça) e só os vídeos que o saldo paga, deixando o resto para quando os créditos renovarem;
- encurtar cenas (4 s = 7 e 6 s = 10 créditos no Omni 1.1);
- se a pessoa usa mais de uma conta, mostrar de qual conta sai cada vídeo.
Nunca sugira comprar créditos nem clique em "Adicionar créditos".
