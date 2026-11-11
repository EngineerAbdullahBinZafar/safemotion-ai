# Contributing to SafeMotion AI

We welcome contributions to the CBF-QP solver, MCP bridge tools, and ROS 2 deployment bindings.

## Running Local Tests
```bash
uv venv
uv pip install -r requirements.txt pytest httpx
pytest tests/ -v
python demo.py
```

## Safety Guidelines
- All safety filter modifications must preserve mathematical forward-invariance $h(x) \ge 0$ over discrete test trajectories.
- Include deterministic regression tests in `tests/` before submitting pull requests.
