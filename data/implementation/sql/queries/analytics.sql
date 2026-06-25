-- Procurement Analysis: Key SQL Queries

-- 1. Monthly procurement volume trends
-- Purpose: Track overall procurement activity over time
SELECT 
    DATE_TRUNC('month', published_date) as month,
    COUNT(*) as procurement_count,
    SUM(initial_price) as total_nmck,
    SUM(contract_price) as total_contracts,
    AVG(savings_percent) as avg_savings,
    ROUND(SUM(CASE WHEN participants_count = 1 THEN 1 ELSE 0 END)::NUMERIC / COUNT(*) * 100, 2) as monopoly_percent
FROM procurements
WHERE status = 'completed'
    AND published_date >= '2024-01-01'
GROUP BY DATE_TRUNC('month', published_date)
ORDER BY month;

-- 2. Top 20 most expensive procurements
-- Purpose: Identify largest contracts for detailed review
SELECT 
    p.procurement_number,
    p.object_name,
    o_cust.org_name as customer,
    o_win.org_name as winner,
    p.initial_price,
    p.contract_price,
    p.savings_percent,
    p.published_date,
    c.category_name
FROM procurements p
JOIN organizations o_cust ON p.customer_id = o_cust.org_id
LEFT JOIN organizations o_win ON p.winner_id = o_win.org_id
LEFT JOIN categories c ON p.category_code = c.okpd2_code
WHERE p.contract_price IS NOT NULL
ORDER BY p.contract_price DESC
LIMIT 20;

-- 3. Monopoly procurements analysis
-- Purpose: Identify procurements with no competition
SELECT 
    p.procurement_number,
    p.object_name,
    o_cust.org_name as customer,
    o_win.org_name as winner,
    p.initial_price,
    p.contract_price,
    p.savings_percent,
    p.procurement_method,
    c.category_name
FROM procurements p
JOIN organizations o_cust ON p.customer_id = o_cust.org_id
LEFT JOIN organizations o_win ON p.winner_id = o_win.org_id
LEFT JOIN categories c ON p.category_code = c.okpd2_code
WHERE p.participants_count = 1
    AND p.status = 'completed'
ORDER BY p.contract_price DESC
LIMIT 100;

-- 4. Supplier performance ranking
-- Purpose: Identify most successful suppliers
SELECT 
    o.org_name,
    o.inn,
    COUNT(*) as wins,
    SUM(p.contract_price) as total_value,
    AVG(p.contract_price) as avg_contract,
    AVG(p.savings_percent) as avg_savings,
    ROUND(SUM(CASE WHEN p.participants_count = 1 THEN 1 ELSE 0 END)::NUMERIC / COUNT(*) * 100, 2) as monopoly_rate,
    COUNT(DISTINCT p.customer_id) as unique_customers
FROM organizations o
JOIN procurements p ON o.org_id = p.winner_id
WHERE p.status = 'completed'
GROUP BY o.org_id, o.org_name, o.inn
HAVING COUNT(*) >= 10
ORDER BY total_value DESC
LIMIT 50;

-- 5. Category analysis
-- Purpose: Understand distribution across procurement categories
SELECT 
    c.category_name,
    c.okpd2_code,
    COUNT(*) as procurement_count,
    SUM(p.initial_price) as total_nmck,
    SUM(p.contract_price) as total_contracts,
    AVG(p.savings_percent) as avg_savings,
    AVG(p.participants_count) as avg_participants
FROM categories c
JOIN procurements p ON c.okpd2_code = p.category_code
WHERE p.status = 'completed'
GROUP BY c.category_id, c.category_name, c.okpd2_code
HAVING COUNT(*) >= 5
ORDER BY total_contracts DESC
LIMIT 30;

-- 6. Savings distribution analysis
-- Purpose: Understand procurement efficiency
SELECT 
    CASE 
        WHEN savings_percent < 0 THEN 'Overspend (< 0%)'
        WHEN savings_percent BETWEEN 0 AND 5 THEN 'Low (0-5%)'
        WHEN savings_percent BETWEEN 5 AND 10 THEN 'Medium (5-10%)'
        WHEN savings_percent BETWEEN 10 AND 20 THEN 'Good (10-20%)'
        WHEN savings_percent BETWEEN 20 AND 50 THEN 'High (20-50%)'
        ELSE 'Excessive (>50%)'
    END as savings_range,
    COUNT(*) as count,
    ROUND(COUNT(*)::NUMERIC / SUM(COUNT(*)) OVER () * 100, 2) as percent,
    AVG(contract_price) as avg_value
FROM procurements
WHERE contract_price IS NOT NULL
    AND initial_price > 0
GROUP BY savings_range
ORDER BY 
    CASE savings_range
        WHEN 'Overspend (< 0%)' THEN 1
        WHEN 'Low (0-5%)' THEN 2
        WHEN 'Medium (5-10%)' THEN 3
        WHEN 'Good (10-20%)' THEN 4
        WHEN 'High (20-50%)' THEN 5
        WHEN 'Excessive (>50%)' THEN 6
    END;

