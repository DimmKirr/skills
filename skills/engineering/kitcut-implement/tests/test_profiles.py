"""Bundle profiles (spec rev 2, KUT-211/212 rev): distribution = evidence-free.

F3 is the distribution-profile fixture: same facts/requirements/digests as F2
but no evidence/ directory. Reconstruction must be possible from it alone;
images are generation targets, never copies.
"""
import json
import shutil
import sys
from pathlib import Path

import pytest

SKILL_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_DIR / "scripts"))

import kit  # noqa: E402

F1 = Path("/kirr.dev-112/apps/kitcut/test/results/2026-08-17T07-50-44Z-go-helloworld-kitcut-v2-source")
F3 = Path("/kirr.dev-112/apps/kitcut/test/results/2026-08-17T07-40-18Z-kitcut-v2-example-artifact")


class TestDistributionProfile:
    def test_loads_without_evidence(self):
        """V3 must not fire when the bundle has no evidence/ (distribution)."""
        art = kit.load_artifact(F3)
        assert art.profile == "distribution"
        assert len(art.resources) > 50

    def test_full_profile_detected(self):
        assert kit.load_artifact(F1).profile == "full"

    def test_plan_works_on_distribution(self, tmp_path):
        target = tmp_path / "t"
        target.mkdir()
        plan = kit.plan(kit.load_artifact(F3), target)
        assert "ui_page_home" in plan["create"]

    def test_image_resources_carry_generation_inputs(self):
        """Distribution bundles must make images generatable: description +
        model hint + requirements prose per image resource."""
        art = kit.load_artifact(F3)
        imgs = [r for r in art.resources if r["name"].startswith("ui_image_")]
        assert len(imgs) == 4
        for r in imgs:
            assert r["attributes"].get("description")
            assert r["attributes"].get("model")
            assert r.get("requirements")


class TestVerifyOnDistribution:
    def test_l3_without_reference_is_skipped_not_gating(self, tmp_path):
        """An L3 item whose reference file is absent must be emitted with a
        'skipped' reason and must not affect ok/exit."""
        target = tmp_path / "t"
        (target / "assets" / "css").mkdir(parents=True)
        (target / "index.html").write_text("<html><body></body></html>")
        (target / "assets" / "css" / "style.css").write_text("/* */")
        art = kit.load_artifact(F3)
        result = kit.verify(art, target)
        for item in result["L3_items"]:
            ref = item.get("reference")
            if ref and not (F3 / ref).exists():
                assert item.get("skipped") == "reference unavailable"
        # ok is determined by L1/L2 only — L3 skip must not crash or gate
        assert isinstance(result["ok"], bool)


class TestDistributionHygiene:
    def test_no_views_dir_in_distribution(self):
        """Distribution bundles must not ship views/ (producer-internal,
        prompt-leaking). Spec rev 2 §1."""
        assert not (F3 / "views").exists(), "distribution bundle ships views/"

    def test_no_v1_prompt_pointers_in_distribution(self):
        art = kit.load_artifact(F3)
        offenders = [r["id"] for r in art.resources if r.get("v1_prompt")]
        assert not offenders, f"v1_prompt pointers in distribution: {offenders[:3]}"

    def test_loader_warns_on_views_in_distribution(self, tmp_path):
        import shutil
        b = tmp_path / "artifact"
        shutil.copytree(F3, b)
        (b / "views" / "v1-prompts").mkdir(parents=True)
        (b / "views" / "v1-prompts" / "x.md").write_text("# old prompt")
        art = kit.load_artifact(b)
        assert any("V10" in w for w in art.warnings)
