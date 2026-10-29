
def test_provider_failure_logs_are_redacted_end_to_end(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Provider exceptions must never leak secrets into structured logs."""
    secret = "api_key=private-value-do-not-log"
    private_prompt = "confidential-property-brief-do-not-log"

    primary = FakeProvider(
        ProviderResponse(
            "Unused response",
            PRIMARY.provider_id,
            PRIMARY.model_id,
        ),
        error=RuntimeError(f"provider timeout; {secret}"),
    )

    logger = logging.getLogger("homio.test.observability.redaction")
    observer = StructuredLoggingObservability(logger)

    gateway, _, _, usage, _ = make_gateway(
        providers={PRIMARY.provider_id: primary},
        observer=observer,  # type: ignore[arg-type]
    )

    request = make_request()
    request = AIRequest(
        request_id=request.request_id,
        operation=request.operation,
        input_text=private_prompt,
        context=request.context,
        model_id=request.model_id,
    )

    with caplog.at_level(
        logging.INFO,
        logger="homio.test.observability.redaction",
    ):
        with pytest.raises(ProviderCallFailedError) as exc:
            gateway.complete(request)

    assert secret not in str(exc.value)
    assert private_prompt not in str(exc.value)

    records = [
        record
        for record in caplog.records
        if record.name == "homio.test.observability.redaction"
    ]
    assert records, "Expected structured failure telemetry"

    allowed_fields = {
        "event_name",
        "request_id",
        "correlation_id",
        "outcome",
        "provider_id",
        "model_id",
        "duration_ms",
        "error_code",
    }

    for record in records:
        assert record.getMessage() == "homio_ai_event"
        payload = record.homio_ai_event
        assert set(payload) == allowed_fields
        assert secret not in repr(payload)
        assert private_prompt not in repr(payload)
        assert "api_key" not in repr(payload).lower()

    assert any(
        record.homio_ai_event["event_name"] == "REQUEST_FAILED"
        for record in records
    )
    assert usage.settlements[0][1] is UsageOutcome.FAILED
