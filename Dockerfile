# NOTE: critical_high_vulnerabilities の警告が出ているけど……
#       なんかどのイメージも同じ感じなのでしょうがない。
FROM python:3.14.5-slim-trixie

RUN pip install --no-cache-dir pipenv

WORKDIR /app

# コンテナ内では仮想環境をプロジェクト直下に作ります
ENV PIPENV_VENV_IN_PROJECT=1

# Pipfile.lock があれば依存をインストールします (ソースはマウントで入る)
# NOTE: 開発の最初期は Pipfile 無いからコメントアウトしてコンテナ作ってよね。
COPY Pipfile Pipfile.lock* ./
RUN if [ -f Pipfile.lock ]; then pipenv sync --dev; fi
