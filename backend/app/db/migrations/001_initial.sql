CREATE TABLE IF NOT EXISTS users (
  id VARCHAR(64) PRIMARY KEY,
  email VARCHAR(320) UNIQUE,
  display_name VARCHAR(255),
  created_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS projects (
  id VARCHAR(64) PRIMARY KEY,
  user_id VARCHAR(64) REFERENCES users(id),
  name VARCHAR(255) NOT NULL,
  description TEXT,
  status VARCHAR(32) NOT NULL,
  created_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS image_sets (
  id VARCHAR(64) PRIMARY KEY,
  project_id VARCHAR(64) NOT NULL REFERENCES projects(id),
  name VARCHAR(255),
  capture_group VARCHAR(255),
  status VARCHAR(32) NOT NULL,
  created_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS source_images (
  id VARCHAR(64) PRIMARY KEY,
  image_set_id VARCHAR(64) NOT NULL REFERENCES image_sets(id),
  storage_key VARCHAR(1024) NOT NULL,
  original_filename VARCHAR(512) NOT NULL,
  mime_type VARCHAR(128),
  file_size INTEGER,
  raw_format VARCHAR(64),
  camera_make VARCHAR(255),
  camera_model VARCHAR(255),
  lens_model VARCHAR(255),
  width INTEGER,
  height INTEGER,
  iso DOUBLE PRECISION,
  aperture DOUBLE PRECISION,
  shutter_speed VARCHAR(64),
  exposure_time DOUBLE PRECISION,
  exposure_bias DOUBLE PRECISION,
  focal_length DOUBLE PRECISION,
  capture_time TIMESTAMPTZ,
  black_level JSONB,
  white_level DOUBLE PRECISION,
  cfa_pattern JSONB,
  color_matrix JSONB,
  camera_wb JSONB,
  measured_luminance DOUBLE PRECISION,
  exposure_order INTEGER,
  relative_exposure_ratio DOUBLE PRECISION,
  is_reference BOOLEAN NOT NULL DEFAULT FALSE,
  audit_status VARCHAR(32) NOT NULL,
  audit_warnings JSONB,
  created_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS jobs (
  id VARCHAR(64) PRIMARY KEY,
  image_set_id VARCHAR(64) NOT NULL REFERENCES image_sets(id),
  status VARCHAR(32) NOT NULL,
  progress DOUBLE PRECISION NOT NULL,
  pipeline_name VARCHAR(128) NOT NULL,
  pipeline_version VARCHAR(128) NOT NULL,
  preset_name VARCHAR(128) NOT NULL,
  preset_version VARCHAR(128) NOT NULL,
  params JSONB,
  config_snapshot JSONB,
  output_artifact_id VARCHAR(64),
  error_message TEXT,
  created_at TIMESTAMPTZ NOT NULL,
  started_at TIMESTAMPTZ,
  completed_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS job_steps (
  id VARCHAR(64) PRIMARY KEY,
  job_id VARCHAR(64) NOT NULL REFERENCES jobs(id),
  step_name VARCHAR(128) NOT NULL,
  status VARCHAR(32) NOT NULL,
  progress DOUBLE PRECISION NOT NULL,
  metrics JSONB,
  warnings JSONB,
  artifacts JSONB,
  started_at TIMESTAMPTZ,
  completed_at TIMESTAMPTZ,
  error_message TEXT
);

CREATE TABLE IF NOT EXISTS artifacts (
  id VARCHAR(64) PRIMARY KEY,
  job_id VARCHAR(64) REFERENCES jobs(id),
  image_set_id VARCHAR(64) REFERENCES image_sets(id),
  source_image_id VARCHAR(64) REFERENCES source_images(id),
  artifact_type VARCHAR(128) NOT NULL,
  storage_key VARCHAR(1024) NOT NULL,
  mime_type VARCHAR(128),
  width INTEGER,
  height INTEGER,
  file_size INTEGER,
  metadata JSONB,
  created_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS presets (
  id VARCHAR(64) PRIMARY KEY,
  name VARCHAR(128) NOT NULL,
  version VARCHAR(128) NOT NULL,
  config JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL,
  UNIQUE(name, version)
);

CREATE TABLE IF NOT EXISTS pipeline_versions (
  id VARCHAR(64) PRIMARY KEY,
  name VARCHAR(128) NOT NULL,
  version VARCHAR(128) NOT NULL,
  git_sha VARCHAR(64),
  notes TEXT,
  created_at TIMESTAMPTZ NOT NULL,
  UNIQUE(name, version)
);

CREATE TABLE IF NOT EXISTS model_versions (
  id VARCHAR(64) PRIMARY KEY,
  name VARCHAR(128) NOT NULL,
  version VARCHAR(128) NOT NULL,
  purpose VARCHAR(128),
  storage_key VARCHAR(1024),
  metadata JSONB,
  created_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS feedback_events (
  id VARCHAR(64) PRIMARY KEY,
  job_id VARCHAR(64) REFERENCES jobs(id),
  event_type VARCHAR(128) NOT NULL,
  payload JSONB,
  created_at TIMESTAMPTZ NOT NULL
);

