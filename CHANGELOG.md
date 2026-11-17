# Histórico de versões

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
