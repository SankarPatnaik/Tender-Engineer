# TenderEngineerCrew Crew

Welcome to the TenderEngineerCrew Crew project, powered by [crewAI](https://crewai.com). This template is designed to help you set up a multi-agent AI system with ease, leveraging the powerful and flexible framework provided by crewAI. Our goal is to enable your agents to collaborate effectively on complex tasks, maximizing their collective intelligence and capabilities.

## Installation

Ensure you have Python >=3.10 <3.14 installed on your system. This project uses [UV](https://docs.astral.sh/uv/) for dependency management and package handling, offering a seamless setup and execution experience.

First, if you haven't already, install uv:

```bash
pip install uv
```

Next, navigate to your project directory and install the dependencies:

(Optional) Lock the dependencies and install them by using the CLI command:
```bash
crewai install
```
### Customizing

**Add your `OPENAI_API_KEY` into the `.env` file**

- Modify `src/tender_engineer_crew/config/agents.yaml` to define your agents
- Modify `src/tender_engineer_crew/config/tasks.yaml` to define your tasks
- Modify `src/tender_engineer_crew/crew.py` to add your own logic, tools and specific args
- Modify `src/tender_engineer_crew/main.py` to add custom inputs for your agents and tasks

## Running the Project

To kickstart your crew of AI agents and begin task execution, run this from the root folder of your project:

```bash
$ crewai run
```

This command initializes the Tender-Engineer-Crew Crew, assembling the agents and assigning them tasks as defined in your configuration.

This example, unmodified, will run the create a `report.md` file with the output of a research on LLMs in the root folder.

## Understanding Your Crew

The Tender-Engineer-Crew Crew is composed of multiple AI agents, each with unique roles, goals, and tools. These agents collaborate on a series of tasks, defined in `config/tasks.yaml`, leveraging their collective skills to achieve complex objectives. The `config/agents.yaml` file outlines the capabilities and configurations of each agent in your crew.

## Support

For support, questions, or feedback regarding the TenderEngineerCrew Crew or crewAI.
- Visit our [documentation](https://docs.crewai.com)
- Reach out to us through our [GitHub repository](https://github.com/joaomdmoura/crewai)
- [Join our Discord](https://discord.com/invite/X4JWnZnxPb)
- [Chat with our docs](https://chatg.pt/DWjSBZn)

Let's create wonders together with the power and simplicity of crewAI.


## MongoDB Setup for Tender + Vendor Costing

This project now includes a MongoDB schema initializer for the power tender workflow. It creates and validates:

- **Vendor collection** (`MONGODB_COLLECTION`, default `vendors`) for vendor profiles used in semantic matching.
- **Tender collection** (`TENDER_MONGODB_COLLECTION`, default `tender_documents`) for uploaded tender files, extracted summaries, vendor matches, and cost estimates.

### Required environment variables

- `MONGODB_URI`
- `MONGODB_DB`
- `MONGODB_COLLECTION` (optional, defaults to `vendors`)
- `TENDER_MONGODB_COLLECTION` (optional, defaults to `tender_documents`)

### Initialize database schema

```bash
uv run init_mongodb_schema
```

This command creates collections (if missing), applies JSON schema validators, and creates indexes for status/date/vendor lookup performance.
