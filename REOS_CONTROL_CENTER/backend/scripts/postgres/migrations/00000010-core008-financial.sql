CREATE TABLE core008.commission_contracts (
  commission_id text NOT NULL,
  tenant_id uuid NOT NULL,

  entitlement jsonb NOT NULL,
  basis jsonb NOT NULL,
  rate jsonb NOT NULL,
  eligibility_rules jsonb NOT NULL,

  effective_from timestamp with time zone NOT NULL,
  effective_to timestamp with time zone,

  contract_version integer NOT NULL,

  provenance jsonb NOT NULL,

  state text NOT NULL DEFAULT 'DRAFT',

  metadata jsonb NOT NULL DEFAULT '{}'::jsonb,

  CONSTRAINT commission_contracts_pkey
    PRIMARY KEY (
      tenant_id,
      commission_id,
      contract_version
    ),

  CONSTRAINT commission_contracts_tenant_fk
    FOREIGN KEY (tenant_id)
    REFERENCES core001.tenants (tenant_id),

  CONSTRAINT commission_contracts_commission_id_check
    CHECK (
      commission_id = btrim(commission_id)
      AND length(commission_id) > 0
    ),

  CONSTRAINT commission_contracts_entitlement_object_check
    CHECK (jsonb_typeof(entitlement) = 'object'),

  CONSTRAINT commission_contracts_basis_object_check
    CHECK (jsonb_typeof(basis) = 'object'),

  CONSTRAINT commission_contracts_rate_object_check
    CHECK (jsonb_typeof(rate) = 'object'),

  CONSTRAINT commission_contracts_eligibility_array_check
    CHECK (jsonb_typeof(eligibility_rules) = 'array'),

  CONSTRAINT commission_contracts_provenance_object_check
    CHECK (jsonb_typeof(provenance) = 'object'),

  CONSTRAINT commission_contracts_metadata_object_check
    CHECK (jsonb_typeof(metadata) = 'object'),

  CONSTRAINT commission_contracts_effective_window_check
    CHECK (
      effective_to IS NULL
      OR effective_to > effective_from
    ),

  CONSTRAINT commission_contracts_version_check
    CHECK (contract_version > 0),

  CONSTRAINT commission_contracts_state_check
    CHECK (
      state IN (
        'DRAFT',
        'ACTIVE',
        'SUSPENDED',
        'EXPIRED',
        'REVOKED'
      )
    )
);

CREATE INDEX commission_contracts_tenant_state_effective_idx
  ON core008.commission_contracts (
    tenant_id,
    state,
    effective_from DESC
  );

ALTER TABLE core008.commission_contracts
  ENABLE ROW LEVEL SECURITY;

ALTER TABLE core008.commission_contracts
  FORCE ROW LEVEL SECURITY;

CREATE POLICY commission_contracts_application_access
  ON core008.commission_contracts
  AS PERMISSIVE
  FOR ALL
  TO __HOMIO_APPLICATION_ROLE__
  USING (true)
  WITH CHECK (true);

CREATE POLICY commission_contracts_tenant_guard
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

CREATE FUNCTION core008.reject_commission_contract_mutation()
RETURNS trigger
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $function$
BEGIN
  RAISE EXCEPTION
    'CORE-008 commission contract versions are immutable'
    USING ERRCODE = '55000';
END;
$function$;

CREATE TRIGGER commission_contracts_immutable
  BEFORE UPDATE OR DELETE
  ON core008.commission_contracts
  FOR EACH ROW
  EXECUTE FUNCTION
    core008.reject_commission_contract_mutation();

REVOKE ALL ON FUNCTION
  core008.reject_commission_contract_mutation()
FROM PUBLIC, __HOMIO_APPLICATION_ROLE__;

