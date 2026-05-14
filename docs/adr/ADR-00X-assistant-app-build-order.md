# ADR-00X: Assistant App Build Order

## Context
This ADR defines the step-by-step build order for the Assistant App.

## Decision
Follow the sequence below to ensure reproducible builds.

## Build Order
1. Install dependencies
2. Configure environment
3. Run database migrations
4. Build application
5. Run tests
6. Package artifacts

## Status
Accepted
