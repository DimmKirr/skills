# Security Policy

## Reporting a vulnerability

If you discover a security issue in this project, please report it responsibly.

**Email:** dmitry@hazelops.com

Please include:
- Description of the vulnerability
- Steps to reproduce
- Potential impact

You will receive a response within 72 hours. Please do not open a public issue for security vulnerabilities.

## Scope

Security concerns for this project include:

- **Prompt injection in SKILL.md:** skill instructions that could cause an agent to execute unintended actions
- **Credential exposure:** secrets, API keys, or tokens embedded in skill files or references
- **YAML frontmatter injection:** values containing `<` or `>` that could be interpreted as XML/HTML in the instruction body
- **Path traversal:** references or scripts that access files outside the expected scope

## Supported versions

| Version | Supported |
|---------|-----------|
| 0.1.x | Yes |
