# My agent: expense-tracker
One-liner: A conversational agent that helps individuals track, categorize, and analyze their expenses across multiple payment methods (credit card, bank account, cash) with manual entry and notification ingestion, backed by an interactive catalog of transactions, period tabs (daily, monthly, yearly), category spending stats, and export capabilities.

Tool coverage:
- Memory: Monthly and annual budget caps, savings targets, default currency, preferred payment methods (credit cards, accounts, cash), recurring bills/subscriptions, and merchant auto-categorization preferences.
- Tools:
  - `log_expense(amount, category, merchant, payment_method, note, date)`: Records manual or parsed transactions.
  - `parse_notification(raw_text)`: Extracts transaction details from simulated SMS or email receipt text.
  - `get_expense_stats(period, category, payment_method)`: Aggregates spending totals, category breakdowns, and payment method distributions.
  - `export_expenses(format, period)`: Generates export files in JSON, CSV/XLS, or PDF formats.
  - `get_budget_status()`: Computes remaining budget and alerts on category threshold overruns.
- Catalog/UI:
  - Interactive transaction cards displaying merchant, amount, category badge, and payment method icon.
  - Tabular breakdown tables with daily, monthly, and yearly views.
  - Category spending breakdown tables and stats summary cards rendered via A2UI.
- Image gen: Category spending breakdown infographics, budget milestone badge graphics, and receipt preview cards.
- Sandbox: Code sandbox execution to compute category percentages, compound interest/savings forecasts, budget burn-rate projections, and file generation for spreadsheet/pdf data exports.

Recommended for every project: memory, storage, tools, image generation, A2UI
Agent-specific / stretch (pick what fits): Code sandbox for financial analysis and export file generation, multi-format export tool (JSON/XLS/PDF), Cloud Trace observability for transaction latency.
