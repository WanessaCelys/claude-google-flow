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
    F.salvar_preferencias({"estilo": "natural", "idioma": "pt-BR", "musica": "depende", "formato": "16:9"})
    assert F.ler_preferencias()["idioma"] == "pt-BR"
    F.salvar_preferencias({"musica": "sem"})  # só muda o que veio
    p = F.ler_preferencias()
    assert (p["musica"], p["estilo"]) == ("sem", "natural")


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
        F.salvar_preferencias({"musica": "talvez"})


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
        F.comando_juntar("ffmpeg", ["a.mp4", "b.mp4"], "f.mp4", duracoes=[8, 8], com_audio=[True, True], transicao="zoom")


def test_le_duracao_e_audio_do_ffmpeg():
    saida = ("Input #0, mov,mp4,m4a, from 'a.mp4':\n  Duration: 00:00:08.04, start: 0.000000, bitrate: 1840 kb/s\n"
             "  Stream #0:0[0x1](und): Video: h264\n  Stream #0:1[0x2](und): Audio: aac (LC), 48000 Hz, stereo\n")
    assert F.ler_info_ffmpeg(saida) == (8.04, True)
    assert F.ler_info_ffmpeg("  Duration: 00:01:02.50, start\n  Stream #0:0: Video: h264\n") == (62.5, False)
