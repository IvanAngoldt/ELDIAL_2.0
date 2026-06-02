-- ElDial: схема БД PostgreSQL
-- Логическая модель: users, projects, simulations, model_results, membranes, parameters

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE users (
    id              SERIAL PRIMARY KEY,
    login           VARCHAR(64) NOT NULL UNIQUE,
    password_hash   VARCHAR(256) NOT NULL,
    full_name       VARCHAR(128),
    organization    VARCHAR(256),
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE projects (
    id              SERIAL PRIMARY KEY,
    user_id         INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name            VARCHAR(256) NOT NULL,
    description     TEXT,
    process_type    VARCHAR(16) DEFAULT 'ED',
    transport_model VARCHAR(32) DEFAULT 'nernst_planck',
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE membranes (
    id                      SERIAL PRIMARY KEY,
    project_id              INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    membrane_pairs          INTEGER NOT NULL DEFAULT 20,
    effective_area_m2       DOUBLE PRECISION NOT NULL DEFAULT 0.32,
    channel_thickness_mm    DOUBLE PRECISION NOT NULL DEFAULT 0.75,
    channel_length_m        DOUBLE PRECISION NOT NULL DEFAULT 0.48,
    cation_transfer_number  DOUBLE PRECISION NOT NULL DEFAULT 0.92,
    anion_transfer_number   DOUBLE PRECISION NOT NULL DEFAULT 0.04,
    membrane_resistivity    DOUBLE PRECISION NOT NULL DEFAULT 3.5,
    diffusion_coefficient   DOUBLE PRECISION NOT NULL DEFAULT 1.2e-9
);

CREATE TABLE parameters (
    id                          SERIAL PRIMARY KEY,
    project_id                  INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    nacl_concentration_g_l      DOUBLE PRECISION NOT NULL DEFAULT 5.0,
    temperature_c               DOUBLE PRECISION NOT NULL DEFAULT 25.0,
    ph                          DOUBLE PRECISION NOT NULL DEFAULT 7.2,
    voltage_v                   DOUBLE PRECISION NOT NULL DEFAULT 12.0,
    volumetric_flow_l_min       DOUBLE PRECISION NOT NULL DEFAULT 2.5,
    simulation_time_s           DOUBLE PRECISION NOT NULL DEFAULT 7200,
    time_step_s                 DOUBLE PRECISION NOT NULL DEFAULT 0.5,
    grid_nodes                  INTEGER NOT NULL DEFAULT 100,
    boundary_condition          VARCHAR(64) DEFAULT 'constant_voltage',
    initial_diluate_conc        DOUBLE PRECISION NOT NULL DEFAULT 5.0,
    initial_concentrate_conc    DOUBLE PRECISION NOT NULL DEFAULT 0.5,
    updated_at                  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE simulations (
    id              SERIAL PRIMARY KEY,
    project_id      INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    status          VARCHAR(32) NOT NULL DEFAULT 'draft',
    started_at      TIMESTAMP,
    finished_at     TIMESTAMP,
    error_message   TEXT,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE model_results (
    id                          SERIAL PRIMARY KEY,
    simulation_id               INTEGER NOT NULL REFERENCES simulations(id) ON DELETE CASCADE,
    demineralization_degree_pct DOUBLE PRECISION,
    specific_energy_kwh_m3      DOUBLE PRECISION,
    current_efficiency_pct      DOUBLE PRECISION,
    average_current_a           DOUBLE PRECISION,
    result_json                 JSONB,
    created_at                  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE time_series_data (
    id                      SERIAL PRIMARY KEY,
    model_result_id         INTEGER NOT NULL REFERENCES model_results(id) ON DELETE CASCADE,
    time_min                DOUBLE PRECISION NOT NULL,
    diluate_concentration   DOUBLE PRECISION,
    concentrate_concentration DOUBLE PRECISION,
    current_a               DOUBLE PRECISION,
    voltage_v               DOUBLE PRECISION,
    power_w                 DOUBLE PRECISION,
    current_density_a_m2    DOUBLE PRECISION
);

CREATE TABLE reports (
    id              SERIAL PRIMARY KEY,
    simulation_id   INTEGER NOT NULL REFERENCES simulations(id) ON DELETE CASCADE,
    title           VARCHAR(512) NOT NULL,
    author          VARCHAR(128),
    format          VARCHAR(16) DEFAULT 'pdf',
    file_path       TEXT,
    sections        JSONB,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_projects_user ON projects(user_id);
CREATE INDEX idx_simulations_project ON simulations(project_id);
CREATE INDEX idx_model_results_simulation ON model_results(simulation_id);
