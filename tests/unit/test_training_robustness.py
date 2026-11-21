"""Recovery paths of stage A training: the step retry in train.py and the supervisor script.

The supervisor tests run ``tools/phase2/run_stage_a.sh`` with small stand-in training programs, so
they need bash (Git Bash on Windows) and take a few seconds each.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest
import torch

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools" / "phase2"))
import train  # noqa: E402

BASH = shutil.which("bash")
needs_bash = pytest.mark.skipif(BASH is None, reason="needs bash")


# --- train.py -------------------------------------------------------------------------------


def test_is_oom_recognises_both_forms() -> None:
    assert train.is_oom(RuntimeError("CUDA error: out of memory"))
    assert train.is_oom(torch.OutOfMemoryError("CUDA out of memory. Tried to allocate 2.00 MiB"))
    assert not train.is_oom(RuntimeError("cuDNN error: CUDNN_STATUS_EXECUTION_FAILED_CUDART"))


def test_forward_backward_raises_other_errors_on_cpu() -> None:
    class Net(torch.nn.Module):
        def forward(self, b):
            raise RuntimeError("CUDA error: out of memory")

    opt = torch.optim.SGD([torch.nn.Parameter(torch.zeros(1))], lr=0.1)
    with pytest.raises(RuntimeError):  # retries are for the GPU only
        train.forward_backward(Net(), {}, None, opt, "cpu", 0)


@pytest.mark.gpu
def test_retry_after_out_of_memory_gives_identical_gradients(monkeypatch) -> None:
    monkeypatch.setattr(train, "OOM_WAIT", 0)
    monkeypatch.setattr(train, "losses", lambda res, batch, w: {"total": res.pow(2).mean()})

    class Net(torch.nn.Module):
        def __init__(self, fail: int):
            super().__init__()
            self.lin, self.drop, self.fail = torch.nn.Linear(16, 16), torch.nn.Dropout(0.5), fail

        def forward(self, b):
            y = self.drop(self.lin(b["x"]))
            if self.fail > 0:
                self.fail -= 1
                y.sum().backward()  # partial gradients, as a failed pass leaves
                raise RuntimeError("CUDA error: out of memory")
            return y

    def grads(fail: int):
        torch.manual_seed(0)
        net = Net(fail).cuda()
        opt = torch.optim.AdamW(net.parameters())
        b = {"x": torch.randn(8, 16, device="cuda")}
        torch.cuda.manual_seed(123)
        train.forward_backward(net, b, None, opt, "cuda", 0)
        return [p.grad.clone() for p in net.parameters()]

    ref = grads(0)
    assert all(torch.equal(a, b) for a, b in zip(ref, grads(2), strict=True))
    with pytest.raises(RuntimeError):
        grads(train.OOM_RETRIES + 1)


def test_leave_exits_with_its_code() -> None:
    code = (
        f"import sys; sys.path.insert(0, {str(REPO / 'tools' / 'phase2')!r}); import train; train.leave(75)"
    )
    assert subprocess.run([sys.executable, "-c", code], timeout=120).returncode == 75


# --- run_stage_a.sh -------------------------------------------------------------------------

STUB = """
import sys, time
from pathlib import Path
out = Path(sys.argv[sys.argv.index("--out") + 1]); out.mkdir(parents=True, exist_ok=True)
runs = out / "runs"; n = int(runs.read_text()) + 1 if runs.exists() else 1; runs.write_text(str(n))
def beat(): (out / "heartbeat").write_text(f"{time.time():.0f}")
beat()
MODE = "{mode}"
if MODE == "crash_once" and n == 1:
    sys.exit(75)
if MODE == "always_fail":
    sys.exit(75)
if MODE == "fail_marker_then_hang" and n == 1:
    (out / "failed").write_text("1")
    while True:
        time.sleep(1)
done = 0
while done < {beats}:  # a frozen run makes no progress, as in a hang or standby
    if not (out / "freeze").exists():
        beat()
        done += 1
    time.sleep(1)
