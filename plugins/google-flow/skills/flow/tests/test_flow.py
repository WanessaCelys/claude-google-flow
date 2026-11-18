"""Testes do núcleo da skill flow (só lógica pura: nada abre o Chrome nem gasta crédito)."""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import flow as F  # noqa: E402


@pytest.fixture(autouse=True)
def sem_navegador(monkeypatch, tmp_path):
    """Nenhum teste pode abrir o Chrome nem usar a pasta real de login: se algum código chegar
    até o navegador, o teste falha na hora (sem gerar nada, sem gastar crédito)."""
    def proibido(*a, **k):
        raise AssertionError("o teste tentou abrir o Chrome")
    monkeypatch.setattr(F, "_abrir", proibido)
    monkeypatch.setattr(F, "_abrir_chrome", proibido)
    monkeypatch.setattr(F, "CONFIG", tmp_path / "flow-config")


def test_custo_por_duracao_e_modelo(monkeypatch):
    monkeypatch.delenv("FLOW_OMNI", raising=False)
    assert (F.custo_video(8), F.custo_video(10)) == (12, 15)  # Omni 1.1
    assert (F.custo_video(12), F.custo_video(15)) == (42, 60)  # Omni 1.2
    assert F.custo_video(8, "1.2") == 24


def test_duracao_fora_da_tabela_nao_chuta():
    with pytest.raises(SystemExit) as e:
        F.custo_video(14)
    assert "14" in str(e.value)


def test_modelo_pela_duracao_e_pela_variavel(monkeypatch):
    monkeypatch.delenv("FLOW_OMNI", raising=False)
    assert F.modelo_omni(10) == "1.1" and F.modelo_omni(11) == "1.2"
    monkeypatch.setenv("FLOW_OMNI", "1.2")
    assert F.modelo_omni(8) == "1.2"


def test_opcoes_de_video_levam_formato_e_barra_no_1_2(monkeypatch):
    monkeypatch.delenv("FLOW_OMNI", raising=False)
    assert F.opcoes_video(10, formato="16:9")[-2] == "duracao"
    assert F.SELETORES["formato"] == "16:9"
    assert F.opcoes_video(15)[-2] == "duracao_barra"


def test_trava_de_gasto():
    with pytest.raises(SystemExit):
        F.conferir_gasto(saldo=7, custo=15)
    with pytest.raises(SystemExit):
        F.conferir_gasto(saldo=None, custo=15)
    assert F.conferir_gasto(saldo=52, custo=15) == 37


def test_video_sem_confirmacao_nao_gasta():
    with pytest.raises(SystemExit) as e:
        F.gerar_video("p", ["i.jpg"], "s.mp4", 8, confirmo=False)
    assert "--confirmo" in str(e.value)


def test_plano_do_lote_pula_o_que_existe_e_soma_so_videos(tmp_path, monkeypatch):
    monkeypatch.delenv("FLOW_OMNI", raising=False)
    (tmp_path / "pronta.jpg").write_bytes(b"x")
    itens = [
        {"tipo": "imagem", "prompt": "a", "saida": "pronta.jpg"},
        {"tipo": "imagem", "prompt": "b", "saida": "nova.jpg"},
        {"tipo": "video", "prompt": "c", "saida": "c.mp4", "imagem": "nova.jpg", "segundos": 8},
        {"tipo": "video", "prompt": "d", "saida": "d.mp4", "imagem": "nova.jpg", "segundos": 15},
    ]
    faltam, custo = F.plano_do_lote(itens, tmp_path)
    assert [i["saida"] for i in faltam] == ["nova.jpg", "c.mp4", "d.mp4"]
    assert custo == 12 + 60


def test_lote_de_video_exige_confirmacao(tmp_path):
    arq = tmp_path / "itens.json"
    arq.write_text(json.dumps([{"tipo": "video", "prompt": "p", "saida": "v.mp4", "imagem": "i.jpg", "segundos": 8}]))
    with pytest.raises(SystemExit) as e:
        F.lote(arq, confirmo=False)
    assert "--confirmo" in str(e.value)


def test_lote_acima_do_limite_nao_gasta(tmp_path):
    arq = tmp_path / "itens.json"
    arq.write_text(json.dumps([{"tipo": "video", "prompt": "p", "saida": "v.mp4", "imagem": "i.jpg", "segundos": 15}]))
    with pytest.raises(SystemExit) as e:
        F.lote(arq, confirmo=True, maximo_total=20)
    assert "60" in str(e.value)


def test_pasta_de_perfis_pela_variavel(monkeypatch, tmp_path):
    monkeypatch.setenv("FLOW_HOME", str(tmp_path))
    assert F._pasta_de_perfis() == tmp_path


def test_pasta_padrao_e_config_flow(monkeypatch):
    monkeypatch.delenv("FLOW_HOME", raising=False)
    assert F._pasta_de_perfis() == Path.home() / ".config" / "flow"


def test_chrome_pela_variavel(monkeypatch):
    monkeypatch.setenv("FLOW_CHROME", "/meu/chrome")
    assert F.achar_chrome() == "/meu/chrome"


