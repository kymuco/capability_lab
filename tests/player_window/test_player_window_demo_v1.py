from capability_lab.player_window.demo import main


def test_demo_entry_point_writes_openable_local_html(tmp_path) -> None:
    output = tmp_path / "player_window.html"
    assert main(["--output", str(output)]) == 0
    text = output.read_text(encoding="utf-8")
    assert text.startswith("<!doctype html>")
    assert "Player Window" in text
    assert "Basic Electricity" in text
    assert "Low-Voltage Power Distribution" in text
    assert "Potable Water Treatment" in text
