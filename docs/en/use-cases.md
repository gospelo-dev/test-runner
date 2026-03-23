# Use Cases

Use cases achievable with gospelo-test-runner + KATA Markdown.

---

## Use Case Overview

```mermaid
graph LR
    subgraph Define["Test Definition"]
        kata["KATA Markdown<br/>Test spec template"]
        yml["api_test_data.yml<br/>Test case definitions"]
        script["run_test.py<br/>Custom Executor"]
    end

    subgraph Execute["Test Execution"]
        runner["gospelo-test-runner"]
    end

    subgraph Evidence["Evidence"]
        json_ev["evidence_*.json"]
        log_ev["evidence_*.log"]
        spec_json["test_spec.json"]
    end

    subgraph Report["Report"]
        kata_report["KATA Markdown<br/>Test result report"]
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

## UC1: API Security Testing

Define test cases in YAML and run security tests against APIs using the HTTP Executor.

```mermaid
sequenceDiagram
    participant Dev as Developer
    participant KATA as KATA Markdown
    participant Runner as test-runner
    participant API as Target API

    Dev->>KATA: Generate YAML from test spec template
    KATA-->>Dev: api_test_data.yml
    Dev->>Runner: gospelo-test-runner run --spec-yml api_test_data.yml
    loop For each test case
        Runner->>API: HTTP request (GET/POST/PUT/DELETE)
        API-->>Runner: Response (status, body)
        Runner->>Runner: Compare with expected → OK/NG
    end
    Runner-->>Dev: evidence_*.json + evidence_*.log
    Dev->>KATA: Generate report from evidence
```

**Example:**

```bash
# List test cases
gospelo-test-runner run --spec-yml templates/api_test_data.yml --list

# Dry run (verify request contents)
gospelo-test-runner run --spec-yml templates/api_test_data.yml --dry-run

# Execute tests
gospelo-test-runner run --spec-yml templates/api_test_data.yml -c config.yml
```

---

## UC2: Testing with Custom Executors

Subclass `BaseExecutor` in `run_test.py` to implement test-specific logic.

```mermaid
sequenceDiagram
    participant Dev as Developer
    participant Script as run_test.py
    participant Runner as runner.py
    participant Custom as CustomExecutor
    participant Target as Test Target

    Dev->>Script: python run_test.py -c config.yml
    Script->>Script: Define TestCase[]
    Script->>Runner: run_suite(config, cases, executor)
    loop For each test case
        Runner->>Custom: execute(case)
        Custom->>Target: Test-specific request
        Target-->>Custom: Response
        Custom->>Custom: Custom evaluation logic
        Custom-->>Runner: TestResult
    end
    Runner-->>Script: evidence_*.json + evidence_*.log
```

**Examples:**
- CSRF token validation (combined Cookie + Token operations)
- Rate limiting tests (rapid requests with timing measurements)
- Session management tests (login → action → logout flows)
- Infrastructure config verification (SSL certificates, HTTP header inspection)

```python
from gospelo_test_runner import BaseExecutor, TestCase, TestResult, TestStatus

class CsrfExecutor(BaseExecutor):
    def execute(self, case, dry_run=False):
        # 1. Login and obtain CSRF token
        # 2. Send request without token / with invalid token
        # 3. Verify response
        return TestResult(
            test_id=case.test_id,
            status=TestStatus.OK if rejected else TestStatus.NG,
            message="CSRF protection verified",
        )
```

---

## UC3: Test Spec Generation with KATA Markdown

Generate test specification YAML from a KATA Markdown template and feed it directly into the runner.

```mermaid
flowchart LR
    subgraph KATA["KATA Markdown"]
        template["Test spec<br/>template"]
        data["Test spec<br/>data (YAML)"]
        rendered["Rendered<br/>test spec (.md)"]
    end

    subgraph Runner["test-runner"]
        spec_yml["api_test_data.yml"]
        execute["Test execution"]
    end

    template --> data
    data --> rendered
    data --> spec_yml
    spec_yml --> execute

    style KATA fill:#E8E8E8,stroke:#5B8DB8
    style Runner fill:#5B8DB8,stroke:#2C2C2C,color:#fff
```

**Workflow:**

```bash
# 1. Generate data file from KATA template
gospelo-kata assemble --type api_test --data templates/api_test_data.yml

# 2. Render (human-readable test specification)
gospelo-kata render outputs/api_test_spec.kata.md --output outputs/api_test_spec.md

# 3. Run tests using the same YAML
gospelo-test-runner run --spec-yml templates/api_test_data.yml -c config.yml
```

**Key point:** Test specifications (documentation) and test execution (automation) are generated from the **same data source**.

---

## UC4: Partial Execution by Category / Test ID

Run only specific categories or IDs from a large set of test cases.

```bash
# Specific category only
gospelo-test-runner run --spec-yml api_test_data.yml -c config.yml \
  --category "Aurora SQL"

# Specific test ID only
gospelo-test-runner run --spec-yml api_test_data.yml -c config.yml \
  --test-id SI-SQL-01

# Adjust delay between tests (e.g. for rate limiting tests)
gospelo-test-runner run --spec-yml api_test_data.yml -c config.yml \
  --delay 2.0
```

---

## UC5: Evidence Report Generation with KATA Markdown

Feed test execution results (evidence JSON) into a KATA Markdown template to generate reports.

```mermaid
flowchart LR
    evidence["evidence_*.json"]
    spec["test_spec.json"]
    template["KATA report<br/>template"]
    report["Test result<br/>report (.md)"]

    evidence --> template
    spec --> template
    template --> report

    style evidence fill:#E8943A,stroke:#2C2C2C,color:#fff
    style template fill:#E8E8E8,stroke:#5B8DB8
    style report fill:#4CAF50,stroke:#2C2C2C,color:#fff
```

```bash
# After test execution
gospelo-test-runner run --spec-yml api_test_data.yml -c config.yml
# → logs/evidence_20260323_120000.json

# Generate report from evidence (KATA)
gospelo-kata assemble --type test_report \
  --data logs/evidence_20260323_120000.json \
  --output outputs/test_report.kata.md
gospelo-kata render outputs/test_report.kata.md --output outputs/test_report.md
```

---

## UC6: Test Execution in Docker Containers

Run tests inside a Docker container for reproducibility.

```mermaid
flowchart TB
    subgraph Host["Host PC"]
        yml_h["api_test_data.yml"]
        config_h["config.yml"]
        script_h["run_test.py"]
        logs_h["logs/<br/>evidence_*.json<br/>evidence_*.log"]
    end

    subgraph Docker["Docker Container"]
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
