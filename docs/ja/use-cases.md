# ユースケース

gospelo-test-runner + KATA Markdown で実現できるユースケース。

---

## ユースケース全体像

```mermaid
graph LR
    subgraph Define["テスト定義"]
        kata["KATA Markdown<br/>テスト仕様テンプレート"]
        yml["api_test_data.yml<br/>テストケース定義"]
        script["run_test.py<br/>カスタム Executor"]
    end

    subgraph Execute["テスト実行"]
        runner["gospelo-test-runner"]
    end

    subgraph Evidence["エビデンス"]
        json_ev["evidence_*.json"]
        log_ev["evidence_*.log"]
        spec_json["test_spec.json"]
    end

    subgraph Report["レポート"]
        kata_report["KATA Markdown<br/>テスト結果レポート"]
    end

    kata --> yml
    yml --> runner
    script --> runner
    runner --> json_ev
    runner --> log_ev
    runner --> spec_json
    json_ev --> kata_report
    spec_json --> kata_report

    style Define fill:#E8E8E8,stroke:#5B8DB8
    style Execute fill:#5B8DB8,stroke:#2C2C2C,color:#fff
    style Evidence fill:#E8943A,stroke:#2C2C2C,color:#fff
    style Report fill:#4CAF50,stroke:#2C2C2C,color:#fff
```

---

## UC1: API セキュリティテスト

YAML でテストケースを定義し、HTTP Executor で API に対してセキュリティテストを実行する。

```mermaid
sequenceDiagram
    participant Dev as 開発者
    participant KATA as KATA Markdown
    participant Runner as test-runner
    participant API as テスト対象 API

    Dev->>KATA: テスト仕様テンプレートからYAML生成
    KATA-->>Dev: api_test_data.yml
    Dev->>Runner: gospelo-test-runner run --spec-yml api_test_data.yml
    loop テストケースごと
        Runner->>API: HTTP リクエスト (GET/POST/PUT/DELETE)
        API-->>Runner: レスポンス (status, body)
        Runner->>Runner: 期待値と比較 → OK/NG
    end
    Runner-->>Dev: evidence_*.json + evidence_*.log
    Dev->>KATA: エビデンスからレポート生成
```

**実行例:**

```bash
# テスト一覧の確認
gospelo-test-runner run --spec-yml templates/api_test_data.yml --list

# ドライラン (リクエスト内容の確認)
gospelo-test-runner run --spec-yml templates/api_test_data.yml --dry-run

# テスト実行
gospelo-test-runner run --spec-yml templates/api_test_data.yml -c config.yml
```

---

## UC2: カスタム Executor によるテスト

`run_test.py` 内で `BaseExecutor` を継承し、テスト固有のロジックを実装する。

```mermaid
sequenceDiagram
    participant Dev as 開発者
    participant Script as run_test.py
    participant Runner as runner.py
    participant Custom as CustomExecutor
    participant Target as テスト対象

    Dev->>Script: python run_test.py -c config.yml
    Script->>Script: TestCase[] 定義
    Script->>Runner: run_suite(config, cases, executor)
    loop テストケースごと
        Runner->>Custom: execute(case)
        Custom->>Target: テスト固有のリクエスト
        Target-->>Custom: レスポンス
        Custom->>Custom: 独自の判定ロジック
        Custom-->>Runner: TestResult
    end
    Runner-->>Script: evidence_*.json + evidence_*.log
```

**適用例:**
- CSRF トークン検証（Cookie + Token の複合操作）
- レート制限テスト（連続リクエストとタイミング計測）
- セッション管理テスト（ログイン → 操作 → ログアウトのフロー）
- インフラ設定検証（SSL 証明書、HTTP ヘッダー検査）

```python
from gospelo_test_runner import BaseExecutor, TestCase, TestResult, TestStatus

class CsrfExecutor(BaseExecutor):
    def execute(self, case, dry_run=False):
        # 1. ログインして CSRF トークン取得
        # 2. トークンなし/不正トークンでリクエスト
        # 3. レスポンスを検証
        return TestResult(
            test_id=case.test_id,
            status=TestStatus.OK if rejected else TestStatus.NG,
            message="CSRF protection verified",
        )
```

---

## UC3: KATA Markdown によるテスト仕様生成

KATA Markdown テンプレートからテスト仕様 YAML を生成し、そのまま runner に投入する。

