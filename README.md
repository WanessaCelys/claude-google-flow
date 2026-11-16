# Google Flow para o Claude Code

Skill (plugin) para o **Claude Code** gerar imagens (**Nano Banana**) e vídeos (**Omni**) no **Google Flow** usando o seu próprio Chrome. Você pede em português, o Claude escreve o prompt, gera e baixa o arquivo, e **sempre mostra o custo em créditos antes de gerar**.

> Projeto independente. Não é do Google nem afiliado ao Google. Google Flow, Nano Banana, Omni e Veo são marcas do Google.

## O que ela faz

- **Imagens e vídeos no Flow** com um comando por geração, sem o Claude ficar clicando na tela passo a passo (gasta bem menos tokens).
- **Perguntas no primeiro uso:** estilo, idioma da fala, música, legendas, formato, download em 1080p e uso de mais de uma conta. As respostas guiam todos os pedidos seguintes.
- **Receitas de prompt:** natural (foto e vídeo de celular, UGC, depoimento), institucional, produto e fundos para motion. Se você já tem seus prompts, ela usa o seu texto exatamente como está.
- **Modo projeto:** para pedidos com várias cenas, monta roteiro e storyboard com o custo, gera as imagens em lote (de graça), espera a sua aprovação e só então gera os vídeos.
- **Download em 1080p** (opcional, cobrado à parte pelo Flow) e **vídeo de teste em 360p** (mais barato).

## Requisitos

- [Claude Code](https://claude.com/claude-code) instalado no computador (não funciona no claude.ai pelo navegador: a skill precisa abrir o Chrome local).
- **Python 3.10+** e **Google Chrome**.
- Uma conta Google com acesso ao Google Flow. Imagens não gastam crédito; vídeos precisam de um plano com créditos.

## Instalar

**Jeito mais fácil:** abra o Claude Code e peça:

```
Instala o plugin do GitHub WanessaCelys/claude-google-flow
```

**Ou pelo comando do Claude Code** (um passo, Claude Code 2.1.275 ou mais novo):

```
/plugin install google-flow --marketplace WanessaCelys/claude-google-flow
```

Em versões mais antigas, em dois passos:

```
/plugin marketplace add WanessaCelys/claude-google-flow
/plugin install google-flow@claude-google-flow
```

Depois de instalar, feche e abra o Claude Code de novo.

**Ou manualmente:** baixe este repositório (botão *Code → Download ZIP*) e copie a pasta `plugins/google-flow/skills/flow` para `~/.claude/skills/flow` (no Windows: `C:\Users\<você>\.claude\skills\flow`).

## Primeiro uso

Peça qualquer coisa como *"gera uma imagem no Flow de uma mulher numa cafeteria, estilo foto de celular"*. Na primeira vez o Claude:

1. instala o Playwright (`pip install playwright`);
2. abre uma janela do Chrome para **você** entrar na sua conta Google (o Claude nunca vê nem digita a sua senha);
3. faz as perguntas de preferência e guarda as respostas.

Exemplos de pedidos:

- *"Gera 3 imagens naturais de uma barbearia de bairro, 9:16."*
- *"Usa este prompt exatamente como está e gera em 16:9: …"*
- *"Faz um anúncio de 3 cenas para a minha padaria, com uma cliente falando em português."*
- *"Baixa em 1080p o vídeo que acabamos de gerar."*

## Custos (créditos do Google Flow, conferidos em 16/11/2026)

| O quê | Créditos |
|---|---|
| Imagem (Nano Banana) | 0 |
| Vídeo 4 s / 6 s / 8 s / 10 s (Omni 1.1, 720p) | 7 / 10 / 12 / 15 |
| Vídeo 11 a 15 s (Omni 1.2, 720p) | 36 a 60 |
| Vídeo em 360p | cerca de metade |
| Download em 1080p | +5 por vídeo |

O Google muda esses valores. A skill confere o preço que o próprio Flow mostra antes de cada geração e para, sem gastar, se for diferente do combinado. **O Omni 1.1 sai do Flow em 5/12/2026**; depois disso os vídeos usam o Omni 1.2, que custa o dobro.

## Segurança e privacidade

- **Tudo roda no seu computador.** O login fica salvo só na sua máquina (`~/.config/flow`). A skill não envia nada para servidores além do próprio Google Flow.
- **O Claude nunca digita senha.** Você entra na sua conta na janela do Chrome que a skill abre.
- **Nenhum crédito é gasto sem o seu ok.** Vídeos só são gerados depois que você aprova o custo, e a skill nunca clica em "Fazer upgrade" ou "Adicionar créditos".
- **Termos do Google:** os termos costumam proibir automação e o uso de várias contas para somar créditos, com risco de bloqueio da conta. O recomendado é usar uma conta só. Você é responsável pelo uso da sua conta.
- O código é aberto: o robô está em [`plugins/google-flow/skills/flow/scripts/flow.py`](plugins/google-flow/skills/flow/scripts/flow.py) e pode ser lido antes de instalar.

## Atualizar e desinstalar

```
/plugin update google-flow@claude-google-flow
/plugin uninstall google-flow@claude-google-flow
```

Para apagar também o login e as preferências salvas, apague a pasta `~/.config/flow`.

## Problemas comuns

- **"O Flow mudou a tela" / um botão não é encontrado:** peça ao Claude *"o Flow mudou, roda o mapear e corrige"*.
- **Pede para aceitar "Direitos de uso desta imagem":** acontece só na primeira vez. Aceite na janela do Chrome e peça de novo.
- **Não achou o Chrome:** instale o Google Chrome ou defina a variável `FLOW_CHROME` com o caminho dele.

## Licença

[MIT](LICENSE). Use, modifique e compartilhe à vontade.
