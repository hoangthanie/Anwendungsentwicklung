"""Prüft nur, dass das Backend-Paket installiert und importierbar ist."""


def test_pipeline_ist_importierbar():
    import pipeline.harness.llm  # noqa: F401
    import pipeline.run  # noqa: F401
