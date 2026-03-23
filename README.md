# gospelo-test-runner

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://github.com/gospelo-dev/test-runner/blob/main/LICENSE.md)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-3776AB.svg?logo=python&logoColor=white)](https://www.python.org/)
[![PyPI](https://img.shields.io/badge/PyPI-gospelo--test--runner-3775A9.svg?logo=pypi&logoColor=white)](https://pypi.org/project/gospelo-test-runner/)
[![AI Collaborative](https://img.shields.io/badge/AI-Collaborative-ff6f00.svg?logo=openai&logoColor=white)](#機能)

Generic test execution engine with pluggable executors and evidence collection.

## Features

| Module      | Description                                                 |
| ----------- | ----------------------------------------------------------- |
| `types`     | TestCase, TestResult, TestStatus, TestSuiteConfig           |
| `runner`    | Test execution orchestration (run_suite, run_tests)         |
| `executor/` | BaseExecutor, HttpExecutor, ProcessExecutor, AssertExecutor |
| `loader/`   | config_loader (YAML/JSON), spec_loader (JSON/YAML)          |
| `reporter/` | JsonReporter, LogReporter, SpecExporter                     |
| `version`   | Version info and artifact stamps                            |

## Installation

```bash
pip install gospelo-test-runner
```

## CLI

```bash
gospelo-test-runner run --spec-json test_spec.json -c config.yml
gospelo-test-runner run --spec-yml api_test_data.yml --dry-run
gospelo-test-runner run --spec-yml api_test_data.yml --list
gospelo-test-runner --version
```

## Usage (Python)

```python
from gospelo_test_runner import (
    TestCase, TestSuiteConfig, HttpExecutor, run_suite,
)
```

## License

MIT