-- 7. Competition level impact on savings
-- Purpose: Analyze relationship between competition and savings
SELECT 
    CASE 
        WHEN participants_count = 1 THEN '1 (Monopoly)'
        WHEN participants_count = 2 THEN '2'
        WHEN participants_count = 3 THEN '3'
        WHEN participants_count BETWEEN 4 AND 5 THEN '4-5'
        ELSE '6+'
    END as participant_range,
    COUNT(*) as procurement_count,
    AVG(savings_percent) as avg_savings,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY savings_percent) as median_savings,
    MIN(savings_percent) as min_savings,
    MAX(savings_percent) as max_savings
FROM procurements
WHERE contract_price IS NOT NULL
GROUP BY participant_range
ORDER BY participant_range;

-- 8. Year-over-year comparison
-- Purpose: Compare 2024 vs 2025 performance
SELECT 
    EXTRACT(YEAR FROM published_date) as year,
    COUNT(*) as procurement_count,
    SUM(initial_price) as total_nmck,
    SUM(contract_price) as total_contracts,
    AVG(savings_percent) as avg_savings,
    AVG(participants_count) as avg_participants
FROM procurements
WHERE status = 'completed'
    AND published_date >= '2024-01-01'
GROUP BY EXTRACT(YEAR FROM published_date)
ORDER BY year;

-- 9. Procurement method effectiveness
-- Purpose: Compare different procurement methods
SELECT 
    procurement_method,
    law_type,
    COUNT(*) as count,
    AVG(savings_percent) as avg_savings,
    AVG(participants_count) as avg_participants,
    AVG(contract_price) as avg_value
FROM procurements
WHERE status = 'completed'
GROUP BY procurement_method, law_type
HAVING COUNT(*) >= 10
ORDER BY avg_savings DESC;

-- 10. Customer activity ranking
-- Purpose: Identify most active customers
SELECT 
    o.org_name,
    o.inn,
    COUNT(*) as procurement_count,
    SUM(p.contract_price) as total_spent,
    AVG(p.savings_percent) as avg_savings,
    AVG(p.participants_count) as avg_competition
FROM organizations o
JOIN procurements p ON o.org_id = p.customer_id
WHERE o.is_sber_group = TRUE
    AND p.status = 'completed'
GROUP BY o.org_id, o.org_name, o.inn
ORDER BY total_spent DESC;

-- 11. Seasonal patterns
-- Purpose: Identify procurement seasonality
SELECT 
    EXTRACT(QUARTER FROM published_date) as quarter,
    EXTRACT(MONTH FROM published_date) as month,
    COUNT(*) as procurement_count,
    SUM(contract_price) as total_value,
    AVG(savings_percent) as avg_savings
FROM procurements
WHERE status = 'completed'
GROUP BY EXTRACT(QUARTER FROM published_date), EXTRACT(MONTH FROM published_date)
ORDER BY quarter, month;

-- 12. Anomalies summary
-- Purpose: Overview of detected anomalies
SELECT 
    anomaly_type,
    severity,
    COUNT(*) as count,
    AVG(confidence_score) as avg_confidence
FROM anomalies
WHERE is_validated = FALSE
GROUP BY anomaly_type, severity
ORDER BY 
    CASE severity
        WHEN 'critical' THEN 1
        WHEN 'high' THEN 2
        WHEN 'medium' THEN 3
        ELSE 4
    END,
    count DESC;

-- 13. Data quality report
-- Purpose: Assess data completeness
SELECT 
    source,
    COUNT(*) as total_records,
    AVG(data_quality_score) as avg_quality_score,
    SUM(CASE WHEN data_quality_score >= 0.8 THEN 1 ELSE 0 END) as high_quality_count,
    SUM(CASE WHEN data_quality_score < 0.5 THEN 1 ELSE 0 END) as low_quality_count
FROM procurements
GROUP BY source
ORDER BY total_records DESC;

-- 14. Supplier concentration risk
-- Purpose: Identify dependency on few suppliers
WITH supplier_totals AS (
    SELECT 
        winner_id,
        SUM(contract_price) as supplier_total
    FROM procurements
    WHERE status = 'completed'
    GROUP BY winner_id
),
ranked_suppliers AS (
    SELECT 
        winner_id,
        supplier_total,
        RANK() OVER (ORDER BY supplier_total DESC) as rank,
        SUM(supplier_total) OVER () as grand_total
    FROM supplier_totals
)
SELECT 
    r.rank,
    o.org_name,
    r.supplier_total,
    ROUND(r.supplier_total / r.grand_total * 100, 2) as market_share,
    ROUND(SUM(r.supplier_total) OVER (ORDER BY r.rank) / r.grand_total * 100, 2) as cumulative_share
FROM ranked_suppliers r
JOIN organizations o ON r.winner_id = o.org_id
WHERE r.rank <= 20
ORDER BY r.rank;

-- 15. Price volatility analysis
-- Purpose: Identify categories with high price fluctuation
SELECT 
    c.category_name,
    COUNT(*) as procurement_count,
    AVG(p.contract_price) as avg_price,
    STDDEV(p.contract_price) as price_stddev,
    ROUND(STDDEV(p.contract_price) / NULLIF(AVG(p.contract_price), 0) * 100, 2) as coefficient_of_variation
FROM procurements p
JOIN categories c ON p.category_code = c.okpd2_code
WHERE p.contract_price IS NOT NULL
GROUP BY c.category_id, c.category_name
HAVING COUNT(*) >= 20
ORDER BY coefficient_of_variation DESC
LIMIT 20;
