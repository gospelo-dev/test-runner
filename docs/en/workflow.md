# Workflow

End-to-end testing workflow using gospelo-test-runner + KATA Markdown.

---

## Overall Workflow

```mermaid
flowchart TB
    subgraph Phase1["Phase 1: Design"]
        design["Test design"]
        kata_spec["KATA template<br/>Test specification"]
        yml["api_test_data.yml<br/>Test case definitions"]
        spec_md["Test spec (.md)<br/>Human-readable document"]
    end

    subgraph Phase2["Phase 2: Implementation"]
        script["run_test.py<br/>Custom Executor (if needed)"]
        config["config.yml<br/>Connection info"]
    end

    subgraph Phase3["Phase 3: Execution"]
        dry["Dry run<br/>--dry-run"]
        run["Test execution<br/>gospelo-test-runner run"]
    end

    subgraph Phase4["Phase 4: Reporting"]
        evidence["evidence_*.json<br/>evidence_*.log"]
        kata_report["KATA template<br/>Test result report"]
        report["Test result<br/>report (.md)"]
    end

    design --> kata_spec
    kata_spec --> yml
    kata_spec --> spec_md
    yml --> dry
    script --> dry
    config --> dry
    dry -->|Verified OK| run
    run --> evidence
    evidence --> kata_report
    kata_report --> report

    style Phase1 fill:#E8E8E8,stroke:#5B8DB8
    style Phase2 fill:#E8E8E8,stroke:#8A8A8A
    style Phase3 fill:#5B8DB8,stroke:#2C2C2C,color:#fff
    style Phase4 fill:#4CAF50,stroke:#2C2C2C,color:#fff
```

---

## Test Execution Flow (Internal Details)

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
    loop For each test case
        R->>E: execute(case, dry_run)
        E-->>R: TestResult
        R->>R: print_result() [color output]
    end
    R->>E: teardown()
    R->>R: _print_summary() [color output]

    R->>LR: stop()
    R->>JR: write(results)
    JR-->>R: evidence_*.json

    R-->>CLI: TestResult[]
```

---

## Phase 1: Test Design

Define test specifications using KATA Markdown templates.

```mermaid
flowchart LR
    template["KATA template<br/>(Test spec)"] --> data["YAML data<br/>api_test_data.yml"]
    data --> render["gospelo-kata<br/>render"]
    render --> doc["Test spec<br/>(Markdown)"]
    data --> runner["Test execution<br/>(Used in Phase 3)"]

    style template fill:#E8E8E8,stroke:#5B8DB8
    style data fill:#E8943A,stroke:#2C2C2C,color:#fff
    style doc fill:#E8E8E8,stroke:#8A8A8A
    style runner fill:#5B8DB8,stroke:#2C2C2C,color:#fff
```

```bash
# Create data file from template
gospelo-kata assemble --type api_test --data templates/api_test_data.yml

# Render test specification
gospelo-kata render outputs/api_test_spec.kata.md --output outputs/api_test_spec.md
gospelo-kata lint outputs/api_test_spec.md
```

**Key point:** `api_test_data.yml` serves as the **Single Source of Truth** for both the test specification (for humans) and test execution (for automation).

---

## Phase 2: Test Implementation

### A: YAML Only (when HttpExecutor is sufficient)

```
templates/api_test_data.yml  →  gospelo-test-runner run --spec-yml ...
```

No additional code required. Automated testing using endpoints, methods, and expected statuses defined in YAML.

### B: Custom Executor (when complex test logic is needed)

```python
# run_test.py
from gospelo_test_runner import (
    TestCase, TestResult, TestStatus, TestSuiteConfig,
    BaseExecutor, run_suite, load_config,
)

class MyExecutor(BaseExecutor):
    def execute(self, case, dry_run=False):
        # Test-specific logic
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

## Phase 3: Test Execution

```mermaid
flowchart LR
    subgraph Pre["Pre-check"]
        list["--list<br/>List test cases"]
        dry["--dry-run<br/>Dry run"]
    end

    subgraph Run["Execution"]
        full["Full execution"]
        filter_cat["--category<br/>Filter by category"]
        filter_id["--test-id<br/>Filter by ID"]
    end

    subgraph Out["Output"]
        stdout["stdout<br/>[OK] [NG] Color display"]
        json_ev["evidence_*.json"]
        log_ev["evidence_*.log"]
    end

    list --> dry
    dry -->|Verified OK| full
    dry -->|Partial run| filter_cat
    dry -->|Partial run| filter_id
    full --> Out
    filter_cat --> Out
    filter_id --> Out

    style Pre fill:#E8E8E8,stroke:#8A8A8A
    style Run fill:#5B8DB8,stroke:#2C2C2C,color:#fff
    style Out fill:#E8943A,stroke:#2C2C2C,color:#fff
```

