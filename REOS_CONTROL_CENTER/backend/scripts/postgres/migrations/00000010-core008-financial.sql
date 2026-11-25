
BEGIN;

CREATE SCHEMA core008;

REVOKE ALL ON SCHEMA core008 FROM PUBLIC;
GRANT USAGE ON SCHEMA core008 TO __HOMIO_APPLICATION_ROLE__;

ALTER DEFAULT PRIVILEGES IN SCHEMA core008
  REVOKE ALL ON TABLES
  FROM PUBLIC, __HOMIO_APPLICATION_ROLE__;

CREATE TABLE core008.commission_contracts (
  commission_id text NOT NULL,
  tenant_id uuid NOT NULL,
  entitlement jsonb NOT NULL,
  basis jsonb NOT NULL,
  rate jsonb NOT NULL,
  eligibility_rules jsonb NOT NULL DEFAULT '[]'::jsonb,
  effective_from timestamptz NOT NULL,
  effective_to timestamptz,
  contract_version integer NOT NULL,
  provenance jsonb NOT NULL,
  state text NOT NULL DEFAULT 'DRAFT',
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb,

  CONSTRAINT core008_commission_contracts_pkey
    PRIMARY KEY (
      tenant_id,
      commission_id,
      contract_version
    ),

  CONSTRAINT core008_commission_contracts_tenant_fk
    FOREIGN KEY (tenant_id)
    REFERENCES core001.tenants (tenant_id)
    ON UPDATE RESTRICT
    ON DELETE RESTRICT,

  CONSTRAINT core008_commission_contracts_identity_check
    CHECK (char_length(commission_id) > 0),

  CONSTRAINT core008_commission_contracts_version_check
    CHECK (contract_version >= 1),

  CONSTRAINT core008_commission_contracts_state_check
    CHECK (
      state IN (
        'DRAFT',
        'ACTIVE',
        'SUSPENDED',
        'EXPIRED',
        'REVOKED'
      )
    ),

  CONSTRAINT core008_commission_contracts_effective_window_check
    CHECK (
      effective_to IS NULL
      OR effective_to > effective_from
    ),

  CONSTRAINT core008_commission_contracts_entitlement_check
    CHECK (
      jsonb_typeof(entitlement) = 'object'
      AND entitlement ?& ARRAY[
        'entitlement_id',
        'tenant_id',
        'entitled_party',
        'deal_reference',
        'ownership_reference',
        'provenance_reference'
      ]
      AND jsonb_typeof(entitlement->'entitled_party') = 'object'
      AND entitlement->>'tenant_id' = tenant_id::text
      AND char_length(entitlement->>'entitlement_id') > 0
      AND char_length(entitlement->>'deal_reference') > 0
      AND char_length(entitlement->>'ownership_reference') > 0
      AND char_length(entitlement->>'provenance_reference') > 0
      AND entitlement->'entitled_party' ?& ARRAY[
        'party_type',
        'party_id'
      ]
      AND entitlement->'entitled_party'->>'party_type' IN (
        'BROKER',
        'AGENT',
        'PARTNER',
        'BROKERAGE',
        'REFERRAL_PARTY'
      )
      AND char_length(
        entitlement->'entitled_party'->>'party_id'
      ) > 0
    ),

  CONSTRAINT core008_commission_contracts_basis_check
    CHECK (
      jsonb_typeof(basis) = 'object'
      AND basis ?& ARRAY[
        'basis_type',
        'source_reference'
      ]
      AND basis->>'basis_type' IN (
        'GROSS_TRANSACTION_VALUE',
        'NET_TRANSACTION_VALUE',
        'FIXED_TRANSACTION_AMOUNT',
        'REFERENCE_AMOUNT'
      )
      AND char_length(basis->>'source_reference') > 0
    ),

  CONSTRAINT core008_commission_contracts_rate_check
    CHECK (
      jsonb_typeof(rate) = 'object'
      AND rate ?& ARRAY[
        'rate_type',
        'value'
      ]
      AND rate->>'rate_type' IN (
        'PERCENTAGE',
        'FIXED_AMOUNT'
      )
      AND char_length(rate->>'value') > 0
    ),

  CONSTRAINT core008_commission_contracts_eligibility_array_check
    CHECK (
      jsonb_typeof(eligibility_rules) = 'array'
    ),

  CONSTRAINT core008_commission_contracts_provenance_check
    CHECK (
      jsonb_typeof(provenance) = 'object'
      AND provenance ?& ARRAY[
        'source_type',
        'source_reference',
        'captured_at',
        'evidence_reference'
      ]
      AND char_length(provenance->>'source_type') > 0
      AND char_length(provenance->>'source_reference') > 0
      AND char_length(provenance->>'captured_at') > 0
      AND char_length(provenance->>'evidence_reference') > 0
    ),

  CONSTRAINT core008_commission_contracts_metadata_object_check
    CHECK (
      jsonb_typeof(metadata) = 'object'
    )
);

