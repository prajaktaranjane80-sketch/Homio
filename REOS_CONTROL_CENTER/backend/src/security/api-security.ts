export function isValidApiRouteSecurityContract(
  routeOptions: ApiRouteRegistration
): boolean {
  const config = isRecord(routeOptions.config)
    ? routeOptions.config
    : undefined;

  const policy = config?.homioSecurity as
    | ApiRouteSecurityPolicy
    | undefined;

  if (
    policy === undefined ||
    !isValidApiRouteSecurityPolicy(policy)
  ) {
    return false;
  }

  const methods = Array.isArray(routeOptions.method)
    ? routeOptions.method
    : [routeOptions.method];

  if (
    methods.length === 0 ||
    !methods.every(
      (method) =>
        typeof method === "string" &&
        method.length > 0 &&
        method === method.toUpperCase()
    )
  ) {
    return false;
  }

  const normalizedMethods = methods as string[];

  const isMutation = normalizedMethods.some(
    (method) => !READ_ONLY_METHODS.has(method)
  );

  const schema = isRecord(routeOptions.schema)
    ? routeOptions.schema
    : undefined;

  const hasPathParameters =
    typeof routeOptions.url === "string" &&
    /(?:^|\/):[A-Za-z][A-Za-z0-9_]*/.test(routeOptions.url);

  // Every parameterized route needs an explicit params schema,
  // including read-only routes.
  if (
    hasPathParameters &&
    (
      schema === undefined ||
      !isRecord(schema.params)
    )
  ) {
    return false;
  }

  if (isMutation) {
    if (schema === undefined) {
      return false;
    }

    if (
      normalizedMethods.some((method) =>
        METHODS_REQUIRING_BODY_SCHEMA.has(method)
      ) &&
      !isRecord(schema.body)
    ) {
      return false;
    }

    // A public mutation must be explicit. A protected mutation
    // must be reauthorized immediately before its handler.
    if (policy.public !== true) {
      if (!isProtectedPolicy(policy)) {
        return false;
      }

      if (policy.reauthorizeBeforeMutation !== true) {
        return false;
      }
    }
  } else if (
    isProtectedPolicy(policy) &&
    policy.reauthorizeBeforeMutation === true
  ) {
    return false;
  }

  return true;
}
