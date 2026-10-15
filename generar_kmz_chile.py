"""Genera chile_indice.kmz (índice nacional estilo Visor del Maule) desde el capas.json de GeoChile."""
import json, zipfile, html, collections, sys
sys.stdout.reconfigure(encoding="utf-8")
GEOCHILE = "https://cvenegas-sernageomin.github.io/GeoChile/"
SRC = "../Geo_Repo_Maule_Sernageomin/capas.json"
CATS = [  # id, carpeta, color KML aabbggrr, color html
    ("geologia", "🗺️ Cartografía Geológica", "ff0000cc", "#cc0000"),
    ("peligros", "⚠️ Peligros Geológicos", "ff0080ff", "#ff8000"),
    ("aplicada", "🧪 Geología Aplicada", "ff7a7a00", "#007a7a"),
    ("historico", "📜 Cartografía Histórica", "ff4f4f8d", "#8d4f4f"),
]
e = lambda s: html.escape(str(s or ""), quote=True)
capas = json.load(open(SRC, encoding="utf-8"))

def pdf_url(p):
    if not p: return None
    return p if p.startswith("https://") else GEOCHILE + p

def popup(c, color):
    b = c["bounds"]
    rows = [("Informe", c.get("informe")), ("Escala", c.get("escala")), ("Año", c.get("anio")),
            ("Autores", c.get("autor")), ("Región", c.get("region")), ("Tema", c.get("tema"))]
    t = "".join(f"<tr><td style='color:#666;padding:2px 8px 2px 0'><b>{k}</b></td><td>{e(v)}</td></tr>" for k, v in rows if v)
    pdf = pdf_url(c.get("pdf"))
    btn = lambda u, txt, bg: f"<a href='{u}' style='display:inline-block;margin:6px 6px 0 0;padding:7px 12px;background:{bg};color:#fff;text-decoration:none;border-radius:4px;font-weight:bold'>{txt}</a>"
    return (f"<div style='width:400px;font-family:Segoe UI,Arial,sans-serif;font-size:13px'>"
            f"<div style='background:{color};color:#fff;padding:8px 10px;font-size:15px;font-weight:bold'>{e(c['titulo'])}</div>"
            f"<div style='padding:6px 2px;color:#444'>{e(c.get('fuente'))}</div><table>{t}</table>"
            f"{btn(GEOCHILE, '🌐 Abrir en visor GeoChile', '#1a5276')}"
            f"{btn(pdf, '⬇ Informe PDF', '#c0392b') if pdf else ''}</div>")

def ring(b):
    w, e_, s, n = b["w"], b["e"], b["s"], b["n"]
    return f"{w},{s},0 {w},{n},0 {e_},{n},0 {e_},{s},0 {w},{s},0"

# ── Grilla nacional IGM 1:100.000 (460 hojas, de Cartas100mil.kmz) ──
grilla = json.load(open("grilla_igm100k.json", encoding="utf-8"))
CATN = {c[0]: c[1] for c in CATS}
def solape(h, b):
    w, e_ = max(h["w"], b["w"]), min(h["e"], b["e"]); s_, n = max(h["s"], b["s"]), min(h["n"], b["n"])
    return max(0, e_ - w) * max(0, n - s_) / ((h["e"] - h["w"]) * (h["n"] - h["s"]))
stats = collections.Counter(c["categoria"] for c in capas if c["categoria"] != "hillshade")
out, con, sin = [], [], []
for h in sorted(grilla, key=lambda h: (-h["n"], h["w"])):
    h["cartas"] = [c for c in capas if c["categoria"] in CATN and solape(h, c["bounds"]) >= 0.15]
    (con if h["cartas"] else sin).append(h)

def popup_hoja(h):
    nom = h["nombre"] or "Hoja sin nombre"
    items = ""
    for cid, nombre, _, hcol in CATS:
        cs = [c for c in h["cartas"] if c["categoria"] == cid]
        if not cs: continue
        items += f"<div style='margin-top:8px;font-weight:bold;color:{hcol}'>{e(nombre)}</div>"
        for c in cs:
            p = pdf_url(c.get("pdf"))
            items += (f"<div style='padding:3px 0;border-bottom:1px solid #eee'>{e(c['titulo'])}"
                      f"<br><span style='color:#777'>{e(c.get('informe') or '')} {e(c.get('anio') or '')}</span>"
                      + (f" &nbsp;<a href='{p}'>⬇ PDF</a>" if p else "") + "</div>")
    if not items: items = "<p style='color:#777'>Sin cartografía publicada en el visor para esta hoja.</p>"
    return (f"<div style='width:400px;font-family:Segoe UI,Arial,sans-serif;font-size:13px'>"
            f"<div style='background:#1a5276;color:#fff;padding:8px 10px;font-size:15px;font-weight:bold'>{e(h['codigo'])} — {e(nom)}</div>"
            f"<div style='padding:6px 2px;color:#444'>Hoja IGM 1:100.000 · estado: {e(h['estado'] or 's/i')}</div>"
            f"<div style='max-height:260px;overflow-y:auto'>{items}</div>"
            f"<a href='{GEOCHILE}' style='display:inline-block;margin-top:8px;padding:7px 12px;background:#1a5276;color:#fff;text-decoration:none;border-radius:4px;font-weight:bold'>🌐 Abrir en visor GeoChile</a></div>")

