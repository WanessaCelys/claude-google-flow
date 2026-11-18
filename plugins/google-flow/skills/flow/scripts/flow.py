"""Gera imagens e vídeos no Google Flow (flow.google.com) controlando o Chrome por Playwright, sem o Claude
clicar na tela passo a passo (um comando por geração, bem menos tokens). Serve a qualquer projeto: o pedido
(prompt) e os arquivos vêm de quem chama; este script não conhece roteiro nem estilo.

  python flow.py verificar                          # confere Python, Playwright, Chrome e login
  python flow.py login [2|3]                        # abre o Chrome da conta; a pessoa entra uma vez e deixa aberto
  python flow.py saldo                              # saldo de cada conta com login
  python flow.py mapear [arquivo]                   # lista os botões da tela (para ajustar SELETORES se o Flow mudar)
  python flow.py preferencias [--formato 9:16] [--download 720p]
  python flow.py imagem --prompt-arquivo p.txt --saida img.jpg [--ref a.jpg --ref b.jpg] [--formato 9:16]
  python flow.py video  --prompt-arquivo p.txt [--imagem img.jpg] --saida clipe.mp4 --segundos 8 --confirmo [--max N]
                        [--formato 9:16] [--baixar 1080p]   # sem --imagem: so texto; gera sempre em 720p
  python flow.py juntar cena01.mp4@0-6 cena02.mp4 --saida final.mp4 [--transicao suave] [--musica m.mp3]   # sem crédito
  python flow.py storyboard projeto.json [--itens imagens|videos] [--abrir]   # página para aprovar + itens do lote
  python flow.py opcoes 30 [--1080p]                 # jeitos de dividir um vídeo de 30 s em clipes, com o custo
  python flow.py gastos [--dias 7]                  # quanto já gastou, por tipo e por conta (registro local)
  python flow.py fechar                             # fecha a janela do robô quando terminar (o login continua salvo)
  python flow.py ampliar <link do vídeo no Flow> --saida clipe_1080p.mp4 --confirmo   # 1080p de um vídeo já gerado
  python flow.py lote itens.json [--confirmo] [--max N]   # várias gerações; pula as que já existem

Imagem: Nano Banana (sem gasto de crédito). Vídeo: gasta crédito, então exige --confirmo.
Omni: até 10 s usa o Omni 1.1 Flash (8 s = 12 créditos, 10 s = 15). De 11 a 15 s usa o Omni 1.2 Flash (duração em barra;
15 s = 60). FLOW_OMNI=1.2 força o 1.2 em tudo (o 1.1 sai do Flow em 5/12/2026).
Vídeo é gerado sempre em 720p (o tamanho original do Flow). 1080p é opcional, no download (--baixar 1080p, +5 créditos).
Duração fora da tabela de custos: o script lê o preço que o próprio Flow mostra e só gera se couber no --max.
A pessoa faz o login; o Claude nunca digita senha. Variáveis: FLOW_HOME (pasta de perfis), FLOW_CHROME, FLOW_CONTAS, FLOW_OMNI.
"""
import json
import os
import re
from collections import Counter
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

URL = "https://flow.google.com"


def _pasta_de_perfis():
    """FLOW_HOME, ou ~/.config/flow (login, projeto e preferências)."""
    if os.environ.get("FLOW_HOME"):
        return Path(os.environ["FLOW_HOME"])
    return Path.home() / ".config" / "flow"


CONFIG = _pasta_de_perfis()


def _ordem_das_contas():
    """Ordem em que as contas são usadas: padrão 1, 2, 3. Para usar as contas grátis primeiro, crie
    CONFIG/config.json com {"ordem": [2, 3, 1]}. Uma conta só (o normal) ignora isso."""
    arq = CONFIG / "config.json"
    if arq.exists():
        try:
            return tuple(int(x) for x in json.loads(arq.read_text(encoding="utf-8"))["ordem"])
        except (ValueError, KeyError, TypeError):
            sys.exit(f'{arq} inválido: esperado {{"ordem": [2, 3, 1]}}.')
    return (1, 2, 3)


CONTAS = _ordem_das_contas()
ATUAL = 1


def achar_chrome():
    """Chrome do computador: FLOW_CHROME, caminhos comuns (Windows, macOS) ou o PATH (Linux)."""
    if os.environ.get("FLOW_CHROME"):
        return os.environ["FLOW_CHROME"]
    comuns = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        str(Path(os.environ.get("LOCALAPPDATA", "")) / "Google" / "Chrome" / "Application" / "chrome.exe"),
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    ]
    for c in comuns:
        if Path(c).exists():
            return c
    for nome in ("google-chrome", "google-chrome-stable", "chromium", "chrome"):
        achado = shutil.which(nome)
        if achado:
            return achado
    sys.exit("Não achei o Chrome. Instale o Google Chrome ou defina FLOW_CHROME com o caminho dele.")


def conta(n):
    """Cada conta tem perfil de Chrome, porta e projeto próprios. A conta 1 mantém os nomes antigos."""
    sufixo = "" if n == 1 else f"-{n}"
    return {"perfil": CONFIG / f"flow-perfil{sufixo}", "porta": 9332 + n,
            "projeto": CONFIG / f"flow-projeto{sufixo}.txt"}


def contas_com_login():
    """FLOW_CONTAS=1 (ou "1,3") limita às contas que a pessoa liberou no dia."""
    import os
    liberadas = [int(x) for x in os.environ.get("FLOW_CONTAS", "").split(",") if x.strip()]
    return [n for n in (liberadas or CONTAS) if conta(n)["perfil"].exists()]
# Créditos por clipe (x1, 720p), lidos no menu do Flow em 10 e 16/11/2026. Fora da tabela (outra duração):
# o script não chuta; lê o preço que o Flow mostra e exige um teto (--max) aprovado pela pessoa.
CUSTO_OMNI = {
    "1.1": {4: 7, 6: 10, 8: 12, 10: 15},
    "1.2": {3: 9, 6: 18, 8: 24, 9: 27, 10: 30, 11: 36, 12: 42, 13: 48, 15: 60},
}
MODELOS_OMNI = {"1.1": "Omni 1.1 Flash", "1.2": "Omni 1.2 Flash"}
ESPERA_GERACAO_MS = 8 * 60 * 1000

# Nomes acessíveis dos controles (testados no Chrome em 08/10). Se o Google mudar a tela,
# rode `mapear` e corrija só aqui.
SELETORES = {
    "novo_projeto": "Novo projeto",
    "config": "Gatilho de configurações",
    "gerar": "Iniciar geração",
    "inicio": "Início",
    "adicionar": "Menu para adicionar arquivos",
    "enviar_midia": "Fazer upload de mídia",   # era "Enviar mídia" até nov/2026
    "incluir": "Incluir no comando",
    "apagar": "Apagar comando",
    "elementos_add": "Adicionar elementos à caixa de comando",
    "baixar": "Baixar mídia",
    "original": "Tamanho original",
    "avatar": "Detalhes da conta",
    "menu_arquivos": "Menu para adicionar arquivos",
    "aba_video": "Vídeo",
    "aba_imagem": "Imagem",
    "frames": "Frames",
    "elementos": "Elementos",
    "omni": "Omni 1.1 Flash",
    "nano": "Nano Banana 2.1",
    "formato": "9:16",
    "resolucao": "720p",
    "x1": "x1",
}
PROIBIDOS = ("Fazer upgrade", "Adicionar créditos")  # nunca clicar


# ---------- regras (testadas) ----------

def ler_saldo(texto):
    m = re.search(r"([\d.]+)\s*créditos do Google Flow", texto or "")
    return int(m.group(1).replace(".", "")) if m else None


def modelo_omni(segundos):
    """Até 10 s: Omni 1.1 (mais barato), como sempre. Acima de 10 s só o 1.2 tem. FLOW_OMNI=1.2 força o 1.2 em tudo."""
    import os
    if segundos > 10:
        return "1.2"
    return os.environ.get("FLOW_OMNI", "1.1")


def custo_video(segundos, modelo=None):
    modelo = modelo or modelo_omni(segundos)
    tabela = CUSTO_OMNI[modelo]
    if segundos not in tabela:
        sys.exit(f"Não sei o custo de {segundos} s no Omni {modelo} (conhecidos: {sorted(tabela)}). Nada foi gasto.")
    return tabela[segundos]


def custo_conhecido(segundos, modelo=None):
    """Custo da tabela (720p) ou None quando o script não sabe: aí vale o preço do Flow, limitado pelo --max."""
    return CUSTO_OMNI[modelo or modelo_omni(segundos)].get(segundos)


def ler_custo_menu(texto):
    m = re.search(r"vai usar\s*(\d+)\s*créditos", texto or "")
    return int(m.group(1)) if m else None


def conferir_custo_menu(mostrado, esperado, teto=None):
    """Com custo conhecido, o Flow tem que mostrar exatamente ele. Sem custo conhecido, tem que caber no teto."""
    if esperado is None:
        if mostrado is None or teto is None or mostrado > teto:
            sys.exit(f"O Flow mostra {mostrado} créditos e o teto combinado é {teto}. Nada foi gerado.")
        return mostrado
    if mostrado != esperado:
        sys.exit(f"O Flow mostra {mostrado} créditos, o combinado era {esperado}. Nada foi gerado: confira x1 e a duração.")
    return mostrado


def opcoes_video(segundos, modo="elementos", formato="9:16"):
    """Elementos: a imagem entra como única referência (o prompt diz isso). Frames só se for usar quadro final.
    Resolução sempre 720p (tamanho original); 1080p é pedido no download."""
    SELETORES["formato"] = formato
    SELETORES["resolucao"] = "720p"
    modelo = modelo_omni(segundos)
    SELETORES["omni"] = MODELOS_OMNI[modelo]
    if modelo == "1.2":  # no 1.2 a duração é uma barra (3 a 15 s), não botões
        return ["aba_video", modo, "formato", "omni", "resolucao", "duracao_barra", "x1"]
    SELETORES["duracao"] = f"{segundos}s"
    return ["aba_video", modo, "formato", "omni", "resolucao", "duracao", "x1"]


def escolher_conta(saldos, custo):
    """saldos: {conta: créditos ou None}. Primeira conta, na ordem, que paga a cena."""
    for n, saldo in saldos.items():
        if saldo is not None and saldo >= custo:
            return n
    return None


