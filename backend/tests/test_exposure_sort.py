from app.cv.audit.exposure_sort import FrameExposure, relative_exposure_ratios, sort_dark_to_bright


def test_exposure_sort_works_for_five_frames():
    frames = [
        FrameExposure(0, exposure_time=1 / 30, iso=100, aperture=4),
        FrameExposure(1, exposure_time=1 / 250, iso=100, aperture=4),
        FrameExposure(2, exposure_time=1 / 8, iso=100, aperture=4),
        FrameExposure(3, exposure_time=1 / 60, iso=100, aperture=4),
        FrameExposure(4, exposure_time=1 / 125, iso=100, aperture=4),
    ]
    order = sort_dark_to_bright(frames)
    assert order == [1, 4, 3, 0, 2]
    ratios = relative_exposure_ratios(frames, reference_index=3)
    assert ratios[3] == 1.0
    assert ratios[2] > ratios[1]

