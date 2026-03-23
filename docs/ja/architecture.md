# アーキテクチャ

gospelo-test-runner のパッケージ構成と内部設計。

---

## パッケージ構成

```
gospelo_test_runner/
├── types.py            # TestCase, TestResult, TestSuiteConfig, TestStatus
├── cli.py              # CLI: run / version
├── runner.py           # テスト実行オーケストレーション
├── version.py          # バージョン情報、生成物スタンプ
├── executor/           # テスト実行エンジン (プラグイン)
│   ├── base.py         #   BaseExecutor (ABC)
│   ├── registry.py     #   entry_points プラグイン発見
│   ├── http_executor.py    # HTTP リクエスト実行
│   ├── process_executor.py # サブプロセス実行
│   └── assert_executor.py  # アサーション実行
├── loader/             # 入力データ読み込み
│   ├── config_loader.py    # YAML/JSON 設定ファイル
│   └── spec_loader.py     # テスト仕様 JSON/YAML
└── reporter/           # 出力・レポート生成
    ├── json_reporter.py    # evidence_*.json
    ├── log_reporter.py     # evidence_*.log (stdout キャプチャ)
    └── spec_exporter.py    # TestCase → test_spec.json
```

---

## レイヤー構成

```mermaid
graph TB
    subgraph CLI["CLI / Python Script"]
        cli["cli.py / run_test.py"]
    end

    subgraph Core["実行コア"]
        runner["runner.py<br/>run_suite() / run_tests()"]
    end

    subgraph Input["入力"]
        config["config_loader<br/>YAML/JSON → dict"]
        spec["spec_loader<br/>JSON/YAML → TestCase[]"]
    end

    subgraph Executor["Executor Layer"]
        base["BaseExecutor (ABC)"]
        http["HttpExecutor"]
        process["ProcessExecutor"]
        assert_ex["AssertExecutor"]
        custom["CustomExecutor<br/>(プラグイン)"]
    end

    subgraph Output["出力"]
        json_r["JsonReporter<br/>evidence_*.json"]
        log_r["LogReporter<br/>evidence_*.log"]
        spec_ex["SpecExporter<br/>test_spec.json"]
    end

    subgraph Data["データモデル (types.py)"]
        tc["TestCase"]
        tr["TestResult"]
        ts["TestStatus<br/>OK / NG / ERROR / INFO / SKIP"]
        tsc["TestSuiteConfig"]
    end

    cli --> config
    cli --> spec
    cli --> runner
    runner --> base
    base --> http
    base --> process
    base --> assert_ex
    base -.-> custom
    runner --> json_r
    runner --> log_r
    cli --> spec_ex

    style CLI fill:#5B8DB8,stroke:#2C2C2C,color:#fff
    style Core fill:#E8943A,stroke:#2C2C2C,color:#fff
    style Input fill:#E8E8E8,stroke:#5B8DB8
    style Executor fill:#E8E8E8,stroke:#5B8DB8
    style Output fill:#E8E8E8,stroke:#5B8DB8
    style Data fill:#F5F5F5,stroke:#8A8A8A
```

---

## Executor プラグインシステム

```mermaid
classDiagram
    class BaseExecutor {
        <<abstract>>
        +suite_config: TestSuiteConfig
        +execute(case, dry_run)* TestResult
        +setup() void
        +teardown() void
        +get_dry_run_info(case) dict
    }

    class HttpExecutor {
        +execute(case, dry_run) TestResult
        urllib.request による HTTP 通信
    }

    class ProcessExecutor {
        +execute(case, dry_run) TestResult
        subprocess.run による外部コマンド
    }

    class AssertExecutor {
        +execute(case, dry_run) TestResult
        params 内のアサーション評価
    }

    class CustomExecutor {
        <<plugin>>
        +execute(case, dry_run) TestResult
        run_test.py 内で定義
    }

    BaseExecutor <|-- HttpExecutor
    BaseExecutor <|-- ProcessExecutor
    BaseExecutor <|-- AssertExecutor
    BaseExecutor <|.. CustomExecutor
```

組み込み Executor は `entry_points` で登録されており、外部プラグインと同じ仕組みで発見される：

```toml
# pyproject.toml
[project.entry-points."gospelo_test_runner.executors"]
http = "gospelo_test_runner.executor.http_executor:HttpExecutor"
process = "gospelo_test_runner.executor.process_executor:ProcessExecutor"
assert = "gospelo_test_runner.executor.assert_executor:AssertExecutor"
```

`run_test.py` 内で `BaseExecutor` を継承したカスタム Executor を定義するパターンも一般的。

---

## データモデル

```mermaid
classDiagram
    class TestCase {
        +test_id: str
        +category: str
        +description: str
        +test_type: str
        +expected_result: str
        +params: dict
    }

    class TestResult {
        +test_id: str
        +status: TestStatus
        +message: str
        +details: dict
        +evidence: dict
    }

    class TestStatus {
        <<enumeration>>
        OK
        NG
        ERROR
        INFO
        SKIP
    }

    class TestSuiteConfig {
        +test_name: str
        +test_id_prefix: str
        +config: dict
        +output_dir: str
        +dry_run: bool
        +delay: float
        +test_id_filter: str
        +category_filter: str
    }

    TestResult --> TestStatus
    TestCase ..> TestResult : "Executor.execute()"
    TestSuiteConfig ..> TestCase : "filters"
```

---

## 入力フォーマット

### テスト仕様 YAML (`--spec-yml`)

```yaml
suite_name: "テスト名"
base_url: "https://api.example.com"
test_cases:
  - test_id: "XX-01"
    category: "カテゴリ"
    description: "テスト内容"
    method: GET
    endpoint: /api/endpoint
    headers: {}
    params: {}
    body: {}
    expected_status: 400
    expected_body_contains: []
    tags: [tag1]
    priority: medium
    status: draft
```

### テスト仕様 JSON (`--spec-json`)

```json
{
  "test_name": "テスト名",
  "test_id_prefix": "XX",
  "cases": [
    {
      "id": "XX-01",
      "group": "カテゴリ",
      "input": "テスト内容",
      "method": "GET",
      "expected": "期待結果"
    }
  ]
}
```

---

## 出力フォーマット

| ファイル | 生成元 | 内容 |
|---------|-------|------|
| `evidence_*.json` | JsonReporter | テスト結果 (meta + results) |
| `evidence_*.log` | LogReporter | 実行ログ (stdout キャプチャ) |
| `test_spec.json` | SpecExporter | テスト仕様書 (TestCase → JSON) |

---

## 依存関係

- **必須**: Python 3.11+, `pyyaml>=6.0`
- **外部ライブラリ不要**: HTTP 通信は `urllib.request` を使用