def hoja_pm(h, estilo):
    r = f"{h['w']},{h['s']},0 {h['w']},{h['n']},0 {h['e']},{h['n']},0 {h['e']},{h['s']},0 {h['w']},{h['s']},0"
    return (f"<Placemark><name>{e(h['codigo'])}</name><Snippet maxLines='0'></Snippet><styleUrl>#{estilo}</styleUrl>"
            f"<description><![CDATA[{popup_hoja(h)}]]></description>"
            f"<Polygon><tessellate>1</tessellate><outerBoundaryIs><LinearRing><coordinates>{r}</coordinates></LinearRing></outerBoundaryIs></Polygon></Placemark>")

def estilo(i, kline, kfill, w):
    return (f"<Style id='{i}'><LabelStyle><scale>0</scale></LabelStyle><LineStyle><color>{kline}</color><width>{w}</width></LineStyle>"
            f"<PolyStyle><color>{kfill}</color><outline>1</outline></PolyStyle>"
            f"<BalloonStyle><text>$[description]</text><bgColor>ffffffff</bgColor></BalloonStyle></Style>")
LIST = "<Style><ListStyle><listItemType>checkHideChildren</listItemType></ListStyle></Style>"
out.append(f"<Folder><name>🗺️ Cartografía Geológica Interactiva — Chile ({len(grilla)} hojas)</name>"
           "<description>Grilla de hojas IGM 1:100.000 de todo el país. Verde = hay cartografía en el visor GeoChile | Rojo = sin cartografía aún.</description>"
           f"<visibility>1</visibility>{LIST}"
           + estilo("h_con", "ff2e7d32", "3300b050", 2) + estilo("h_sin", "ff0000cc", "1affffff", 1.5))
out += [hoja_pm(h, "h_con") for h in con] + [hoja_pm(h, "h_sin") for h in sin]
out.append("</Folder>")

# Acceso por hoja (estrellas) solo donde hay cartografía, una carpeta por región
reg = collections.defaultdict(list)
for h in con:
    cs = [c for c in h["cartas"] if c["categoria"] == "geologia"] or h["cartas"]
    reg[collections.Counter(c.get("region") or "Sin región" for c in cs).most_common(1)[0][0]].append(h)
out.append(f"<Folder><name>📍 Acceso a capas por hoja ({len(con)})</name><open>0</open>{LIST}")
for r in sorted(reg):
    out.append(f"<Folder><name>{e(r)} ({len(reg[r])})</name><visibility>0</visibility>")
    for h in reg[r]:
        out.append(f"<Placemark><name>{e(h['codigo'])} {e(h['nombre'])}</name><styleUrl>#marcador</styleUrl>"
                   f"<description><![CDATA[{popup_hoja(h)}]]></description>"
                   f"<Point><coordinates>{(h['w'] + h['e']) / 2},{(h['s'] + h['n']) / 2},0</coordinates></Point></Placemark>")
    out.append("</Folder>")
out.append("</Folder>")
stats = {"geologia": stats["geologia"], "peligros": stats["peligros"], "hojas": len(grilla), "con": len(con)}

portada = (f"<div style='width:420px;font-family:Segoe UI,Arial,sans-serif;font-size:13px'><img src='quads/banner_sernageomin.jpg' width='420'/>"
           f"<h3 style='color:#1a5276'>Cartografía Geológica Interactiva — Chile</h3>"
           f"<p>{stats["geologia"]} cartas geológicas y {stats["peligros"]} mapas de peligros geológicos sobre la grilla de {stats["hojas"]} hojas 1:100.000, "
           f"con acceso al visor web y a los informes en PDF.</p>"
           f"<a href='{GEOCHILE}' style='display:inline-block;padding:9px 16px;background:#1a5276;color:#fff;text-decoration:none;border-radius:4px;font-weight:bold'>🌐 Abrir visor GeoChile</a></div>")
kml = f"""<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2"><Document>
<name>SERNAGEOMIN — Geología de Chile</name>
<description>Índice nacional de cartas geológicas y mapas de peligros geológicos. Fuente: SERNAGEOMIN. Visor web: {GEOCHILE}</description>
<open>0</open>
<LookAt><longitude>-70.6</longitude><latitude>-33.5</latitude><range>4500000</range></LookAt>
<Style id="marcador"><IconStyle><color>ffffffff</color><scale>1.2</scale><Icon><href>http://maps.google.com/mapfiles/kml/paddle/ylw-stars.png</href></Icon><hotSpot x="0.5" y="0" xunits="fraction" yunits="fraction"/></IconStyle><LabelStyle><scale>0.7</scale></LabelStyle><BalloonStyle><text>$[description]</text><bgColor>ffffffff</bgColor></BalloonStyle></Style>
<Placemark><name>🌐 Visor web GeoChile</name><styleUrl>#marcador</styleUrl><description><![CDATA[{portada}]]></description><Point><coordinates>-70.6,-33.5,0</coordinates></Point></Placemark>
{chr(10).join(out)}
</Document></kml>"""
with zipfile.ZipFile("chile_indice.kmz", "w", zipfile.ZIP_DEFLATED) as z:
    z.writestr("doc.kml", kml); z.write("quads/banner_sernageomin.jpg")
print(stats, len(kml) // 1024, "KB kml")