def conferir_gasto(saldo, custo):
    if saldo is None:
        sys.exit("Não consegui ler o saldo do Flow. Nada foi gasto.")
    if saldo < custo:
        sys.exit(f"Saldo {saldo} créditos, a cena custa {custo}. Nada foi gasto: use a API do Veo ou espere renovar.")
    return saldo - custo


# ---------- navegador ----------

def padrao_perfil(perfil):
    """Expressão que acha, na linha de comando de um processo, exatamente este perfil (não o -2, -3...)."""
    return r'--user-data-dir="?' + re.escape(str(perfil)) + r'"?(?:\s|$)'


def _linhas_de_comando_do_chrome():
    if sys.platform == "win32":
        r = subprocess.run(["powershell", "-NoProfile", "-Command",
                            "Get-CimInstance Win32_Process -Filter \"Name='chrome.exe'\" | ForEach-Object { $_.CommandLine }"],
                           capture_output=True, text=True)
    else:
        r = subprocess.run(["ps", "-eo", "args"], capture_output=True, text=True)
    return r.stdout.splitlines()


def _porta_e_do_nosso_chrome(porta, perfil):
    """A porta de controle só é usada se quem está nela é o Chrome do perfil do robô. Outro Chrome aberto com
    depuração (de outro programa ou outro perfil) nunca é controlado."""
    alvo = re.compile(padrao_perfil(perfil))
    return any(f"--remote-debugging-port={porta}" in l and alvo.search(l) for l in _linhas_de_comando_do_chrome())


def _chrome_aberto():
    c = conta(ATUAL)
    try:
        urllib.request.urlopen(f"http://127.0.0.1:{c['porta']}/json/version", timeout=2)
    except OSError:
        return False
    if not _porta_e_do_nosso_chrome(c["porta"], c["perfil"]):
        sys.exit(f"A porta {c['porta']} está em uso por outro programa ou outro Chrome, não pelo Chrome do robô "
                 f"({c['perfil']}). Por segurança o robô não se conecta. Feche esse programa e rode de novo.")
    return True


def _abrir_chrome():
    """Chrome comum, com perfil próprio. O Google não aceita login em navegador lançado pela automação,
    então o script só se conecta a este Chrome depois que a pessoa entrou."""
    if _chrome_aberto():
        return
    c = conta(ATUAL)
    c["perfil"].mkdir(parents=True, exist_ok=True)
    subprocess.Popen([achar_chrome(), f"--remote-debugging-port={c['porta']}", f"--user-data-dir={c['perfil']}",
                      "--no-first-run", URL])
    for _ in range(30):
        if _chrome_aberto():
            return
        time.sleep(1)
    sys.exit("O Chrome do Flow não abriu.")


def _fechar_chrome_da_conta():
    """Fecha só o Chrome desta conta (pelo perfil). O login fica salvo no perfil."""
    padrao = padrao_perfil(conta(ATUAL)["perfil"]).replace("'", "''")
    if sys.platform != "win32":
        subprocess.run(["pkill", "-f", "--", padrao], capture_output=True)
        time.sleep(3)
        return
    subprocess.run(["powershell", "-NoProfile", "-Command",
                    "Get-CimInstance Win32_Process -Filter \"Name='chrome.exe'\" | "
                    f"Where-Object {{ $_.CommandLine -match '{padrao}' }} | "
                    "ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }"],
                   capture_output=True)
    time.sleep(3)


def _abrir(p):
    _abrir_chrome()
    url = f"http://127.0.0.1:{conta(ATUAL)['porta']}"
    try:
        navegador = p.chromium.connect_over_cdp(url, timeout=20000)
    except Exception:  # o Chrome da conta às vezes trava e não aceita mais controle: reinicia só ele
        print(f"Conta {ATUAL}: Chrome travado, reiniciando.")
        _fechar_chrome_da_conta()
        _abrir_chrome()
        navegador = p.chromium.connect_over_cdp(url, timeout=60000)
    ctx = navegador.contexts[0]
    pagina = ctx.new_page()
    return pagina, pagina


def _clicar(pg, chave, exato=False):
    nome = SELETORES[chave]
    if any(x in nome for x in PROIBIDOS):
        raise RuntimeError(f"Botão proibido: {nome}")
    for papel in ("radio", "menuitem", "option", "tab", "button"):
        alvo = pg.get_by_role(papel, name=nome, exact=exato)
        if alvo.count():
            alvo.first.click()
            return
    pg.get_by_text(nome, exact=exato).first.click()


def _fechar_paineis(pg):
    """Fecha painéis do Flow (conta, menus, configuração). Esc primeiro; se não fechar, clica no fundo
    ou, no menu de configuração (que não tem fundo), no próprio gatilho."""
    for _ in range(4):
        paineis = pg.locator(".cdk-overlay-pane")
        if not any(paineis.nth(i).inner_text().strip() for i in range(paineis.count())):
            return
        pg.keyboard.press("Escape")
        pg.wait_for_timeout(400)
        fundo = pg.locator(".cdk-overlay-backdrop-showing")
        if fundo.count():
            fundo.last.click(force=True)
        elif pg.locator(".cdk-overlay-container .credit-cost-label").count():
            pg.get_by_role("button", name=SELETORES["config"]).first.click(force=True)
        pg.wait_for_timeout(500)


def _desligar_agente(pg):
    """Contas novas do Flow abrem com o modo Agente ligado e o painel do agente aberto à direita: o pedido iria
    para o assistente, não direto para a geração. Desliga o Agente e fecha esse painel (visto em 18/11/2026)."""
    agente = pg.get_by_role("button", name="Agente", exact=True)
    if agente.count() and agente.first.get_attribute("aria-pressed") == "true":
        agente.first.click()
        pg.wait_for_timeout(800)
    painel = pg.locator("button[aria-label='Fechar']").filter(has_not_text="left_panel_close")
    if pg.get_by_role("button", name="Iniciar nova sessão").count() and painel.count():
        painel.first.click()
        pg.wait_for_timeout(800)


def _preparar(pg):
    """Tela limpa: sem painel aberto, sem busca filtrando a grade, vendo todas as mídias, comando vazio,
    modo Agente desligado."""
    _fechar_paineis(pg)
    _desligar_agente(pg)
    limpar = pg.get_by_role("button", name="Limpar entrada da pesquisa")
    if limpar.count() and limpar.first.is_visible():
        limpar.first.click()
        pg.wait_for_timeout(500)
    pg.get_by_text("Todas as mídias", exact=True).first.click()
    pg.wait_for_timeout(1000)
    _apagar_comando(pg)


def _ir_ao_projeto(pg):
    arq = conta(ATUAL)["projeto"]
    url = arq.read_text(encoding="utf-8").strip() if arq.exists() else ""
    # ?hl=pt-BR: cada conta pode estar em outro idioma, e os SELETORES são em português
    pg.goto((url or URL).split("?")[0] + "?hl=pt-BR")
    # o Flow às vezes nunca fica "networkidle" (visto em 27/10): espera o load e segue
    try:
        pg.wait_for_load_state("networkidle", timeout=20000)
    except Exception:
        pg.wait_for_load_state("load")
        pg.wait_for_timeout(5000)
    if not url:
        _clicar(pg, "novo_projeto")
        pg.wait_for_url(re.compile(r".*/project/.*"), timeout=60000)
        arq.parent.mkdir(parents=True, exist_ok=True)
        arq.write_text(pg.url.split("?")[0], encoding="utf-8")
    pg.wait_for_timeout(2000)
    _preparar(pg)


def _saldo(pg):
    texto = pg.inner_text("body")
    if ler_saldo(texto) is None:
        _clicar(pg, "avatar")
        pg.wait_for_timeout(1500)
        texto = pg.inner_text("body")
        _fechar_paineis(pg)
    return ler_saldo(texto)


def _modelo(pg, nome):
    botao = pg.locator(".cdk-overlay-container button", has_text="arrow_drop_down").first
    if nome in botao.inner_text():
        return
    botao.click()
    pg.wait_for_timeout(800)
    pg.locator(".cdk-overlay-container [role=menuitem], .cdk-overlay-container [role=option], .cdk-overlay-container button",
               has_text=nome).last.click()
    pg.wait_for_timeout(800)


def _duracao_barra(pg, segundos):
    """Omni 1.2: barra de 3 a 15 s com passo de 1. Home vai a 3 s e cada seta soma 1 s; confere o valor ao final."""
    barra = pg.locator(".cdk-overlay-container").get_by_role("slider").first
    barra.focus()
    pg.keyboard.press("Home")
    for _ in range(segundos - 3):
        pg.keyboard.press("ArrowRight")
    pg.wait_for_timeout(400)
    if barra.input_value() != str(segundos - 3):  # o valor da barra é o passo (0 a 12); o rótulo mostra passo + 3
        sys.exit(f"A barra de duração ficou no passo {barra.input_value()}, o combinado era {segundos} s. Nada foi gerado.")


def _configurar(pg, opcoes, custo_esperado, segundos=None, teto=None):
    """Marca cada opção e confere o custo que o próprio Flow mostra antes de fechar o menu."""
    _fechar_paineis(pg)
    _clicar(pg, "config")
    pg.wait_for_timeout(800)
    for chave in opcoes:
        if chave in ("omni", "nano"):
            _modelo(pg, SELETORES[chave])
        elif chave == "duracao_barra":
            _duracao_barra(pg, segundos)
        else:
            _clicar(pg, chave, exato=chave in ("x1", "duracao", "formato", "resolucao"))
        pg.wait_for_timeout(400)
    pg.wait_for_timeout(600)
    mostrado = conferir_custo_menu(ler_custo_menu(pg.locator(".cdk-overlay-container").inner_text()), custo_esperado, teto)
    _fechar_paineis(pg)
    return mostrado


def _apagar_comando(pg):
    botao = pg.get_by_role("button", name=SELETORES["apagar"])
    if botao.count() and botao.first.is_visible():
        botao.first.click()
        pg.wait_for_timeout(500)


def _subir_imagem(pg, arquivo, limpar=True):
    """Envia a imagem com nome único (cena + horário) e coloca no comando. Assim nunca pega uma imagem antiga."""
    pasta_tmp = Path(tempfile.mkdtemp(prefix="flow_"))
    unico = pasta_tmp / f"{Path(arquivo).stem}_{time.strftime('%H%M%S')}{Path(arquivo).suffix}"
    shutil.copy(arquivo, unico)
    try:
        _enviar_arquivo(pg, unico, limpar)
    finally:
        shutil.rmtree(pasta_tmp, ignore_errors=True)


