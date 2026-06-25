from types import SimpleNamespace

from tools import youtube


def test_youtube_fetch_uses_proxy_before_direct(monkeypatch):
    calls = []

    class FakeApi:
        def __init__(self, proxy_config=None):
            calls.append(proxy_config.to_requests_dict() if proxy_config else None)

        def fetch(self, video_id, languages=("en",), preserve_formatting=False):
            if calls[-1] is not None:
                return SimpleNamespace(snippets=[SimpleNamespace(text="proxied transcript")])
            raise AssertionError("direct fetch should not be first when proxies exist")

    monkeypatch.setenv("YT_PROXY_LIST", "http://user:pass@1.1.1.1:8000")
    monkeypatch.setattr(youtube, "YouTubeTranscriptApi", FakeApi)
    youtube._CACHE.clear()
    youtube._IDX = 0

    result = youtube.ext_yt("https://www.youtube.com/watch?v=dQw4w9WgXcQ")

    assert result["text"] == "proxied transcript"
    assert calls == [
        {
            "http": "http://user:pass@1.1.1.1:8000",
            "https": "http://user:pass@1.1.1.1:8000",
        }
    ]


def test_youtube_fetch_falls_back_to_direct_after_proxies(monkeypatch):
    calls = []

    class FakeApi:
        def __init__(self, proxy_config=None):
            calls.append(proxy_config.to_requests_dict() if proxy_config else None)

        def fetch(self, video_id, languages=("en",), preserve_formatting=False):
            if calls[-1] is None:
                return SimpleNamespace(snippets=[SimpleNamespace(text="direct transcript")])
            raise RuntimeError("proxy blocked")

    monkeypatch.setenv("YT_PROXY_LIST", "http://user:pass@1.1.1.1:8000")
    monkeypatch.setattr(youtube, "YouTubeTranscriptApi", FakeApi)
    monkeypatch.setattr(youtube, "timedtext", lambda video_id, proxy=None: "")
    monkeypatch.setattr(youtube, "watch_pg", lambda video_id, proxy=None: "")
    monkeypatch.setattr(youtube, "from_ytdlp", lambda url, proxy=None: "")
    youtube._CACHE.clear()
    youtube._IDX = 0

    result = youtube.ext_yt("https://www.youtube.com/watch?v=dQw4w9WgXcQ")

    assert result["text"] == "direct transcript"
    assert calls == [
        {
            "http": "http://user:pass@1.1.1.1:8000",
            "https": "http://user:pass@1.1.1.1:8000",
        },
        None,
    ]