def test_pedido_sem_prompt_para():
    with pytest.raises(SystemExit):
        F._ler_prompt(None, None)


def test_argumentos_do_video():
    a = F._argumentos(["video", "--prompt", "x", "--imagem", "a.jpg", "--imagem", "b.jpg", "--saida", "s.mp4",
                       "--segundos", "15", "--confirmo", "--formato", "16:9"])
    assert (a.imagem, a.segundos, a.confirmo, a.formato) == (["a.jpg", "b.jpg"], 15, True, "16:9")


# ---------- versão compartilhável: durações novas, vídeo só com texto, preferências ----------

def test_duracoes_curtas_do_omni_1_1(monkeypatch):
    monkeypatch.delenv("FLOW_OMNI", raising=False)
    assert (F.custo_video(4), F.custo_video(6)) == (7, 10)


def test_custo_conhecido_so_da_tabela(monkeypatch):
    monkeypatch.delenv("FLOW_OMNI", raising=False)
    assert F.custo_conhecido(10) == 15
    assert F.custo_conhecido(14) is None  # duração fora da tabela: o Flow diz o preço e vale o --max


def test_video_sempre_em_720p(monkeypatch):
    monkeypatch.delenv("FLOW_OMNI", raising=False)
    F.opcoes_video(8)
    assert F.SELETORES["resolucao"] == "720p"
    assert not hasattr(F, "RESOLUCOES")


def test_custo_desconhecido_exige_teto():
    with pytest.raises(SystemExit) as e:
        F.gerar_video("p", [], "s.mp4", 14, confirmo=True, maximo=None)
    assert "--max" in str(e.value)


def test_conferir_custo_pelo_teto():
    assert F.conferir_custo_menu(7, None, teto=8) == 7
    with pytest.raises(SystemExit):
        F.conferir_custo_menu(9, None, teto=8)
    with pytest.raises(SystemExit):
        F.conferir_custo_menu(None, None, teto=8)


def test_video_so_com_texto_nos_argumentos():
    a = F._argumentos(["video", "--prompt", "x", "--saida", "s.mp4", "--segundos", "8", "--confirmo"])
    assert a.imagem == []
    with pytest.raises(SystemExit):  # não existe mais escolha de resolução na geração
        F._argumentos(["video", "--prompt", "x", "--saida", "s.mp4", "--segundos", "8", "--resolucao", "360p"])


def test_preferencias_salvar_e_ler(monkeypatch, tmp_path):
    monkeypatch.setattr(F, "CONFIG", tmp_path)
    assert F.ler_preferencias() == {}
    F.salvar_preferencias({"formato": "16:9", "download": "720p"})
    assert F.ler_preferencias()["formato"] == "16:9"
    F.salvar_preferencias({"download": "1080p"})  # só muda o que veio
    p = F.ler_preferencias()
    assert (p["download"], p["formato"]) == ("1080p", "16:9")


def test_formato_padrao_vem_das_preferencias(monkeypatch, tmp_path):
    monkeypatch.setattr(F, "CONFIG", tmp_path)
    assert F.formato_padrao(None) == "9:16"
    F.salvar_preferencias({"formato": "16:9"})
    assert F.formato_padrao(None) == "16:9"
    assert F.formato_padrao("1:1") == "1:1"
    F.salvar_preferencias({"formato": "depende"})
    assert F.formato_padrao(None) == "9:16"


def test_preferencia_invalida_e_recusada(monkeypatch, tmp_path):
    monkeypatch.setattr(F, "CONFIG", tmp_path)
    with pytest.raises(SystemExit):
        F.salvar_preferencias({"download": "4K"})
    with pytest.raises(SystemExit):  # estilo, idioma, música e legendas ficam no prompt da pessoa
        F.salvar_preferencias({"estilo": "natural"})


def test_preferencia_de_download_1080p(monkeypatch, tmp_path):
    monkeypatch.setattr(F, "CONFIG", tmp_path)
    F.salvar_preferencias({"download": "1080p"})
    assert F.ler_preferencias()["download"] == "1080p"
    assert F.CUSTO_1080P == 5
    with pytest.raises(SystemExit):
        F.salvar_preferencias({"download": "4K"})


# ---------- download em 1080p (versão ampliada do Flow) ----------

def test_le_o_preco_do_1080p_no_menu():
    assert F.ler_custo_1080p("1080p Resolução ampliada · 5 créditos") == 5
    assert F.ler_custo_1080p("1080p Resolução ampliada · 8 créditos") == 8
    assert F.ler_custo_1080p("1080p") is None


def test_preco_do_1080p_diferente_para():
    assert F.conferir_custo_1080p(5) == 5
    with pytest.raises(SystemExit):
        F.conferir_custo_1080p(8)
    with pytest.raises(SystemExit):
        F.conferir_custo_1080p(None)