CREATE INDEX core008_commission_contracts_tenant_state_effective_idx
  ON core008.commission_contracts (
    tenant_id,
    state,
    effective_from,
    effective_to
  );

CREATE TABLE core008.financial_ledger_entries (
  entry_id text NOT NULL,
  tenant_id uuid NOT NULL,
  commission_id text NOT NULL,
  entry_version integer NOT NULL,
  transaction_reference text NOT NULL,
  debit jsonb NOT NULL,
  credit jsonb NOT NULL,
  amount numeric NOT NULL,
  currency_code char(3) NOT NULL,
  currency_minor_unit integer NOT NULL,
  currency_rounding_mode text NOT NULL,
  entry_timestamp timestamptz NOT NULL,
  source_reference text NOT NULL,
  provenance_reference text NOT NULL,
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  immutable_fingerprint text NOT NULL,

  CONSTRAINT core008_financial_ledger_entries_pkey
    PRIMARY KEY (
      tenant_id,
      entry_id,
      entry_version
    ),

  CONSTRAINT core008_financial_ledger_entries_tenant_fk
    FOREIGN KEY (tenant_id)
    REFERENCES core001.tenants (tenant_id)
    ON UPDATE RESTRICT
    ON DELETE RESTRICT,

  CONSTRAINT core008_financial_ledger_entries_identity_check
    CHECK (
      char_length(entry_id) > 0
      AND char_length(commission_id) > 0
      AND char_length(transaction_reference) > 0
      AND char_length(source_reference) > 0
      AND char_length(provenance_reference) > 0
    ),

  CONSTRAINT core008_financial_ledger_entries_version_check
    CHECK (entry_version >= 1),

  CONSTRAINT core008_financial_ledger_entries_amount_check
    CHECK (
      amount > 0
      AND amount NOT IN (
        'NaN'::numeric,
        'Infinity'::numeric,
        '-Infinity'::numeric
      )
      AND amount = round(amount, currency_minor_unit)
    ),

  CONSTRAINT core008_financial_ledger_entries_currency_code_check
    CHECK (
      currency_code ~ '^[A-Z]{3}$'
    ),

  CONSTRAINT core008_financial_ledger_entries_currency_minor_unit_check
    CHECK (
      currency_minor_unit BETWEEN 0 AND 6
    ),

  CONSTRAINT core008_financial_ledger_entries_rounding_mode_check
    CHECK (
      currency_rounding_mode IN (
        'CEILING',
        'DOWN',
        'FLOOR',
        'HALF_DOWN',
        'HALF_EVEN',
        'HALF_UP',
        'UP'
      )
    ),

  CONSTRAINT core008_financial_ledger_entries_debit_check
    CHECK (
      jsonb_typeof(debit) = 'object'
      AND debit ?& ARRAY[
        'account_id',
        'account_type'
      ]
      AND char_length(debit->>'account_id') > 0
      AND char_length(debit->>'account_type') > 0
    ),

  CONSTRAINT core008_financial_ledger_entries_credit_check
    CHECK (
      jsonb_typeof(credit) = 'object'
      AND credit ?& ARRAY[
        'account_id',
        'account_type'
      ]
      AND char_length(credit->>'account_id') > 0
      AND char_length(credit->>'account_type') > 0
    ),

  CONSTRAINT core008_financial_ledger_entries_distinct_accounts_check
    CHECK (
      debit->>'account_id' <> credit->>'account_id'
    ),

  CONSTRAINT core008_financial_ledger_entries_metadata_object_check
    CHECK (
      jsonb_typeof(metadata) = 'object'
    ),

  CONSTRAINT core008_financial_ledger_entries_fingerprint_check
    CHECK (
      immutable_fingerprint ~ '^[a-f0-9]{64}$'
    )
);