```mermaid
flowchart LR
    subgraph KATA["KATA Markdown"]
        template["テスト仕様<br/>テンプレート"]
        data["テスト仕様<br/>データ (YAML)"]
        rendered["レンダリング済み<br/>テスト仕様書 (.md)"]
    end

    subgraph Runner["test-runner"]
        spec_yml["api_test_data.yml"]
        execute["テスト実行"]
    end

    template --> data
    data --> rendered
    data --> spec_yml
    spec_yml --> execute

    style KATA fill:#E8E8E8,stroke:#5B8DB8
    style Runner fill:#5B8DB8,stroke:#2C2C2C,color:#fff
```

**ワークフロー:**

```bash
# 1. KATA テンプレートからデータファイル生成
gospelo-kata assemble --type api_test --data templates/api_test_data.yml

# 2. レンダリング (人間可読なテスト仕様書)
gospelo-kata render outputs/api_test_spec.kata.md --output outputs/api_test_spec.md

# 3. 同じ YAML でテスト実行
gospelo-test-runner run --spec-yml templates/api_test_data.yml -c config.yml
```

**ポイント:** テスト仕様書（ドキュメント）とテスト実行（自動化）が**同じデータソース**から生成される。

---

## UC4: カテゴリ / テストID による部分実行

大量のテストケースから特定のカテゴリやIDだけを実行する。

```bash
# 特定カテゴリのみ
gospelo-test-runner run --spec-yml api_test_data.yml -c config.yml \
  --category "Aurora SQL"

# 特定テストIDのみ
gospelo-test-runner run --spec-yml api_test_data.yml -c config.yml \
  --test-id SI-SQL-01

# テスト間の遅延を調整 (レート制限テスト等)
gospelo-test-runner run --spec-yml api_test_data.yml -c config.yml \
  --delay 2.0
```

---

## UC5: KATA Markdown によるエビデンスレポート生成

テスト実行結果（evidence JSON）を KATA Markdown テンプレートに流し込み、レポートを生成する。

```mermaid
flowchart LR
    evidence["evidence_*.json"]
    spec["test_spec.json"]
    template["KATA レポート<br/>テンプレート"]
    report["テスト結果<br/>レポート (.md)"]

    evidence --> template
    spec --> template
    template --> report

    style evidence fill:#E8943A,stroke:#2C2C2C,color:#fff
    style template fill:#E8E8E8,stroke:#5B8DB8
    style report fill:#4CAF50,stroke:#2C2C2C,color:#fff
```

```bash
# テスト実行後
gospelo-test-runner run --spec-yml api_test_data.yml -c config.yml
# → logs/evidence_20260323_120000.json

# エビデンスからレポート生成 (KATA)
gospelo-kata assemble --type test_report \
  --data logs/evidence_20260323_120000.json \
  --output outputs/test_report.kata.md
gospelo-kata render outputs/test_report.kata.md --output outputs/test_report.md
```

---

## UC6: Docker コンテナ内でのテスト実行

テスト実行を Docker コンテナ内に閉じ込め、再現性を確保する。

```mermaid
flowchart TB
    subgraph Host["ホスト PC"]
        yml_h["api_test_data.yml"]
        config_h["config.yml"]
        script_h["run_test.py"]
        logs_h["logs/<br/>evidence_*.json<br/>evidence_*.log"]
    end

    subgraph Docker["Docker コンテナ"]
        pip["pip install gospelo-test-runner"]
        runner_d["gospelo-test-runner run"]
    end

    yml_h -->|mount| runner_d
    config_h -->|mount| runner_d
    script_h -->|mount| runner_d
    pip --> runner_d
    runner_d -->|mount| logs_h

    style Host fill:#E8E8E8,stroke:#8A8A8A
    style Docker fill:#5B8DB8,stroke:#2C2C2C,color:#fff
```

```dockerfile
FROM python:3.12-slim
RUN pip install gospelo-test-runner
WORKDIR /tests
ENTRYPOINT ["gospelo-test-runner"]
```

```bash
docker run --rm \
  -v $(pwd)/templates:/tests/templates:ro \
  -v $(pwd)/config.yml:/tests/config.yml:ro \
  -v $(pwd)/logs:/tests/logs \
  gospelo-test-runner \
  run --spec-yml templates/api_test_data.yml -c config.yml
```