def test_acha_o_1080p_baixado_na_pasta(tmp_path):
    import os
    import time
    velho = tmp_path / "antigo_1080p.mp4"
    velho.write_bytes(b"x" * 10)
    os.utime(velho, (time.time() - 3600, time.time() - 3600))
    inicio = time.time() - 1
    assert F.achar_1080p_baixado(tmp_path, inicio) is None
    (tmp_path / "video_abc_1080p.mp4.crdownload").write_bytes(b"x")  # ainda baixando: ignora
    assert F.achar_1080p_baixado(tmp_path, inicio) is None
    novo = tmp_path / "video_abc_1080p.mp4"
    novo.write_bytes(b"x" * 10)
    assert F.achar_1080p_baixado(tmp_path, inicio) == novo


def test_nome_da_saida_1080p():
    assert F.saida_1080p("pasta/cena01.mp4") == Path("pasta/cena01_1080p.mp4")


def test_lote_soma_o_1080p(tmp_path, monkeypatch):
    monkeypatch.delenv("FLOW_OMNI", raising=False)
    itens = [{"tipo": "video", "prompt": "c", "saida": "c.mp4", "imagem": "i.jpg", "segundos": 8, "baixar": "1080p"},
             {"tipo": "video", "prompt": "d", "saida": "d.mp4", "imagem": "i.jpg", "segundos": 8}]
    faltam, custo = F.plano_do_lote(itens, tmp_path)
    assert custo == 12 + 5 + 12


def test_argumentos_do_1080p():
    a = F._argumentos(["video", "--prompt", "x", "--saida", "s.mp4", "--segundos", "8", "--confirmo", "--baixar", "1080p"])
    assert a.baixar == "1080p"
    b = F._argumentos(["ampliar", "https://flow.google.com/project/p/edit/m", "--saida", "s_1080p.mp4", "--confirmo"])
    assert (b.midia, b.saida, b.confirmo) == ("https://flow.google.com/project/p/edit/m", "s_1080p.mp4", True)


def test_ampliar_sem_confirmacao_nao_gasta():
    with pytest.raises(SystemExit) as e:
        F.ampliar("https://flow.google.com/project/p/edit/m", "s.mp4", confirmo=False)
    assert "--confirmo" in str(e.value)


# ---------- imagem em tamanho original (desde 17/11/2026 a grade só entrega miniatura WebP) ----------

def test_escolhe_a_imagem_principal_pela_area_na_tela():
    imagens = [
        {"src": "faixa1", "w": 896, "h": 1200, "area": 60 * 80},      # miniatura da faixa: arquivo grande, tela pequena
        {"src": "principal", "w": 768, "h": 1376, "area": 500 * 900},  # a imagem aberta
        {"src": "icone", "w": 64, "h": 64, "area": 900 * 900},         # pequena demais para ser a imagem
    ]
    assert F.escolher_imagem_principal(imagens) == "principal"
    assert F.escolher_imagem_principal([]) is None


# ---------- correções da auditoria de segurança (17/11/2026) ----------

def test_lote_recusa_tipo_desconhecido(tmp_path):
    for tipo in ("Video", "vídeo", "image", ""):
        with pytest.raises(SystemExit) as e:
            F.plano_do_lote([{"tipo": tipo, "prompt": "p", "saida": "x.mp4", "imagem": "i.jpg", "segundos": 8}], tmp_path)
        assert "tipo" in str(e.value)


def test_lote_recusa_caminho_fora_da_pasta(tmp_path):
    for item in ({"tipo": "imagem", "prompt": "p", "saida": "../fora.jpg"},
                 {"tipo": "imagem", "prompt": "p", "saida": str(tmp_path.parent / "abs.jpg")},
                 {"tipo": "imagem", "prompt": "p", "saida": "ok.jpg", "referencias": ["../../segredo.jpg"]},
                 {"tipo": "video", "prompt": "p", "saida": "ok.mp4", "imagem": "/etc/passwd", "segundos": 8}):
        with pytest.raises(SystemExit) as e:
            F.plano_do_lote([item], tmp_path)
        assert "fora da pasta" in str(e.value)


def test_max_inclui_os_5_do_1080p(monkeypatch):
    monkeypatch.delenv("FLOW_OMNI", raising=False)
    with pytest.raises(SystemExit) as e:  # 12 + 5 = 17 > 12
        F.gerar_video("p", [], "nao_existe.mp4", 8, confirmo=True, maximo=12, baixar="1080p")
    assert "17" in str(e.value) and "limite" in str(e.value)
    with pytest.raises(SystemExit):  # duração desconhecida: o teto precisa sobrar depois dos 5 do 1080p
        F.gerar_video("p", [], "nao_existe.mp4", 14, confirmo=True, maximo=5, baixar="1080p")


def test_marcador_de_gerado_nao_cobra_de_novo(tmp_path, monkeypatch):
    monkeypatch.delenv("FLOW_OMNI", raising=False)
    F.marcador(tmp_path / "v.mp4").write_text('{"nome": "Clipe X", "conta": 1}', encoding="utf-8")
    itens = [{"tipo": "video", "prompt": "p", "saida": "v.mp4", "imagem": "i.jpg", "segundos": 8},
             {"tipo": "video", "prompt": "p", "saida": "w.mp4", "imagem": "i.jpg", "segundos": 8}]
    faltam, custo = F.plano_do_lote(itens, tmp_path)
    assert [i["saida"] for i in faltam] == ["v.mp4", "w.mp4"] and custo == 12  # v.mp4 só falta baixar


