# AIMS Engineering Standards

## Directory Convention

```
backend/
├── api
├── agents
├── services
├── repositories
├── models
├── schemas
├── tasks
└── utils
```

## Naming Rules

Python:

- Files: snake_case
- Classes: PascalCase
- Functions: snake_case

Frontend:

- Components: PascalCase.tsx
- Hooks: useXxx
- API modules: xxx.ts

## Git Commit Convention

Format:

```
type(scope): message
```

Examples:

```
feat(agent): add market collector
fix(api): fix report endpoint
docs(spec): update specification
refactor(storage): improve repository
```

## Development Principle

Data first, API second, UI third.
