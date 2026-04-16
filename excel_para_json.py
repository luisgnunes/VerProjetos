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
  trecho        | ex: km 452+454
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
    "trecho":        "TRECHO",
    "revisao":       "REVISÃO",
    "palavras_chave":"PALAVRAS-CHAVE",
    "link":          "PASTA",
    "arquivo":        "ARQUIVO"
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
            "trecho":        normalizar(row[indices["trecho"]])        if "trecho"        in indices else "",
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


if __name__ == "__main__":
    excel = sys.argv[1] if len(sys.argv) > 1 else EXCEL_FILE
    saida = sys.argv[2] if len(sys.argv) > 2 else JSON_FILE
    converter(excel, saida)