def test_nao_sobrescreve_saida(tmp_path):
    existe = tmp_path / "ja.jpg"
    existe.write_bytes(b"x")
    with pytest.raises(SystemExit) as e:
        F.gerar_imagem("p", existe)
    assert "já existe" in str(e.value)
    v = tmp_path / "ja.mp4"
    v.write_bytes(b"x")
    with pytest.raises(SystemExit):
        F.gerar_video("p", [], v, 8, confirmo=True)


def test_ampliar_so_aceita_link_do_flow():
    for link in ("https://exemplo.com/x", "http://flow.google.com/project/p/edit/m", "file:///c:/x"):
        with pytest.raises(SystemExit) as e:
            F.ampliar(link, "s.mp4", confirmo=True)
        assert "flow.google.com" in str(e.value)


def test_fechar_chrome_so_da_conta_certa():
    import re
    p1 = F.padrao_perfil(r"C:\Users\x\.config\flow\flow-perfil")
    assert re.search(p1, r'chrome.exe --remote-debugging-port=9333 --user-data-dir=C:\Users\x\.config\flow\flow-perfil --no-first-run')
    assert re.search(p1, r'chrome.exe "--user-data-dir=C:\Users\x\.config\flow\flow-perfil" x')
    assert not re.search(p1, r'chrome.exe --user-data-dir=C:\Users\x\.config\flow\flow-perfil-2 --no-first-run')


# ---------- juntar os vídeos (ffmpeg, sem crédito) ----------

def test_juntar_com_corte_usa_concat_e_normaliza_o_formato():
    cmd = F.comando_juntar("ffmpeg", ["a.mp4", "b.mp4", "c.mp4"], "f.mp4", duracoes=[8, 8, 8],
                           com_audio=[True, True, True], formato="9:16")
    filtro = cmd[cmd.index("-filter_complex") + 1]
    assert "concat=n=3:v=1:a=1" in filtro and "scale=720:1280" in filtro and "fps=30" in filtro
    assert cmd[-1] == "f.mp4" and "libx264" in cmd
    assert cmd[cmd.index("-pix_fmt") + 1] == "yuv420p"  # yuv444p não abre em celular nem no WhatsApp


def test_juntar_suave_calcula_os_pontos_da_transicao():
    cmd = F.comando_juntar("ffmpeg", ["a.mp4", "b.mp4", "c.mp4"], "f.mp4", duracoes=[8, 8, 8],
                           com_audio=[True, True, True], transicao="suave", formato="16:9")
    filtro = cmd[cmd.index("-filter_complex") + 1]
    assert "xfade=transition=fade:duration=0.4:offset=7.6" in filtro
    assert "offset=15.2" in filtro and "acrossfade=d=0.4" in filtro and "scale=1280:720" in filtro


def test_juntar_clipe_sem_som_ganha_silencio():
    cmd = F.comando_juntar("ffmpeg", ["a.mp4", "b.mp4"], "f.mp4", duracoes=[8, 6], com_audio=[True, False])
    filtro = cmd[cmd.index("-filter_complex") + 1]
    assert "anullsrc" in filtro and "atrim=duration=6" in filtro


def test_juntar_com_musica_de_fundo():
    cmd = F.comando_juntar("ffmpeg", ["a.mp4", "b.mp4"], "f.mp4", duracoes=[8, 8], com_audio=[True, True],
                           musica="m.mp3", volume_musica=0.2)
    assert cmd[cmd.index("m.mp3") - 3:cmd.index("m.mp3")] == ["-stream_loop", "-1", "-i"]
    filtro = cmd[cmd.index("-filter_complex") + 1]
    assert "volume=0.2" in filtro and "amix=inputs=2:duration=first" in filtro and "normalize=0" in filtro


def test_juntar_recusa_pedido_invalido():
    with pytest.raises(SystemExit):
        F.comando_juntar("ffmpeg", ["a.mp4"], "f.mp4", duracoes=[8], com_audio=[True])
    with pytest.raises(SystemExit):
        F.comando_juntar("ffmpeg", ["a.mp4", "b.mp4"], "f.mp4", duracoes=[8, 8], com_audio=[True, True], transicao="explosao")


def test_le_duracao_e_audio_do_ffmpeg():
    saida = ("Input #0, mov,mp4,m4a, from 'a.mp4':\n  Duration: 00:00:08.04, start: 0.000000, bitrate: 1840 kb/s\n"
             "  Stream #0:0[0x1](und): Video: h264\n  Stream #0:1[0x2](und): Audio: aac (LC), 48000 Hz, stereo\n")
    assert F.ler_info_ffmpeg(saida) == (8.04, True)
    assert F.ler_info_ffmpeg("  Duration: 00:01:02.50, start\n  Stream #0:0: Video: h264\n") == (62.5, False)


# ---------- transição por junção e storyboard visual ----------

