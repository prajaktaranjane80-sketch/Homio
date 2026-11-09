import {
  TokenVerificationError
} from "../../src/security/contracts.js";
import type {
  BackendSecurityRuntime,
  TrustedRequestContext,
  VerifiedExternalPrincipal
} from "../../src/security/contracts.js";

export const VALID_TEST_TOKEN = "test-bearer-token";

export const TEST_PRINCIPAL: VerifiedExternalPrincipal = {
  issuer: "https://identity.example.test/",
  subject: "provider-subject-001",
  audiences: ["homio-api"],
  clientId: "homio-frontend",
  tokenId: "test-access-token-jti-001"
};

export const TEST_CONTEXT: TrustedRequestContext = {
  identityId: "11111111-1111-4111-8111-111111111111",
  accountId: "22222222-2222-4222-8222-222222222222",
  tenantId: "33333333-3333-4333-8333-333333333333",
  tenantRevision: 2,
  organizationId: "44444444-4444-4444-8444-444444444444",
  membershipId: "55555555-5555-4555-8555-555555555555",
  membershipRevision: 3
};

export function createSecurityRuntime(
  overrides: Partial<BackendSecurityRuntime> = {}
): BackendSecurityRuntime {
  return {
    tokenVerifier: {
      verifyAccessToken: async (token) => {
        if (token !== VALID_TEST_TOKEN) {
          throw new TokenVerificationError("invalid");
        }
        return TEST_PRINCIPAL;
      }
    },
    sessionValidator: {
      isSessionActive: async () => true
    },
    contextResolver: {
      resolve: async () => TEST_CONTEXT
    },
    authorization: {
      authorize: async () => ({
        allowed: true,
        reasonCode: "ALLOWED"
      })
    },
    rateLimiter: {
      consume: async () => ({ allowed: true })
    },
    audit: {
      record: async () => undefined
    },
    ...overrides
  };
}
