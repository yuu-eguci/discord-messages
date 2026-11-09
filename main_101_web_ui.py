import asyncio
import json
import logging
import os
import sys
from collections.abc import AsyncIterator
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Self

import uvicorn

# NOTE: pipenv は自動で .env を読むので、機能的には dotenv は不要。
#       ただし pipenv が .env を読むタイミングはプロセスを起動したとき。
#       dotenv であれば、リアルタイムで .env を変更できる良さがあるので、今回は採用。
from dotenv import dotenv_values
from fastapi import FastAPI, HTTPException
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, model_validator

logger = logging.getLogger(__name__)

INDEX_HTML_PATH = Path(__file__).parent / "main_101_web_ui.html"
ENV_PATH = Path(__file__).parent / ".env"

SCRIPT_001 = "main_001_discord_to_jsonl.py"
SCRIPT_002 = "main_002_rawjsonl_to_parsedjsonl.py"
SCRIPT_003 = "main_003_parsedjsonl_to_anotherformat.py"

# 各スクリプトのデフォルト出力先。次のスクリプトの --input への橋渡しに使います。
OUTPUT_001 = "output/main_001_discord_to_jsonl.jsonl"
OUTPUT_002 = "output/main_002_rawjsonl_to_parsedjsonl.jsonl"

# NOTE: FastAPI の読み方は……
#       @app.get とか @app.post がルーティング定義なので、そこを見ていく。
app = FastAPI()
# GET /api/defaults は bot token を返すので、 Host が localhost / 127.0.0.1 以外のリクエストは 400 で拒否します。
# (悪意のあるサイトが DNS rebinding で、ブラウザ経由でこの API を読むのを防ぐため。)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["localhost", "127.0.0.1"])


@app.get("/")
async def index() -> FileResponse:
    """
    まずは GET /
    Web UI のページ (html 1 枚) を返します。
    """
    return FileResponse(INDEX_HTML_PATH)


@app.get("/api/defaults")
async def defaults() -> dict[str, object]:
    """
    次に GET /api/defaults
    index.html を開いた直後に、フォームの初期値を取得するための API です。
    ただの便利機能。
    """
    env = dotenv_values(ENV_PATH)
    return {
        "discord_bot_token": env.get("WEB_DEFAULT_DISCORD_BOT_TOKEN") or "",
        "discord_channel_id": env.get("WEB_DEFAULT_DISCORD_CHANNEL_ID") or "",
        "discord_user_id_choices": _parse_user_id_choices(env.get("WEB_DISCORD_USER_ID_CHOICES_CSV") or ""),
    }