def _enviar_arquivo(pg, unico, limpar):
    _fechar_paineis(pg)
    if limpar:
        _apagar_comando(pg)
    pg.get_by_role("button", name=SELETORES["elementos_add"]).first.click(force=True)
    pg.wait_for_timeout(1000)
    with pg.expect_file_chooser() as fc:
        pg.locator(".cdk-overlay-container").get_by_text(SELETORES["enviar_midia"]).first.click()
    fc.value.set_files(str(unico))
    pg.wait_for_timeout(2000)
    if pg.get_by_text("Direitos de uso desta imagem").count():
        sys.exit(f"Conta {ATUAL}: o Flow pede para a pessoa aceitar 'Direitos de uso desta imagem' (só na 1ª vez). "
                 "Peça para ela clicar em Concordo na janela e rode de novo. Nada foi gerado.")
    item = pg.locator(".cdk-overlay-container").get_by_text(unico.name, exact=True).first
    item.wait_for(timeout=120000)
    pg.wait_for_timeout(1500)
    item.click()
    pg.wait_for_timeout(1000)
    pg.locator(".cdk-overlay-container").get_by_text(SELETORES["incluir"], exact=True).click()
    pg.wait_for_timeout(1500)
    _fechar_paineis(pg)


def _escrever_comando(pg, texto):
    """A caixa do comando é um editor ProseMirror (não é a busca do topo)."""
    caixa = pg.locator(".ProseMirror[contenteditable=true]").last
    caixa.click()
    pg.keyboard.press("Control+A")
    pg.keyboard.press("Delete")
    pg.keyboard.insert_text(texto)
    pg.wait_for_timeout(500)
    if texto[:40] not in caixa.inner_text():
        sys.exit("O texto não entrou na caixa do comando. Nada foi gerado.")


JS_TILES = """t => [...document.querySelectorAll('flow-grid-tile-container')]
    .filter(c => !!c.querySelector(t === 'video' ? 'flow-video-tile' : 'flow-image-tile'))
    .map(c => {
      const m = c.querySelector('video, source, img');
      return {src: (m && (m.currentSrc || m.src)) || '', nome: c.getAttribute('aria-label') || ''};
    }).filter(x => x.src)"""
# Cada miniatura é um <flow-grid-tile-container aria-label="nome">, com <flow-video-tile> ou <flow-image-tile>.
# O vídeo só vira <video> com o mouse em cima; antes é um <img> com o mesmo link (flow.google.com/asb/...),
# que baixa o mp4 inteiro. Testado em 09/10.
_ULTIMA_MIDIA = {"nome": None}
ENVIADO = re.compile(r"\.(jpe?g|png|webp|mp4|mov)$", re.I)


def baixado_ok(tipo, corpo, content_type):
    """Recusa miniatura ou página no lugar da mídia: imagem original tem centenas de KB, vídeo mais ainda."""
    minimo = 200_000 if tipo == "video" else 150_000
    return (content_type or "").startswith(tipo) and len(corpo) >= minimo


def contar(tiles):
    """Quantas mídias de cada nome já existem (o link muda ao recarregar a página; o nome não)."""
    return Counter(t["nome"] for t in tiles)


def midias_novas(antes, tiles):
    """Todas as mídias que apareceram depois de `antes` (sem contar arquivos enviados), na ordem da grade."""
    agora, vistos, novas = contar(tiles), set(), []
    for t in tiles:
        nome = t["nome"]
        if nome in vistos or ENVIADO.search(nome.strip()):
            continue
        vistos.add(nome)
        if agora[nome] > antes[nome]:
            novas.append(nome)
    return novas


def conferir_marcador(pendente, destino):
    """Marcador com várias candidatas (outra pessoa gerou no mesmo projeto ao mesmo tempo): não adivinha."""
    if pendente and not pendente.get("nome"):
        sys.exit("Esta mídia já foi gerada (crédito usado), mas apareceram outras ao mesmo tempo no projeto: "
                 f"{', '.join(pendente.get('candidatos', []))}. Veja no Flow qual é a deste pedido, escreva o nome no "
                 f"campo \"nome\" de {marcador(destino)} e rode de novo: o robô só baixa, sem gerar outra vez.")
    return pendente


def escolher_nova(antes, tiles):
    """A mídia gerada agora: a primeira (a grade mostra as mais novas primeiro) de um nome que passou da
    contagem de antes, ignorando arquivo enviado (nome de arquivo, ex. T1_135123.jpg)."""
    agora = contar(tiles)
    for t in tiles:
        if agora[t["nome"]] > antes[t["nome"]] and not ENVIADO.search(t["nome"].strip()):
            return t
    return None


def escolher_imagem_principal(imagens):
    """Na página da mídia aberta, a imagem principal é a que ocupa mais área na tela (as da faixa de cima
    são miniaturas pequenas na tela, mesmo com arquivo grande). Ignora ícones (< 500 px)."""
    candidatas = [i for i in imagens if i["w"] >= 500 and i["h"] >= 500]
    return max(candidatas, key=lambda i: i["area"])["src"] if candidatas else None


JS_IMAGENS_DA_PAGINA = """() => [...document.querySelectorAll('img')].map(i => {
    const r = i.getBoundingClientRect();
    return {src: i.currentSrc || i.src, w: i.naturalWidth, h: i.naturalHeight, area: r.width * r.height};
}).filter(x => x.src)"""


def _link_original_imagem(pg, nome):
    """Desde 17/11/2026 a miniatura da grade é um WebP pequeno. A imagem em tamanho original (1K) aparece
    ao abrir a mídia: abre a página dela (…/edit/<id>) e pega a imagem principal."""
    if "/edit/" not in pg.url:
        pg.locator(f'flow-grid-tile-container[aria-label="{nome}"]').first.click()
        pg.wait_for_url(re.compile(r".*/edit/.*"), timeout=60000)
    pg.wait_for_timeout(3000)
    return escolher_imagem_principal(pg.evaluate(JS_IMAGENS_DA_PAGINA))


def _link_da_midia(pg, tipo, nome):
    """Link da mídia da miniatura. No vídeo, o <img> é só a capa: passa o mouse para o <video> aparecer."""
    tile = pg.locator(f'flow-grid-tile-container[aria-label="{nome}"]').first
    if tipo == "video":
        tile.scroll_into_view_if_needed()
        tile.hover()
        pg.wait_for_timeout(2500)
        sel = "video, source"
    else:
        sel = "img"
    return tile.evaluate(f"c => {{ const m = c.querySelector('{sel}'); return m ? (m.currentSrc || m.src) : ''; }}")


def marcador(saida):
    """Arquivo ao lado da saída que diz "já foi gerado (crédito usado), falta baixar"."""
    return Path(f"{saida}.gerado.json")


def ler_marcador(saida):
    m = marcador(saida)
    return json.loads(m.read_text(encoding="utf-8")) if m.exists() else None


def _mostrar_tipo(pg, tipo):
    """Filtra a grade (Imagens / Vídeos) para achar uma mídia mais antiga pelo nome."""
    rotulo = "Vídeos" if tipo == "video" else "Imagens"
    alvo = pg.get_by_text(rotulo, exact=True)
    if alvo.count():
        alvo.first.click()
        pg.wait_for_timeout(2500)


# Quadro de falha na grade (ex.: "Falha / Esta geração talvez viole nossas políticas... Não houve cobrança").
JS_FALHAS = r"""() => [...document.querySelectorAll('flow-grid-tile-container, [role=listitem], div')]
    .filter(e => /N[ãa]o houve cobran[çc]a/i.test(e.innerText || '') && !e.querySelector('img, video')
                 && e.children.length < 12 && (e.innerText || '').length < 400)
    .map(e => (e.innerText || '').trim().replace(/\s+/g, ' '))"""


def falha_nova(antes, agora):
    """Texto da falha que apareceu depois de clicar em gerar (None se não houve). Compara quantas vezes
    cada texto aparece, porque falhas antigas no mesmo projeto continuam na grade."""
    novas = Counter(agora) - Counter(antes)
    texto = next(iter(novas), None)
    if texto:  # tira os nomes dos ícones que vêm junto no texto do quadro
        texto = re.sub(r"\b(warning|error|refresh|undo|delete_forever|delete)\b", "", texto)
        texto = re.sub(r"\s+", " ", texto).strip().rstrip(".")
    return texto


def _falhas(pg):
    try:
        return pg.evaluate(JS_FALHAS)
    except Exception:
        return []


def _enviar_e_baixar(pg, prompt, tipo, destino, conferir_antes=None):
    """tipo: 'image' ou 'video'. Gera, espera aparecer a mídia gerada na grade e baixa o tamanho original.
    Logo que a mídia aparece, grava o marcador: se o download falhar, rodar de novo só baixa, sem gerar
    (e sem gastar) outra vez. `conferir_antes` roda depois de escrever o pedido e antes de clicar em gerar."""
    pendente = conferir_marcador(ler_marcador(destino), destino)
    if pendente:
        print(f"Já gerado antes ({pendente['nome']}): só baixando, sem gerar de novo.")
        _mostrar_tipo(pg, tipo)
        antes, nova = Counter(), {"nome": pendente["nome"], "src": ""}
        falhas_antes = None
    else:
        antes = contar(pg.evaluate(JS_TILES, tipo))
        falhas_antes = _falhas(pg)
        _desligar_agente(pg)  # o Agente sempre desligado: com ele ligado o pedido vira conversa e não gera
        _escrever_comando(pg, prompt)
        if conferir_antes:
            conferir_antes()
        _clicar(pg, "gerar")
        nova = None
    voltas, limite = 0, time.time() + ESPERA_GERACAO_MS / 1000
    while not nova:
        if time.time() > limite:
            sys.exit("A geração não apareceu na grade a tempo (falhou ou demorou). Confira no Flow antes de tentar de novo.")
        pg.wait_for_timeout(5000)
        voltas += 1
        if falhas_antes is not None:
            falha = falha_nova(falhas_antes, _falhas(pg))
            if falha:
                sys.exit(f"O Flow recusou esta geração: \"{falha}\" (nada foi cobrado). Mude o pedido "
                         "(texto ou imagens de referência) e rode de novo")
        if voltas % 12 == 0:  # a grade nem sempre mostra o vídeo novo sem recarregar
            pg.reload()
            pg.wait_for_timeout(8000)
        nova = escolher_nova(antes, pg.evaluate(JS_TILES, tipo))
    if not pendente:
        pg.wait_for_timeout(5000)  # dá tempo de aparecer outra mídia nova (outra pessoa gerando no mesmo projeto)
        candidatas = midias_novas(antes, pg.evaluate(JS_TILES, tipo))
        if len(candidatas) > 1:
            marcador(destino).parent.mkdir(parents=True, exist_ok=True)
            marcador(destino).write_text(json.dumps({"nome": None, "candidatos": candidatas, "conta": ATUAL},
                                                    ensure_ascii=False), encoding="utf-8")
            conferir_marcador(ler_marcador(destino), destino)
        marcador(destino).parent.mkdir(parents=True, exist_ok=True)
        marcador(destino).write_text(json.dumps({"nome": nova["nome"], "conta": ATUAL}, ensure_ascii=False), encoding="utf-8")
    corpo = b""
    for tentativa in range(24):  # a mídia pode ainda estar processando (até ~3 min)
        pg.wait_for_timeout(5000)
        if tentativa and tentativa % 6 == 0:
            pg.reload()
            pg.wait_for_timeout(8000)
        if tipo == "image":
            link = _link_original_imagem(pg, nova["nome"]) or nova["src"]
        else:
            if not pendente:
                nova = escolher_nova(antes, pg.evaluate(JS_TILES, tipo)) or nova
            link = _link_da_midia(pg, tipo, nova["nome"]) or nova["src"]
        resposta = pg.request.get(link)
        corpo = resposta.body() if resposta.ok else b""
        if baixado_ok(tipo, corpo, resposta.headers.get("content-type")):
            break
    else:
        sys.exit(f"A mídia ({nova['nome']}) foi gerada mas não baixou inteira. Rode o mesmo comando de novo: "
                 "o robô só baixa, sem gerar nem gastar outra vez.")
    destino = Path(destino)
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_bytes(corpo)
    marcador(destino).unlink(missing_ok=True)
    _ULTIMA_MIDIA["nome"] = nova["nome"]
    print(f"Baixada: {nova['nome'] or 'sem nome'}")
    return destino


