CREATE TABLE __HOMIO_CORE002_SCHEMA__.events (
  tenant_id uuid NOT NULL,
  event_id uuid NOT NULL,
  envelope jsonb NOT NULL,
  immutable_fingerprint text NOT NULL,
  created_at timestamp with time zone NOT NULL
    DEFAULT clock_timestamp(),

  CONSTRAINT core002_events_pkey
    PRIMARY KEY (tenant_id, event_id),

  CONSTRAINT core002_events_fingerprint_key
    UNIQUE (tenant_id, event_id, immutable_fingerprint),

  CONSTRAINT core002_events_envelope_object_check
    CHECK (jsonb_typeof(envelope) = 'object'),

  CONSTRAINT core002_events_event_id_check
    CHECK (envelope->>'event_id' = event_id::text),

  CONSTRAINT core002_events_tenant_id_check
    CHECK (envelope->>'tenant_id' = tenant_id::text),

  CONSTRAINT core002_events_fingerprint_check
    CHECK (immutable_fingerprint ~ '^[a-f0-9]{64}$')
);

CREATE UNIQUE INDEX core002_events_idempotency_uq
  ON __HOMIO_CORE002_SCHEMA__.events (
    tenant_id,
    (envelope->>'idempotency_key')
  )
  WHERE jsonb_typeof(envelope->'idempotency_key') = 'string'
    AND envelope->>'idempotency_key' <> '';

CREATE INDEX core002_events_type_time_idx
  ON __HOMIO_CORE002_SCHEMA__.events (
    tenant_id,
    (envelope->>'event_type'),
    created_at
  );

CREATE INDEX core002_events_correlation_idx
  ON __HOMIO_CORE002_SCHEMA__.events (
    tenant_id,
    (envelope->>'correlation_id')
  );

CREATE TABLE __HOMIO_CORE002_SCHEMA__.outbox_publications (
  tenant_id uuid NOT NULL,
  publication_id uuid NOT NULL,
  event_id uuid NOT NULL,
  event_fingerprint text NOT NULL,
  created_at timestamp with time zone NOT NULL,
  state text NOT NULL DEFAULT 'CREATED',
  state_changed_at timestamp with time zone NOT NULL
    DEFAULT clock_timestamp(),

  CONSTRAINT core002_outbox_publications_pkey
    PRIMARY KEY (tenant_id, publication_id),

  CONSTRAINT core002_outbox_one_publication_per_event
    UNIQUE (tenant_id, event_id),

  CONSTRAINT core002_outbox_event_fingerprint_fk
    FOREIGN KEY (
      tenant_id,
      event_id,
      event_fingerprint
    )
    REFERENCES __HOMIO_CORE002_SCHEMA__.events (
      tenant_id,
      event_id,
      immutable_fingerprint
    ),

  CONSTRAINT core002_outbox_fingerprint_check
    CHECK (event_fingerprint ~ '^[a-f0-9]{64}$'),

  CONSTRAINT core002_outbox_state_check
    CHECK (
      state IN (
        'CREATED',
        'COMMITTED',
        'PUBLISHED',
        'RECOVERABLE',
        'FAILED'
      )
    )
);

CREATE INDEX core002_outbox_recovery_idx
  ON __HOMIO_CORE002_SCHEMA__.outbox_publications (
    tenant_id,
    created_at,
    publication_id
  )
  WHERE state IN ('COMMITTED', 'RECOVERABLE');

CREATE FUNCTION __HOMIO_CORE002_SCHEMA__.reject_event_mutation()
RETURNS trigger
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $function$
BEGIN
  RAISE EXCEPTION
    'CORE-002 event envelopes are immutable'
    USING ERRCODE = '55000';
END;
$function$;

CREATE TRIGGER core002_events_immutable
  BEFORE UPDATE OR DELETE
  ON __HOMIO_CORE002_SCHEMA__.events
  FOR EACH ROW
  EXECUTE FUNCTION
    __HOMIO_CORE002_SCHEMA__.reject_event_mutation();

