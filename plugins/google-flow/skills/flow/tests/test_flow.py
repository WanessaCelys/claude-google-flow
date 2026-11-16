"""Testes do núcleo da skill flow (só lógica pura: nada abre o Chrome nem gasta crédito)."""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import flow as F  # noqa: E402


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


# ---------- versão compartilhável: durações novas, 360p, vídeo só com texto, preferências ----------

def test_duracoes_curtas_do_omni_1_1(monkeypatch):
    monkeypatch.delenv("FLOW_OMNI", raising=False)
    assert (F.custo_video(4), F.custo_video(6)) == (7, 10)


def test_custo_conhecido_depende_da_resolucao(monkeypatch):
    monkeypatch.delenv("FLOW_OMNI", raising=False)
    assert F.custo_conhecido(10, resolucao="720p") == 15
    assert F.custo_conhecido(10, resolucao="360p") is None  # não está na tabela: o Flow diz o preço e vale o --max


def test_custo_desconhecido_exige_teto():
    with pytest.raises(SystemExit) as e:
        F.gerar_video("p", [], "s.mp4", 10, confirmo=True, maximo=None, resolucao="360p")
    assert "--max" in str(e.value)


def test_conferir_custo_pelo_teto():
    assert F.conferir_custo_menu(7, None, teto=8) == 7
    with pytest.raises(SystemExit):
        F.conferir_custo_menu(9, None, teto=8)
    with pytest.raises(SystemExit):
        F.conferir_custo_menu(None, None, teto=8)


def test_video_so_com_texto_nos_argumentos():
    a = F._argumentos(["video", "--prompt", "x", "--saida", "s.mp4", "--segundos", "8", "--confirmo"])
    assert a.imagem == [] and a.resolucao == "720p"


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
