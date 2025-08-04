<p align="center">
  <img src="frontend/public/aci-dev-full-logo-light-bg.svg" alt="ACI.dev Logo" width="100%">
</p>

# ACI: Open-Source Infra to Power Unified MCP Servers and VibeOps

<p align="center">
  <a href="https://trendshift.io/repositories/13645" target="_blank">
    <img src="https://trendshift.io/api/badge/repositories/13645" alt="aipotheosis-labs%2Faci | Trendshift" style="width: 250px; height: 55px;" width="250" height="55"/>
  </a>
</p>

<p align="center">
  <a href="https://aci.dev/docs"><img src="https://img.shields.io/badge/Documentation-34a1bf" alt="Documentation"></a>
  <a href="https://badge.fury.io/py/aci-sdk"><img src="https://badge.fury.io/py/aci-sdk.svg" alt="PyPI version"></a>
  <a href="https://opensource.org/licenses/Apache-2.0"><img src="https://img.shields.io/badge/License-Apache_2.0-blue.svg" alt="License"></a>
  <a href="https://discord.com/invite/UU2XAnfHJh"><img src="https://img.shields.io/discord/1349424813550342275?logo=discord&label=Discord&color=7289DA" alt="Discord"></a>
  <a href="https://x.com/AipoLabs"><img src="https://img.shields.io/twitter/follow/AipoLabs?style=social" alt="Twitter Follow"></a>
</p>

> [!NOTE]
> This repo is for the ACI.dev platform. If you're looking for the **Unified MCP** server built with ACI.dev, see [aci-mcp](https://github.com/aipotheosis-labs/aci-mcp).

ACI.dev is the open-source tool-calling platform that hooks up 600+ tools into any agentic IDE or custom AI agent. It gives agents intent-aware access to tools with multi-tenant auth, granular permissions, and dynamic tool discovery—exposed as either direct function calls or through a **Unified Model-Context-Protocol (MCP) server**.

**Examples:** Instead of writing separate OAuth flows and API clients for Google Calendar, Slack, and more, use ACI.dev to manage authentication and provide AI agents with unified, secure function calls. Access these capabilities through our **Unified** [MCP server](https://github.com/aipotheosis-labs/aci-mcp) or via our lightweight [Python SDK](https://github.com/aipotheosis-labs/aci-python-sdk), compatible with any LLM framework.

Supercharge vibe coding and automate devOps by adding a single unified MCP server to your favourite agentic IDE. Configure the MCP with Vercel, Supabase, Cloudflare, and other platforms. Let AI handle provisioning, deployment, database configs, and debugging to turn a vibe coded prototype into a live product.

![ACI.dev Architecture](frontend/public/aci-architecture-intro.svg)

<p align="center">
  Join us on <a href="https://discord.com/invite/UU2XAnfHJh">Discord</a> to help shape the future of Open Source AI Infrastructure and VibeOps.<br/><br/>
  🌟 <strong>Star ACI.dev to stay updated on new releases!</strong><br/><br/>
  <a href="https://github.com/aipotheosis-labs/aci/stargazers">
    <img src="https://img.shields.io/github/stars/aipotheosis-labs/aci?style=social" alt="GitHub Stars">
  </a>
</p>

## 📺 Demo Video

[ACI.dev **Unified MCP Server** Demo](https://youtu.be/GSR9P53-_7E?feature=shared)

[![ACI.dev Unified MCP Server Demo](frontend/public/umcp-demo-thumbnail.png)](https://youtu.be/GSR9P53-_7E?feature=shared)

[ACI.dev **VibeOps** Demo](https://youtu.be/SfEtNqB6yqI?feature=shared)

[![ACI.dev VibeOps Demo](frontend/public/vibeops-thumbnail.jpg)](https://youtu.be/SfEtNqB6yqI?feature=shared)

## ✨ Key Features

- **600+ Pre-built Integrations**: Connect to popular services and apps in minutes.
- **Flexible Access Methods**: Use our unified MCP server or our lightweight SDK for direct function calling.
- **Multi-tenant Authentication**: Built-in OAuth flows and secrets management for both developers and end-users.
- **Enhanced Agent Reliability**: Natural language permission boundaries and dynamic tool discovery.
- **Framework & Model Agnostic**: Works with any LLM framework and agent architecture.
- **100% Open Source**: Everything released under Apache 2.0 (backend, dev portal, integrations).

## 💡 Why Use ACI.dev?

ACI.dev improves tool-calling reliability and accountability:

- **Authentication at Scale**: Connect multiple users to multiple services securely.
- **Discovery Without Overload**: Find and use the right tools without overwhelming LLM context windows.
- **Natural Language Permissions**: Control agent capabilities with human-readable boundaries.
- **Tool-use Logging**: See how your agent called tools and the issues it ran into.
- **Build Once, Run Anywhere**: No vendor lock-in with our open source, framework-agnostic approach.

## 🧰 Common Use Cases

- **VibeOps:** Automate devOps by letting your agentic IDE access Vercel, Supabase, Cloudflare, Sentry and more to ship live products.
- **Personal Assistant Chatbots:** Build chatbots that can search the web, manage calendars, send emails, interact with SaaS tools, etc.
- **Research Agent:** Conducts research on specific topics and syncs results to other apps (e.g., Notion, Google Sheets).
- **Outbound Sales Agent:** Automates lead generation, email outreach, and CRM updates.
- **Customer Support Agent:** Provides answers, manages tickets, and performs actions based on customer queries.

## 🔗 Quick Links

- **Managed Service:** [aci.dev](https://www.aci.dev/)
- **Documentation:** [aci.dev/docs](https://www.aci.dev/docs)
- **Available Tools List:** [aci.dev/tools](https://www.aci.dev/tools)
- **Python SDK:** [github.com/aipotheosis-labs/aci-python-sdk](https://github.com/aipotheosis-labs/aci-python-sdk)
- **Typescript SDK:** [github.com/aipotheosis-labs/aci-typescript-sdk](https://github.com/aipotheosis-labs/aci-typescript-sdk)
- **Unified MCP Server:** [github.com/aipotheosis-labs/aci-mcp](https://github.com/aipotheosis-labs/aci-mcp)
- **Agent Examples Built with ACI.dev:** [github.com/aipotheosis-labs/aci-agents](https://github.com/aipotheosis-labs/aci-agents)
- **Blog:** [aci.dev/blog](https://www.aci.dev/blog)
- **Community:** [Discord](https://discord.com/invite/UU2XAnfHJh) | [Twitter/X](https://x.com/AipoLabs) | [LinkedIn](https://www.linkedin.com/company/aci-dev-by-aipolabs/posts/?feedView=all)

## 💻 Getting Started: Local Development

To run the full ACI.dev platform (backend server and frontend portal) locally, follow the individual README files for each component:

- **Backend:** [backend/README.md](backend/README.md)
- **Frontend:** [frontend/README.md](frontend/README.md)

## 👋 Contributing

We welcome contributions! Please see our [CONTRIBUTING.md](CONTRIBUTING.md) for more information.

## Integration Requests

Missing any integrations (apps or functions) you need? Please see our [Integration Request Template](.github/ISSUE_TEMPLATE/integration_request.yml) and submit an integration request! Or, if you're feeling adventurous, you can submit a PR to add the integration yourself!

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=aipotheosis-labs/aci&type=Date)](https://www.star-history.com/#aipotheosis-labs/aci&Date)
