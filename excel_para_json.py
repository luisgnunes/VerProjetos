#!/usr/bin/env python3
"""
excel_para_json.py
──────────────────
Converte a planilha Excel de lista mestra de documentos para o arquivo
documentos.json utilizado pela página web.

Colunas esperadas no Excel (nomes podem ser ajustados nas constantes abaixo):
  codigo        | código do documento (ex: DR-452-001)
  titulo        | título completo do documento
  disciplina    | DRENAGEM | TERRAPLENAGEM | PAVIMENTO | TOPOGRAFIA | GEOMÉTRICO
  obra        | ex: km 452+454
  revisao       | letra de revisão (ex: A, B, C)
  palavras_chave| termos separados por espaço ou vírgula
  link          | URL do OneDrive (gerado pelo "Copiar link" do OneDrive)

USO:
  pip install openpyxl
  python excel_para_json.py lista_mestra.xlsx documentos.json

  Ou apenas:
  python excel_para_json.py   (assume nomes padrão abaixo)
"""

import sys
import json
import re
from pathlib import Path

try:
    import openpyxl
except ImportError:
    print("Instale openpyxl:  pip install openpyxl")
    sys.exit(1)

# ── CONFIGURAÇÕES (ajuste conforme seus cabeçalhos) ───────────────────────
EXCEL_FILE  = "0.LD_TABLET.xlsx"
JSON_FILE   = "documentos.json"
SHEET_NAME  = None  # None = primeira aba

# Mapeamento: chave JSON → nome (ou índice) da coluna no Excel
# Use o nome exato do cabeçalho ou o índice da coluna (A=1, B=2, …)
COL_MAP = {
    "codigo":        "DOCUMENTO",
    "titulo":        "TÍTULO",
    "disciplina":    "DISCIPLINA",
    "sigla":         "SIGLA",
    "ano":           "ANO",
    "grupo":         "GRUPO",
    "obra":        "OBRA",
    "revisao":       "REVISÃO",
    "palavras_chave":"PALAVRAS-CHAVE",
    "link":          "LINK",
    "arquivo":        "LOCAL"
}

DISCIPLINAS_VALIDAS = {
    'ADEQUAÇÃO DE ACESSIBILIDADE', 'LEVANTAMENTO AEROFOTOGRAMÉTRICO', 'ARQUITETURA', 
    'AR CONDICIONADO (VENTILAÇÃO)', 'AUTOMAÇÃO (TELECOMUNICAÇÕES)', 'BOTA FORA', 
    'CONTROLE DE QUALIDADE', 'CAMINHO DE SERVIÇO', 'DATA BOOK', 'DRENAGEM', 
    'DESAPROPRIAÇÃO', 'DESVIO DE TRÁFEGO', 'ESTUDOS ESPECIAIS', 
    'ILUMINAÇÃO E INSTALAÇÕES ELÉTRICAS', 'ESTRUTURA METÁLICA', 'ESTRUTURA', 
    'SEQUÊNCIA EXECUTIVA', 'GEOMÉTRICO', 'GEOTECNIA E GEOLOGIA', 
    'VÁRIAS CLASSES DE PROJETOS / GENÉRICOS / GERAL', 'INSTALAÇÃO HIDRÁULICA', 
    'IMPERMEABILIZAÇÃO', 'INTERFERÊNCIAS (FAIXA DE DOMÍNIO)', 'IDENTIDADE VISUAL', 
    'MEIO AMBIENTE', 'OUTROS', 'PAISAGISMO', 'PAVIMENTAÇÃO', 
    'REINTEGRAÇÃO DE POSSE', 'DISPOSITIVOS DE SEGURANÇA', 'SINALIZAÇÃO', 
    'TERRAPLENAGEM', 'TOPOGRAFIA', 'ESTUDO DE TRÁFEGO', 'OBRAS COMPLEMENTARES'
}
# ─────────────────────────────────────────────────────────────────────────


def normalizar(s):
    """Remove espaços extras e converte para string."""
    if s is None:
        return ""
    return str(s).strip()


def ler_excel(caminho: Path, aba=None):
    wb = openpyxl.load_workbook(caminho, read_only=True, data_only=True)
    ws = wb[aba] if aba else wb.active
    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        raise ValueError("Planilha vazia.")
    return rows


def mapear_colunas(cabecalho, col_map):
    """Retorna dict: chave_json → índice_coluna."""
    header_norm = {str(c).strip().lower(): i for i, c in enumerate(cabecalho)}
    indices = {}
    missing = []
    for chave, nome_col in col_map.items():
        if isinstance(nome_col, int):
            indices[chave] = nome_col - 1
        else:
            idx = header_norm.get(nome_col.lower())
            if idx is None:
                missing.append(nome_col)
            else:
                indices[chave] = idx
    if missing:
        print(f"⚠  Colunas não encontradas (serão ignoradas): {missing}")
        print(f"   Cabeçalhos encontrados: {list(header_norm.keys())}")
    return indices


