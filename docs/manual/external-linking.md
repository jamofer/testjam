# External linking

> Traducción: [external-linking.es.md](external-linking.es.md).

Testjam links bugs to external trackers without copying the data. Each bug stores a link to one or more external tickets (or work items, or issues, or stories — the wording depends on the provider) and renders them as chips in the bug context panel.

## Supported providers

| Provider | Auth method | Object linked |
|----------|-------------|---------------|
| GitHub Issues | personal access token | issue |
| Jira Cloud | API token (email + token) | issue |
| GitLab Issues | personal access token | issue |
| Azure DevOps | personal access token | work item |
| OpenProject | API key | work package |

The provider list is fixed in v1.0. The adapter pattern in `services/integrations/providers/` makes new providers cheap to add.

## Configuration

**Project → Integrations** lists every integration configured for the project. **New integration** opens a dialog asking for:

- **Provider** — one of the supported five
- **Base URL** — your tenant's API root (e.g. `https://your-org.atlassian.net`, `https://github.com`)
- **Credential** — token / API key, encrypted at rest with Fernet
- **Status mapping** — map Testjam bug statuses → provider status names. Used during pull-sync (see below)

A project can have multiple integrations of the same provider (e.g. two Jira tenants). Each integration carries an opaque name used in the bug context panel.

## Linking a bug

From the bug detail context panel, **Add link → External tracker** opens a dialog with:

- **Integration** — pick from the configured list
- **Action** — *Create new* (push) or *Link existing* (pull)

### Push (create)

Testjam crafts a new ticket on the external system using the bug title + description as body. Markdown is converted to the provider's native rich-text format (HTML for GitHub, ADF for Jira, etc.). The returned ticket id + URL are stored on the bug; the new chip appears in the context panel.

### Pull (link existing)

Paste a ticket URL or id. Testjam validates it against the integration's API and stores the link without creating anything. Useful when the ticket already exists in the external tracker.

In both cases the **Testjam bug URL** can be pasted into the external ticket as a back-link — there's no automatic round-trip in v1.0.

## Status sync

The status mapping you configured per-integration is used for **manual pull sync**: a button on each external link refreshes the cached status name from the provider. There's no background polling in v1.0; future versions may add scheduled sync.

Changing a bug's status in Testjam does **not** automatically push to the external tracker. Triggering the push is a separate explicit action (`Push status`) on the link chip. This is intentional — it avoids surprise updates on tickets owned by other teams.

## Token rotation

Edit the integration to paste a new credential. The old one is overwritten and re-encrypted. Existing links keep working with the new credential immediately; no re-link required.

## Permissions

| Action | Required role |
|--------|---------------|
| List integrations | viewer / tester / owner / admin |
| Add / edit / remove integration | owner / admin |
| Create or link external tickets | tester / owner / admin |
| Remove a link from a bug | tester / owner / admin (bug delete = owner/admin) |

## Security notes

- Credentials are encrypted at rest with the Fernet key configured in `INTEGRATION_ENCRYPTION_KEY`. Rotate this key by following the migration script in `scripts/rotate_fernet.py`.
- Failed authentication returns 503 with the provider's error message — never the credential.
- Push and pull both use the provider's official REST API; nothing is scraped.
- Integration tests cover the happy path per provider using a `FakeProvider` shim.