def test_juntar_com_transicao_diferente_em_cada_juncao():
    cmd = F.comando_juntar("ffmpeg", ["a.mp4", "b.mp4", "c.mp4", "d.mp4"], "f.mp4", duracoes=[4, 6, 8, 6],
                           com_audio=[True] * 4, transicao=["corte", "deslizar", "suave"])
    filtro = cmd[cmd.index("-filter_complex") + 1]
    assert "concat=n=2:v=1:a=1" in filtro                                   # a→b: corte seco (10 s juntos)
    assert "settb=1/30" in filtro  # depois do corte, volta à régua de tempo de 30 q/s (senão o xfade seguinte falha)
    assert "xfade=transition=slideleft:duration=0.4:offset=9.6" in filtro  # b→c: desliza no fim dos 10 s
    assert "xfade=transition=fade:duration=0.4:offset=17.2" in filtro      # c→d: 10 + 8 - 0,4 - 0,4
    with pytest.raises(SystemExit):  # tem que ter uma transição por junção
        F.comando_juntar("ffmpeg", ["a.mp4", "b.mp4", "c.mp4"], "f.mp4", duracoes=[4, 4, 4], com_audio=[True] * 3,
                         transicao=["corte"])


PROJETO = {
    "titulo": "Teste", "formato": "9:16", "estilo": "natural", "idioma": "pt-BR", "musica": "sem", "legendas": "sem",
    "download": "720p", "saldo": 20,
    "cenas": [
        {"descricao": "Ela chega", "fala": "Oi!", "segundos": 4, "prompt_imagem": "img1", "prompt_video": "vid1",
         "referencias": ["ref/fachada.png"], "transicao": "corte"},
        {"descricao": "Ela entra", "fala": "", "segundos": 8, "prompt_imagem": "img2", "prompt_video": "vid2",
         "referencias": ["cena01.jpg"], "baixar": "1080p"},
    ],
}


def test_storyboard_calcula_custos_e_avisa_saldo():
    resumo = F.resumo_do_projeto(PROJETO)
    assert [c["creditos"] for c in resumo["cenas"]] == [7, 17]  # 7 | 12 + 5 do 1080p
    assert resumo["total"] == 24 and resumo["falta"] == 4 and resumo["duracao"] == 12


def test_storyboard_html_tem_tabela_prompts_e_pergunta(tmp_path):
    html = F.html_storyboard(PROJETO, tmp_path)
    assert "Teste" in html and "img1" in html and "vid2" in html and "Faltam 4" in html
    assert "imagem ainda não gerada" in html  # cena sem imagem ainda
    (tmp_path / "cena01.jpg").write_bytes(b"x")
    assert 'src="cena01.jpg"' in F.html_storyboard(PROJETO, tmp_path)


def test_storyboard_gera_os_itens_do_lote_por_etapa():
    imgs = F.itens_do_projeto(PROJETO, "imagens")
    assert [i["saida"] for i in imgs] == ["cena01.jpg", "cena02.jpg"] and imgs[1]["referencias"] == ["cena01.jpg"]
    vids = F.itens_do_projeto(PROJETO, "videos")
    assert [(v["saida"], v["imagem"], v["segundos"]) for v in vids] == [("cena01.mp4", "cena01.jpg", 4), ("cena02.mp4", "cena02.jpg", 8)]
    assert vids[1]["baixar"] == "1080p" and "baixar" not in vids[0]


def test_imagem_usa_a_conta_escolhida(monkeypatch):
    monkeypatch.setattr(F, "contas_com_login", lambda: [3, 1])
    F.usar(1)
    with pytest.raises(AssertionError):  # o teste para quando o robô tenta abrir o Chrome
        F.gerar_imagem("p", "nao_existe_ainda.jpg")
    assert F.ATUAL == 3


def test_video_com_mais_de_uma_imagem_de_referencia():
    proj = {"cenas": [{"segundos": 10, "prompt_imagem": "x", "prompt_video": "v", "imagens_extra": ["ref_loja.jpg"]}]}
    v = F.itens_do_projeto(proj, "videos")[0]
    assert v["imagens"] == ["cena01.jpg", "ref_loja.jpg"] and "imagem" not in v


def test_juntar_usa_so_um_trecho_do_video():
    assert F.ler_trecho("cena01.mp4@0-6") == ("cena01.mp4", 0.0, 6.0)
    assert F.ler_trecho(r"C:\pasta\cena01.mp4") == (r"C:\pasta\cena01.mp4", None, None)
    with pytest.raises(SystemExit):
        F.ler_trecho("cena01.mp4@6-2")
    cmd = F.comando_juntar("ffmpeg", ["a.mp4@0-6", "b.mp4"], "f.mp4", duracoes=[6, 8], com_audio=[True, True])
    i = cmd.index("a.mp4")
    assert cmd[i - 5:i] == ["-ss", "0", "-to", "6", "-i"] and cmd[cmd.index("b.mp4") - 1] == "-i"