def _parse_user_id_choices(raw: str) -> list[dict[str, str]]:
    """
    "noctis:12345,seraphina:67890" 形式の文字列を、セレクトボックスの選択肢リストにパースします。
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


class RunRequest(BaseModel):
    """
    POST /api/run のリクエストボディです。
    各フィールドは main scripts 001〜003 のコマンドライン引数に対応します。
    """

    discord_bot_token: str | None = None
    discord_channel_id: int | None = None
    discord_user_id: int | None = None
    date_from: str | None = None
    limit: int | None = None
    format: Literal["anki", "fancyhtml"] = "anki"
    dry_run: bool = False

    @model_validator(mode="after")
    def _require_discord_args_unless_dry_run(self) -> Self:
        """
        mode="before" 各フィールドに型を適用する前。 dict が渡ってくる。
        mode="after" self の中に型付きの値が入ってくる。
        そもそも型チェックでおかしかったらどーなんの? --> ここに来る前にすでに 422 で返る。

        本実行のときだけ、 Discord まわりの必須引数が揃っているか検証します。
        (dry run は UI のテスト用なので、空っぽでも通します。)
        """
        if self.dry_run:
            return self
        required = ("discord_bot_token", "discord_channel_id")
        missing = [name for name in required if getattr(self, name) in (None, "")]
        if missing:
            raise ValueError(f"dry run でないなら必須だよ: {', '.join(missing)}")
        return self


@app.post("/api/run")
async def run(request: RunRequest) -> dict[str, bool]:
    """
    POST /api/run
    ジョブ (script 001 → 002 → 003) を開始します。進捗は GET /api/events の SSE で流れます。
    """
    # 【この関数読む前に coroutine を知っとけ】
    # coroutine は「誰かに駆動されるまでただの遅延オブジェクト」である。
    # coroutine が駆動されるのは……
    # - await されたとき (こいつはグローバルスコープに書けない)
    # - asyncio.run されたとき (こいつがグローバルスコープに書けて、 async 処理を「始める者」!)
    # - asyncio.create_task で「スケジュール」されて、さらに「イベントループ」で順番が来たとき

    # dataclass Job です。 GET /api/events と POST /api/run で共有するので、グローバル変数に置いています。
    global _current_job

    # asyncio.Task の done() から、「もうタスク終わった?」ってのを聞いている。
    # どうやってタスクのスタートをエンドが決まるの? って思うと思うけど、それは下を見て。
    if _current_job is not None and not _current_job.task.done():
        raise HTTPException(status_code=409, detail="ジョブが既に実行中だよ。")

    # このキューはタスクを入れるものじゃなくて、 _run_job の中で dict を積むためのもの。
    # GET /api/events のほうで dict を取り出して SSE で流すのに使います。
    queue: asyncio.Queue = asyncio.Queue()

    # 上でおさらいしたスケジュールされてイベントループで順番が来たとき (関数の return 後) 実行されるやつ。
    task = asyncio.create_task(_run_job(request, queue))

    _current_job = Job(queue=queue, task=task)

    # 画面へ JSON を返す。
    # JSONResponse を使ってもいいんだけど、 FastAPI はそこ自動なんだってさ。
    return {"started": True}


@dataclass
class Job:
    """
    実行中 (または実行済み) のジョブです。 queue には SSE で流すイベントが積まれます。
    """

    queue: asyncio.Queue
    task: asyncio.Task


# 一人用ツールなので、ジョブは同時に 1 個だけ、というシンプルな作りにしています。
# NOTE: これはシングルトンではない。シングルトンは、何回インスタンスを new しても同じオブジェクトが返るやつね。
#       このプログラムでは run ごとに新しい Job インスタンスを作らないといけないっしょ?
_current_job: Job | None = None


async def _run_job(request: RunRequest, queue: asyncio.Queue) -> None:
    """
    ジョブ全体を実行して、最後に done か error のイベントを積みます。
    """
    try:
        if request.dry_run:
            await _run_dry(queue)
        else:
            await _run_real(request, queue)
    except Exception as exception:
        logger.exception("ジョブが失敗した。")
        await queue.put({"type": "error", "message": str(exception)})
    else:
        await queue.put({"type": "done"})


async def _run_dry(queue: asyncio.Queue) -> None:
    """
    UI テスト用のドライランです。 subprocess の代わりに sleep しながら、本物と同じ形のイベントを流します。
    """
    fake_logs = [
        (
            SCRIPT_001,
            ["Discord にログインしたつもり。", "メッセージを 42 件取得したつもり。", f"出力ファイル: {OUTPUT_001}"],
        ),
        (SCRIPT_002, ["42 件パースしたつもり。", f"出力ファイル: {OUTPUT_002}"]),
        (SCRIPT_003, ["フォーマットしたつもり。", "出力ファイル: output/(dry run なので何も書いてないよ)"]),
    ]
    for step, (script, lines) in enumerate(fake_logs, start=1):
        await queue.put({"type": "step_start", "step": step, "script": script})
        for line in lines:
            await asyncio.sleep(0.6)
            await queue.put({"type": "log", "step": step, "line": f"[dry run] {line}"})
        await queue.put({"type": "step_end", "step": step, "script": script})


async def _run_real(request: RunRequest, queue: asyncio.Queue) -> None:
    """
    script 001 → 002 → 003 を順番に subprocess で実行します。
    """
    env = _build_env(request)
    for step, (script, command) in enumerate(_build_commands(request), start=1):
        await _run_script(queue, step, script, command, env)


def _build_env(request: RunRequest) -> dict[str, str]:
    """
    サブプロセスの環境変数です。 bot token は引数ではなくここで渡します。 (プロセス一覧に出さないため。)
    """
    return {**os.environ, "DISCORD_BOT_TOKEN": str(request.discord_bot_token)}


def _build_commands(request: RunRequest) -> list[tuple[str, list[str]]]:
    """
    001 → 002 → 003 のコマンドを組み立てます。各スクリプトのデフォルト出力先を次の --input に橋渡しします。
    """
    command_001 = [
        sys.executable,
        SCRIPT_001,
        "--discord-channel-id",
        str(request.discord_channel_id),
    ]
    if request.discord_user_id is not None:
        command_001 += ["--discord-user-id", str(request.discord_user_id)]
    if request.date_from:
        command_001 += ["--date-from", request.date_from]
    if request.limit is not None:
        command_001 += ["--limit", str(request.limit)]

    command_002 = [sys.executable, SCRIPT_002, "--input", OUTPUT_001]
    command_003 = [sys.executable, SCRIPT_003, "--input", OUTPUT_002, "--format", request.format]

    return [(SCRIPT_001, command_001), (SCRIPT_002, command_002), (SCRIPT_003, command_003)]


async def _run_script(queue: asyncio.Queue, step: int, script: str, command: list[str], env: dict[str, str]) -> None:
    """
    スクリプトを 1 本実行して、出力を一行ずつイベントとして queue に積みます。
    NOTE: イベントに env は入れません。 bot token などの秘密情報が SSE に漏れてしまうので。
    """
    await queue.put({"type": "step_start", "step": step, "script": script})
    process = await asyncio.create_subprocess_exec(
        *command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
        env=env,
    )
    assert process.stdout is not None
    while line := await process.stdout.readline():
        await queue.put({"type": "log", "step": step, "line": line.decode(errors="replace").rstrip()})
    exit_code = await process.wait()
    if exit_code != 0:
        raise RuntimeError(f"{script} が exit code {exit_code} で失敗した。")
    await queue.put({"type": "step_end", "step": step, "script": script})


@app.get("/api/events")
async def events() -> StreamingResponse:
    """
    GET /api/events
    実行中のジョブの進捗イベントを SSE で流します。 done か error を流したら接続を閉じます。
    """
    if _current_job is None:
        raise HTTPException(status_code=404, detail="ジョブがまだ開始されてないよ。")

    # グローバル変数のほうは POST /api/run の中でいつ変わるとも分からない。
    # なのでこの時点での Job インスタンスの参照を握っておきます。
    job = _current_job

    async def stream() -> AsyncIterator[str]:
        while True:
            # queue に次のモノが put されるまで止まってるやつ。
            event = await job.queue.get()
            # SSE の形式は「data: (中身)」+ 空行。これだけで動く素朴なプロトコルです。
            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
            if event["type"] in ("done", "error"):
                return

    return StreamingResponse(stream(), media_type="text/event-stream")


@app.post("/api/shutdown")
async def shutdown() -> dict[str, bool]:
    """
    POST /api/shutdown
    サーバー自身を終了します。 run --rm で起動していれば、コンテナごと消えて終わりです。
    """
    if _server is None:
        raise HTTPException(status_code=500, detail="サーバーの参照が無い。 main() 以外から起動された?")
    # should_exit を立てると、 uvicorn はこのレスポンスを返し終えたあと、行儀よく終了してくれます。
    _server.should_exit = True
    return {"bye": True}


# shutdown エンドポイントから uvicorn を止めるために、 Server インスタンスをグローバルに握っておきます。
# NOTE: uvicorn.run(app) はお手軽だけど、 Server を内部で作って隠しちゃうので、外から止められません。
_server: uvicorn.Server | None = None


def main() -> int:
    global _server
    logging.basicConfig(level=logging.INFO)
    # NOTE: 0.0.0.0 で待ち受けます。 127.0.0.1 だとコンテナの外 (ホストのブラウザ) から届きません。
    config = uvicorn.Config(app, host="0.0.0.0", port=8000)
    _server = uvicorn.Server(config)
    _server.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
