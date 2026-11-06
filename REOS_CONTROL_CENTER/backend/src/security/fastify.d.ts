import type {
  ApiRouteSecurityPolicy,
  TrustedRequestContext
} from "./contracts.js";

declare module "fastify" {
  interface FastifyContextConfig {
    homioSecurity?: ApiRouteSecurityPolicy;
  }

  interface FastifyRequest {
    securityContext: TrustedRequestContext | null;
  }
}

export {};
