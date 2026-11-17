# Várias contas do Flow (quando a pessoa escolher usar)

**Antes de tudo, avise:** os termos do Google costumam proibir automação e o uso de várias contas para somar créditos. Há risco de bloqueio, inclusive da conta paga. Cada pessoa responde pela própria conta; a decisão é dela. Repita este aviso antes de conectar cada conta nova.

## Como conectar
- Conta 1 é a do `flow.py login`. As outras: `python flow.py login 2` e `python flow.py login 3` (cada uma abre um Chrome separado; a pessoa entra na conta Google correspondente e deixa a janela aberta).
- Cada conta tem perfil, porta (9333, 9334, 9335) e projeto próprios dentro de `~/.config/flow` (ou `FLOW_HOME`).
- `python flow.py saldo` mostra o saldo de cada conta conectada.

## Como o robô escolhe a conta
- **Imagem:** a primeira conta liberada (não gasta crédito); com `FLOW_CONTAS=3`, usa a conta 3.
- **Vídeo:** lê o saldo das contas na ordem e usa a primeira que paga o clipe inteiro. Se nenhuma paga, para sem gastar.
- Ordem padrão: 1, 2, 3. Para usar primeiro as contas grátis, crie `~/.config/flow/config.json` com `{"ordem": [2, 3, 1]}`.
- Para limitar às contas liberadas no dia: variável `FLOW_CONTAS=1,3`.

## Na tabela de custo
Mostre também de qual conta sai cada vídeo e quanto sobra em cada uma.