# ---------- registro de gastos (cada geração, com conta, créditos e saldo que sobrou) ----------

def _arq_gastos():
    return CONFIG / "gastos.jsonl"


def registrar_gasto(tipo, conta_n, creditos, arquivo, saldo_depois=None):
    """Anota uma geração: imagem (0), vídeo ou 1080p. Fica no computador da pessoa (CONFIG/gastos.jsonl)."""
    linha = {"quando": time.strftime("%Y-%m-%d %H:%M"), "ts": time.time(), "tipo": tipo, "conta": conta_n,
             "creditos": int(creditos or 0), "arquivo": str(arquivo)}
    if saldo_depois is not None:
        linha["saldo_depois"] = int(saldo_depois)
    _arq_gastos().parent.mkdir(parents=True, exist_ok=True)
    with _arq_gastos().open("a", encoding="utf-8") as f:
        f.write(json.dumps(linha, ensure_ascii=False) + "\n")


def resumo_gastos(dias=None):
    """Total gasto, por tipo (quantidade, créditos), por conta e o último saldo conhecido de cada conta."""
    r = {"total": 0, "por_tipo": {}, "por_conta": {}, "ultimo_saldo": {}, "itens": []}
    if not _arq_gastos().exists():
        return r
    limite = time.time() - dias * 86400 if dias else 0
    for linha in _arq_gastos().read_text(encoding="utf-8").splitlines():
        try:
            g = json.loads(linha)
        except ValueError:
            continue
        if g.get("ts", 0) < limite:
            continue
        r["itens"].append(g)
        r["total"] += g["creditos"]
        qtd, cred = r["por_tipo"].get(g["tipo"], (0, 0))
        r["por_tipo"][g["tipo"]] = (qtd + 1, cred + g["creditos"])
        r["por_conta"][g["conta"]] = r["por_conta"].get(g["conta"], 0) + g["creditos"]
        if "saldo_depois" in g:
            r["ultimo_saldo"][g["conta"]] = g["saldo_depois"]
    return r


def mostrar_gastos(dias=None):
    r = resumo_gastos(dias)
    periodo = f"nos últimos {dias} dias" if dias else "desde o começo"
    if not r["itens"]:
        print(f"Nenhuma geração registrada {periodo}.")
        return
    print(f"Gastos {periodo}: {r['total']} créditos")
    nomes = {"imagem": "imagens", "video": "vídeos", "1080p": "downloads em 1080p"}
    for tipo, (qtd, cred) in r["por_tipo"].items():
        print(f"  {qtd} {nomes.get(tipo, tipo)}: {cred} créditos")
    for c, cred in sorted(r["por_conta"].items()):
        saldo = r["ultimo_saldo"].get(c)
        print(f"  conta {c}: gastou {cred}" + (f", sobrou {saldo} na última geração" if saldo is not None else ""))
    print("Saldo de agora: python flow.py saldo")


# ---------- preferências da pessoa (perguntas iniciais) ----------

OPCOES_PREF = {
    # Só o que a ferramenta usa. Estilo, idioma, música e legendas ficam no prompt da pessoa.
    "formato": ("9:16", "16:9", "1:1", "4:3", "3:4", "depende"),
    "download": ("720p", "1080p", "depende"),  # 1080p = versão ampliada do Flow, cobrada à parte
}

# Baixar a versão ampliada em 1080p (menu "Baixar mídia" > "1080p Resolução ampliada"): 5 créditos por vídeo,
# lido no Flow em 16/11/2026. 4K exige upgrade do plano e fica de fora (o robô nunca clica em upgrade).
CUSTO_1080P = 5
ESPERA_1080P_S = 12 * 60  # o Flow processa a ampliação (~1,5 min num vídeo de 15 s, testado em 16/11/2026)


def ler_custo_1080p(texto):
    m = re.search(r"(\d+)\s*créditos", texto or "")
    return int(m.group(1)) if m else None


def conferir_custo_1080p(mostrado):
    if mostrado != CUSTO_1080P:
        sys.exit(f"O Flow mostra {mostrado} créditos para o 1080p, o combinado era {CUSTO_1080P}. Nada foi gasto.")
    return mostrado


def saida_1080p(saida):
    s = Path(saida)
    return s.with_name(f"{s.stem}_1080p{s.suffix}")


def achar_1080p_baixado(pasta, desde):
    """O arquivo *_1080p.mp4 que chegou na pasta depois de `desde` (ignora o que ainda está baixando)."""
    novos = [f for f in Path(pasta).glob("*_1080p.mp4") if f.stat().st_mtime >= desde]
    return max(novos, key=lambda f: f.stat().st_mtime) if novos else None


def _arq_pref():
    return CONFIG / "preferencias.json"


def ler_preferencias():
    arq = _arq_pref()
    if not arq.exists():
        return {}
    try:
        return json.loads(arq.read_text(encoding="utf-8"))
    except ValueError:
        sys.exit(f"{arq} está corrompido: apague e responda as perguntas iniciais de novo.")


def salvar_preferencias(novas):
    for campo, valor in novas.items():
        if campo not in OPCOES_PREF:
            sys.exit(f"Preferência desconhecida: {campo}. Use {', '.join(OPCOES_PREF)}.")
        validos = OPCOES_PREF[campo]
        if validos and valor not in validos:
            sys.exit(f"{campo}={valor} não vale. Opções: {', '.join(validos)}.")
    prefs = {**ler_preferencias(), **novas}
    _arq_pref().parent.mkdir(parents=True, exist_ok=True)
    _arq_pref().write_text(json.dumps(prefs, ensure_ascii=False, indent=2), encoding="utf-8")
    return prefs


def formato_padrao(pedido):
    """O formato pedido; sem pedido, o das preferências; se lá estiver "depende" ou vazio, 9:16."""
    if pedido:
        return pedido
    f = ler_preferencias().get("formato")
    return f if f and f != "depende" else "9:16"


# ---------- comandos ----------

def usar(n):
    global ATUAL
    ATUAL = n


def login(n=1):
    usar(n)
    _abrir_chrome()
    print("Entre na sua conta Google na janela do Chrome que abriu. Deixe a janela aberta.")


def mapear(saida=None):
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        ctx, pg = _abrir(p)
        _ir_ao_projeto(pg)
        nomes = pg.evaluate("""() => [...document.querySelectorAll('button,[role=button],[role=menuitem],[role=tab],[role=option]')]
            .map(e => (e.getAttribute('aria-label') || e.innerText || '').trim().replace(/\\s+/g,' '))
            .filter(Boolean)""")
        nomes = sorted(set(nomes))
        texto = "\n".join(nomes)
        print(texto)
        if saida:
            Path(saida).write_text(texto, encoding="utf-8")
        ctx.close()


def _saldo_da_conta(p, n):
    usar(n)
    ctx, pg = _abrir(p)
    _ir_ao_projeto(pg)
    valor = _saldo(pg)
    ctx.close()
    return valor


def saldo():
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        for n in contas_com_login():
            print(f"Conta {n}: {_saldo_da_conta(p, n)} créditos")


def _ler_prompt(prompt, arquivo):
    if arquivo:
        return Path(arquivo).read_text(encoding="utf-8").strip()
    if prompt:
        return prompt.strip()
    sys.exit("Faltou o pedido: use --prompt ou --prompt-arquivo.")


def gerar_imagem(prompt, saida, referencias=(), formato="9:16"):
    """Imagem no Nano Banana (sem crédito). `referencias`: imagens que entram junto no comando (mesma pessoa, estilo...)."""
    _nao_sobrescrever(saida)
    contas = contas_com_login()
    if contas:  # imagem não gasta crédito: usa a primeira conta liberada (FLOW_CONTAS / ordem)
        usar(contas[0])
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        ctx, pg = _abrir(p)
        _ir_ao_projeto(pg)
        SELETORES["formato"] = formato
        _configurar(pg, ["aba_imagem", "formato", "nano", "x1"], 0)
        for i, arq in enumerate(referencias):
            _subir_imagem(pg, arq, limpar=(i == 0))
        destino = _enviar_e_baixar(pg, prompt, "image", saida)
        registrar_gasto("imagem", ATUAL, 0, destino)
        ctx.close()
    return destino


