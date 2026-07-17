import logging
from pathlib import Path

import uvicorn

# NOTE: pipenv は自動で .env を読むので、機能的には dotenv は不要。
#       ただし pipenv が .env を読むタイミングはプロセスを起動したとき。
#       dotenv であれば、リアルタイムで .env を変更できる良さがあるので、今回は採用。
from dotenv import dotenv_values
from fastapi import FastAPI
from fastapi.responses import FileResponse

logger = logging.getLogger(__name__)

INDEX_HTML_PATH = Path(__file__).parent / "main_101_web_ui.html"
ENV_PATH = Path(__file__).parent / ".env"

app = FastAPI()


@app.get("/")
async def index() -> FileResponse:
    """
    Web UI のページ (html 1 枚) を返します。
    """
    return FileResponse(INDEX_HTML_PATH)


def _parse_user_id_choices(raw: str) -> list[dict[str, str]]:
    """
    "yuu:12345,taro:67890" 形式の文字列を、セレクトボックスの選択肢リストにパースします。
    ":" が無い要素は ID のみとみなして、表示名にも ID をそのまま使います。
    """
    choices: list[dict[str, str]] = []
    for item in raw.split(","):
        stripped = item.strip()
        if not stripped:
            continue
        name, _, user_id = stripped.partition(":")
        if not user_id:
            name = user_id = stripped
        choices.append({"name": name, "user_id": user_id})
    return choices


@app.get("/api/defaults")
async def defaults() -> dict[str, object]:
    """
    フォームの初期値と選択肢を .env から読んで返します。 .env が無ければ全部空です。
    NOTE: この .env は web UI 専用です。 001〜003 のスクリプトは読みません (秘密情報は引数で渡す思想)。
    """
    env = dotenv_values(ENV_PATH)
    return {
        "discord_application_id": env.get("WEB_DEFAULT_DISCORD_APPLICATION_ID") or "",
        "discord_public_key": env.get("WEB_DEFAULT_DISCORD_PUBLIC_KEY") or "",
        "discord_bot_token": env.get("WEB_DEFAULT_DISCORD_BOT_TOKEN") or "",
        "discord_channel_id": env.get("WEB_DEFAULT_DISCORD_CHANNEL_ID") or "",
        "discord_user_id_choices": _parse_user_id_choices(env.get("WEB_DISCORD_USER_ID_CHOICES_CSV") or ""),
    }


def main() -> int:
    logging.basicConfig(level=logging.INFO)
    # NOTE: 0.0.0.0 で待ち受けます。 127.0.0.1 だとコンテナの外 (ホストのブラウザ) から届きません。
    uvicorn.run(app, host="0.0.0.0", port=8000)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
