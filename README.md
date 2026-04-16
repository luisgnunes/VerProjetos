# 📋 Consulta de Documentos — Guia de Deploy

## Arquivos da aplicação

```
index.html          → página principal (PWA)
documentos.json     → base de dados dos documentos (você atualiza este)
manifest.json       → configuração do app instalável
sw.js               → service worker (offline)
icon-192.png        → ícone do app
icon-512.png        → ícone do app (HD)
excel_para_json.py  → script para exportar seu Excel → documentos.json
```

---

## 1. Como atualizar os documentos

1. Edite sua planilha Excel normalmente (adicione/altere documentos)
2. Execute o script de exportação:
   ```bash
   pip install openpyxl    # (só na primeira vez)
   python excel_para_json.py lista_mestra.xlsx documentos.json
   ```
3. Faça o upload do novo `documentos.json` no GitHub (substitui o anterior)
4. A página atualiza automaticamente em ~1 minuto

---

## 2. Links do OneDrive

Na planilha Excel, coluna **Link OneDrive**:

1. Abra o OneDrive / SharePoint no navegador
2. Encontre o PDF desejado
3. Clique com botão direito → **"Copiar link"**
4. Cole o link gerado na célula da planilha

> ⚠️ Se a pasta for corporativa (SharePoint/Teams), certifique-se de que o link 
> está com permissão "Qualquer pessoa com o link" ou restrito aos usuários da equipe.

---

## 3. Deploy no GitHub Pages (gratuito)

### Primeira vez:

1. Crie uma conta em [github.com](https://github.com) se não tiver
2. Clique em **"New repository"** → nome: `projetos-docs` (ou o que preferir)
3. Marque **Public** (necessário para GitHub Pages gratuito)
4. Faça upload de todos os arquivos acima
5. Vá em **Settings → Pages → Source**: selecione `main` branch, pasta `/root`
6. Clique **Save** — em ~2 minutos o site estará disponível em:
   `https://seu-usuario.github.io/projetos-docs/`

### Atualizações posteriores:

- No GitHub, clique no arquivo `documentos.json` → ícone de lápis (editar)
- Ou use o botão "Add file → Upload files" para substituir

---

## 4. Instalar como app no tablet (Chrome)

1. Abra o Chrome no tablet e acesse a URL do GitHub Pages
2. Toque no menu (⋮) → **"Adicionar à tela inicial"** ou **"Instalar app"**
3. Confirme → o ícone aparece na tela inicial como um aplicativo nativo
4. A partir de agora funciona offline com os dados da última sincronização

---

## 5. Funcionamento offline

- Na primeira visita com internet, todos os arquivos são armazenados no cache
- Nas visitas seguintes, funciona sem internet
- Quando uma nova versão do `documentos.json` for publicada, um banner 
  aparece na parte inferior da tela: **"🔄 Nova versão disponível"**
- Toque nele para atualizar

---

## 6. Estrutura do documentos.json

```json
[
  {
    "codigo":        "DR-452-001",
    "titulo":        "Planta de Drenagem - Bueiro BST 1.00m - Est. 452+100",
    "disciplina":    "DRENAGEM",
    "trecho":        "km 452+454",
    "revisao":       "B",
    "palavras_chave":"bueiro tubular bst drenagem transversal",
    "link":          "https://seu-link-do-onedrive-aqui"
  }
]
```

**Disciplinas válidas:** `DRENAGEM` | `TERRAPLENAGEM` | `PAVIMENTO` | `TOPOGRAFIA` | `GEOMÉTRICO`