def gerar_video(prompt, imagens, saida, segundos, confirmo, maximo=None, modo="elementos", formato="9:16",
                baixar=None):
    """Vídeo no Omni, modo Elementos (as imagens entram como referência; sem imagem, só o texto). Gasta crédito: exige `confirmo`.
    Escolhe a primeira conta que paga e confere o custo que o Flow mostra antes de gerar."""
    if not confirmo:
        sys.exit("Gasto não confirmado. Rode de novo com --confirmo depois de a pessoa aprovar o custo.")
    if modo == "frames":
        sys.exit("O modo Frames não está no script: gere pelo Chrome (referencias/flow-navegador.md).")
    _nao_sobrescrever(saida)
    extra = CUSTO_1080P if baixar == "1080p" else 0
    if baixar == "1080p":
        _nao_sobrescrever(saida_1080p(saida))
    custo = custo_conhecido(segundos)
    teto_geracao = None
    if custo is None:
        if maximo is None:
            sys.exit(f"Não sei o custo de {segundos} s: rode com --max N (teto aprovado pela pessoa); "
                     "o script confere o preço que o Flow mostra antes de gerar. Nada foi gasto.")
        teto_geracao = maximo - extra
        if teto_geracao <= 0:
            sys.exit(f"O limite combinado ({maximo}) não cobre nem o 1080p ({extra}). Nada foi gasto.")
        para_saldo = maximo
    else:
        para_saldo = custo + extra
        if maximo is not None and para_saldo > maximo:
            sys.exit(f"O clipe custa {para_saldo} ({custo} + {extra} do 1080p), acima do limite combinado ({maximo}). "
                     "Nada foi gasto.")
    pendente = ler_marcador(saida)
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        if pendente:  # já gerado antes: só baixa, na mesma conta, sem conferir saldo nem gastar
            usar(pendente.get("conta", 1))
            ctx, pg = _abrir(p)
            _ir_ao_projeto(pg)
            destino = _enviar_e_baixar(pg, prompt, "video", saida)
            if baixar == "1080p":
                _ir_a_midia(pg, nome=_ULTIMA_MIDIA["nome"])
                _baixar_1080p(pg, saida_1080p(saida))
            ctx.close()
            return destino
        saldos = {}
        for n in contas_com_login():
            saldos[n] = _saldo_da_conta(p, n)
            if escolher_conta(saldos, para_saldo):
                break
        n = escolher_conta(saldos, para_saldo)
        if n is None:
            sys.exit(f"Nenhuma conta paga {para_saldo} créditos ({saldos}). Nada foi gasto: espere renovar ou use menos segundos.")
        usar(n)
        ctx, pg = _abrir(p)
        _ir_ao_projeto(pg)
        saldo_atual = _saldo(pg)
        conferir_gasto(saldo_atual, para_saldo)
        mostrado = _configurar(pg, opcoes_video(segundos, modo, formato), custo, segundos, teto=teto_geracao)
        print(f"Conta {n}, {mostrado} créditos no Omni {modelo_omni(segundos)} (720p), sobram {saldo_atual - mostrado}")
        if not imagens:
            _apagar_comando(pg)
        for i, arq in enumerate(imagens):
            _subir_imagem(pg, arq, limpar=(i == 0))
        destino = _enviar_e_baixar(pg, prompt, "video", saida,
                                   conferir_antes=lambda: _reconferir_custo(pg, custo, teto_geracao))
        registrar_gasto("video", n, mostrado, destino, saldo_depois=saldo_atual - mostrado)
        if baixar == "1080p":
            _ir_a_midia(pg, nome=_ULTIMA_MIDIA["nome"])
            _baixar_1080p(pg, saida_1080p(saida))
        ctx.close()
    return destino


def _reconferir_custo(pg, esperado, teto):
    """Lê de novo o "A geração vai usar N créditos" logo antes de gerar (depois de subir as imagens e escrever
    o pedido), para nada ter mudado o custo no caminho."""
    _fechar_paineis(pg)
    _clicar(pg, "config")
    pg.wait_for_timeout(800)
    try:
        conferir_custo_menu(ler_custo_menu(pg.locator(".cdk-overlay-container").inner_text()), esperado, teto)
    finally:
        _fechar_paineis(pg)


def _nao_sobrescrever(saida):
    if Path(saida).exists():
        sys.exit(f"{saida} já existe. Apague ou escolha outro nome; nada foi gerado.")


# ---------- 1080p: menu "Baixar mídia" > "1080p Resolução ampliada" (cobrado à parte) ----------

def _ir_a_midia(pg, url=None, nome=None):
    """Abre a página do vídeo (…/edit/<id>): pelo link, ou clicando na miniatura pelo nome."""
    if url:
        pg.goto(url.split("?")[0] + "?hl=pt-BR")
        pg.wait_for_load_state("load")
    else:
        pg.locator(f'flow-grid-tile-container[aria-label="{nome}"]').first.click()
    pg.wait_for_url(re.compile(r".*/edit/.*"), timeout=60000)
    pg.wait_for_timeout(4000)


def _baixar_1080p(pg, destino):
    """Confere o preço no menu, pede o 1080p e espera o arquivo: pelo evento de download do navegador ou,
    se o Chrome salvar direto, pela pasta Downloads."""
    baixados = []
    pg.on("download", lambda d: baixados.append(d))
    pg.get_by_role("button", name=SELETORES["baixar"]).first.click()
    pg.wait_for_timeout(1500)
    item = pg.get_by_role("menuitem", name=re.compile(r"^1080p")).first
    if not item.count():
        pg.keyboard.press("Escape")
        sys.exit("O menu de download não tem a opção 1080p. Nada foi gasto.")
    texto = item.inner_text()
    if any(x in texto for x in PROIBIDOS):
        pg.keyboard.press("Escape")
        raise RuntimeError(f"Opção proibida: {texto}")
    try:
        conferir_custo_1080p(ler_custo_1080p(texto))
    except SystemExit:
        pg.keyboard.press("Escape")
        raise
    pasta = Path.home() / "Downloads"
    inicio = time.time() - 2
    item.click()
    print(f"1080p pedido ({CUSTO_1080P} créditos). O Flow está ampliando; pode levar alguns minutos.")
    limite = time.time() + ESPERA_1080P_S
    destino = Path(destino)
    destino.parent.mkdir(parents=True, exist_ok=True)
    while time.time() < limite:
        pg.wait_for_timeout(5000)
        if baixados:
            baixados[0].save_as(str(destino))
            break
        achado = achar_1080p_baixado(pasta, inicio)
        if achado:
            pg.wait_for_timeout(3000)  # termina de gravar
            shutil.move(str(achado), str(destino))
            break
    else:
        sys.exit("O 1080p não chegou a tempo. Os créditos podem ter sido usados: baixe à mão no Flow "
                 "(vídeo > Baixar mídia > 1080p) antes de pedir de novo.")
    if destino.stat().st_size < 500_000:
        sys.exit(f"O arquivo 1080p ficou pequeno demais ({destino.stat().st_size} bytes). Confira no Flow.")
    print(f"1080p salvo em {destino}")
    registrar_gasto("1080p", ATUAL, CUSTO_1080P, destino)
    return destino


def ampliar(midia, saida, confirmo, maximo=None):
    """1080p de um vídeo que já está no Flow (o link da página dele). Gasta crédito: exige `confirmo`."""
    if not confirmo:
        sys.exit("Gasto não confirmado. Rode de novo com --confirmo depois de a pessoa aprovar o custo.")
    if not str(midia).startswith("https://flow.google.com/"):
        sys.exit("O link precisa ser da página do vídeo no Flow (https://flow.google.com/...). Nada foi gasto.")
    _nao_sobrescrever(saida)
    if maximo is not None and CUSTO_1080P > maximo:
        sys.exit(f"O 1080p custa {CUSTO_1080P}, acima do limite combinado ({maximo}). Nada foi gasto.")
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        ctx, pg = _abrir(p)
        _ir_ao_projeto(pg)
        saldo_atual = _saldo(pg)
        conferir_gasto(saldo_atual, CUSTO_1080P)
        print(f"Conta {ATUAL}: {saldo_atual} créditos, o 1080p usa {CUSTO_1080P}.")
        _ir_a_midia(pg, url=midia)
        destino = _baixar_1080p(pg, saida)
        ctx.close()
    return destino


# ---------- juntar os vídeos (ffmpeg local, não usa o Flow nem gasta crédito) ----------

TAMANHOS = {"9:16": (720, 1280), "16:9": (1280, 720), "1:1": (720, 720)}
TRANSICAO_S = 0.4
# nome em português -> efeito do ffmpeg (xfade); "corte" é corte seco
TRANSICOES = {
    "corte": None,
    "suave": "fade",
    "esmaecer-preto": "fadeblack",
    "esmaecer-branco": "fadewhite",
    "deslizar-esquerda": "slideleft",
    "deslizar-direita": "slideright",
    "aproximar": "zoomin",
    "afastar": "custom",  # o ffmpeg não tem: a cena A encolhe até o centro e revela a B (EXPR_AFASTAR)
    # nomes antigos (v1.2), aceitos para projetos já salvos
    "deslizar": "slideleft", "zoom": "zoomin", "circulo": "circleopen",
}
_SX = "floor((X-W/2)/max(P,0.001)+W/2)"
_SY = "floor((Y-H/2)/max(P,0.001)+H/2)"
# Sem st()/ld(): o xfade roda em várias partes ao mesmo tempo e essas variáveis se misturam (dava chuvisco).
EXPR_AFASTAR = (f"if(between({_SX},0,W-1)*between({_SY},0,H-1),"
                f"if(eq(PLANE,0),a0({_SX},{_SY}),if(eq(PLANE,1),a1({_SX},{_SY}),a2({_SX},{_SY}))),"
                "if(eq(PLANE,0),b0(X,Y),if(eq(PLANE,1),b1(X,Y),b2(X,Y))))")


def ler_trecho(entrada):
    """"cena01.mp4@0-6" = só do segundo 0 ao 6 (para aproveitar a parte boa de um clipe). Sem @, o vídeo inteiro."""
    m = re.match(r"^(.*)@([\d.]+)-([\d.]+)$", str(entrada))
    if not m:
        return str(entrada), None, None
    inicio, fim = float(m.group(2)), float(m.group(3))
    if fim <= inicio:
        sys.exit(f"Trecho inválido em {entrada}: o fim tem que ser depois do início.")
    return m.group(1), inicio, fim


def lista_de_transicoes(transicao, n):
    """Uma transição para todas as junções ("suave") ou uma por junção (["corte", "deslizar", ...] ou "corte,suave")."""
    if isinstance(transicao, str):
        transicao = transicao.split(",") if "," in transicao else [transicao] * (n - 1)
    transicao = [t.strip() for t in transicao]
    if len(transicao) != n - 1:
        sys.exit(f"São {n} vídeos, então são {n - 1} junções: informe {n - 1} transições (ou uma só para todas).")
    for t in transicao:
        if t not in TRANSICOES:
            validas = [k for k in TRANSICOES if k not in ("deslizar", "zoom", "circulo")]
            sys.exit(f"Transição '{t}' não existe. Use: {', '.join(validas)}.")
    return transicao


