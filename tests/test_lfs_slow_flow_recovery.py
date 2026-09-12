#!/usr/bin/env python3
"""Offline regressions for object-scoped slow LFS flow recovery."""

import io
import sys
import tempfile
from contextlib import contextmanager
from types import SimpleNamespace

import atomgit  # noqa: F401
import httpx
import huggingface_hub.lfs as hf_lfs


api_mod = sys.modules["atomgit.api"]


class Clock:
    def __init__(self, value=0.0):
        self.value = value

    def __call__(self):
        return self.value

    def advance(self, seconds):
        self.value += seconds


class FakeOperation:
    def __init__(self, payload=b"abcdefghij"):
        self.payload = payload
        self.path_or_fileobj = payload
        self.path_in_repo = "private-name.bin"
        self.upload_info = SimpleNamespace(
            size=len(payload),
            sha256=b"x" * 32,
        )
        self.open_positions = []

    @contextmanager
    def as_file(self, with_tqdm=False):
        stream = io.BytesIO(self.payload)
        self.open_positions.append(stream.tell())
        yield stream


class FakeResponse:
    def __init__(self, headers=None):
        self.headers = headers or {}


def main():
    results = []

    def check(name, condition, detail=""):
        results.append(bool(condition))
        label = "PASS" if condition else "FAIL"
        print(f"[{label}] {name}" + (f" -> {detail}" if detail else ""))

    stable = api_mod._slow_flow_stable_baseline
    check("20 percent median movement is stable", stable((100.0, 120.0, 96.0)) == 100.0)
    check("movement above 20 percent is unstable", stable((100.0, 121.0, 96.0)) is None)
    check("median-band drift is not mistaken for stable movement", stable((80.0, 100.0, 120.0)) is None)
    check("70 and 130 percent membership boundaries are inclusive", api_mod._slow_flow_peer_baseline(
        ((70.0, 100.0, 130.0),) * 3
    ) == 100.0)

    observed_clock = Clock()
    observed_states = []
    observed = api_mod._SlowFlowCoordinator(
        monotonic=observed_clock,
        observation_callback=observed_states.append,
    )
    observed.register(
        "private-object-key",
        total_bytes=100,
        file_abbrev="source.bin",
        transfer_type="basic",
    )
    initial_state = observed_states[-1]
    check(
        "Flow registration publishes an anonymous baseline state",
        initial_state["type"] == "flow_state"
        and initial_state["flow_key"] == 1
        and initial_state["payload"]["phase"] == "establishing_baseline"
        and initial_state["payload"]["sample_speed"] is None
        and "private-object-key" not in repr(initial_state),
    )
    observed.observe_sample("private-object-key", 20.0, 80)
    sample_state = observed_states[-1]
    check(
        "five-second display samples do not enter recovery policy",
        sample_state["payload"]["sample_speed"] == 20.0
        and sample_state["payload"]["remaining_bytes"] == 80
        and observed._states["private-object-key"].speeds == []
        and observed.replacement_count("private-object-key") == 0,
    )
    for _ in range(13):
        observed.observe_window("private-object-key", 100.0, 50)
    window_state = observed_states[-1]
    check(
        "formal display trend contains only twelve real windows",
        window_state["payload"]["window_speed"] == 100.0
        and window_state["payload"]["stable_baseline"] == 100.0
        and window_state["payload"]["trend"] == [100.0] * 12,
    )
    flow_key = window_state["flow_key"]
    observed.complete("private-object-key")
    observed.register(
        "private-object-key",
        total_bytes=100,
        file_abbrev="source.bin",
        transfer_type="basic",
    )
    check(
        "the same object keeps one anonymous Flow across lifecycle changes",
        observed_states[-1]["flow_key"] == flow_key,
    )

    def broken_observer(message):
        raise RuntimeError("observation unavailable")

    isolated = api_mod._SlowFlowCoordinator(
        monotonic=observed_clock,
        reconnect_jitter=lambda: 2.0,
        observation_callback=broken_observer,
    )
    isolated.register("isolated", total_bytes=10_000)
    isolated_decision = None
    for speed in (100.0, 100.0, 100.0, 30.0, 30.0, 30.0):
        isolated_decision = isolated.observe_window("isolated", speed, 9_000)
    check(
        "observation callback failure cannot change recovery decisions",
        isolated_decision is not None
        and isolated_decision.delay == 2.0
        and isolated.replacement_count("isolated") == 1,
    )

    clock = Clock()
    coordinator = api_mod._SlowFlowCoordinator(
        monotonic=clock,
        reconnect_jitter=lambda: 2.0,
    )
    for key in ("slow", "peer-a", "peer-b"):
        coordinator.register(key, total_bytes=10_000)
    for _ in range(3):
        coordinator.observe_window("peer-a", 100.0, 5_000)
        coordinator.observe_window("peer-b", 100.0, 5_000)
        coordinator.observe_window("slow", 100.0, 9_000)
        clock.advance(30)
    decisions = []
    for speed in (30.1, 30.0, 30.0, 30.0):
        coordinator.observe_window("peer-a", 100.0, 5_000)
        coordinator.observe_window("peer-b", 100.0, 5_000)
        decisions.append(coordinator.observe_window("slow", speed, 9_000))
        clock.advance(30)
    check("above-threshold window resets slow persistence", decisions[:3] == [None, None, None])
    decision = decisions[-1]
    check("three inclusive 30 percent windows replace only candidate", decision is not None and decision.object_key == "slow")
    check("first replacement uses bounded injected jitter", decision is not None and decision.delay == 2.0)
    check("healthy peers retain zero replacements", coordinator.replacement_count("peer-a") == 0 and coordinator.replacement_count("peer-b") == 0)

    low_benefit = api_mod._SlowFlowCoordinator(monotonic=clock, reconnect_jitter=lambda: 2.0)
    for key in ("candidate", "peer-a", "peer-b"):
        low_benefit.register(key, total_bytes=10_000)
    for _ in range(3):
        for key in ("candidate", "peer-a", "peer-b"):
            low_benefit.observe_window(key, 100.0, 200)
    skipped = None
    for _ in range(3):
        low_benefit.observe_window("peer-a", 100.0, 200)
        low_benefit.observe_window("peer-b", 100.0, 200)
        skipped = low_benefit.observe_window("candidate", 30.0, 200)
    check("replacement is skipped when it cannot halve remaining time", skipped is None)

    collective = api_mod._SlowFlowCoordinator(monotonic=clock, reconnect_jitter=lambda: 2.0)
    for key in ("a", "b", "c"):
        collective.register(key, total_bytes=10_000)
    for _ in range(3):
        for key in ("a", "b", "c"):
            collective.observe_window(key, 100.0, 9_000)
    collective_decisions = []
    decisions_by_round = []
    for _ in range(3):
        round_decisions = []
        for key in ("a", "b", "c"):
            candidate = collective.observe_window(key, 20.0, 9_000)
            if candidate is not None:
                collective_decisions.append(candidate)
                round_decisions.append(candidate)
        decisions_by_round.append(round_decisions)
    check("collective slowdown waits for three complete windows", decisions_by_round[:2] == [[], []])
    check("collective slowdown reserves at most one probe", len(collective_decisions) == 1 and collective_decisions[0].probe)

    weak = api_mod._SlowFlowCoordinator(monotonic=clock, reconnect_jitter=lambda: 2.0)
    weak.register("one", total_bytes=10_000)
    for speed in (100.0, 100.0, 100.0, 30.0, 30.0, 30.0):
        first = weak.observe_window("one", speed, 9_000)
    check("self baseline can trigger one-worker recovery", first is not None)
    weak.replacement_finished("one")
    for speed in (50.0, 50.0, 50.0):
        second = weak.observe_window("one", speed, 9_000)
    clock.advance(180)
    check("less than 2x improvement disables further replacement", second is None and weak.is_disabled("one"))

    immediate = api_mod._SlowFlowCoordinator(monotonic=clock, reconnect_jitter=lambda: 2.0)
    immediate.register("one", total_bytes=10_000)
    check("initially slow object has no invented self baseline", all(
        immediate.observe_window("one", 10.0, 9_000) is None for _ in range(8)
    ))

    rolling = api_mod._SlowFlowCoordinator(
        monotonic=clock, reconnect_jitter=lambda: 2.0
    )
    rolling.register("one", total_bytes=10_000)
    rolling_decision = None
    for speed in (
        100.0, 100.0, 100.0,
        200.0, 200.0, 200.0,
        60.0, 60.0, 60.0,
    ):
        rolling_decision = rolling.observe_window("one", speed, 9_000)
    check(
        "self baseline rolls forward before a later collapse",
        rolling_decision is not None,
    )

    peer_improvement = api_mod._SlowFlowCoordinator(
        monotonic=clock, reconnect_jitter=lambda: 2.0
    )
    for key in ("candidate", "peer-a", "peer-b"):
        peer_improvement.register(key, total_bytes=10_000)
    for _ in range(3):
        for key in ("candidate", "peer-a", "peer-b"):
            peer_improvement.observe_window(key, 100.0, 9_000)
    peer_decision = None
    for _ in range(3):
        peer_improvement.observe_window("peer-a", 100.0, 9_000)
        peer_improvement.observe_window("peer-b", 100.0, 9_000)
        peer_decision = peer_improvement.observe_window(
            "candidate", 10.0, 9_000
        )
    peer_improvement.replacement_finished("candidate")
    for _ in range(3):
        peer_improvement.observe_window("peer-a", 100.0, 9_000)
        peer_improvement.observe_window("peer-b", 100.0, 9_000)
        peer_improvement.observe_window("candidate", 30.0, 9_000)
    check(
        "2x improvement must also reach 70 percent of healthy peers",
        peer_decision is not None
        and peer_improvement.is_disabled("candidate"),
    )

    capped = api_mod._SlowFlowCoordinator(
        monotonic=clock, reconnect_jitter=lambda: 2.0
    )
    capped.register("one", total_bytes=1_000_000_000)
    for speed in (100.0, 100.0, 100.0, 30.0, 30.0, 30.0):
        cap_first = capped.observe_window("one", speed, 999_000_000)
    capped.replacement_finished("one")
    for speed in (200.0, 200.0, 200.0, 60.0, 60.0, 60.0):
        cap_second = capped.observe_window("one", speed, 999_000_000)
    capped.replacement_finished("one")
    for speed in (400.0, 400.0, 400.0, 120.0, 120.0, 120.0):
        cap_third = capped.observe_window("one", speed, 999_000_000)
    capped.replacement_finished("one")
    for speed in (800.0, 800.0, 800.0, 240.0, 240.0, 240.0):
        cap_fourth = capped.observe_window("one", speed, 999_000_000)
    check(
        "replacement cooldowns and three-attempt cap are bounded",
        cap_first is not None
        and cap_first.delay == 2.0
        and cap_second is not None
        and cap_second.delay >= 60.0
        and cap_third is not None
        and cap_third.delay >= 180.0
        and cap_fourth is None
        and capped.replacement_count("one") == 3,
    )

    reset = api_mod._SlowFlowCoordinator()
    reset.register("same-oid", total_bytes=10_000)
    for speed in (100.0, 100.0, 100.0, 30.0, 30.0):
        reset.observe_window("same-oid", speed, 9_000)
    reset.complete("same-oid", reset_windows=True)
    reset.register("same-oid", total_bytes=10_000)
    check(
        "a refreshed LFS action starts with fresh observation windows",
        all(
            reset.observe_window("same-oid", 30.0, 9_000) is None
            for _ in range(3)
        ),
    )

    operation = FakeOperation()
    basic_calls = []
    sleeps = []

    def basic_http(method, url, *, data, max_retries):
        basic_calls.append((method, data.tell(), max_retries))
        if len(basic_calls) == 1:
            data.read(4)
            raise api_mod._SlowFlowReconnect(
                api_mod._SlowFlowDecision("basic", 0, 2.0, False)
            )
        data.read()
        return FakeResponse()

    transfer = api_mod._ResumableLfsTransferController(
        coordinator=api_mod._SlowFlowCoordinator(),
        http_backoff=basic_http,
        raise_for_status=lambda response: None,
        sleep=sleeps.append,
    )
    transfer.upload_single_part(operation, "https://signed.invalid/basic")
    check("basic replacement opens source at byte zero", basic_calls == [("PUT", 0, 0), ("PUT", 0, 0)])
    check("ambiguous basic failure returns to LFS Batch before retry", all(call[2] == 0 for call in basic_calls))
    check("basic replacement waits only for its object", sleeps == [2.0])

    encoded = api_mod._SlowFlowPayload(
        io.BytesIO(b"httpx-compatible"),
        coordinator=api_mod._SlowFlowCoordinator(),
        object_key="unused",
        total_bytes=16,
    )
    encoded_request = httpx.Request(
        "PUT", "https://unit.invalid/upload", data=encoded
    )
    encoded_chunks = list(encoded_request.stream)
    check(
        "payload wrapper follows the locked httpx iterable contract",
        b"".join(encoded_chunks) == b"httpx-compatible"
        and encoded_request.headers["Content-Length"] == "16",
    )
    large_encoded = api_mod._SlowFlowPayload(
        io.BytesIO(b"x" * (api_mod._SLOW_FLOW_STREAM_CHUNK_BYTES + 1)),
        coordinator=api_mod._SlowFlowCoordinator(),
        object_key="unused",
        total_bytes=api_mod._SLOW_FLOW_STREAM_CHUNK_BYTES + 1,
    )
    large_request = httpx.Request(
        "PUT", "https://unit.invalid/upload", data=large_encoded
    )
    large_chunks = [len(chunk) for chunk in large_request.stream]
    check(
        "payload sampling uses bounded 512 KiB request chunks",
        sum(large_chunks) == api_mod._SLOW_FLOW_STREAM_CHUNK_BYTES + 1
        and max(large_chunks) <= api_mod._SLOW_FLOW_STREAM_CHUNK_BYTES,
    )

    with tempfile.TemporaryDirectory() as directory:
        source = api_mod.Path(directory) / "source.bin"
        source.write_bytes(b"original")
        mutating_operation = FakeOperation(b"original")
        mutating_operation.path_or_fileobj = source

        def mutate_after_read(method, url, *, data, max_retries):
            data.read()
            source.write_bytes(b"changed!")
            return FakeResponse()

        mutating_transfer = api_mod._ResumableLfsTransferController(
            coordinator=api_mod._SlowFlowCoordinator(),
            http_backoff=mutate_after_read,
            raise_for_status=lambda response: None,
        )
        try:
            mutating_transfer.upload_single_part(
                mutating_operation, "https://signed.invalid/mutating"
            )
        except RuntimeError:
            mutation_rejected = True
        else:
            mutation_rejected = False
        check("source mutation after PUT fails closed", mutation_rejected)

    multipart_calls = []
    completion_payloads = []
    multipart_operation = FakeOperation(b"abcdefghijkl")

    def multipart_http(method, url, *, data, max_retries):
        if max_retries != 0:
            raise AssertionError("multipart PUT must reconcile through LFS Batch")
        multipart_calls.append((url.rsplit("/", 1)[-1], data.tell()))
        if url.endswith("/2") and sum(call[0] == "2" for call in multipart_calls) == 1:
            data.read(2)
            raise api_mod._SlowFlowReconnect(
                api_mod._SlowFlowDecision("multipart", 0, 0.0, False)
            )
        data.read()
        return FakeResponse({"etag": f"etag-{url[-1]}"})

    class Session:
        def post(self, url, *, json, headers):
            completion_payloads.append(json)
            return FakeResponse()

    multipart_transfer = api_mod._ResumableLfsTransferController(
        coordinator=api_mod._SlowFlowCoordinator(),
        http_backoff=multipart_http,
        raise_for_status=lambda response: None,
        get_session=lambda: Session(),
        sleep=lambda delay: None,
    )
    multipart_transfer.upload_multi_part(
        multipart_operation,
        {"1": "https://signed.invalid/1", "2": "https://signed.invalid/2", "3": "https://signed.invalid/3"},
        4,
        "https://signed.invalid/complete",
    )
    check("multipart retains confirmed part and retries only unconfirmed part", [call[0] for call in multipart_calls] == ["1", "2", "2", "3"])
    check("multipart completion contains one validated ETag per part", completion_payloads == [{
        "oid": (b"x" * 32).hex(),
        "parts": [
            {"partNumber": 1, "etag": "etag-1"},
            {"partNumber": 2, "etag": "etag-2"},
            {"partNumber": 3, "etag": "etag-3"},
        ],
    }])

    original_single = hf_lfs._upload_single_part
    original_multi = hf_lfs._upload_multi_part
    try:
        with api_mod._scoped_resumable_lfs_recovery(api_mod._SlowFlowCoordinator()):
            check("scoped recovery installs both HF LFS hooks", hf_lfs._upload_single_part is not original_single and hf_lfs._upload_multi_part is not original_multi)
            raise RuntimeError("exercise restoration")
    except RuntimeError:
        pass
    check("scoped recovery restores both HF LFS hooks", hf_lfs._upload_single_part is original_single and hf_lfs._upload_multi_part is original_multi)

    passed = sum(results)
    print(f"summary: {passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