def gerar_filtros(documentos: list, json_path: str):
    """
    Gera filtros.json com anos, obras e disciplinas pré-computadas por
    combinação ano×obra — evita que o JavaScript precise calcular isso.
    """
    from collections import defaultdict

    anos = sorted(set(d.get("ano", "") for d in documentos if d.get("ano")))
    grupos_set = set(d.get("grupo", "principal") or "principal" for d in documentos)
    grupos_outros = sorted(g for g in grupos_set if g != "principal")
    grupos = (["principal"] if "principal" in grupos_set else []) + grupos_outros
    
    # obras por ano
    o_por_a: dict = defaultdict(set)
    for d in documentos:
        a, o = d.get("ano", ""), d.get("obra", "")
        if o:
            o_por_a["todos"].add(o)
            if a:
                o_por_a[a].add(o)
    obras = {k: sorted(v) for k, v in o_por_a.items()}

    # disciplinas por ano × obra
    disc: dict = defaultdict(lambda: defaultdict(set))
    for d in documentos:
        a, o, s = d.get("ano", ""), d.get("obra", ""), d.get("sigla", "")
        if not s:
            continue
        disc["todos"]["todos"].add(s)
        if o:
            disc["todos"][o].add(s)
        if a:
            disc[a]["todos"].add(s)
            if o:
                disc[a][o].add(s)

    disciplinas = {
        ano: {obra: sorted(siglas) for obra, siglas in td.items()}
        for ano, td in disc.items()
    }

    # obras por ano × grupo
    obras_por_ano_grupo: dict = defaultdict(lambda: defaultdict(set))
    for d in documentos:
        a = d.get("ano", "")
        g = d.get("grupo", "principal") or "principal"
        o = d.get("obra", "")
        if not o:
            continue
        obras_por_ano_grupo["todos"]["todos"].add(o)
        obras_por_ano_grupo["todos"][g].add(o)
        if a:
            obras_por_ano_grupo[a]["todos"].add(o)
            obras_por_ano_grupo[a][g].add(o)

    obras_ag = {
        ano: {grupo: sorted(lista) for grupo, lista in grupos_dict.items()}
        for ano, grupos_dict in obras_por_ano_grupo.items()
    }

    # disciplinas por ano × grupo × obra
    disc_por_ano_grupo: dict = defaultdict(lambda: defaultdict(lambda: defaultdict(set)))
    for d in documentos:
        a = d.get("ano", "")
        g = d.get("grupo", "principal") or "principal"
        o = d.get("obra", "")
        s = d.get("sigla", "")
        if not s:
            continue

        disc_por_ano_grupo["todos"]["todos"]["todos"].add(s)
        disc_por_ano_grupo["todos"][g]["todos"].add(s)
        if o:
            disc_por_ano_grupo["todos"]["todos"][o].add(s)
            disc_por_ano_grupo["todos"][g][o].add(s)

        if a:
            disc_por_ano_grupo[a]["todos"]["todos"].add(s)
            disc_por_ano_grupo[a][g]["todos"].add(s)
            if o:
                disc_por_ano_grupo[a]["todos"][o].add(s)
                disc_por_ano_grupo[a][g][o].add(s)

    disciplinas_ag = {
        ano: {
            grupo: {obra: sorted(siglas) for obra, siglas in obras_dict.items()}
            for grupo, obras_dict in grupos_dict.items()
        }
        for ano, grupos_dict in disc_por_ano_grupo.items()
    }

    filtros = {
        "anos": anos,
        "grupos": grupos,
        "obras": obras,
        "disciplinas": disciplinas,
        "obras_por_ano_grupo": obras_ag,
        "disciplinas_por_ano_grupo": disciplinas_ag,
    }
    filtros_path = Path(json_path).parent / "filtros.json"
    filtros_path.write_text(
        json.dumps(filtros, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    print(f"✅ filtros.json → {filtros_path}")


def converter(excel_path: str, json_path: str):
    print(f"📂 Lendo: {excel_path}")
    rows = ler_excel(Path(excel_path), SHEET_NAME)
    cabecalho = rows[2]
    dados = rows[3:]

    indices = mapear_colunas(cabecalho, COL_MAP)

    documentos = []
    ignorados  = 0

    for i, row in enumerate(dados, start=2):
        codigo = normalizar(row[indices.get("codigo", -1)] if "codigo" in indices else "")
        if not codigo:
            ignorados += 1
            continue  # linha sem código é ignorada

        disc = normalizar(row[indices.get("disciplina", -1)] if "disciplina" in indices else "")
        disc_upper = disc.upper()

        doc = {
            "codigo":        codigo,
            "titulo":        normalizar(row[indices["titulo"]])        if "titulo"        in indices else "",
            "disciplina":    disc_upper                                if disc_upper in DISCIPLINAS_VALIDAS else disc_upper,
            "ano":           normalizar(row[indices["ano"]])           if "ano"           in indices else "",
            "grupo":         (normalizar(row[indices["grupo"]]).lower() if "grupo" in indices else "") or "principal",
            "obra":          normalizar(row[indices["obra"]])          if "obra"        in indices else "",
            "revisao":       normalizar(row[indices["revisao"]])       if "revisao"       in indices else "",
            "palavras_chave":normalizar(row[indices["palavras_chave"]]) if "palavras_chave" in indices else "",
            "link":          normalizar(row[indices["link"]])          if "link"          in indices else "",
            "sigla":         normalizar(row[indices["sigla"]])         if "sigla"         in indices else "",
            "arquivo":       normalizar(row[indices["arquivo"]])       if "arquivo"       in indices else "",
        }

        if disc_upper not in DISCIPLINAS_VALIDAS:
            print(f"  ⚠  Linha {i}: disciplina desconhecida '{disc}' — mantida assim mesmo")

        documentos.append(doc)

    Path(json_path).write_text(
        json.dumps(documentos, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    print(f"✅ {len(documentos)} documentos exportados → {json_path}")
    if ignorados:
        print(f"   ({ignorados} linhas sem código ignoradas)")

    gerar_filtros(documentos, json_path)


if __name__ == "__main__":
    excel = sys.argv[1] if len(sys.argv) > 1 else EXCEL_FILE
    saida = sys.argv[2] if len(sys.argv) > 2 else JSON_FILE
    converter(excel, saida)