def achar_ffmpeg():
    """FLOW_FFMPEG, o ffmpeg do sistema ou o do pacote imageio-ffmpeg (pip install imageio-ffmpeg)."""
    if os.environ.get("FLOW_FFMPEG"):
        return os.environ["FLOW_FFMPEG"]
    if shutil.which("ffmpeg"):
        return shutil.which("ffmpeg")
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        sys.exit("Para juntar vídeos falta o ffmpeg. Instale com: pip install imageio-ffmpeg")


def ler_info_ffmpeg(texto):
    """(duração em segundos, tem áudio?) a partir do que o `ffmpeg -i arquivo` escreve."""
    m = re.search(r"Duration:\s*(\d+):(\d+):([\d.]+)", texto or "")
    if not m:
        sys.exit("Não consegui ler a duração do vídeo.")
    duracao = int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))
    return round(duracao, 3), bool(re.search(r"Stream #.*: Audio:", texto))


def _info_do_video(ffmpeg, arquivo):
    r = subprocess.run([ffmpeg, "-hide_banner", "-i", str(arquivo)], capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    return ler_info_ffmpeg(r.stderr)


def comando_juntar(ffmpeg, entradas, saida, duracoes, com_audio, transicao="corte", musica=None,
                   volume_musica=0.15, formato="9:16"):
    """Monta o comando do ffmpeg: todos os clipes no mesmo tamanho e ritmo (30 q/s), na ordem, com corte seco
    ou transição suave; clipe sem som ganha silêncio; música opcional em loop, baixa, por baixo das falas."""
    if len(entradas) < 2:
        sys.exit("Para juntar são precisos pelo menos 2 vídeos.")
    transicoes = lista_de_transicoes(transicao, len(entradas))
    if formato not in TAMANHOS:
        sys.exit(f"Formato para juntar: {', '.join(TAMANHOS)}.")
    w, h = TAMANHOS[formato]
    cmd = [ffmpeg, "-hide_banner", "-y"]
    for e in entradas:
        arquivo, inicio, fim = ler_trecho(e)
        if inicio is not None:
            cmd += ["-ss", f"{inicio:g}", "-to", f"{fim:g}"]
        cmd += ["-i", arquivo]
    if musica:
        cmd += ["-stream_loop", "-1", "-i", str(musica)]
    partes = []
    for i, (d, a) in enumerate(zip(duracoes, com_audio)):
        partes.append(f"[{i}:v]scale={w}:{h}:force_original_aspect_ratio=decrease,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2,"
                      f"setsar=1,fps=30,format=yuv420p[v{i}]")
        if a:
            partes.append(f"[{i}:a]aresample=48000,aformat=channel_layouts=stereo[a{i}]")
        else:
            partes.append(f"anullsrc=r=48000:cl=stereo,atrim=duration={d:g}[a{i}]")
    n = len(entradas)
    if all(t == "corte" for t in transicoes):
        partes.append("".join(f"[v{i}][a{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=1[v][a]")
    else:
        v, a, acumulado = "[v0]", "[a0]", float(duracoes[0])
        for i in range(1, n):
            vo = "[v]" if i == n - 1 else f"[x{i}]"
            ao = "[a]" if i == n - 1 else f"[y{i}]"
            efeito = TRANSICOES[transicoes[i - 1]]
            if efeito is None:
                partes.append(f"{v}{a}[v{i}][a{i}]concat=n=2:v=1:a=1[c{i}]{ao}")
                partes.append(f"[c{i}]settb=1/30{vo}")  # o concat muda a base de tempo; o xfade exige 1/30 dos dois lados
                acumulado += duracoes[i]
            else:
                tipo = f"custom:expr='{EXPR_AFASTAR}'" if efeito == "custom" else efeito
                partes.append(f"{v}[v{i}]xfade=transition={tipo}:duration={TRANSICAO_S}:"
                              f"offset={round(acumulado - TRANSICAO_S, 3):g}{vo}")
                partes.append(f"{a}[a{i}]acrossfade=d={TRANSICAO_S}{ao}")
                acumulado += duracoes[i] - TRANSICAO_S
            v, a = vo, ao
    saida_audio = "[a]"
    if musica:
        partes.append(f"[{n}:a]aresample=48000,aformat=channel_layouts=stereo,volume={volume_musica:g}[m]")
        partes.append("[a][m]amix=inputs=2:duration=first:dropout_transition=0:normalize=0[am]")
        saida_audio = "[am]"
    cmd += ["-filter_complex", ";".join(partes), "-map", "[v]", "-map", saida_audio,
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-movflags", "+faststart", "-crf", "18", "-preset", "medium", "-c:a", "aac", "-b:a", "192k",
            "-movflags", "+faststart", str(saida)]
    return cmd


def juntar(entradas, saida, transicao="corte", musica=None, volume_musica=0.15, formato=None):
    """Une os clipes na ordem dada num único vídeo. Roda no computador da pessoa; não gasta crédito."""
    _nao_sobrescrever(saida)
    for e in [ler_trecho(x)[0] for x in entradas] + ([musica] if musica else []):
        if not Path(e).exists():
            sys.exit(f"Não achei {e}.")
    ffmpeg = achar_ffmpeg()
    infos = []
    for e in entradas:
        arquivo, inicio, fim = ler_trecho(e)
        duracao, audio = _info_do_video(ffmpeg, arquivo)
        if inicio is not None:
            if fim > duracao + 0.05:
                sys.exit(f"{arquivo} tem {duracao:.1f} s; o trecho pedido vai até {fim:g} s.")
            duracao = fim - inicio
        infos.append((duracao, audio))
    cmd = comando_juntar(ffmpeg, entradas, saida, [d for d, _ in infos], [a for _, a in infos], transicao,
                         musica, volume_musica, formato_padrao(formato))
    Path(saida).parent.mkdir(parents=True, exist_ok=True)
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0 or not Path(saida).exists():
        Path(saida).unlink(missing_ok=True)  # não deixa arquivo final quebrado
        ultima = (r.stderr or "erro desconhecido").strip().splitlines()[-1]
        sys.exit(f"O ffmpeg não conseguiu juntar: {ultima}")
    total = sum(d for d, _ in infos) - TRANSICAO_S * sum(1 for t in lista_de_transicoes(transicao, len(entradas)) if t != "corte")
    print(f"Vídeo final: {saida} ({len(entradas)} clipes, {total:.1f} s)")
    return Path(saida)


# ---------- opções de duração e custo para um vídeo de X segundos (a pessoa escolhe antes do storyboard) ----------

def opcoes_de_duracao(total, folga=2):
    """Jeitos de dividir `total` segundos em clipes que o Flow gera, com o custo de cada jeito. Uma opção por
    quantidade de clipes (a mais barata). Se der para fechar o total exato, só mostra as exatas; senão, as mais
    próximas (até `folga` segundos de diferença)."""
    from itertools import combinations_with_replacement
    tabela = CUSTO_OMNI[os.environ.get("FLOW_OMNI", "1.1")]
    duracoes = sorted(tabela)
    melhores = {}
    for n in range(1, (total + folga) // min(duracoes) + 1):
        for combo in combinations_with_replacement(sorted(duracoes, reverse=True), n):
            if len(set(combo)) > 2:  # no máximo dois tamanhos de clipe: fácil de entender e de montar
                continue
            soma = sum(combo)
            dif = abs(soma - total)
            if dif > folga:
                continue
            custo = sum(tabela[d] for d in combo)
            chave = (dif, custo, max(combo) - min(combo))
            k = (n, soma)  # uma opção por quantidade de clipes e por duração final (24 s e 26 s aparecem as duas)
            if k not in melhores or chave < melhores[k][0]:
                melhores[k] = (chave, {"clipes": list(combo), "total": soma, "creditos": custo})
    ops = [o for _, o in sorted(melhores.values(), key=lambda x: x[0])]
    exatas = [o for o in ops if o["total"] == total]
    escolhidas = exatas or ops
    return sorted(escolhidas, key=lambda o: (abs(o["total"] - total), o["creditos"], len(o["clipes"])))[:5]


def texto_opcoes(total, com_1080p=False):
    from collections import Counter as _C
    linhas = [f"Opções para um vídeo de {total} s:"]
    for i, o in enumerate(opcoes_de_duracao(total), 1):
        partes = " + ".join(f"{q} vídeo{'s' if q > 1 else ''} de {d} s" for d, q in sorted(_C(o["clipes"]).items(), reverse=True))
        extra = f" (+{CUSTO_1080P * len(o['clipes'])} no 1080p)" if com_1080p else ""
        aviso = "" if o["total"] == total else f" · fica com {o['total']} s"
        linhas.append(f"  {i}. {partes} = {o['total']} s → {o['creditos']} créditos{extra}{aviso}")
    linhas.append("10 s é o mais barato por segundo; mais clipes curtos = mais cortes e mais custo.")
    return "\n".join(linhas)


# ---------- storyboard (página visual para aprovar) e itens do lote, a partir de projeto.json ----------

def _nome_cena(n, ext):
    return f"cena{n:02d}.{ext}"


def resumo_do_projeto(proj):
    """Custos por cena (vídeo + 1080p), total, duração e quanto falta do saldo."""
    cenas, total, duracao = [], 0, 0
    for n, c in enumerate(proj["cenas"], 1):
        seg = int(c.get("segundos", 0))
        cred = 0
        if c.get("prompt_video"):
            base = custo_conhecido(seg) if seg else 0
            if base is None:
                if c.get("max") is None:
                    sys.exit(f"Cena {n}: custo de {seg} s não está na tabela; ponha \"max\" (teto aprovado).")
                base = int(c["max"])
            cred = base + (CUSTO_1080P if c.get("baixar") == "1080p" else 0)
        cenas.append({**c, "n": n, "creditos": cred, "imagem": _nome_cena(n, "jpg"), "video": _nome_cena(n, "mp4")})
        total += cred
        duracao += seg
    saldo = proj.get("saldo")
    falta = max(0, total - saldo) if saldo is not None else None
    return {"cenas": cenas, "total": total, "duracao": duracao, "saldo": saldo, "falta": falta}


def itens_do_projeto(proj, etapa):
    """Itens do lote de uma etapa: "imagens" (0 crédito) ou "videos" (só depois das imagens aprovadas)."""
    fmt = proj.get("formato", "9:16")
    itens = []
    for c in resumo_do_projeto(proj)["cenas"]:
        if etapa == "imagens" and c.get("prompt_imagem"):
            itens.append({"tipo": "imagem", "prompt": c["prompt_imagem"], "saida": c["imagem"],
                          "referencias": list(c.get("referencias", [])), "formato": fmt})
        elif etapa == "videos" and c.get("prompt_video"):
            item = {"tipo": "video", "prompt": c["prompt_video"], "saida": c["video"], "segundos": int(c["segundos"]),
                    "formato": fmt}
            if c.get("prompt_imagem"):
                if c.get("imagens_extra"):  # Omni (Elementos) aceita várias imagens: ex. personagem + outro ambiente
                    item["imagens"] = [c["imagem"], *c["imagens_extra"]]
                else:
                    item["imagem"] = c["imagem"]
            if c.get("baixar") == "1080p":
                item["baixar"] = "1080p"
            if c.get("max") is not None:
                item["max"] = int(c["max"])
            itens.append(item)
    if etapa not in ("imagens", "videos"):
        sys.exit("Etapa: imagens ou videos.")
    return itens


def html_storyboard(proj, pasta):
    """Página do storyboard: cabeçalho, tabela resumo com créditos, aviso de saldo, cada cena com a imagem
    (quando já existe), os prompts e a transição, e a pergunta da etapa."""
    import html as H
    e = lambda t: H.escape(str(t or ""))
    r = resumo_do_projeto(proj)
    pasta = Path(pasta)
    tem_imagens = any((pasta / c["imagem"]).exists() for c in r["cenas"])
    linhas = "".join(
        f"<tr><td>{c['n']}</td><td>{e(c.get('descricao'))}</td><td class=num>{c.get('segundos', 0)} s</td>"
        f"<td>{e(c['imagem'])}{' (ref. ' + e(', '.join(c.get('referencias', []))) + ')' if c.get('referencias') else ''}</td>"
        f"<td>{e(c['video']) + ' · 720p' + (' + 1080p' if c.get('baixar') == '1080p' else '') if c.get('prompt_video') else '-'}</td>"
        f"<td>{e(c.get('transicao', '') if c['n'] < len(r['cenas']) else 'fim')}</td>"
        f"<td class=num>0 + {c['creditos']}</td></tr>" for c in r["cenas"])
    blocos = []
    for c in r["cenas"]:
        img = (f'<img src="{e(c["imagem"])}" alt="cena {c["n"]}">' if (pasta / c["imagem"]).exists()
               else '<div class=vazio>imagem ainda não gerada</div>')
        extras = [x for x in list(c.get("referencias", [])) + list(c.get("imagens_extra", [])) if (pasta / x).exists()]
        if extras:
            img += ('<p class=refs>Referências</p><div class=miniaturas>'
                    + "".join(f'<figure><img src="{e(x)}" alt="{e(x)}"><figcaption>{e(x)}</figcaption></figure>' for x in extras)
                    + "</div>")
        fala = f'<p><b>Fala:</b> “{e(c["fala"])}”</p>' if c.get("fala") else ""
        blocos.append(f"""<section class=cena><div class=quadro>{img}</div><div class=texto>
<h2>Cena {c['n']} · {e(c.get('descricao'))} <small>{c.get('segundos', 0)} s · {c['creditos']} créditos</small></h2>{fala}
<p><b>Transição para a próxima:</b> {e(c.get('transicao', '-') if c['n'] < len(r['cenas']) else 'fim do vídeo')}</p>
<h3>Prompt da imagem</h3><pre>{e(c.get('prompt_imagem'))}</pre>
<h3>Prompt do vídeo</h3><pre>{e(c.get('prompt_video'))}</pre></div></section>""")
    if r["saldo"] is None:
        saldo = ""
    elif r["falta"]:
        saldo = (f"<div class=aviso><b>Saldo: {r['saldo']} créditos. Faltam {r['falta']}.</b> Dá para gerar agora todas as "
                 "imagens (0 créditos) e só os vídeos que o saldo paga, encurtar cenas, ou esperar os créditos renovarem.</div>")
    else:
        saldo = f"<div class=ok><b>Saldo: {r['saldo']} créditos → sobram {r['saldo'] - r['total']}.</b></div>"
    n_img = len(r["cenas"])
    pergunta = (f"Aprova as {n_img} imagens? Se sim, os vídeos custam {r['total']} créditos (mostro de novo antes de gerar)."
                if tem_imagens else f"Posso gerar as {n_img} imagens (0 créditos)?")
    prefs = " · ".join(e(proj.get(k)) for k in ("estilo", "idioma", "musica", "legendas") if proj.get(k))
    regua = _regua_html(r["cenas"], e)
    return f"""<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Storyboard · {e(proj.get('titulo'))}</title><style>
:root{{--fundo:#f6f5f2;--cartao:#fff;--texto:#1f1d1a;--suave:#6b665e;--linha:#e3dfd7;--destaque:#b4531f}}
body{{margin:0;background:var(--fundo);color:var(--texto);font:16px/1.55 system-ui,"Segoe UI",sans-serif}}
main{{max-width:1000px;margin:0 auto;padding:32px 16px 64px}}h1{{font-size:24px;margin:0 0 4px}}.sub{{color:var(--suave);margin:0 0 20px}}
table{{width:100%;border-collapse:collapse;background:var(--cartao);border:1px solid var(--linha)}}
th,td{{text-align:left;padding:9px 11px;border-bottom:1px solid var(--linha);font-size:14px;vertical-align:top}}
th{{background:#efece6;font-size:12px;text-transform:uppercase;color:var(--suave)}}tr.t td{{font-weight:700}}.num{{white-space:nowrap}}
.aviso{{margin:18px 0;padding:12px 14px;background:#fff4e5;border-left:4px solid #e8a33d;border-radius:6px}}
.ok{{margin:18px 0;padding:12px 14px;background:#ecf8ef;border-left:4px solid #2f9e57;border-radius:6px}}
.regua{{display:flex;gap:2px;margin:6px 0 4px;height:58px}}.regua .seg{{display:flex;flex-direction:column;justify-content:center;padding:0 8px;color:#fff;border-radius:6px;font-size:12px;line-height:1.3;overflow:hidden;white-space:nowrap}}
.regua .seg b{{font-size:13px}}.reguaeixo{{display:flex;justify-content:space-between;color:var(--suave);font-size:12px;margin-bottom:6px}}
.transicoes{{color:var(--suave);font-size:12px;margin:0 0 18px}}.duracao{{font-weight:700;color:var(--texto)}}
.cena{{display:flex;gap:20px;background:var(--cartao);border:1px solid var(--linha);border-radius:10px;padding:16px;margin-top:20px}}
.quadro{{flex:0 0 220px}}.quadro img{{width:220px;border-radius:8px;display:block}}
.vazio{{width:220px;aspect-ratio:9/16;border:2px dashed var(--linha);border-radius:8px;display:flex;align-items:center;justify-content:center;color:var(--suave);font-size:13px;text-align:center}}
.refs{{font-size:12px;text-transform:uppercase;color:var(--suave);margin:10px 0 4px}}
.miniaturas{{display:flex;flex-wrap:wrap;gap:6px;width:220px}}.miniaturas figure{{margin:0;width:68px}}
.miniaturas img{{width:68px;height:68px;object-fit:cover;border-radius:6px}}.miniaturas figcaption{{font-size:10px;color:var(--suave);word-break:break-all}}
.texto{{flex:1;min-width:0}}h2{{font-size:17px;margin:0 0 6px}}h2 small{{color:var(--suave);font-weight:400}}
h3{{font-size:12px;text-transform:uppercase;color:var(--suave);margin:12px 0 4px}}
pre{{background:#f1efea;border:1px solid var(--linha);border-radius:8px;padding:10px;white-space:pre-wrap;font:12.5px/1.5 Consolas,monospace;margin:0}}
.pergunta{{margin-top:28px;padding:16px;border:2px solid var(--destaque);border-radius:10px;font-weight:600;background:var(--cartao)}}
@media(max-width:700px){{.cena{{flex-direction:column}}th:nth-child(4),td:nth-child(4){{display:none}}}}
</style></head><body><main>
<h1>Storyboard: {e(proj.get('titulo'))}</h1>
<p class=sub>{e(proj.get('formato', '9:16'))} · {r['duracao']} s · {prefs} · download em {e(proj.get('download', '720p'))}</p>
{regua}
<table><thead><tr><th>#</th><th>Cena</th><th>Dur.</th><th>Imagem</th><th>Vídeo</th><th>Transição</th><th>Créditos</th></tr></thead>
<tbody>{linhas}<tr class=t><td></td><td>Total</td><td class=num>{r['duracao']} s</td><td>{n_img} imagens: 0</td><td></td><td></td><td class=num>{r['total']}</td></tr></tbody></table>
{saldo}{''.join(blocos)}<div class=pergunta>{e(pergunta)}</div></main></body></html>"""


CORES_REGUA = ("#b4531f", "#2f6f9f", "#5d8a3a", "#8a4fa0", "#c08a1e", "#3d7d7a")


def _regua_html(cenas, e):
    """Barra de tempo: cada cena com largura proporcional aos segundos, o início e o fim de cada uma,
    as transições entre elas e a duração final (cada transição que não é corte sobrepõe 0,4 s)."""
    if not cenas:
        return ""
    inicio, segs = 0, []
    for i, c in enumerate(cenas):
        d = int(c.get("segundos", 0))
        segs.append(f'<div class="seg" style="flex:{max(d, 1)};background:{CORES_REGUA[i % len(CORES_REGUA)]}">'
                    f'<b>Cena {c["n"]}</b><span>{inicio}–{inicio + d} s</span></div>')
        inicio += d
    trans = [c.get("transicao", "corte") for c in cenas[:-1]]
    final = inicio - TRANSICAO_S * sum(1 for t in trans if t != "corte")
    juncoes = " · ".join(f"{c['n']}→{c['n'] + 1}: {e(t)}" for c, t in zip(cenas, trans)) or "uma cena só"
    final_txt = f"{final:.1f}".replace(".", ",").replace(",0", "") if final != int(final) else str(int(final))
    return (f'<div class="regua">{"".join(segs)}</div>'
            f'<div class="reguaeixo"><span>0 s</span><span>{inicio} s</span></div>'
            f'<p class="transicoes">Transições: {juncoes} · <span class="duracao">Duração final: {final_txt} s</span></p>')


def storyboard(arquivo, etapa=None, abrir=False):
    arquivo = Path(arquivo)
    proj = json.loads(arquivo.read_text(encoding="utf-8"))
    saida = arquivo.with_name("storyboard.html")
    saida.write_text(html_storyboard(proj, arquivo.parent), encoding="utf-8")
    print(f"Storyboard: {saida}")
    if etapa:
        itens = itens_do_projeto(proj, etapa)
        destino = arquivo.with_name(f"itens_{etapa}.json")
        destino.write_text(json.dumps(itens, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Itens do lote ({etapa}): {destino}")
    if abrir:
        if sys.platform == "win32":
            os.startfile(str(saida.resolve()))  # o webbrowser não abriu no Windows (visto em 18/11/2026)
        else:
            import webbrowser
            webbrowser.open(saida.resolve().as_uri())


TIPOS_DO_LOTE = ("imagem", "video")


def _dentro_da_pasta(base, caminho):
    raiz = Path(base).resolve()
    alvo = (raiz / caminho).resolve()
    if alvo != raiz and raiz not in alvo.parents:
        sys.exit(f"Caminho fora da pasta do lote: {caminho}. Use só caminhos dentro de {raiz}. Nada foi gerado.")
    return alvo


def validar_lote(itens, base):
    """Antes de planejar ou gastar: só tipos conhecidos e só caminhos dentro da pasta do JSON."""
    for i in itens:
        if i.get("tipo") not in TIPOS_DO_LOTE:
            sys.exit(f"Item com tipo inválido ({i.get('tipo')!r}): use \"imagem\" ou \"video\". Nada foi gerado.")
        _dentro_da_pasta(base, i["saida"])
        for r in i.get("referencias", []) + i.get("imagens", []) + ([i["imagem"]] if i.get("imagem") else []):
            _dentro_da_pasta(base, r)


def plano_do_lote(itens, base):
    """Itens ainda não gerados (a saída não existe) e o custo em créditos dos vídeos. Item já gerado que só
    falta baixar (marcador) não conta de novo."""
    validar_lote(itens, base)
    faltam = [i for i in itens if not (Path(base) / i["saida"]).exists()]
    custo = 0
    for i in faltam:
        if i["tipo"] != "video":
            continue
        if ler_marcador(Path(base) / i["saida"]):
            continue
        c = custo_conhecido(int(i["segundos"]))
        if c is None:
            if i.get("max") is None:
                sys.exit(f"{i['saida']}: custo desconhecido ({i['segundos']} s). "
                         "Ponha 'max' no item (teto aprovado). Nada foi gasto.")
            c = int(i["max"])
        custo += c
        if i.get("baixar") == "1080p":
            custo += CUSTO_1080P
    return faltam, custo


def lote(arquivo, confirmo=False, maximo_total=None):
    """Gera tudo o que está em `arquivo` (JSON: lista de {tipo, prompt, saida, imagem(ns), referencias, segundos, formato}).
    Caminhos relativos são relativos à pasta do JSON. Pula o que já existe e para na primeira falha."""
    arquivo = Path(arquivo)
    base = arquivo.parent
    faltam, custo = plano_do_lote(json.loads(arquivo.read_text(encoding="utf-8")), base)
    if not faltam:
        print("Nada para gerar: todas as saídas já existem.")
        return
    videos = [i for i in faltam if i["tipo"] == "video"]
    print(f"{len(faltam)} itens ({len(videos)} vídeos, {custo} créditos no total).")
    if videos:
        if not confirmo:
            sys.exit("Gasto não confirmado. Rode de novo com --confirmo depois de a pessoa aprovar o custo.")
        if maximo_total is not None and custo > maximo_total:
            sys.exit(f"O lote custa {custo}, acima do combinado ({maximo_total}). Nada foi gasto.")
    feitos = []
    for i in faltam:
        nome = i["saida"]
        try:
            formato = formato_padrao(i.get("formato"))
            if i["tipo"] == "imagem":
                gerar_imagem(i["prompt"], base / nome, [base / r for r in i.get("referencias", [])], formato)
            elif i["tipo"] == "video":
                imgs = i.get("imagens") or ([i["imagem"]] if i.get("imagem") else [])
                gerar_video(i["prompt"], [base / x for x in imgs], base / nome, int(i["segundos"]), True,
                            maximo=i.get("max"), formato=formato, baixar=i.get("baixar"))
            feitos.append(nome)
        except SystemExit as e:
            ficou = [x["saida"] for x in faltam if x["saida"] not in feitos]
            sys.exit(f"Parou em {nome}: {e}. Prontos: {feitos or 'nenhum'}. Faltam: {ficou}.")
    print(f"Lote pronto: {feitos}")


def verificar():
    """Confere o que a instalação precisa e diz o que falta, em linguagem simples."""
    ok = True
    try:
        import playwright  # noqa: F401
        print("OK  Playwright instalado.")
    except ImportError:
        ok = False
        print("FALTA  Playwright. Instale com: pip install playwright (não precisa baixar navegador).")
    try:
        print(f"OK  Chrome: {achar_chrome()}")
    except SystemExit as e:
        ok = False
        print(f"FALTA  {e}")
    try:
        import imageio_ffmpeg  # noqa: F401
        print("OK  ffmpeg para juntar vídeos (imageio-ffmpeg).")
    except ImportError:
        if shutil.which("ffmpeg"):
            print("OK  ffmpeg para juntar vídeos (do sistema).")
        else:
            print("OPCIONAL  ffmpeg, só para juntar vídeos: pip install imageio-ffmpeg")
    logadas = contas_com_login()
    if logadas:
        print(f"OK  Conta(s) com login salvo: {logadas}. Pasta: {CONFIG}")
    else:
        ok = False
        print("FALTA  Login. Rode: python flow.py login (entre na sua conta Google na janela que abrir).")
    sys.exit(0 if ok else 1)


def _argumentos(argv):
    import argparse
    ap = argparse.ArgumentParser(prog="flow.py", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("verificar")
    s = sub.add_parser("login")
    s.add_argument("conta", nargs="?", type=int, default=1)
    sub.add_parser("saldo")
    s = sub.add_parser("mapear")
    s.add_argument("arquivo", nargs="?")
    for nome in ("imagem", "video"):
        s = sub.add_parser(nome)
        s.add_argument("--prompt")
        s.add_argument("--prompt-arquivo")
        s.add_argument("--saida", required=True)
        s.add_argument("--formato")
        if nome == "imagem":
            s.add_argument("--ref", action="append", default=[])
        else:
            s.add_argument("--imagem", action="append", default=[])
            s.add_argument("--baixar", choices=("720p", "1080p"))
            s.add_argument("--segundos", type=int, required=True)
            s.add_argument("--confirmo", action="store_true")
            s.add_argument("--max", type=int)
            s.add_argument("--frames", action="store_true")
    sub.add_parser("fechar")
    s = sub.add_parser("opcoes")
    s.add_argument("segundos", type=int)
    s.add_argument("--1080p", dest="hd", action="store_true")
    s = sub.add_parser("gastos")
    s.add_argument("--dias", type=int)
    s = sub.add_parser("storyboard")
    s.add_argument("projeto")
    s.add_argument("--itens", choices=("imagens", "videos"))
    s.add_argument("--abrir", action="store_true")
    s = sub.add_parser("juntar")
    s.add_argument("entradas", nargs="+")
    s.add_argument("--saida", required=True)
    s.add_argument("--transicao", default="corte",
                   help="uma para todas ou uma por junção (corte,esmaecer-preto,...): corte, suave, esmaecer-preto, "
                        "esmaecer-branco, deslizar-esquerda, deslizar-direita, aproximar, afastar")
    s.add_argument("--musica")
    s.add_argument("--volume-musica", type=float, default=0.15)
    s.add_argument("--formato")
    s = sub.add_parser("ampliar")
    s.add_argument("midia")
    s.add_argument("--saida", required=True)
    s.add_argument("--confirmo", action="store_true")
    s.add_argument("--max", type=int)
    s = sub.add_parser("preferencias")
    for campo in OPCOES_PREF:
        s.add_argument(f"--{campo}")
    s = sub.add_parser("lote")
    s.add_argument("arquivo")
    s.add_argument("--confirmo", action="store_true")
    s.add_argument("--max", type=int)
    return ap.parse_args(argv)


def main(argv=None):
    a = _argumentos(sys.argv[1:] if argv is None else argv)
    if a.cmd == "verificar":
        verificar()
    elif a.cmd == "login":
        login(a.conta)
    elif a.cmd == "saldo":
        saldo()
    elif a.cmd == "mapear":
        mapear(a.arquivo)
    elif a.cmd == "preferencias":
        novas = {c: getattr(a, c) for c in OPCOES_PREF if getattr(a, c)}
        if novas:
            salvar_preferencias(novas)
        prefs = ler_preferencias()
        print(json.dumps(prefs, ensure_ascii=False, indent=2) if prefs else
              "Sem preferências salvas. Faça as perguntas iniciais (SKILL.md) e salve com: python flow.py preferencias --formato 9:16 --download 720p")
    elif a.cmd == "imagem":
        print(f"Imagem salva em {gerar_imagem(_ler_prompt(a.prompt, a.prompt_arquivo), a.saida, a.ref, formato_padrao(a.formato))}")
    elif a.cmd == "video":
        destino = gerar_video(_ler_prompt(a.prompt, a.prompt_arquivo), a.imagem, a.saida, a.segundos, a.confirmo, a.max,
                              "frames" if a.frames else "elementos", formato_padrao(a.formato), a.baixar)
        print(f"Clipe salvo em {destino}")
    elif a.cmd == "opcoes":
        print(texto_opcoes(a.segundos, a.hd))
    elif a.cmd == "gastos":
        mostrar_gastos(a.dias)
    elif a.cmd == "storyboard":
        storyboard(a.projeto, a.itens, a.abrir)
    elif a.cmd == "juntar":
        juntar(a.entradas, a.saida, a.transicao, a.musica, a.volume_musica, a.formato)
    elif a.cmd == "fechar":
        for n in contas_com_login():
            usar(n)
            _fechar_chrome_da_conta()
        print("Janela(s) do robô fechada(s). O login continua salvo.")
    elif a.cmd == "ampliar":
        ampliar(a.midia, a.saida, a.confirmo, a.max)
    elif a.cmd == "lote":
        lote(a.arquivo, a.confirmo, a.max)


if __name__ == "__main__":
    main()
