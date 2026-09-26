--
-- PostgreSQL database dump
--

-- Dumped from database version 15.8 (Debian 15.8-1.pgdg110+1)
-- Dumped by pg_dump version 15.8 (Debian 15.8-1.pgdg110+1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: iceberg_detections; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.iceberg_detections (
    id uuid NOT NULL,
    iceberg_id uuid NOT NULL,
    "timestamp" timestamp with time zone NOT NULL,
    geometry public.geometry(Point,4326) NOT NULL,
    estimated_size double precision,
    extent public.geometry(Polygon,4326),
    confidence double precision NOT NULL,
    source_imagery character varying(255),
    detection_metadata json
);


ALTER TABLE public.iceberg_detections OWNER TO postgres;

--
-- Name: icebergs; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.icebergs (
    iceberg_id uuid NOT NULL
);


ALTER TABLE public.icebergs OWNER TO postgres;

--
-- Name: ocean_observations; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.ocean_observations (
    id uuid NOT NULL,
    "timestamp" timestamp with time zone NOT NULL,
    geometry public.geometry(Point,4326) NOT NULL,
    current_speed double precision NOT NULL,
    current_direction double precision NOT NULL,
    sea_surface_temperature double precision NOT NULL,
    wave_information character varying(255),
    source character varying(255) NOT NULL
);


ALTER TABLE public.ocean_observations OWNER TO postgres;

--
-- Name: risk_cells; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.risk_cells (
    id uuid NOT NULL,
    geometry public.geometry(Polygon,4326) NOT NULL,
    "timestamp" timestamp with time zone NOT NULL,
    ice_risk double precision NOT NULL,
    iceberg_risk double precision NOT NULL,
    weather_risk double precision NOT NULL,
    current_risk double precision NOT NULL,
    composite_risk double precision NOT NULL,
    risk_category character varying(50) NOT NULL,
    confidence_score double precision NOT NULL,
    missing_data_flags json NOT NULL,
    metadata_info json NOT NULL
);


ALTER TABLE public.risk_cells OWNER TO postgres;

--
-- Name: routes; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.routes (
    route_id uuid NOT NULL,
    origin character varying(255) NOT NULL,
    destination character varying(255) NOT NULL,
    vessel_id uuid NOT NULL,
    departure_time timestamp with time zone NOT NULL,
    geometry public.geometry(LineString,4326) NOT NULL,
    distance double precision NOT NULL,
    eta timestamp with time zone NOT NULL,
    estimated_fuel double precision NOT NULL,
    risk_score double precision NOT NULL,
    objective_type public.objectivetype NOT NULL,
    algorithm_version character varying(50)
);


ALTER TABLE public.routes OWNER TO postgres;

--
-- Name: COLUMN routes.distance; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.routes.distance IS 'distance in nautical miles';


--
-- Name: vessels; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.vessels (
    vessel_id uuid NOT NULL,
    vessel_name character varying(255) NOT NULL,
    vessel_type character varying(100) NOT NULL,
    cruising_speed double precision NOT NULL,
    fuel_consumption double precision NOT NULL,
    ice_capability character varying(50) NOT NULL,
    operational_limits json
);


ALTER TABLE public.vessels OWNER TO postgres;

--
-- Name: COLUMN vessels.cruising_speed; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.vessels.cruising_speed IS 'in knots';


--
-- Name: COLUMN vessels.fuel_consumption; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.vessels.fuel_consumption IS 'rate of consumption';


--
-- Name: COLUMN vessels.ice_capability; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.vessels.ice_capability IS 'ice class';


--
-- Name: iceberg_detections iceberg_detections_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.iceberg_detections
    ADD CONSTRAINT iceberg_detections_pkey PRIMARY KEY (id);


--
-- Name: icebergs icebergs_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.icebergs
    ADD CONSTRAINT icebergs_pkey PRIMARY KEY (iceberg_id);


--
-- Name: ocean_observations ocean_observations_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ocean_observations
    ADD CONSTRAINT ocean_observations_pkey PRIMARY KEY (id);


--
-- Name: risk_cells risk_cells_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.risk_cells
    ADD CONSTRAINT risk_cells_pkey PRIMARY KEY (id);


--
-- Name: routes routes_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.routes
    ADD CONSTRAINT routes_pkey PRIMARY KEY (route_id);


--
-- Name: vessels vessels_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.vessels
    ADD CONSTRAINT vessels_pkey PRIMARY KEY (vessel_id);


--
-- Name: idx_iceberg_detections_extent; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_iceberg_detections_extent ON public.iceberg_detections USING gist (extent);


--
-- Name: idx_iceberg_detections_geometry; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_iceberg_detections_geometry ON public.iceberg_detections USING gist (geometry);


--
-- Name: idx_ocean_observations_geometry; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_ocean_observations_geometry ON public.ocean_observations USING gist (geometry);


--
-- Name: idx_risk_cells_geometry; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_risk_cells_geometry ON public.risk_cells USING gist (geometry);


--
-- Name: idx_routes_geometry; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_routes_geometry ON public.routes USING gist (geometry);


--
-- Name: ix_iceberg_detections_geometry; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_iceberg_detections_geometry ON public.iceberg_detections USING btree (geometry);


--
-- Name: ix_iceberg_detections_iceberg_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_iceberg_detections_iceberg_id ON public.iceberg_detections USING btree (iceberg_id);


--
-- Name: ix_iceberg_detections_timestamp; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_iceberg_detections_timestamp ON public.iceberg_detections USING btree ("timestamp");


--
-- Name: ix_ocean_observations_geometry; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_ocean_observations_geometry ON public.ocean_observations USING btree (geometry);


--
-- Name: ix_ocean_observations_timestamp; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_ocean_observations_timestamp ON public.ocean_observations USING btree ("timestamp");


--
-- Name: ix_risk_cells_geometry; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_risk_cells_geometry ON public.risk_cells USING btree (geometry);


--
-- Name: ix_risk_cells_timestamp; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_risk_cells_timestamp ON public.risk_cells USING btree ("timestamp");


--
-- Name: ix_routes_geometry; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_routes_geometry ON public.routes USING btree (geometry);


--
-- Name: ix_routes_vessel_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_routes_vessel_id ON public.routes USING btree (vessel_id);


--
-- Name: ix_vessels_vessel_name; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_vessels_vessel_name ON public.vessels USING btree (vessel_name);


--
-- Name: iceberg_detections iceberg_detections_iceberg_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.iceberg_detections
    ADD CONSTRAINT iceberg_detections_iceberg_id_fkey FOREIGN KEY (iceberg_id) REFERENCES public.icebergs(iceberg_id);


--
-- Name: routes routes_vessel_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.routes
    ADD CONSTRAINT routes_vessel_id_fkey FOREIGN KEY (vessel_id) REFERENCES public.vessels(vessel_id);


--
-- PostgreSQL database dump complete
--

