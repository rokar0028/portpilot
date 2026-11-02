# PortPilot — Phase 2 Implementation Plan

## Goal

Replace the in-memory starter catalogue with a small PostgreSQL-backed catalogue that stores device specifications and their manufacturer evidence. The API should return the same useful device records after a restart, including explicit unknown values and source details.

## Starting point

At the start of Phase 2, FastAPI served one laptop and one hub from dictionaries. Records carried source links, but specs and evidence were not persisted or tied to individual capabilities. The public catalogue had fewer than five entries of either type.

## Data model

### Laptop model

Store an exact model or configuration identifier, brand, display name, region/variant where documented, operating system, and USB-C/HDMI capabilities used by checks. A specification that is not explicitly established remains `null`; do not convert missing documentation into `false`.

### Accessory model

Store an exact model identifier, brand, display name, category, host connection requirements, video outputs and modes, Power Delivery values, and supported peripheral features. Keep unknown capabilities nullable.

### Source evidence

Store official source title, URL, factual excerpt, checked date, and review status (`draft`, `verified`, or `needs_review`). Link each evidence record to exactly one laptop or accessory and to the capability key it supports. Keep evidence separate from capability columns so one device can cite multiple documents and each populated compatibility fact can be audited.

## Plan review

- Model variants matter: if a manufacturer documents different ports by processor/configuration, store the verified configuration in the catalogue identifier and display name.
- Evidence must map to a capability key, not only to the product as a whole; this prevents a general manual link from being treated as support for every field.
- Unknown values are represented as null. A missing specification is not a negative capability.
- The first migration will enforce exactly one device owner for each evidence row and valid evidence review statuses.

## Work plan

### 1. Define persistence and API contracts

- [x] Add SQLAlchemy models for laptops, accessories, and source evidence.
- [x] Add database constraints for unique device identifiers, valid categories/statuses, and evidence ownership.
- [x] Create Pydantic response schemas for devices, evidence, catalogue lists, and check inputs.
- [x] Keep the current check response contract stable while replacing internal dictionary lookups with repository/database lookups.
- [x] Return structured 404 errors for unknown device identifiers.

**Output:** a documented schema where unknown facts remain explicit and every published seed device has linked evidence.

### 2. Add migrations and database configuration

- [x] Add SQLAlchemy and Alembic to backend dependencies and configure Alembic against the application models.
- [x] Create migrations for the entities and constraints.
- [x] Read the database connection string from `DATABASE_URL`; keep secrets out of source control.
- [x] Add PostgreSQL to Docker Compose with a persistent named volume and a health check.
- [x] Make API startup wait for a healthy database in the Compose workflow and apply migrations explicitly.

**Output:** a fresh local PostgreSQL database can be created and upgraded from migrations.

### 3. Seed five evidence-backed laptops and five accessories

- [x] Keep the initial Lenovo IdeaPad Slim 3 14IRH10R and Anker 364 hub records.
- [x] Add four laptop entries with exact model/variant identification and manufacturer documentation.
- [x] Add four accessory entries with exact model identification and manufacturer documentation.
- [x] Preserve the manufacturer URL, concise factual excerpt, and checked date for each source.
- [x] Mark records `verified` only for facts directly supported by the linked source; leave unsupported fields null.
- [x] Make seeding idempotent so rerunning it updates or preserves records without duplicates.

**Output:** ten catalog records load into PostgreSQL, each with at least one official evidence record.

### 4. Move catalogue and check endpoints to the database

- [x] Query laptops and accessories from the configured database in `GET /devices`.
- [x] Add `GET /devices/laptops/{device_id}` and `GET /devices/accessories/{device_id}` detail routes.
- [x] Use database records for `POST /checks`; keep mode-limit evaluation for Phase 3.
- [x] Include capability-linked source evidence in catalogue responses and make the frontend selectors database-driven.
- [x] Keep records with incomplete specs visible; unknown values remain null.

**Output:** the frontend and API can discover all ten devices and view the sources used for each.

### 5. Document the data workflow

- [x] Document local database setup, migrations, and seeding in the README.
- [x] Document that the catalog is manually curated from official manufacturer pages/manuals.
- [x] Record source review statuses and missing facts as nullable values in the data/API schema.
- [x] Update Compose instructions and environment examples for `DATABASE_URL`.

**Output:** a contributor can rebuild the catalogue from an empty database by following the README.

## Suggested implementation order

1. Define ORM models and Pydantic schemas.
2. Configure SQLAlchemy sessions and Alembic, then create the initial migration.
3. Add PostgreSQL and environment configuration to Compose.
4. Add sourced device records and an idempotent seed command.
5. Move catalogue/check reads to the database.
6. Update API/frontend contracts and setup documentation.

## Phase 2 acceptance criteria

- [ ] A fresh PostgreSQL database upgrades successfully through Alembic. (Compose runtime could not be exercised because Docker Desktop's engine is stopped.)
- [x] Idempotent seeding creates five laptops and five accessories, each linked to official evidence; migration and seed ran locally on SQLite.
- [x] Missing specifications stay null and are not represented as unsupported capabilities.
- [x] Catalogue endpoints are typed and query records/evidence through SQLAlchemy.
- [x] `POST /checks` resolves selected records from the database and keeps the response shape.
- [ ] Compose starts PostgreSQL, API, and frontend in dependency order when Docker is available. (Compose configuration is valid; runtime pending.)
- [x] README instructions cover environment setup, migration, seeding, and local startup.

## Exit condition

Phase 2 is complete when a clean database can be migrated and seeded, the API can list and return all ten evidence-backed records, and the existing frontend can still request a check using database-backed catalogue records. Compatibility behavior expansion and scenario coverage remain Phase 3 work.
