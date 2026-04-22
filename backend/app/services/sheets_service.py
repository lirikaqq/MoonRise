import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.exceptions import HttpError

class SheetsService:
    def __init__(self):
        self.credentials = Credentials.from_service_account_file(
            '/app/google_credentials.json',
            scopes=['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        )
        self.gc = gspread.authorize(self.credentials)

    async def export_participants(
        self,
        sheet_id: str,
        tournament_title: str,
        participants: list[dict]
    ) -> dict:
        try:
            sh = self.gc.open_by_key(sheet_id)
        except gspread.exceptions.SpreadsheetNotFound:
            raise Exception(f"Таблица с ID {sheet_id} не найдена")
        except gspread.exceptions.APIError as e:
            raise Exception(f"Ошибка доступа к таблице: {e}")

        worksheet = sh.sheet1
        worksheet.clear()

        headers = [
            "Discord",
            "Battle Tag",
            "Твинк аккаунты",
            "Основная роль",
            "Доп. роль",
            "Хочет быть капитаном",
            "О себе",
            "Дивизион",
            "Допуск",
            "Чек-ин"
        ]
        worksheet.update([headers])

        data = []
        for participant in participants:
            row = [
                participant["discord"],
                participant["battle_tag"],
                participant["alt_battle_tags"],
                participant["primary_role"],
                participant["secondary_role"],
                participant["wants_captain"],
                participant["notes"],
                participant["division"],
                participant["approved"],
                participant["checked_in"]
            ]
            data.append(row)

        worksheet.update(data)

        requests = []
        for i, participant in enumerate(participants, start=2):
            if participant["banned"]:
                requests.append({
                    "updateCells": {
                        "rows": [{"values": [{}, {}, {}, {}, {}, {}, {}, {}, {}, {}]}],
                        "range": {
                            "sheetId": 0,
                            "startRowIndex": i - 1,
                            "endRowIndex": i,
                            "startColumnIndex": 0,
                            "endColumnIndex": 10
                        },
                        "fields": "userEnteredFormat"
                    }
                })
                worksheet.update_cell(i, 9, "")
                worksheet.update_cells(
                    f"{i}:{i}",
                    body={
                        "requests": [{
                            "repeatCell": {
                                "range": {
                                    "sheetId": 0,
                                    "startRowIndex": i - 1,
                                    "endRowIndex": i,
                                    "startColumnIndex": 0,
                                    "endColumnIndex": 10
                                },
                                "cell": {
                                    "userEnteredFormat": {
                                        "backgroundColor": {"red": 0.957, "green": 0.800, "blue": 0.800}
                                    }
                                },
                                "fields": "userEnteredFormat"
                            }
                        }]
                    }
                )
            elif participant["approved"]:
                worksheet.update_cell(i, 9, "")
                worksheet.update_cells(
                    f"{i}:{i}",
                    body={
                        "requests": [{
                            "repeatCell": {
                                "range": {
                                    "sheetId": 0,
                                    "startRowIndex": i - 1,
                                    "endRowIndex": i,
                                    "startColumnIndex": 0,
                                    "endColumnIndex": 10
                                },
                                "cell": {
                                    "userEnteredFormat": {
                                        "backgroundColor": {"red": 0.718, "green": 0.882, "blue": 0.804}
                                    }
                                },
                                "fields": "userEnteredFormat"
                            }
                        }]
                    }
                )
            else:
                worksheet.update_cell(i, 9, "")
                worksheet.update_cells(
                    f"{i}:{i}",
                    body={
                        "requests": [{
                            "repeatCell": {
                                "range": {
                                    "sheetId": 0,
                                    "startRowIndex": i - 1,
                                    "endRowIndex": i,
                                    "startColumnIndex": 0,
                                    "endColumnIndex": 10
                                },
                                "cell": {
                                    "userEnteredFormat": {
                                        "backgroundColor": {"red": 0.851, "green": 0.851, "blue": 0.851}
                                    }
                                },
                                "fields": "userEnteredFormat"
                            }
                        }]
                    }
                )

        return {
            "success": True,
            "rows_exported": len(participants),
            "sheet_url": f"https://docs.google.com/spreadsheets/d/{sheet_id}"
        }