CREATE INDEX core008_financial_ledger_entries_tenant_commission_idx
  ON core008.financial_ledger_entries (
    tenant_id,
    commission_id
  );

CREATE INDEX core008_financial_ledger_entries_tenant_time_idx
  ON core008.financial_ledger_entries (
    tenant_id,
    entry_timestamp DESC
  );

CREATE FUNCTION core008.reject_financial_record_mutation()
RETURNS trigger
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $function$
BEGIN
  RAISE EXCEPTION
    'CORE-008 immutable financial records cannot be updated or deleted'
    USING ERRCODE = '55000';
END;
$function$;

CREATE TRIGGER core008_commission_contracts_immutable
  BEFORE UPDATE OR DELETE
  ON core008.commission_contracts
  FOR EACH ROW
  EXECUTE FUNCTION core008.reject_financial_record_mutation();

CREATE TRIGGER core008_financial_ledger_entries_immutable
  BEFORE UPDATE OR DELETE
  ON core008.financial_ledger_entries
  FOR EACH ROW
  EXECUTE FUNCTION core008.reject_financial_record_mutation();

ALTER TABLE core008.commission_contracts
  ENABLE ROW LEVEL SECURITY;

ALTER TABLE core008.commission_contracts
  FORCE ROW LEVEL SECURITY;

CREATE POLICY core008_commission_contracts_application_access
  ON core008.commission_contracts
  AS PERMISSIVE
  FOR ALL
  TO __HOMIO_APPLICATION_ROLE__
  USING (true)
  WITH CHECK (true);

CREATE POLICY core008_commission_contracts_tenant_guard
  ON core008.commission_contracts
  AS RESTRICTIVE
  FOR ALL
  TO __HOMIO_APPLICATION_ROLE__
  USING (
    tenant_id = CASE
      WHEN pg_input_is_valid(
        current_setting('app.tenant_id', true),
        'uuid'
      )
      THEN current_setting('app.tenant_id', true)::uuid
      ELSE NULL::uuid
    END
  )
  WITH CHECK (
    tenant_id = CASE
      WHEN pg_input_is_valid(
        current_setting('app.tenant_id', true),
        'uuid'
      )
      THEN current_setting('app.tenant_id', true)::uuid
      ELSE NULL::uuid
    END
  );

ALTER TABLE core008.financial_ledger_entries
  ENABLE ROW LEVEL SECURITY;

ALTER TABLE core008.financial_ledger_entries
  FORCE ROW LEVEL SECURITY;

CREATE POLICY core008_financial_ledger_entries_application_access
  ON core008.financial_ledger_entries
  AS PERMISSIVE
  FOR ALL
  TO __HOMIO_APPLICATION_ROLE__
  USING (true)
  WITH CHECK (true);

CREATE POLICY core008_financial_ledger_entries_tenant_guard
  ON core008.financial_ledger_entries
  AS RESTRICTIVE
  FOR ALL
  TO __HOMIO_APPLICATION_ROLE__
  USING (
    tenant_id = CASE
      WHEN pg_input_is_valid(
        current_setting('app.tenant_id', true),
        'uuid'
      )
      THEN current_setting('app.tenant_id', true)::uuid
      ELSE NULL::uuid
    END
  )
  WITH CHECK (
    tenant_id = CASE
      WHEN pg_input_is_valid(
        current_setting('app.tenant_id', true),
        'uuid'
      )
      THEN current_setting('app.tenant_id', true)::uuid
      ELSE NULL::uuid
    END
  );

REVOKE ALL ON ALL TABLES IN SCHEMA core008
  FROM PUBLIC, __HOMIO_APPLICATION_ROLE__;

GRANT SELECT, INSERT ON TABLE
  core008.commission_contracts,
  core008.financial_ledger_entries
  TO __HOMIO_APPLICATION_ROLE__;

REVOKE ALL ON FUNCTION
  core008.reject_financial_record_mutation()
  FROM PUBLIC, __HOMIO_APPLICATION_ROLE__;

COMMIT;
