-- PostgreSQL-oriented target schema for the PLM demo.
-- The runnable local demo uses the same logical model through SQLAlchemy
-- and defaults to SQLite for zero-configuration setup.
CREATE TABLE IF NOT EXISTS app_state (
  id integer PRIMARY KEY,
  state_json jsonb NOT NULL,
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS products (
  id text PRIMARY KEY,
  plan_product_name text NOT NULL,
  product_domain text,
  product_family text,
  category text,
  subcategory text,
  offering text,
  variant text,
  lifecycle_state text,
  current_version text,
  business_owner text,
  product_manager text,
  technical_owner text,
  raw_json jsonb NOT NULL,
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS templates (
  id text PRIMARY KEY,
  template_name text NOT NULL,
  state text,
  product_domain text,
  product_family text,
  category text,
  subcategory text,
  offering_scope text,
  variant_scope text,
  owner text,
  raw_json jsonb NOT NULL,
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS product_requests (
  id text PRIMARY KEY,
  request_type text NOT NULL,
  product_id text,
  status text,
  risk_tier integer,
  owner text,
  raw_json jsonb NOT NULL,
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS approvals (
  id bigserial PRIMARY KEY,
  request_id text NOT NULL,
  stage text,
  approver_role text,
  approver text,
  decision text,
  decided_at timestamptz,
  raw_json jsonb NOT NULL
);

CREATE TABLE IF NOT EXISTS release_packages (
  request_id text PRIMARY KEY,
  package_id text,
  package_hash text,
  test_version text,
  production_version text,
  stage text,
  raw_json jsonb NOT NULL,
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS test_cases (
  id text PRIMARY KEY,
  request_id text NOT NULL,
  scenario_id text,
  scenario text,
  objective text,
  component text,
  test_type text,
  priority text,
  mandatory boolean NOT NULL DEFAULT true,
  expected_result text,
  latest_result text,
  raw_json jsonb NOT NULL
);

CREATE TABLE IF NOT EXISTS test_executions (
  id bigserial PRIMARY KEY,
  test_case_id text NOT NULL,
  actual_result text,
  result text,
  tester text,
  transaction_reference text,
  executed_at timestamptz,
  raw_json jsonb NOT NULL
);

CREATE TABLE IF NOT EXISTS defects (
  id text PRIMARY KEY,
  request_id text,
  test_case_id text,
  severity text,
  priority text,
  owner text,
  status text,
  raw_json jsonb NOT NULL
);

CREATE TABLE IF NOT EXISTS dependencies (
  id text PRIMARY KEY,
  product_id text NOT NULL,
  dependency_type text,
  target_entity_type text,
  target_entity_id text,
  authoritative_system text,
  criticality text,
  blocking boolean NOT NULL DEFAULT false,
  status text,
  raw_json jsonb NOT NULL
);

CREATE TABLE IF NOT EXISTS discrepancies (
  id text PRIMARY KEY,
  product_id text,
  request_id text,
  field_key text,
  expected_value text,
  actual_value text,
  source_of_truth text,
  severity text,
  owner text,
  status text,
  raw_json jsonb NOT NULL
);

CREATE TABLE IF NOT EXISTS audit_events (
  id bigserial PRIMARY KEY,
  event_key text UNIQUE NOT NULL,
  event_type text,
  entity_id text,
  actor text,
  environment text,
  raw_json jsonb NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS import_batches (
  id bigserial PRIMARY KEY,
  batch_id text UNIQUE NOT NULL,
  import_type text NOT NULL,
  file_name text NOT NULL,
  row_count integer NOT NULL DEFAULT 0,
  valid_count integer NOT NULL DEFAULT 0,
  error_count integer NOT NULL DEFAULT 0,
  status text,
  raw_json jsonb NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);

-- Demo v3 module-level persistence. This table becomes the authoritative
-- persistence contract for frontend modules during the incremental migration.
CREATE TABLE IF NOT EXISTS module_state (
  module_name varchar(64) PRIMARY KEY,
  data_json jsonb NOT NULL DEFAULT '{}'::jsonb,
  revision integer NOT NULL DEFAULT 1,
  updated_by varchar(255),
  updated_at timestamptz NOT NULL DEFAULT now()
);
