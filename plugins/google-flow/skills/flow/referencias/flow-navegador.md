# Plano B: operar o Flow pelo Chrome com o Claude

**Primeiro caminho é sempre `scripts/flow.py`** (gasta bem menos tokens). Use este guia só quando o script falhar e for urgente, ou para recursos que o script não tem (modo Frames).

## Como o script funciona (para entender o erro)
- Abre um Chrome comum com perfil próprio (`flow-perfil` dentro de `~/.config/flow` ou `FLOW_HOME`, porta 9333). O Google bloqueia login em navegador aberto pela automação, por isso a pessoa entra uma vez pelo `flow.py login` e o script só se conecta depois.
- O endereço do projeto usado fica em `~/.config/flow/flow-projeto.txt`. Apague esse arquivo para o script criar um projeto novo.
- Abre a tela sempre com `?hl=pt-BR` (botões em português).
- Antes de gerar, confere o "A geração vai usar N créditos" do Flow e marca sempre 1 cópia (x1).
- Baixa a mídia nova pelo link direto (`flow-content.google/...` ou `flow.google.com/asb/...`) e recusa arquivo pequeno (miniatura).

## Pelo Chrome, passo a passo
- Endereço: **https://flow.google.com** → "Novo projeto".
- **Saldo:** avatar no canto superior direito → "N créditos do Google Flow". Nunca clique em "Fazer upgrade" nem "Adicionar créditos".
- **Configuração:** botão ao lado da seta de enviar (mostra, por exemplo, "Vídeo · 720p · 10s · x1"). Ali: Imagem ou Vídeo; para vídeo, **Elementos** (a imagem como referência) ou **Frames** (quadro inicial e final); formato; modelo; **720p**; duração; **x1**. O menu mostra "A geração vai usar N créditos": confira com a pessoa antes de enviar.
- **Enviar imagem de referência:** "+" ao lado da caixa → "Fazer upload de mídia" → escolha o arquivo → clique nele na lista → "Incluir no comando".
- **Escrever o pedido:** a caixa do comando (não a busca do topo). "Apagar comando" limpa.
- **Gerar:** clique na seta ("Iniciar geração"). Enter às vezes só quebra a linha.
- **Baixar:** abra a mídia → "Baixar mídia" → **"Tamanho original"**. Vai para a pasta Downloads; confira pelo horário que é o arquivo certo.
- "Falha ao carregar": tente de novo (↻) uma vez.
- Aviso de "créditos insuficientes" logo após enviar pode ser clique repetido: confira se a geração começou antes de concluir.

## Se nada funcionar
Mostre à pessoa o prompt e a imagem de referência, peça para ela gerar à mão no Flow e salvar o arquivo no destino combinado, e siga com o resto do trabalho.
