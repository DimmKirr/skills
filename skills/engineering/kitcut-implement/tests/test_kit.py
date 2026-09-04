"""pytest suite for scripts/kit.py — written RED-first (KUT-212).

Fixture F1: the go-helloworld v2 artifact bundle. Tests copy it to tmp_path
when they need to corrupt or edit it; the original is never modified.

Run: python3 -m pytest tests/ -v   (from the skill directory)
"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

SKILL_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_DIR / "scripts"))

import kit  # noqa: E402  (the module under test)

F1 = Path("/kirr.dev-112/apps/kitcut/test/results/2026-08-17T07-50-44Z-go-helloworld-kitcut-v2-source")


# ---------- helpers ----------

def copy_f1(tmp_path: Path) -> Path:
    dst = tmp_path / "artifact"
    shutil.copytree(F1, dst)
    return dst


def mutate_facts(bundle: Path, fn):
    facts = json.loads((bundle / "facts.json").read_text())
    fn(facts)
    (bundle / "facts.json").write_text(json.dumps(facts, indent=2))


def make_target(tmp_path: Path, with_evidence: bool = False) -> Path:
    target = tmp_path / "target"
    target.mkdir(exist_ok=True)
    if with_evidence:
        for f in ("main.go", "main_test.go"):
            shutil.copy(F1 / "evidence" / f, target / f)
        (target / "go.mod").write_text("module helloworld\n\ngo 1.21\n")
    return target


# ---------- load + artifact-level verify rules (V1-V5) ----------

class TestLoad:
    def test_load_valid_f1(self):
        art = kit.load_artifact(F1)
        assert len(art.resources) == 6
        assert len(art.edges) == 6
        assert art.root == "tofukit_project.go_helloworld"

    def test_rejects_dangling_edge(self, tmp_path):
        b = copy_f1(tmp_path)
        mutate_facts(b, lambda f: f["edges"].append(
            {"src": f["root"], "role": "contains",
             "dst": "tofukit_feature.ghost", "provenance": "inferred"}))
        with pytest.raises(kit.ArtifactError, match="V1"):
            kit.load_artifact(b)

    def test_rejects_orphan(self, tmp_path):
        b = copy_f1(tmp_path)
        mutate_facts(b, lambda f: f["resources"].append(
            {"id": "tofukit_feature.floating", "type": "tofukit_feature",
             "name": "floating", "category": "project", "provenance": "inferred"}))
        with pytest.raises(kit.ArtifactError, match="V2"):
            kit.load_artifact(b)

    def test_rejects_orphan_prose(self, tmp_path):
        b = copy_f1(tmp_path)
        (b / "requirements" / "unclaimed.md").write_text("# unclaimed\n")
        with pytest.raises(kit.ArtifactError, match="V4"):
            kit.load_artifact(b)

    def test_rejects_prose_interpolation(self, tmp_path):
        b = copy_f1(tmp_path)
        req = b / "requirements" / "hello_greeting.md"
        req.write_text(req.read_text() + "\nuses ${tofukit_file.main_go.link}\n")
        with pytest.raises(kit.ArtifactError, match="V5"):
            kit.load_artifact(b)

    def test_rejects_bad_role(self, tmp_path):
        b = copy_f1(tmp_path)
        mutate_facts(b, lambda f: f["edges"][0].update(role="depends_on_maybe"))
        with pytest.raises(kit.ArtifactError):
            kit.load_artifact(b)


# ---------- build units + topo order ----------

class TestUnits:
    def test_f1_units(self):
        art = kit.load_artifact(F1)
        units = kit.build_units(art)
        names = [u.id for u in units]
        assert "scaffold" in names
        assert "hello_greeting" in names

    def test_topo_scaffold_first(self):
        art = kit.load_artifact(F1)
        units = kit.build_units(art)
        names = [u.id for u in units]
        assert names.index("scaffold") < names.index("hello_greeting")

    def test_feature_unit_owns_its_files(self):
        art = kit.load_artifact(F1)
        units = {u.id: u for u in kit.build_units(art)}
        hg = units["hello_greeting"].resources
        assert "tofukit_file.main_go" in hg
        assert "tofukit_file.main_test_go" in hg
        assert "tofukit_feature.hello_greeting" in hg


# ---------- plan ----------

class TestPlan:
    def test_plan_empty_lock_all_create(self, tmp_path):
        target = make_target(tmp_path)
        plan = kit.plan(kit.load_artifact(F1), target)
        assert plan["keep"] == [] and plan["delete"] == [] and plan["regenerate"] == []
        assert set(plan["create"]) == {"scaffold", "hello_greeting"}

    def test_plan_after_record_is_keep(self, tmp_path):
        b, target = copy_f1(tmp_path), make_target(tmp_path, with_evidence=True)
        art = kit.load_artifact(b)
        for unit in ("scaffold", "hello_greeting"):
            kit.record(art, target, unit,
                       ["go.mod"] if unit == "scaffold" else ["main.go", "main_test.go"])
        plan = kit.plan(art, target)
        assert set(plan["keep"]) == {"scaffold", "hello_greeting"}
        assert plan["create"] == [] and plan["regenerate"] == [] and plan["delete"] == []

    def test_plan_edit_is_delta_only(self, tmp_path):
        b, target = copy_f1(tmp_path), make_target(tmp_path, with_evidence=True)
        art = kit.load_artifact(b)
        for unit in ("scaffold", "hello_greeting"):
            kit.record(art, target, unit,
                       ["go.mod"] if unit == "scaffold" else ["main.go", "main_test.go"])
        # edit: drop the test resource + its edges (facts change in hello_greeting only)
        mutate_facts(b, lambda f: (
            f["resources"].__setitem__(slice(None), [r for r in f["resources"] if r["name"] != "main_test_go"]),
            f["edges"].__setitem__(slice(None), [e for e in f["edges"] if "main_test_go" not in e["src"] + e["dst"]]),
        ))
        art2 = kit.load_artifact(b)
        plan = kit.plan(art2, target)
        assert plan["keep"] == ["scaffold"]
        assert plan["regenerate"] == ["hello_greeting"]
        assert plan["create"] == [] and plan["delete"] == []


# ---------- next (context package) ----------

class TestNext:
    def test_next_first_unit_is_scaffold(self, tmp_path):
        target = make_target(tmp_path)
        pkg = kit.next_unit(kit.load_artifact(F1), target)
        assert pkg["unit"] == "scaffold"
        assert pkg["done"] is False

    def test_next_package_shape(self, tmp_path):
        b, target = copy_f1(tmp_path), make_target(tmp_path, with_evidence=True)
        art = kit.load_artifact(b)
        kit.record(art, target, "scaffold", ["go.mod"])
        pkg = kit.next_unit(art, target)
        assert pkg["unit"] == "hello_greeting"
        # carries the unit's requirements prose
        assert "hello_greeting" in pkg["requirements"]
        assert "Hello World!!" in pkg["requirements"]["hello_greeting"]
        # carries relevant digests
        assert "symbol-map" in pkg["digests"]
        # dep interfaces only — never dep source, never evidence content
        assert "evidence" not in pkg
        assert any(d["unit"] == "scaffold" for d in pkg["dep_interfaces"])
        blob = json.dumps(pkg)
        assert "fmt.Println" not in blob  # evidence source must not leak

    def test_next_done_when_all_recorded(self, tmp_path):
        b, target = copy_f1(tmp_path), make_target(tmp_path, with_evidence=True)
        art = kit.load_artifact(b)
        for unit in ("scaffold", "hello_greeting"):
            kit.record(art, target, unit,
                       ["go.mod"] if unit == "scaffold" else ["main.go", "main_test.go"])
        assert kit.next_unit(art, target)["done"] is True


# ---------- record / lockfile ----------

class TestRecord:
    def test_record_writes_lockfile(self, tmp_path):
        b, target = copy_f1(tmp_path), make_target(tmp_path, with_evidence=True)
        art = kit.load_artifact(b)
        kit.record(art, target, "hello_greeting", ["main.go", "main_test.go"])
        lock = json.loads((target / ".kit-lock.json").read_text())
        assert lock["spec"].startswith("kitcut-lock/")
        u = lock["units"]["hello_greeting"]
        assert set(u["files"]) == {"main.go", "main_test.go"}
        assert all(h.startswith("sha256:") for h in u["files"].values())

    def test_record_hashes_stable(self, tmp_path):
        b, target = copy_f1(tmp_path), make_target(tmp_path, with_evidence=True)
        art = kit.load_artifact(b)
        kit.record(art, target, "hello_greeting", ["main.go"])
        h1 = json.loads((target / ".kit-lock.json").read_text())["units"]["hello_greeting"]
        kit.record(art, target, "hello_greeting", ["main.go"])
        h2 = json.loads((target / ".kit-lock.json").read_text())["units"]["hello_greeting"]
        assert h1["files"] == h2["files"]
        assert h1["facts_hash"] == h2["facts_hash"]


# ---------- verify ----------

class TestVerify:
    def test_verify_green_on_evidence(self, tmp_path):
        target = make_target(tmp_path, with_evidence=True)
        result = kit.verify(kit.load_artifact(F1), target)
        assert result["ok"] is True, json.dumps(result, indent=2)
        assert all(c["passed"] for c in result["L1"])
        assert all(c["passed"] for c in result["L2"])
        # L3/L4 are emitted for the model, not judged by kit.py
        assert len(result["L4_items"]) == 1
        assert result["L4_items"][0]["against"] == "requirements/hello_greeting.md"

    def test_verify_fails_on_wrong_stdout(self, tmp_path):
        target = make_target(tmp_path, with_evidence=True)
        src = (target / "main.go").read_text().replace("Hello World!!", "Goodbye!!")
        (target / "main.go").write_text(src)
        result = kit.verify(kit.load_artifact(F1), target)
        assert result["ok"] is False
        failed = [c for c in result["L1"] + result["L2"] if not c["passed"]]
        assert failed, "expected at least one failing check"

    def test_verify_fails_on_missing_symbol(self, tmp_path):
        target = make_target(tmp_path, with_evidence=True)
        src = (target / "main.go").read_text().replace("helloworld", "greet")
        (target / "main.go").write_text(src)
        (target / "main_test.go").write_text(
            (target / "main_test.go").read_text().replace("helloworld", "greet"))
        result = kit.verify(kit.load_artifact(F1), target)
        assert result["ok"] is False
        assert any(c.get("check") == "symbol_exists" and not c["passed"]
                   for c in result["L2"])


# ---------- CLI smoke ----------

class TestCLI:
    def test_cli_plan_json(self, tmp_path):
        target = make_target(tmp_path)
        out = subprocess.run(
            [sys.executable, str(SKILL_DIR / "scripts" / "kit.py"),
             "plan", str(F1), "--target", str(target)],
            capture_output=True, text=True)
        assert out.returncode == 0, out.stderr
        plan = json.loads(out.stdout)
        assert set(plan["create"]) == {"scaffold", "hello_greeting"}

    def test_cli_verify_exit_code(self, tmp_path):
        target = make_target(tmp_path, with_evidence=True)
        (target / "main.go").write_text(
            (target / "main.go").read_text().replace("Hello World!!", "nope"))
        out = subprocess.run(
            [sys.executable, str(SKILL_DIR / "scripts" / "kit.py"),
             "verify", str(F1), "--target", str(target)],
            capture_output=True, text=True)
        assert out.returncode != 0


class TestRecordNoFiles:
    def test_record_unit_with_no_files(self, tmp_path):
        """Token/concept units are realized inside other units' files and may
        record with an empty file list (KUT-215 finding)."""
        b, target = copy_f1(tmp_path), make_target(tmp_path)
        art = kit.load_artifact(b)
        kit.record(art, target, "scaffold", [])
        lock = json.loads((target / ".kit-lock.json").read_text())
        assert lock["units"]["scaffold"]["files"] == {}

    def test_cli_record_no_files(self, tmp_path):
        target = make_target(tmp_path)
        out = subprocess.run(
            [sys.executable, str(SKILL_DIR / "scripts" / "kit.py"),
             "record", str(F1), "--target", str(target), "--unit", "scaffold"],
            capture_output=True, text=True)
        assert out.returncode == 0, out.stderr
