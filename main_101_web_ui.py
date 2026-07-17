import logging
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.responses import FileResponse

logger = logging.getLogger(__name__)

INDEX_HTML_PATH = Path(__file__).parent / "main_101_web_ui.html"

app = FastAPI()


@app.get("/")
async def index() -> FileResponse:
    """
    Web UI のページ (html 1 枚) を返します。
    """
    return FileResponse(INDEX_HTML_PATH)


def main() -> int:
    logging.basicConfig(level=logging.INFO)
    # NOTE: 0.0.0.0 で待ち受けます。 127.0.0.1 だとコンテナの外 (ホストのブラウザ) から届きません。
    uvicorn.run(app, host="0.0.0.0", port=8000)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
