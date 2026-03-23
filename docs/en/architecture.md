# Architecture

Package structure and internal design of gospelo-test-runner.

---

## Package Structure

```
gospelo_test_runner/
├── types.py            # TestCase, TestResult, TestSuiteConfig, TestStatus
├── cli.py              # CLI: run / version
├── runner.py           # Test execution orchestration
├── version.py          # Version info, artifact stamps
├── executor/           # Test execution engines (plugins)
│   ├── base.py         #   BaseExecutor (ABC)
│   ├── registry.py     #   entry_points plugin discovery
│   ├── http_executor.py    # HTTP request execution
│   ├── process_executor.py # Subprocess execution
│   └── assert_executor.py  # Assertion execution
├── loader/             # Input data loading
│   ├── config_loader.py    # YAML/JSON config files
│   └── spec_loader.py     # Test spec JSON/YAML
└── reporter/           # Output & report generation
    ├── json_reporter.py    # evidence_*.json
    ├── log_reporter.py     # evidence_*.log (stdout capture)
    └── spec_exporter.py    # TestCase → test_spec.json
```

---

## Layer Architecture

```mermaid
graph TB
    subgraph CLI["CLI / Python Script"]
        cli["cli.py / run_test.py"]
    end

    subgraph Core["Execution Core"]
        runner["runner.py<br/>run_suite() / run_tests()"]
    end

    subgraph Input["Input"]
        config["config_loader<br/>YAML/JSON → dict"]
        spec["spec_loader<br/>JSON/YAML → TestCase[]"]
    end

    subgraph Executor["Executor Layer"]
        base["BaseExecutor (ABC)"]
        http["HttpExecutor"]
        process["ProcessExecutor"]
        assert_ex["AssertExecutor"]
        custom["CustomExecutor<br/>(Plugin)"]
    end

    subgraph Output["Output"]
        json_r["JsonReporter<br/>evidence_*.json"]
        log_r["LogReporter<br/>evidence_*.log"]
        spec_ex["SpecExporter<br/>test_spec.json"]
    end

    subgraph Data["Data Model (types.py)"]
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

## Executor Plugin System

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
        HTTP via urllib.request
    }

    class ProcessExecutor {
        +execute(case, dry_run) TestResult
        External commands via subprocess.run
    }

    class AssertExecutor {
        +execute(case, dry_run) TestResult
        Assertion evaluation within params
    }

    class CustomExecutor {
        <<plugin>>
        +execute(case, dry_run) TestResult
        Defined in run_test.py
    }

    BaseExecutor <|-- HttpExecutor
    BaseExecutor <|-- ProcessExecutor
    BaseExecutor <|-- AssertExecutor
    BaseExecutor <|.. CustomExecutor
```

Built-in executors are registered via `entry_points` and discovered using the same mechanism as external plugins:

```toml
# pyproject.toml
[project.entry-points."gospelo_test_runner.executors"]
http = "gospelo_test_runner.executor.http_executor:HttpExecutor"
process = "gospelo_test_runner.executor.process_executor:ProcessExecutor"
assert = "gospelo_test_runner.executor.assert_executor:AssertExecutor"
```

Defining a custom executor by subclassing `BaseExecutor` in `run_test.py` is also a common pattern.

---

## Data Model

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

## Input Formats

### Test Spec YAML (`--spec-yml`)

```yaml
suite_name: "Test Name"
base_url: "https://api.example.com"
test_cases:
  - test_id: "XX-01"
    category: "Category"
    description: "Test description"
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

### Test Spec JSON (`--spec-json`)

```json
{
  "test_name": "Test Name",
  "test_id_prefix": "XX",
  "cases": [
    {
      "id": "XX-01",
      "group": "Category",
      "input": "Test description",
      "method": "GET",
      "expected": "Expected result"
    }
  ]
}
```

---

## Output Formats

| File | Generator | Contents |
|------|-----------|----------|
| `evidence_*.json` | JsonReporter | Test results (meta + results) |
| `evidence_*.log` | LogReporter | Execution log (stdout capture) |
| `test_spec.json` | SpecExporter | Test specification (TestCase → JSON) |

---

## Dependencies

- **Required**: Python 3.11+, `pyyaml>=6.0`
- **No external libraries needed**: HTTP communication uses `urllib.request`