CREATE FUNCTION __HOMIO_CORE002_SCHEMA__.enforce_outbox_transition()
RETURNS trigger
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $function$
BEGIN
  IF
    NEW.tenant_id IS DISTINCT FROM OLD.tenant_id
    OR NEW.publication_id IS DISTINCT FROM OLD.publication_id
    OR NEW.event_id IS DISTINCT FROM OLD.event_id
    OR NEW.event_fingerprint IS DISTINCT FROM OLD.event_fingerprint
    OR NEW.created_at IS DISTINCT FROM OLD.created_at
  THEN
    RAISE EXCEPTION
      'CORE-002 publication identity and event binding are immutable'
      USING ERRCODE = '55000';
  END IF;

  IF NEW.state = OLD.state THEN
    IF NEW.state_changed_at IS DISTINCT FROM OLD.state_changed_at THEN
      RAISE EXCEPTION
        'CORE-002 state timestamp cannot be changed independently'
        USING ERRCODE = '55000';
    END IF;

    RETURN NEW;
  END IF;

  IF NOT (
    (
      OLD.state = 'CREATED'
      AND NEW.state IN ('COMMITTED', 'FAILED')
    )
    OR
    (
      OLD.state = 'COMMITTED'
      AND NEW.state IN ('PUBLISHED', 'RECOVERABLE', 'FAILED')
    )
    OR
    (
      OLD.state = 'RECOVERABLE'
      AND NEW.state IN ('PUBLISHED', 'FAILED')
    )
  ) THEN
    RAISE EXCEPTION
      'Invalid CORE-002 publication state transition: % -> %',
      OLD.state,
      NEW.state
      USING ERRCODE = '55000';
  END IF;

  NEW.state_changed_at := clock_timestamp();

  RETURN NEW;
END;
$function$;

CREATE TRIGGER core002_outbox_state_guard
  BEFORE UPDATE
  ON __HOMIO_CORE002_SCHEMA__.outbox_publications
  FOR EACH ROW
  EXECUTE FUNCTION
    __HOMIO_CORE002_SCHEMA__.enforce_outbox_transition();

ALTER TABLE __HOMIO_CORE002_SCHEMA__.events
  ENABLE ROW LEVEL SECURITY;

ALTER TABLE __HOMIO_CORE002_SCHEMA__.events
  FORCE ROW LEVEL SECURITY;

CREATE POLICY core002_events_application_access
  ON __HOMIO_CORE002_SCHEMA__.events
  AS PERMISSIVE
  FOR ALL
  TO __HOMIO_APPLICATION_ROLE__
  USING (true)
  WITH CHECK (true);

CREATE POLICY core002_events_tenant_guard
  ON __HOMIO_CORE002_SCHEMA__.events
  AS RESTRICTIVE
  FOR ALL
  TO __HOMIO_APPLICATION_ROLE__
  USING (
    tenant_id = current_setting('app.tenant_id', true)::uuid
  )
  WITH CHECK (
    tenant_id = current_setting('app.tenant_id', true)::uuid
  );

ALTER TABLE __HOMIO_CORE002_SCHEMA__.outbox_publications
  ENABLE ROW LEVEL SECURITY;

ALTER TABLE __HOMIO_CORE002_SCHEMA__.outbox_publications
  FORCE ROW LEVEL SECURITY;

CREATE POLICY core002_outbox_application_access
  ON __HOMIO_CORE002_SCHEMA__.outbox_publications
  AS PERMISSIVE
  FOR ALL
  TO __HOMIO_APPLICATION_ROLE__
  USING (true)
  WITH CHECK (true);

CREATE POLICY core002_outbox_tenant_guard
  ON __HOMIO_CORE002_SCHEMA__.outbox_publications
  AS RESTRICTIVE
  FOR ALL
  TO __HOMIO_APPLICATION_ROLE__
  USING (
    tenant_id = current_setting('app.tenant_id', true)::uuid
  )
  WITH CHECK (
    tenant_id = current_setting('app.tenant_id', true)::uuid
  );

REVOKE ALL ON TABLE
  __HOMIO_CORE002_SCHEMA__.events
  FROM PUBLIC, __HOMIO_APPLICATION_ROLE__;

REVOKE ALL ON TABLE
  __HOMIO_CORE002_SCHEMA__.outbox_publications
  FROM PUBLIC, __HOMIO_APPLICATION_ROLE__;

GRANT SELECT, INSERT ON TABLE
  __HOMIO_CORE002_SCHEMA__.events
  TO __HOMIO_APPLICATION_ROLE__;

GRANT SELECT, INSERT, UPDATE ON TABLE
  __HOMIO_CORE002_SCHEMA__.outbox_publications
  TO __HOMIO_APPLICATION_ROLE__;

REVOKE ALL ON FUNCTION
  __HOMIO_CORE002_SCHEMA__.reject_event_mutation()
  FROM PUBLIC, __HOMIO_APPLICATION_ROLE__;

REVOKE ALL ON FUNCTION
  __HOMIO_CORE002_SCHEMA__.enforce_outbox_transition()
  FROM PUBLIC, __HOMIO_APPLICATION_ROLE__;