CREATE TABLE core008.financial_ledger_entries (
  entry_id text NOT NULL,
  tenant_id uuid NOT NULL,

  commission_id text NOT NULL,
  entry_version integer NOT NULL,

  transaction_reference text NOT NULL,

  debit_account_id text NOT NULL,
  debit_account_type text NOT NULL,

  credit_account_id text NOT NULL,
  credit_account_type text NOT NULL,

  amount numeric NOT NULL,

  currency_code text NOT NULL,
  currency_minor_unit smallint NOT NULL,
  currency_rounding_mode text NOT NULL,

  entry_timestamp timestamp with time zone NOT NULL,

  source_reference text NOT NULL,
  provenance_reference text NOT NULL,

  metadata jsonb NOT NULL DEFAULT '{}'::jsonb,

  CONSTRAINT financial_ledger_entries_pkey
    PRIMARY KEY (
      tenant_id,
      entry_id,
      entry_version
    ),

  CONSTRAINT financial_ledger_entries_tenant_fk
    FOREIGN KEY (tenant_id)
    REFERENCES core001.tenants (tenant_id),

  CONSTRAINT financial_ledger_entries_entry_id_check
    CHECK (
      entry_id = btrim(entry_id)
      AND length(entry_id) > 0
    ),

  CONSTRAINT financial_ledger_entries_commission_id_check
    CHECK (
      commission_id = btrim(commission_id)
      AND length(commission_id) > 0
    ),

  CONSTRAINT financial_ledger_entries_transaction_reference_check
    CHECK (
      transaction_reference = btrim(transaction_reference)
      AND length(transaction_reference) > 0
    ),

  CONSTRAINT financial_ledger_entries_debit_account_id_check
    CHECK (
      debit_account_id = btrim(debit_account_id)
      AND length(debit_account_id) > 0
    ),

  CONSTRAINT financial_ledger_entries_debit_account_type_check
    CHECK (
      debit_account_type = btrim(debit_account_type)
      AND length(debit_account_type) > 0
    ),

  CONSTRAINT financial_ledger_entries_credit_account_id_check
    CHECK (
      credit_account_id = btrim(credit_account_id)
      AND length(credit_account_id) > 0
    ),

  CONSTRAINT financial_ledger_entries_credit_account_type_check
    CHECK (
      credit_account_type = btrim(credit_account_type)
      AND length(credit_account_type) > 0
    ),

  CONSTRAINT financial_ledger_entries_distinct_accounts_check
    CHECK (debit_account_id <> credit_account_id),

  CONSTRAINT financial_ledger_entries_version_check
    CHECK (entry_version > 0),

  CONSTRAINT financial_ledger_entries_amount_finite_check
    CHECK (
      amount NOT IN (
        'NaN'::numeric,
        'Infinity'::numeric,
        '-Infinity'::numeric
      )
    ),

  CONSTRAINT financial_ledger_entries_currency_code_check
    CHECK (currency_code ~ '^[A-Z]{3}$'),

  CONSTRAINT financial_ledger_entries_currency_minor_unit_check
    CHECK (
      currency_minor_unit BETWEEN 0 AND 6
    ),

  CONSTRAINT financial_ledger_entries_rounding_mode_check
    CHECK (
      currency_rounding_mode IN (
        'ROUND_CEILING',
        'ROUND_DOWN',
        'ROUND_FLOOR',
        'ROUND_HALF_DOWN',
        'ROUND_HALF_EVEN',
        'ROUND_HALF_UP',
        'ROUND_UP'
      )
    ),

  CONSTRAINT financial_ledger_entries_currency_precision_check
    CHECK (
      amount = round(
        amount,
        currency_minor_unit
      )
    ),

  CONSTRAINT financial_ledger_entries_source_reference_check
    CHECK (
      source_reference = btrim(source_reference)
      AND length(source_reference) > 0
    ),

  CONSTRAINT financial_ledger_entries_provenance_reference_check
    CHECK (
      provenance_reference = btrim(provenance_reference)
      AND length(provenance_reference) > 0
    ),

  CONSTRAINT financial_ledger_entries_metadata_object_check
    CHECK (jsonb_typeof(metadata) = 'object')
);

CREATE INDEX financial_ledger_entries_tenant_commission_time_idx
  ON core008.financial_ledger_entries (
    tenant_id,
    commission_id,
    entry_timestamp DESC
  );

CREATE INDEX financial_ledger_entries_tenant_time_idx
  ON core008.financial_ledger_entries (
    tenant_id,
    entry_timestamp DESC,
    entry_id
  );

ALTER TABLE core008.financial_ledger_entries
  ENABLE ROW LEVEL SECURITY;

ALTER TABLE core008.financial_ledger_entries
  FORCE ROW LEVEL SECURITY;

CREATE POLICY financial_ledger_entries_application_access
  ON core008.financial_ledger_entries
  AS PERMISSIVE
  FOR ALL
  TO __HOMIO_APPLICATION_ROLE__
  USING (true)
  WITH CHECK (true);

CREATE POLICY financial_ledger_entries_tenant_guard
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

CREATE FUNCTION core008.reject_financial_ledger_mutation()
RETURNS trigger
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $function$
BEGIN
  RAISE EXCEPTION
    'CORE-008 financial ledger entries are append-only'
    USING ERRCODE = '55000';
END;
$function$;

CREATE TRIGGER financial_ledger_entries_append_only
  BEFORE UPDATE OR DELETE
  ON core008.financial_ledger_entries
  FOR EACH ROW
  EXECUTE FUNCTION
    core008.reject_financial_ledger_mutation();

REVOKE ALL ON FUNCTION
  core008.reject_financial_ledger_mutation()
FROM PUBLIC, __HOMIO_APPLICATION_ROLE__;

REVOKE ALL ON TABLE
  core008.commission_contracts,
  core008.financial_ledger_entries
FROM PUBLIC, __HOMIO_APPLICATION_ROLE__;

GRANT SELECT, INSERT ON TABLE
  core008.commission_contracts,
  core008.financial_ledger_entries
TO __HOMIO_APPLICATION_ROLE__;
