# Receita: natural (foto e vídeo de celular, pessoas reais, UGC)

Use para: anúncio com cara de vídeo de celular, depoimento, diálogo, antes e depois, "foto que parece de iPhone", pessoas comuns em lugares comuns.
Não use para: peça de marca produzida de propósito, foto de produto em estúdio, fundo de motion.

O segredo: o prompt descreve **um flagrante tirado por alguém**, não uma foto produzida. Nada de palavras de estúdio.

## Imagem (prompt em inglês)

Nesta ordem. Troque "vertical 9:16" pelo formato pedido ("horizontal 16:9", "square 1:1") e passe o mesmo `--formato` no comando.
1. **Abertura (quem tirou e o momento):** "Unedited vertical 9:16 iPhone photo taken by <who> from a few meters away, a quick candid snapshot <moment>, not a professional photoshoot. Nobody is looking at the camera."
2. **Pessoa principal:** idade, origem, físico, roupa (comum, limpa, em bom estado, nunca gasta), ação **no meio do movimento**, emoção ou esforço visível.
3. **Segunda pessoa** (se houver): onde está em relação à primeira, físico, roupa, atitude.
4. **Setting:** lugar comum e real, luz misturada (dia + lâmpada), dois ou três detalhes do lugar.
5. **Figurantes ao fundo**, pequenos no quadro (se fizer sentido).
6. **Bloco de naturalidade** (sempre, no fim, igual):
   "Real skin texture with visible pores, natural body hair. Framing slightly off-center, slight tilt, shot at chest height. Ordinary iPhone quality: sharp, everything in focus, mild noise, true-to-life colors, no background blur, no filter. No readable text, logos or brand names anywhere."
   Se alguém estiver suando, antes do bloco: "sweat shine only on <who>".

**Variações da abertura**
- Cena flagrante ou diálogo: mantenha "Nobody is looking at the camera".
- Depoimento filmado por outra pessoa: a pessoa fala para quem filma. Tire "Nobody is looking at the camera" e diga "like a casual video being recorded" (ex.: "taken by her daughter").
- Selfie de verdade (ela mesma segura o celular): abra com "Unedited vertical 9:16 front-camera iPhone selfie, held at arm's length by the woman herself, …" e diga "one arm extended toward the camera, the phone itself not visible".
- Mesma pessoa em outra imagem: passe a imagem anterior com `--ref` e comece com "Same woman (and same …) as in the attached photo: keep their exact faces, hair, bodies, skin tone, ages and clothes. Same place, same light." Descreva só o que muda e termine com o bloco de naturalidade.

**Exemplo (cena flagrante):**
```
Unedited vertical 9:16 iPhone photo taken by a coworker from a few meters away, a quick candid snapshot during a busy Saturday morning at a small neighborhood bakery, not a professional photoshoot. Nobody is looking at the camera.

In the foreground, a 42-year-old ordinary woman, medium build, dark curly hair tied back, light flour marks on her forearms, wearing a clean plain olive green t-shirt and a beige cotton apron. She is behind the counter mid-motion, sliding a tray of bread rolls onto the shelf with both hands, slightly hurried, focused expression.

On the other side of the counter, a 70-year-old man with short white hair and glasses, slim, wearing a navy cardigan over a checked shirt, leaning on the counter and pointing at the rolls with a friendly half smile.

Setting: a simple bakery with white tiled walls, a glass display case, paper bags on a wooden shelf, daylight from the street door mixed with warm ceiling lights. Further back, two customers waiting in line, slightly small in the frame.

Real skin texture with visible pores, natural body hair. Framing slightly off-center, slight tilt, shot at chest height. Ordinary iPhone quality: sharp, everything in focus, mild noise, true-to-life colors, no background blur, no filter. No readable text, logos or brand names anywhere.
```

**Exemplo (depoimento):**
```
Unedited vertical 9:16 iPhone photo taken by her son from a couple of meters away, an ordinary weekday evening at home, like a casual video selfie being recorded, not a professional photoshoot. A 58-year-old ordinary woman, slightly overweight, short grey hair, wearing a clean light blue blouse and dark trousers, sitting on the arm of a fabric sofa, looking at the camera and talking naturally, one hand open in a small gesture, relaxed half smile. Setting: a simple middle-class living room, a TV rack, a potted plant, a window with the last daylight mixed with a warm ceiling lamp. No people in the background. Real skin texture with visible pores, natural body hair. Framing slightly off-center, slight tilt, shot at chest height. Ordinary iPhone quality: sharp, everything in focus, mild noise, true-to-life colors, no background blur, no filter. No readable text, logos or brand names anywhere.
```

**Nunca escreva:** "professional photo", "cinematic", "bokeh", "studio lighting", "8k", "masterpiece", "ultra realistic" (deixam com cara de IA). Nada de texto, logo ou marca na imagem. Roupa gasta ou suja só se a cena pedir.

