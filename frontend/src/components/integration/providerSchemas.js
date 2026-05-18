// Per-provider config field schemas used by the New Integration wizard.
// Keep in sync with the backend provider.validate_config implementations.

export const PROVIDER_FIELDS = {
  github: [
    {
      key: "owner",
      label: "Owner",
      placeholder: "acme",
      required: true,
      help: "GitHub user or organization that owns the repo.",
    },
    {
      key: "repo",
      label: "Repository",
      placeholder: "awesome-app",
      required: true,
    },
    {
      key: "api_base",
      label: "API base URL (Enterprise only)",
      placeholder: "https://api.github.com",
      required: false,
      help: "Leave empty for github.com.",
    },
  ],
}

export function buildProviderConfig(provider, values) {
  const fields = PROVIDER_FIELDS[provider] ?? []
  const config = {}
  for (const field of fields) {
    const value = values[field.key]
    if (value !== undefined && value !== "") {
      config[field.key] = value
    }
  }
  return config
}
