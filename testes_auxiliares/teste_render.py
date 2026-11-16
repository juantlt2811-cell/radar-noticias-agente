from pathlib import Path
import agente_noticias as a

noticias = [{
    "fonte": f"Fonte {i}",
    "titulo": f"Notícia de teste {i} " + "palavralongasemespacos" * 4,
    "data": "Wed, 28 Oct 2026 23:28:00 GMT",
    "link": "https://news.google.com/x",
} for i in range(1, 5)]
noticias[0]["titulo"] = "<script>alert(1)</script> & cia"

dados = {
    "consulta": "teste local",
    "coletado_em": "2026-01-01T00:00:00+00:00",
    "noticias": noticias,
}
html = a.renderizar_site("Tema <i>teste</i>", "delivery", dados)
Path("saida_teste.html").write_text(html, encoding="utf-8")
print("gravado saida_teste.html")