## Vídeo a partir da imagem (Omni, modo Elementos)

A imagem aprovada entra com `--imagem` e é a única referência. Prompt em português mesmo (o Omni entende), nesta ordem:
1. **Abertura:** "Crie um vídeo em estilo natural UGC de <N> segundos. Use a imagem anexada como única referência dos personagens, das roupas e do cenário, mantenha os traços, as características físicas e as roupas, e desconsidere textos."
2. **Personagens:** uma descrição curta de cada um (idade, físico, roupa, onde está).
3. **Cena em ordem:** o que a pessoa faz → a fala dela; a outra pessoa reage → a fala dela. **Nunca** liste todas as ações primeiro e todas as falas depois (a boca e as reações saem trocadas).
4. **Idioma da fala:** "<Pessoa> fala em <idioma das preferências>, com naturalidade: "<fala>"". Limite: cerca de 4,6 palavras por segundo (8 s ≈ 32 palavras, 10 s ≈ 46, 15 s ≈ 69).
5. **Câmera e textura depois das falas**, nunca antes: "Câmera de mão parada, plano médio… Texturas naturais, leves poros, filmagem de iPhone." (Câmera descrita antes da cena faz o Omni cortar para outro ângulo.)
6. **Fecho, conforme as preferências:**
   - legendas `sem`: "Sem legendas, sem textos na tela."
   - música `sem`: "Sem música." · `com`: "Com uma música de fundo suave, baixa, que não cobre a fala."
   - formato: "Formato 9:16." (ou 16:9)

**Marca do cliente no vídeo (importante):** o Omni completa objetos genéricos com a marca mais famosa daquele tipo. "Freezer vermelho e amarelo" virou freezer de sorvete de outra marca, mesmo com a imagem certa anexada. Descreva o objeto **pela marca e pela imagem**: "os freezers da <Marca> exatamente como na imagem anexada, com o logo <Marca> nas laterais", e feche com "sem logotipos de outras marcas, sem freezers ou embalagens de outras marcas". Produto sem embalagem conhecida: "pacote liso, sem marca".

**Antes de juntar, confira cada vídeo quadro a quadro** (1 quadro por segundo): marca trocada, ambiente inventado, objeto que some. Se só uma parte do clipe ficou boa, aproveite o trecho no `juntar` (`clipe.mp4@0-6`) em vez de gerar de novo.

**Truques que evitam erro:**
- Objetos com nome completo: "latinha de refrigerante prateada, sem marca" (só "latinha" vira marca famosa).
- Emoção explícita onde importa: "constrangida, sem sorrir".
- Com 2+ pessoas: quem escuta "fica calado, de boca fechada, só ouvindo" enquanto o outro fala.
- O que está na mesa ou na mão: "fica na mesa o vídeo todo". Objeto que passa de mão em mão some: deixe cada objeto com uma pessoa só.
- Alguém ao fundo que acena ou sorri: "olhando para <pessoa>, de perfil para a câmera" (senão acena para a lente).
- Mão mexendo na roupa por cima da barriga pode trocar o corpo da pessoa: evite e reforce "mesmo rosto e mesmo corpo do começo ao fim".

## Clipe de 10 s dirigido (o padrão)

Em vez de vários clipes curtos e parados, faça um clipe de 10 s com mais de um momento. Escreva as ações **em ordem**, cada uma com o movimento de câmera junto:
"Ela se abana por causa do calor e diz: "…". Ela aponta para a placa; a câmera sobe acompanhando o dedo até a placa e volta. Ela entra pela porta; a câmera de mão vai atrás dela, revelando a loja da segunda imagem anexada; ela olha em volta, encantada."
- Movimentos que o Omni entende: câmera acompanha a pessoa, aproxima até o close, se afasta revelando o lugar, sobe/desce, gira em volta, passa de um ângulo para outro.
- Se o clipe passa por dois ambientes, anexe as duas imagens (personagem/ambiente 1 + ambiente 2) e diga no prompt qual é qual ("a primeira imagem é a fachada, a segunda é o interior").
- Fala: até cerca de 46 palavras em 10 s, dividida entre os momentos.
- A descrição de textura e o fecho (legenda, música, formato) continuam no fim.

## Vídeo só com texto (sem `--imagem`)

Mesma estrutura, trocando a abertura por "Crie um vídeo em estilo natural UGC de <N> segundos, filmado com celular." e descrevendo personagens e cenário com o detalhe do prompt de imagem. Sem imagem, a pessoa muda de um clipe para outro: para manter o mesmo personagem em vários clipes, gere a imagem primeiro.

## Conferir antes de aprovar

Mãos (dedos a mais, terceira mão), objeto que some ou muda, texto ou logo na imagem, roupa que troca entre clipes, rosto diferente da referência. Imagem com erro: gere de novo (não gasta crédito). Só imagem aprovada vira vídeo.
