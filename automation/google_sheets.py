import gspread
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta
from gspread_formatting import format_cell_range, CellFormat, NumberFormat, Color, TextFormat, Borders, Border
from pathlib import Path

# Configurações de autenticação
AUTHENTICATION_FILE = "credentials.json"  # seu arquivo JSON de serviço
SPREADSHEET_NAME = "Recargas PIX e DINHEIRO - Cantina Batistério"

# Autenticação com gspread
gc = gspread.service_account(filename=AUTHENTICATION_FILE)

# Função para obter ou criar a aba
def get_or_create_sheet():
    today = datetime.now().strftime("%d/%m/%Y")
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%d/%m/%Y")

    sh = gc.open(SPREADSHEET_NAME)
    worksheet = None

    # Verifica se já existe aba com data de hoje ou ontem
    for ws in sh.worksheets():
        if ws.title in (today, yesterday):
            worksheet = ws
            break

    # Se não existir, cria e formata
    if worksheet is None:
        worksheet = sh.add_worksheet(title=today, rows=1000, cols=27)

        # Mesclar A1:C1 e título
        worksheet.merge_cells(1, 1, 1, 3)  # A1:C1
        worksheet.update_acell("A1", "RECARGAS VIA PIX")
        format_cell_range(
            worksheet,
            "A1:C1",
            CellFormat(
                textFormat=TextFormat(bold=True),
                horizontalAlignment="CENTER",
                backgroundColor=Color(red=0.56, green=0.48, blue=0.76),
            ),
        )

        # Cabeçalhos A2:C2
        headers = [["NOME DO PAGADOR", "VALOR", "CARTÃO"]]
        worksheet.update("A2:C2", headers)
        format_cell_range(
            worksheet,
            "A2:C2",
            CellFormat(
                textFormat=TextFormat(bold=True),
                horizontalAlignment="CENTER",
            ),
        )

        format_cell_range(
            worksheet,
            "B3:B1000",
            CellFormat(
                numberFormat=NumberFormat(
                    type="NUMBER",
                    pattern='"R$"#,##0.00'
                )
            )
        )

        format_cell_range(
            worksheet,
            "F3:F7",
            CellFormat(
                numberFormat=NumberFormat(
                    type="NUMBER",
                    pattern='"R$"#,##0.00'
                )
            )
        )

        # E3:E7 labels
        labels = [["TOTAL SISTEMA"], ["PIX"], ["DINHEIRO"], ["SANGRIA"], ["EM CAIXA"]]
        worksheet.update("E3:E7", labels)

        # Fórmula PIX → soma da coluna B (VALOR)
        worksheet.update_acell("F4", "=SUM(B3:B1000)")

        # Cores e bordas E3:F6
        row_colors = [
            Color(red=0.0, green=1.0, blue=0.0),   # Verde
            Color(red=1.0, green=0.65, blue=0.0),  # Laranja
            Color(red=0.0, green=0.0, blue=1.0),   # Azul
            Color(red=1.0, green=0.0, blue=0.0),   # Vermelho
            Color(red=1.0, green=1.0, blue=1.0)    # Branco
        ]
        for i, color in enumerate(row_colors, start=3):
            format_cell_range(
                worksheet,
                f"E{i}",
                CellFormat(
                    backgroundColor=color,
                    horizontalAlignment="CENTER",
                    textFormat=TextFormat(bold=True),
                    borders=Borders(
                        top=Border(style="SOLID"),
                        bottom=Border(style="SOLID"),
                        left=Border(style="SOLID"),
                        right=Border(style="SOLID"),
                    ),
                ),
            )
            format_cell_range(
                worksheet,
                f"F{i}",
                CellFormat(
                    horizontalAlignment="CENTER",
                    textFormat=TextFormat(bold=True),
                    borders=Borders(
                        top=Border(style="SOLID"),
                        bottom=Border(style="SOLID"),
                        left=Border(style="SOLID"),
                        right=Border(style="SOLID"),
                    ),
                ),
            )

        # Bordas A1:C2
        format_cell_range(
            worksheet,
            "A1:C2",
            CellFormat(
                borders=Borders(
                    top=Border(style="SOLID"),
                    bottom=Border(style="SOLID"),
                    left=Border(style="SOLID"),
                    right=Border(style="SOLID"),
                )
            ),
        )
        format_cell_range(
            worksheet,
            "A3:C1000",
            CellFormat(horizontalAlignment="CENTER")
        )

        creds = Credentials.from_service_account_file("credentials.json")

        service = build("sheets", "v4", credentials=creds)
        sheet_id = worksheet._properties["sheetId"]

        requests = [
            # Coluna A (índices baseados em zero: A=0)
            {
                "updateDimensionProperties": {
                    "range": {
                        "sheetId": sheet_id,
                        "dimension": "COLUMNS",
                        "startIndex": 0,   # A
                        "endIndex": 1
                    },
                    "properties": { "pixelSize": 465 },
                    "fields": "pixelSize"
                }
            },
            # Coluna E (E = índice 4)
            {
                "updateDimensionProperties": {
                    "range": {
                        "sheetId": sheet_id,
                        "dimension": "COLUMNS",
                        "startIndex": 4,   # E
                        "endIndex": 5
                    },
                    "properties": { "pixelSize": 255 },
                    "fields": "pixelSize"
                }
            }
        ]

        service.spreadsheets().batchUpdate(
            spreadsheetId=sh.id,
            body={"requests": requests}
        ).execute()

    return worksheet

def adicionar_recarga(metodo_pagamento):
    if metodo_pagamento.upper() == "PIX":
        ws = get_or_create_sheet()
        # Encontra próxima linha vazia
        
        with open("recargas.txt", "r", encoding="utf-8") as f:
            for linha in f:
                next_row = len(ws.col_values(1)) + 1
                linha_limpa = linha.replace("\n", "")
                nome, valor, cartao = linha_limpa.split(",")
                ws.update(f"A{next_row}:C{next_row}", [[nome.upper(), float(valor.replace(",", ".")), cartao]])
                print(f"Recarga PIX adicionada na linha {next_row}.")
    else:
        print("Pagamento em dinheiro — não será adicionado ao Google Sheets.")

def adicionar_recarga_txt(nome, valor, cartao):
    if Path("recargas.txt").exists():
        with open("recargas.txt", "a", encoding="utf-8") as f:
            f.write(f"{nome},{valor},{cartao}\n")
    else:
        with open("recargas.txt", "w", encoding="utf-8") as f:
            f.write(f"{nome},{valor},{cartao}\n")