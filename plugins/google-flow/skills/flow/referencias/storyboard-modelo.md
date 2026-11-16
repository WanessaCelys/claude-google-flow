# Modelo de storyboard (modo projeto)

Monte sempre nesta ordem: **cabeçalho → tabela resumo → saldo → prompts em blocos → pergunta**. Os prompts ficam fora da tabela porque são longos e deixariam a tabela ilegível; a tabela é para a pessoa ver o projeto e o custo de uma vez.

## Modelo

```
### Storyboard: "<nome do projeto>", <formato> · <duração total>
<estilo> · fala em <idioma> · <com/sem> música · <com/sem> legendas · download em <720p/1080p>

| # | Cena | Dur. | Imagem | Vídeo | Créditos |
|---|---|---|---|---|---|
| 1 | <o que acontece, em uma frase> | 8 s | cena01.jpg | cena01.mp4 · 720p | 0 + 12 |
| 2 | <…> | 8 s | cena02.jpg (ref. cena01) | cena02.mp4 · 720p | 0 + 12 |
|   | **Total** | **16 s** | **2 imagens: 0** | **2 vídeos: 24** | **24** |

**Saldo:** <N> créditos → sobram <N − total>.

**Cena 1: prompt da imagem**
<bloco de código com o prompt completo>
**Cena 1: prompt do vídeo**
<bloco de código com o prompt completo>
(repita para cada cena; prompts prontos da pessoa entram exatamente como ela mandou)

**Posso gerar as <N> imagens (0 créditos)?**
```

## Regras da tabela
- **Créditos por cena:** "imagem + vídeo" (a imagem é sempre 0). Some +5 na cena quando o download for 1080p ("0 + 12 + 5").
- **Imagem com referência:** escreva de qual cena ela herda a pessoa ("ref. cena01").
- **Só imagens** (projeto de fotos): tire a coluna Vídeo e a linha de créditos mostra 0.
- **Primeira pergunta é sempre sobre as imagens**, que não custam nada. O custo dos vídeos é mostrado de novo, só com as imagens aprovadas, antes do `--confirmo`.

## Quando o saldo não cobre tudo
Diga quanto falta e dê as saídas, sem escolher pela pessoa:
- gerar agora todas as imagens (de graça) e só os vídeos que o saldo paga, deixando o resto para quando os créditos renovarem;
- testar os vídeos em 360p (cerca de metade do preço) e gerar em 720p só os aprovados;
- encurtar cenas (4 s = 7 e 6 s = 10 créditos no Omni 1.1);
- se a pessoa usa mais de uma conta, mostrar de qual conta sai cada vídeo.
Nunca sugira comprar créditos nem clique em "Adicionar créditos".
