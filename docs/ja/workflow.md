# ワークフロー

gospelo-test-runner + KATA Markdown を使ったテストの全体ワークフロー。

---

## 全体ワークフロー

```mermaid
flowchart TB
    subgraph Phase1["Phase 1: 設計"]
        design["テスト設計"]
        kata_spec["KATA テンプレート<br/>テスト仕様"]
        yml["api_test_data.yml<br/>テストケース定義"]
        spec_md["テスト仕様書 (.md)<br/>人間可読ドキュメント"]
    end

    subgraph Phase2["Phase 2: 実装"]
        script["run_test.py<br/>カスタム Executor (必要な場合)"]
        config["config.yml<br/>接続情報"]
    end

    subgraph Phase3["Phase 3: 実行"]
        dry["ドライラン<br/>--dry-run"]
        run["テスト実行<br/>gospelo-test-runner run"]
    end

    subgraph Phase4["Phase 4: レポート"]
        evidence["evidence_*.json<br/>evidence_*.log"]
        kata_report["KATA テンプレート<br/>テスト結果レポート"]
        report["テスト結果<br/>レポート (.md)"]
    end

    design --> kata_spec
    kata_spec --> yml
    kata_spec --> spec_md
    yml --> dry
    script --> dry
    config --> dry
    dry -->|確認OK| run
    run --> evidence
    evidence --> kata_report
    kata_report --> report

    style Phase1 fill:#E8E8E8,stroke:#5B8DB8
    style Phase2 fill:#E8E8E8,stroke:#8A8A8A
    style Phase3 fill:#5B8DB8,stroke:#2C2C2C,color:#fff
    style Phase4 fill:#4CAF50,stroke:#2C2C2C,color:#fff
```

---

## テスト実行フロー（内部詳細）

```mermaid
sequenceDiagram
    participant CLI as cli.py
    participant CL as config_loader
    participant SL as spec_loader
    participant R as runner
    participant LR as LogReporter
    participant E as Executor
    participant JR as JsonReporter

    CLI->>CL: load_config(path)
    CL-->>CLI: config dict

    alt --spec-yml
        CLI->>SL: load_spec_yml(path)
    else --spec-json
        CLI->>SL: load_spec_json(path)
    end
    SL-->>CLI: (suite_name, prefix, {category: TestCase[]})

    CLI->>R: run_suite(config, cases, executor)
    R->>LR: start()
    LR-->>R: log_path

    R->>E: setup()
    loop テストケースごと
        R->>E: execute(case, dry_run)
        E-->>R: TestResult
        R->>R: print_result() [カラー出力]
    end
    R->>E: teardown()
    R->>R: _print_summary() [カラー出力]

    R->>LR: stop()
    R->>JR: write(results)
    JR-->>R: evidence_*.json

    R-->>CLI: TestResult[]
```

---

## Phase 1: テスト設計

KATA Markdown テンプレートを使ってテスト仕様を定義する。

```mermaid
flowchart LR
    template["KATA テンプレート<br/>(テスト仕様)"] --> data["YAML データ<br/>api_test_data.yml"]
    data --> render["gospelo-kata<br/>render"]
    render --> doc["テスト仕様書<br/>(Markdown)"]
    data --> runner["テスト実行<br/>(Phase 3 で使用)"]

    style template fill:#E8E8E8,stroke:#5B8DB8
    style data fill:#E8943A,stroke:#2C2C2C,color:#fff
    style doc fill:#E8E8E8,stroke:#8A8A8A
    style runner fill:#5B8DB8,stroke:#2C2C2C,color:#fff
```

```bash
# テンプレートからデータファイルを作成
gospelo-kata assemble --type api_test --data templates/api_test_data.yml

# テスト仕様書をレンダリング
gospelo-kata render outputs/api_test_spec.kata.md --output outputs/api_test_spec.md
gospelo-kata lint outputs/api_test_spec.md
```

**ポイント:** `api_test_data.yml` がテスト仕様書（人間用）とテスト実行（自動化用）の**Single Source of Truth**。

---

## Phase 2: テスト実装

### A: YAML のみ（HttpExecutor で十分な場合）

```
templates/api_test_data.yml  →  gospelo-test-runner run --spec-yml ...
```

追加のコードは不要。YAML に定義されたエンドポイント、メソッド、期待ステータスで自動テスト。

### B: カスタム Executor（複雑なテストロジックが必要な場合）

```python
# run_test.py
from gospelo_test_runner import (
    TestCase, TestResult, TestStatus, TestSuiteConfig,
    BaseExecutor, run_suite, load_config,
)

class MyExecutor(BaseExecutor):
    def execute(self, case, dry_run=False):
        # テスト固有のロジック
        ...
        return TestResult(test_id=case.test_id, status=..., message=...)

if __name__ == "__main__":
    cases = build_test_cases()
    config = load_config("config.yml")
    suite_config = TestSuiteConfig(test_name="My Test", ...)
    executor = MyExecutor(suite_config)
    results = run_suite(suite_config, cases, executor)
```

---

## Phase 3: テスト実行

