from paladin.progress import BatchProgress, Eta


def test_eta_starts_honest_and_becomes_estimate():
    eta = Eta()
    assert eta.estimate(3) == "Calculating..."
    eta.add(10)
    assert eta.estimate(3) == "~00:30"


def test_plain_progress_lifecycle():
    progress = BatchProgress(1)
    with progress:
        progress.set_current("episode.mkv", "processing")
        progress.complete(True)
    assert progress.completed == 1
