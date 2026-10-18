/** Fixed display copy only. Never interpolate provider responses or exception text. */
export const generationErrors: Record<string, string> = {
  incomplete_response: "The provider did not finish its response. No revision was saved. Review output limits before retrying.",
  invalid_response: "The provider did not return a valid structured draft. No revision was saved.",
  invalid_artifact: "The generated draft did not satisfy the handoff rules. No revision was saved. Review the sources or provider settings before retrying.",
  provider_timeout: "The provider request timed out. A retry may repeat a billable call.",
  provider_http_error: "The provider rejected the request. Check the endpoint, model, credentials and account status before retrying.",
  provider_transport_error: "The provider connection failed. Check connectivity and the configured endpoint before retrying.",
  response_too_large: "The provider response exceeded the supported size. No revision was saved.",
  secret_in_request: "Generation was blocked because selected content contains the configured credential. Remove it from the evidence before continuing.",
  secret_in_response: "The provider response was rejected because it contained the configured credential. No revision was saved.",
  invalid_sources: "Selected evidence does not meet the supported source limits. Review the selection before continuing.",
  invalid_configuration: "Provider configuration is invalid. Review the local settings before continuing.",
  generation_failed: "This saved generation attempt failed, but its specific cause was not recorded. This version preserves known provider failure categories on new attempts. Retrying may incur another charge.",
};

export function generationError(code: string): string {
  return Object.hasOwn(generationErrors, code)
    ? generationErrors[code]
    : "The workflow failed. Inspect the saved state before choosing an explicit retry.";
}