def test_juntar_de_verdade_com_corte_e_transicao(tmp_path):
    """Roda o ffmpeg de verdade (sem Flow, sem crédito) com corte seco seguido de transição e um trecho."""
    import subprocess
    try:
        ff = F.achar_ffmpeg()
    except SystemExit:
        pytest.skip("ffmpeg não instalado")
    clipes = []
    for i, cor in enumerate(("red", "green", "blue")):
        c = tmp_path / f"c{i}.mp4"
        subprocess.run([ff, "-v", "error", "-y", "-f", "lavfi", "-i", f"color=c={cor}:s=360x640:d=1.5:r=24",
                        "-f", "lavfi", "-i", "sine=frequency=440:duration=1.5", "-shortest", "-c:v", "libx264",
                        "-pix_fmt", "yuv420p", "-c:a", "aac", str(c)], check=True)
        clipes.append(str(c))
    final = tmp_path / "final.mp4"
    F.juntar([clipes[0] + "@0-1", clipes[1], clipes[2]], str(final), transicao="corte,deslizar", formato="9:16")
    assert final.exists() and final.stat().st_size > 1000


def test_duas_midias_novas_ao_mesmo_tempo_nao_adivinha():
    from collections import Counter
    antes = Counter({"Velha": 1})
    tiles = [{"nome": "Couple discussing personal train…", "src": "a"}, {"nome": "Woman pointing at store sign", "src": "b"},
             {"nome": "Velha", "src": "c"}, {"nome": "foto_123.jpg", "src": "d"}]
    assert F.midias_novas(antes, tiles) == ["Couple discussing personal train…", "Woman pointing at store sign"]
    assert F.midias_novas(antes, tiles[1:]) == ["Woman pointing at store sign"]


def test_marcador_com_candidatos_pede_escolha(tmp_path):
    saida = tmp_path / "v.mp4"
    F.marcador(saida).write_text('{"nome": null, "candidatos": ["A", "B"], "conta": 3}', encoding="utf-8")
    with pytest.raises(SystemExit) as e:
        F.conferir_marcador(F.ler_marcador(saida), saida)
    assert "A" in str(e.value) and "B" in str(e.value) and "nome" in str(e.value)


def test_storyboard_mostra_as_referencias_extras(tmp_path):
    (tmp_path / "cena01.jpg").write_bytes(b"x")
    (tmp_path / "logo.png").write_bytes(b"x")
    proj = {"cenas": [{"segundos": 10, "prompt_imagem": "x", "prompt_video": "v", "imagens_extra": ["logo.png"]}]}
    html = F.html_storyboard(proj, tmp_path)
    assert 'src="logo.png"' in html and "Referências" in html


# ---------- registro de gastos ----------

def test_registra_e_resume_os_gastos():
    F.registrar_gasto("imagem", 1, 0, "a.jpg")
    F.registrar_gasto("video", 3, 15, "v.mp4", saldo_depois=81)
    F.registrar_gasto("1080p", 3, 5, "v_1080p.mp4", saldo_depois=76)
    r = F.resumo_gastos()
    assert r["total"] == 20 and r["por_tipo"] == {"imagem": (1, 0), "video": (1, 15), "1080p": (1, 5)}
    assert r["por_conta"] == {1: 0, 3: 20} and r["ultimo_saldo"] == {3: 76}


def test_resumo_vazio_e_por_periodo():
    assert F.resumo_gastos()["total"] == 0
    F.registrar_gasto("video", 1, 12, "v.mp4")
    assert F.resumo_gastos(dias=1)["total"] == 12


# ---------- opções de duração e custo (antes do storyboard) ----------

def test_opcoes_para_30_segundos(monkeypatch):
    monkeypatch.delenv("FLOW_OMNI", raising=False)
    ops = F.opcoes_de_duracao(30)
    assert ops[0] == {"clipes": [10, 10, 10], "total": 30, "creditos": 45}
    assert {"clipes": [8, 8, 8, 6], "total": 30, "creditos": 46} in ops
    assert {"clipes": [6, 6, 6, 6, 6], "total": 30, "creditos": 50} in ops
    assert all(o["total"] == 30 for o in ops)  # quando dá exato, só mostra o exato


def test_opcoes_quando_nao_da_exato(monkeypatch):
    monkeypatch.delenv("FLOW_OMNI", raising=False)
    ops = F.opcoes_de_duracao(25)  # 25 s não fecha com 4/6/8/10: mostra os mais próximos
    assert ops and all(abs(o["total"] - 25) <= 2 for o in ops)
    assert {o["total"] for o in ops} <= {24, 26}


def test_texto_das_opcoes_mostra_creditos_e_1080p(monkeypatch):
    monkeypatch.delenv("FLOW_OMNI", raising=False)
    texto = F.texto_opcoes(30, com_1080p=True)
    assert "3 vídeos de 10 s" in texto and "45 créditos" in texto and "+15 no 1080p" in texto


def test_storyboard_tem_regua_de_tempo(tmp_path):
    proj = {"titulo": "T", "cenas": [
        {"segundos": 10, "prompt_video": "a", "transicao": "suave", "descricao": "Um"},
        {"segundos": 8, "prompt_video": "b", "transicao": "corte", "descricao": "Dois"},
        {"segundos": 6, "prompt_video": "c", "descricao": "Três"}]}
    html = F.html_storyboard(proj, tmp_path)
    assert 'class="regua"' in html and "0–10 s" in html and "10–18 s" in html and "18–24 s" in html
    assert "Duração final: 23,6 s" in html          # 24 s menos 0,4 s da transição suave


