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

out, stats = [], {}
for cid, nombre, kcol, hcol in CATS:
    items = [c for c in capas if c["categoria"] == cid]
    if not items: continue
    stats[cid] = len(items)
    out.append(f"<Folder><name>{e(nombre)} ({len(items)})</name><visibility>1</visibility>"
               f"<Style><ListStyle><listItemType>checkHideChildren</listItemType></ListStyle></Style>"
               f"<Style id='p_{cid}'><LabelStyle><scale>0</scale></LabelStyle><LineStyle><color>{kcol}</color><width>2</width></LineStyle>"
               f"<PolyStyle><color>22{kcol[2:]}</color><outline>1</outline></PolyStyle>"
               f"<BalloonStyle><text>$[description]</text><bgColor>ffffffff</bgColor></BalloonStyle></Style>")
    for c in sorted(items, key=lambda c: -c["bounds"]["n"]):
        out.append(f"<Placemark><name>{e(c.get('informe') or c['id'])}</name><styleUrl>#p_{cid}</styleUrl>"
                   f"<description><![CDATA[{popup(c, hcol)}]]></description>"
                   f"<Polygon><tessellate>1</tessellate><outerBoundaryIs><LinearRing><coordinates>{ring(c['bounds'])}</coordinates></LinearRing></outerBoundaryIs></Polygon></Placemark>")
    out.append("</Folder>")

# Acceso por carta (estrellas), una carpeta por región, solo geología
reg = collections.defaultdict(list)
for c in capas:
    if c["categoria"] == "geologia": reg[c.get("region") or "Sin región"].append(c)
out.append("<Folder><name>📍 Acceso a capas por carta</name><open>0</open>"
           "<Style><ListStyle><listItemType>checkHideChildren</listItemType></ListStyle></Style>")
for r in sorted(reg):
    out.append(f"<Folder><name>{e(r)} ({len(reg[r])})</name><visibility>0</visibility>")
    for c in sorted(reg[r], key=lambda c: -c["bounds"]["n"]):
        b = c["bounds"]; x, y = (b["w"] + b["e"]) / 2, (b["s"] + b["n"]) / 2
        out.append(f"<Placemark><name>{e(c['titulo'])}</name><styleUrl>#marcador</styleUrl>"
                   f"<description><![CDATA[{popup(c, '#cc0000')}]]></description><Point><coordinates>{x},{y},0</coordinates></Point></Placemark>")
    out.append("</Folder>")
out.append("</Folder>")

portada = (f"<div style='width:420px;font-family:Segoe UI,Arial,sans-serif;font-size:13px'><img src='quads/banner_sernageomin.jpg' width='420'/>"
           f"<h3 style='color:#1a5276'>Cartografía Geológica Interactiva — Chile</h3>"
           f"<p>{stats.get('geologia',0)} cartas geológicas y {stats.get('peligros',0)} mapas de peligros geológicos, "
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
