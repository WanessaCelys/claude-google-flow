# Receita: natural (foto de celular, pessoas reais, UGC)

Para **imagem**. Use quando a pessoa pedir ao Claude para escrever o prompt de uma foto que pareça de celular: depoimento, flagrante do dia a dia, antes e depois, pessoas comuns em lugares comuns. Prompt pronto da pessoa é usado como está.
Não use para: peça de marca produzida de propósito, foto de produto em estúdio.

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

## Logo ou nome da marca na imagem

Quando a marca aparece num objeto (placa, fachada, embalagem, camiseta, crachá):
1. Anexe **o arquivo do logo** como imagem de referência (`--ref logo.png`), além da foto do lugar.
2. Diga **qual logo está em qual objeto**: "the shop sign shows the logo from the attached logo image".
3. Escreva **o texto exato** que aparece ("written <Nome da Marca>"). Sem isso, a IA inventa letras.
4. Proíba as outras marcas: "no other brand logos". Objeto genérico vira a marca mais famosa daquele tipo de objeto.

## Conferir antes de aprovar

Mãos (dedos a mais, terceira mão), objeto que some ou muda, texto ou logo errado, rosto diferente da referência. Imagem com erro: gere de novo (não gasta crédito). Só imagem aprovada vira vídeo.
