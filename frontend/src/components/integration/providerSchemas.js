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
  jira: [
    {
      key: "base_url",
      label: "Base URL",
      placeholder: "https://acme.atlassian.net",
      required: true,
      help: "Site root, no trailing slash.",
    },
    {
      key: "project_key",
      label: "Project key",
      placeholder: "TJ",
      required: true,
    },
    {
      key: "issue_type",
      label: "Issue type",
      placeholder: "Bug",
      required: false,
      help: "Defaults to Bug. Use any type your workflow accepts.",
    },
    {
      key: "email",
      label: "Atlassian account email",
      placeholder: "alice@acme.com",
      required: false,
      help: "Required for Atlassian Cloud (Basic auth). Leave empty for Server/DC PAT.",
    },
  ],
  gitlab: [
    {
      key: "project",
      label: "Project",
      placeholder: "acme/awesome  (or numeric id)",
      required: true,
      help: "Full path (group/subgroup/project) or numeric project id.",
    },
    {
      key: "base_url",
      label: "Base URL (self-hosted only)",
      placeholder: "https://gitlab.com",
      required: false,
      help: "Leave empty for gitlab.com.",
    },
  ],
  azure_devops: [
    {
      key: "organization_url",
      label: "Organization URL",
      placeholder: "https://dev.azure.com/acme",
      required: true,
      help: "Site root, no trailing slash.",
    },
    {
      key: "project",
      label: "Project",
      placeholder: "Widgets",
      required: true,
    },
    {
      key: "work_item_type",
      label: "Work item type",
      placeholder: "Bug",
      required: false,
      help: "Defaults to Bug. Match a type your process template ships.",
    },
  ],
  openproject: [
    {
      key: "base_url",
      label: "Base URL",
      placeholder: "https://openproject.example.org",
      required: true,
      help: "Site root, no trailing slash.",
    },
    {
      key: "project",
      label: "Project",
      placeholder: "myproject  (identifier or numeric id)",
      required: true,
    },
    {
      key: "type_id",
      label: "Work-package type id",
      placeholder: "1",
      required: false,
      help: "Numeric id of the type (Bug, Task…). Leave empty to use the project default.",
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