def test_transicoes_classicas():
    for nome, efeito in [("esmaecer-preto", "fadeblack"), ("esmaecer-branco", "fadewhite"), ("deslizar-esquerda", "slideleft"),
                         ("deslizar-direita", "slideright"), ("aproximar", "zoomin")]:
        cmd = F.comando_juntar("ffmpeg", ["a.mp4", "b.mp4"], "f.mp4", duracoes=[8, 8], com_audio=[True, True], transicao=nome)
        assert f"xfade=transition={efeito}:" in cmd[cmd.index("-filter_complex") + 1]
    cmd = F.comando_juntar("ffmpeg", ["a.mp4", "b.mp4"], "f.mp4", duracoes=[8, 8], com_audio=[True, True], transicao="afastar")
    filtro = cmd[cmd.index("-filter_complex") + 1]
    assert "xfade=transition=custom" in filtro and "st(" not in filtro  # sem variáveis compartilhadas (dava chuvisco)


def test_juntar_de_verdade_com_afastar_e_esmaecer(tmp_path):
    import subprocess
    try:
        ff = F.achar_ffmpeg()
    except SystemExit:
        pytest.skip("ffmpeg não instalado")
    clipes = []
    for i, cor in enumerate(("red", "green", "blue")):
        c = tmp_path / f"c{i}.mp4"
        subprocess.run([ff, "-v", "error", "-y", "-f", "lavfi", "-i", f"color=c={cor}:s=360x640:d=1.5:r=24",
                        "-f", "lavfi", "-i", "sine=frequency=440:duration=1.5", "-shortest", "-c:v", "libx264",
                        "-pix_fmt", "yuv420p", "-c:a", "aac", str(c)], check=True)
        clipes.append(str(c))
    final = tmp_path / "final.mp4"
    F.juntar(clipes, str(final), transicao="afastar,esmaecer-preto", formato="9:16")
    assert final.exists() and final.stat().st_size > 1000


def test_falha_nova_ignora_falhas_antigas_e_acha_a_nova():
    velha = "Falha Esta geração talvez viole nossas políticas. Não houve cobrança por esta geração."
    assert F.falha_nova([velha], [velha]) is None
    assert F.falha_nova([], []) is None
    assert "viole" in F.falha_nova([velha], [velha, velha])


def test_falha_nova_tira_nomes_de_icones():
    bruto = "warning Falha Esta geração talvez viole nossas políticas. Não houve cobrança por esta geração. refresh undo delete_forever"
    assert F.falha_nova([], [bruto]) == ("Falha Esta geração talvez viole nossas políticas. "
                                         "Não houve cobrança por esta geração")


def _proj_com_personagem():
    return {"titulo": "t", "formato": "9:16", "saldo": 50,
            "personagens": [{"nome": "Ana Luíza", "prompt_imagem": "retrato da Ana", "referencias": []},
                            {"nome": "Dono", "foto": "ref/dono.jpg"}],
            "cenas": [{"descricao": "a", "segundos": 10, "prompt_imagem": "cena com Ana",
                       "referencias": ["personagem_ana_luiza.jpg"], "prompt_video": "v"}]}


def test_personagem_gerado_vem_antes_das_cenas_e_foto_real_nao_gera():
    proj = _proj_com_personagem()
    so_retratos = F.itens_do_projeto(proj, "personagens")
    assert [i["saida"] for i in so_retratos] == ["personagem_ana_luiza.jpg"]
    imagens = F.itens_do_projeto(proj, "imagens")
    assert [i["saida"] for i in imagens] == ["personagem_ana_luiza.jpg", "cena01.jpg"]
    assert all(i["saida"] != "ref/dono.jpg" for i in imagens)
    assert [i["saida"] for i in F.itens_do_projeto(proj, "videos")] == ["cena01.mp4"]


def test_personagem_sem_foto_nem_prompt_para():
    proj = _proj_com_personagem()
    proj["personagens"] = [{"nome": "X"}]
    with pytest.raises(SystemExit):
        F.itens_do_projeto(proj, "personagens")


def test_storyboard_mostra_personagem_e_pede_retrato_primeiro(tmp_path):
    pagina = F.html_storyboard(_proj_com_personagem(), tmp_path)
    assert "<section class=personagens>" in pagina and pagina.count("<article class=personagem>") == 2
    assert "Ana Luíza" in pagina and "Dono" in pagina and "rgba(250,190,140,.8)" in pagina
    assert "imagem de Ana Luíza" in pagina and "Posso gerar as" not in pagina
    (tmp_path / "personagem_ana_luiza.jpg").write_bytes(b"x")
    assert "Posso gerar as 1 imagens" in F.html_storyboard(_proj_com_personagem(), tmp_path)


def test_projeto_sem_personagens_continua_igual(tmp_path):
    proj = _proj_com_personagem(); proj.pop("personagens")
    assert [i["saida"] for i in F.itens_do_projeto(proj, "imagens")] == ["cena01.jpg"]
    assert "Personagem ·" not in F.html_storyboard(proj, tmp_path)
    proj["cenas"][0]["referencias"] = []  # sem nenhuma imagem enviada, sem bloco de referências
    assert "<section class=personagens>" not in F.html_storyboard(proj, tmp_path)