```bash
# Step 1: List test cases
gospelo-test-runner run --spec-yml templates/api_test_data.yml --list

# Step 2: Dry run
gospelo-test-runner run --spec-yml templates/api_test_data.yml -c config.yml --dry-run

# Step 3: Execute
gospelo-test-runner run --spec-yml templates/api_test_data.yml -c config.yml

# Partial execution (by category)
gospelo-test-runner run --spec-yml templates/api_test_data.yml -c config.yml \
  --category "Aurora SQL"

# Partial execution (by test ID)
gospelo-test-runner run --spec-yml templates/api_test_data.yml -c config.yml \
  --test-id SI-SQL-01
```

### Execution Output (Color Support)

```
============================================================
  SQL Injection / NoSQL Injection
  2026-03-23 12:00:00
  Cases: 63 / 63
============================================================

--- Aurora SQL Injection ---
  [OK] SI-SQL-01: Vector search - Single quote
  [OK] SI-SQL-02: Vector search - UNION SELECT
  [NG] SI-SQL-03: Vector search - Time-based

============================================================
  Results: 63 total
    [OK] OK: 60
    [NG] NG: 2
    [!!] ERROR: 1
============================================================
```

Color output is automatic on TTY. Automatically disabled when piped or redirected.

---

## Phase 4: Report Generation

```mermaid
flowchart LR
    json_ev["evidence_*.json"] --> kata_tpl["KATA template<br/>(Test result report)"]
    spec_json["test_spec.json"] --> kata_tpl
    kata_tpl --> render["gospelo-kata render"]
    render --> report["Test result report<br/>(.md)"]
    render --> lint["gospelo-kata lint"]

    style json_ev fill:#E8943A,stroke:#2C2C2C,color:#fff
    style kata_tpl fill:#E8E8E8,stroke:#5B8DB8
    style report fill:#4CAF50,stroke:#2C2C2C,color:#fff
```

```bash
# Export test spec in JSON format (for report generation)
gospelo-test-runner run --spec-yml templates/api_test_data.yml --export-spec

# Generate report with KATA template
gospelo-kata assemble --type test_report \
  --data logs/evidence_20260323_120000.json \
  --output outputs/test_report.kata.md

gospelo-kata render outputs/test_report.kata.md --output outputs/test_report.md
gospelo-kata lint outputs/test_report.md
```

---

## Test Suite Directory Structure

```
tests/{test_id_prefix}/
├── scripts/
│   └── run_test.py              # Test execution script
├── templates/
│   ├── api_test_data.yml        # Test case definitions (YAML)
│   ├── test_spec_data.yml       # Test spec data (for KATA)
│   └── test_prereq_data.yml     # Prerequisite data (for KATA)
├── outputs/
│   ├── test_spec.md             # Rendered test specification
│   ├── test_spec.json           # Exported test spec JSON
│   └── test_report.md           # Test result report
└── logs/
    ├── evidence_*.json          # Test result JSON
    └── evidence_*.log           # Test execution log
```

---

## Docker Workflow

```mermaid
sequenceDiagram
    participant Dev as Developer (Host)
    participant Docker as Docker Container
    participant API as Target API

    Dev->>Dev: Test design (KATA + YAML)
    Dev->>Docker: docker run (mount: yml, config, scripts)
    Docker->>Docker: pip install gospelo-test-runner
    Docker->>API: Execute tests
    API-->>Docker: Response
    Docker-->>Dev: evidence_*.json (via mount)
    Dev->>Dev: Generate report with KATA
```

```bash
# Build
docker build -t test-runner .

# Execute
docker run --rm \
  -v $(pwd)/templates:/tests/templates:ro \
  -v $(pwd)/scripts:/tests/scripts:ro \
  -v $(pwd)/config.yml:/tests/config.yml:ro \
  -v $(pwd)/logs:/tests/logs \
  test-runner \
  run --spec-yml templates/api_test_data.yml -c config.yml
```