(out / "last.pt").write_text("done")
"""


def supervise(tmp: Path, mode: str, *, beats: int = 2, script: str = "", **env) -> tuple[int, str]:
    stub = tmp / f"stub_{mode}.py"
    stub.write_text(textwrap.dedent(STUB).replace("{mode}", mode).replace("{beats}", str(beats)))
    runs = tmp / "runs"
    runs.mkdir(exist_ok=True)
    base = {"RUNS": runs.as_posix(), "TRAIN": stub.as_posix(), "POLL": "1", "RESTART_WAIT": "0"}
    full = {**os.environ, **base, **{k: str(v) for k, v in env.items()}}
    cmd = script or "bash tools/phase2/run_stage_a.sh list job"
    r = subprocess.run([BASH, "-c", cmd], cwd=REPO, env=full, timeout=240, capture_output=True)
    return r.returncode, (runs / "queue.log").read_text()


@needs_bash
@pytest.mark.slow
def test_supervisor_restarts_a_crashed_run(tmp_path: Path) -> None:
    code, log = supervise(tmp_path, "crash_once")
    assert code == 0
    assert "failed with status 75; restart 1 of" in log and "job: done" in log


@needs_bash
@pytest.mark.slow
def test_supervisor_gives_up_after_max_restarts(tmp_path: Path) -> None:
    code, log = supervise(tmp_path, "always_fail", MAX_RESTARTS=2)
    assert code == 75
    assert "after 2 restarts" in log


@needs_bash
@pytest.mark.slow
def test_supervisor_skips_a_finished_run(tmp_path: Path) -> None:
    (tmp_path / "runs" / "job_s1").mkdir(parents=True)
    (tmp_path / "runs" / "job_s1" / "last.pt").write_text("done")
    code, log = supervise(tmp_path, "crash_once")
    assert code == 0 and "job: finished" in log
    assert not (tmp_path / "runs" / "job_s1" / "runs").exists()  # never launched


@needs_bash
@pytest.mark.slow
def test_supervisor_stops_a_failed_run_that_does_not_exit(tmp_path: Path) -> None:
    code, log = supervise(tmp_path, "fail_marker_then_hang", STALL=600)
    assert code == 0
    assert "reported a failure but did not exit" in log and "job: done" in log


@needs_bash
@pytest.mark.slow
def test_supervisor_stops_a_hung_run(tmp_path: Path) -> None:
    # A run whose heartbeat stops (freeze file present) is stopped after STALL seconds.
    (tmp_path / "runs" / "job_s1").mkdir(parents=True)
    (tmp_path / "runs" / "job_s1" / "freeze").write_text("1")
    script = (
        'bash tools/phase2/run_stage_a.sh list job & sup=$!; sleep 12; rm -f "$RUNS/job_s1/freeze"; wait $sup'
    )
    code, log = supervise(tmp_path, "hang_until_thawed", beats=4, STALL=5, script=script)
    assert code == 0
    assert "no heartbeat for" in log and "job: done" in log


@needs_bash
@pytest.mark.slow
def test_supervisor_does_not_count_standby_as_a_stall(tmp_path: Path) -> None:
    # Standby freezes both the supervisor and training: stop the supervisor and freeze the
    # heartbeat together for longer than STALL, then thaw both.
    script = (
        "bash tools/phase2/run_stage_a.sh list job & sup=$!; sleep 3; "
        'touch "$RUNS/job_s1/freeze"; kill -STOP $sup; sleep 12; '
        'rm -f "$RUNS/job_s1/freeze"; kill -CONT $sup; '
        "while kill -0 $sup 2>/dev/null; do sleep 1; done"
    )
    code, log = supervise(tmp_path, "standby", beats=8, STALL=8, SUSPEND=4, script=script)
    assert code == 0, log
    assert "machine was suspended" in log and "no heartbeat" not in log and "job: done" in log
