-- Procurement Analysis Database Schema

-- Organizations (buyers and suppliers)
CREATE TABLE IF NOT EXISTS organizations (
    org_id SERIAL PRIMARY KEY,
    inn VARCHAR(12) UNIQUE NOT NULL,
    kpp VARCHAR(9),
    org_name VARCHAR(500) NOT NULL,
    full_name TEXT,
    short_name VARCHAR(500),
    ogrn VARCHAR(15),
    is_sber_group BOOLEAN DEFAULT FALSE,
    org_type VARCHAR(50), -- customer, supplier, both
    region VARCHAR(200),
    address TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Categories (OKPD2)
CREATE TABLE IF NOT EXISTS categories (
    category_id SERIAL PRIMARY KEY,
    okpd2_code VARCHAR(20) UNIQUE NOT NULL,
    category_name VARCHAR(500) NOT NULL,
    parent_code VARCHAR(20),
    level INTEGER,
    created_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (parent_code) REFERENCES categories(okpd2_code) ON DELETE SET NULL
);

-- Procurements
CREATE TABLE IF NOT EXISTS procurements (
    procurement_id BIGSERIAL PRIMARY KEY,
    source VARCHAR(50) NOT NULL, -- eis, sberbank-ast, etp-gpb, etc.
    procurement_number VARCHAR(200) UNIQUE NOT NULL,
    customer_id INTEGER NOT NULL,
    
    -- Typology
    law_type VARCHAR(20), -- 44-fz, 223-fz, commercial
    procurement_method VARCHAR(100), -- auction, tender, quotation, etc.
    category_code VARCHAR(20),
    
    -- Dates
    published_date DATE NOT NULL,
    submission_deadline TIMESTAMP,
    auction_date TIMESTAMP,
    contract_start_date DATE,
    contract_end_date DATE,
    
    -- Financial
    initial_price NUMERIC(18,2) NOT NULL, -- NMCK
    contract_price NUMERIC(18,2), -- final price
    savings_amount NUMERIC(18,2),
    savings_percent NUMERIC(5,2),
    currency VARCHAR(3) DEFAULT 'RUB',
    
    -- Description
    object_name VARCHAR(1000),
    object_description TEXT,
    
    -- Results
    participants_count INTEGER DEFAULT 0,
    winner_id INTEGER,
    status VARCHAR(50) DEFAULT 'published', -- published, completed, cancelled, failed
    
    -- Metadata
    is_anomaly BOOLEAN DEFAULT FALSE,
    anomaly_type VARCHAR(100),
    data_quality_score NUMERIC(3,2), -- 0.00 to 1.00
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    FOREIGN KEY (customer_id) REFERENCES organizations(org_id) ON DELETE CASCADE,
    FOREIGN KEY (winner_id) REFERENCES organizations(org_id) ON DELETE SET NULL,
    FOREIGN KEY (category_code) REFERENCES categories(okpd2_code) ON DELETE SET NULL
);

-- Procurement Lots
CREATE TABLE IF NOT EXISTS procurement_lots (
    lot_id BIGSERIAL PRIMARY KEY,
    procurement_id BIGINT NOT NULL,
    lot_number INTEGER NOT NULL,
    lot_name VARCHAR(500),
    lot_description TEXT,
    category_code VARCHAR(20),
    initial_price NUMERIC(18,2) NOT NULL,
    contract_price NUMERIC(18,2),
    winner_id INTEGER,
    participants_count INTEGER DEFAULT 0,
    status VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW(),
    
    FOREIGN KEY (procurement_id) REFERENCES procurements(procurement_id) ON DELETE CASCADE,
    FOREIGN KEY (winner_id) REFERENCES organizations(org_id) ON DELETE SET NULL,
    FOREIGN KEY (category_code) REFERENCES categories(okpd2_code) ON DELETE SET NULL,
    UNIQUE (procurement_id, lot_number)
);

-- Documents
CREATE TABLE IF NOT EXISTS documents (
    doc_id BIGSERIAL PRIMARY KEY,
    procurement_id BIGINT NOT NULL,
    doc_type VARCHAR(100), -- technical_spec, contract, protocol, etc.
    file_name VARCHAR(500),
    file_path VARCHAR(1000),
    file_size BIGINT,
    file_hash VARCHAR(64),
    url TEXT,
    extracted_text TEXT,
    is_anonymized BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    
    FOREIGN KEY (procurement_id) REFERENCES procurements(procurement_id) ON DELETE CASCADE
);

-- External Data: Exchange Rates
CREATE TABLE IF NOT EXISTS exchange_rates (
    rate_id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    currency VARCHAR(3) NOT NULL,
    rate NUMERIC(10,4) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE (date, currency)
);

-- External Data: Key Rate
CREATE TABLE IF NOT EXISTS key_rate (
    rate_id SERIAL PRIMARY KEY,
    date DATE NOT NULL UNIQUE,
    rate NUMERIC(5,2) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- External Data: Inflation
CREATE TABLE IF NOT EXISTS inflation_data (
    inflation_id SERIAL PRIMARY KEY,
    date DATE NOT NULL UNIQUE,
    cpi NUMERIC(6,2), -- consumer price index
    ppi NUMERIC(6,2), -- producer price index
    inflation_rate NUMERIC(5,2), -- yearly %
    created_at TIMESTAMP DEFAULT NOW()
);

-- Anomalies Log
CREATE TABLE IF NOT EXISTS anomalies (
    anomaly_id BIGSERIAL PRIMARY KEY,
    procurement_id BIGINT NOT NULL,
    anomaly_type VARCHAR(100) NOT NULL,
    severity VARCHAR(20), -- low, medium, high, critical
    description TEXT,
    detection_method VARCHAR(100), -- iqr, zscore, isolation_forest, business_rule
    confidence_score NUMERIC(3,2),
    is_validated BOOLEAN DEFAULT FALSE,
    validator_notes TEXT,
    detected_at TIMESTAMP DEFAULT NOW(),
    
    FOREIGN KEY (procurement_id) REFERENCES procurements(procurement_id) ON DELETE CASCADE
);

-- Analytics Cache (for complex queries)
CREATE TABLE IF NOT EXISTS analytics_cache (
    cache_id SERIAL PRIMARY KEY,
    cache_key VARCHAR(200) UNIQUE NOT NULL,
    query_name VARCHAR(200),
    result_data JSONB,
    parameters JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP
);

-- Data Collection Log
CREATE TABLE IF NOT EXISTS collection_log (
    log_id BIGSERIAL PRIMARY KEY,
    source VARCHAR(50) NOT NULL,
    collection_date DATE NOT NULL,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    records_collected INTEGER DEFAULT 0,
    records_new INTEGER DEFAULT 0,
    records_updated INTEGER DEFAULT 0,
    records_failed INTEGER DEFAULT 0,
    status VARCHAR(20), -- running, completed, failed
    error_message TEXT,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_proc_customer ON procurements(customer_id);
CREATE INDEX idx_proc_winner ON procurements(winner_id);
CREATE INDEX idx_proc_dates ON procurements(published_date, contract_start_date);
CREATE INDEX idx_proc_category ON procurements(category_code);
CREATE INDEX idx_proc_prices ON procurements(initial_price, contract_price);
CREATE INDEX idx_proc_source ON procurements(source);
CREATE INDEX idx_proc_status ON procurements(status);
CREATE INDEX idx_proc_law_type ON procurements(law_type);
CREATE INDEX idx_proc_method ON procurements(procurement_method);
CREATE INDEX idx_proc_anomaly ON procurements(is_anomaly) WHERE is_anomaly = TRUE;

CREATE INDEX idx_org_inn ON organizations(inn);
CREATE INDEX idx_org_sber ON organizations(is_sber_group) WHERE is_sber_group = TRUE;
CREATE INDEX idx_org_type ON organizations(org_type);

CREATE INDEX idx_lots_proc ON procurement_lots(procurement_id);
CREATE INDEX idx_lots_winner ON procurement_lots(winner_id);

CREATE INDEX idx_docs_proc ON documents(procurement_id);
CREATE INDEX idx_docs_type ON documents(doc_type);

CREATE INDEX idx_exrate_date ON exchange_rates(date);
CREATE INDEX idx_keyrate_date ON key_rate(date);
CREATE INDEX idx_inflation_date ON inflation_data(date);

CREATE INDEX idx_anomalies_proc ON anomalies(procurement_id);
CREATE INDEX idx_anomalies_type ON anomalies(anomaly_type);

-- Views for common queries

-- Sberbank Group Procurements
CREATE OR REPLACE VIEW v_sber_procurements AS
SELECT 
    p.*,
    o.org_name as customer_name,
    o.inn as customer_inn,
    w.org_name as winner_name,
    w.inn as winner_inn,
    c.category_name
FROM procurements p
JOIN organizations o ON p.customer_id = o.org_id
LEFT JOIN organizations w ON p.winner_id = w.org_id
LEFT JOIN categories c ON p.category_code = c.okpd2_code
WHERE o.is_sber_group = TRUE;

-- Monthly Statistics
CREATE OR REPLACE VIEW v_monthly_stats AS
SELECT 
    DATE_TRUNC('month', published_date) as month,
    source,
    law_type,
    COUNT(*) as procurement_count,
    SUM(initial_price) as total_nmck,
    SUM(contract_price) as total_contracts,
    AVG(savings_percent) as avg_savings,
    SUM(CASE WHEN participants_count = 1 THEN 1 ELSE 0 END) as monopoly_count
FROM procurements
WHERE status = 'completed'
GROUP BY DATE_TRUNC('month', published_date), source, law_type;

-- Supplier Performance
CREATE OR REPLACE VIEW v_supplier_performance AS
SELECT 
    o.org_id,
    o.org_name,
    o.inn,
    COUNT(*) as total_wins,
    SUM(p.contract_price) as total_value,
    AVG(p.contract_price) as avg_contract,
    AVG(p.savings_percent) as avg_savings,
    SUM(CASE WHEN p.participants_count = 1 THEN 1 ELSE 0 END) as monopoly_wins,
    COUNT(DISTINCT p.customer_id) as unique_customers
FROM organizations o
JOIN procurements p ON o.org_id = p.winner_id
WHERE p.status = 'completed'
GROUP BY o.org_id, o.org_name, o.inn;

-- Functions

-- Calculate savings
CREATE OR REPLACE FUNCTION calculate_savings()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.contract_price IS NOT NULL AND NEW.initial_price > 0 THEN
        NEW.savings_amount := NEW.initial_price - NEW.contract_price;
        NEW.savings_percent := (NEW.savings_amount / NEW.initial_price) * 100;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_calculate_savings
BEFORE INSERT OR UPDATE ON procurements
FOR EACH ROW
EXECUTE FUNCTION calculate_savings();

-- Update timestamp
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at := NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_update_organizations
BEFORE UPDATE ON organizations
FOR EACH ROW
EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER trg_update_procurements
BEFORE UPDATE ON procurements
FOR EACH ROW
EXECUTE FUNCTION update_updated_at();

-- Comments
COMMENT ON TABLE procurements IS 'Main procurement data from all sources';
COMMENT ON TABLE organizations IS 'Customers and suppliers (unified)';
COMMENT ON TABLE categories IS 'OKPD2 classification hierarchy';
COMMENT ON TABLE anomalies IS 'Detected anomalies with validation status';
COMMENT ON COLUMN procurements.data_quality_score IS 'Data completeness score 0-1';
COMMENT ON COLUMN procurements.is_anomaly IS 'Flag for quick anomaly filtering';