def test_copia_de_referencia_e_recusada_mas_imagem_nova_nao():
    assert F.eh_copia_de_referencia([1.2])          # mesma imagem recomprimida
    assert not F.eh_copia_de_referencia([35.0])     # imagem nova, mesmo personagem em outro cenário
    assert not F.eh_copia_de_referencia([None, 40])  # referência que não deu para comparar
    assert not F.eh_copia_de_referencia([])


def test_storyboard_tem_assinatura_fixa(tmp_path):
    pagina = F.html_storyboard(_proj_com_personagem(), tmp_path)
    assert "criado por Wanessa Celys" in pagina and "class=assinatura" in pagina
    assert "position:fixed" in pagina and "background:#2b2b2b" in pagina and "Great Vibes" in pagina


def test_recomenda_ate_um_minuto_sem_limitar():
    assert "recomendado é até 60 s" not in F.texto_opcoes(60)
    longo = F.texto_opcoes(90)
    assert "Não há limite" in longo and "até 60 s" in longo
    assert F.opcoes_de_duracao(180)  # vídeo longo continua tendo opções


def test_sem_alteracao_acrescenta_a_frase_no_fim_do_prompt(tmp_path):
    proj = _proj_com_personagem()
    assert F.SEM_ALTERACAO not in F.itens_do_projeto(proj, "imagens")[-1]["prompt"]  # padrão: prompt intacto
    proj["sem_alteracao"] = True
    img = F.itens_do_projeto(proj, "imagens")[-1]["prompt"]
    vid = F.itens_do_projeto(proj, "videos")[0]["prompt"]
    assert img.startswith("cena com Ana") and img.endswith(F.SEM_ALTERACAO)
    assert vid.startswith("v") and vid.endswith(F.SEM_ALTERACAO)
    assert F.SEM_ALTERACAO in F.html_storyboard(proj, tmp_path)  # a pessoa vê o prompt que vai ser usado
    proj["cenas"][0]["sem_alteracao"] = False  # a cena pode desligar
    assert F.SEM_ALTERACAO not in F.itens_do_projeto(proj, "imagens")[-1]["prompt"]


def test_sem_alteracao_nao_repete_a_frase():
    proj = _proj_com_personagem(); proj["sem_alteracao"] = True
    proj["cenas"][0]["prompt_imagem"] += " " + F.SEM_ALTERACAO
    assert F.itens_do_projeto(proj, "imagens")[-1]["prompt"].count(F.SEM_ALTERACAO) == 1


def test_bloco_laranja_tem_todas_as_referencias_enviadas(tmp_path):
    proj = _proj_com_personagem()
    proj["cenas"][0]["referencias"] = ["personagem_ana_luiza.jpg", "ref/fachada.png"]
    proj["cenas"][0]["imagens_extra"] = ["ref/logo.png", "cena02.jpg"]
    proj["cenas"].append({"descricao": "b", "segundos": 10, "prompt_imagem": "x", "referencias": ["ref/fachada.png", "cena01.jpg"]})
    assert F.referencias_enviadas(proj) == ["ref/fachada.png", "ref/logo.png"]  # sem personagem, sem cena gerada, sem repetir
    pagina = F.html_storyboard(proj, tmp_path)
    bloco = pagina.split("<section class=personagens>")[1].split("</section>")[0]
    assert "Personagem · Ana Luíza" in bloco and "ref/fachada.png" in bloco and "ref/logo.png" in bloco
    assert "cena02.jpg" not in bloco


def test_assinatura_vira_link_do_instagram(tmp_path, monkeypatch):
    monkeypatch.setattr(F, "INSTAGRAM", "https://www.instagram.com/exemplo")
    pagina = F.html_storyboard(_proj_com_personagem(), tmp_path)
    assert '<span class=assinatura>criado por Wanessa Celys</span><a class=insta href="https://www.instagram.com/exemplo"' in pagina
    assert "<svg" in pagina
    sem = F.html_storyboard.__globals__  # sem Instagram, sem ícone
    monkeypatch.setattr(F, "INSTAGRAM", "")
    assert "class=insta" not in F.html_storyboard(_proj_com_personagem(), tmp_path)


def test_atividade_incomum_manda_parar_e_nao_mudar_o_pedido():
    m = F.mensagem_de_falha("Falha Notamos uma atividade incomum. As extensões do navegador podem causar problemas")
    assert "Pare de usar o robô" in m and "Mude o pedido" not in m
    assert "Mude o pedido" in F.mensagem_de_falha("Falha Esta geração talvez viole nossas políticas")


def test_regua_so_em_tons_de_laranja_e_tarja_com_assinatura(tmp_path):
    for cor in F.CORES_REGUA:
        r, g, b = (int(cor[i:i + 2], 16) for i in (1, 3, 5))
        assert r > g > b, cor  # laranja: vermelho > verde > azul
    pagina = F.html_storyboard(_proj_com_personagem(), tmp_path)
    assert "<header class=tarja>" in pagina and "position:fixed;top:0" in pagina
