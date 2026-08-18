-- 0002 Principal context
--
-- Resolving "who is this and which tenants may they act in" has a bootstrap
-- problem: the answer is a set of tenants, so the query cannot be scoped by a
-- tenant. The obvious fixes are both bad — a SECURITY DEFINER function that
-- runs as a superuser hands RLS-free access to whatever calls it, and granting
-- the API BYPASSRLS defeats the entire policy layer.
--
-- Instead the transaction carries a second piece of context: the verified user.
-- Policies then permit a row when it belongs to the tenant in context OR when
-- it belongs to the user in context. Both settings come from server-verified
-- identity (ADR-014); neither is ever read from a request.

BEGIN;

CREATE OR REPLACE FUNCTION app.current_user_id()
RETURNS text
LANGUAGE sql
STABLE
AS $$
  SELECT nullif(current_setting('app.user_id', true), '');
$$;

-- A user may always see their own memberships, in any tenant, so that identity
-- resolution can run before a tenant is known. They may still only see other
-- people's memberships within the tenant in context.
DROP POLICY memberships_in_context ON app.memberships;

CREATE POLICY memberships_readable ON app.memberships
  FOR SELECT
  USING (
    tenant_id = app.current_tenant_id()
    OR user_id = app.current_user_id()
  );

-- Writes stay strictly tenant-scoped: being a member of a tenant does not
-- permit granting yourself membership of another one.
CREATE POLICY memberships_writable ON app.memberships
  FOR ALL
  USING (tenant_id = app.current_tenant_id())
  WITH CHECK (tenant_id = app.current_tenant_id());

-- A tenant record is visible in context, or to a user who belongs to it. The
-- inner lookup is itself policy-filtered, and the membership read policy above
-- is what makes it resolvable.
DROP POLICY tenants_in_context ON app.tenants;

CREATE POLICY tenants_readable ON app.tenants
  FOR SELECT
  USING (
    id = app.current_tenant_id()
    OR EXISTS (
      SELECT 1 FROM app.memberships m
      WHERE m.tenant_id = app.tenants.id
        AND m.user_id = app.current_user_id()
    )
  );

CREATE POLICY tenants_writable ON app.tenants
  FOR ALL
  USING (id = app.current_tenant_id())
  WITH CHECK (id = app.current_tenant_id());

COMMIT;