```mermaid
flowchart LR
    subgraph Pre["事前確認"]
        list["--list<br/>テスト一覧"]
        dry["--dry-run<br/>ドライラン"]
    end

    subgraph Run["実行"]
        full["全件実行"]
        filter_cat["--category<br/>カテゴリ絞込"]
        filter_id["--test-id<br/>ID 絞込"]
    end

    subgraph Out["出力"]
        stdout["stdout<br/>[OK] [NG] カラー表示"]
        json_ev["evidence_*.json"]
        log_ev["evidence_*.log"]
    end

    list --> dry
    dry -->|確認OK| full
    dry -->|部分実行| filter_cat
    dry -->|部分実行| filter_id
    full --> Out
    filter_cat --> Out
    filter_id --> Out

    style Pre fill:#E8E8E8,stroke:#8A8A8A
    style Run fill:#5B8DB8,stroke:#2C2C2C,color:#fff
    style Out fill:#E8943A,stroke:#2C2C2C,color:#fff
```

```bash
# Step 1: テスト一覧確認
gospelo-test-runner run --spec-yml templates/api_test_data.yml --list

# Step 2: ドライラン
gospelo-test-runner run --spec-yml templates/api_test_data.yml -c config.yml --dry-run

# Step 3: 本番実行
gospelo-test-runner run --spec-yml templates/api_test_data.yml -c config.yml

# 部分実行 (カテゴリ)
gospelo-test-runner run --spec-yml templates/api_test_data.yml -c config.yml \
  --category "Aurora SQL"

# 部分実行 (テストID)
gospelo-test-runner run --spec-yml templates/api_test_data.yml -c config.yml \
  --test-id SI-SQL-01
```

### 実行時の出力（カラー対応）

```
============================================================
  SQLインジェクション / NoSQLインジェクション
  2026-03-23 12:00:00
  Cases: 63 / 63
============================================================

--- Aurora SQLインジェクション ---
  [OK] SI-SQL-01: ベクトル検索 - シングルクォート
  [OK] SI-SQL-02: ベクトル検索 - UNION SELECT
  [NG] SI-SQL-03: ベクトル検索 - タイムベース

============================================================
  Results: 63 total
    [OK] OK: 60
    [NG] NG: 2
    [!!] ERROR: 1
============================================================
```

TTY 出力時に自動でカラー表示。パイプ/リダイレクト時は自動で無効化。

---

## Phase 4: レポート生成

```mermaid
flowchart LR
    json_ev["evidence_*.json"] --> kata_tpl["KATA テンプレート<br/>(テスト結果レポート)"]
    spec_json["test_spec.json"] --> kata_tpl
    kata_tpl --> render["gospelo-kata render"]
    render --> report["テスト結果レポート<br/>(.md)"]
    render --> lint["gospelo-kata lint"]

    style json_ev fill:#E8943A,stroke:#2C2C2C,color:#fff
    style kata_tpl fill:#E8E8E8,stroke:#5B8DB8
    style report fill:#4CAF50,stroke:#2C2C2C,color:#fff
```

```bash
# テスト仕様をJSON形式でエクスポート (レポート生成用)
gospelo-test-runner run --spec-yml templates/api_test_data.yml --export-spec

# KATA テンプレートでレポート生成
gospelo-kata assemble --type test_report \
  --data logs/evidence_20260323_120000.json \
  --output outputs/test_report.kata.md

gospelo-kata render outputs/test_report.kata.md --output outputs/test_report.md
gospelo-kata lint outputs/test_report.md
```

---

## テストスイートのディレクトリ構成

```
tests/{test_id_prefix}/
├── scripts/
│   └── run_test.py              # テスト実行スクリプト
├── templates/
│   ├── api_test_data.yml        # テストケース定義 (YAML)
│   ├── test_spec_data.yml       # テスト仕様データ (KATA 用)
│   └── test_prereq_data.yml     # 前提条件データ (KATA 用)
├── outputs/
│   ├── test_spec.md             # レンダリング済みテスト仕様書
│   ├── test_spec.json           # エクスポート済みテスト仕様 JSON
│   └── test_report.md           # テスト結果レポート
└── logs/
    ├── evidence_*.json          # テスト結果 JSON
    └── evidence_*.log           # テスト実行ログ
```

---

## Docker でのワークフロー

```mermaid
sequenceDiagram
    participant Dev as 開発者 (Host)
    participant Docker as Docker コンテナ
    participant API as テスト対象 API

    Dev->>Dev: テスト設計 (KATA + YAML)
    Dev->>Docker: docker run (mount: yml, config, scripts)
    Docker->>Docker: pip install gospelo-test-runner
    Docker->>API: テスト実行
    API-->>Docker: レスポンス
    Docker-->>Dev: evidence_*.json (mount 経由)
    Dev->>Dev: KATA でレポート生成
```

```bash
# ビルド
docker build -t test-runner .

# 実行
docker run --rm \
  -v $(pwd)/templates:/tests/templates:ro \
  -v $(pwd)/scripts:/tests/scripts:ro \
  -v $(pwd)/config.yml:/tests/config.yml:ro \
  -v $(pwd)/logs:/tests/logs \
  test-runner \
  run --spec-yml templates/api_test_data.yml -c config.yml
```
