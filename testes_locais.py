"""Testes locais do agente de notícias.

Não verificam a conexão com o Gemini, o RSS real nem a aparência visual.
Todos os dados abaixo são fictícios, escritos à mão: não são notícias
recuperadas ao vivo.
"""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import logging

import agente_noticias as a
logging.disable(logging.CRITICAL)

NOTICIA = {"id": 1, "titulo": "Titulo de teste", "link": "https://news.google.com/x",
           "fonte": "Fonte de teste", "data": "hoje"}

def estado_novo(noticias=None):
    """Monta um estado de teste. Os dados são fictícios, escritos à mão."""
    dados = {}
    if noticias is not None:
        dados = {
            "consulta": "teste local",
            "coletado_em": "2026-01-01T00:00:00+00:00",
            "noticias": noticias,
            "url_feed": "https://news.google.com/rss/search",
        }
    return {"concluido": False, "cancelado": False, "dados": dados,
            "buscas": 0, "historico": []}

class ComPastaTemporaria(unittest.TestCase):
    """Base: cada teste ganha uma pasta temporária que some no fim."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.pasta = Path(self._tmp.name) / "site"


class TestCriacaoSemNoticias(ComPastaTemporaria):
    ARGS = {"tema": "Teste", "paleta": "delivery"}

    def test_recusa_sem_busca_previa(self):
        estado = estado_novo()
        with self.assertRaises(ValueError) as ctx:
            a.processar_ferramenta("criar_site", self.ARGS, estado, self.pasta)
        self.assertIn("recuperar notícias", str(ctx.exception))
        self.assertFalse(self.pasta.exists())

    def test_recusa_lista_vazia(self):
        estado = estado_novo(noticias=[])
        with self.assertRaises(ValueError) as ctx:
            a.processar_ferramenta("criar_site", self.ARGS, estado, self.pasta)
        self.assertIn("recuperar notícias", str(ctx.exception))
        self.assertFalse(self.pasta.exists())

class TestLimitesDaBusca(ComPastaTemporaria):
    def test_limite_de_duas_buscas(self):
        estado = estado_novo()
        estado["buscas"] = 2
        with patch.object(a, "buscar_noticias") as busca:
            with self.assertRaises(ValueError) as ctx:
                a.processar_ferramenta("buscar_noticias", {"consulta": "x"}, estado, self.pasta)
        self.assertIn("Limite de duas buscas", str(ctx.exception))
        busca.assert_not_called()

    def test_recusa_argumento_extra(self):
        estado = estado_novo()
        with patch.object(a, "buscar_noticias") as busca:
            with self.assertRaises(ValueError):
                a.processar_ferramenta(
                    "buscar_noticias", {"consulta": "x", "caminho": "C:/"}, estado, self.pasta)
        busca.assert_not_called()
        self.assertEqual(estado["buscas"], 0)

    def test_recusa_nova_busca_se_ja_ha_noticias(self):
        estado = estado_novo(noticias=[NOTICIA])
        with patch.object(a, "buscar_noticias") as busca:
            with self.assertRaises(ValueError):
                a.processar_ferramenta("buscar_noticias", {"consulta": "x"}, estado, self.pasta)
        busca.assert_not_called()

    def test_ferramenta_desconhecida(self):
        with self.assertRaises(ValueError):
            a.processar_ferramenta("apagar_tudo", {}, estado_novo(), self.pasta)

    def test_consulta_invalida_levanta_value_error(self):
        for consulta in [123, None, "a", "x" * 181, "   "]:
            with self.subTest(consulta=consulta):
                with self.assertRaises(ValueError):
                    a.buscar_noticias(consulta)


class TestCriacaoComNoticias(ComPastaTemporaria):
    ARGS = {"tema": "Teste", "paleta": "delivery"}

    def test_recusa_paleta_invalida(self):
        estado = estado_novo(noticias=[NOTICIA])
        with self.assertRaises(ValueError):
            a.processar_ferramenta(
                "criar_site", {"tema": "Teste", "paleta": "xyz"}, estado, self.pasta)
        self.assertFalse(self.pasta.exists())

    def test_cancelamento_nao_cria_nada(self):
        estado = estado_novo(noticias=[NOTICIA])
        with patch("builtins.input", return_value="n"):
            resultado = a.processar_ferramenta("criar_site", self.ARGS, estado, self.pasta)
        self.assertEqual(resultado, {"status": "cancelado"})
        self.assertTrue(estado["cancelado"])
        self.assertFalse(estado["concluido"])
        self.assertFalse(self.pasta.exists())

    def test_qualquer_resposta_diferente_de_s_cancela(self):
        for resposta in ["sim", "", "yes", "n"]:
            with self.subTest(resposta=resposta):
                estado = estado_novo(noticias=[NOTICIA])
                with patch("builtins.input", return_value=resposta):
                    resultado = a.processar_ferramenta("criar_site", self.ARGS, estado, self.pasta)
                self.assertEqual(resultado["status"], "cancelado")
                self.assertFalse(self.pasta.exists())

    def test_sucesso_grava_arquivos(self):
        estado = estado_novo(noticias=[NOTICIA])
        with patch("builtins.input", return_value=" S "):
            resultado = a.processar_ferramenta("criar_site", self.ARGS, estado, self.pasta)
        self.assertEqual(resultado["status"], "sucesso")
        self.assertTrue(estado["concluido"])
        self.assertEqual(sorted(p.name for p in self.pasta.iterdir()),
                         ["index.html", "noticias.json"])
        gravado = json.loads((self.pasta / "noticias.json").read_text(encoding="utf-8"))
        self.assertEqual(gravado["noticias"], [NOTICIA])

    def test_nao_aceita_nova_chamada_apos_encerrar(self):
        estado = estado_novo(noticias=[NOTICIA])
        estado["cancelado"] = True
        with self.assertRaises(ValueError) as ctx:
            a.processar_ferramenta("buscar_noticias", {"consulta": "x"}, estado, self.pasta)
        self.assertIn("encerrada", str(ctx.exception))

class TestRenderizacao(unittest.TestCase):
    def dados_hostis(self):
        return {
            "consulta": "<b>consulta</b>",
            "coletado_em": "2026-01-01T00:00:00+00:00",
            "noticias": [{
                "id": 1,
                "titulo": "<script>alert(1)</script> & cia",
                "fonte": "Fonte <b>Teste</b>",
                "data": "hoje",
                "link": 'https://news.google.com/x" onmouseover="alert(1)',
            }],
        }

    def test_escapa_conteudo_externo(self):
        html = a.renderizar_site("Tema <i>x</i>", "delivery", self.dados_hostis())
        self.assertNotIn("<script>", html)
        self.assertNotIn("<b>", html)
        self.assertNotIn("<i>", html)
        self.assertIn("&lt;script&gt;", html)
        self.assertNotIn('" onmouseover=', html)
        self.assertIn("&quot; onmouseover=&quot;", html)

    def test_politica_de_seguranca_presente(self):
        html = a.renderizar_site("Tema", "delivery", self.dados_hostis())
        self.assertIn("Content-Security-Policy", html)
        self.assertIn("default-src 'none'", html)

    def test_todas_as_paletas_renderizam_com_suas_cores(self):
        for nome, cores in a.PALETAS.items():
            with self.subTest(paleta=nome):
                html = a.renderizar_site("Tema", nome, self.dados_hostis())
                for cor in cores:
                    self.assertIn(cor, html)

    def test_todas_as_paletas_estao_nas_instrucoes(self):
        for nome in a.PALETAS:
            with self.subTest(paleta=nome):
                self.assertIn(nome, a.INSTRUCOES)

    def test_enum_do_esquema_acompanha_o_dicionario(self):
        props = a.FERRAMENTAS.function_declarations[1].parameters.properties
        self.assertEqual(props["paleta"].enum, list(a.PALETAS))

    def test_criar_site_nao_recebe_noticias(self):
        props = a.FERRAMENTAS.function_declarations[1].parameters.properties
        self.assertEqual(set(props), {"tema", "paleta"})


class RespostaFalsa:
    def __init__(self, conteudo):
        self.content = conteudo
        self.url = "https://news.google.com/rss/search?q=teste"

    def raise_for_status(self):
        pass


def rss(itens):
    corpo = "".join(
        f"<item><title>{titulo}</title><link>{link}</link>"
        f"<pubDate>Wed, 01 Jan 2026 00:00:00 GMT</pubDate>"
        f'<source url="https://exemplo.com">{fonte}</source></item>'
        for titulo, link, fonte in itens
    )
    xml = ('<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel>'
           f"<title>t</title>{corpo}</channel></rss>")
    return xml.encode("utf-8")


class TestFiltroDoFeed(unittest.TestCase):
    def busca_com(self, itens):
        with patch.object(a.requests, "get", return_value=RespostaFalsa(rss(itens))):
            return a.buscar_noticias("teste")

    def test_descarta_links_inseguros_e_duplicados(self):
        itens = [
            ("Valida", "https://news.google.com/a", "Fonte A"),
            ("Esquema javascript", "javascript:alert(1)", "Fonte B"),
            ("Esquema http", "http://news.google.com/b", "Fonte C"),
            ("Host parecido", "https://news.google.com.exemplo.com/c", "Fonte D"),
            ("Outro dominio", "https://exemplo.com/d", "Fonte E"),
            ("Duplicada", "https://news.google.com/a", "Fonte F"),
            ("", "https://news.google.com/e", "Fonte G"),
        ]
        resultado = self.busca_com(itens)
        self.assertEqual([n["titulo"] for n in resultado["noticias"]], ["Valida"])

    def test_limita_a_seis_noticias(self):
        itens = [(f"Noticia {i}", f"https://news.google.com/{i}", "Fonte") for i in range(10)]
        self.assertEqual(len(self.busca_com(itens)["noticias"]), 6)

    def test_corta_titulo_longo(self):
        itens = [("x" * 900, "https://news.google.com/a", "Fonte")]
        self.assertEqual(len(self.busca_com(itens)["noticias"][0]["titulo"]), 500)

    def test_feed_vazio_devolve_lista_vazia(self):
        self.assertEqual(self.busca_com([])["noticias"], [])

    def test_guarda_fonte_e_data_do_feed(self):
        noticia = self.busca_com([("Valida", "https://news.google.com/a", "Fonte A")])["noticias"][0]
        self.assertEqual(noticia["fonte"], "Fonte A")
        self.assertIn("2026", noticia["data"])


if __name__ == "__main__":
    unittest.main(verbosity=2)